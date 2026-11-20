"""Re-read each case using the prior argon contact graph instead of a density grid.

Secondary analysis fixed after launch and before reviewing any mixture trajectories.
It uses the original contact graph constants, 2-tau output, 240-tau anchor and
320–500-tau window with the same ten-atom requirement and transit conditions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

from measure import PLAN, count_events, fractions, geometry, load_binary
from tools.study_record import check_record, load_plan, read_object

sys.path.append(str(PLAN.parent.parent / "20261120-argon-interface-turnover"))
from contact_check import classify_contacts


def measure(evidence, plan):
    record_path = evidence / "record.json"
    check_record(PLAN, record_path)
    record = read_object(record_path)
    p = plan["protocol"]
    result = {}
    for name, case in plan["cases"].items():
        attempt = record["cases"][name][-1]
        if attempt["status"] != "completed":
            continue
        positions, ledger, species, _ = load_binary(evidence, name, attempt)
        times = ledger[:, 1]
        start = np.flatnonzero(times == p["fork"]).item() - p["residence_frames"] + 1
        positions, times = positions[start:], times[start:]
        phase = np.zeros(positions.shape[:2], dtype=np.uint8)
        rows = []
        previous = np.zeros(len(species), dtype=bool)
        for i, (position, t) in enumerate(zip(positions, times)):
            members, phase[i], bounded = classify_contacts(position, case["length"])
            union = np.count_nonzero(members | previous)
            overlap = float(np.count_nonzero(members & previous) / union) if union else None
            rows.append({"t": float(t), "bounded": bounded, "overlap": overlap})
            previous = members

        anchor, end = geometry.mine_track(rows, p["fork"], p["overlap_min"])
        total = np.column_stack([(phase == k).sum(axis=1) for k in (1, 2)])
        heavy = np.column_stack([(phase[:, species == 1] == k).sum(axis=1) for k in (1, 2)])
        window = (times >= p["comparison_start"]) & (np.arange(len(times)) <= (end if end is not None else -1))
        valid = window & (total >= p["minimum_core_count"]).all(axis=1)
        result[name] = {
            "track_through_tau": rows[end]["t"] if end is not None else None,
            "window_valid_frames": int(valid.sum()),
            "window_complete": end == len(times) - 1 and bool(valid[times >= p["comparison_start"]].all()),
            "window_composition": fractions(total[valid], heavy[valid]),
            "transits": None,
        }
        if end is not None:
            exchanges = geometry.exchange(phase, positions, times, anchor, end, p["residence_frames"],
                                          case["length"], p["minimum_displacement"])["events"]
            late = [event for event in exchanges if event["from_t"] >= p["comparison_start"]]
            result[name]["transits"] = count_events(late, species, phase, window & (np.arange(len(times)) < end),
                                                  p["sample"], displaced=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = measure(args.evidence.resolve(), load_plan(PLAN))
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
