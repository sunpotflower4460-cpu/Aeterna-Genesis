#!/usr/bin/env python3
"""e039 robustness (LAW.md audit 6): the differentiation must survive a different morphogen decay k (gradient
steepness) and a different Turing seed. What must not move: the French-flag domains stay 3 and spatially
ordered; the Turing activator std still grows from ~uniform into a self-organized pattern. Not put in."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e039_field_differentiation import differentiation as D  # noqa: E402


def _case(mor_k, seed):
    p = dict(D.DEFAULT)
    p.update({"mor_k": mor_k, "seed": seed, "N": 100, "mor_steps": 3500, "tur_steps": 7000})
    N = p["N"]
    M = D._morphogen(p)
    fate = np.where(M > p["th1"], 0, np.where(M > p["th2"], 1, 2))
    col = fate[:, N // 2]
    doms = [int((col == f).sum()) for f in range(3)]
    ordered = bool(all(d > 0 for d in doms) and int(np.argmax(col == 0)) < int(np.argmax(col == 2)))
    a, var = D._turing(p)
    ok = ordered and var[0] < 0.1 and var[-1] > 0.5
    return {"mor_k": mor_k, "seed": seed, "domains": doms, "ordered": ordered,
            "turing_std": [var[0], var[-1]], "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(0.006, 1)] if quick else [_case(0.006, 1), _case(0.004, 2), _case(0.009, 3)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e039 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e039 robustness (ordered domains + Turing pattern vs morphogen k / seed) ===")
    for c in r["cases"]:
        print("  k=%s seed=%s: domains=%s ordered=%s turing_std=%s ok=%s"
              % (c["mor_k"], c["seed"], c["domains"], c["ordered"], c["turing_std"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
