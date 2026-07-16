#!/usr/bin/env python3
"""e057 -- the first genuine Level-4 test: does a self-formed, already-bound vortex dipole RECOVER after a
local perturbation nearby, or does it dissolve? (EMERGENCE_LEVELS.md Level 4 criterion
`recovers_after_perturbation`, the one piece e052-e056 never measured.)

Protocol (matched control, deterministic replay):
  1. Run the standard KZ quench (same law/thresholds as e052 onward) and, post-hoc, find a
     mutual-nearest-neighbor +/- pair that has already been bound for >= PRE_BOUND_MIN snapshots
     (confidence it's a real structure, not a fleeting crossing).
  2. Re-run the SAME seed deterministically up to exactly that intervention step (same law, same noise
     draw -- floating point determinism reconstructs the identical psi) to get the exact field state.
  3. Branch A (CONTROL): continue this exact state for N_FOLLOWUP steps, unperturbed.
     Branch B (PERTURBED): continue an independent copy of the SAME state, but with a local complex-noise
     kick injected NEAR (not on top of) the pair -- a nearby disturbance, not a direct hit.
  4. In each branch, track whether the SAME pair (identified by charge + proximity to its intervention-
     time position) remains a mutual-nearest-neighbor bound pair for >= RECOVERY_MIN of the follow-up
     snapshots. Branch A's rate is the baseline ("would it have survived this long anyway"); Branch B's
     rate answers the actual question.

Physics (core.field.step_damped_2d, L=96, tauQ=200) and the vortex/pairing observer
(genesis.diagnostics.level3_motion) are unchanged from e052 onward -- FROZEN, not re-tuned.
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
from genesis.diagnostics.level3_motion import link_frames, dipole_events, _wrap_delta  # noqa: E402
from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import FROZEN  # noqa: E402
from experiments.e055_dipole_survival_time.dipole_survival_time import TRACK_EVERY  # noqa: E402

L_FIXED = 96
TAUQ, HOLD = 200, 150            # e052 baseline quench recipe
SEARCH_POST_STEPS = 2400         # window to search for a suitable pre-bound pair (1.5x e052 baseline)
PRE_BOUND_MIN = 20               # snapshots the pair must ALREADY have been bound before intervening
N_FOLLOWUP = 800                 # steps evolved after intervention, each branch
RECOVERY_MIN = 12                # snapshots the (same) pair must remain bound post-intervention to "recover"
PERTURB_RADIUS = 5.0             # grid units: perturbation disk radius
PERTURB_OFFSET = 5.0             # grid units: perturbation disk center offset from the pair's midpoint --
                                  # small enough (vs typical pair separation ~10-15) to reliably land close
                                  # to at least one vortex regardless of the random angle (a genuine nearby
                                  # disturbance test, not a guaranteed miss)
PERTURB_AMPLITUDE = 1.0          # complex-noise kick amplitude (relative to the |psi|~1 condensed background)

CONFIG_FULL = dict(seed_start=1801, n_seeds=10)
CONFIG_QUICK = dict(seed_start=1901, n_seeds=2)


def _quench_and_track(seed, post_steps, p=FROZEN):
    """Run the quench + post-track evolution, returning (psi_final, frames, k2, V) so the caller can also
    re-derive intermediate states deterministically by re-running with the same seed."""
    g, dt, gamma = p["g"], p["dt"], p["gamma"]
    k2 = k_squared(L_FIXED)
    V = np.zeros((L_FIXED, L_FIXED))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L_FIXED, L_FIXED)) + 1j * rng.standard_normal((L_FIXED, L_FIXED)))
    for s in range(TAUQ + HOLD):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / TAUQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, dt, gamma)
    frames = [vortex.find_vortices(psi)]
    for s in range(post_steps):
        psi = field.step_damped_2d(psi, V, k2, g, p["mu_f"], dt, gamma)
        if (s + 1) % TRACK_EVERY == 0:
            frames.append(vortex.find_vortices(psi))
    return frames, k2, V


def _replay_to_step(seed, extra_steps, p=FROZEN):
    """Deterministically reconstruct psi at (TAUQ+HOLD+extra_steps) steps by re-running from scratch."""
    g, dt, gamma = p["g"], p["dt"], p["gamma"]
    k2 = k_squared(L_FIXED)
    V = np.zeros((L_FIXED, L_FIXED))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L_FIXED, L_FIXED)) + 1j * rng.standard_normal((L_FIXED, L_FIXED)))
    for s in range(TAUQ + HOLD):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / TAUQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, dt, gamma)
    for s in range(extra_steps):
        psi = field.step_damped_2d(psi, V, k2, g, p["mu_f"], dt, gamma)
    return psi, k2, V


def _find_intervention_candidate(frames, L, p):
    """From a full frame series, find the pair with the longest run of mutual-nearest-neighbor binding
    that reaches >= PRE_BOUND_MIN, and return (intervene_frame_idx, pos_pos, neg_pos, charges) at that
    point -- the earliest frame at which it has already been bound for PRE_BOUND_MIN snapshots, so the
    follow-up window afterward is maximized."""
    tracks = link_frames(frames, L, max_step=p["max_step"])
    pos_tracks = [t for t in tracks if t["charge"] > 0]
    neg_tracks = [t for t in tracks if t["charge"] < 0]

    def overlap(ta, tb):
        fa = {pt[0] for pt in ta["points"]}
        fb = {pt[0] for pt in tb["points"]}
        return sorted(fa & fb)

    best = None  # (duration, intervene_frame, pos_xy, neg_xy)
    all_pairs = []
    for ta in pos_tracks:
        for tb in neg_tracks:
            common = overlap(ta, tb)
            if len(common) < PRE_BOUND_MIN:
                continue
            pa = {pt[0]: (pt[1], pt[2]) for pt in ta["points"] if pt[0] in common}
            pb = {pt[0]: (pt[1], pt[2]) for pt in tb["points"] if pt[0] in common}
            mean_sep = float(np.mean([np.hypot(*(_wrap_delta(pb[t][0] - pa[t][0], L),
                                                   _wrap_delta(pb[t][1] - pa[t][1], L))) for t in common]))
            all_pairs.append((ta, tb, common, mean_sep))
    for ta, tb, common, mean_sep in all_pairs:
        ta_best = min((mm for (a2, b2, c2, mm) in all_pairs if a2 is ta), default=None)
        tb_best = min((mm for (a2, b2, c2, mm) in all_pairs if b2 is tb), default=None)
        is_mutual = (ta_best is not None and abs(mean_sep - ta_best) < 1e-9 and
                     tb_best is not None and abs(mean_sep - tb_best) < 1e-9)
        if not is_mutual:
            continue
        intervene_frame = common[PRE_BOUND_MIN - 1]   # earliest point it's been bound PRE_BOUND_MIN frames
        duration = len(common)
        if best is None or duration > best[0]:
            pa = {pt[0]: (pt[1], pt[2]) for pt in ta["points"] if pt[0] in common}
            pb = {pt[0]: (pt[1], pt[2]) for pt in tb["points"] if pt[0] in common}
            best = (duration, intervene_frame, pa[intervene_frame], pb[intervene_frame])
    return best


def _follow_up_recovery(psi0, k2, V, pos_xy, neg_xy, seed, perturb, p=FROZEN):
    """Evolve N_FOLLOWUP steps from psi0 (optionally perturbed), tracking whether the pair starting at
    pos_xy/neg_xy remains mutual-nearest-neighbor bound. Returns (recovered: bool, duration: int)."""
    psi = psi0.copy()
    g, dt, gamma = p["g"], p["dt"], p["gamma"]
    if perturb:
        rng = np.random.default_rng(seed + 90000)   # perturbation noise, independent of the IC seed
        mx = 0.5 * (pos_xy[0] + neg_xy[0])
        my = 0.5 * (pos_xy[1] + neg_xy[1])
        # offset the perturbation disk AWAY from the pair (a nearby disturbance, not a direct hit)
        angle = rng.uniform(0, 2 * np.pi)
        cx = (mx + PERTURB_OFFSET * np.cos(angle)) % L_FIXED
        cy = (my + PERTURB_OFFSET * np.sin(angle)) % L_FIXED
        # core.vortex convention: 'x' is the FIRST array index (axis 0, rows), 'y' is the SECOND (axis 1,
        # columns) -- see core/vortex.py's _refine_core. row_idx must therefore be compared against cx.
        row_idx, col_idx = np.meshgrid(np.arange(L_FIXED), np.arange(L_FIXED), indexing="ij")
        dx = np.minimum(np.abs(row_idx - cx), L_FIXED - np.abs(row_idx - cx))
        dy = np.minimum(np.abs(col_idx - cy), L_FIXED - np.abs(col_idx - cy))
        mask = (dx * dx + dy * dy) <= PERTURB_RADIUS ** 2
        kick = PERTURB_AMPLITUDE * (rng.standard_normal((L_FIXED, L_FIXED)) +
                                     1j * rng.standard_normal((L_FIXED, L_FIXED)))
        psi = psi + mask * kick

    frames = [vortex.find_vortices(psi)]
    for s in range(N_FOLLOWUP):
        psi = field.step_damped_2d(psi, V, k2, p["g"], p["mu_f"], dt, gamma)
        if (s + 1) % TRACK_EVERY == 0:
            frames.append(vortex.find_vortices(psi))

    tracks = link_frames(frames, L_FIXED, max_step=p["max_step"])
    # identify the tracks starting at frame 0 nearest to pos_xy/neg_xy (the known pair)
    def nearest_track(charge, xy):
        cands = [t for t in tracks if t["charge"] == charge and t["points"][0][0] == 0]
        if not cands:
            return None
        def d2(t):
            _, x, y = t["points"][0]
            dx = _wrap_delta(x - xy[0], L_FIXED); dy = _wrap_delta(y - xy[1], L_FIXED)
            return dx * dx + dy * dy
        return min(cands, key=d2)

    ta = nearest_track(1, pos_xy)
    tb = nearest_track(-1, neg_xy)
    if ta is None or tb is None:
        return False, 0
    fa = {pt[0] for pt in ta["points"]}
    fb = {pt[0] for pt in tb["points"]}
    common = sorted(fa & fb)
    if not common or common[0] != 0:
        return False, 0
    # consecutive run starting at frame 0
    run = 0
    for i, t in enumerate(common):
        if t != i:
            break
        run += 1
    return bool(run >= RECOVERY_MIN), run


def run_one_seed(seed, p=FROZEN):
    frames, k2, V = _quench_and_track(seed, SEARCH_POST_STEPS, p)
    cand = _find_intervention_candidate(frames, L_FIXED, p)
    if cand is None:
        return dict(seed=seed, found_candidate=False)
    duration_pre, intervene_frame, pos_xy, neg_xy = cand
    extra_steps = intervene_frame * TRACK_EVERY
    psi0, k2r, Vr = _replay_to_step(seed, extra_steps, p)
    control_recovered, control_run = _follow_up_recovery(psi0, k2r, Vr, pos_xy, neg_xy, seed, False, p)
    perturbed_recovered, perturbed_run = _follow_up_recovery(psi0, k2r, Vr, pos_xy, neg_xy, seed, True, p)
    return dict(seed=seed, found_candidate=True, pre_bound_duration=duration_pre,
                intervene_frame=intervene_frame, control_recovered=control_recovered,
                control_run=control_run, perturbed_recovered=perturbed_recovered,
                perturbed_run=perturbed_run)


def run(cfg, p=FROZEN):
    seeds = range(cfg["seed_start"], cfg["seed_start"] + cfg["n_seeds"])
    rows = [run_one_seed(seed, p) for seed in seeds]
    found = [r for r in rows if r["found_candidate"]]
    n_found = len(found)
    n_control_recovered = sum(1 for r in found if r["control_recovered"])
    n_perturbed_recovered = sum(1 for r in found if r["perturbed_recovered"])
    if n_found == 0:
        verdict = "no_suitable_candidate_in_budget"
    elif n_perturbed_recovered >= n_control_recovered and n_perturbed_recovered > 0:
        verdict = "recovers_after_perturbation_candidate"
    elif n_perturbed_recovered < n_control_recovered:
        verdict = "does_not_reliably_recover"
    else:
        verdict = "inconclusive"
    return dict(per_seed=rows, n_seeds=len(rows), n_found_candidate=n_found,
                n_control_recovered=n_control_recovered, n_perturbed_recovered=n_perturbed_recovered,
                verdict=verdict, run_valid=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="e057 Level-4 perturbation-recovery test on self-formed dipoles")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e057 Level-4 perturbation-recovery test (self-formed vortex dipoles) ===")
    r = run(cfg)
    for row in r["per_seed"]:
        if not row["found_candidate"]:
            print("  seed=%-5d  no suitable pre-bound candidate found" % row["seed"])
            continue
        print("  seed=%-5d pre_bound=%-3d  control: recovered=%s(run=%-3d)  perturbed: recovered=%s(run=%-3d)"
              % (row["seed"], row["pre_bound_duration"], row["control_recovered"], row["control_run"],
                 row["perturbed_recovered"], row["perturbed_run"]))
    print("  found candidate: %d/%d  control recovered: %d  perturbed recovered: %d"
          % (r["n_found_candidate"], r["n_seeds"], r["n_control_recovered"], r["n_perturbed_recovered"]))
    print("STATUS:", "GREEN" if r["run_valid"] else "RED")
    print("  VERDICT:", r["verdict"])
    result = dict(experiment="e057_dipole_perturbation_recovery", campaign="H021", follows="e052..e056",
                  role_pending_on_result=True, status="GREEN" if r["run_valid"] else "RED", frozen=FROZEN,
                  L_fixed=L_FIXED, tauQ=TAUQ, hold=HOLD, pre_bound_min=PRE_BOUND_MIN,
                  n_followup=N_FOLLOWUP, recovery_min=RECOVERY_MIN, perturb_radius=PERTURB_RADIUS,
                  perturb_offset=PERTURB_OFFSET, perturb_amplitude=PERTURB_AMPLITUDE, **r)
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
        json.dump(result, open(os.path.join(args.out, "dipole_perturbation_recovery.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "dipole_perturbation_recovery.json"))
    return 0 if r["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
