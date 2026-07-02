#!/usr/bin/env python3
"""e017 robustness (LAW.md audit 6): the recovered Ra_c must converge with grid
resolution N and keep no-slip > free-slip. We sweep N and check both critical
numbers stay near the textbook values and in the right order."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e017_walled_convection import rb_linear_stability as e017  # noqa: E402


def run_sweep(quick=False):
    Ns = [48, 60] if quick else [48, 56, 64, 72]
    rows = []
    for N in Ns:
        ns = e017.critical("noslip", N)
        fs = e017.critical("freeslip", N)
        rows.append({"N": N, "Ra_noslip": ns["Ra_c"], "err_noslip": ns["err_pct"],
                     "Ra_freeslip": fs["Ra_c"], "err_freeslip": fs["err_pct"],
                     "order_ok": bool(ns["Ra_c"] > fs["Ra_c"]),
                     "pass": bool(ns["err_pct"] < 0.6 and fs["err_pct"] < 0.3 and ns["Ra_c"] > fs["Ra_c"])})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="e017 robustness")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    rows = run_sweep(quick=args.quick)
    for r in rows:
        print("  N=%3d: no-slip %.1f (%.2f%%)  free-slip %.1f (%.2f%%)  order_ok=%s  %s"
              % (r["N"], r["Ra_noslip"], r["err_noslip"], r["Ra_freeslip"], r["err_freeslip"],
                 r["order_ok"], "PASS" if r["pass"] else "FAIL"))
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
