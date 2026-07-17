"""Synthetic validation for genesis/diagnostics/vessel_geometry_3d.py (Active Vessel P10, PR-1, role V).

No physics claims -- every check here is against an ANALYTICALLY KNOWN synthetic sphere geometry
(reusing F1 V0's validated `vessel_permeability.radial_phi`), not P10 physics run data.
"""
import numpy as np

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


def test_interface_width_fraction_shrinks_with_sharper_interface():
    phi_diffuse = _sphere(width=3.0)
    phi_sharp = _sphere(width=0.5)
    assert vg.interface_width_fraction(phi_sharp) < vg.interface_width_fraction(phi_diffuse)


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


def test_detect_split_fusion_none_when_component_count_unchanged():
    phi = _sphere()
    mask = vg.vessel_mask(phi)
    ev = vg.detect_split_fusion(mask, mask)
    assert ev == dict(n_prev=1, n_curr=1, event="none")


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
