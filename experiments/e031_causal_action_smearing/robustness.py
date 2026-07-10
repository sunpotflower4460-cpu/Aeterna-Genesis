#!/usr/bin/env python3
"""e031 robustness (LAW.md audit 6): the obstacle + cure must survive a fresh seed batch and the smearing
scale. The raw BD action's std grows with N and the smeared std is smaller by a large factor -- these must
hold across seed batches and for a couple of eps values (the cure is not a single tuned eps)."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e031_causal_action_smearing import smearing as SM  # noqa: E402


def _case(seeds, eps):
    Ns = [200, 800]
    ratios = []
    for N in Ns:
        raws, smes = [], []
        for s in seeds:
            R = SM._relation(*SM._sprinkle_diamond(N, s))
            raws.append(SM._bd_raw(R))
            smes.append(SM._bd_smeared(R, eps))
        ratios.append(np.std(raws) / max(np.std(smes), 1e-9))
    damp = ratios[-1]
    ok = all(r > 3.0 for r in ratios) and damp > 5.0
    return {"seeds": seeds, "eps": eps, "ratio_small_N": round(float(ratios[0]), 1),
            "damp_factor": round(float(damp), 1), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case([10, 11, 12, 13], 0.15)] if quick else [
        _case([10, 11, 12, 13], 0.15), _case([20, 21, 22, 23], 0.10), _case([30, 31, 32, 33], 0.20)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e031 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e031 robustness (fluctuation obstacle + smearing cure vs seed / eps) ===")
    for c in r["cases"]:
        print("  seeds=%s eps=%s: raw/smeared ratio(smallN)=%s damp(bigN)=%sx ok=%s"
              % (c["seeds"], c["eps"], c["ratio_small_N"], c["damp_factor"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
