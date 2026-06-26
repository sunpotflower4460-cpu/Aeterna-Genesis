#!/usr/bin/env python3
"""e013 robustness (LAW.md audit 6): the dead-core / inner-b-vs-Pe result must
survive changing the consumption k, decay m, cell number nroll, and box L.

For each case we re-run the no-flow and a strong-flow simulation and check that
(a) the interior is far deader without flow, and (b) inner biomass rises with
flow. The qualitative "circulation is load-bearing inside" must not be fragile.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e013_vessel_content import run as e013  # noqa: E402


def _case(L, k, m, nroll, U_hi, steps):
    p = dict(e013.DEFAULT)
    p.update({"L": L, "k": k, "m": m, "nroll": nroll, "steps": steps})
    _, b0 = e013.simulate_one(p, 0.0)
    _, bh = e013.simulate_one(p, U_hi)
    i0 = e013._metrics(b0, p["inner_frac"])["inner_b"]
    ih = e013._metrics(bh, p["inner_frac"])["inner_b"]
    dead = i0 < 0.2 * (ih + 1e-12)
    rises = ih > 5 * (i0 + 1e-9)
    return {"L": L, "k": k, "m": m, "nroll": nroll,
            "inner_no_flow": round(i0, 5), "inner_flow": round(ih, 5),
            "dead_core": bool(dead), "rises_with_flow": bool(rises),
            "pass": bool(dead and rises)}


def run_sweep(quick=False):
    if quick:
        cases = [(48, 1.0, 0.2, 2, 8.0, 3000), (48, 2.0, 0.2, 2, 8.0, 3000)]
    else:
        cases = [(64, 1.0, 0.2, 2, 8.0, 6000),
                 (64, 2.0, 0.2, 2, 8.0, 6000),
                 (64, 1.0, 0.4, 2, 8.0, 6000),
                 (64, 1.0, 0.2, 3, 8.0, 6000),
                 (80, 1.0, 0.2, 2, 8.0, 6000)]
    return [_case(*c) for c in cases]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e013 robustness")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    rows = run_sweep(quick=args.quick)
    for r in rows:
        print("  L=%3d k=%.1f m=%.1f nroll=%d: inner %.5f(no) -> %.5f(flow)  %s"
              % (r["L"], r["k"], r["m"], r["nroll"], r["inner_no_flow"],
                 r["inner_flow"], "PASS" if r["pass"] else "FAIL"))
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
