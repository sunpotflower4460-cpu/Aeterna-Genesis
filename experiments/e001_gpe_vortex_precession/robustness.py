#!/usr/bin/env python3
"""Robustness sweep for e001 (LAW.md audit 6).

Re-runs the GPE vortex-precession experiment across R0 in {6, 10, 14} and
Omega in {0.05, 0.06, 0.08}. The emergence is robust if, for every parameter
set, the vortex keeps precessing (cumulative rotation grows monotonically and
clears a sensible fraction of a turn) while the radius stays nearly constant
and the circulation stays quantized at +1.

Writes robustness.json and prints a table that is copied into AUDIT.md.
Note: for the precession *rate*, smaller R0 (closer to centre) and larger
Omega precess faster -- so the rotation total varies by design; what must
hold for every case is monotonic, persistent precession at constant radius.
"""

import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from run import simulate  # noqa: E402

R0_VALUES = [6.0, 10.0, 14.0]
OMEGA_VALUES = [0.05, 0.06, 0.08]


def _persists(result):
    """A case passes audit 6 if precession persists at near-constant radius."""
    return (
        result["rotation_monotonic"]
        and abs(result["cumulative_rotation_deg"]) > 90.0
        and result["radius_spread"] < 2.5
        and result["charge"] == 1
        and result["circulation_quantized"]
        and result["energy_drift"] < 1e-4
    )


def main():
    rows = []
    all_pass = True
    print(f"{'R0':>4} {'Omega':>6} | {'r_mean':>7} {'r_spread':>8} "
          f"{'rot_deg':>8} {'mono':>5} {'q':>2} | result")
    print("-" * 62)
    for R0 in R0_VALUES:
        for Om in OMEGA_VALUES:
            res = simulate({"R0": R0, "Omega": Om})
            ok = _persists(res)
            all_pass = all_pass and ok
            rows.append({
                "R0": R0, "Omega": Om,
                "radius_mean": res["radius_mean"],
                "radius_spread": res["radius_spread"],
                "cumulative_rotation_deg": res["cumulative_rotation_deg"],
                "rotation_monotonic": res["rotation_monotonic"],
                "charge": res["charge"],
                "circulation_quantized": res["circulation_quantized"],
                "energy_drift": res["energy_drift"],
                "pass": ok,
            })
            print(f"{R0:>4.0f} {Om:>6.3f} | {res['radius_mean']:>7.2f} "
                  f"{res['radius_spread']:>8.2f} "
                  f"{res['cumulative_rotation_deg']:>8.1f} "
                  f"{str(res['rotation_monotonic']):>5} {res['charge']:>2} | "
                  f"{'PASS' if ok else 'FAIL'}")
    print("-" * 62)
    print(f"OVERALL: {'PASS (audit 6 satisfied -> e001 GREEN)' if all_pass else 'FAIL'}")

    out = {"cases": rows, "all_pass": all_pass}
    out_path = os.path.join(os.path.dirname(__file__), "robustness.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
