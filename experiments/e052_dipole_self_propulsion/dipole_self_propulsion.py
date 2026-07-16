#!/usr/bin/env python3
"""e052 -- does a genuinely SELF-FORMED (not placed) +/- vortex dipole survive the Kibble-Zurek defect
tangle and translate coherently -- Level 3 (EMERGENCE_LEVELS.md) in a SINGLE CONTINUOUS run from an
undifferentiated t=0 IC?

First iteration of the H021 frontier campaign ("0から最も遠くに行く"): docs/working_ledger/
H021_frontier_campaign_0_to_far.md. e002 already showed (role E/analogy, PLACED initial condition) that an
imprinted opposite-sign vortex pair translates from the local GPE law alone (same-sign co-rotate, opposite-
sign translate). The unasked, harder question this experiment measures: does the natural post-quench defect
tangle -- with no pair imprinted, only white noise -- ever leave behind an isolated +/- pair whose motion is
DISTINGUISHABLE from generic single-defect jitter and from a uniform box-wide drift artifact? Physics is
100% reused (core.field.step_damped_2d, the exact e010 Kibble-Zurek quench recipe -- no new propagator); the
new instrument is genesis/diagnostics/level3_motion.py (role V observer, measures.py untouched/no_touch).

  PUT IN:  damped GPE dpsi/dt=-(i+gamma)(-1/2 lap + g|psi|^2 - mu) psi + white noise + mu quench (tauQ steps,
           e010 protocol). NO vortex, pair, or motion is named or imprinted.
  MEASURE: Level 1 (measures.mean_amplitude/structure_factor_peak), Level 2 (measures.winding_defect_count),
           Level 3 NEW (genesis.diagnostics.level3_motion: self-formed dipole tracking + two self-calibrating
           floors -- an analytic random-walk straightness floor and the empirical single-defect jitter floor
           from the SAME run's own tracked population; NOT a mismatched-pair shuffle, which leaks signal --
           see level3_motion.py's module docstring for why that was tried and rejected).
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
from genesis.diagnostics.level3_motion import (  # noqa: E402
    link_frames, dipole_events, level3_verdict, track_step_sizes, box_centroid_drift,
)

FROZEN = dict(g=1.0, mu_i=-0.2, mu_f=1.0, dt=0.05, gamma=1.0, noise=0.05,
              max_step=3.0, persist_min=15, sep_max=8.0, straight_min=0.5,
              speed_margin=3.0, straight_margin=2.0)
CONFIG_FULL = dict(L=96, tauQ=200, hold=150, post_track_steps=1600, track_every=8,
                    seeds=(1, 2, 3, 4, 5, 6))
CONFIG_QUICK = dict(L=48, tauQ=60, hold=60, post_track_steps=320, track_every=8, seeds=(1, 2))


def run_one_seed(L, tauQ, hold, post_track_steps, track_every, seed, p=FROZEN):
    """A single continuous run from Level 0: quench (e010 recipe, reused verbatim) -> extended post-freeze
    evolution with vortex-position snapshots for Level-3 tracking. Returns the L1/L2 trajectory and the
    Level-3 verdict for THIS run."""
    g, dt, gamma = p["g"], p["dt"], p["gamma"]
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))

    l12_traj = []

    def snap_l12():
        l12_traj.append(dict(mean_amp=measures.mean_amplitude(psi),
                              sk_prom=measures.structure_factor_peak(psi)[1],
                              defects=measures.winding_defect_count(psi)))

    snap_l12()
    for s in range(tauQ + hold):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, dt, gamma)
        if s % max(1, (tauQ + hold) // 10) == 0:
            snap_l12()
    snap_l12()

    frames = [vortex.find_vortices(psi)]
    for s in range(post_track_steps):
        psi = field.step_damped_2d(psi, V, k2, g, p["mu_f"], dt, gamma)
        if (s + 1) % track_every == 0:
            frames.append(vortex.find_vortices(psi))
        if (s + 1) % max(1, post_track_steps // 10) == 0:
            snap_l12()

    reached, detected, measured_by = measures.assess_level(l12_traj)

    tracks = link_frames(frames, L, max_step=p["max_step"])
    cands, other_speeds = dipole_events(tracks, L, persist_min=p["persist_min"],
                                         sep_max=p["sep_max"], straight_min=p["straight_min"])
    steps = track_step_sizes(tracks, L)
    v3 = level3_verdict(cands, steps, persist_min=p["persist_min"],
                         speed_margin=p["speed_margin"], straight_margin=p["straight_margin"])
    drift = box_centroid_drift(frames, L)
    drift_rms = float(np.sqrt(np.mean(np.sum(drift ** 2, axis=1)))) if len(drift) else 0.0
    reached3 = 3 if (reached >= 2 and v3["level3_reached"]) else reached

    return dict(seed=seed, reached_level12=reached, reached_level=reached3, detected=detected,
                measured_by=measured_by, n_frames_tracked=len(frames), n_tracks=len(tracks),
                n_dipole_candidates=v3["n_candidates"], level3=v3, box_drift_rms=round(drift_rms, 6))


def run(cfg, p=FROZEN):
    per_seed = [run_one_seed(cfg["L"], cfg["tauQ"], cfg["hold"], cfg["post_track_steps"],
                              cfg["track_every"], seed, p) for seed in cfg["seeds"]]
    n = len(per_seed)
    n_level2 = sum(1 for r in per_seed if r["reached_level12"] >= 2)
    n_level3 = sum(1 for r in per_seed if r["reached_level"] >= 3)
    max_level_seen = max((r["reached_level"] for r in per_seed), default=0)
    if n_level3 > 0:
        verdict = "level3_dipole_survives_in_budget" if n_level3 >= max(1, n // 3) else \
                  "level3_rare_candidate"
    elif n_level2 == n:
        verdict = "level2_ceiling_reconfirmed"
    else:
        verdict = "partial"
    return dict(per_seed=per_seed, n_seeds=n, n_reaching_level2=n_level2, n_reaching_level3=n_level3,
                max_level_seen=max_level_seen, verdict=verdict,
                run_valid=all(np.isfinite(r["box_drift_rms"]) for r in per_seed))


def main(argv=None):
    ap = argparse.ArgumentParser(description="e052 self-formed vortex-dipole Level-3 propulsion (frontier)")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e052 self-formed +/- vortex dipole -- Level 3 spontaneous motion (single continuous t=0 run) ===")
    r = run(cfg)
    for row in r["per_seed"]:
        print("  seed=%d  L1/L2 reached=%d  L3 reached=%s  candidates=%d  verdict=%s  box_drift_rms=%.4f"
              % (row["seed"], row["reached_level12"], row["reached_level"] >= 3,
                 row["n_dipole_candidates"], row["level3"]["verdict"], row["box_drift_rms"]))
    print("  seeds reaching Level>=2: %d/%d   Level>=3: %d/%d   max level seen: %d"
          % (r["n_reaching_level2"], r["n_seeds"], r["n_reaching_level3"], r["n_seeds"], r["max_level_seen"]))
    passed = r["run_valid"]
    print("STATUS:", "GREEN" if passed else "RED",
          "(GREEN = valid matched runs across seeds reached a definitive verdict; the science is below)")
    print("  CAMPAIGN VERDICT:", r["verdict"])
    result = dict(experiment="e052_dipole_self_propulsion", campaign="H021", role_pending_on_result=True,
                  status="GREEN" if passed else "RED", frozen=FROZEN,
                  config={k: v for k, v in cfg.items() if k != "seeds"}, n_seeds_config=len(cfg["seeds"]), **r)
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
        json.dump(result, open(os.path.join(args.out, "dipole_self_propulsion.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_self_propulsion.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
