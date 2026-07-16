#!/usr/bin/env python3
"""e056 -- does the self-formed vortex-dipole survival time (e055) SATURATE at a finite characteristic
lifetime, or keep growing without bound as the observation window is extended?

e055 (H021 campaign iteration 4) compared a baseline window (e052/e053/e054, 1600 post-track steps) against
a 3x-longer window (4800 steps): max duration grew only ~1.5-2x, not 3x, suggesting partial saturation --
but left the question explicitly unresolved (a single window-length comparison cannot distinguish "finite
lifetime" from "just hasn't finished growing yet"). This experiment adds TWO further window lengths (6x and
9x the baseline) with fresh, independent seeds, so the max/median duration can be compared across THREE
extensions (3x from e055, 6x, 9x here) -- if the values plateau, that is real evidence of a finite
characteristic lifetime (Level 4 remains unreached: transient, not persistent). If they keep growing
roughly linearly with the window, that would be evidence AGAINST saturation and worth a much longer test.

Physics, observer, and FROZEN thresholds are unchanged from e052/e055 (same L=96, tauQ=200 quench). e055's
own 3x-window numbers are NOT recomputed here -- cited directly from its committed results (no duplicate
work, no overwritten artifacts).
"""
import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e055_dipole_survival_time.dipole_survival_time import (  # noqa: E402
    run_one_seed_survival, PRIOR_WINDOW_SNAPSHOTS, TRACK_EVERY,
)
from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import FROZEN  # noqa: E402

BASELINE_STEPS = 1600             # e052/e053/e054's window (for reference/labeling only)
CONFIG_FULL = [
    dict(multiple=6, post_track_steps=9600, seed_start=1501, n_seeds=8),
    dict(multiple=9, post_track_steps=14400, seed_start=1601, n_seeds=8),
]
CONFIG_QUICK = [
    dict(multiple=0.2, post_track_steps=320, seed_start=1701, n_seeds=2),
    dict(multiple=0.3, post_track_steps=480, seed_start=1801, n_seeds=2),
]

# e055's own committed full-config result (3x window, 10 seeds) -- cited for the saturation comparison,
# NOT recomputed (avoids duplicate work / overwriting e055's artifact). See experiments/e055_.../results/.
E055_REFERENCE = dict(multiple=3, post_track_steps=4800, n_seeds=10,
                       global_max_duration_snapshots=358, global_max_phys_time=143.20)


def run_window_point(row, p=FROZEN):
    seeds = range(row["seed_start"], row["seed_start"] + row["n_seeds"])
    rows = [run_one_seed_survival(seed, row["post_track_steps"], p) for seed in seeds]
    max_durations = [r["max_duration_snapshots"] for r in rows]
    max_phys_times = [r["max_phys_time"] for r in rows]
    return dict(multiple=row["multiple"], post_track_steps=row["post_track_steps"], n_seeds=len(rows),
                global_max_duration_snapshots=max(max_durations) if max_durations else 0,
                global_max_phys_time=max(max_phys_times) if max_phys_times else 0.0,
                median_max_duration_snapshots=float(np.median(max_durations)) if max_durations else 0.0,
                seeds=list(seeds), per_seed=rows)


def run(cfg, p=FROZEN):
    by_window = [run_window_point(row, p) for row in cfg]
    # saturation check: compare global-max duration growth across window multiples (including e055's cited
    # 3x point). If duration growth per unit of ADDITIONAL window is small/flat at the largest multiples,
    # that's evidence of a plateau (finite characteristic lifetime).
    points = [dict(multiple=E055_REFERENCE["multiple"],
                    global_max_duration_snapshots=E055_REFERENCE["global_max_duration_snapshots"],
                    global_max_phys_time=E055_REFERENCE["global_max_phys_time"], source="e055_cited")]
    for row in by_window:
        points.append(dict(multiple=row["multiple"],
                            global_max_duration_snapshots=row["global_max_duration_snapshots"],
                            global_max_phys_time=row["global_max_phys_time"], source="e056_measured"))
    points.sort(key=lambda d: d["multiple"])
    # ratio of duration-growth to window-growth between consecutive points (< 1 means sub-linear = plateauing)
    growth_ratios = []
    for i in range(len(points) - 1):
        window_ratio = points[i + 1]["multiple"] / points[i]["multiple"]
        dur_a = max(points[i]["global_max_duration_snapshots"], 1)
        dur_ratio = points[i + 1]["global_max_duration_snapshots"] / dur_a
        growth_ratios.append(dict(from_multiple=points[i]["multiple"], to_multiple=points[i + 1]["multiple"],
                                   window_ratio=round(window_ratio, 3), duration_ratio=round(dur_ratio, 3),
                                   sublinear=bool(dur_ratio < window_ratio)))
    all_sublinear = all(g["sublinear"] for g in growth_ratios) if growth_ratios else False
    # the LAST (largest-window) growth step is the most informative for "still growing vs plateaued"
    last_sublinear = growth_ratios[-1]["sublinear"] if growth_ratios else False
    last_duration_ratio = growth_ratios[-1]["duration_ratio"] if growth_ratios else None
    if all_sublinear and last_duration_ratio is not None and last_duration_ratio < 1.15:
        verdict = "saturation_supported"
    elif all_sublinear:
        verdict = "saturation_partial_still_growing"
    else:
        verdict = "no_saturation_evidence"
    return dict(by_window=by_window, points=points, growth_ratios=growth_ratios,
                all_sublinear=all_sublinear, verdict=verdict, run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e056 dipole survival-time saturation (6x/9x window)")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e056 dipole survival-time SATURATION check (window multiples vs e052 baseline=%d steps) ==="
          % BASELINE_STEPS)
    r = run(cfg)
    print("  points (multiple -> global max duration):")
    for p in r["points"]:
        print("    %sx  max_duration=%-4d snap  max_phys_t=%-7.2f  [%s]"
              % (p["multiple"], p["global_max_duration_snapshots"], p["global_max_phys_time"], p["source"]))
    print("  growth ratios (window x vs duration x, sublinear=plateauing):")
    for g in r["growth_ratios"]:
        print("    %sx->%sx: window_ratio=%.2f  duration_ratio=%.2f  sublinear=%s"
              % (g["from_multiple"], g["to_multiple"], g["window_ratio"], g["duration_ratio"], g["sublinear"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED")
    print("  VERDICT:", r["verdict"])
    result = dict(experiment="e056_dipole_survival_saturation", campaign="H021", follows="e052..e055",
                  role_pending_on_result=True, status="GREEN" if r["run_valid"] else "RED",
                  frozen=FROZEN, baseline_steps=BASELINE_STEPS, e055_reference=E055_REFERENCE, **r)
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
        json.dump(result, open(os.path.join(args.out, "dipole_survival_saturation.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_survival_saturation.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
