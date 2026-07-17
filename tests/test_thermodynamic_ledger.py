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


def test_outer_shell_mask_rejects_negative_or_fractional_shell_width():
    # int(shell_width) silently truncates a fractional width and accepts a negative width as a
    # valid Python slice bound, marking almost the entire box as the reservoir (Codex).
    with pytest.raises(ValueError):
        tl.outer_shell_mask((4, 4, 4), shell_width=-1)
    with pytest.raises(ValueError):
        tl.outer_shell_mask((4, 4, 4), shell_width=1.7)


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


def test_matter_in_rejects_a_wrong_shaped_outer_mask():
    # a scalar or wrong-shaped-but-broadcast-compatible mask must never silently integrate the
    # WRONG region -- e.g. outer_mask=True would integrate fuel exchange over the ENTIRE domain
    # instead of the fixed outer shell (Codex).
    shape = (4, 4, 4)
    f = np.full(shape, 0.5)
    with pytest.raises(ValueError):
        tl.matter_in(f, True, k_res=0.3, f_res=1.0)
    with pytest.raises(ValueError):
        tl.matter_in(f, np.ones((2, 2, 2), dtype=bool), k_res=0.3, f_res=1.0)


def test_matter_in_rejects_a_same_shaped_non_boolean_mask():
    # a same-shaped NUMERIC mask (e.g. all 0.5) passes the shape check but is not a 0/1 selector
    # -- it silently WEIGHTS the reservoir integration by arbitrary values (CodeRabbit).
    shape = (4, 4, 4)
    f = np.full(shape, 0.5)
    with pytest.raises(ValueError):
        tl.matter_in(f, np.full(shape, 0.5), k_res=0.3, f_res=1.0)


def test_matter_in_rejects_invalid_dx():
    shape = (4, 4, 4)
    mask = tl.outer_shell_mask(shape, shell_width=1)
    f = np.full(shape, 0.5)
    with pytest.raises(ValueError):
        tl.matter_in(f, mask, k_res=0.3, f_res=1.0, dx=0.0)
    with pytest.raises(ValueError):
        tl.matter_in(f, mask, k_res=0.3, f_res=1.0, dx=-1.0)


def test_matter_in_rejects_invalid_f_k_res_f_res():
    # a negative/non-finite f, k_res, or f_res must fail closed -- but the computed TOTAL may
    # still be legitimately negative when a valid f > f_res (net efflux) (Codex).
    shape = (4, 4, 4)
    mask = tl.outer_shell_mask(shape, shell_width=1)
    with pytest.raises(ValueError):
        tl.matter_in(np.full(shape, -5.0), mask, k_res=0.3, f_res=1.0)
    with pytest.raises(ValueError):
        tl.matter_in(np.full(shape, 0.5), mask, k_res=-0.3, f_res=1.0)
    with pytest.raises(ValueError):
        tl.matter_in(np.full(shape, 0.5), mask, k_res=0.3, f_res=-1.0)
    net_negative = tl.matter_in(np.full(shape, 2.0), mask, k_res=0.3, f_res=1.0)
    assert net_negative < 0.0   # f > f_res, valid net efflux, must not be rejected


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


def test_chemical_potential_rejects_invalid_RT():
    # RT=0/negative/non-finite would silently zero, reverse the sign of, or contaminate every
    # chemical potential (CodeRabbit).
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0]), RT=0.0)
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0]), RT=-1.0)
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0]), RT=float("nan"))


def test_chemical_potential_rejects_a_python_list_of_booleans():
    # a plain Python list of booleans (e.g. [True, False]) is neither a bool scalar nor an
    # np.ndarray -- checking isinstance on the raw input misses it (CodeRabbit).
    with pytest.raises(ValueError):
        tl.chemical_potential([True, False])


def test_chemical_potential_rejects_boolean_concentration():
    # an accidentally-passed occupancy/mask array must not have its True/False cells silently
    # cast to 1.0/0.0 and be treated as a real measured concentration (Codex).
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([True, False]))
    with pytest.raises(ValueError):
        tl.chemical_potential(True)


def test_chemical_potential_rejects_non_finite_concentration():
    # a solver blow-up producing inf/nan is invisible to the `c < -eps` check (both
    # `inf < -eps` and `nan < -eps` are False) -- must be rejected explicitly, not silently
    # flow into chemical_potential/reaction_delta_g/entropy_production (Codex).
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0, np.inf, 2.0]))
    with pytest.raises(ValueError):
        tl.chemical_potential(np.array([1.0, np.nan, 2.0]))


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


def test_chemical_free_energy_change_rejects_mismatched_species_shapes():
    # a species present in both before/after with mismatched array shapes must never silently
    # broadcast into a fabricated (and physically meaningless) combined shape (Codex).
    before = {"a": np.full((2, 2, 2), 1.0)}
    after = {"a": np.full((4,), 1.0)}
    with pytest.raises(ValueError):
        tl.chemical_free_energy_change(before, after, mu0={"a": 0.0})


def test_chemical_free_energy_change_rejects_species_on_different_common_grids():
    # two DIFFERENT species could each have internally-consistent before/after shapes but differ
    # from EACH OTHER -- summed together into one purported domain integral, that's a physically
    # meaningless total (dx^3 means a different cell volume per species) (CodeRabbit).
    before = {"a": np.full((2, 2, 2), 1.0), "b": np.full((4, 4, 4), 1.0)}
    after = {"a": np.full((2, 2, 2), 2.0), "b": np.full((4, 4, 4), 2.0)}
    with pytest.raises(ValueError):
        tl.chemical_free_energy_change(before, after, mu0={"a": 0.0, "b": 0.0})


def test_chemical_free_energy_change_rejects_invalid_dx():
    before = {"a": np.full((2, 2, 2), 1.0)}
    after = {"a": np.full((2, 2, 2), 2.0)}
    with pytest.raises(ValueError):
        tl.chemical_free_energy_change(before, after, mu0={"a": 0.0}, dx=0.0)


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


def test_reaction_delta_g_rejects_mismatched_species_shapes():
    # a broadcast-compatible placeholder (e.g. a 1-element array standing in for a full 3-D
    # field) must not silently broadcast in the per-species sum and fabricate a finite Delta
    # G_rxn field from malformed reaction metadata (Codex).
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.array([1.0])}
    with pytest.raises(ValueError):
        tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0})


def test_reaction_delta_g_allows_scalar_mixed_with_a_single_field_shape():
    # a genuinely scalar species concentration (a deliberate uniform value) is not a shape
    # mismatch -- only two DIFFERING non-scalar shapes must raise.
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": 1.0}
    dg = tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0})
    assert np.asarray(dg).shape == shape


def test_reaction_delta_g_rejects_invalid_stoich_coefficients():
    # a NaN or boolean coefficient must fail closed, not silently produce a NaN audit result or
    # convert True/False to 1.0/0.0 (CodeRabbit); a genuinely negative coefficient stays valid.
    shape = (2, 2, 2)
    conc = {"f": np.full(shape, 2.0), "m": np.full(shape, 1.0)}
    with pytest.raises(ValueError):
        tl.reaction_delta_g(conc, {"f": float("nan"), "m": 1.0}, mu0={"f": 0.0, "m": 0.0})
    with pytest.raises(ValueError):
        tl.reaction_delta_g(conc, {"f": True, "m": 1.0}, mu0={"f": 0.0, "m": 0.0})
    dg = tl.reaction_delta_g(conc, {"f": -1.0, "m": 1.0}, mu0={"f": 0.0, "m": 0.0})
    assert np.asarray(dg).shape == shape


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


def test_waste_out_rejects_negative_w_overshoot():
    # the frozen ledger treats waste removal as a positive sink magnitude -- a negative
    # concentration overshoot in w must fail closed, not silently produce a negative waste_out
    # that could offset a real mass change in mass_balance_error (Codex).
    with pytest.raises(ValueError):
        tl.waste_out(np.array([-5.0, 1.0]), k_out=1.0)


def test_waste_out_rejects_negative_or_non_finite_k_out():
    with pytest.raises(ValueError):
        tl.waste_out(np.array([1.0, 1.0]), k_out=-1.0)
    with pytest.raises(ValueError):
        tl.waste_out(np.array([1.0, 1.0]), k_out=float("inf"))


def test_waste_out_rejects_a_non_boolean_or_wrong_shaped_region_mask():
    # region_mask=True would silently ignore the intended subregion (integrating the whole
    # domain), and a numeric mask would silently rescale the sink (CodeRabbit).
    w = np.full((2, 2, 2), 1.0)
    with pytest.raises(ValueError):
        tl.waste_out(w, k_out=0.1, region_mask=True)
    with pytest.raises(ValueError):
        tl.waste_out(w, k_out=0.1, region_mask=np.full((2, 2, 2), 0.5))
    with pytest.raises(ValueError):
        tl.waste_out(w, k_out=0.1, region_mask=np.ones((3, 3, 3), dtype=bool))


def test_waste_out_rejects_invalid_dx():
    w = np.full((2, 2, 2), 1.0)
    with pytest.raises(ValueError):
        tl.waste_out(w, k_out=0.1, dx=0.0)


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


def test_entropy_production_rejects_boolean_rate_or_affinity():
    # a boolean mask must not be silently cast (True -> 1.0) and treated as a real measured
    # rate/affinity, satisfying the preregistered entropy_production>0 maintenance check (Codex).
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(True, 2.0)
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(1.0, False)


def test_entropy_production_rejects_non_finite_rate_or_affinity():
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(1.0, float("inf"))
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(float("nan"), 2.0)


def test_entropy_production_allows_a_genuinely_negative_affinity():
    # a negative rate*affinity combination is a real, reportable inconsistent-rate-law finding --
    # sign itself must not be rejected, only booleans and non-finite values.
    ep = tl.entropy_production_reaction(1.0, -2.0)
    assert ep == -2.0


def test_entropy_production_rejects_a_python_list_of_booleans():
    # a plain Python list of booleans is neither a bool scalar nor an np.ndarray -- an isinstance
    # check on the raw input misses it (CodeRabbit).
    with pytest.raises(ValueError):
        tl.entropy_production_reaction([True, False], 2.0)


def test_entropy_production_rejects_invalid_RT_or_dx():
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(1.0, 2.0, RT=0.0)
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(1.0, 2.0, RT=-1.0)
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(1.0, 2.0, dx=0.0)


def test_entropy_production_rejects_mismatched_rate_affinity_shapes():
    # a broadcast-compatible-but-incomplete placeholder for rate or affinity (e.g. a 1-element
    # array against a full 3-D field) must not silently broadcast and report a finite entropy-
    # production total from malformed per-cell reaction metadata (Codex).
    rate = np.full((4, 4, 4), 1.0)
    affinity = np.array([1.0])
    with pytest.raises(ValueError):
        tl.entropy_production_reaction(rate, affinity)


def test_entropy_production_allows_a_scalar_affinity_broadcast_against_a_rate_field():
    # a genuinely scalar affinity (a deliberate uniform driving force) is not a shape mismatch.
    rate = np.full((4, 4, 4), 1.0)
    ep = tl.entropy_production_reaction(rate, 2.0)
    assert abs(ep - 128.0) < 1e-9   # sum(1.0*2.0) over 64 cells


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


def test_viscous_dissipation_rejects_boolean_strain_rate_sq():
    # True/False must never silently cast to 1.0/0.0 and report dissipation from a boolean mask.
    with pytest.raises(ValueError):
        tl.viscous_dissipation(np.array([True, False, True]))


def test_viscous_dissipation_rejects_negative_or_non_finite_strain_rate_sq():
    # e:e is a sum of squared tensor components -- always non-negative and finite; a negative or
    # non-finite value is corrupted hydrodynamic metadata, not a real measurement.
    with pytest.raises(ValueError):
        tl.viscous_dissipation(np.array([-1.0, 2.0]))
    with pytest.raises(ValueError):
        tl.viscous_dissipation(np.array([1.0, float("inf")]))


def test_viscous_dissipation_rejects_invalid_eta_or_dx():
    # eta is a physical viscosity coefficient -- negative/boolean/non-finite must fail closed
    # just like invalid strain_rate_sq values do (CodeRabbit/Codex).
    strain_sq = np.array([1.0, 2.0])
    with pytest.raises(ValueError):
        tl.viscous_dissipation(strain_sq, eta=-1.0)
    with pytest.raises(ValueError):
        tl.viscous_dissipation(strain_sq, eta=True)
    with pytest.raises(ValueError):
        tl.viscous_dissipation(strain_sq, eta=float("nan"))
    with pytest.raises(ValueError):
        tl.viscous_dissipation(strain_sq, dx=0.0)


def test_mass_balance_error_zero_for_consistent_accounting():
    assert tl.mass_balance_error(10.0, 13.0, matter_in_amt=5.0, waste_out_amt=2.0) < 1e-12


def test_mass_balance_error_nonzero_flags_bug():
    err = tl.mass_balance_error(10.0, 20.0, matter_in_amt=5.0, waste_out_amt=0.0)
    assert abs(err - 5.0) < 1e-9


def test_mass_balance_error_rejects_boolean_or_negative_mass():
    # a negative or boolean mass_before/mass_after must never be able to coincidentally offset
    # the residual and pass the "~0" audit with corrupted accounting data (Codex).
    with pytest.raises(ValueError):
        tl.mass_balance_error(True, 2.0, matter_in_amt=1.0, waste_out_amt=0.0)
    with pytest.raises(ValueError):
        tl.mass_balance_error(-5.0, 2.0, matter_in_amt=1.0, waste_out_amt=0.0)


def test_mass_balance_error_rejects_non_finite_or_boolean_flux_terms():
    with pytest.raises(ValueError):
        tl.mass_balance_error(10.0, 13.0, matter_in_amt=float("inf"), waste_out_amt=0.0)
    with pytest.raises(ValueError):
        tl.mass_balance_error(10.0, 13.0, matter_in_amt=True, waste_out_amt=0.0)


def test_mass_balance_error_allows_a_negative_matter_in_amt_under_net_efflux():
    # matter_in can be genuinely negative (net efflux through the outer shell, per the frozen
    # k_res*(f_res-f) formula) -- this must NOT be rejected as if it were corrupted data, unlike
    # mass_before/mass_after (which are always non-negative field sums).
    err = tl.mass_balance_error(10.0, 8.0, matter_in_amt=-2.0, waste_out_amt=0.0)
    assert err < 1e-12


def test_mass_balance_error_rejects_a_negative_waste_out_amt_or_other_sinks():
    # waste_out_amt/other_sinks are SINK magnitudes, SUBTRACTED in the formula -- unlike
    # matter_in_amt, a negative value here would become an ADDITION and could silently cancel a
    # real residual (e.g. mass_before=10, mass_after=15, matter_in_amt=3, waste_out_amt=-2
    # passing as if +2 of extra waste had left the system) (CodeRabbit/Codex).
    with pytest.raises(ValueError):
        tl.mass_balance_error(10.0, 15.0, matter_in_amt=3.0, waste_out_amt=-2.0)
    with pytest.raises(ValueError):
        tl.mass_balance_error(10.0, 15.0, matter_in_amt=3.0, waste_out_amt=0.0, other_sinks=-1.0)


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
    before = {"f": 10.0, "m": 5.0, "w": 9.0}
    after = {"f": 10.0, "m": 5.0, "w": 2.0}    # w decreased by 7, matched by an external sink
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


def test_stoichiometric_balance_error_rejects_negative_mass():
    # an impossible negative species mass (e.g. from a solver bug) must raise, never silently
    # flow into the residual and coincidentally balance to zero (CodeRabbit).
    before = {"f": 10.0}
    after = {"f": -1.0}
    with pytest.raises(ValueError):
        tl.stoichiometric_balance_error(before, after, {"f": 1.0})


def test_stoichiometric_balance_error_rejects_negative_source_or_sink():
    before = {"f": 10.0}
    after = {"f": 15.0}
    with pytest.raises(ValueError):
        tl.stoichiometric_balance_error(before, after, {"f": 1.0}, sources={"in": -5.0})
    with pytest.raises(ValueError):
        tl.stoichiometric_balance_error(before, after, {"f": 1.0}, sinks={"out": -5.0})


def test_stoichiometric_balance_error_rejects_invalid_stoich_coefficient():
    # a NaN or boolean stoich[k] coefficient must fail closed, not silently return a NaN audit
    # result or introduce unintended broadcasting (CodeRabbit).
    before = {"f": 10.0}
    after = {"f": 15.0}
    with pytest.raises(ValueError):
        tl.stoichiometric_balance_error(before, after, {"f": float("nan")})
    with pytest.raises(ValueError):
        tl.stoichiometric_balance_error(before, after, {"f": True})


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


def test_useful_work_rejects_a_wrong_shaped_nonscalar_stress_power():
    # a broadcast-compatible-but-wrong-shaped stress_power_density (e.g. a 1-element array
    # against a full 3D phi) must never silently broadcast past the nonzero-scalar guard and
    # fabricate a spatially uniform "measurement" (Codex).
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    with pytest.raises(ValueError):
        tl.useful_work(np.array([3.0]), phi, band_thresh=0.9)


def test_useful_work_rejects_a_boolean_stress_power_array():
    # a boolean field must not silently cast True/False to 1.0/0.0 and report positive
    # boundary-maintenance work from a mask rather than a real measured sigma_M:grad(u) (Codex).
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    spd_bool = np.zeros(shape, dtype=bool)
    spd_bool[2, 2, 2] = True
    with pytest.raises(ValueError):
        tl.useful_work(spd_bool, phi, band_thresh=0.9)


def test_useful_work_rejects_non_finite_stress_power_values():
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    spd_inf = np.zeros(shape)
    spd_inf[2, 2, 2] = float("inf")
    with pytest.raises(ValueError):
        tl.useful_work(spd_inf, phi, band_thresh=0.9)


def test_useful_work_rejects_non_finite_phi():
    # a NaN cell makes abs(phi) < band_thresh False (NaN comparisons are always False), so a
    # corrupted interface cell would otherwise be silently EXCLUDED from the band instead of
    # failing the whole measurement, underreporting Gate III work (CodeRabbit).
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    phi[0, 0, 0] = float("nan")
    with pytest.raises(ValueError):
        tl.useful_work(np.zeros(shape), phi, band_thresh=0.9)


def test_useful_work_rejects_invalid_dx():
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    with pytest.raises(ValueError):
        tl.useful_work(np.zeros(shape), phi, band_thresh=0.9, dx=0.0)


def test_useful_work_scales_by_dx_cubed():
    shape = (6, 6, 6)
    phi = np.full(shape, 1.0)
    phi[2:4, 2:4, 2:4] = 0.0
    stress_power = np.full(shape, 3.0)
    base = tl.useful_work(stress_power, phi, band_thresh=0.9, dx=1.0)
    scaled = tl.useful_work(stress_power, phi, band_thresh=0.9, dx=2.0)
    assert abs(scaled - base * 8.0) < 1e-9
