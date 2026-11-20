"""Compare two periodic-boundary tests on the same saved particle histories."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from study import PLAN
import measure as binary
from winding import topology
from tools.study_record import check_record, load_plan, read_object

geometry = binary.geometry


def core_footprint(dx, depth):
    radius = int(np.floor(depth / dx))
    x, y, z = np.ogrid[-radius:radius + 1, -radius:radius + 1, -radius:radius + 1]
    return dx**2 * (x * x + y * y + z * z) <= depth**2


def read_mask(field, dx, cutoff, minimum_volume, depth, footprint):
    """Use one component and one set of cores for both tests of its geometry."""
    dense, liquid, vapor, vacant, second = geometry.separate(field, minimum_volume, dx, cutoff, depth)
    voxels = int(dense.sum())
    volume = voxels * dx**3
    enough_volume = volume >= minimum_volume
    wraps = []
    if enough_volume and not vacant:
        graph = topology.periodic_components(dense)
        if graph["count"] != 1:
            raise ValueError("the detected dense component is disconnected on the torus")
        wraps = [axis for axis, flag in zip("xyz", graph["largest_winding_axes"]) if flag]
        liquid = ndimage.minimum_filter(dense, footprint=footprint, mode="wrap")
        vapor = ~ndimage.maximum_filter(field >= cutoff, footprint=footprint, mode="wrap")

    return dense, liquid, vapor, {
        "volume_sigma3": float(volume),
        "second_volume_sigma3": second,
        "vacant": bool(vacant),
        "finite": enough_volume and not wraps,
        "winding_axes": wraps,
        "above_minimum_volume": enough_volume,
    }


def read_history(positions, times, length, protocol, scheme):
    n = round(length)
    dx = length / n
    # Uint16 bin midpoints, with an optional common half-voxel shift of the sampling grid.
    indices = (((2 * positions.astype(np.int32) + 1) * n + 65536 * scheme["half_voxel_shift"]) // 131072) % n
    anchor = np.flatnonzero(times == protocol["fork"]).item()
    footprint = core_footprint(dx, protocol["core_depth"])
    phase = np.zeros(indices.shape[:2], dtype=np.uint8)
    fixed_phase = np.zeros_like(phase)
    previous = None
    rows = []
    for i, ids in enumerate(indices):
        flat = np.ravel_multi_index(ids.T, (n, n, n))
        raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
        smooth = ndimage.gaussian_filter(raw, protocol["smooth_sigma"] / dx, mode="wrap")
        dense, liquid, vapor, info = read_mask(smooth, dx, scheme["threshold"],
                                                protocol["minimum_component_volume"], protocol["core_depth"],
                                                footprint)
        union = np.count_nonzero(dense | previous) if previous is not None else 0
        overlap = float(np.count_nonzero(dense & previous) / union) if union else None
        rows.append({"t": float(times[i]), "overlap": overlap, **info})
        previous = dense
        if info["above_minimum_volume"]:
            for target, coordinates in ((phase, ids), (fixed_phase, indices[anchor])):
                target[i, geometry.phase_at(liquid, coordinates)] = 1
                target[i, geometry.phase_at(vapor, coordinates)] = 2
    return rows, phase, fixed_phase


def counts_by_phase(phase, species):
    totals = np.column_stack([(phase == k).sum(axis=1) for k in (1, 2)])
    heavy = np.column_stack([(phase[:, species == 1] == k).sum(axis=1) for k in (1, 2)])
    return totals, heavy


def stop_reason(row, method):
    if not row["above_minimum_volume"]:
        return "below_minimum_volume"
    if row["winding_axes"]:
        return "winding"
    if not row[method]:
        return "no_vacant_plane"
    return "overlap"


def track(rows, phases, fixed, method, positions, times, species, length, protocol):
    gated = [{**row, "bounded": row[method]} for row in rows]
    accepted = np.array([row[method] for row in rows])
    phase = np.where(accepted[:, None], phases, 0)
    fixed_phase = np.where(accepted[:, None], fixed, 0)
    anchor, last = geometry.mine_track(gated, protocol["fork"], protocol["overlap_min"])
    end = len(rows) - 1
    failure = anchor if last is None else last + 1
    t_stop = {"time_tau": float(times[failure]), "reason": stop_reason(rows[failure], method)} if failure <= end else None
    totals, heavy = counts_by_phase(phase, species)
    frame_index = np.arange(len(times))
    late = times >= protocol["comparison_start"]
    in_track = frame_index <= last if last is not None else np.zeros_like(late)
    core_window = late & in_track & (totals >= protocol["minimum_core_count"]).all(axis=1)
    retained = int(core_window.sum())
    transits = None
    null_events = []
    events = []
    if last is not None:
        args = (times, anchor, last, protocol["residence_frames"], length, protocol["minimum_displacement"])
        frozen = np.broadcast_to(positions[anchor], positions.shape)
        start = protocol["comparison_start"]
        events = [e for e in geometry.exchange(phase, positions, *args)["events"] if e["from_t"] >= start]
        null_events = [
            e for e in geometry.exchange(fixed_phase, frozen, *args)["events"] if e["from_t"] >= start
        ]
        transits = binary.count_events(events, species, phase, late & (frame_index < last),
                                       protocol["sample"], displaced=True)
    blocks = []
    edges = protocol["composition_block_edges"]
    for lo, hi in zip(edges, edges[1:]):
        keep = core_window & (times >= lo) & ((times <= hi) if hi == edges[-1] else (times < hi))
        blocks.append({"frames": int(keep.sum()), "composition": binary.fractions(totals[keep], heavy[keep])})
    summary = {
        "track_to_tau": float(times[last]) if last is not None else None,
        "stopped_at": t_stop,
        "composition_frames": retained,
        "complete": last == end and retained == int(late.sum()),
        "composition": binary.fractions(totals[core_window], heavy[core_window]),
        "blocks": blocks,
        "transits": transits,
        "fixed_positions_raw_events": len(null_events),
        "fixed_positions_displacement_events": sum(e["moves_between_cores"] for e in null_events),
        "both_species_both_directions": transits is not None and all(
            direction["events"] > 0 for element in transits.values() for direction in element.values()),
    }
    return summary, {"events": events, "fixed_positions_events": null_events}


def observe(positions, times, species, length, protocol, scheme):
    frames, phase, fixed = read_history(positions, times, length, protocol, scheme)
    scopes, details = {}, {}
    for method in ("vacant", "finite"):
        scopes[method], details[method] = track(
            frames, phase, fixed, method, positions, times, species, length, protocol)
    old, new = scopes["vacant"], scopes["finite"]
    if old["track_to_tau"] is not None and (
            new["track_to_tau"] is None or new["track_to_tau"] < old["track_to_tau"]):
        raise ValueError("a vacant plane on each axis must exclude winding")

    totals, heavy = counts_by_phase(phase, species)
    late = times >= protocol["comparison_start"]
    fit_cores = (totals >= protocol["minimum_core_count"]).all(axis=1)
    enough_volume = np.array([row["above_minimum_volume"] for row in frames])
    finite = np.array([row["finite"] for row in frames])
    old_bounded = np.array([row["vacant"] for row in frames])
    certain = finite & ~old_bounded
    pointwise = {}
    for name, box_condition in (("finite", finite), ("winding", enough_volume & ~finite)):
        selected = late & box_condition
        keep = selected & fit_cores
        pointwise[name] = {
            "frames": int(selected.sum()), "valid_core_frames": int(keep.sum()),
            "composition": binary.fractions(totals[keep], heavy[keep]),
            "mean_dense_volume_fraction": float(np.mean([frames[i]["volume_sigma3"] / length**3
                                                         for i in np.flatnonzero(selected)])) if selected.any() else None,
        }
    for i, row in enumerate(frames):
        row["total_core_counts"] = totals[i].tolist()
        row["krypton_core_counts"] = heavy[i].tolist()

    counts = {
        "fork_to_end": int((times >= protocol["fork"]).sum()),
        "old_rejections_at_fork_or_later": int((certain & (times >= protocol["fork"])).sum()),
        "old_rejections_before_fork": int((certain & (times < protocol["fork"])).sum()),
        "first_old_rejection_tau": next((row["t"] for row in frames if row["finite"] and not row["vacant"]), None),
        "winding_frames_at_fork_or_later": int((enough_volume & ~finite & (times >= protocol["fork"])).sum()),
    }
    return {**scopes, "counts": counts, "pointwise_window": pointwise}, {"frames": frames, **details}


def energy_record(ledger, particles, protocol, units):
    t = ledger[:, 1]
    fork = np.flatnonzero(t == protocol["fork"]).item()
    energy = ledger[:, 3] + ledger[:, 4]
    work = ledger[:, 5]
    momentum = ledger[:, 6:9]
    return {
        "late_mean_K": float(ledger[t >= protocol["comparison_start"], 2].mean() * units["kelvin_per_reduced_unit"]),
        "heat_balance_abs_error_per_atom": float(np.abs(energy - energy[0] - work).max() / particles),
        "max_change_energy_after_fork_per_atom": float(np.abs(energy[fork:] - energy[fork]).max() / particles),
        "max_change_bath_work_after_fork_per_atom": float(np.abs(work[fork:] - work[fork]).max() / particles),
        "max_change_momentum_after_fork": float(np.linalg.norm(momentum[fork:] - momentum[fork], axis=1).max()),
    }


def analyze(evidence, output):
    plan = load_plan(PLAN)
    protocol = plan["protocol"]
    record_path = evidence / "record.json"
    manifest = check_record(PLAN, record_path)
    record = read_object(record_path)
    units = binary.scales(plan)
    cases, readouts = {}, {}
    prefixes = {}
    initials = {}
    for name, config in plan["cases"].items():
        entry = record["cases"][name][-1]
        if entry["status"] != "completed":
            continue
        positions, ledger, species, initial = binary.load_binary(evidence, name, entry)
        group = config["group"]
        checkpoint = (entry.get("prefix"), entry.get("checkpoint_sha256"))
        if prefixes.setdefault(group, checkpoint) != checkpoint:
            raise ValueError(f"{group}: branches disagree about their shared prefix")
        key = (config["seed"], config["cells"])
        initial_digest = hashlib.sha256(initial[1].tobytes() + species.tobytes()).hexdigest()
        if initials.setdefault(key, initial_digest) != initial_digest:
            raise ValueError(f"{name}: density pair has unmatched velocities or species")
        measures, details = {}, {}
        for scheme, setup in plan["schemes"].items():
            measures[scheme], details[scheme] = observe(
                positions, ledger[:, 1], species, config["length"], protocol, setup)
        measures["ledger"] = energy_record(ledger, len(species), protocol, units)
        if config["mode"] == "isolated" and measures["ledger"]["max_change_bath_work_after_fork_per_atom"] != 0:
            raise ValueError(f"{name}: unregistered heat exchange after isolation")
        cases[name], readouts[name] = measures, details

    output.mkdir(parents=True, exist_ok=False)
    payload = {"manifest": manifest, "units": units, "cases": cases}
    (output / "results.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "readouts.json.gz").write_bytes(gzip.compress(
        json.dumps(readouts, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
