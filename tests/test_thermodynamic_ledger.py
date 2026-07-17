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


def test_matter_in_scales_by_dx_cubed():
    # matter_in must scale as dx^3 (volumetric), matching vessel_flux_3d.total_mass's convention,
    # so it stays in the same units as mass_before/mass_after in mass_balance_error -- a bare
    # cell-count sum would silently drift with grid resolution (Codex).
    shape = (4, 4, 4)
    mask = tl.outer_shell_mask(shape, shell_width=1)
    f = np.full(shape, 0.5)
    base = tl.matter_in(f, mask, k_res=0.3, f_res=1.0, dx=1.0)
    scaled = tl.matter_in(f, mask, k_res=0.3, f_res=1.0, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9   # dx=2 -> cell volume x8


def test_chemical_potential_dilute_ideal_known_values():
    c = np.array([1.0, np.e, np.e ** 2])
    mu = tl.chemical_potential(c, mu0=0.0, RT=1.0)
    assert np.allclose(mu, [0.0, 1.0, 2.0], atol=1e-9)


def test_chemical_potential_shifts_with_mu0():
    c = np.array([1.0])
    assert abs(float(tl.chemical_potential(c, mu0=5.0, RT=1.0)[0]) - 5.0) < 1e-12


def test_chemical_free_energy_change_matches_the_dilute_ideal_free_energy_density_integral():
    # the free-energy DENSITY is f(c) = mu0*c + RT*(c*ln(c) - c) -- the Legendre-consistent
    # integral of mu(c) dc -- NOT the bare product c*mu(c), which overstates it by RT*c (Codex:
    # an earlier version of this function used c*mu(c) directly, which "looks" extensive but is
    # thermodynamically the wrong quantity and silently overstates Delta G whenever the total
    # amount of material changes).
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}       # f(1) = 0*1 + 1*(1*ln1 - 1) = -1
    after = {"a": np.full(shape, np.e)}       # f(e) = 0*e + 1*(e*1 - e) = 0
    dG = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0)
    assert abs(dG - 8.0 * (0.0 - (-1.0))) < 1e-9   # 8 cells * (f(e) - f(1)) = 8 cells * 1.0


def test_chemical_free_energy_change_derivative_matches_chemical_potential():
    # sanity cross-check: the free-energy density's slope (measured via a small finite
    # difference) must reproduce chemical_potential exactly -- this is the defining property
    # that pins down f(c) uniquely (up to an additive constant, which cancels in a difference).
    c0, dc = 2.0, 1e-6
    shape = (1,)
    f_lo = tl.chemical_free_energy_change(
        {"a": np.full(shape, c0)}, {"a": np.full(shape, c0 - dc)}, mu0={"a": 0.5}, RT=1.3)
    f_hi = tl.chemical_free_energy_change(
        {"a": np.full(shape, c0)}, {"a": np.full(shape, c0 + dc)}, mu0={"a": 0.5}, RT=1.3)
    slope = (f_hi - f_lo) / (2 * dc)
    mu_c0 = float(tl.chemical_potential(np.array([c0]), mu0=0.5, RT=1.3)[0])
    assert abs(slope - mu_c0) < 1e-5


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


def test_waste_out_scales_by_dx_cubed():
    shape = (2, 2, 2)
    w = np.full(shape, 0.4)
    base = tl.waste_out(w, k_out=0.1, dx=1.0)
    scaled = tl.waste_out(w, k_out=0.1, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9


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


def test_useful_work_only_integrates_the_interface_band():
    # useful_work must count ONLY the interface-band contribution of sigma_M:grad(u), not the
    # bulk -- this is the required Gate III ledger field distinguishing boundary-maintenance
    # energy from bulk dissipation (F0 §4; Codex: this field was entirely absent from the module).
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0   # a small "interface band" region (|phi|<0.9) inside a bulk of phi=1
    stress_power = np.full(shape, 3.0)
    uw = tl.useful_work(stress_power, phi, band_thresh=0.9)
    band = np.abs(phi) < 0.9
    assert abs(uw - 3.0 * band.sum()) < 1e-9
    assert band.sum() < phi.size   # sanity: the band is a strict subset of the domain


def test_useful_work_zero_for_s1_stage_with_zero_stress_power():
    phi = np.full((4, 4, 4), 0.0)   # everything in-band
    stress_power = np.zeros((4, 4, 4))   # u=0, no hydrodynamics yet
    assert tl.useful_work(stress_power, phi) == 0.0
