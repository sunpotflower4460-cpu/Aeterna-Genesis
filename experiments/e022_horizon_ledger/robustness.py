#!/usr/bin/env python3
"""e022 robustness (LAW.md audit 6): the AB reception is exact at any seed; the DS ledger facts must
survive the seed (which sets the sprinkling). Absolute molecule counts are noisy floors; what must not
move is: the count is density-independent (spread small), moves toward pi^2/6 with beta, and the ledger
reads only the horizon-line profile (spot==ridge). We sweep seed offsets and confirm."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e022_horizon_ledger import ab_gap as AB      # noqa: E402
from experiments.e022_horizon_ledger import ledger as LED      # noqa: E402


def _ab_case(seed):
    p = dict(AB.DEFAULT)
    p.update({"seed": seed})
    saved = AB.DEFAULT
    try:
        AB.DEFAULT = p
        r = AB.simulate(quick=False)
    finally:
        AB.DEFAULT = saved
    ok = r["gauge_dE"] < 1e-9 and r["period_dE"] < 1e-9 and r["density_std"] < 1e-9
    return {"seed": seed, "gauge_dE": r["gauge_dE"], "ok": bool(ok)}


def _led_case(seed0):
    p = dict(LED.DEFAULT)
    p.update({"seed0": seed0, "betas": [1.0, 16.0], "beta_seeds": 200, "dens_seeds": 1200,
              "ledger_seeds": 500})
    saved = LED.DEFAULT
    try:
        LED.DEFAULT = p
        r = LED.simulate(quick=False)
    finally:
        LED.DEFAULT = saved
    _, checks = LED.evaluate(r, quick=False)
    return {"seed0": seed0, "density_spread": r["density_spread"],
            "spot_on": r["ledger_spot_on"], "ridge": r["ledger_ridge"],
            "ok": bool(all(checks.values()))}


def simulate(quick=False):
    ab = [_ab_case(s) for s in ([1, 2] if quick else [1, 2, 3])]
    led = [_led_case(s) for s in ([31000] if quick else [31000, 52000, 73000])]
    return {
        "ab": ab, "ledger": led,
        "ab_all_ok": all(c["ok"] for c in ab),
        "ledger_all_ok": all(c["ok"] for c in led),
        "robust": bool(all(c["ok"] for c in ab + led)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e022 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e022 robustness (AB reception + DS ledger vs seed) ===")
    print("  ab all ok:     %s" % r["ab_all_ok"])
    print("  ledger all ok: %s" % r["ledger_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
