#!/usr/bin/env python3
"""Frontier Campaign M1 / V1 -- NON-VARIATIONAL Swift-Hohenberg: a DISTINCT white that breaks the gradient
structure of SH (#40) to probe whether the translation mode (m=1) can be destabilised -- i.e. whether a
static localized individual can be MEASURED to self-propel (drift bifurcation), the affirmative counterpart
to the variational no-go (docs/ANGULAR_MODES.md, #44).

    u_t = [ r u - (1+lap)^2 u + b u^3 - u^5 ]      (the variational SH part, genesis/models/swift_hohenberg)
        + a * |grad u|^2 + c * u lap(u)            (ISOTROPIC, parity-even, NON-VARIATIONAL terms)

The non-variational terms are rotationally invariant (no preferred direction) and parity-even (a symmetric
state remains a solution): if translation (m=1) went unstable, the drift direction would be chosen by
spontaneous symmetry breaking (random per seed), NOT imposed -- ANTI_DRIFT-clean (docs/ANTI_DRIFT.md 精密化③:
give the CAPACITY to move, not the direction).

MEASURED STATUS (docs/ANGULAR_MODES.md): in this white the non-variational term drives the SPLIT mode (m=2)
toward instability BEFORE the translation mode (m=1), which stays marginal -- i.e. **split-before-drift**:
the structure tends to SPLIT, not self-propel. Increasing the coefficient blows the state up before m=1
lifts. So a self-propelled individual (drift-before-split) is NOT found in the SH family (variational or
this non-variational form) = white-specific frontier, with the mechanistic finding that this family couples
to m=2 (split) more strongly than to m=1 (drift). 「同じ数学 != 同じもの」.
"""

import numpy as np

from genesis.models import swift_hohenberg as sh

MODEL_ID = "nvsh_nonvariational_swift_hohenberg"

# a = |grad u|^2 coefficient, c = u lap(u) coefficient. Small (larger -> blow-up before m=1 lifts).
DEFAULTS = dict(sh.DEFAULTS)
DEFAULTS.update({"nv_grad2": 0.5, "nv_ulap": 0.0})


def _wavenumbers(N, dx):
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    return k[:, None], k[None, :]


def make_step(N, p):
    """Return a step_fn(u)->u_next for the non-variational SH white (variational SH + isotropic NV terms)."""
    k2 = sh._k2(N, p["dx"])
    kx, ky = _wavenumbers(N, p["dx"])
    a, c, dt = p["nv_grad2"], p["nv_ulap"], p["dt"]

    def step_fn(u):
        u_var = sh.step(u, p, k2)                              # variational SH part (exact-diffusion split)
        uh = np.fft.fft2(u)
        ux = np.real(np.fft.ifft2(1j * kx * uh))
        uy = np.real(np.fft.ifft2(1j * ky * uh))
        lap = np.real(np.fft.ifft2(-k2 * uh))
        nv = a * (ux * ux + uy * uy) + c * (u * lap)          # isotropic, parity-even, non-variational
        return u_var + dt * nv

    return step_fn, k2


def settle_static(N=64, steps=2500, seed=0, p=None):
    """Settle the VARIATIONAL SH localized state (the static individual whose modes we then probe)."""
    p = dict(DEFAULTS if p is None else p)
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    k2 = sh._k2(N, p["dx"])
    for _ in range(steps):
        u = sh.step(u, p, k2)
    return u, p


def angular_spectrum(nv_grad2, N=64, settle_steps=2500, relax=400, t_steps=250, seed=0):
    """Measure the angular-mode spectrum (m=0/1/2) of the SH localized state under the non-variational flow
    with |grad u|^2 coefficient `nv_grad2`. Returns (sigmas, label, measured_by) or {'unstable': True}."""
    from genesis.diagnostics import angular_modes as am
    u_star, p = settle_static(N=N, steps=settle_steps, seed=seed)
    p = dict(p); p["nv_grad2"] = float(nv_grad2)
    step_fn, _ = make_step(N, p)
    u = u_star.copy()
    for _ in range(relax):                                     # let it relax to a fixed point of the NV flow
        u = step_fn(u)
        if not np.all(np.isfinite(u)):
            return {"unstable": True, "nv_grad2": float(nv_grad2)}
    sig = am.angular_mode_growth_rates(u, step_fn, dx=p["dx"], dt=p["dt"], t_steps=t_steps)
    label, detected, mb = am.classify_angular_spectrum(sig)
    return {"unstable": False, "nv_grad2": float(nv_grad2), "sigmas": sig, "label": label,
            "detected": detected, "measured_by": mb}
