#!/usr/bin/env python3
"""Robustness sweep for e002 (LAW.md audit 6).

Re-runs both two-vortex cases across several initial separations:
  same-sign     d in {6, 7, 9}   -> must co-rotate (rotation grows, no drift)
  opposite-sign d in {12, 16, 20} -> must translate (centroid drifts, no rotation)

Every case is run to the SAME generous step budget (N_REAL); the self-detecting
clean-window guard in simulate_case ends each run at its own physical limit. So
the clean window -- and hence the total rotation/translation -- is set by the
physics per separation, not by a hand-tuned step count.

Consequence (honest): wider same-sign pairs expand and degrade FASTER, so their
clean window is SHORTER and their absolute rotation is smaller (d=6 ~ 600 deg,
d=9 ~ 100 deg). Audit 6 therefore tests the CHARACTER of the motion (co-rotation
vs translation, and the monotonic d-trend), not a fixed magnitude. The pass
thresholds match the main evaluate() (opposite drift > 15), except the same-sign
rotation floor is 60 deg rather than 180 deg -- a wider pair's clean window does
not last long enough for half a turn, yet its co-rotation is unmistakable.

Writes robustness.json and prints a table copied into AUDIT.md.
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from run import COMMON, simulate_case  # noqa: E402

SAME_D = [6.0, 7.0, 9.0]
OPP_D = [12.0, 16.0, 20.0]
N_REAL = 8000  # generous budget; the clean-window guard terminates each run
COMMON_SAMPLE = COMMON["sample"]


def _same_ok(r):
    return (r["rotation_monotonic"] and r["rotation_final_deg"] > 60.0
            and r["centroid_drift_max"] < 3.0 and r["charge_set"] == [1]
            and r["circulation_quantized"] and r["energy_drift"] < 1e-4)


def _opp_ok(r):
    return (abs(r["rotation_final_deg"]) < 40.0 and r["centroid_monotonic"]
            and r["centroid_drift_final"] > 15.0 and r["charge_set"] == [-1, 1]
            and r["circulation_quantized"] and r["energy_drift"] < 1e-4)


def main():
    rows = []
    all_pass = True
    print(f"{'case':>9} {'d':>4} | {'window':>6} {'sep_mean':>8} {'rot_deg':>8} "
          f"{'drift':>6} | result")
    print("-" * 62)
    for d in SAME_D:
        r = simulate_case((1, 1), d, N_REAL)
        ok = _same_ok(r)
        all_pass &= ok
        window = r["n_samples"] * COMMON_SAMPLE
        rows.append({"case": "same", "d": d, "window_steps": window,
                     "sep_mean": r["separation_mean"],
                     "rotation_final_deg": r["rotation_final_deg"],
                     "centroid_drift_max": r["centroid_drift_max"], "pass": ok})
        print(f"{'same':>9} {d:>4.0f} | {window:>6d} {r['separation_mean']:>8.2f} "
              f"{r['rotation_final_deg']:>8.1f} {r['centroid_drift_max']:>6.2f} | "
              f"{'PASS' if ok else 'FAIL'}")
    for d in OPP_D:
        r = simulate_case((1, -1), d, N_REAL)
        ok = _opp_ok(r)
        all_pass &= ok
        window = r["n_samples"] * COMMON_SAMPLE
        rows.append({"case": "opposite", "d": d, "window_steps": window,
                     "sep_mean": r["separation_mean"],
                     "rotation_final_deg": r["rotation_final_deg"],
                     "centroid_drift_final": r["centroid_drift_final"], "pass": ok})
        print(f"{'opposite':>9} {d:>4.0f} | {window:>6d} {r['separation_mean']:>8.2f} "
              f"{r['rotation_final_deg']:>8.1f} {r['centroid_drift_final']:>6.2f} | "
              f"{'PASS' if ok else 'FAIL'}")
    print("-" * 62)
    print(f"OVERALL: {'PASS (audit 6 satisfied -> e002 GREEN)' if all_pass else 'FAIL'}")

    out = {"cases": rows, "all_pass": all_pass}
    out_path = os.path.join(os.path.dirname(__file__), "robustness.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
