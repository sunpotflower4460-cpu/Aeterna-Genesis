"""Check pair prefixes, measure cohort retention and quantify the energy balance."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import sys

import numpy as np

from tools.study_record import check_record, load_plan, read_object

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261120-vortex-drive-stop"))
from loops import follow, frames, minimum_image


def reduce_tracks(tracks, period, ledger):
    cohort = [tr for tr in tracks if tr[0]["t"] <= 54 and tr[-1]["t"] >= 58]
    positions = {row[0]: np.array([period[0] / 2, period[1] / 2, row[1]]) for row in ledger}
    terminal = []
    for track in cohort:
        if track[-1]["t"] != 160:
            continue
        after = [pt for pt in track if pt["t"] >= 82]
        deltas = [minimum_image(np.subtract(b["center"], a["center"]), period) for a, b in zip(after[:-1], after[1:])]
        distances = [np.linalg.norm(minimum_image(np.subtract(pt["center"], positions[pt["t"]]), period))
                     for pt in after]
        terminal.append({
            "radius_at_58": next(pt["radius"] for pt in track if pt["t"] == 58),
            "radius_at_82": after[0]["radius"],
            "radius_at_160": after[-1]["radius"],
            "axial_displacement_82_to_160": float(sum(v[2] for v in deltas)),
            "min_center_distance_from_stop_site_82_to_160": float(min(distances)),
        })
    return {
        "cohort": len(cohort),
        "cohort_last_times": [tr[-1]["t"] for tr in cohort],
        "still_linked": {str(t): sum(tr[-1]["t"] >= t for tr in cohort) for t in (70, 82, 120, 160)},
        "terminal_cohort_members": terminal,
        "later_track_starts": [tr[0]["t"] for tr in tracks if len(tr) >= 3 and tr[0]["t"] > 82],
    }


def measure(data):
    pieces = frames(data)
    period = data["dx"] * data["shape"]
    ledger = data["ledger"]
    t, _, _, height, work, _, energy, mass, power = ledger.T
    observations, full = {}, {}
    for label, cutoff, stride in (("main", 0.5, 1), ("mask-025", 0.25, 1),
                                  ("mask-100", 1.0, 1), ("every-four", 0.5, 2)):
        # Anchor the decimation at the split. Include the initial and terminal frames.
        indices = np.arange(len(t)) if stride == 1 else np.r_[0, np.arange(1, len(t), 2), len(t) - 1]
        counts, tracks = follow([pieces[i] for i in indices], t[indices], period, cutoff)
        observations[label] = reduce_tracks(tracks, period, ledger)
        full[label] = {"counts": counts, "tracks": tracks}
    starts = {time: np.flatnonzero(t == time).item() for time in (58, 70, 82)}
    a, b, c = (starts[time] for time in (58, 70, 82))
    observations["budget"] = {
        "work_braking_window": float(work[b] - work[a]),
        "work_release_window": float(work[c] - work[b]),
        "work_after_82": float(work[-1] - work[c]),
        "max_abs_power_after_82": float(np.abs(power[c:]).max()),
        "max_abs_height_after_82": float(np.abs(height[c:]).max()),
        "energy_change_after_82": float(energy[-1] - energy[c]),
        "max_absolute_balance_residual": float(np.abs(energy - energy[0] - work).max()),
        "max_relative_mass_drift": float(np.abs(mass / mass[0] - 1).max()),
        "max_energy": float(energy.max()),
    }
    return observations, full


def compare(evidence, names, attempts, time):
    reference = names[0]
    lengths = {}
    hashes = {attempts[name][f"state_t{time}_sha256"] for name in names}
    if len(hashes) != 1:
        raise ValueError(f"field mismatch at t={time} for {names}")
    for name in names:
        with np.load(evidence / f"{reference}.npz") as a, np.load(evidence / f"{name}.npz") as b:
            i = np.flatnonzero(a["ledger"][:, 0] == time).item()
            for kind in ("ledger", "faces"):
                left, right = a[kind], b[kind]
                if kind == "faces":
                    left, right = left[left[:, 0] <= i], right[right[:, 0] <= i]
                else:
                    left, right = left[:i + 1], right[:i + 1]
                if not np.array_equal(left, right):
                    raise ValueError(f"measurement prefix mismatch at t={time}: {reference}, {name}")
            lengths[name] = i + 1
    return lengths


def analyze(evidence, out):
    plan = load_plan(HERE / "PLAN.json")
    record_path = evidence / "record.json"
    manifest = check_record(HERE / "PLAN.json", record_path)
    record = read_object(record_path)
    grouped = defaultdict(list)
    results, tracks, attempts, pairs = {}, {}, {}, {}
    for name, case in plan["cases"].items():
        attempt = record["cases"][name][-1]
        if attempt["status"] == "completed":
            with np.load(evidence / (name + ".npz")) as data:
                results[name], tracks[name] = measure(data)
            attempts[name] = attempt
            grouped[(case["variant"], case["seed"])].append(name)
    for (variant, seed), names in grouped.items():
        stopped = [name for name in names if not name.endswith("-continue")]
        pairs[f"{variant}-{seed}"] = {
            "prefix_to_58": compare(evidence, names, attempts, 58) if len(names) >= 2 else {},
            "prefix_to_70": compare(evidence, stopped, attempts, 70) if len(stopped) >= 2 else {},
        }
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(
        {"manifest": manifest, "prefixes": pairs, "flows": results}, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "tracking.json.gz").write_bytes(gzip.compress(json.dumps(tracks, separators=(",", ":"), allow_nan=False)
                                                         .encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
