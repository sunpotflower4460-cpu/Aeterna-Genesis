#!/usr/bin/env python3
"""Robustness sweep for e002 (LAW.md audit 6).

Re-runs both two-vortex cases across several initial separations:
  same-sign     d in {6, 7, 9}   -> must co-rotate (rotation grows, no drift)
  opposite-sign d in {12, 16, 20} -> must translate (centroid drifts, no rotation)

The emergence is robust if the QUALITATIVE behaviour (co-rotation vs
translation) holds for every separation. The rate changes with d -- closer
same-sign pairs orbit faster, wider dipoles translate slower -- so the totals
vary by design; what must hold is the character of the motion.

Writes robustness.json and prints a table copied into AUDIT.md.
"""

import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from run import simulate_case  # noqa: E402

SAME_D = [6.0, 7.0, 9.0]
OPP_D = [12.0, 16.0, 20.0]
SAME_STEPS = 3000
OPP_STEPS = 4000


def _same_ok(r):
    return (r["rotation_monotonic"] and r["rotation_final_deg"] > 60.0
            and r["centroid_drift_max"] < 3.0 and r["charge_set"] == [1]
            and r["circulation_quantized"] and r["energy_drift"] < 1e-4)


def _opp_ok(r):
    return (abs(r["rotation_final_deg"]) < 40.0 and r["centroid_monotonic"]
            and r["centroid_drift_final"] > 5.0 and r["charge_set"] == [-1, 1]
            and r["circulation_quantized"] and r["energy_drift"] < 1e-4)


def main():
    rows = []
    all_pass = True
    print(f"{'case':>9} {'d':>4} | {'sep_mean':>8} {'rot_deg':>8} "
          f"{'drift':>6} | result")
    print("-" * 52)
    for d in SAME_D:
        r = simulate_case((1, 1), d, SAME_STEPS)
        ok = _same_ok(r)
        all_pass &= ok
        rows.append({"case": "same", "d": d, "sep_mean": r["separation_mean"],
                     "rotation_final_deg": r["rotation_final_deg"],
                     "centroid_drift_max": r["centroid_drift_max"], "pass": ok})
        print(f"{'same':>9} {d:>4.0f} | {r['separation_mean']:>8.2f} "
              f"{r['rotation_final_deg']:>8.1f} {r['centroid_drift_max']:>6.2f} | "
              f"{'PASS' if ok else 'FAIL'}")
    for d in OPP_D:
        r = simulate_case((1, -1), d, OPP_STEPS)
        ok = _opp_ok(r)
        all_pass &= ok
        rows.append({"case": "opposite", "d": d, "sep_mean": r["separation_mean"],
                     "rotation_final_deg": r["rotation_final_deg"],
                     "centroid_drift_final": r["centroid_drift_final"], "pass": ok})
        print(f"{'opposite':>9} {d:>4.0f} | {r['separation_mean']:>8.2f} "
              f"{r['rotation_final_deg']:>8.1f} {r['centroid_drift_final']:>6.2f} | "
              f"{'PASS' if ok else 'FAIL'}")
    print("-" * 52)
    print(f"OVERALL: {'PASS (audit 6 satisfied -> e002 GREEN)' if all_pass else 'FAIL'}")

    out = {"cases": rows, "all_pass": all_pass}
    out_path = os.path.join(os.path.dirname(__file__), "robustness.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
