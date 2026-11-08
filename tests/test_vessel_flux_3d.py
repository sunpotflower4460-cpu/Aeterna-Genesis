"""Synthetic validation for genesis/diagnostics/vessel_flux_3d.py (Active Vessel P10, PR-1, role V).

No physics claims -- checks against the F1 V0-validated Boltzmann/Nernst partition instrument
(`vessel_permeability`) and simple analytic mass-balance identities.
"""
import numpy as np
import pytest

import genesis.diagnostics.vessel_flux_3d as vf
import genesis.diagnostics.vessel_permeability as vp

L = 16
R = 4.0
WIDTH = 1.5


def _sphere():
    return vp.radial_phi(L, R, WIDTH)


def test_species_partition_ratio_matches_f1_v0_instrument():
    # this module's partition readout must agree EXACTLY with the already-validated F1 V0
    # instrument on the same field (no silent redefinition of "partition ratio").
    phi = _sphere()
    c, converged, _ = vp.equilibrate(phi, chi=0.5, n_steps=4000)
    assert converged
    assert abs(vf.species_partition_ratio(c, phi) - vp.partition_ratio(c, phi)) < 1e-12


def test_species_partition_ratio_nan_when_region_empty():
    phi = np.full((8, 8, 8), 1.0)   # no "outside" region at all
    c = np.full((8, 8, 8), 1.0)
    assert np.isnan(vf.species_partition_ratio(c, phi))


def test_species_partition_ratio_nan_not_inf_when_outside_concentration_is_zero():
    # a depleted/never-present species outside must read as an undefined (NaN) partition, not
    # `inf` -- `inf` could pass a downstream "ratio>=2 selectivity" check as if infinitely
    # selective instead of failing closed on an unmeasurable ratio (Codex).
    phi = _sphere()
    c = np.zeros_like(phi)
    c[phi > 0.5] = 1.0   # nonzero inside, exactly zero outside
    assert np.isnan(vf.species_partition_ratio(c, phi))


def test_species_partition_ratio_rejects_a_stacked_extra_dimensional_c():
    # a stacked (phi.shape + (n_species,)) c would otherwise still be accepted by the phi-derived
    # boolean mask (broadcast across the trailing axis), and .mean() would silently average over
    # the trailing species axis, reporting a ratio for a MIXTURE of species (Codex).
    phi = _sphere()
    c_stacked = np.random.default_rng(0).uniform(0, 1, phi.shape + (2,))
    with pytest.raises(ValueError):
        vf.species_partition_ratio(c_stacked, phi)


def test_species_partition_ratio_rejects_invalid_c_or_phi():
    # an unchecked inf inside-concentration with a finite outside would otherwise return inf,
    # satisfying a downstream ratio>=2 selectivity/Gate-I check as if it were real (Codex);
    # a boolean occupancy mask would have True/False silently averaged as concentrations.
    phi = _sphere()
    c_inf = np.full(phi.shape, 1.0)
    c_inf[phi > 0.5] = np.inf
    with pytest.raises(ValueError):
        vf.species_partition_ratio(c_inf, phi)
    with pytest.raises(ValueError):
        vf.species_partition_ratio(np.full(phi.shape, True), phi)
    with pytest.raises(ValueError):
        vf.species_partition_ratio(np.full(phi.shape, 1.0), np.where(phi > 0, phi, np.nan))


def test_net_boundary_flux_vanishes_at_equilibrium_but_not_in_transient():
    phi = _sphere()
    c_eq, converged, _ = vp.equilibrate(phi, chi=0.5, n_steps=4000)
    assert converged
    flux_eq = vf.net_boundary_flux(c_eq, phi, chi=0.5)
    c0 = np.full(phi.shape, 1.0)
    flux_early = vf.net_boundary_flux(c0, phi, chi=0.5)
    assert abs(flux_eq) < 1e-6
    assert abs(flux_early) > 100 * max(abs(flux_eq), 1e-12)


def test_instantaneous_face_flux_matches_vessel_permeability_relax_step_direction():
    # the SG face-flux instrument here must reproduce the same net d_t c as F1 V0's relax_step
    # (both are the same Boltzmann-balanced law -- this checks they haven't drifted apart).
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    c_after = vp.relax_step(c, phi, chi=0.5, D=1.0, dt=1.0)
    dc_expected = c_after - c
    dc_measured = np.zeros_like(c)
    for ax in range(c.ndim):
        J = vf.instantaneous_face_flux(c, phi, chi=0.5, D=1.0, axis=ax)
        L_ = c.shape[ax]
        sl = [slice(None)] * 3
        sl[ax] = L_ - 1
        J[tuple(sl)] = 0.0
        Jm = np.roll(J, 1, axis=ax)
        sl0 = [slice(None)] * 3
        sl0[ax] = 0
        Jm[tuple(sl0)] = 0.0
        dc_measured += (Jm - J)
    assert np.allclose(dc_measured, dc_expected, atol=1e-10)


def test_instantaneous_face_flux_zeroes_the_domain_boundary_face():
    # the last face along an axis (which np.roll(-1) would otherwise wrap to a nonexistent
    # periodic neighbour) must read zero, matching vessel_permeability.relax_step's Neumann
    # (no-flux) domain boundary -- this instrument must not silently report a periodic variant.
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    for ax in range(3):
        J = vf.instantaneous_face_flux(c, phi, chi=0.5, D=1.0, axis=ax)
        sl = [slice(None)] * 3
        sl[ax] = phi.shape[ax] - 1
        assert np.allclose(J[tuple(sl)], 0.0)


def test_instantaneous_face_flux_rejects_a_wrong_shaped_nonscalar_mobility():
    # a broadcast-compatible-but-incomplete D (e.g. a 1-element array) must not silently
    # broadcast across the whole 3-D flux calculation and report a valid-looking permeability
    # from incomplete mobility metadata (Codex).
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, D=np.array([1.0]), axis=0)


def test_instantaneous_face_flux_accepts_a_full_field_mobility():
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    D_field = np.full(phi.shape, 2.0)
    J = vf.instantaneous_face_flux(c, phi, chi=0.5, D=D_field, axis=0)
    assert J.shape == phi.shape


def test_instantaneous_face_flux_rejects_mismatched_c_phi_shapes():
    # a broadcast-compatible-but-different grid for c (e.g. a one-slice field against a full
    # 3-D interface) must not silently broadcast together in the roll/Bernoulli arithmetic and
    # produce a flux net_boundary_flux can treat as measured permeability (Codex).
    phi = np.full((4, 4, 4), 1.0)
    c_bad = np.full((4, 4, 1), 1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c_bad, phi, chi=0.5, axis=0)


def test_instantaneous_face_flux_rejects_invalid_mobility():
    # D is a physical mobility -- negative makes the SG flux anti-diffusive, boolean silently
    # casts to 1.0/0.0, non-finite propagates to an infinite flux; all invalid measurements
    # that net_boundary_flux would otherwise sum as if they were real permeability evidence
    # (Codex).
    phi = np.full((4, 4, 4), 1.0)
    c = np.full((4, 4, 4), 1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, D=-1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, D=True)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, D=float("inf"))


def test_instantaneous_face_flux_rejects_invalid_RT_or_chi():
    # RT=0 divides by zero forming beta=chi/RT; a negative/non-finite RT or non-finite chi
    # produces an invalid SG flux instead of failing closed (CodeRabbit/Codex).
    phi = np.full((4, 4, 4), 1.0)
    c = np.full((4, 4, 4), 1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, RT=0.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=0.5, RT=-1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi, chi=float("nan"))


def test_instantaneous_face_flux_rejects_invalid_c_or_phi():
    # a negative/non-finite c produces an anti-physical or infinite flux, and a non-finite phi
    # makes the Bernoulli factors blow up -- either would otherwise be treated by
    # net_boundary_flux as real measured permeability evidence (Codex).
    phi = np.full((4, 4, 4), 1.0)
    c = np.full((4, 4, 4), 1.0)
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(np.full((4, 4, 4), -1.0), phi, chi=0.5)
    phi_nan = np.full((4, 4, 4), 1.0)
    phi_nan[0, 0, 0] = float("nan")
    with pytest.raises(ValueError):
        vf.instantaneous_face_flux(c, phi_nan, chi=0.5)


def test_instantaneous_face_flux_rt_scaling_matches_beta_convention():
    # RT must divide chi exactly as vessel_permeability.relax_step's beta = chi/RT -- doubling RT
    # while doubling chi must reproduce the RT=1 flux exactly (same beta).
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    J1 = vf.instantaneous_face_flux(c, phi, chi=0.5, D=1.0, axis=0, RT=1.0)
    J2 = vf.instantaneous_face_flux(c, phi, chi=1.0, D=1.0, axis=0, RT=2.0)
    assert np.allclose(J1, J2)


def test_total_mass_matches_sum():
    c = np.random.default_rng(0).uniform(0, 1, (6, 6, 6))
    assert abs(vf.total_mass(c) - float(c.sum())) < 1e-9


def test_total_mass_rejects_invalid_c():
    # an unchecked invalid field can hide corruption behind a plausible-looking total, e.g.
    # [-1, 2] sums to a plausible 1, and a boolean mask silently sums as a real amount (Codex).
    with pytest.raises(ValueError):
        vf.total_mass(np.array([-1.0, 2.0]))
    with pytest.raises(ValueError):
        vf.total_mass(np.array([True, False]))
    with pytest.raises(ValueError):
        vf.total_mass(np.array([1.0, float("inf")]))


def test_stoichiometric_invariant_is_weighted_sum():
    masses = dict(a=10.0, b=5.0, w=2.0)
    inv = vf.stoichiometric_invariant(masses, dict(a=1.0, b=1.0, w=1.0))
    assert abs(inv - 17.0) < 1e-9
    inv2 = vf.stoichiometric_invariant(masses, dict(a=1.0, b=1.0, w=0.0))
    assert abs(inv2 - 15.0) < 1e-9


def test_stoichiometric_invariant_treats_species_absent_from_masses_as_zero():
    # a waste/product species genuinely absent from a sparse before/after mass dict (not yet
    # appeared) must not abort the computation -- treated as mass 0, matching
    # thermodynamic_ledger.stoichiometric_balance_error's identical sparse-species handling.
    masses = dict(a=10.0)   # "w" not present yet
    inv = vf.stoichiometric_invariant(masses, dict(a=1.0, w=1.0))
    assert abs(inv - 10.0) < 1e-9


def test_stoichiometric_invariant_rejects_negative_mass():
    # a negative species mass is never physically valid -- must not silently flow into the
    # invariant computation (Codex: matches thermodynamic_ledger's identical discipline).
    with pytest.raises(ValueError):
        vf.stoichiometric_invariant({"a": -1.0}, {"a": 1.0})


def test_stoichiometric_invariant_rejects_boolean_mass():
    with pytest.raises(ValueError):
        vf.stoichiometric_invariant({"a": True}, {"a": 1.0})


def test_stoichiometric_invariant_rejects_non_finite_mass():
    with pytest.raises(ValueError):
        vf.stoichiometric_invariant({"a": float("inf")}, {"a": 1.0})


def test_stoichiometric_invariant_rejects_invalid_coefficient():
    # a NaN or boolean coeffs[k] must fail closed, not yield a misleading invariant or an
    # uncontrolled exception -- a genuinely negative coefficient remains valid (CodeRabbit).
    with pytest.raises(ValueError):
        vf.stoichiometric_invariant({"a": 1.0}, {"a": float("nan")})
    with pytest.raises(ValueError):
        vf.stoichiometric_invariant({"a": 1.0}, {"a": True})
    assert vf.stoichiometric_invariant({"a": 1.0}, {"a": -1.0}) == -1.0


def test_mass_balance_residual_zero_for_consistent_accounting():
    assert vf.mass_balance_residual(10.0, 13.0, sources=5.0, sinks=2.0) < 1e-12


def test_mass_balance_residual_nonzero_flags_inconsistent_accounting():
    # an actual mass jump of 5 but claimed sources/sinks explaining only 2 -> nonzero residual.
    r = vf.mass_balance_residual(10.0, 15.0, sources=2.0, sinks=0.0)
    assert abs(r - 3.0) < 1e-9


def test_mass_balance_residual_rejects_invalid_totals():
    # an impossible negative/boolean total or source/sink magnitude must fail closed, not
    # arithmetically balance to a coincidental zero (e.g. mass_before=-1, mass_after=0,
    # sources=1) and hide corrupted accounting instead of surfacing it (Codex).
    with pytest.raises(ValueError):
        vf.mass_balance_residual(-1.0, 0.0, sources=1.0)
    with pytest.raises(ValueError):
        vf.mass_balance_residual(1.0, 2.0, sources=True)
