#!/usr/bin/env python3
"""Robustness sweep for e003 (LAW.md audit 6).

Re-runs the vortex-ring experiment across initial radii R in {8, 10, 12}. The
emergence is robust if, for every R, the ring (a) propagates monotonically at
(b) near-constant radius with (c) quantized circulation, AND (d) the speed
DECREASES with R -- the hallmark of the vortex-ring self-induced velocity
v ~ (1/2R)[ln(8R/xi) - c]. A smaller ring chasing its own tail moves faster.

Writes robustness.json and prints a table copied into AUDIT.md.
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from run import simulate  # noqa: E402

R_VALUES = [8.0, 10.0, 12.0]


def _ok(r):
    return (r["propagation_distance"] > 4.0 and r["propagation_monotonic"]
            and r["radius_spread"] < 0.3 * r["radius_mean"]
            and r["circulation_quantized"] and r["energy_drift"] < 1e-3)


def main():
    rows = []
    all_pass = True
    print(f"{'R':>4} | {'travel':>7} {'speed/step':>10} {'R_mean':>7} "
          f"{'spread':>6} {'mono':>5} | result")
    print("-" * 58)
    for R in R_VALUES:
        r = simulate({"R": R})
        ok = _ok(r)
        all_pass &= ok
        rows.append({"R": R, "propagation_distance": r["propagation_distance"],
                     "speed_per_step": r["speed_per_step"],
                     "radius_mean": r["radius_mean"],
                     "radius_spread": r["radius_spread"],
                     "monotonic": r["propagation_monotonic"], "pass": ok})
        print(f"{R:>4.0f} | {r['propagation_distance']:>7.1f} "
              f"{r['speed_per_step']:>10.4f} {r['radius_mean']:>7.2f} "
              f"{r['radius_spread']:>6.2f} {str(r['propagation_monotonic']):>5} | "
              f"{'PASS' if ok else 'FAIL'}")
    print("-" * 58)
    # speed must decrease with R (smaller ring faster) -- net decrease across the
    # sweep (deterministic; a tiny per-step margin guards last-digit FFT diffs).
    speeds = [row["speed_per_step"] for row in rows]
    trend = all(speeds[i] >= speeds[i + 1] - 1e-4 for i in range(len(speeds) - 1)) \
        and speeds[0] > speeds[-1]
    all_pass &= trend
    print("smaller-ring-faster trend (v decreases with R): %s" % trend)

    # Box-size convergence: a SELF-INDUCED speed is box-independent once L is big
    # enough; an image/boundary-sheet-driven speed would keep changing with L.
    # We verify v(L=64) ~ v(L=80) (converged), ruling out image domination.
    print("-" * 58)
    print("box-size convergence (R=10): self-induced => v converges with L")
    box = []
    for L in (56, 64, 80):
        r = simulate({"L": L, "R": 10.0, "n_real": 1200})
        box.append({"L": L, "speed_per_step": r["speed_per_step"]})
        print(f"  L={L:>3d}  v/step={r['speed_per_step']:.4f}")
    v64 = next(b["speed_per_step"] for b in box if b["L"] == 64)
    v80 = next(b["speed_per_step"] for b in box if b["L"] == 80)
    converged = abs(v64 - v80) <= 0.1 * v64        # within 10% => box-converged
    all_pass &= converged
    print("  v(64) ~ v(80) (self-induced, image ruled out): %s" % converged)
    print("OVERALL: %s" % ("PASS (audit 6 -> e003 GREEN)" if all_pass else "FAIL"))

    out = {"cases": rows, "speed_decreases_with_R": trend,
           "box_convergence": box, "self_induced_box_converged": converged,
           "all_pass": all_pass}
    with open(os.path.join(_THIS_DIR, "robustness.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote robustness.json")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
