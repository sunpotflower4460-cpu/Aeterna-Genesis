#!/usr/bin/env python3
"""e026 robustness (LAW.md audit 6): the winding accounting must be a topological invariant --
independent of the reading-loop radii, the daughter separation, and the shed-anti position. We
sweep those geometric choices and confirm (A) gives (+1, 0) and (B) gives (+1, +1) with a
conserved total (+1) every time."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e026_vessel_division import division as D  # noqa: E402


def _case(sep, R_daughter, R_both, R_all, shed_y):
    p = dict(D.DEFAULT)
    p.update({"sep": sep, "R_daughter": R_daughter, "R_both": R_both,
              "R_all": R_all, "shed_y": shed_y})
    N, n = p["N"], p["n"]
    phA = D._phase_of([(-sep, 0, 1)], N)
    A = (D._wind(phA, -sep, 0, R_daughter, N, n), D._wind(phA, sep, 0, R_daughter, N, n))
    phB = D._phase_of([(-sep, 0, 1), (sep, 0, 1), (0, shed_y, -1)], N)
    B = (D._wind(phB, -sep, 0, R_daughter, N, n), D._wind(phB, sep, 0, R_daughter, N, n),
         D._wind(phB, 0, 0, R_both, N, n), D._wind(phB, 0, 0, R_all, N, n))
    ok = (abs(A[0]) > 0.5 and abs(A[1]) < 0.5
          and abs(B[0]) > 0.5 and abs(B[1]) > 0.5
          and abs(B[2] - 2) < 0.5 and abs(B[3] - 1) < 0.5)
    return {"sep": sep, "R_daughter": R_daughter, "R_both": R_both, "R_all": R_all,
            "shed_y": shed_y, "A": [round(v, 2) for v in A], "B": [round(v, 2) for v in B],
            "ok": bool(ok)}


def simulate(quick=False):
    cases = [
        _case(18, 10, 32, 66, 50),      # canon
        _case(18, 8, 32, 66, 50),
        _case(18, 12, 30, 64, 50),
        _case(22, 10, 36, 70, 55),
    ]
    if not quick:
        cases += [_case(16, 9, 30, 60, 45), _case(20, 11, 34, 68, 60)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e026 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e026 robustness (winding accounting vs loop radii / separation / shed pos) ===")
    for c in r["cases"]:
        print("  sep=%s R_d=%s: A=%s B=%s ok=%s" % (c["sep"], c["R_daughter"], c["A"], c["B"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
