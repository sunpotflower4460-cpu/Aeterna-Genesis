"""ai_lab/relational/verify.py -- PR-R2.1/PR-R2.4/PR-R2.7 pre-checks (AUDIT.md Sec.13,
Sec.16, Sec.19).

Four tools:

1. `verify_long_window`: bakes a 10-20x window re-check into the DEFINITION of
   `sustained`, rather than treating it as an optional follow-up. Two prior positive-result
   retractions in this PR series (PR-R1.5's memory=on sweep, 605/1200 "periodic" -> 0/1200
   sustained; this PR's own damping=0.05 saturation="none" cell, Sec.12.2, 10/11 flagged
   nodes shown to diverge once the window was extended 20x) both trace to the same root
   cause: a window too short to see continued growth. `verify_long_window` re-runs the
   IDENTICAL configuration at `extend_factor` x the original step count and re-checks
   `settled` (not the whole-window `sustained` comparison -- see the function's own
   docstring for why that check specifically is not window-length-robust) on that longer
   recording. A node is only "sustained" in any headline count from here on if this
   passes -- a short-window flag by itself is a CANDIDATE, not a result.

2. `check_attractor_recovery`: the damage-recovery / attractor-vs-orbit-family instrument.
   A verified-sustained oscillation could be (a) a genuine ATTRACTING limit cycle -- nearby
   trajectories converge back to the same amplitude after a perturbation, i.e. it is
   self-sustaining -- or (b) a family of periodic orbits parametrized by amplitude/energy
   (as in an undamped conservative oscillator) -- a perturbation just moves the trajectory
   to a different family member, permanently, and nothing pulls it back. This is measured
   directly by perturbing a settled trajectory's entire state at a checkpoint and comparing
   its later plateau amplitude to an unperturbed control continued from the same checkpoint.
   This is the R-layer's own instance of the same underlying MEASUREMENT CONCEPT that
   ai_lab/dream/frontier_expander.py's capability roster flags as "self_repair" /
   "damage-recovery" (status UNMEASURED there, for the unrelated TDGL-based dream/ system)
   -- implemented here independently for the R-layer's own physics; this module does not
   read or write frontier_expansion.json or any ai_lab/dream/ file. `achieved` is this
   module's own explicit flag, scoped to the R-layer result it was computed from.

3. `verify_long_window_all_nodes` (PR-R2.7, AUDIT.md Sec.19.3): the SAME check as
   `verify_long_window`, but reads every node's result off ONE rerun instead of rerunning
   once per node. `verify_long_window` alone was, until this PR, always called once per
   (seed, run_kwargs, node) even when many nodes from the same run needed checking (e.g.
   PR-R2.6's sampling scripts) -- a ~24x cost multiplier for n=24 that was not noticed
   until Sec.19.3 measured it directly. Use this whenever more than one node from the same
   run needs long-window verification.

4. `check_driven_vs_self_sustaining` (PR-R2.4, AUDIT.md Sec.16.2): review's priority
   question after PR-R2.3's amplitude-propagation finding (non-verified direct neighbors of
   a verified node retain 72% of the verified node's amplitude, non-adjacent nodes 61%) --
   is that retained amplitude evidence the neighbor is ITSELF a self-sustaining oscillator,
   or is it merely being DRIVEN by the verified node's own oscillation, with nothing left
   once that drive is removed? Answered by the same interventional logic as
   `check_attractor_recovery`, but cutting EDGES rather than perturbing amplitude: at a
   checkpoint, the relation graph is split into the verified node set and everything else
   (all edges between the two groups zeroed via `substrate.run`'s `W_override`), and each
   non-verified direct neighbor's plateau amplitude after the cut is compared against an
   unperturbed (still-connected) control continued from the identical checkpoint.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

from ai_lab.relational import instruments, substrate

# Fixed, disclosed constants -- same for every call, not tuned per configuration.
LONG_WINDOW_EXTEND_FACTOR = 15   # re-verification window length, as a multiple of the original
RECOVERY_TOL = 0.20              # relative plateau-amplitude tolerance for "recovered"
DEFAULT_PERTURB_FACTOR = 0.4     # whole-state amplitude rescale applied at the checkpoint
DEFAULT_CHECKPOINT_FRAC = 0.6    # fraction into the long window where the checkpoint is taken


def verify_long_window(
    run_kwargs: Dict[str, Any],
    seed: Optional[int],
    node: int,
    extend_factor: int = LONG_WINDOW_EXTEND_FACTOR,
) -> Dict[str, Any]:
    """Re-run `run_kwargs` (with `seed`) at `extend_factor` x its original `steps`, and
    re-check `node`'s classification on that longer trajectory.

    Uses `settled` (not `sustained_and_settled`) as the long-window criterion -- a
    deliberate, disclosed choice, not an oversight: `sustained`'s whole-window
    first-half-vs-second-half comparison assumes the initial transient is a small fraction
    of the recording, which holds at the original (screening) window length but breaks at
    `extend_factor`x it. Empirically (AUDIT.md Sec.13.2), a config independently confirmed
    by `check_attractor_recovery` to be a genuine attracting limit cycle showed
    `settled=True, settled_ratio~1.00` (flat trailing quarter) but `sustained=False,
    classification='growing'` on the SAME 15x-extended trajectory, purely because the
    transient's low amplitude drags down the first-half average once the transient is only
    a small fraction of a much longer recording. `settled`'s trailing-quarter-only
    comparison does not have this failure mode, so it is the correct, window-length-robust
    criterion for a re-verification check whose entire point is to look far past any
    transient.

    Returns a dict with `verified_sustained` (bool) -- the authoritative definition of
    "sustained" from PR-R2.1 onward -- plus the long-window R4 entry for that node and the
    step counts used, for audit purposes.
    """
    kw = dict(run_kwargs)
    base_steps = kw["steps"]
    kw["steps"] = base_steps * extend_factor
    res = substrate.run(seed=seed, **kw)
    r4 = instruments.period(res.x_traj, res.dt)
    if not r4.defined or node >= len(r4.value["per_node"]):
        return {
            "verified_sustained": False,
            "long_entry": None,
            "base_steps": base_steps,
            "long_steps": kw["steps"],
            "extend_factor": extend_factor,
        }
    entry = r4.value["per_node"][node]
    verified = bool(entry.get("defined", False)) and bool(entry.get("settled", False))
    return {
        "verified_sustained": verified,
        "long_entry": entry,
        "base_steps": base_steps,
        "long_steps": kw["steps"],
        "extend_factor": extend_factor,
    }


def verify_long_window_all_nodes(
    run_kwargs: Dict[str, Any],
    seed: Optional[int],
    extend_factor: int = LONG_WINDOW_EXTEND_FACTOR,
) -> "list[Dict[str, Any]]":
    """Same criterion as `verify_long_window`, for every node in ONE rerun.

    `verify_long_window` reruns `substrate.run` in full for a single `node`, even though
    one rerun's R4 (`instruments.period`) already computes every node's `settled` status at
    once. Calling it once per node (as PR-R2.6's sampling scripts did) repeats the IDENTICAL
    rerun `n` times for no reason -- AUDIT.md Sec.19.3 measured this as a ~24x cost
    multiplier for n=24 (one rerun ~8-11s regardless of whether 1 or 24 nodes' results are
    read off it). Use this whenever more than one node from the SAME (seed, run_kwargs)
    needs long-window verification -- e.g. exhaustively verifying an entire sweep, or every
    node in a candidate-covered cycle.

    Returns a list of `n` dicts (one per node, `run_kwargs["n"]` long), each with the same
    fields and `verified_sustained` semantics as `verify_long_window`'s return value, plus
    `"node"`.
    """
    kw = dict(run_kwargs)
    base_steps = kw["steps"]
    kw["steps"] = base_steps * extend_factor
    res = substrate.run(seed=seed, **kw)
    r4 = instruments.period(res.x_traj, res.dt)
    n = run_kwargs["n"]
    if not r4.defined:
        return [
            {"verified_sustained": False, "long_entry": None, "base_steps": base_steps,
             "long_steps": kw["steps"], "extend_factor": extend_factor, "node": i}
            for i in range(n)
        ]
    out = []
    for i in range(n):
        entry = r4.value["per_node"][i] if i < len(r4.value["per_node"]) else None
        verified = bool(entry) and bool(entry.get("defined", False)) and bool(entry.get("settled", False))
        out.append({
            "verified_sustained": verified, "long_entry": entry, "node": i,
            "base_steps": base_steps, "long_steps": kw["steps"], "extend_factor": extend_factor,
        })
    return out


def _plateau_amplitude(x_traj: np.ndarray, node: int, tail_fraction: float = 0.25) -> float:
    series = x_traj[:, node, :].sum(axis=-1)
    tail = series[-max(1, int(len(series) * tail_fraction)):]
    return float(np.abs(tail).mean())


def check_attractor_recovery(
    run_kwargs: Dict[str, Any],
    seed: Optional[int],
    node: int,
    perturb_factor: float = DEFAULT_PERTURB_FACTOR,
    checkpoint_frac: float = DEFAULT_CHECKPOINT_FRAC,
    extend_factor: int = LONG_WINDOW_EXTEND_FACTOR,
    continue_steps: Optional[int] = None,
    recovery_tol: float = RECOVERY_TOL,
) -> Dict[str, Any]:
    """Perturb a settled trajectory's whole state at a checkpoint; compare its later plateau
    amplitude (for `node`) against an unperturbed control continued from the SAME checkpoint.

    `achieved=True` means the damaged continuation's plateau amplitude is within
    `recovery_tol` (relative) of the control's -- the trajectory returned to the same
    amplitude after being perturbed away from it, i.e. this is a genuine attracting limit
    cycle (self-sustaining). `achieved=False` means the damaged continuation settled onto a
    different amplitude (set by the perturbation) and did not return -- consistent with a
    conservative family of periodic orbits, not a self-sustaining structure.
    """
    kw = dict(run_kwargs)
    base_steps = kw["steps"]
    long_steps = base_steps * extend_factor
    kw["steps"] = long_steps
    baseline = substrate.run(seed=seed, **kw)
    if baseline.v_traj is None and kw.get("memory") == "on":
        raise ValueError("memory='on' expected but v_traj is None")

    checkpoint_idx = int(long_steps * checkpoint_frac)
    x_ckpt = baseline.x_traj[checkpoint_idx]
    v_ckpt = baseline.v_traj[checkpoint_idx] if baseline.v_traj is not None else None

    cont_steps = continue_steps if continue_steps is not None else base_steps * 5
    cont_kw = dict(kw)
    cont_kw["steps"] = cont_steps

    control = substrate.run(seed=seed, x0_override=x_ckpt, v0_override=v_ckpt, **cont_kw)
    damaged = substrate.run(
        seed=seed,
        x0_override=x_ckpt * perturb_factor,
        v0_override=(v_ckpt * perturb_factor if v_ckpt is not None else None),
        **cont_kw,
    )

    a_control = _plateau_amplitude(control.x_traj, node)
    a_damaged = _plateau_amplitude(damaged.x_traj, node)

    if a_control <= 0.0:
        return {
            "achieved": False, "reason": "control plateau amplitude is zero -- cannot judge recovery",
            "control_plateau_amplitude": a_control, "damaged_plateau_amplitude": a_damaged,
            "perturb_factor": perturb_factor, "checkpoint_frac": checkpoint_frac,
            "relative_difference": None, "tolerance": recovery_tol,
        }

    rel_diff = abs(a_damaged - a_control) / a_control
    return {
        "achieved": bool(rel_diff <= recovery_tol),
        "control_plateau_amplitude": a_control,
        "damaged_plateau_amplitude": a_damaged,
        "perturb_factor": perturb_factor,
        "checkpoint_frac": checkpoint_frac,
        "relative_difference": rel_diff,
        "tolerance": recovery_tol,
        "checkpoint_idx": checkpoint_idx,
        "long_steps": long_steps,
        "continue_steps": cont_steps,
    }


# Fixed, disclosed default -- a neighbor retaining at least half its connected-control
# amplitude after the verified set is disconnected counts as self-sustaining; below that,
# driven-only. Same threshold for every call, not tuned per configuration.
DEFAULT_SELF_SUSTAINING_TOL = 0.5


def check_driven_vs_self_sustaining(
    run_kwargs: Dict[str, Any],
    seed: Optional[int],
    verified_mask: np.ndarray,
    checkpoint_frac: float = DEFAULT_CHECKPOINT_FRAC,
    extend_factor: int = LONG_WINDOW_EXTEND_FACTOR,
    continue_steps: Optional[int] = None,
    self_sustaining_tol: float = DEFAULT_SELF_SUSTAINING_TOL,
) -> Dict[str, Any]:
    """At a checkpoint on a long (`extend_factor`x) trajectory, cut every edge between the
    `verified_mask` node set and the rest of the graph (`substrate.run`'s `W_override`,
    PR-R2.4), then continue both a CUT and a CONNECTED-control run from the identical
    checkpoint state. For every non-verified node that is a DIRECT neighbor (in the
    original, uncut graph) of at least one verified node, compares its post-cut plateau
    amplitude against its own connected-control plateau amplitude.

    `self_sustaining` (per neighbor) = ratio >= `self_sustaining_tol` (default 50%): the
    neighbor kept most of its amplitude even once decoupled from the verified set, i.e. it
    was NOT merely being driven -- it has its own local capacity to sustain the
    oscillation. `driven_only` = ratio below tolerance: the neighbor's amplitude collapsed
    once the drive was removed, i.e. it was riding on the verified node's oscillation, not
    generating its own.

    Returns a dict with `per_neighbor` (list of per-node results) and `n_self_sustaining` /
    `n_driven_only` / `n_checked` summary counts for this one run.
    """
    kw = dict(run_kwargs)
    base_steps = kw["steps"]
    long_steps = base_steps * extend_factor
    kw["steps"] = long_steps
    baseline = substrate.run(seed=seed, **kw)

    mask = np.asarray(verified_mask, dtype=bool)
    n = baseline.W_final.shape[0]
    W = baseline.W_final.copy()
    adjacency = W > 0
    neighbor_of_verified = np.zeros(n, dtype=bool)
    for i in range(n):
        if mask[i]:
            continue
        if adjacency[i, mask].any():
            neighbor_of_verified[i] = True

    if not neighbor_of_verified.any():
        return {"per_neighbor": [], "n_self_sustaining": 0, "n_driven_only": 0, "n_checked": 0}

    W_cut = W.copy()
    W_cut[np.ix_(mask, ~mask)] = 0.0
    W_cut[np.ix_(~mask, mask)] = 0.0

    checkpoint_idx = int(long_steps * checkpoint_frac)
    x_ckpt = baseline.x_traj[checkpoint_idx]
    v_ckpt = baseline.v_traj[checkpoint_idx] if baseline.v_traj is not None else None

    cont_steps = continue_steps if continue_steps is not None else base_steps * 5
    cont_kw = dict(kw)
    cont_kw["steps"] = cont_steps

    control = substrate.run(seed=seed, x0_override=x_ckpt, v0_override=v_ckpt,
                             W_override=W, **cont_kw)
    cut = substrate.run(seed=seed, x0_override=x_ckpt, v0_override=v_ckpt,
                         W_override=W_cut, **cont_kw)

    per_neighbor = []
    n_self_sustaining = 0
    n_driven_only = 0
    for i in range(n):
        if not neighbor_of_verified[i]:
            continue
        a_control = _plateau_amplitude(control.x_traj, i)
        a_cut = _plateau_amplitude(cut.x_traj, i)
        ratio = (a_cut / a_control) if a_control > 0 else None
        self_sustaining = bool(ratio is not None and ratio >= self_sustaining_tol)
        if self_sustaining:
            n_self_sustaining += 1
        else:
            n_driven_only += 1
        per_neighbor.append({
            "node": i, "control_amplitude": a_control, "cut_amplitude": a_cut,
            "ratio": ratio, "self_sustaining": self_sustaining,
        })

    return {
        "per_neighbor": per_neighbor,
        "n_self_sustaining": n_self_sustaining,
        "n_driven_only": n_driven_only,
        "n_checked": len(per_neighbor),
        "checkpoint_idx": checkpoint_idx,
        "long_steps": long_steps,
        "continue_steps": cont_steps,
        "self_sustaining_tol": self_sustaining_tol,
    }
