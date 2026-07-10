#!/usr/bin/env python3
"""e038 robustness (LAW.md audit 6): the de novo climb must survive a different mutation rate and seed.
What must not move: seeded at a LOW uniform trait (no standing variation), the mean trait still climbs well
above the seed and the distribution stays continuous. Not put in."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e038_field_objtrack import objtrack as O  # noqa: E402


def _case(mut, seed):
    p = dict(O.DEFAULT)
    p.update({"mut": mut, "seed": seed, "N": 80, "steps": 16000})
    Ha, ta, Va = O._run(p, seed_tau=p["seed_tau"], moving=False)
    m = Va > 0.15
    hist, _ = np.histogram(ta[m], bins=p["hist_bins"], range=(0, 1))
    occ = int((hist > 0).sum())
    ok = (Ha[-1][1] > 0.6 and occ >= 4)
    return {"mut": mut, "seed": seed, "trait_start": Ha[0][1], "trait_end": Ha[-1][1],
            "occupied_bins": occ, "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(0.035, 1)] if quick else [_case(0.035, 1), _case(0.02, 2), _case(0.05, 3)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e038 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e038 robustness (de novo climb vs mutation rate / seed) ===")
    for c in r["cases"]:
        print("  mut=%s seed=%s: trait %s -> %s occupied=%s ok=%s"
              % (c["mut"], c["seed"], c["trait_start"], c["trait_end"], c["occupied_bins"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
