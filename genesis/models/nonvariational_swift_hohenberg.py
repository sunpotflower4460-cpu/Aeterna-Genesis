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


def coupled_audit(a, c, N=64, settle_steps=2500, relax=600, T=50, seed=0, k=10):
    """M2-B: re-measure this white at (a,c) with the COUPLED-Jacobian eigenvalue solver (not the M1 proxy).
    Settle the variational LS, relax to a fixed point of the non-variational flow, measure the residual and
    the base-state centre drift, then compute the coupled spectrum, identify/exclude the translation
    Goldstone, and classify drift-before-split. Returns residual/center_drift, the classification, and the
    leading NON-Goldstone m=1 and m>=2 eigenvalues (docs/ANGULAR_MODES.md M2)."""
    import numpy as np
    from genesis.models.adapters.state_layout import StateLayout
    from genesis.diagnostics import coupled_spectrum as cs
    u, p0 = settle_static(N=N, steps=settle_steps, seed=seed)
    p = dict(p0); p["nv_grad2"] = float(a); p["nv_ulap"] = float(c)
    step_fn, _ = make_step(N, p)
    for _ in range(relax):
        u = step_fn(u)
        if not np.all(np.isfinite(u)):
            return {"a": float(a), "c": float(c), "unstable": True}
    residual = float(np.linalg.norm(step_fn(u) - u))
    idx = np.indices(u.shape)
    mA = np.abs(u) > 0.3
    c0 = (float((idx[0] * mA).sum() / mA.sum()), float((idx[1] * mA).sum() / mA.sum()))
    w = u.copy()
    for _ in range(50):
        w = step_fn(w)
    mB = np.abs(w) > 0.3
    center_drift = float(np.hypot((idx[0] * mB).sum() / mB.sum() - c0[0],
                                  (idx[1] * mB).sum() / mB.sum() - c0[1]) / (50 * p["dt"]))
    lay = StateLayout(("u",), ((N, N),))

    def step_T(vec):
        z = vec.reshape(N, N)
        for _ in range(T):
            z = step_fn(z)
        return z.ravel()

    spec = cs.coupled_spectrum(u.ravel(), step_T, lay, dx=p["dx"], T_dt=T * p["dt"], k=k)
    label, detected, mb = cs.classify_drift_before_split(spec)
    return {"a": float(a), "c": float(c), "unstable": False, "residual": residual,
            "center_drift": center_drift, "n_goldstone": sum(1 for s in spec if s["is_goldstone"]),
            "label": label, "detected": detected, "measured_by": mb}
