"""Synthetic validation for genesis/diagnostics/thermodynamic_ledger.py (Active Vessel P10, PR-1,
role V). Every check is an exact analytic identity (dilute-ideal chemical potential, matched
mass-balance arithmetic) matching the F0's frozen formulas 1:1 -- no physics run data involved.
"""
import numpy as np

import genesis.diagnostics.thermodynamic_ledger as tl


def test_outer_shell_mask_is_a_fixed_box_geometry_independent_of_phi():
    shape = (4, 4, 4)
    mask = tl.outer_shell_mask(shape, shell_width=1)
    assert mask.sum() == 64 - 8   # every cell except the interior 2x2x2 block
    interior = mask[1:3, 1:3, 1:3]
    assert not interior.any()


def test_matter_in_only_counts_the_outer_shell_region():
    shape = (4, 4, 4)
    mask = tl.outer_shell_mask(shape, shell_width=1)
    f = np.full(shape, 0.5)
    expected = float(mask.sum()) * 0.3 * (1.0 - 0.5)
    assert abs(tl.matter_in(f, mask, k_res=0.3, f_res=1.0) - expected) < 1e-12


def test_matter_in_zero_when_no_outer_region():
    shape = (4, 4, 4)
    empty_mask = np.zeros(shape, dtype=bool)
    f = np.full(shape, 0.2)
    assert tl.matter_in(f, empty_mask, k_res=0.3, f_res=1.0) == 0.0


def test_chemical_potential_dilute_ideal_known_values():
    c = np.array([1.0, np.e, np.e ** 2])
    mu = tl.chemical_potential(c, mu0=0.0, RT=1.0)
    assert np.allclose(mu, [0.0, 1.0, 2.0], atol=1e-9)


def test_chemical_potential_shifts_with_mu0():
    c = np.array([1.0])
    assert abs(float(tl.chemical_potential(c, mu0=5.0, RT=1.0)[0]) - 5.0) < 1e-12


def test_chemical_free_energy_change_is_extensive_c_times_mu_not_bare_mu():
    # mu alone is intensive; the F0 frozen formula integrates c*mu, so doubling the concentration
    # (at fixed mu) must double the free-energy change -- a bare mu-only sum would miss this.
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}       # mu=0 -> c*mu=0
    after = {"a": np.full(shape, np.e)}       # mu=1 -> c*mu=e
    dG = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0)
    assert abs(dG - 8.0 * np.e) < 1e-9   # 8 cells * (e*1 - 1*0)


def test_reaction_delta_g_matches_stoichiometric_combination():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    dg = tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0}, RT=1.0)
    expected = np.log(1.0) - np.log(2.0)   # nu_m*mu_m + nu_f*mu_f = ln(1) - ln(2)
    assert np.allclose(dg, expected, atol=1e-9)


def test_waste_out_defaults_to_the_whole_domain():
    # the frozen PDE's -k_out*w sink is global, not restricted to any sub-region.
    shape = (2, 2, 2)
    w = np.full(shape, 0.4)
    expected = float(np.prod(shape)) * 0.1 * 0.4
    assert abs(tl.waste_out(w, k_out=0.1) - expected) < 1e-12


def test_waste_out_region_mask_restricts_when_explicitly_given():
    shape = (2, 2, 2)
    w = np.full(shape, 0.4)
    half_mask = np.zeros(shape, dtype=bool)
    half_mask[0] = True   # half the cells
    expected = 4.0 * 0.1 * 0.4
    assert abs(tl.waste_out(w, k_out=0.1, region_mask=half_mask) - expected) < 1e-12


def test_entropy_production_matches_analytic_value_and_is_nonnegative_for_spontaneous_reaction():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    delta_g = tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0}, RT=1.0)
    rate = np.full(shape, 1.0)
    ep = tl.entropy_production_reaction(rate, -delta_g, RT=1.0)   # affinity = -Delta G_rxn
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
    before = {"f": 10.0, "m": 5.0, "w": 2.0}
    after = {"f": 10.0, "m": 5.0, "w": 19.0}   # w increased by 17, matched by an external source
    err = tl.stoichiometric_balance_error(before, after, {"f": 1.0, "m": 1.0, "w": 1.0}, {"in": 17.0})
    assert err < 1e-9


def test_stoichiometric_balance_error_zero_for_closed_chain_even_with_nonzero_total():
    # a perfectly conserved but NONZERO total invariant must read as zero error -- comparing the
    # absolute total (instead of its before/after change) would wrongly flag this as a bug.
    before = {"f": 10.0, "m": 5.0, "w": 2.0}
    after = {"f": 9.0, "m": 5.0, "w": 3.0}   # f->w conversion of 1 unit; f+m+w invariant unchanged
    err = tl.stoichiometric_balance_error(before, after, {"f": 1.0, "m": 1.0, "w": 1.0})
    assert err < 1e-9


def test_stoichiometric_balance_error_nonzero_when_invariant_actually_drifts():
    before = {"f": 10.0, "m": 5.0}
    after = {"f": 9.0, "m": 5.0}   # f dropped by 1 with no matching m/w change and no source term
    err = tl.stoichiometric_balance_error(before, after, {"f": 1.0, "m": 1.0})
    assert abs(err - 1.0) < 1e-9
