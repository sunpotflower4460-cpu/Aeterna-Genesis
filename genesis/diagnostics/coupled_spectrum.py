#!/usr/bin/env python3
"""Frontier Campaign M2 -- COUPLED-Jacobian eigenvalue spectroscopy (the M2 source of truth).

M1 (`angular_modes.py`, kept as history) perturbed the translation shape d_x u* of a SINGLE field and read
its short-time growth. But for a translation-symmetric PDE with a stationary state U*, the translation
Tx = d_x U* (bundling ALL fields) is a **Goldstone mode** with a NEUTRAL eigenvalue (lambda ~ 0) whether or
not a drift bifurcation has happened. So a near-zero m=1 signal is the GOLDSTONE, not evidence of drift
(GPT M2 addendum §1). A true drift bifurcation is a SEPARATE, NON-Goldstone m=1 polarity mode crossing zero.

This module solves the COUPLED-state Jacobian eigenproblem MATRIX-FREE via the time-T step map (well
conditioned: the map contracts high-k modes so ARPACK 'LM' targets |mu|~1, i.e. lambda~0):

    A v ~ [ Phi_T(U* + eps v) - Phi_T(U* - eps v) ] / (2 eps) ,   lambda = ln|mu| / (T dt)

It then IDENTIFIES the translation Goldstone (overlap with d_x U*/d_y U*, lambda~0, x/y degeneracy),
EXCLUDES it, classifies each remaining mode's angular content m (0..4) around the structure centre, and
reports the drift-before-split ordering: a spectral drift candidate needs a NON-Goldstone m=1 crossing zero
BEFORE m=2. no_touch: measures.py untouched; M1 angular_modes.py kept. Physical quantity (lambda) FIRST.
"""

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigs
from scipy import ndimage


def _deriv(field, dx, axis):
    N = field.shape[axis]
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    K = k[:, None] if axis == 0 else k[None, :]
    return np.real(np.fft.ifft2(1j * K * np.fft.fft2(field)))


def translation_modes(fields, dx, layout):
    """Coupled Goldstone shapes Tx, Ty = d/dx, d/dy of ALL fields, bundled and metric-normalised."""
    Tx = layout.flatten([_deriv(f, dx, 0) for f in fields])
    Ty = layout.flatten([_deriv(f, dx, 1) for f in fields])
    return layout.normalized(Tx), layout.normalized(Ty)


def _centre(field, thr=0.3):
    m = np.abs(field) > thr
    if m.sum() == 0:
        n = field.shape[0]
        return (n / 2.0, n / 2.0)
    idx = np.indices(field.shape)
    return (float((idx[0] * m).sum() / m.sum()), float((idx[1] * m).sum() / m.sum()))


def angular_content(field, centre, dx, nr=16, nth=64, rmax=8.0):
    """Dominant angular wavenumber m (0..5) of `field` around `centre` (polar sample -> angular FFT)."""
    cy, cx = centre
    rr = np.linspace(1.0, rmax, nr)
    th = np.linspace(0.0, 2.0 * np.pi, nth, endpoint=False)
    R, TH = np.meshgrid(rr, th, indexing="ij")
    ys = cy + R * np.cos(TH) / dx
    xs = cx + R * np.sin(TH) / dx
    vals = ndimage.map_coordinates(field, [ys, xs], order=1, mode="wrap")
    power = np.sum(np.abs(np.fft.rfft(vals, axis=1)) ** 2, axis=0)[:6]
    return int(np.argmax(power)), (power / (power.sum() + 1e-30)).tolist()


def coupled_spectrum(state_vec, step_map_T, layout, dx, T_dt, k=12, eps=1e-4, ncv=40,
                     goldstone_tol=5e-3, overlap_tol=0.4):
    """Leading eigenmodes of the coupled step-map Jacobian. `step_map_T(vec)->vec` advances the FULL state
    T steps; `T_dt = T*dt`. Returns a list of dicts (sorted by lambda desc), each with lambda, mu, overlap_x,
    overlap_y, m (of the primary field), is_goldstone."""
    n = layout.size

    def matvec(v):
        return (step_map_T(state_vec + eps * v) - step_map_T(state_vec - eps * v)) / (2.0 * eps)

    A = LinearOperator((n, n), matvec=matvec, dtype=float)
    mu, vecs = eigs(A, k=k, which="LM", ncv=min(ncv, n - 1), maxiter=4000, tol=1e-7)
    lam = np.log(np.abs(mu) + 1e-300) / float(T_dt)
    fields = layout.unflatten(state_vec)
    Tx, Ty = translation_modes(fields, dx, layout)
    centre = _centre(fields[0])
    out = []
    for i in range(len(mu)):
        q = layout.normalized(np.real(vecs[:, i]))
        ox = abs(layout.inner(q, Tx))
        oy = abs(layout.inner(q, Ty))
        qm = layout.unflatten(q)[0]                          # angular content of the primary field
        m, _ = angular_content(qm, centre, dx)
        is_gold = bool(abs(lam[i]) < goldstone_tol and max(ox, oy) > overlap_tol)
        out.append({"lambda": float(lam[i]), "mu_abs": float(abs(mu[i])), "overlap_x": round(ox, 3),
                    "overlap_y": round(oy, 3), "m": m, "is_goldstone": is_gold})
    out.sort(key=lambda d: -d["lambda"])
    return out


def classify_drift_before_split(spectrum, tol=1.0e-3):
    """Name the structure from the COUPLED spectrum with the Goldstone EXCLUDED. A spectral drift candidate
    needs a NON-Goldstone m=1 mode with Re lambda > tol that is the first to cross (>= the leading m>=2).

    Returns (label, detected, measured_by). Labels: 'spectral_drift_candidate' (non-Goldstone m=1 leads),
    'splitting' (m=2 leads), 'breathing' (m=0 leads), 'static' (nothing non-Goldstone unstable)."""
    non_gold = [s for s in spectrum if not s["is_goldstone"]]

    def lead(mset):
        c = [s["lambda"] for s in non_gold if s["m"] in mset]
        return max(c) if c else -np.inf

    l_m0, l_m1, l_m2 = lead({0}), lead({1}), lead({2, 3, 4})   # m>=2 grouped as "split/multi-split"
    goldstone_lambda = max([s["lambda"] for s in spectrum if s["is_goldstone"]], default=None)
    drift_candidate = bool(l_m1 > tol and l_m1 >= l_m2 and l_m1 >= l_m0)
    split_first = bool(l_m2 > tol and l_m2 > l_m1)
    breathing_first = bool(l_m0 > tol and l_m0 >= l_m1 and l_m0 >= l_m2)
    if drift_candidate:
        label = "spectral_drift_candidate"                    # NOT yet "self-propelled" (needs §15 audits)
    elif split_first:
        label = "splitting"
    elif breathing_first:
        label = "breathing"
    else:
        label = "static"
    detected = {"spectral_drift_candidate": drift_candidate, "splitting": split_first,
                "breathing": breathing_first, "static": bool(label == "static"),
                "non_goldstone_m1_unstable": bool(l_m1 > tol)}
    measured_by = {"lambda_goldstone": (round(goldstone_lambda, 5) if goldstone_lambda is not None else None),
                   "lambda_m0": (round(l_m0, 5) if np.isfinite(l_m0) else None),
                   "lambda_m1_non_goldstone": (round(l_m1, 5) if np.isfinite(l_m1) else None),
                   "lambda_m2plus": (round(l_m2, 5) if np.isfinite(l_m2) else None),
                   "drift_margin": (round(l_m1 - l_m2, 5) if np.isfinite(l_m1) and np.isfinite(l_m2) else None)}
    return label, detected, measured_by
