#!/usr/bin/env python3
"""e029 robustness (LAW.md audit 6): the FRONTIER findings must survive a fresh set of seeds and a grid
change. The coevolution ensemble facts (static plateaus / demand rises / coevolution keeps climbing) and
the major-transition facts (individual collapses / group rescues / bottleneck tightens) must hold under a
shifted seed set and a different group size. Individual arms-race runs are variable, so we check the same
ENSEMBLE gates on a different seed batch, not run-by-run."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e029_openended_frontier import coevolution as CO       # noqa: E402
from experiments.e029_openended_frontier import major_transition as MT   # noqa: E402


def _coev_case(seeds):
    p = dict(CO.DEFAULT)
    p.update({"seeds": seeds, "T": 450})
    saved = CO.DEFAULT
    try:
        CO.DEFAULT = p
        r = CO.simulate(quick=False)
    finally:
        CO.DEFAULT = saved
    _, checks = CO.evaluate(r, quick=False)
    return {"seeds": seeds, "median_coev_len": r["median_coev_final_len"],
            "median_static_len": r["median_static_final_len"], "ok": bool(all(checks.values()))}


def _mt_case(seeds, n):
    p = dict(MT.DEFAULT)
    p.update({"seeds": seeds, "n": n, "T": 200})
    saved = MT.DEFAULT
    try:
        MT.DEFAULT = p
        r = MT.simulate(quick=False)
    finally:
        MT.DEFAULT = saved
    _, checks = MT.evaluate(r, quick=False)
    return {"seeds": seeds, "n": n, "group_main": r["group_main"],
            "individual_main": r["individual_main"], "ok": bool(all(checks.values()))}


def simulate(quick=False):
    coev = [_coev_case([10, 11, 12, 13])] if quick else [_coev_case([10, 11, 12, 13]),
                                                         _coev_case([20, 21, 22, 23, 24])]
    mt = [_mt_case([5, 6, 7], 20)] if quick else [_mt_case([5, 6, 7], 20), _mt_case([8, 9, 10], 30)]
    return {
        "coevolution": coev, "major_transition": mt,
        "coev_all_ok": all(c["ok"] for c in coev),
        "mt_all_ok": all(c["ok"] for c in mt),
        "robust": bool(all(c["ok"] for c in coev + mt)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e029 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e029 robustness (frontier findings vs seed batch / grid) ===")
    for c in r["coevolution"]:
        print("  coevolution seeds=%s: median coev=%s static=%s ok=%s"
              % (c["seeds"], c["median_coev_len"], c["median_static_len"], c["ok"]))
    for c in r["major_transition"]:
        print("  major_transition seeds=%s n=%s: group=%s individual=%s ok=%s"
              % (c["seeds"], c["n"], c["group_main"], c["individual_main"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
