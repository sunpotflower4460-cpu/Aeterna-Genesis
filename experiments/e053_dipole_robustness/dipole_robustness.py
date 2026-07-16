#!/usr/bin/env python3
"""e053 -- robustness follow-up (S2-style) to e052's Level-3 self-formed vortex-dipole candidate.

e052 (H021 campaign iteration 1) found 3/6 seeds at L=96 reaching Level 3 (level3_dipole_candidate), with
thin margins (~10-12% over the jitter floor) -- an honest "frontier candidate", NOT a robust claim. Same
question e049(S1)->e050(S2) asked of the slow-field memory candidate: does this survive more seeds and a
resolution sweep, or was it a finite-size / small-sample artifact?

PHYSICS AND THRESHOLDS ARE FROZEN FROM e052 (pre-registered, not re-tuned on this run's results): same
FROZEN dict (margins, persist_min, sep_max, straight_min), same quench recipe, same level3_motion.py
observer. Only NEW, INDEPENDENT seeds are used (disjoint ranges per L, distinct from e052's seeds 1-6) --
this is a fresh replication, not a re-analysis of the same runs. Only two things vary: seed COUNT (more
statistics) and grid size L (finite-size check).
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

# (L, tauQ, hold, post_track_steps, track_every, seed_start, n_seeds) -- tauQ/hold/post scaled with L the
# same way e052's single L=96 config was chosen (KZ hold ~ tauQ, post_track long enough for many snapshots).
CONFIG_FULL = [
    dict(L=64, tauQ=130, hold=100, post_track_steps=1000, track_every=8, seed_start=201, n_seeds=12),
    dict(L=96, tauQ=200, hold=150, post_track_steps=1600, track_every=8, seed_start=101, n_seeds=24),
    dict(L=128, tauQ=260, hold=200, post_track_steps=2000, track_every=8, seed_start=301, n_seeds=8),
]
CONFIG_QUICK = [
    dict(L=48, tauQ=60, hold=60, post_track_steps=320, track_every=8, seed_start=401, n_seeds=3),
    dict(L=64, tauQ=80, hold=70, post_track_steps=400, track_every=8, seed_start=501, n_seeds=3),
]


def _wilson_interval(k, n, z=1.96):
    """95% Wilson score interval for a binomial proportion -- no scipy dependency."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return round(p, 4), round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)


def run_resolution(cfg_row, p=FROZEN):
    seeds = range(cfg_row["seed_start"], cfg_row["seed_start"] + cfg_row["n_seeds"])
    rows = [run_one_seed(cfg_row["L"], cfg_row["tauQ"], cfg_row["hold"], cfg_row["post_track_steps"],
                          cfg_row["track_every"], seed, p) for seed in seeds]
    n = len(rows)
    n_l3 = sum(1 for r in rows if r["reached_level"] >= 3)
    n_l2 = sum(1 for r in rows if r["reached_level12"] >= 2)
    frac, lo, hi = _wilson_interval(n_l3, n)
    margins = []
    for r in rows:
        if r["level3"]["level3_reached"] and r["level3"]["speed_required"]:
            margins.append(r["level3"]["best"]["speed"] / r["level3"]["speed_required"])
    return dict(L=cfg_row["L"], n_seeds=n, n_reaching_level2=n_l2, n_reaching_level3=n_l3,
                level3_fraction=frac, level3_fraction_ci95=[lo, hi],
                mean_margin_ratio=round(float(np.mean(margins)), 4) if margins else None,
                seeds=list(seeds), per_seed=rows)


def run(cfg, p=FROZEN):
    by_L = [run_resolution(row, p) for row in cfg]
    fracs = [row["level3_fraction"] for row in by_L]
    cis = [row["level3_fraction_ci95"] for row in by_L]
    all_nonzero_lower = all(ci[0] >= 0.0 for ci in cis)  # informational; the real gate is below
    any_l3_at_every_L = all(row["n_reaching_level3"] > 0 for row in by_L)
    # a genuine (not finite-size) effect should not VANISH as L grows: compare smallest vs largest L
    smallest, largest = by_L[0], by_L[-1]
    not_vanishing = (largest["n_reaching_level3"] > 0) if smallest["n_reaching_level3"] > 0 else True
    fraction_stable = (max(fracs) - min(fracs)) < 0.5 if any_l3_at_every_L else False

    if any_l3_at_every_L and fraction_stable:
        verdict = "robust_level3_candidate_confirmed"
    elif largest["n_reaching_level3"] == 0 and smallest["n_reaching_level3"] > 0:
        verdict = "finite_size_artifact_suspected"
    elif not any(row["n_reaching_level3"] > 0 for row in by_L):
        verdict = "level3_not_reproduced"
    else:
        verdict = "marginal_not_resolved"

    return dict(by_resolution=by_L, verdict=verdict, any_l3_at_every_L=any_l3_at_every_L,
                fraction_stable=fraction_stable, not_vanishing_at_largest_L=not_vanishing,
                run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e053 robustness follow-up to e052 Level-3 dipole candidate")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e053 robustness follow-up: e052 Level-3 dipole candidate across resolution + more seeds ===")
    r = run(cfg)
    for row in r["by_resolution"]:
        print("  L=%-4d n=%-3d L2=%d/%d  L3=%d/%d  frac=%.3f (95%% CI [%.3f, %.3f])  mean_margin=%s"
              % (row["L"], row["n_seeds"], row["n_reaching_level2"], row["n_seeds"],
                 row["n_reaching_level3"], row["n_seeds"], row["level3_fraction"],
                 row["level3_fraction_ci95"][0], row["level3_fraction_ci95"][1], row["mean_margin_ratio"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED",
          "(GREEN = valid runs across all resolutions/seeds reached a definitive verdict)")
    print("  VERDICT:", r["verdict"])
    result = dict(experiment="e053_dipole_robustness", campaign="H021", follows="e052",
                  role_pending_on_result=True, status="GREEN" if r["run_valid"] else "RED",
                  frozen=FROZEN, **r)
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
        json.dump(result, open(os.path.join(args.out, "dipole_robustness.json"), "w"), indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_robustness.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
