#!/usr/bin/env python3
"""e018 robustness (LAW.md audit 6): the three-arm result (intact alive; cut any
arm -> death) must survive changing the rates. We sweep (k1, k2, dM) and check
intact coexistence and death on each knockout stay true."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e018_membrane_vesicle import vessel_membrane as e018  # noqa: E402


def _case(k1, k2, dM, steps):
    p = dict(e018.DEFAULT)
    p.update({"k1": k1, "k2": k2, "dM": dM, "steps": steps})
    intact = e018._alive(e018.integrate(p))
    dead_met = not e018._alive(e018.integrate(p, cut_metabolism=p["cut_time"]))
    dead_mem = not e018._alive(e018.integrate(p, cut_membrane=p["cut_time"]))
    dead_drv = not e018._alive(e018.integrate(p, s=0.0))
    return {"k1": k1, "k2": k2, "dM": dM, "intact_alive": intact,
            "dies_cut_metabolism": dead_met, "dies_cut_membrane": dead_mem,
            "dies_cut_drive": dead_drv,
            "pass": bool(intact and dead_met and dead_mem and dead_drv)}


def run_sweep(quick=False):
    if quick:
        cases = [(3.0, 1.0, 0.2, 5000), (4.0, 1.0, 0.2, 5000)]
    else:
        cases = [(3.0, 1.0, 0.2, 8000), (4.0, 1.0, 0.2, 8000),
                 (3.0, 1.5, 0.2, 8000), (3.0, 1.0, 0.3, 8000),
                 (2.5, 1.0, 0.15, 8000)]
    return [_case(*c) for c in cases]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e018 robustness")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    rows = run_sweep(quick=args.quick)
    for r in rows:
        print("  k1=%.1f k2=%.1f dM=%.2f: intact=%s cuts_die=%s/%s/%s  %s"
              % (r["k1"], r["k2"], r["dM"], r["intact_alive"], r["dies_cut_metabolism"],
                 r["dies_cut_membrane"], r["dies_cut_drive"], "PASS" if r["pass"] else "FAIL"))
    npass = sum(r["pass"] for r in rows)
    ok = npass == len(rows)
    print("ROBUSTNESS: %s (%d/%d cases PASS)" % ("GREEN" if ok else "MIXED", npass, len(rows)))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump({"cases": rows}, f, indent=2)
        print("wrote robustness.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
