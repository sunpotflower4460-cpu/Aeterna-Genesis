#!/usr/bin/env python3
"""e055 -- how long do self-formed vortex dipoles (e052/e053/e054) actually persist? A first step toward
Level 4 (persistent individuality, EMERGENCE_LEVELS.md): dipole_events (e052) only asks "did >= persist_min
frames of COHERENT (straight+fast) motion occur" -- a fixed threshold pass/fail. This experiment asks the
more basic question first: what is the full SURVIVAL-TIME distribution of mutual-nearest-neighbor bound
pairs (genesis.diagnostics.level3_motion.mutual_neighbor_durations, a NEW additive function, same
observer file, no_touch on measures.py preserved), over an OBSERVATION WINDOW 3x longer than e052/e053/e054?

If some fraction of pairs persist for a LARGE fraction of the (much longer) window, that is evidence of a
quasi-permanent bound compound -- worth a follow-up perturbation-recovery test (the harder Level-4 criterion:
"recovers_after_perturbation"). If survival times stay short relative to the window regardless of how long
we watch, that is an honest ceiling: the pairing is a transient event, not a persistent individual, and
Level 4 remains unreached by this white -- consistent with WHITE_CEILINGS.md's existing "single self-
propelling individual is a codimension>=2 knife-edge" finding (a DIFFERENT, harder problem than this pair-
level question, but pointing the same direction).
"""
import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402
from genesis.diagnostics.level3_motion import link_frames, mutual_neighbor_durations  # noqa: E402
from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import FROZEN  # noqa: E402

L_FIXED = 96
TAUQ, HOLD = 200, 150            # e052/e053 baseline quench rate
POST_TRACK_STEPS_FULL = 4800     # 3x e052's 1600 -- a much longer observation window
POST_TRACK_STEPS_QUICK = 480
TRACK_EVERY = 8
LONG_LIVED_FRACTION = 0.5        # >= half the observation window counts as "long-lived" (informational label)
PRIOR_WINDOW_SNAPSHOTS = 1600 // TRACK_EVERY + 1   # e052/e053/e054's window (201 snapshots) -- a duration
                                                    # exceeding this means those experiments' fixed persist_min
                                                    # gate could not have distinguished "still going" from "the
                                                    # window simply ended" for that pair (a truncation concern).

CONFIG_FULL = dict(seed_start=1301, n_seeds=10, post_track_steps=POST_TRACK_STEPS_FULL)
CONFIG_QUICK = dict(seed_start=1401, n_seeds=2, post_track_steps=POST_TRACK_STEPS_QUICK)


def run_one_seed_survival(seed, post_track_steps, p=FROZEN):
    g, dt, gamma = p["g"], p["dt"], p["gamma"]
    k2 = k_squared(L_FIXED)
    V = np.zeros((L_FIXED, L_FIXED))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L_FIXED, L_FIXED)) + 1j * rng.standard_normal((L_FIXED, L_FIXED)))

    for s in range(TAUQ + HOLD):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / TAUQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, dt, gamma)

    frames = [vortex.find_vortices(psi)]
    for s in range(post_track_steps):
        psi = field.step_damped_2d(psi, V, k2, g, p["mu_f"], dt, gamma)
        if (s + 1) % TRACK_EVERY == 0:
            frames.append(vortex.find_vortices(psi))

    n_snapshots = len(frames)
    tracks = link_frames(frames, L_FIXED, max_step=p["max_step"])
    durations = mutual_neighbor_durations(tracks, L_FIXED, sep_max=p["sep_max"])
    fractions = [d / n_snapshots for d in durations]
    phys_time = [d * TRACK_EVERY * p["dt"] for d in durations]   # absolute duration in physical time units
    return dict(seed=seed, n_snapshots=n_snapshots, n_tracks=len(tracks),
                n_bound_pairs=len(durations), durations=durations,
                survival_fractions=[round(f, 4) for f in fractions],
                max_survival_fraction=round(max(fractions), 4) if fractions else 0.0,
                median_survival_fraction=round(float(np.median(fractions)), 4) if fractions else 0.0,
                max_duration_snapshots=max(durations) if durations else 0,
                median_duration_snapshots=float(np.median(durations)) if durations else 0.0,
                max_phys_time=round(max(phys_time), 3) if phys_time else 0.0,
                n_long_lived=sum(1 for f in fractions if f >= LONG_LIVED_FRACTION),
                n_exceeding_prior_window=sum(1 for d in durations if d > PRIOR_WINDOW_SNAPSHOTS))


def run(cfg, p=FROZEN):
    seeds = range(cfg["seed_start"], cfg["seed_start"] + cfg["n_seeds"])
    rows = [run_one_seed_survival(seed, cfg["post_track_steps"], p) for seed in seeds]
    all_max = [r["max_survival_fraction"] for r in rows]
    global_max = max(all_max) if all_max else 0.0
    global_max_duration = max((r["max_duration_snapshots"] for r in rows), default=0)
    global_max_phys_time = max((r["max_phys_time"] for r in rows), default=0.0)
    n_seeds_with_long_lived = sum(1 for r in rows if r["n_long_lived"] > 0)
    n_seeds_exceeding_prior_window = sum(1 for r in rows if r["n_exceeding_prior_window"] > 0)
    # honest interpretation: exceeding the PRIOR (e052/e053/e054) window is a real, measured finding
    # (those experiments' fixed observation window truncated some pairs' true lifetime). Whether the
    # lifetime SATURATES at some physical timescale (transient, not persistent) or keeps growing with an
    # even longer window (would need iteration 5+ to resolve) is explicitly left open, NOT claimed here.
    if global_max_duration > PRIOR_WINDOW_SNAPSHOTS and n_seeds_with_long_lived == 0:
        verdict = "lifetimes_exceed_prior_window_saturation_unresolved"
    elif n_seeds_with_long_lived > 0:
        verdict = "long_lived_compound_candidate_saturation_unresolved"
    else:
        verdict = "no_long_lived_compound_in_budget"
    return dict(per_seed=rows, n_seeds=len(rows), global_max_survival_fraction=round(global_max, 4),
                global_max_duration_snapshots=global_max_duration, global_max_phys_time=global_max_phys_time,
                prior_window_snapshots=PRIOR_WINDOW_SNAPSHOTS,
                n_seeds_with_long_lived_pair=n_seeds_with_long_lived,
                n_seeds_exceeding_prior_window=n_seeds_exceeding_prior_window,
                long_lived_threshold=LONG_LIVED_FRACTION, verdict=verdict, run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e055 self-formed dipole survival-time distribution")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e055 self-formed dipole survival-time distribution (L=%d, window=%d steps) ==="
          % (L_FIXED, cfg["post_track_steps"]))
    r = run(cfg)
    for row in r["per_seed"]:
        print("  seed=%-5d n_bound_pairs=%-3d max_duration=%-4d(snap) max_phys_t=%-7.2f max_frac=%.3f  median_frac=%.3f"
              % (row["seed"], row["n_bound_pairs"], row["max_duration_snapshots"], row["max_phys_time"],
                 row["max_survival_fraction"], row["median_survival_fraction"]))
    print("  global max duration: %d snapshots (%.2f phys time)  vs prior (e052/e053/e054) window: %d snapshots"
          % (r["global_max_duration_snapshots"], r["global_max_phys_time"], r["prior_window_snapshots"]))
    print("  seeds with >=1 pair exceeding the PRIOR window: %d/%d  (>=50%% of THIS window: %d/%d)"
          % (r["n_seeds_exceeding_prior_window"], r["n_seeds"], r["n_seeds_with_long_lived_pair"], r["n_seeds"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED")
    print("  VERDICT:", r["verdict"], " (saturation vs unbounded growth is NOT resolved by this experiment)")
    result = dict(experiment="e055_dipole_survival_time", campaign="H021", follows="e052,e053,e054",
                  role_pending_on_result=True, status="GREEN" if r["run_valid"] else "RED",
                  frozen=FROZEN, L_fixed=L_FIXED, tauQ=TAUQ, hold=HOLD, **r)
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
        json.dump(result, open(os.path.join(args.out, "dipole_survival_time.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_survival_time.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
