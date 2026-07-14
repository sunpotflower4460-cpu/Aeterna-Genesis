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
    """d/d(axis) via spectral differentiation, for ANY number of dimensions (2D or 3D)."""
    N = field.shape[axis]
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    shape = [1] * field.ndim
    shape[axis] = N
    K = k.reshape(shape)
    return np.real(np.fft.ifftn(1j * K * np.fft.fftn(field)))


def translation_modes(fields, dx, layout):
    """Coupled translation Goldstone shapes = d/d(axis) of ALL fields, bundled and metric-normalised.
    Returns ONE mode per spatial axis: [Tx, Ty] in 2D, [Tx, Ty, Tz] in 3D."""
    ndim = fields[0].ndim
    return [layout.normalized(layout.flatten([_deriv(f, dx, ax) for f in fields])) for ax in range(ndim)]


def _centre(field, thr=0.3):
    m = np.abs(field) > thr
    idx = np.indices(field.shape)
    if m.sum() == 0:
        return tuple(s / 2.0 for s in field.shape)
    return tuple(float((idx[a] * m).sum() / m.sum()) for a in range(field.ndim))


def _fib_sphere(n):
    """n quasi-uniform unit directions on the sphere (Fibonacci lattice), as an (n, 3) array."""
    i = np.arange(n) + 0.5
    phi = np.arccos(1.0 - 2.0 * i / n)
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)], axis=1)


def _angular_content_3d(field, centre, dx, nr=12, rmax=8.0, ndir=150):
    """Dominant SPHERICAL-HARMONIC degree ell (0=breathing/monopole, 1=translation/dipole, 2=split/
    quadrupole) of a 3D `field` around `centre`: sample on spherical shells, project onto real SH l=0,1,2."""
    dirs = _fib_sphere(ndir)                                  # (ndir, 3) unit vectors in (axis0,1,2)
    x, y, z = dirs[:, 0], dirs[:, 1], dirs[:, 2]
    groups = [(0, [np.ones_like(x)]),
              (1, [x, y, z]),
              (2, [x * y, y * z, z * x, x * x - y * y, 3.0 * z * z - 1.0])]  # orthogonal over the sphere
    c = np.array(centre)
    rr = np.linspace(1.0, rmax, nr)
    power = np.zeros(3)
    for r in rr:
        pts = c[:, None] + r * dirs.T / dx                   # (3, ndir) index coordinates
        vals = ndimage.map_coordinates(field, pts, order=1, mode="wrap")
        for ell, basis in groups:
            for B in basis:
                Bn = B / (np.sqrt(np.mean(B * B)) + 1e-30)    # normalise each SH over the sample
                power[ell] += float(np.mean(vals * Bn)) ** 2
    return int(np.argmax(power)), (power / (power.sum() + 1e-30)).tolist()


def angular_content(field, centre, dx, nr=16, nth=64, rmax=8.0):
    """Dominant angular index of `field` around `centre`: in 2D the angular wavenumber m (0..5, polar FFT);
    in 3D the spherical-harmonic degree ell (0..2). Both use 1=translation/drift, >=2=split -- so the same
    drift-before-split classifier works in either dimension."""
    if field.ndim == 3:
        return _angular_content_3d(field, centre, dx, nr=nr, rmax=rmax)
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
    trans = translation_modes(fields, dx, layout)            # [Tx, Ty] (2D) or [Tx, Ty, Tz] (3D)
    centre = _centre(fields[0])
    ndim = fields[0].ndim
    out = []
    for i in range(len(mu)):
        q = layout.normalized(np.real(vecs[:, i]))
        overlaps = [abs(layout.inner(q, T)) for T in trans]  # overlap with each translation Goldstone
        qm = layout.unflatten(q)[0]                          # angular content of the primary field
        m, _ = angular_content(qm, centre, dx)               # m (2D) or spherical ell (3D)
        is_gold = bool(abs(lam[i]) < goldstone_tol and max(overlaps) > overlap_tol)
        d = {"lambda": float(lam[i]), "mu_abs": float(abs(mu[i])), "overlap_x": round(overlaps[0], 3),
             "overlap_y": round(overlaps[1], 3), "m": m, "is_goldstone": is_gold}
        if ndim == 3:
            d["overlap_z"] = round(overlaps[2], 3)
        out.append(d)
    out.sort(key=lambda d: -d["lambda"])
    return out


def existence_gate(state_vec, next_vec, layout, count, area_frac, res_gate=1e-2, area_max=0.5):
    """Guard BEFORE linearising: refuse to compute/interpret a coupled spectrum unless the base state is a
    genuine COMPACT LOCALIZED (single) STATIONARY individual. A drift bifurcation is a statement ABOUT an
    individual; if the state has DIED, keeps EVOLVING (not a fixed point), or the domain is FILLED (uniform,
    not localized), there is no individual to linearise around and any eigenvalues would be meaningless. This
    encodes the honest posture that an EXISTENCE frontier is UPSTREAM of a drift frontier (docs/ANGULAR_MODES.md
    M2-C): the instrument must not hallucinate a spectrum where there is no individual.

    Returns (ok, info) where info carries the measured rel_res / localized / stationary / count / area_frac and,
    when refused, the `reason` ('no_localized_individual' | 'not_stationary'). `state_vec`/`next_vec` are the
    bundled full state at t and t+dt (one step), `layout` the StateLayout, `count`/`area_frac` the connected
    activator-spot count and its area fraction of the domain."""
    rel_res = float(np.linalg.norm(next_vec - state_vec) / (np.linalg.norm(state_vec) + 1e-30))
    localized = bool(count == 1 and 0.0 < area_frac < area_max)
    stationary = bool(rel_res < res_gate)
    ok = bool(localized and stationary)
    reason = None if ok else ("no_localized_individual" if not localized else "not_stationary")
    return ok, {"rel_res": round(rel_res, 6), "localized": localized, "stationary": stationary,
                "count": int(count), "area_frac": round(float(area_frac), 4), "reason": reason}


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
