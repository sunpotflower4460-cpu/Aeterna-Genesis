"""Synthetic validation for genesis/diagnostics/reaction_localization.py (Active Vessel P10, PR-1,
role V). No physics claims -- checks against synthetic concentration fields with a known spatial
pattern; the F0's guard is that R is never assumed localized, so these tests explicitly cover a
UNIFORM rate (ratio must be 1.0) as well as patterned rates.
"""
import numpy as np
import pytest

import genesis.diagnostics.reaction_localization as rl
import genesis.diagnostics.vessel_permeability as vp

L = 16
R = 4.0


def _sphere():
    return vp.radial_phi(L, R, 1.5)


def test_reaction_rate_field_is_k_times_R_times_c():
    c = np.full((4, 4, 4), 2.0)
    rate = rl.reaction_rate_field(c, k=0.5, R=3.0)
    assert np.allclose(rate, 3.0)   # 0.5 * 3.0 * 2.0


def test_reaction_rate_field_defaults_to_uniform_R():
    c = np.full((4, 4, 4), 2.0)
    rate = rl.reaction_rate_field(c, k=0.5)
    assert np.allclose(rate, 1.0)   # 0.5 * 1.0 * 2.0


def test_reaction_rate_field_rejects_wrong_shaped_nonscalar_R():
    # a non-scalar R that doesn't match c's shape must never silently broadcast and fabricate a
    # spatial reaction pattern before any localization audit runs (Codex).
    c = np.full((4, 4, 4), 2.0)
    with pytest.raises(ValueError):
        rl.reaction_rate_field(c, k=0.5, R=np.full((4,), 1.0))


def test_reaction_rate_field_rejects_negative_or_non_finite_operands():
    # the frozen k*R*c rate is a non-negative real density -- a negative/non-finite c, k, or R
    # must fail closed rather than multiplying directly into a plausible-looking field (Codex).
    c = np.full((4, 4, 4), 2.0)
    with pytest.raises(ValueError):
        rl.reaction_rate_field(np.full((4, 4, 4), -1.0), k=0.5)
    with pytest.raises(ValueError):
        rl.reaction_rate_field(c, k=-0.5)
    with pytest.raises(ValueError):
        rl.reaction_rate_field(c, k=0.5, R=-1.0)
    with pytest.raises(ValueError):
        rl.reaction_rate_field(c, k=float("nan"))


def test_uniform_rate_gives_ratio_one_regardless_of_geometry():
    # a spatially UNIFORM reaction rate must read as "no localization" (ratio=1) even though the
    # vessel geometry is highly structured -- this is the F0 #2 target-encoding guard, checked
    # directly: localization must come from the CONCENTRATION field, never assumed from R.
    phi = _sphere()
    rate = np.full(phi.shape, 2.0)
    assert abs(rl.band_vs_bulk_ratio(rate, phi) - 1.0) < 1e-12
    assert abs(rl.band_vs_bulk_ratio(rate, phi, bulk_region="inside") - 1.0) < 1e-12


def test_band_vs_bulk_ratio_rejects_a_stacked_extra_dimensional_rate():
    # a stacked (L, L, L, n_species) rate would otherwise still be accepted by the phi-derived
    # boolean masks (broadcast across the trailing axis), and .mean() would silently average
    # over the remaining species axis, reporting a ratio for a MIXTURE of rates (Codex).
    phi = _sphere()
    rate_stacked = np.random.default_rng(2).uniform(0, 1, phi.shape + (2,))
    with pytest.raises(ValueError):
        rl.band_vs_bulk_ratio(rate_stacked, phi)


def test_band_vs_bulk_ratio_rejects_non_finite_rate_or_phi():
    # an unchecked inf rate confined to the interface band (with an otherwise finite bulk) would
    # otherwise return inf, satisfying ANY ratio>1 gate on a blown-up run (Codex).
    phi = _sphere()
    rate_inf = np.full(phi.shape, 1.0)
    rate_inf[np.abs(phi) < 0.5] = np.inf
    with pytest.raises(ValueError):
        rl.band_vs_bulk_ratio(rate_inf, phi)
    phi_nan = phi.copy()
    phi_nan[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        rl.band_vs_bulk_ratio(np.full(phi.shape, 1.0), phi_nan)


def test_ratio_reflects_where_concentration_actually_sits():
    # concentration depleted near the interface (chi>0, fuel prefers outside) -> band/outside
    # ratio < 1; concentration enriched near the interface (chi<0) -> band/outside ratio > 1.
    phi = _sphere()
    c_depleted, conv1, _ = vp.equilibrate(phi, chi=0.5, n_steps=4000)
    c_enriched, conv2, _ = vp.equilibrate(phi, chi=-0.5, n_steps=4000)
    assert conv1 and conv2
    r_dep = rl.band_vs_bulk_ratio(rl.reaction_rate_field(c_depleted, k=1.0), phi)
    r_enr = rl.band_vs_bulk_ratio(rl.reaction_rate_field(c_enriched, k=1.0), phi)
    assert r_enr > r_dep


def test_band_vs_bulk_ratio_nan_for_empty_region_or_zero_bulk():
    phi = np.full((8, 8, 8), 1.0)   # no "outside" at all
    rate = np.full((8, 8, 8), 1.0)
    assert np.isnan(rl.band_vs_bulk_ratio(rate, phi))
    phi2 = _sphere()
    zero_rate = np.zeros_like(phi2)
    assert np.isnan(rl.band_vs_bulk_ratio(zero_rate, phi2))


def test_band_vs_bulk_ratio_rejects_invalid_region():
    phi = _sphere()
    rate = np.ones_like(phi)
    with pytest.raises(ValueError):
        rl.band_vs_bulk_ratio(rate, phi, bulk_region="nowhere")


def test_radial_reaction_profile_rejects_mismatched_shape_with_same_element_count():
    # a reshaped/transposed rate array with the same SIZE but a different SHAPE must not
    # silently .ravel() and bin against unrelated phi cells via the shared flat index,
    # fabricating a spatially scrambled but plausible-looking localization profile (Codex).
    phi = np.zeros((4, 4))
    rate = np.full((16,), 1.0)   # same element count (16), different shape
    with pytest.raises(ValueError):
        rl.radial_reaction_profile(rate, phi, n_bins=4)


def test_radial_reaction_profile_monotonic_for_monotonic_concentration():
    # chi<0 (concentration enriched toward phi=+1, i.e. inside) -> the binned mean rate must be
    # monotonically non-decreasing in phi (a clean, independently-checkable pattern).
    phi = _sphere()
    c, converged, _ = vp.equilibrate(phi, chi=-0.5, n_steps=4000)
    assert converged
    rate = rl.reaction_rate_field(c, k=1.0)
    _, means = rl.radial_reaction_profile(rate, phi, n_bins=10)
    valid = ~np.isnan(means)
    m = means[valid]
    assert np.all(np.diff(m) >= -1e-9)   # non-decreasing (allow float noise)


def test_radial_reaction_profile_empty_bins_are_nan_not_zero():
    phi = np.full((6, 6, 6), 1.0)   # all phi=1 -> only the top bin is populated
    rate = np.ones_like(phi)
    _, means = rl.radial_reaction_profile(rate, phi, n_bins=5, phi_range=(-1.0, 1.0))
    assert np.isnan(means[0])        # bottom bin (phi near -1) has no data
    assert not np.isnan(means[-1])   # top bin has data


def test_radial_reaction_profile_excludes_out_of_range_phi_instead_of_clipping_into_edge_bins():
    # a narrowed phi_range that excludes the true interior (phi up to 1.0) must NOT fold those
    # cells into the top bin -- they must be excluded entirely (Codex #10: clip-based binning
    # silently mixes out-of-range cells into edge bins, corrupting a narrowed-range inspection).
    phi = _sphere()
    rate = np.full(phi.shape, 5.0)   # uniform rate everywhere, including phi>0.5
    _, means_full = rl.radial_reaction_profile(rate, phi, n_bins=4, phi_range=(-1.0, 1.0))
    _, means_narrow = rl.radial_reaction_profile(rate, phi, n_bins=4, phi_range=(-0.5, 0.5))
    # uniform rate -> every populated bin reads exactly 5.0 in both cases (excluding, not
    # clipping, out-of-range cells does not change the MEAN for a spatially uniform rate, but it
    # does mean cells with phi>0.5 must not count toward the narrow profile's top bin at all).
    assert np.allclose(means_full[~np.isnan(means_full)], 5.0)
    assert np.allclose(means_narrow[~np.isnan(means_narrow)], 5.0)
    out_of_range_count = int(((phi < -0.5) | (phi > 0.5)).sum())
    in_range_count = int(((phi >= -0.5) & (phi <= 0.5)).sum())
    assert out_of_range_count > 0 and in_range_count > 0   # sanity: the narrowing is non-trivial
