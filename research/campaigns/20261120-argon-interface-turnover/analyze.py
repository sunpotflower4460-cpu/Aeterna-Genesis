"""Read a moving 3D liquid component and atom identities from archived trajectories."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from tools.study_record import check_record, load_plan, read_object

HERE = Path(__file__).resolve().parent
SCHEMES = {
    "main": (0.35, 2.0, 1),
    "low-density-cut": (0.30, 2.0, 1),
    "high-density-cut": (0.40, 2.0, 1),
    "deep-cores": (0.35, 3.0, 1),
    "coarser-time": (0.35, 2.0, 2),
}


def periodic_labels(active):
    """Join face-connected labels across each of the six periodic faces."""
    labels, count = ndimage.label(active)
    parent = np.arange(count + 1)

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for axis in range(3):
        a, b = np.take(labels, 0, axis=axis), np.take(labels, -1, axis=axis)
        valid = (a != 0) & (b != 0) & (a != b)
        for left, right in np.unique(np.column_stack((a[valid], b[valid])), axis=0):
            parent[root(right)] = root(left)
    return np.array([root(k) for k in range(count + 1)])[labels]


def separate(field, minimum_volume, dx, threshold, distance):
    active = field >= threshold
    labels = periodic_labels(active)
    counts = np.bincount(labels.ravel())
    counts[0] = 0
    leading = int(np.argmax(counts))
    peak = int(counts[leading])
    if not peak:
        empty = np.zeros_like(active)
        return empty, empty, empty, False, 0
    dense = labels == leading
    extent = [
        np.count_nonzero(np.any(dense, axis=tuple(i for i in range(3) if i != axis)))
        for axis in range(3)
    ]
    # A vacant plane on each axis makes it possible to cut the torus around this component.
    bounded = peak * dx**3 >= minimum_volume and all(n < limit for n, limit in zip(extent, dense.shape))
    counts[leading] = 0
    second = float(counts.max() * dx**3)
    if not bounded:
        empty = np.zeros_like(active)
        return dense, empty, empty, False, second
    radius = int(np.floor(distance / dx))
    x, y, z = np.ogrid[-radius:radius + 1, -radius:radius + 1, -radius:radius + 1]
    footprint = dx**2 * (x * x + y * y + z * z) <= distance**2
    liquid = ndimage.minimum_filter(dense, footprint=footprint, mode="wrap")
    vapor = ~ndimage.maximum_filter(active, footprint=footprint, mode="wrap")
    return dense, liquid, vapor, True, second


def phase_at(flags, indices):
    return flags[indices[:, 0], indices[:, 1], indices[:, 2]]


def classify(positions, times, length, cutoff, distance, protocol):
    n = round(length)
    dx = length / n
    indices = ((2 * positions.astype(np.int32) + 1) * n) // 131072
    anchor = np.flatnonzero(times == protocol["fork"]).item()
    frozen = indices[anchor]
    phase = np.zeros(indices.shape[:2], dtype=np.uint8)
    null_phase = np.zeros_like(phase)
    previous = None
    rows = []
    for i, ids in enumerate(indices):
        flat = np.ravel_multi_index(ids.T, (n, n, n))
        raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
        smooth = ndimage.gaussian_filter(raw, protocol["smooth_sigma"] / dx, mode="wrap")
        dense, liquid, vapor, bounded, second = separate(
            smooth, protocol["minimum_component_volume"], dx, cutoff, distance)
        shape_overlap = None
        if previous is not None:
            union = np.count_nonzero(previous | dense)
            if union:
                shape_overlap = float(np.count_nonzero(previous & dense) / union)
        previous = dense
        liquid_n, vapor_n = int(np.count_nonzero(liquid)), int(np.count_nonzero(vapor))
        if bounded:
            for target, positions_for_reading in ((phase, ids), (null_phase, frozen)):
                target[i, phase_at(liquid, positions_for_reading)] = 1
                target[i, phase_at(vapor, positions_for_reading)] = 2
        rows.append({
            "t": float(times[i]),
            "bounded": bounded,
            "component_volume": float(np.count_nonzero(dense) * dx**3),
            "second_component_volume": second,
            "overlap": shape_overlap,
            "liquid_count": int(np.count_nonzero(phase[i] == 1)),
            "vapor_count": int(np.count_nonzero(phase[i] == 2)),
            "liquid_density": float(raw[liquid].mean()) if liquid_n else None,
            "vapor_density": float(raw[vapor].mean()) if vapor_n else None,
            "max_smoothed_density": float(smooth.max()),
        })
    return phase, null_phase, rows


def mine_track(rows, split, gate):
    """Follow the bounded dominant component without bridging gaps."""
    anchor = next(i for i, row in enumerate(rows) if row["t"] == split)
    if not rows[anchor]["bounded"]:
        return anchor, None
    end = anchor
    for i, current in enumerate(rows[anchor + 1:], start=anchor + 1):
        if not current["bounded"] or current["overlap"] is None or current["overlap"] < gate:
            break
        end = i
    return anchor, end


def stable_at(phase, index, residence):
    window = phase[index - residence + 1:index + 1]
    ending = window[-1]
    return np.where(np.all(window == ending, axis=0), ending, 0)


def minimum_image(x, length):
    return (x + length / 2) % length - length / 2


def exchange(phase, positions, times, anchor, end, residence, length, min_displacement):
    """Count completed bulk visits in each direction and retain the atom IDs and endpoints."""
    baseline = stable_at(phase, anchor, residence)
    last_phase = baseline.copy()
    last_time = np.full(len(baseline), anchor, dtype=int)
    events = []
    for i in range(anchor + 1, end + 1):
        new = stable_at(phase, i, residence)
        different = np.flatnonzero((new != 0) & (last_phase != 0) & (new != last_phase))
        for atom in different:
            prev = last_time[atom]
            displacement = minimum_image((positions[i, atom].astype(float) - positions[prev, atom]) *
                                         (length / 65536), length)
            moved = float(np.linalg.norm(displacement))
            events.append({
                "atom": int(atom), "from_t": float(times[prev]), "to_t": float(times[i]),
                "direction": "liquid_to_vapor" if new[atom] == 2 else "vapor_to_liquid",
                "endpoint_displacement": moved, "moves_between_cores": moved >= min_displacement,
            })
        seen = new != 0
        last_phase[seen] = new[seen]
        last_time[seen] = i

    final = stable_at(phase, end, residence)
    initial_liquid = baseline == 1
    final_liquid = final == 1
    first = int(initial_liquid.sum())
    last = int(final_liquid.sum())
    distinct_departures = {x["atom"] for x in events if x["direction"] == "liquid_to_vapor" and
                           x["moves_between_cores"]}
    return {
        "initial_liquid_core_count": first,
        "final_liquid_core_count": last,
        "final_core_from_initial_core": int((initial_liquid & final_liquid).sum()),
        "final_core_from_initial_vapor": int(((baseline == 2) & final_liquid).sum()),
        "initial_core_atoms_confirmed_in_vapor": sum(bool(initial_liquid[k]) for k in distinct_departures),
        "arrival_events": sum(x["direction"] == "vapor_to_liquid" for x in events),
        "departure_events": sum(x["direction"] == "liquid_to_vapor" for x in events),
        "arrivals_with_displacement": sum(x["direction"] == "vapor_to_liquid" and
                                          x["moves_between_cores"] for x in events),
        "departures_with_displacement": sum(x["direction"] == "liquid_to_vapor" and
                                            x["moves_between_cores"] for x in events),
        "events": events,
    }


def mean_or_none(data):
    return float(np.mean(data)) if len(data) else None


def summarize_case(positions, ledger, case, plan):
    p = plan["protocol"]
    length = case["length"]
    n = positions.shape[1]
    times = ledger[:, 1]
    details, histories = {}, {}
    for name, (threshold, separation, stride) in SCHEMES.items():
        history = positions[::stride]
        clock = times[::stride]
        phase, frozen_phase, rows = classify(history, clock, length, threshold, separation, p)
        anchor, end = mine_track(rows, p["fork"], p["overlap_min"])
        observed = {
            "bounded_frames_before_fork": sum(r["t"] < p["fork"] and r["bounded"] for r in rows),
            "bounded_frames_after_fork": sum(r["t"] >= p["fork"] and r["bounded"] for r in rows),
            "first_bounded_time": next((r["t"] for r in rows if r["bounded"]), None),
            "track_through": rows[end]["t"] if end is not None else None,
            "tracked_to_end": end == len(rows) - 1,
        }
        evidence = {"frames": rows}
        if end is not None:
            args = (clock, anchor, end, p["residence_frames"], length, p["minimum_displacement"])
            result = exchange(phase, history, *args)
            frozen = np.broadcast_to(history[anchor], history.shape)
            null = exchange(frozen_phase, frozen, *args)
            observed.update({k: v for k, v in result.items() if k != "events"})
            observed["fixed_atom_null_arrivals"] = null["arrival_events"]
            observed["fixed_atom_null_departures"] = null["departure_events"]
            observed["minimum_overlap_in_track"] = min(
                (row["overlap"] for row in rows[anchor + 1:end + 1]), default=None)
            observed["minimum_component_volume"] = float(min(r["component_volume"] for r in rows[anchor:end + 1]))
            observed["maximum_component_volume"] = float(max(r["component_volume"] for r in rows[anchor:end + 1]))
            observed["largest_secondary_volume"] = float(max(r["second_component_volume"] for r in rows[anchor:end + 1]))
            late = [row for row in rows[anchor:end + 1] if row["t"] >= p["density_window_starts"]]
            for phase_name in ("liquid", "vapor"):
                key = phase_name + "_density"
                values = [row[key] for row in late if row[key] is not None]
                observed["late_mean_" + key] = mean_or_none(values)
            observed["late_density_frames"] = len(late)
            evidence["events"] = result["events"]
            evidence["fixed_atom_null_events"] = null["events"]
        details[name], histories[name] = observed, evidence
    energy = ledger[:, 3] + ledger[:, 4]
    work = ledger[:, 5]
    fork = np.flatnonzero(times == p["fork"]).item()
    details["energy"] = {
        "max_balance_error_per_atom": float(np.abs(energy - energy[0] - work).max() / n),
        "terminal_bath_work_after_fork_per_atom": float((work[-1] - work[fork]) / n),
        "max_bath_work_change_after_fork_per_atom": float(np.abs(work[fork:] - work[fork]).max() / n),
        "max_energy_change_after_fork_per_atom": float(np.abs(energy[fork:] - energy[fork]).max() / n),
        "max_momentum_change_after_fork": float(np.linalg.norm(ledger[fork:, 6:] - ledger[fork, 6:], axis=1).max()),
        "late_temperature": float(ledger[times >= p["density_window_starts"], 2].mean()),
    }
    return details, histories


def load_trajectory(evidence, name, outcome):
    with np.load(evidence / (name + ".npz")) as child:
        ledger, positions = child["ledger"], child["positions"]
    if "prefix" in outcome:
        with np.load(evidence / outcome["prefix"]) as parent:
            if (not np.array_equal(parent["ledger"][-1], ledger[0])
                    or not np.array_equal(parent["positions"][-1], positions[0])):
                raise ValueError(f"prefix/continuation discontinuity for {name}")
            digest = hashlib.sha256(parent["common_state"].astype("<f8", copy=False).tobytes()).hexdigest()
            if digest != outcome["checkpoint_sha256"]:
                raise ValueError(f"exact common checkpoint mismatch for {name}")
            ledger = np.concatenate((parent["ledger"][:-1], ledger))
            positions = np.concatenate((parent["positions"][:-1], positions))
    return positions, ledger


def scale_data(plan):
    p = plan["material"]
    mass = p["mass_u"] * p["atomic_mass_constant"]
    sigma = p["sigma_m"]
    epsilon = p["epsilon_over_k_K"] * p["boltzmann_J_per_K"]
    return {
        "mass_kg": mass, "epsilon_J": epsilon, "tau_ps": float(1e12 * sigma * np.sqrt(mass / epsilon)),
        "density_kg_per_m3_per_reduced_unit": mass / sigma**3,
        "cold_temperature_K": 0.8 * p["epsilon_over_k_K"],
    }


def analyze(evidence, out):
    plan = load_plan(HERE / "PLAN.json")
    path = evidence / "record.json"
    manifest = check_record(HERE / "PLAN.json", path)
    record = read_object(path)
    scale = scale_data(plan)
    results, measurement, groups = {}, {}, {}
    for name, case in plan["cases"].items():
        completed = record["cases"][name][-1]
        if completed["status"] != "completed":
            continue
        if "prefix" in completed:
            audit = (completed["prefix"], completed["checkpoint_sha256"])
            if case["group"] in groups and groups[case["group"]] != audit:
                raise ValueError(f"the arms reference different states for {case['group']}")
            groups[case["group"]] = audit
        positions, ledger = load_trajectory(evidence, name, completed)
        summary, detail = summarize_case(positions, ledger, case, plan)
        v = summary["main"]
        if case["mode"] == "bath" and all(v.get(f"late_mean_{phase}_density") is not None
                                           for phase in ("liquid", "vapor")):
            ref = plan["coexistence_reference"]
            factor = scale["density_kg_per_m3_per_reduced_unit"]
            b = ref["nist_reduced"][str(case["cutoff"])]
            n_l, n_v = v["late_mean_liquid_density"], v["late_mean_vapor_density"]
            summary["calibration"] = {
                "liquid_kg_m3": n_l * factor,
                "vapor_kg_m3": n_v * factor,
                "liquid_relative_difference_to_nist_LJ": n_l / b["liquid"] - 1,
                "vapor_relative_difference_to_nist_LJ": n_v / b["vapor"] - 1,
                "liquid_relative_difference_to_real_argon": n_l * factor / ref["argon"]["liquid_kg_m3"] - 1,
                "vapor_relative_difference_to_real_argon": n_v * factor / ref["argon"]["vapor_kg_m3"] - 1,
            }
        results[name], measurement[name] = summary, detail
        if case["mode"] == "isolated" and summary["energy"]["max_bath_work_change_after_fork_per_atom"] != 0.0:
            raise ValueError(f"{name} has unplanned heat after the fork")
    out.mkdir(parents=True, exist_ok=True)
    payload = {"manifest": manifest, "physical_scales": scale, "shared_prefixes": groups, "cases": results}
    (out / "results.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "measurements.json.gz").write_bytes(gzip.compress(
        json.dumps(measurement, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
