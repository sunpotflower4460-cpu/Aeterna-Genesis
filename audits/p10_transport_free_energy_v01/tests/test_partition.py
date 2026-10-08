"""T2–T6: equilibrium partition, the literal F0 flux control, selectivity, controls, D-independence.

These are checks of the equations and the discrete scheme. They are NOT emergence claims.
"""
import numpy as np

import _setup  # noqa: F401
import model
import solver
import metrics as M

T_EQ = 40.0


def _run(beta, D_kind="const", kind="mu", N=64, c0=None, t_eval=None):
    dx, x = model.grid(N)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, D_kind)
    s = solver.make_setup(N, phi, D, beta, dx, kind)
    if c0 is None:
        c0 = 1.0 + 0.5 * np.cos(2 * np.pi * x)
    if t_eval is None:
        t_eval = [0.0, T_EQ]
    r = solver.run_bdf(s, c0, t_eval, rtol=1e-9, atol=1e-12)
    assert r["success"], r["message"]
    return x, phi, dx, r["C"][-1]


def test_discrete_equilibrium_is_boltzmann_to_solver_tolerance():
    x, phi, dx, c = _run(0.5)
    ceq = M.discrete_equilibrium(phi, 0.5, 1.0, dx)
    assert np.max(np.abs(c - ceq) / ceq) < 1e-6
    assert M.boltzmann_invariant_cv(c, phi, 0.5) < 1e-6
    assert np.max(np.abs(M.mu_spread(c, phi, 0.5))) < 1e-6


def test_partition_ratio_matches_discrete_law():
    x, phi, dx, c = _run(0.5)
    meas = M.partition_ratio_measured(c, x)
    pred = M.partition_ratio_predicted_discrete(phi, 0.5, x)
    assert abs(meas - pred) / pred < 1e-6
    assert meas < 1.0          # beta > 0 depletes the inside


def test_literal_fick_flux_has_no_chi_driven_partition():
    x, phi, dx, c = _run(0.5, D_kind="linear", kind="fick")
    assert abs(M.partition_ratio_measured(c, x) - 1.0) < 1e-6
    assert np.max(np.abs(c - 1.0)) < 1e-6          # relaxes to the uniform mass-average state


def test_fick_and_mu_coincide_when_beta_is_zero():
    x, phi, dx, c_fick = _run(0.0, D_kind="linear", kind="fick", t_eval=[0.0, 0.2])
    x, phi, dx, c_mu = _run(0.0, D_kind="linear", kind="mu", t_eval=[0.0, 0.2])
    # Different discretisations, so only the continuum limit is comparable; the difference must be small.
    assert np.max(np.abs(c_fick - c_mu)) < 0.05


def test_selectivity_comes_from_chi_difference_not_from_D():
    xA, phiA, dxA, cA = _run(0.5)
    xB, phiB, dxB, cB = _run(-0.5)
    rA = M.partition_ratio_measured(cA, xA)
    rB = M.partition_ratio_measured(cB, xB)
    assert rB / rA >= 2.0


def test_equal_chi_gives_no_selectivity_and_zero_chi_gives_uniform():
    xA, phi, dx, cA = _run(0.5)
    xB, phi, dx, cB = _run(0.5)
    assert abs(M.partition_ratio_measured(cA, xA) - M.partition_ratio_measured(cB, xB)) < 1e-9
    x0, phi0, dx0, c0 = _run(0.0)
    assert np.max(np.abs(c0 - 1.0)) < 1e-6


def test_equilibrium_independent_of_shared_mobility():
    x, phi, dx, c_const = _run(0.5, D_kind="const")
    x, phi, dx, c_lin = _run(0.5, D_kind="linear")
    pred = M.partition_ratio_predicted_discrete(phi, 0.5, x)
    for c in (c_const, c_lin):
        assert abs(M.partition_ratio_measured(c, x) - pred) / pred < 1e-6
