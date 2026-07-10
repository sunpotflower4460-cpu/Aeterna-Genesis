#!/usr/bin/env python3
"""e035 robustness (LAW.md audit 6): the plateau->limit-cycle picture must survive changes to the mortality m
and the half-saturation H0 -- which MOVE the Hopf point. What must not move: below the (shifted) Hopf point
the system plateaus, above it it oscillates, and the measured oscillation onset still matches the analytic
Hopf point (Jacobian trace=0). The RELATION (onset = Hopf) is robust even though K_c itself shifts."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e035_field_red_queen import red_queen as RQ  # noqa: E402


def _case(m, H0):
    p = dict(RQ.DEFAULT)
    p.update({"m": m, "H0": H0, "Ks": list(np.round(np.linspace(0.4, 1.6, 13), 3)), "T": 8000})
    hopf = RQ._analytic_hopf(p)
    KK = np.array(p["Ks"])
    AA = np.array([RQ._run(K, p)[0] for K in KK])
    onset = float(np.interp(p["amp_threshold"], AA, KK))
    amp_below = float(np.interp(hopf - 0.15, KK, AA))     # amplitude just below the Hopf point
    amp_above = float(np.interp(hopf + 0.35, KK, AA))     # amplitude well above it
    ok = (abs(onset - hopf) < 0.12 and amp_below < 0.06 and amp_above > 0.25)
    return {"m": m, "H0": H0, "hopf": round(hopf, 3), "onset": round(onset, 3),
            "amp_below": round(amp_below, 3), "amp_above": round(amp_above, 3), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(0.4, 0.3)] if quick else [_case(0.4, 0.3), _case(0.35, 0.3), _case(0.4, 0.35)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e035 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e035 robustness (onset = analytic Hopf under shifts of mortality m / half-saturation H0) ===")
    for c in r["cases"]:
        print("  m=%s H0=%s: hopf=%s onset=%s amp_below=%s amp_above=%s ok=%s"
              % (c["m"], c["H0"], c["hopf"], c["onset"], c["amp_below"], c["amp_above"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
