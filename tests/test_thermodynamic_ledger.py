"""Synthetic validation for genesis/diagnostics/thermodynamic_ledger.py (Active Vessel P10, PR-1,
role V). Every check is an exact analytic identity (dilute-ideal chemical potential, matched
mass-balance arithmetic) matching the F0's frozen formulas 1:1 -- no physics run data involved.
"""
import numpy as np

import genesis.diagnostics.thermodynamic_ledger as tl


def _half_outside_phi():
    # 2x2x2 field, half the cells phi=-1 (outside), half phi=+1 (inside).
    return np.concatenate([np.full(4, -1.0), np.full(4, 1.0)]).reshape(2, 2, 2)


def test_matter_in_only_counts_outside_cells():
    phi = _half_outside_phi()
    f = np.full(phi.shape, 0.5)
    n_outside = int((phi < -0.5).sum())
    expected = n_outside * 0.3 * (1.0 - 0.5)
    assert abs(tl.matter_in(f, phi, k_res=0.3, f_res=1.0, out_thresh=0.5) - expected) < 1e-12


def test_matter_in_zero_when_no_outside_region():
    phi = np.full((4, 4, 4), 1.0)
    f = np.full(phi.shape, 0.2)
    assert tl.matter_in(f, phi, k_res=0.3, f_res=1.0, out_thresh=0.5) == 0.0


def test_chemical_potential_dilute_ideal_known_values():
    c = np.array([1.0, np.e, np.e ** 2])
    mu = tl.chemical_potential(c, mu0=0.0, RT=1.0)
    assert np.allclose(mu, [0.0, 1.0, 2.0], atol=1e-9)


def test_chemical_potential_shifts_with_mu0():
    c = np.array([1.0])
    assert abs(float(tl.chemical_potential(c, mu0=5.0, RT=1.0)[0]) - 5.0) < 1e-12


def test_chemical_free_energy_change_matches_analytic_integral():
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}       # mu=0
    after = {"a": np.full(shape, np.e)}       # mu=1
    dG = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0)
    assert abs(dG - 8.0) < 1e-9   # 8 cells * (1 - 0)


def test_reaction_affinity_matches_stoichiometric_combination():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    aff = tl.reaction_affinity(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0}, RT=1.0)
    expected = np.log(1.0) - np.log(2.0)   # nu_m*mu_m + nu_f*mu_f = ln(1) - ln(2)
    assert np.allclose(aff, expected, atol=1e-9)


def test_waste_out_only_counts_outside_cells():
    phi = _half_outside_phi()
    w = np.full(phi.shape, 0.4)
    n_outside = int((phi < -0.5).sum())
    expected = n_outside * 0.1 * 0.4
    assert abs(tl.waste_out(w, phi, k_out=0.1, out_thresh=0.5) - expected) < 1e-12


def test_entropy_production_matches_analytic_value_and_is_nonnegative_for_spontaneous_reaction():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    affinity = tl.reaction_affinity(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0}, RT=1.0)
    rate = np.full(shape, 1.0)
    ep = tl.entropy_production_reaction(rate, -affinity, RT=1.0)   # driving force = -Delta G_rxn
    expected = 8.0 * np.log(2.0)
    assert abs(ep - expected) < 1e-9
    assert ep >= 0.0   # spontaneous reaction (f->m, mu_f>mu_m here) must have non-negative sigma


def test_viscous_dissipation_zero_when_strain_rate_zero():
    assert tl.viscous_dissipation(np.zeros((3, 3, 3)), eta=1.0) == 0.0


def test_viscous_dissipation_matches_known_formula():
    strain_sq = np.full((2, 2, 2), 0.5)
    assert abs(tl.viscous_dissipation(strain_sq, eta=2.0) - (2.0 * 2.0 * 8 * 0.5)) < 1e-9


def test_mass_balance_error_zero_for_consistent_accounting():
    assert tl.mass_balance_error(10.0, 13.0, matter_in_amt=5.0, waste_out_amt=2.0) < 1e-12


def test_mass_balance_error_nonzero_flags_bug():
    err = tl.mass_balance_error(10.0, 20.0, matter_in_amt=5.0, waste_out_amt=0.0)
    assert abs(err - 5.0) < 1e-9


def test_stoichiometric_balance_error_zero_with_matching_sources():
    err = tl.stoichiometric_balance_error(
        {"f": 10.0, "m": 5.0, "w": 2.0}, {"f": 1.0, "m": 1.0, "w": 1.0}, {"in": 17.0})
    assert err < 1e-9


def test_stoichiometric_balance_error_zero_with_no_sources_for_closed_chain():
    err = tl.stoichiometric_balance_error({"f": 3.0, "m": -3.0}, {"f": 1.0, "m": 1.0})
    assert err < 1e-9
