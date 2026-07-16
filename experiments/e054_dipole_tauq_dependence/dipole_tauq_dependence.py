#!/usr/bin/env python3
"""e054 -- does the self-formed vortex-dipole Level-3 fraction (e052/e053) depend on the KZ quench rate tauQ?

H021 campaign iteration 3. e053 confirmed Level 3 is robust across resolution at ONE quench rate (tauQ=200,
L=96: 62.5% of seeds). This experiment holds L=96 fixed and sweeps tauQ, using e052's SAME physics/observer/
FROZEN thresholds (no re-tuning) with fresh, independent seeds per tauQ point -- a phase-diagram-style
measurement, the same pattern as e050's g-band sweep. A slower quench (larger tauQ) leaves fewer, more
widely separated defects at freeze-out (Kibble-Zurek: xi ~ tauQ^sigma); the physically motivated prediction
is that WIDER spacing gives isolated pairs a better chance to be identified as a clean, uncrowded dipole
(less interference/screening from a dense tangle) -- but this is measured, not assumed.
"""
import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import run_one_seed, FROZEN  # noqa: E402
from experiments.e053_dipole_robustness.dipole_robustness import _wilson_interval  # noqa: E402

L_FIXED = 96
POST_TRACK_STEPS = 1600
TRACK_EVERY = 8

# (tauQ, hold, seed_start, n_seeds) -- hold scales with tauQ (same ratio as e052's baseline 150/200=0.75)
CONFIG_FULL = [
    dict(tauQ=100, hold=75, seed_start=601, n_seeds=10),
    dict(tauQ=150, hold=112, seed_start=701, n_seeds=10),
    dict(tauQ=200, hold=150, seed_start=801, n_seeds=10),   # matches e052/e053 baseline rate
    dict(tauQ=300, hold=225, seed_start=901, n_seeds=10),
    dict(tauQ=400, hold=300, seed_start=1001, n_seeds=10),
]
CONFIG_QUICK = [
    dict(tauQ=60, hold=45, seed_start=1101, n_seeds=3),
    dict(tauQ=120, hold=90, seed_start=1201, n_seeds=3),
]


def run_tauq_point(row, p=FROZEN):
    seeds = range(row["seed_start"], row["seed_start"] + row["n_seeds"])
    rows = [run_one_seed(L_FIXED, row["tauQ"], row["hold"], POST_TRACK_STEPS, TRACK_EVERY, seed, p)
            for seed in seeds]
    n = len(rows)
    n_l3 = sum(1 for r in rows if r["reached_level"] >= 3)
    n_l2 = sum(1 for r in rows if r["reached_level12"] >= 2)
    mean_n_tracks = float(np.mean([r["n_tracks"] for r in rows]))
    frac, lo, hi = _wilson_interval(n_l3, n)
    return dict(tauQ=row["tauQ"], hold=row["hold"], n_seeds=n, n_reaching_level2=n_l2,
                n_reaching_level3=n_l3, level3_fraction=frac, level3_fraction_ci95=[lo, hi],
                mean_n_tracks=round(mean_n_tracks, 2), seeds=list(seeds), per_seed=rows)


def run(cfg, p=FROZEN):
    by_tauq = [run_tauq_point(row, p) for row in cfg]
    fracs = [row["level3_fraction"] for row in by_tauq]
    tauqs = [row["tauQ"] for row in by_tauq]
    # a simple monotone-trend check (Spearman-style sign test via pairwise comparisons, no scipy needed)
    increasing_pairs = sum(1 for i in range(len(fracs) - 1) if fracs[i + 1] >= fracs[i])
    decreasing_pairs = sum(1 for i in range(len(fracs) - 1) if fracs[i + 1] <= fracs[i])
    n_pairs = max(1, len(fracs) - 1)
    trend = "increasing_with_tauQ" if increasing_pairs == n_pairs and increasing_pairs > decreasing_pairs else (
        "decreasing_with_tauQ" if decreasing_pairs == n_pairs and decreasing_pairs > increasing_pairs else
        "no_clear_monotone_trend")
    all_nonzero = all(row["n_reaching_level3"] > 0 for row in by_tauq)
    verdict = "level3_present_across_tauQ_range" if all_nonzero else "level3_vanishes_at_some_tauQ"
    return dict(by_tauq=by_tauq, tauQ_values=tauqs, fractions=fracs, trend=trend,
                all_tauQ_reach_level3=all_nonzero, verdict=verdict, run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e054 Level-3 dipole fraction vs KZ quench rate tauQ")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e054 Level-3 dipole fraction vs quench rate tauQ (L=%d fixed) ===" % L_FIXED)
    r = run(cfg)
    for row in r["by_tauq"]:
        print("  tauQ=%-4d n=%-3d L2=%d/%d  L3=%d/%d  frac=%.3f (95%% CI [%.3f,%.3f])  mean_n_tracks=%.1f"
              % (row["tauQ"], row["n_seeds"], row["n_reaching_level2"], row["n_seeds"],
                 row["n_reaching_level3"], row["n_seeds"], row["level3_fraction"],
                 row["level3_fraction_ci95"][0], row["level3_fraction_ci95"][1], row["mean_n_tracks"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED")
    print("  TREND:", r["trend"], "  VERDICT:", r["verdict"])
    result = dict(experiment="e054_dipole_tauq_dependence", campaign="H021", follows="e052,e053",
                  role_pending_on_result=True, status="GREEN" if r["run_valid"] else "RED",
                  frozen=FROZEN, L_fixed=L_FIXED, **r)
    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        def _np(o):
            if isinstance(o, (np.bool_,)):
                return bool(o)
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            raise TypeError(repr(o))
        json.dump(result, open(os.path.join(args.out, "dipole_tauq_dependence.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_tauq_dependence.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
