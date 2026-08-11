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


def test_check_attractor_recovery_false_for_known_damping_zero_orbit_family():
    """AUDIT.md Sec.13.7's negative control: damping=0.0 removes the only linear
    dissipation channel, so saturation='cubic' alone caps growth into a BOUNDED but still
    energy-parametrized family of periodic orbits, not a unique attracting amplitude. This
    specific config (barabasi_albert seed=0, damping=0.0) was one of 8 sampled
    damping=0.0 cases in Sec.13.7's disclosed sample, and did not recover (relative
    difference ~0.59, far outside tolerance) -- locked in here as a regression test for the
    100%-vs-25% (damping=0.05 vs damping=0.0) split that section reports."""
    kw = dict(n=24, steps=3000, dt=0.05, memory="on", damping=0.0, asymmetry=True,
              asymmetry_strength=0.3, topology="barabasi_albert", saturation="cubic",
              saturation_strength=0.1)
    result = verify.check_attractor_recovery(kw, seed=0, node=1)
    assert result["achieved"] is False
    assert result["relative_difference"] > 0.3


# ---------------------------------------------------------------------------
# PR-R2.4: substrate.run's W_override, and check_driven_vs_self_sustaining
# ---------------------------------------------------------------------------

def test_substrate_run_w_override_replaces_w_final():
    short_kw = dict(_KW_SATURATION_CUBIC, steps=5)
    base = substrate.run(seed=_SEED, **short_kw)
    W_cut = base.W_final.copy()
    W_cut[0, :] = 0.0
    W_cut[:, 0] = 0.0
    overridden = substrate.run(seed=_SEED, W_override=W_cut, **short_kw)
    assert np.array_equal(overridden.W_final, W_cut)
    assert not np.array_equal(overridden.W_final, base.W_final)
    # W_initial still reflects the topology construction, unaffected by the override
    assert np.array_equal(overridden.W_initial, base.W_initial)


def test_substrate_run_w_override_does_not_affect_w_initial_or_seeded_ic():
    short_kw = dict(_KW_SATURATION_CUBIC, steps=5)
    base = substrate.run(seed=_SEED, **short_kw)
    W_cut = np.zeros_like(base.W_final)
    overridden = substrate.run(seed=_SEED, W_override=W_cut, **short_kw)
    assert np.array_equal(overridden.x_traj[0], base.x_traj[0])


def test_check_driven_vs_self_sustaining_reports_expected_fields():
    kw = dict(n=24, steps=3000, dt=0.05, memory="on", damping=0.05, asymmetry=True,
              asymmetry_strength=0.3, topology="random_regular", saturation="cubic",
              saturation_strength=0.1)
    mask = [False] * 24
    mask[6], mask[7] = True, True  # two arbitrary verified nodes for this structural test
    result = verify.check_driven_vs_self_sustaining(kw, seed=5, verified_mask=mask)
    assert "per_neighbor" in result
    assert result["n_checked"] == result["n_self_sustaining"] + result["n_driven_only"]
    for entry in result["per_neighbor"]:
        assert "self_sustaining" in entry and "ratio" in entry
        assert mask[entry["node"]] is False  # only non-verified nodes are ever checked


# ---------------------------------------------------------------------------
# PR-R2.7: verify_long_window_all_nodes -- one rerun verifying every node, not one
# rerun per node (AUDIT.md Sec.19.3's ~24x cost-multiplier finding).
# ---------------------------------------------------------------------------

def test_verify_long_window_all_nodes_matches_per_node_calls():
    """The batched all-nodes result must agree EXACTLY, node by node, with calling
    verify_long_window once per node -- same criterion, same trajectory (both are RK4-
    deterministic given the same seed/kw), just computed once instead of n times."""
    kw = dict(_KW_SATURATION_CUBIC, steps=200)
    all_nodes = verify.verify_long_window_all_nodes(kw, _SEED, extend_factor=3)
    assert len(all_nodes) == kw["n"]
    for node in (0, 5, _NODE % kw["n"]):
        single = verify.verify_long_window(kw, _SEED, node, extend_factor=3)
        assert all_nodes[node]["verified_sustained"] == single["verified_sustained"]
        assert all_nodes[node]["node"] == node


def test_verify_long_window_all_nodes_accepts_known_bounded_config():
    """Same known-good config as test_verify_long_window_accepts_saturation_cubic_known_
    bounded_config (Sec.12.2) -- node 22 must verify True when read from the batched call."""
    result = verify.verify_long_window_all_nodes(_KW_SATURATION_CUBIC, _SEED)
    assert result[_NODE]["verified_sustained"] is True
    assert result[_NODE]["long_entry"]["settled"] is True


def test_verify_long_window_all_nodes_reports_all_disclosed_fields_per_node():
    kw = dict(_KW_SATURATION_CUBIC, steps=200)
    result = verify.verify_long_window_all_nodes(kw, _SEED, extend_factor=2)
    assert len(result) == kw["n"]
    for i, entry in enumerate(result):
        assert entry["node"] == i
        assert isinstance(entry["verified_sustained"], bool)
        for key in ("base_steps", "long_steps", "extend_factor"):
            assert key in entry


def test_check_driven_vs_self_sustaining_empty_mask_checks_nothing():
    kw = dict(n=24, steps=3000, dt=0.05, memory="on", damping=0.05, asymmetry=True,
              asymmetry_strength=0.3, topology="random_regular", saturation="cubic",
              saturation_strength=0.1)
    result = verify.check_driven_vs_self_sustaining(kw, seed=5, verified_mask=[False] * 24)
    assert result["n_checked"] == 0
