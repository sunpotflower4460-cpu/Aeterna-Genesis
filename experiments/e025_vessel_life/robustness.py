#!/usr/bin/env python3
"""e025 robustness (LAW.md audit 6): the vessel's gate SIGNS/CONTRASTS must survive seed and grid
(Nr) changes. Absolute bulk levels are floors; what must not move is: fueled bulk stays high with
winding +/-1; a fuel cut collapses the bulk; an anti-vortex collapses the bulk ONLY under closure.
We sweep seeds (short runs) and confirm."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e025_vessel_life import complete as C       # noqa: E402
from experiments.e025_vessel_life import autopoietic as A     # noqa: E402


def _complete_case(seed, Nr):
    p = dict(C.DEFAULT)
    p.update({"seed": seed, "Nr": Nr, "T": 80.0, "fuel_cut": 40.0, "event_t": 26.0})
    rng = np.random.default_rng(seed)
    b_live, w_live, _ = C.run(p, rng)
    b_fuel, _, _ = C.run(p, rng, fuel_cut=p["fuel_cut"])
    b_anti, w_anti, _ = C.run(p, rng, anti=True)
    ok = (b_live > 0.5 and abs(w_live) > 0.5 and b_fuel < 0.2
          and abs(w_anti) < 0.5 and b_anti > 0.5)
    return {"seed": seed, "Nr": Nr, "bulk_live": round(b_live, 2), "bulk_fuel": round(b_fuel, 2),
            "bulk_anti": round(b_anti, 2), "wind_anti": round(w_anti, 2), "ok": bool(ok)}


def _closure_case(seed, Nr):
    p = dict(A.DEFAULT)
    p.update({"seed": seed, "Nr": Nr, "T": 80.0, "fuel_cut": 40.0, "event_t": 26.0})
    rng = np.random.default_rng(seed)
    b_open, _, _ = A.run(p, rng, anti=True, closure=False)
    b_closed, _, _ = A.run(p, rng, anti=True, closure=True)
    ok = (b_open > 0.5 and b_closed < 0.2)
    return {"seed": seed, "Nr": Nr, "bulk_open": round(b_open, 2),
            "bulk_closed": round(b_closed, 2), "ok": bool(ok)}


def simulate(quick=False):
    seeds = [0, 1] if quick else [0, 1, 2]
    complete = [_complete_case(s, 300) for s in seeds]
    closure = [_closure_case(s, 300) for s in seeds]
    return {
        "complete": complete, "closure": closure,
        "complete_all_ok": all(c["ok"] for c in complete),
        "closure_all_ok": all(c["ok"] for c in closure),
        "robust": bool(all(c["ok"] for c in complete + closure)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e025 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e025 robustness (gate signs/contrasts vs seed / Nr) ===")
    print("  complete all ok: %s" % r["complete_all_ok"])
    print("  closure all ok:  %s" % r["closure_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
