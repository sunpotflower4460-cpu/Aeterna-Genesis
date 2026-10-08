"""Time integration for the independent 1-D model (v0.1).

Primary: scipy.integrate.solve_ivp with BDF (rtol/atol from PRE_REGISTRATION.json), tridiagonal
Jacobian sparsity. Secondary: explicit classical RK4 with a fixed step, used only for the time-step
convergence check (T10c). Neither integrator clips, floors or otherwise edits the state: a negative
or non-finite value is returned as is and judged by metrics.py.
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import diags

import model


def make_setup(N, phi, D, beta, dx, kind="mu"):
    """Bundle of fixed quantities for one species. kind='mu' (main flux B) or 'fick' (control A)."""
    return {"N": N, "dx": dx, "phi": phi, "D": D, "beta": float(beta), "kind": kind}


def rhs_of(setup):
    """Return the right-hand side c -> dc/dt for a setup (no state modification)."""
    dx, phi, D, beta, kind = setup["dx"], setup["phi"], setup["D"], setup["beta"], setup["kind"]
    if kind == "mu":
        def rhs(c):
            return model.rhs_from_flux(model.flux_mu(c, phi, beta, D, dx), dx)
    elif kind == "fick":
        def rhs(c):
            return model.rhs_from_flux(model.flux_fick(c, D, dx), dx)
    else:
        raise ValueError(kind)
    return rhs


def _tridiag(N):
    return diags([np.ones(N - 1), np.ones(N), np.ones(N - 1)], [-1, 0, 1], shape=(N, N), format="csr")


def run_bdf(setup, c0, t_eval, rtol=1e-9, atol=1e-12):
    """BDF integration of one species. Returns dict with t, C (n_t x N), success flag and message.

    C is returned even if the integrator reports a failure, so the caller can record it.
    """
    rhs = rhs_of(setup)
    N = setup["N"]
    t_eval = np.asarray(t_eval, dtype=float)
    res = solve_ivp(lambda t, y: rhs(y), (t_eval[0], t_eval[-1]), np.asarray(c0, dtype=float),
                    method="BDF", t_eval=t_eval, rtol=rtol, atol=atol, jac_sparsity=_tridiag(N))
    C = res.y.T if res.y.size else np.empty((0, N))
    return {"t": res.t, "C": C, "success": bool(res.success), "status": int(res.status),
            "message": str(res.message), "nfev": int(res.nfev)}


def run_rk4(setup, c0, t_end, dt):
    """Fixed-step explicit RK4. Returns the final state and the number of steps."""
    rhs = rhs_of(setup)
    n_steps = int(round(t_end / dt))
    c = np.asarray(c0, dtype=float).copy()
    for _ in range(n_steps):
        k1 = rhs(c)
        k2 = rhs(c + 0.5 * dt * k1)
        k3 = rhs(c + 0.5 * dt * k2)
        k4 = rhs(c + dt * k3)
        c = c + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return c, n_steps
