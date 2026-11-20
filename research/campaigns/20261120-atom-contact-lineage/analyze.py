"""Re-read the three registered losses with an atom-level contact graph."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from study import HERE, PLAN
import measure as binary
from contact_graph import histories
from lineage import affiliation, classify, events, follow, transition
from tools.study_record import check_record, load_plan, read_object, verify_registration

geometry = binary.geometry
ANALYSIS_INPUTS = HERE / "ANALYSIS_INPUTS.json"


def compare_replay(coarse, fine, previous, replay):
    old_q, old_ledger, old_species, old_initial = coarse
    q, ledger, species, initial = fine
    aligned = np.searchsorted(ledger[:, 1], old_ledger[:, 1])
    same_sample_times = len(aligned) != 0 and aligned.max() < len(ledger) and np.array_equal(
        ledger[aligned, 1], old_ledger[:, 1])
    coordinates = bool(same_sample_times and np.array_equal(q[aligned], old_q))
    ledgers = bool(same_sample_times and np.array_equal(ledger[aligned], old_ledger))
    exact_checkpoint = previous["checkpoint_sha256"] == replay["checkpoint_sha256"]
    result = {
        "common_time_frames": len(aligned) if same_sample_times else 0,
        "checked_fine_frames": len(q),
        "identical_saved_coordinates": coordinates,
        "identical_ledger_rows": ledgers,
        "identical_initial_state": np.array_equal(initial, old_initial),
        "identical_species": np.array_equal(species, old_species),
        "identical_fork_digest": exact_checkpoint,
    }
    result["verified"] = all(v for key, v in result.items() if key.startswith("identical_"))
    return result


def voxel_component(encoded, length, protocol, cutoff):
    n = round(length)
    dx = length / n
    ids = ((2 * encoded.astype(np.int32) + 1) * n) // 131072
    flat = np.ravel_multi_index(ids.T, (n,) * 3)
    raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
    field = ndimage.gaussian_filter(raw, protocol["smooth_sigma"] / dx, mode="wrap")
    dense, *_ = geometry.separate(field, protocol["minimum_component_volume"], dx, cutoff, protocol["core_depth"])
    return dense, geometry.phase_at(dense, ids)


def describe_pair(before, after, change, affiliations, grid_jaccard):
    a, b = affiliations
    i, j = a["match"], b["match"]
    return {
        "classification": classify(change, i, j),
        "voxel_jaccard": grid_jaccard,
        "before": {**a, "contact_sizes": before.sizes.tolist(), "winding_axes": before.winding_axes},
        "after": {**b, "contact_sizes": after.sizes.tolist(), "winding_axes": after.winding_axes},
        "shared_ids": change.shared.tolist(),
        "reciprocal_links": list(change.forward.items()),
        "merges": change.merges,
        "splits": change.splits,
    }


def pair_readout(data, times, grids, start, stop, rule):
    i = np.flatnonzero(times == start).item()
    j = np.flatnonzero(times == stop).item()
    grid_a, grid_b = grids[start], grids[stop]
    union = int((grid_a[0] | grid_b[0]).sum())
    jaccard = float((grid_a[0] & grid_b[0]).sum() / union) if union else None
    affiliations = (affiliation(data[i], grid_a[1]), affiliation(data[j], grid_b[1]))
    result = describe_pair(data[i], data[j], transition(data[i], data[j], rule), affiliations, jaccard)
    return {"from_tau": start, "to_tau": stop, **result}


def measure_timeline(data, clock, grids, loss, rule):
    transitions = [transition(a, b, rule) for a, b in zip(data, data[1:])]
    anchor = rule["anchor_tau"]
    summary, trace = follow(data, clock, transitions, grids[anchor][1], anchor)
    detail = {"followed_lineage": trace, "adjacent_events": []}
    if loss is not None:
        interval = rule["original_interval_tau"]
        width = rule["wide_pair_half_width_tau"]
        summary["loss_pair"] = pair_readout(data, clock, grids, loss - interval, loss, rule)
        summary["wide_pair"] = pair_readout(data, clock, grids, loss - width, loss + width, rule)
        detail["adjacent_events"] = events(data, clock, transitions, loss, rule["window_tau"],
                                          rule["persistence_tau"])
        detail["window_frames"] = [
            {"time_tau": float(t), "sizes": frame.sizes.tolist(), "winding_axes": frame.winding_axes}
            for t, frame in zip(clock, data) if abs(t - loss) <= rule["window_tau"]
        ]
        found = detail["adjacent_events"]
        summary["window_events"] = {kind: sum(e["kind"] == kind for e in found) for kind in ("merge", "split")}
        summary["persistent_window_events"] = {
            kind: sum(e["kind"] == kind and e["persistent"] is True for e in found) for kind in ("merge", "split")
        }
    return summary, detail


def observe(trajectory, length, plan, cutoff, loss, schemes):
    positions, ledger, species, _initial = trajectory
    times = ledger[:, 1]
    rule = plan["lineage"]
    grids_needed = {rule["anchor_tau"]}
    if loss is not None:
        width = rule["wide_pair_half_width_tau"]
        grids_needed.update({loss - rule["original_interval_tau"], loss, loss - width, loss + width})
    grids = {
        time: voxel_component(positions[np.flatnonzero(times == time).item()], length, plan["protocol"], cutoff)
        for time in grids_needed
    }
    summaries, details = {}, {}
    start = np.flatnonzero(times == rule["anchor_tau"]).item()
    observed = histories(positions[start:], length, schemes, rule["minimum_component_atoms"])
    t = times[start:]
    step = round(rule["original_interval_tau"] / (t[1] - t[0]))
    for scheme, data in observed.items():
        summaries[scheme], details[scheme] = {}, {}
        for name, stride in (("native", 1), ("archived_cadence", step)):
            if stride == 1 and name == "archived_cadence":
                continue
            summaries[scheme][name], details[scheme][name] = measure_timeline(
                data[::stride], t[::stride], grids, loss, rule)
    return summaries, details


def read_control(trajectory, length, plan):
    q, ledger, _species, _initial = trajectory
    times = ledger[:, 1]
    start = np.flatnonzero(times == plan["lineage"]["anchor_tau"]).item()
    cut = q[start:]
    data = histories(cut, length, {"main": plan["contact_schemes"]["main"]},
                     plan["lineage"]["minimum_component_atoms"])["main"]
    return {
        "samples_at_or_after_anchor": len(data),
        "samples_with_a_dense_component": sum(len(frame.sizes) > 0 for frame in data),
        "samples_with_a_winding_leader": sum(bool(frame.winding_axes[0]) if len(frame.sizes) else False
                                            for frame in data),
        "largest_components_at_anchor": data[0].sizes.tolist(),
        "winding_axes_at_anchor": data[0].winding_axes,
    }


def analyze(original, replay, out, registration):
    plan = load_plan(PLAN)
    verify_registration(ANALYSIS_INPUTS, read_object(ANALYSIS_INPUTS), registration)
    original_path = Path(plan["previous_archive"]) / "PLAN.json"
    previous = load_plan(original_path)
    cutoff = previous["schemes"]["main"]["threshold"]
    original_manifest = check_record(original_path, original / "record.json")
    replay_manifest = check_record(PLAN, replay / "record.json")
    old_record = read_object(original / "record.json")
    fresh_record = read_object(replay / "record.json")
    checks, cases, detail = {}, {}, {}
    for name, setup in plan["cases"].items():
        old_entry = old_record["cases"][name][-1]
        entry = fresh_record["cases"][name][-1]
        coarse = binary.load_binary(original, name, old_entry)
        data = coarse
        checks[name] = {"verified": False, "reason": entry["status"]}
        if entry["status"] == "completed":
            fine = binary.load_binary(replay, name, entry)
            checks[name] = compare_replay(coarse, fine, old_entry, entry)
            if checks[name]["verified"]:
                data = fine
        clock = data[1][:, 1]
        if setup["mode"] == "isolated":
            tail = data[1][clock >= plan["lineage"]["anchor_tau"]]
            checks[name]["no_heat_after_isolation"] = bool(np.all(tail[:, 5] == tail[0, 5]))
            energy = tail[:, 3] + tail[:, 4]
            checks[name]["max_energy_change_per_atom"] = float(np.abs(energy - energy[0]).max() / data[0].shape[1])
            if not checks[name]["no_heat_after_isolation"]:
                raise ValueError(f"Unexpected work on isolated branch {name}")
        cases[name], detail[name] = observe(data, setup["length"], plan, cutoff, plan["targets"].get(name),
                                            plan["contact_schemes"])
    controls = {}
    for name in plan["controls"]:
        data = binary.load_binary(original, name, old_record["cases"][name][-1])
        controls[name] = read_control(data, previous["cases"][name]["length"], plan)
    result = {
        "analysis_registration": registration, "source_archive": original_manifest, "replay_archive": replay_manifest,
        "replay_checks": checks, "cases": cases, "controls": controls,
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "lineages.json.gz").write_bytes(gzip.compress(
        json.dumps(detail, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    print(json.dumps({name: check["verified"] for name, check in checks.items()}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--analysis-at", required=True)
    args = parser.parse_args()
    analyze(args.original.resolve(), args.replay.resolve(), args.out.resolve(), args.analysis_at)


if __name__ == "__main__":
    main()
