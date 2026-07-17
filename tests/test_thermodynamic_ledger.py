"""Synthetic validation for genesis/diagnostics/thermodynamic_ledger.py (Active Vessel P10, PR-1,
role V). Every check is an exact analytic identity (dilute-ideal chemical potential, matched
mass-balance arithmetic) matching the F0's frozen formulas 1:1 -- no physics run data involved.
"""
import numpy as np
import pytest

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


def test_chemical_potential_rejects_negative_concentration():
    # a genuinely negative concentration is a solver bug, not a valid near-zero state -- must
    # raise, never be silently floored to eps and made to look like a valid tiny concentration.
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0, -0.05, 2.0]))


def test_chemical_potential_tolerates_tiny_negative_floating_noise():
    # values within eps of zero (floating-point noise, not a real overshoot) must still floor
    # to eps rather than raise.
    mu = tl.chemical_potential(np.array([-1e-13]), mu0=0.0, RT=1.0, eps=1e-12)
    assert np.isfinite(mu[0])


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


def test_chemical_free_energy_change_rejects_negative_concentration():
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}
    after = {"a": np.full(shape, -0.5)}   # unphysical overshoot
    with pytest.raises(ValueError):
        tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0)


def test_chemical_free_energy_change_includes_species_present_only_after_the_window():
    # a species genuinely absent before the window (e.g. a waste/product field introduced by a
    # stop/restart run) must NOT be silently dropped just because it's missing from
    # species_before -- Codex: iterating only species_before's keys underreported Delta G.
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}                                  # a unchanged: f(1)-f(1)=0
    after = {"a": np.full(shape, 1.0), "b": np.full(shape, np.e)}        # b appears from nothing
    dG = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0, "b": 2.0}, RT=1.0)
    # f_b(0) = 2*0 + (0*ln(eps)-0) = 0 ; f_b(e) = 2*e + (e*1-e) = 2e
    expected = 8.0 * (2.0 * np.e - 0.0)
    assert abs(dG - expected) < 1e-6


def test_chemical_free_energy_change_includes_species_present_only_before_the_window():
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0), "b": np.full(shape, np.e)}       # b disappears
    after = {"a": np.full(shape, 1.0)}
    dG = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0, "b": 2.0}, RT=1.0)
    expected = 8.0 * (0.0 - 2.0 * np.e)
    assert abs(dG - expected) < 1e-6


def test_chemical_free_energy_change_fails_closed_on_missing_mu0_entry():
    # a species newly appearing on one side (via the union-of-keys handling above) must NOT
    # silently get an unregistered mu0=0.0 reference if the caller forgot to preregister it.
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}
    after = {"a": np.full(shape, 1.0), "b": np.full(shape, np.e)}
    with pytest.raises(KeyError):
        tl.chemical_free_energy_change(before, after, mu0={"a": 0.0})   # "b" missing from mu0


def test_reaction_delta_g_fails_closed_on_missing_mu0_entry():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    with pytest.raises(KeyError):
        tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0})   # "m" missing from mu0


def test_chemical_free_energy_change_scales_by_dx_cubed():
    shape = (2, 2, 2)
    before = {"a": np.full(shape, 1.0)}
    after = {"a": np.full(shape, np.e)}
    base = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0, dx=1.0)
    scaled = tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, RT=1.0, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9


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


def test_entropy_production_scales_by_dx_cubed():
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    delta_g = tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0}, RT=1.0)
    rate = np.full(shape, 1.0)
    base = tl.entropy_production_reaction(rate, -delta_g, RT=1.0, dx=1.0)
    scaled = tl.entropy_production_reaction(rate, -delta_g, RT=1.0, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9


def test_viscous_dissipation_zero_when_strain_rate_zero():
    assert tl.viscous_dissipation(np.zeros((3, 3, 3)), eta=1.0) == 0.0


def test_viscous_dissipation_matches_known_formula():
    strain_sq = np.full((2, 2, 2), 0.5)
    assert abs(tl.viscous_dissipation(strain_sq, eta=2.0) - (2.0 * 2.0 * 8 * 0.5)) < 1e-9


def test_viscous_dissipation_scales_by_dx_cubed():
    strain_sq = np.full((2, 2, 2), 0.5)
    base = tl.viscous_dissipation(strain_sq, eta=2.0, dx=1.0)
    scaled = tl.viscous_dissipation(strain_sq, eta=2.0, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9


def test_mass_balance_error_zero_for_consistent_accounting():
    assert tl.mass_balance_error(10.0, 13.0, matter_in_amt=5.0, waste_out_amt=2.0) < 1e-12


def test_mass_balance_error_nonzero_flags_bug():
    err = tl.mass_balance_error(10.0, 20.0, matter_in_amt=5.0, waste_out_amt=0.0)
    assert abs(err - 5.0) < 1e-9


def test_stoichiometric_balance_error_zero_with_matching_sources():
    before = {"f": 10.0, "m": 5.0, "w": 2.0}
    after = {"f": 10.0, "m": 5.0, "w": 19.0}   # w increased by 17, matched by an external source
    err = tl.stoichiometric_balance_error(
        before, after, {"f": 1.0, "m": 1.0, "w": 1.0}, sources={"matter_in": 17.0})
    assert err < 1e-9


def test_stoichiometric_balance_error_zero_with_matching_sinks():
    # a sink (e.g. the POSITIVE-magnitude waste_out amount) must be SUBTRACTED, not blindly
    # summed as if it were an addition -- passing it as `sinks` (not into an undifferentiated
    # source_terms dict) must correctly balance a window where mass genuinely left the system.
    before = {"f": 10.0, "m": 5.0, "w": 2.0}
    after = {"f": 10.0, "m": 5.0, "w": -5.0}   # w decreased by 7, matched by an external sink
    err = tl.stoichiometric_balance_error(
        before, after, {"f": 1.0, "m": 1.0, "w": 1.0}, sinks={"waste_out": 7.0})
    assert err < 1e-9


def test_stoichiometric_balance_error_sources_and_sinks_combine_correctly():
    before = {"f": 10.0}
    after = {"f": 10.0}   # f unchanged -> invariant change is 0
    # a source of 5 and a sink of 5 must cancel, leaving a zero net rhs matching the zero change.
    err = tl.stoichiometric_balance_error(
        before, after, {"f": 1.0}, sources={"in": 5.0}, sinks={"out": 5.0})
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


def test_stoichiometric_balance_error_treats_species_absent_from_one_side_as_zero_mass():
    # a waste/product species genuinely absent before the window (introduced only after it) must
    # not abort the residual computation -- treated as mass 0 there, matching
    # chemical_free_energy_change's sparse-species handling (Codex).
    before = {"f": 10.0}                       # "w" doesn't exist yet
    after = {"f": 9.0, "w": 1.0}                # f->w conversion of 1 unit; f+w invariant unchanged
    err = tl.stoichiometric_balance_error(before, after, {"f": 1.0, "w": 1.0})
    assert err < 1e-9


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


def test_useful_work_accepts_a_bare_scalar_zero_for_the_s1_stage():
    # callers should be able to pass a bare 0.0 for the pre-hydrodynamic S1 stage rather than
    # being forced to construct a full zero-filled field array matching phi's shape.
    phi = np.full((4, 4, 4), 0.0)
    assert tl.useful_work(0.0, phi) == 0.0


def test_useful_work_rejects_a_nonzero_scalar():
    # sigma_M:grad(u) is a real per-cell field, never physically uniform across the interface
    # band -- a nonzero scalar is never a valid measurement (only the documented 0.0 S1 case is
    # accepted as a scalar) and must raise rather than silently broadcast and satisfy a
    # downstream useful_work>0 Gate III check from incomplete hydrodynamic metadata.
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    with pytest.raises(ValueError):
        tl.useful_work(3.0, phi, band_thresh=0.9)


def test_useful_work_scales_by_dx_cubed():
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    stress_power = np.full(shape, 3.0)
    base = tl.useful_work(stress_power, phi, band_thresh=0.9, dx=1.0)
    scaled = tl.useful_work(stress_power, phi, band_thresh=0.9, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9
