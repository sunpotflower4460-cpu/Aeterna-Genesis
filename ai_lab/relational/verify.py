"""ai_lab/relational/verify.py -- PR-R2.1 pre-checks (AUDIT.md Sec.13).

Two tools, both requested by review before R7 could proceed on solid ground:

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
