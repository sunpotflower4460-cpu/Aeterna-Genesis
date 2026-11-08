"""Time integration of the closed well-mixed network (v0.1).

Primary: scipy solve_ivp, BDF, rtol/atol from PRE_REGISTRATION.json, no clipping. Output is returned as is.
Secondary (T15 only): Gillespie SSA for the single association X+Y <-> XY.
"""
import numpy as np
from scipy.integrate import solve_ivp

import reaction_network as RN
import thermodynamics as TH


def rates_for(kr_scale=1.0, kf_scale=1.0):
    kf, kr = TH.forward_reverse_rates()
    return kf * kf_scale, kr * kr_scale


def _rhs_factory(kf, kr):
    def rhs(_t, c):
        r = TH.reaction_rates(c, kf, kr)
        return RN.NU @ r
    return rhs


def integrate(c0, duration, kf, kr, rtol=1e-9, atol=1e-12, t_eval=None):
    """Integrate dc/dt = NU r(c) from 0 to duration. Returns (t, C) with C shape (n_t, 6). No clipping."""
    c0 = np.asarray(c0, dtype=float)
    if duration == 0.0:
        return np.array([0.0]), c0[None, :].copy()
    rhs = _rhs_factory(kf, kr)
    if t_eval is None:
        t_eval = [0.0, duration]
    res = solve_ivp(rhs, (0.0, duration), c0, method="BDF", t_eval=t_eval, rtol=rtol, atol=atol)
    if not res.success:
        raise RuntimeError(f"integrator failed: {res.message}")
    return res.t, res.y.T


def end_state(c0, duration, kf, kr, rtol=1e-9, atol=1e-12):
    _, C = integrate(c0, duration, kf, kr, rtol=rtol, atol=atol)
    return C[-1]


def gillespie_xy(nX, nY, nXY, omega, kf, kr, t_end, rng):
    """Exact SSA for X+Y <-> XY with counts; propensities use concentrations c = n / omega (V = 1 scaled).

    a_f = kf * nX * nY / omega (bimolecular, concentration-based rate constant), a_r = kr * nXY.
    Returns counts at t_end. Used only for the T15 cross-check.
    """
    t = 0.0
    while True:
        af = kf * nX * nY / omega
        ar = kr * nXY
        a0 = af + ar
        if a0 <= 0:
            return nX, nY, nXY
        t += rng.exponential(1.0 / a0)
        if t > t_end:
            return nX, nY, nXY
        if rng.random() * a0 < af:
            nX -= 1; nY -= 1; nXY += 1
        else:
            nX += 1; nY += 1; nXY -= 1
