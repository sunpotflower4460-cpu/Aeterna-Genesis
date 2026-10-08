"""T7: exact species mass, strict positivity (no clipping), finiteness, and the zero-wall structure."""
import numpy as np

import _setup  # noqa: F401
import model
import solver
import metrics as M


def _series(beta, kind="mu", N=64, D_kind="linear", t_end=2.0):
    dx, x = model.grid(N)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, D_kind)
    s = solver.make_setup(N, phi, D, beta, dx, kind)
    c0 = 1.0 + 0.5 * np.cos(2 * np.pi * x)
    r = solver.run_bdf(s, c0, np.linspace(0, t_end, 401), rtol=1e-9, atol=1e-12)
    assert r["success"], r["message"]
    return r["C"], dx


def test_mass_is_conserved_to_roundoff_for_mu_flux():
    C, dx = _series(0.5)
    assert M.mass_residual_rel(C, dx, 1.0) < 1e-9


def test_mass_is_conserved_for_literal_fick_flux_too():
    C, dx = _series(0.5, kind="fick")
    assert M.mass_residual_rel(C, dx, 1.0) < 1e-9


def test_strictly_positive_and_finite_no_clipping():
    C, dx = _series(0.5)
    finite, cmin = M.finite_and_positive(C)
    assert finite and cmin > 0.0


def test_sharp_interface_and_large_beta_stay_positive():
    dx, x = model.grid(128)
    phi = model.phi_profile(x, width=0.02)
    s = solver.make_setup(128, phi, model.D_field(phi, 1.0, "const"), 1.5, dx, "mu")
    r = solver.run_bdf(s, 1.0 + 0.5 * np.cos(2 * np.pi * x), np.linspace(0, 2.0, 201), rtol=1e-9, atol=1e-12)
    assert r["success"]
    finite, cmin = M.finite_and_positive(r["C"])
    assert finite and cmin > 0.0
    assert M.mass_residual_rel(r["C"], dx, 1.0) < 1e-9


def test_rhs_conserves_total_mass_at_random_positive_states():
    rng = np.random.default_rng(7)
    for N in (32, 128):
        dx, x = model.grid(N)
        phi = model.phi_profile(x)
        D = model.D_field(phi, 1.0, "linear")
        c = 0.5 + rng.random(N)
        for J in (model.flux_mu(c, phi, 0.5, D, dx), model.flux_fick(c, D, dx)):
            rhs = model.rhs_from_flux(J, dx)
            assert abs(np.sum(rhs) * dx) <= 1e-12 * max(1.0, np.sum(np.abs(rhs)) * dx)
            assert J[0] == 0.0 and J[-1] == 0.0          # no-flux walls by construction
