#!/usr/bin/env python3
"""e058 -- proper (censoring-aware) survival analysis of self-formed vortex-dipole episodes, using
Observer v2 (genesis.diagnostics.vortex_tracking_v2 + dipole_episodes + survival_analysis).

Follows up e055/e056 (H021 campaign, iterations 4-5), which compared the GLOBAL MAXIMUM duration across
independent seed sets at different window lengths and read the sub-proportional growth as "saturation" --
an external audit (2026-07-16) correctly identified that this treats "still bound when the window ended"
(right-censored) the same as "the pair ended" (an observed event), which biases duration statistics and
can manufacture the appearance of saturation. This experiment redoes the measurement properly:

  - Uses dipole_episodes.detect_episodes (per-frame partner check, not whole-track averaging) so an episode
    genuinely ends at a specific frame (or is censored if it reaches the observation window's last frame).
  - Uses vortex_tracking_v2.link_frames_v2 (global Hungarian assignment) instead of the greedy v1 tracker.
  - Feeds episode durations + a right-censoring flag (censored = episode's end_frame is the window's last
    frame) into survival_analysis.summarize (Kaplan-Meier, restricted mean survival time, censoring
    fraction reported explicitly).

Same physics as e052 onward (L=96, tauQ=200 damped-GPE KZ quench, FROZEN thresholds) -- FROZEN, not
re-tuned. Fresh, independent seeds (disjoint from all prior e052-e057 ranges). e055/e056's own committed
results are NOT touched or recomputed; this is a new, independent measurement with the corrected method.
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
from genesis.diagnostics.vortex_tracking_v2 import link_frames_v2  # noqa: E402
from genesis.diagnostics.dipole_episodes import detect_episodes  # noqa: E402
from genesis.diagnostics.survival_analysis import summarize  # noqa: E402
from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import FROZEN  # noqa: E402

L_FIXED = 96
TAUQ, HOLD = 200, 150             # e052 baseline quench recipe (unchanged)
TRACK_EVERY = 8
CONFIG_FULL = dict(post_track_steps=1600, seed_start=2001, n_seeds=20)   # baseline window, fresh seeds
CONFIG_QUICK = dict(post_track_steps=320, seed_start=2101, n_seeds=3)


def run_one_seed(seed, post_track_steps, p=FROZEN):
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

    last_frame = len(frames) - 1
    tracks = link_frames_v2(frames, L_FIXED, max_step=p["max_step"])
    episodes = detect_episodes(tracks, L_FIXED, sep_max=p["sep_max"], max_sep_rate=2.0, straight_min=0.5)
    durations = [ep["duration"] for ep in episodes]
    censored = [ep["end_frame"] >= last_frame for ep in episodes]
    return dict(seed=seed, n_frames=len(frames), n_episodes=len(episodes),
                durations=durations, censored=censored)


def run(cfg, p=FROZEN):
    seeds = range(cfg["seed_start"], cfg["seed_start"] + cfg["n_seeds"])
    rows = [run_one_seed(seed, cfg["post_track_steps"], p) for seed in seeds]
    all_durations = [d for r in rows for d in r["durations"]]
    all_censored = [c for r in rows for c in r["censored"]]
    n_episodes_total = len(all_durations)
    km = summarize(all_durations, all_censored) if n_episodes_total > 0 else None
    verdict = "insufficient_episodes" if n_episodes_total < 5 else "km_summary_computed"
    return dict(per_seed=rows, n_seeds=len(rows), n_episodes_total=n_episodes_total,
                km_summary=km, verdict=verdict, run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e058 censoring-aware Kaplan-Meier survival analysis (Observer v2)")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e058 censoring-aware dipole-episode survival analysis (Observer v2) ===")
    r = run(cfg)
    for row in r["per_seed"]:
        print("  seed=%-5d n_episodes=%-3d durations=%s censored=%s"
              % (row["seed"], row["n_episodes"], row["durations"], row["censored"]))
    print("  total episodes: %d" % r["n_episodes_total"])
    if r["km_summary"]:
        km = r["km_summary"]
        print("  KM median survival: %s   RMST(tau=%.1f): %.3f   censoring_fraction: %.3f  (n=%d, events=%d, censored=%d)"
              % (km["median_survival"], km["tau"], km["restricted_mean_survival"], km["censoring_fraction"],
                 km["n"], km["n_events"], km["n_censored"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED")
    print("  VERDICT:", r["verdict"])
    result = dict(experiment="e058_dipole_survival_km", campaign="H021", follows="e055,e056 (corrected method)",
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
        json.dump(result, open(os.path.join(args.out, "dipole_survival_km.json"), "w"), indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_survival_km.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
