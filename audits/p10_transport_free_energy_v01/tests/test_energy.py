"""T8: the reference free energy is non-increasing for the mu flux, and dF/dt equals minus the dissipation.

Only the mu flux is tested for monotonicity. The literal F0 flux is not a gradient flow of F_ref in general
(FORMULA_AUDIT E-2), so it is not asserted here.
"""
import numpy as np

import _setup  # noqa: F401
import model
import solver
import metrics as M


def _F_series_on(beta, N, t):
    dx, x = model.grid(N)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, "const")
    s = solver.make_setup(N, phi, D, beta, dx, "mu")
    r = solver.run_bdf(s, 1.0 + 0.5 * np.cos(2 * np.pi * x), t, rtol=1e-9, atol=1e-12)
    assert r["success"]
    return r["t"], r["C"], M.energy_series(r["C"], phi, beta, dx), phi, D, dx


def _F_series(beta, N, t_end=2.0, nt=401):
    return _F_series_on(beta, N, np.linspace(0, t_end, nt))


def test_free_energy_non_increasing_for_mu_flux():
    for beta in (0.5, -0.5):
        for N in (64, 128):
            _, _, F, _, _, _ = _F_series(beta, N)
            assert np.max(np.diff(F)) <= 1e-7


def test_energy_identity_dF_equals_integrated_minus_dissipation():
    # AMD-2: graded time grid resolves the initial transient (uniform grids give 1e-3..1e-2 trapezoid error)
    t_id = np.concatenate([[0.0], np.geomspace(1e-5, 0.1, 400), np.linspace(0.1, 2.0, 2000)[1:]])
    t, C, F, phi, D, dx = _F_series_on(0.5, 128, t_id)
    diss = np.array([model.dissipation_mu(c, phi, 0.5, D, dx) for c in C])
    lhs = F[-1] - F[0]
    rhs = -np.trapezoid(diss, t)
    assert abs(lhs - rhs) / max(abs(lhs), 1e-6) < 1e-4


def test_dissipation_is_nonnegative():
    dx, x = model.grid(64)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, "linear")
    rng = np.random.default_rng(3)
    for _ in range(5):
        c = 0.5 + rng.random(64)
        assert model.dissipation_mu(c, phi, 0.7, D, dx) >= 0.0
