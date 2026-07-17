"""Synthetic F1 V0 validation for genesis/diagnostics/vessel_permeability.py (Active Vessel P10, role V).

Validates the fixed-geometry selective-permeability instrument against the KNOWN Boltzmann/Nernst
partition law, and — the campaign's core honesty point — that selectivity comes from the free-energy
partition coefficient `chi` under a SINGLE shared mobility, NOT from hand-placed species-specific
diffusivity (target-encoding hole flagged by external review on the F0). All claims here are about a
HAND-PLACED fixed sphere; nothing here claims an emergent vessel.
"""
import numpy as np

import genesis.diagnostics.vessel_permeability as vp

L = 16
RADIUS = 4.0
WIDTH = 1.5


def _sphere():
    return vp.radial_phi(L, RADIUS, WIDTH)


def test_fixed_sphere_is_inside_positive_outside_negative():
    phi = _sphere()
    c = (L - 1) / 2.0
    assert phi[int(c), int(c), int(c)] > 0.9        # centre is well inside
    assert phi[0, 0, 0] < -0.9                        # a corner is well outside
    assert -1.0 <= phi.min() and phi.max() <= 1.0


def test_boltzmann_partition_law_is_recovered():
    # after relaxation, c(x) exp(chi phi(x)) must be spatially uniform -> c ∝ exp(-chi phi):
    # the geometry-independent statement of the Nernst/Boltzmann partition (the Gate-I known law).
    phi = _sphere()
    _, converged, cv = vp.equilibrate(phi, chi=0.5, n_steps=4000)
    assert converged, f"Boltzmann invariant not uniform: CV={cv:.4g}"
    assert cv < 1e-2


def test_partition_direction_and_magnitude_match_known_law():
    # chi>0 makes c accumulate OUTSIDE (c ∝ exp(-chi phi), phi=+1 inside -> smaller c inside);
    # the measured inside/outside ratio must match the known-law prediction for THIS geometry.
    phi = _sphere()
    chi = 0.5
    c, converged, _ = vp.equilibrate(phi, chi=chi, n_steps=4000)
    assert converged
    ratio = vp.partition_ratio(c, phi)
    assert ratio < 1.0                                                  # chi>0 -> depleted inside
    pred = vp.predicted_partition_ratio(phi, chi)
    assert abs(ratio - pred) < 0.05 * pred                             # within 5% of known law


def test_selectivity_emerges_from_chi_difference_not_from_D():
    # Two species with DIFFERENT chi (but the SAME single mobility D) partition differently:
    # this is emergent selectivity from the free-energy coupling, exactly what Gate I must read.
    phi = _sphere()
    c_a, _, _ = vp.equilibrate(phi, chi=0.3, D=1.0, n_steps=4000)
    c_b, _, _ = vp.equilibrate(phi, chi=0.8, D=1.0, n_steps=4000)
    r_a = vp.partition_ratio(c_a, phi)
    r_b = vp.partition_ratio(c_b, phi)
    # larger chi -> stronger depletion inside -> smaller ratio; selectivity is nonzero.
    assert r_b < r_a
    assert r_a / r_b > 1.2                                              # a clear, measurable split


def test_no_selectivity_when_chi_equal_control():
    # Control: identical chi -> identical partition, even though these are "different species".
    # Selectivity is NOT baked into a species-specific D (the F0 #1 target-encoding guard).
    phi = _sphere()
    c_a, _, _ = vp.equilibrate(phi, chi=0.5, D=1.0, n_steps=3000)
    c_b, _, _ = vp.equilibrate(phi, chi=0.5, D=1.0, n_steps=3000)
    assert abs(vp.partition_ratio(c_a, phi) - vp.partition_ratio(c_b, phi)) < 1e-6


def test_equilibrium_independent_of_D():
    # D is a MOBILITY (sets the rate), not a selectivity: two different D reach the SAME Boltzmann
    # steady state. Confirms selectivity cannot be hiding in D (validator-level guard for F0 #1).
    phi = _sphere()
    c_slow, _, _ = vp.equilibrate(phi, chi=0.5, D=0.5, n_steps=8000)
    c_fast, _, _ = vp.equilibrate(phi, chi=0.5, D=1.0, n_steps=8000)
    assert abs(vp.partition_ratio(c_slow, phi) - vp.partition_ratio(c_fast, phi)) < 0.02


def test_mass_is_exactly_conserved():
    # the finite-volume transport instrument conserves total species amount to machine precision
    # (no_flux boundaries) -- a hard invariant the F0 promises to audit.
    phi = _sphere()
    c = np.full(phi.shape, 1.0)
    m0 = vp.total_mass(c)
    for _ in range(500):
        c = vp.relax_step(c, phi, chi=0.7)
    assert abs(vp.total_mass(c) - m0) < 1e-9 * m0


def test_net_interface_flux_vanishes_at_equilibrium():
    # at the partition steady state the net flux crossing into the interior is ~0 (Gate-I sanity:
    # a genuine equilibrium, not a spuriously sustained current).
    phi = _sphere()
    c, converged, _ = vp.equilibrate(phi, chi=0.5, n_steps=4000)
    assert converged
    flux0 = vp.net_interface_flux(c, phi, chi=0.5)
    # compare against the transient flux early in relaxation (must be far larger)
    c_early = vp.relax_step(np.full(phi.shape, 1.0), phi, chi=0.5)
    flux_early = vp.net_interface_flux(c_early, phi, chi=0.5)
    assert abs(flux0) < 1e-3
    assert abs(flux_early) > 10 * abs(flux0)


def test_zero_chi_gives_uniform_field():
    # no partition coupling -> uniform stays uniform (no spurious selectivity from geometry alone).
    phi = _sphere()
    c, converged, _ = vp.equilibrate(phi, chi=0.0, n_steps=1000)
    assert converged
    assert abs(vp.partition_ratio(c, phi) - 1.0) < 1e-6
