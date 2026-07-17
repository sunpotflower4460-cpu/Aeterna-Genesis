"""Synthetic validation for genesis/diagnostics/vessel_flux_3d.py (Active Vessel P10, PR-1, role V).

No physics claims -- checks against the F1 V0-validated Boltzmann/Nernst partition instrument
(`vessel_permeability`) and simple analytic mass-balance identities.
"""
import numpy as np

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


def test_stoichiometric_invariant_is_weighted_sum():
    masses = dict(a=10.0, b=5.0, w=2.0)
    inv = vf.stoichiometric_invariant(masses, dict(a=1.0, b=1.0, w=1.0))
    assert abs(inv - 17.0) < 1e-9
    inv2 = vf.stoichiometric_invariant(masses, dict(a=1.0, b=1.0, w=0.0))
    assert abs(inv2 - 15.0) < 1e-9


def test_mass_balance_residual_zero_for_consistent_accounting():
    assert vf.mass_balance_residual(10.0, 13.0, sources=5.0, sinks=2.0) < 1e-12


def test_mass_balance_residual_nonzero_flags_inconsistent_accounting():
    # an actual mass jump of 5 but claimed sources/sinks explaining only 2 -> nonzero residual.
    r = vf.mass_balance_residual(10.0, 15.0, sources=2.0, sinks=0.0)
    assert abs(r - 3.0) < 1e-9
