"""T01–T03: stoichiometric conservation, detailed balance / Wegscheider, free-energy dissipation."""
import numpy as np

import _setup  # noqa: F401
import reaction_network as RN
import solver as S
import species as SP
import thermodynamics as TH


def test_T01_stoichiometry_conserves_building_units_exactly():
    assert RN.conservation_residual() == 0.0


def test_T02_rate_constants_satisfy_detailed_balance_and_wegscheider():
    kf, kr = TH.forward_reverse_rates()
    K = TH.equilibrium_constants()
    assert np.allclose(kf / kr, K, rtol=1e-12, atol=0)   # floating-point identity k+/k- = K
    assert abs(TH.wegscheider_residual()) < 1e-12


def test_T02_long_closed_run_reaches_mass_action_equilibrium_constants():
    kf, kr = TH.forward_reverse_rates()
    eq = S.end_state(np.array([1.0, 1.0, 1.0, 0, 0, 0]), 300.0, kf, kr)
    Q = np.prod(np.power(eq[:, None], RN.MP), axis=0) / np.prod(np.power(eq[:, None], RN.MR), axis=0)
    assert np.allclose(np.log(Q), np.log(TH.equilibrium_constants()), atol=1e-6)


def test_T01_units_conserved_along_a_trajectory():
    kf, kr = TH.forward_reverse_rates()
    _, C = S.integrate(np.array([0.9, 1.1, 1.0, 0.05, 0.02, 0.03]), 5.0, kf, kr,
                       t_eval=np.linspace(0, 5, 26))
    totals = np.array([SP.element_totals(c) for c in C])
    assert np.max(np.abs(totals - totals[0])) < 1e-7


def test_T03_free_energy_never_increases_in_a_closed_phase():
    kf, kr = TH.forward_reverse_rates()
    c0 = np.array([0.9, 1.1, 1.0, 0.05, 0.02, 0.03])
    tg = np.linspace(0, 8, 81)
    _, C = S.integrate(c0, 8.0, kf, kr, t_eval=tg)
    G = np.array([TH.free_energy(c) for c in C])
    assert np.max(np.diff(G)) <= 1e-10


def test_T03_analytic_dissipation_is_nonpositive_on_random_states():
    rng = np.random.default_rng(3)
    for _ in range(200):
        c = rng.uniform(0.01, 2.0, size=6)
        assert TH.dG_dt_closed(c) <= 1e-12


def test_T03_analytic_matches_finite_difference():
    kf, kr = TH.forward_reverse_rates()
    c = np.array([0.7, 0.9, 1.1, 0.2, 0.1, 0.15])
    h = 1e-6
    _, C = S.integrate(c, h, kf, kr, t_eval=[0.0, h])
    G = [TH.free_energy(x) for x in C]
    fd = (G[1] - G[0]) / h
    assert abs(fd - TH.dG_dt_closed(c)) < 1e-3 * max(1.0, abs(fd))
