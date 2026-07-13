#!/usr/bin/env python3
"""Frontier Campaign M1 -- ANGULAR-MODE growth-rate spectroscopy of a stationary localized structure.

The self-propulsion frontier is attacked by MEASUREMENT, not by searching for moving models: perturb a
settled localized structure by its angular modes and measure which mode destabilizes FIRST.

    m = 0  breathing       (radial dilation)
    m = 1  translation     (rigid shift)  -> if this goes unstable FIRST, the body self-propels (drift)
    m = 2  split/elliptical (quadrupole)  -> if this goes unstable first, the body splits (Gray-Scott trap)

The signature of a self-propelled individual is **drift-before-split**: sigma(m=1) > 0 AND sigma(m=1) is the
largest (destabilizes before m=2). For a VARIATIONAL white (a pure gradient flow, e.g. Swift-Hohenberg) the
translation mode is a Goldstone mode with sigma(m=1) ~ 0 (marginal, never positive): a gradient flow CANNOT
spontaneously self-propel -- the GPT/Claude no-go, here MEASURED not asserted.

Physical quantity FIRST, label AFTER (docs/ANTI_DRIFT.md 精密化). This module is NEW and ADDITIVE; it does
not touch genesis/diagnostics/measures.py. 「同じ数学 != 同じもの」: a growth rate is a growth rate.
"""

import numpy as np

MODE_KEYS = ("m0_breathing", "m1_translation", "m2_split")


def _deriv(u, dx, axis):
    N = u.shape[axis]
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    K = k[:, None] if axis == 0 else k[None, :]
    return np.real(np.fft.ifft2(1j * K * np.fft.fft2(u)))


def mode_shapes(u_star, dx):
    """Angular-mode perturbation shapes built from spatial derivatives of the settled structure u_star,
    each normalised. Translation = du/dx, du/dy (Goldstone); breathing = r.grad u; quadrupole = x u_x - y u_y."""
    N = u_star.shape[0]
    x = (np.arange(N) - N / 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    ux, uy = _deriv(u_star, dx, 0), _deriv(u_star, dx, 1)
    raw = {"m1_transx": ux, "m1_transy": uy,
           "m0_breathing": X * ux + Y * uy, "m2_split": X * ux - Y * uy}
    return {k: v / (np.sqrt(np.sum(v * v)) + 1e-30) for k, v in raw.items()}


def _growth_rate(u_star, step_fn, phi, dt, eps=5e-3, t_steps=300):
    """sigma = ln(|a(T)|/|a(0)|)/T where a(t) = <u(t)-u_star, phi>. u_star is a fixed point, so the
    unperturbed drift is ~0 and a(t) tracks the linear evolution of the phi-mode. <0 stable, ~0 marginal,
    >0 unstable."""
    u = u_star + eps * phi
    a0 = float(np.sum((u - u_star) * phi))
    for _ in range(t_steps):
        u = step_fn(u)
    aT = float(np.sum((u - u_star) * phi))
    T = t_steps * dt
    return float(np.log(max(abs(aT), 1e-12) / max(abs(a0), 1e-30)) / T)


def angular_mode_growth_rates(u_star, step_fn, dx, dt, eps=5e-3, t_steps=300):
    """Measure sigma for m=0 (breathing), m=1 (translation; max over x/y), m=2 (split). step_fn(u)->u_next
    advances the SAME PDE the structure came from. Returns {m0_breathing, m1_translation, m2_split}."""
    sh = mode_shapes(u_star, dx)
    sx = _growth_rate(u_star, step_fn, sh["m1_transx"], dt, eps, t_steps)
    sy = _growth_rate(u_star, step_fn, sh["m1_transy"], dt, eps, t_steps)
    return {"m0_breathing": _growth_rate(u_star, step_fn, sh["m0_breathing"], dt, eps, t_steps),
            "m1_translation": max(sx, sy),
            "m2_split": _growth_rate(u_star, step_fn, sh["m2_split"], dt, eps, t_steps)}


def classify_angular_spectrum(sigmas, tol=1.0e-3):
    """Name the structure from its angular spectrum -- AFTER measuring (M1). A self-propelled individual =
    DRIFT-BEFORE-SPLIT: m=1 unstable AND m=1 the most unstable mode. A gradient-flow white has m=1 ~ 0
    (marginal) => static (no-go).

    Returns (label, detected, measured_by). Labels: 'self_propelled_drift' (m=1 first), 'splitting' (m=2
    first, the replication trap), 'breathing' (m=0 first), 'static' (nothing unstable; m=1 <= tol)."""
    s0 = float(sigmas["m0_breathing"]); s1 = float(sigmas["m1_translation"]); s2 = float(sigmas["m2_split"])
    unstable = {k: v for k, v in {"m0_breathing": s0, "m1_translation": s1, "m2_split": s2}.items() if v > tol}
    drift_before_split = bool(s1 > tol and s1 >= s2 and s1 >= s0)   # translation destabilises first
    split_first = bool(s2 > tol and s2 > s1)
    breathing_first = bool(s0 > tol and s0 >= s1 and s0 >= s2)
    if drift_before_split:
        label = "self_propelled_drift"
    elif split_first:
        label = "splitting"                                        # m=2 first = splits/replicates (not one body)
    elif breathing_first:
        label = "breathing"
    else:
        label = "static"                                           # nothing unstable; m=1 marginal (variational no-go)
    detected = {"self_propelled_drift": drift_before_split, "splitting": split_first,
                "breathing": breathing_first, "static": bool(label == "static"),
                "translation_marginal_or_stable": bool(s1 <= tol)}
    measured_by = {"sigma_m0": round(s0, 5), "sigma_m1": round(s1, 5), "sigma_m2": round(s2, 5),
                   "first_unstable_mode": (max(unstable, key=unstable.get) if unstable else None),
                   "drift_minus_split": round(s1 - s2, 5)}
    return label, detected, measured_by
