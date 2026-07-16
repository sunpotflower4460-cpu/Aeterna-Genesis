"""Gauge-aligned complex-field distance (LT-1) — synthetic known-answer tests. role V, physics-free.

Covers the preregistered LT-1 fixtures: identical fields, global-phase offset, different winding targets,
zero/near-zero norm, seeded-noise monotonicity, NaN/inf rejection, and the fixed sign convention.
"""
import numpy as np

from genesis.diagnostics.gauge_aligned_distance import gauge_aligned_distance as gad


def _field(seed, shape=(24, 24)):
    rng = np.random.default_rng(seed)
    return rng.normal(size=shape) + 1j * rng.normal(size=shape)


def test_identical_fields_zero_distance_unit_overlap():
    F = _field(1)
    r = gad(F, F)
    assert r["raw_distance"] < 1e-9 and r["aligned_distance"] < 1e-9 and r["invariant_distance"] < 1e-9
    assert abs(r["gauge_overlap"] - 1.0) < 1e-9
    assert r["finite_count"] == r["total_count"] and not r["zero_norm"]


def test_global_phase_offset_removed_by_alignment():
    """same field + pi/5 global phase: raw is large, but aligned/invariant ~0 and overlap ~1."""
    F = _field(2)
    r = gad(F, np.exp(1j * np.pi / 5) * F)
    assert r["raw_distance"] > 0.1
    assert r["aligned_distance"] < 1e-9 and r["invariant_distance"] < 1e-9
    assert abs(r["gauge_overlap"] - 1.0) < 1e-9
    # theta_star recovers -pi/5 (angle applied to B to rotate it onto A)
    assert abs(((r["theta_star"] + np.pi / 5 + np.pi) % (2 * np.pi)) - np.pi) < 1e-6


def test_structural_difference_survives_alignment():
    """A genuinely different field cannot be aligned away: aligned distance stays > 0."""
    F, G = _field(3), _field(4)
    r = gad(F, G)
    assert r["aligned_distance"] > 0.1
    assert r["aligned_distance"] <= r["raw_distance"] + 1e-9   # alignment never increases distance


def test_different_winding_targets_are_distinguished():
    """Analytic single-charge phase fields W=+1 vs W=-1 (same amplitude): structurally different."""
    n = 24
    x = np.arange(n) - (n - 1) / 2.0
    X, Y = np.meshgrid(x, x, indexing="ij")
    amp = np.tanh(np.sqrt(X ** 2 + Y ** 2) / 3.0)
    wp = amp * np.exp(1j * np.arctan2(Y, X))       # winding +1
    wm = amp * np.exp(-1j * np.arctan2(Y, X))      # winding -1
    r = gad(wp, wm)
    assert r["aligned_distance"] > 0.1 and r["gauge_overlap"] < 0.99


def test_aligned_equals_invariant():
    F, G = _field(5), _field(6)
    r = gad(F, np.exp(0.9j) * (F + 0.4 * G))
    assert abs(r["aligned_distance"] - r["invariant_distance"]) < 1e-9


def test_zero_and_near_zero_norm_handled():
    F = _field(7)
    r0 = gad(F, np.zeros_like(F))
    assert r0["gauge_overlap"] is None and r0["zero_norm"] and np.isfinite(r0["raw_distance"])
    rn = gad(np.zeros_like(F), np.zeros_like(F))
    assert rn["zero_norm"] and rn["gauge_overlap"] is None


def test_seeded_noise_monotonicity():
    """Aligned distance grows monotonically as increasing noise is added to a copy of F."""
    F = _field(8)
    rng = np.random.default_rng(99)
    noise = rng.normal(size=F.shape) + 1j * rng.normal(size=F.shape)
    prev = -1.0
    for a in (0.0, 0.1, 0.3, 0.6, 1.0):
        d = gad(F, F + a * noise)["aligned_distance"]
        assert d >= prev - 1e-9
        prev = d


def test_nan_inf_rejected_not_propagated():
    F, G = _field(10), _field(11)
    Fn = F.copy()
    Fn[0, 0] = np.nan
    Fn[1, 1] = np.inf + 0j
    r = gad(Fn, G)
    assert r["finite_count"] == F.size - 2 and r["total_count"] == F.size
    assert np.isfinite(r["raw_distance"]) and np.isfinite(r["aligned_distance"])


def test_sign_convention_is_documented_and_applied_to_second_field():
    F = _field(12)
    r = gad(F, np.exp(1j * 0.4) * F)
    assert "second field" in r["sign_convention"].lower()
    # applying theta_star to B reproduces the reported aligned distance ~ 0
    assert r["aligned_distance"] < 1e-9
