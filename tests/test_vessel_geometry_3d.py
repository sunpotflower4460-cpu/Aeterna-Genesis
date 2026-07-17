"""Synthetic validation for genesis/diagnostics/vessel_geometry_3d.py (Active Vessel P10, PR-1, role V).

No physics claims -- every check here is against an ANALYTICALLY KNOWN synthetic sphere geometry
(reusing F1 V0's validated `vessel_permeability.radial_phi`), not P10 physics run data.
"""
import numpy as np
import pytest

import genesis.diagnostics.vessel_geometry_3d as vg
import genesis.diagnostics.vessel_permeability as vp


def _sphere(L=40, R=10.0, width=1.5):
    return vp.radial_phi(L, R, width)


def test_single_sphere_is_one_closed_component_genus_zero():
    phi = _sphere()
    mask = vg.vessel_mask(phi)
    n, sizes = vg.connected_components(mask)
    assert n == 1
    assert sizes[0] == int(mask.sum())
    bt = vg.boundary_topology(mask)
    assert bt["b0"] == 1
    assert bt["b1"] == 0
    assert bt["b2"] == 0
    assert bt["is_closed_single_component"] is True
    assert bt["genus"] == 0


def _seam_crossing_sphere(L=20, R=4.0, width=1.5, center_x=0.0, center_yz=10.0):
    idx = np.arange(L, dtype=float)
    X, Y, Z = np.meshgrid(idx, idx, idx, indexing="ij")
    dx = np.minimum(np.abs(X - center_x), L - np.abs(X - center_x))
    r = np.sqrt(dx ** 2 + (Y - center_yz) ** 2 + (Z - center_yz) ** 2)
    return np.tanh((R - r) / width)


def test_interface_width_is_correct_for_a_seam_crossing_vessel():
    # np.gradient's default one-sided edge difference would corrupt the interface-width readout
    # right at the domain seam -- must use a periodic gradient so a seam-crossing vessel
    # measures the same intrinsic width as one placed away from any boundary (Codex).
    phi = _seam_crossing_sphere(width=1.5)
    assert phi[0].max() > 0.5 and phi[-1].max() > 0.5   # sanity: genuinely touches both seam faces
    w = vg.interface_width(phi, band_thresh=0.9)
    assert abs(w - 1.5) < 0.1


def test_mean_curvature_is_correct_for_a_seam_crossing_vessel():
    phi = _seam_crossing_sphere(R=4.0, width=1.5)
    kappa = vg.mean_curvature(phi, band_thresh=0.9)
    known = 2.0 / 4.0
    assert abs(kappa - known) < 0.15 * known


def test_connected_components_is_periodic_across_the_domain_seam():
    # a component that crosses the periodic boundary must count as ONE object, matching the
    # periodic-box vessel model (surface_area already treats the domain as periodic) -- plain
    # ndimage.label alone would split a seam-crossing sphere into two labels (Codex).
    L = 20
    idx = np.arange(L, dtype=float)
    X, Y, Z = np.meshgrid(idx, idx, idx, indexing="ij")
    dx = np.minimum(np.abs(X - 0), L - np.abs(X - 0))   # periodic distance along x from x=0
    r = np.sqrt(dx ** 2 + (Y - 10) ** 2 + (Z - 10) ** 2)
    mask = r < 4.0
    assert mask[0].any() and mask[-1].any()   # sanity: genuinely touches both seam faces
    n, sizes = vg.connected_components(mask)
    assert n == 1
    assert sizes[0] == int(mask.sum())


def test_connected_components_still_separates_genuinely_distinct_components():
    # periodic merging must not glue together components that are NOT seam-connected.
    L = 20
    idx = np.arange(L, dtype=float)
    X, Y, Z = np.meshgrid(idx, idx, idx, indexing="ij")
    r1 = np.sqrt((X - 5) ** 2 + (Y - 10) ** 2 + (Z - 10) ** 2)
    r2 = np.sqrt((X - 15) ** 2 + (Y - 10) ** 2 + (Z - 10) ** 2)
    mask = (r1 < 3.0) | (r2 < 3.0)
    n, sizes = vg.connected_components(mask)
    assert n == 2
    assert len(sizes) == 2


def test_volume_matches_known_sphere_volume():
    for R in (6.0, 10.0, 15.0):
        L = int(R * 4)
        phi = _sphere(L=L, R=R)
        mask = vg.vessel_mask(phi)
        measured = vg.volume(mask)
        known = 4.0 / 3.0 * np.pi * R ** 3
        assert abs(measured - known) < 0.05 * known, "R=%g: measured=%g known=%g" % (R, measured, known)


def test_volume_fraction_matches_volume_over_total():
    phi = _sphere()
    mask = vg.vessel_mask(phi)
    assert abs(vg.volume_fraction(mask) - vg.volume(mask) / mask.size) < 1e-12


def test_surface_area_scales_as_r_squared_with_stable_known_bias():
    # face-counting surface area has a known, roughly-constant overestimate bias (~1.5x) for a
    # smoothly curved surface -- checked here as a STABLE ratio across R, not an exact match
    # (the bias itself is documented honestly in vessel_geometry_3d.surface_area's docstring).
    ratios = []
    for R in (6.0, 10.0, 15.0):
        L = int(R * 4)
        phi = _sphere(L=L, R=R)
        mask = vg.vessel_mask(phi)
        measured = vg.surface_area(mask)
        known = 4.0 * np.pi * R ** 2
        ratios.append(measured / known)
    for r in ratios:
        assert 1.3 < r < 1.7, "surface-area bias ratio out of documented band: %g" % r
    assert max(ratios) - min(ratios) < 0.1, "bias ratio should be stable across R, got %s" % ratios


def test_interface_width_shrinks_with_sharper_interface():
    phi_diffuse = _sphere(width=3.0)
    phi_sharp = _sphere(width=0.5)
    assert vg.interface_width(phi_sharp) < vg.interface_width(phi_diffuse)


def test_interface_width_recovers_the_true_width_parameter():
    # the tanh-profile identity must recover the ACTUAL width used to build the synthetic
    # sphere (sanity-checks the analytic derivation). A width close to the grid spacing (dx=1)
    # is finite-difference-resolution-limited (the width=0.5 case has ~12% error since the
    # profile is barely resolved by the grid) so the tolerance is looser there; widths well
    # above dx recover to <1%.
    tolerances = {0.5: 0.15, 1.5: 0.05, 3.0: 0.05}
    for width, tol in tolerances.items():
        phi = _sphere(width=width)
        measured = vg.interface_width(phi)
        assert abs(measured - width) < tol * width, "width=%g: measured=%g" % (width, measured)


def test_interface_width_is_independent_of_vessel_size_unlike_band_volume_fraction():
    # a band VOLUME FRACTION shrinks as the vessel grows even at fixed physical interface
    # thickness (Codex) -- interface_width must NOT have that size-dependence: the same
    # width=1.5 profile must measure ~1.5 regardless of R.
    widths = []
    for R in (6.0, 10.0, 15.0):
        L = int(R * 4)
        phi = _sphere(L=L, R=R, width=1.5)
        widths.append(vg.interface_width(phi))
    for w in widths:
        assert abs(w - 1.5) < 0.1, "width should stay ~1.5 regardless of R, got %s" % widths
    assert max(widths) - min(widths) < 0.05, "width should be stable across R, got %s" % widths


def test_mean_curvature_matches_known_sphere_curvature():
    # convention: kappa = -div(grad(phi)/|grad(phi)|) = 2/R for a sphere of radius R under this
    # module's phi=tanh((R-r)/width) sign convention (grad(phi) points inward) -- see docstring.
    for R in (6.0, 10.0, 15.0):
        L = int(R * 4)
        phi = _sphere(L=L, R=R, width=1.5)
        measured = vg.mean_curvature(phi)
        known = 2.0 / R
        assert abs(measured - known) < 0.15 * known, "R=%g: measured=%g known=%g" % (R, measured, known)


def test_mean_curvature_field_matches_scalar_average_over_band():
    phi = _sphere()
    field = vg.mean_curvature_field(phi)
    band = np.abs(phi) < 0.9
    assert abs(float(field[band].mean()) - vg.mean_curvature(phi)) < 1e-9


def test_no_defect_field_has_zero_components():
    phi = np.full((16, 16, 16), -1.0)   # uniform "outside" -- no vessel anywhere
    mask = vg.vessel_mask(phi)
    n, sizes = vg.connected_components(mask)
    assert n == 0
    assert sizes == []
    assert vg.volume(mask) == 0.0
    assert vg.volume_fraction(mask) == 0.0


def test_vessel_mask_rejects_non_finite_phi():
    # a solver blow-up leaving NaN/inf cells must fail closed, not be silently classified as
    # outside/inside by the bare > comparison (nan > thresh is always False, inf > thresh is
    # always True) -- this would otherwise corrupt every downstream mask-consuming diagnostic
    # (connected_components, boundary_topology, surface_area, volume, split/fusion) (Codex).
    phi = np.array([1.0, np.nan, -1.0])
    with pytest.raises(ValueError):
        vg.vessel_mask(phi)
    phi2 = np.array([1.0, np.inf, -1.0])
    with pytest.raises(ValueError):
        vg.vessel_mask(phi2)


def test_detect_split_fusion_rejects_mismatched_frame_shapes():
    # a split/fusion event is a same-grid temporal change -- frames accidentally taken from
    # different grid sizes or cropped domains must fail closed rather than being compared by
    # component count alone, which connected_components can still compute independently on
    # either shape and report a plausible but meaningless classification (Codex).
    mask_prev = np.zeros((8, 8, 8), dtype=bool)
    mask_prev[1, 1, 1] = True
    mask_curr = np.zeros((4, 4, 4), dtype=bool)
    mask_curr[1, 1, 1] = True
    with pytest.raises(ValueError):
        vg.detect_split_fusion(mask_prev, mask_curr)


def test_detect_split_fusion_none_when_component_count_unchanged():
    phi = _sphere()
    mask = vg.vessel_mask(phi)
    ev = vg.detect_split_fusion(mask, mask)
    assert ev == dict(n_prev=1, n_curr=1, event="none")


def test_detect_split_fusion_ambiguous_when_count_unchanged_but_mask_actually_moved():
    # same component COUNT (1 -> 1) but the mask itself changed (the sphere moved) -- must read
    # 'ambiguous', not silently 'none', per this function's own documented contract.
    L = 40
    mask_prev = vg.vessel_mask(_sphere(L=L, R=10.0))
    mask_curr = vg.vessel_mask(vp.radial_phi(L, 10.0, 1.5, center=(L - 1) / 2.0 + 2.0))
    n_prev, _ = vg.connected_components(mask_prev)
    n_curr, _ = vg.connected_components(mask_curr)
    assert n_prev == n_curr == 1
    ev = vg.detect_split_fusion(mask_prev, mask_curr)
    assert ev["event"] == "ambiguous"


def test_detect_split_fusion_appear_from_empty():
    empty = np.zeros((16, 16, 16), dtype=bool)
    phi = _sphere(L=16, R=4.0)
    mask = vg.vessel_mask(phi)
    ev = vg.detect_split_fusion(empty, mask)
    assert ev["n_prev"] == 0
    assert ev["n_curr"] == 1
    assert ev["event"] == "appear"


def test_detect_split_fusion_split_when_two_components_appear():
    L = 40
    single = vg.vessel_mask(_sphere(L=L, R=10.0))
    # two well-separated small spheres (synthetic split target, not a physics claim)
    grid = np.meshgrid(*[np.arange(L, dtype=float)] * 3, indexing="ij")
    r1 = np.sqrt((grid[0] - 10) ** 2 + (grid[1] - 20) ** 2 + (grid[2] - 20) ** 2)
    r2 = np.sqrt((grid[0] - 30) ** 2 + (grid[1] - 20) ** 2 + (grid[2] - 20) ** 2)
    two = (r1 < 4.0) | (r2 < 4.0)
    ev = vg.detect_split_fusion(single, two)
    assert ev["n_prev"] == 1
    assert ev["n_curr"] == 2
    assert ev["event"] == "split"
