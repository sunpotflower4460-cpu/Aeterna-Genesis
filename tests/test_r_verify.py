"""Tests for ai_lab/relational/verify.py (PR-R2.1: long-window definition + damage-recovery)."""

import numpy as np
import pytest

from ai_lab.relational import substrate, verify

_KW_SATURATION_NONE = dict(
    n=24, steps=3000, dt=0.05, memory="on", damping=0.05, asymmetry=True,
    asymmetry_strength=0.3, topology="random_regular", saturation="none",
)
_KW_SATURATION_CUBIC = dict(
    n=24, steps=3000, dt=0.05, memory="on", damping=0.05, asymmetry=True,
    asymmetry_strength=0.3, topology="random_regular", saturation="cubic",
    saturation_strength=0.1,
)
_SEED = 5
_NODE = 22


def test_substrate_run_x0_override_reproduces_deterministically():
    """x0_override must fully replace the random initial condition -- the SAME override
    must give the SAME trajectory (RK4 is deterministic given x0/v0/W)."""
    short_kw = dict(_KW_SATURATION_CUBIC, steps=10)
    res = substrate.run(seed=_SEED, **short_kw)
    x0 = res.x_traj[3]
    v0 = res.v_traj[3]
    a = substrate.run(seed=_SEED, x0_override=x0, v0_override=v0, **short_kw)
    b = substrate.run(seed=_SEED, x0_override=x0, v0_override=v0, **short_kw)
    assert np.array_equal(a.x_traj, b.x_traj)
    assert np.array_equal(a.x_traj[0], x0)


def test_substrate_run_x0_override_keeps_same_w_as_unoverridden_run():
    """Continuation must not perturb the relation graph -- same seed/topology => same W,
    with or without x0_override (W's construction never depends on x0)."""
    short_kw = dict(_KW_SATURATION_CUBIC, steps=5)
    base = substrate.run(seed=_SEED, **short_kw)
    overridden = substrate.run(seed=_SEED, x0_override=base.x_traj[2],
                                v0_override=base.v_traj[2], **short_kw)
    assert np.array_equal(base.W_final, overridden.W_final)


def test_verify_long_window_rejects_saturation_none_known_divergent_config():
    """AUDIT.md Sec.12.2's own spot-checked divergent config (random_regular seed=5,
    node=22, saturation='none') must fail long-window verification -- this is the exact
    case whose divergence motivated adding verify_long_window in the first place."""
    result = verify.verify_long_window(_KW_SATURATION_NONE, _SEED, _NODE)
    assert result["verified_sustained"] is False


def test_verify_long_window_accepts_saturation_cubic_known_bounded_config():
    """The identical config, saturation='cubic' only, must pass -- this is AUDIT.md
    Sec.12.2's confirmed genuine bounded oscillation."""
    result = verify.verify_long_window(_KW_SATURATION_CUBIC, _SEED, _NODE)
    assert result["verified_sustained"] is True
    assert result["long_entry"]["settled"] is True


def test_check_attractor_recovery_true_for_known_limit_cycle():
    """A genuine attracting limit cycle must return to its pre-perturbation plateau
    amplitude after the whole state is rescaled at a checkpoint."""
    result = verify.check_attractor_recovery(_KW_SATURATION_CUBIC, _SEED, _NODE)
    assert result["achieved"] is True
    assert result["relative_difference"] < verify.RECOVERY_TOL
    assert result["control_plateau_amplitude"] > 0


def test_check_attractor_recovery_reports_all_disclosed_fields():
    result = verify.check_attractor_recovery(_KW_SATURATION_CUBIC, _SEED, _NODE)
    for key in ("achieved", "control_plateau_amplitude", "damaged_plateau_amplitude",
                "perturb_factor", "relative_difference", "tolerance"):
        assert key in result
