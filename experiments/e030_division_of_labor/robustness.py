#!/usr/bin/env python3
"""e030 robustness (LAW.md audit 6): the division-of-labor finding must survive a fresh seed set and a
different group geometry. Absolute specialist fractions drift a little; what must not move is: a convex
return gives strong specialization (>0.6) with universal germ-soma coexistence, far above the concave
case. We sweep seeds and group size and confirm."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e030_division_of_labor import division_of_labor as DL  # noqa: E402


def _case(seeds, G, n):
    p = dict(DL.DEFAULT)
    p.update({"seeds": seeds, "G": G, "n": n, "T": 400})
    conv = float(np.mean([DL._run(p["a_convex"], p, s)["specialist_frac"] for s in seeds]))
    conc = float(np.mean([DL._run(p["a_concave"], p, s)["specialist_frac"] for s in seeds]))
    both = float(np.mean([DL._run(p["a_convex"], p, s)["both_roles"] for s in seeds]))
    ok = conv > 0.6 and conv > 1.5 * conc and both > 0.9
    return {"seeds": seeds, "G": G, "n": n, "spec_convex": round(conv, 3),
            "spec_concave": round(conc, 3), "both_convex": round(both, 3), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case([10, 11, 12], 100, 16)] if quick else [
        _case([10, 11, 12], 100, 16), _case([20, 21, 22], 60, 24), _case([30, 31, 32], 140, 12)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e030 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e030 robustness (division of labor vs seed / group geometry) ===")
    for c in r["cases"]:
        print("  seeds=%s G=%s n=%s: convex=%s concave=%s both=%s ok=%s"
              % (c["seeds"], c["G"], c["n"], c["spec_convex"], c["spec_concave"], c["both_convex"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
