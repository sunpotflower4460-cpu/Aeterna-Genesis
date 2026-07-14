#!/usr/bin/env python3
"""Dimension-agnostic complex Ginzburg-Landau with a LOCAL nearest-neighbour Laplacian (np.roll only -- no
FFT, no global solve): the SAME code runs in 2D or 3D. From a structureless start (near-zero + tiny complex
noise; NO seeded vortex lines) a vortex tangle GROWS on its own -- in 3D the vortices are LINES threading the
volume (a genuinely 3D object). Honours AGENTS.md: local x parallel x central-none, and grow-don't-place.

    dA/dt = A + (1 + i b) lap(A) - (1 + i c) |A|^2 A

Good part imported from the Genesis-Room- repo (`g001_cgl_3d`) into Aeterna-Genesis as the first local,
3D-capable white. no_touch: measures.py untouched. 「同じ数学 != 同じもの」: a vortex tangle is a field
structure, not life.
"""
import numpy as np

MODEL_ID = "cgl_local"

DEFAULTS = {"b": 0.0, "c": 0.0}


def local_laplacian(z):
    """LOCAL periodic Laplacian for ANY number of dimensions: -2*ndim*z + sum over axes of roll(+-1).
    Nearest neighbours only (7-point in 3D, 5-point in 2D) -- no FFT, no global operation."""
    out = -2.0 * z.ndim * z
    for ax in range(z.ndim):
        out = out + np.roll(z, 1, ax) + np.roll(z, -1, ax)
    return out


def stable_dt(ndim, b, dx=1.0, safety=0.4, dt_min=0.002, dt_max=0.05):
    """Explicit-Euler stability bound for dA/dt superset (1+ib)*lap(A): |1+dt*g| <= 1 at the most negative
    periodic-stencil eigenvalue (-4*ndim/dx^2). Larger |b| tightens dt (imaginary part grows)."""
    lap_max = 4.0 * ndim / dx ** 2
    re_g = 1.0 - lap_max
    im_g = b * lap_max
    denom = re_g ** 2 + im_g ** 2
    dt = safety * (-2.0 * re_g) / denom if denom > 0 else dt_max
    return float(min(max(dt, dt_min), dt_max))


def make_initial(shape, noise_amplitude, rng):
    """Uniform near-zero + tiny complex noise. NO seeded vortex lines/loops (grow, don't place)."""
    return (noise_amplitude * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))).astype(np.complex128)


def step(A, dt, p):
    """One explicit local step (nearest-neighbour Laplacian only)."""
    lap = local_laplacian(A)
    return A + dt * (A + (1.0 + 1j * p["b"]) * lap - (1.0 + 1j * p["c"]) * (np.abs(A) ** 2) * A)


def spectral_k2(shape, dx=1.0):
    """|k|^2 grid for the pseudo-spectral Laplacian (independent numerics for corroboration)."""
    ks = [np.fft.fftfreq(n, d=dx) * 2.0 * np.pi for n in shape]
    K = np.meshgrid(*ks, indexing="ij")
    return sum(k ** 2 for k in K)


def step_spectral(A, dt, p, k2):
    """One explicit step with a SPECTRAL (FFT) Laplacian instead of the local stencil. Same PDE, same time
    integrator, DIFFERENT spatial discretisation -> agreement of physical observables with `step` is
    solver-independent corroboration (not a finite-difference artefact). Not the local main line -- a verifier."""
    lap = np.fft.ifftn(-k2 * np.fft.fftn(A))
    return A + dt * (A + (1.0 + 1j * p["b"]) * lap - (1.0 + 1j * p["c"]) * (np.abs(A) ** 2) * A)


def run(shape, t_final, seed, params=None, noise_amplitude=0.01, dt=None, snap_frac=1.0 / 20):
    """Evolve from t=0 (near-zero + noise) with no intervention; return (snapshots, phys). `shape` sets the
    dimension (len 2 -> 2D, len 3 -> 3D). dt auto-selected from b if None."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    ndim = len(shape)
    dt = dt if dt is not None else stable_dt(ndim, p["b"])
    steps = int(round(t_final / dt))
    every = max(1, int(steps * snap_frac))
    rng = np.random.default_rng(seed)
    A = make_initial(shape, noise_amplitude, rng)
    snaps = []
    diverged = False
    for t in range(steps):
        A = step(A, dt, p)
        if not np.all(np.isfinite(A)):
            diverged = True
            break
        if t % every == 0 or t == steps - 1:
            snaps.append({"step": t, "field": A.copy()})
    if not snaps:
        snaps = [{"step": 0, "field": A.copy()}]
    return snaps, {"diverged": diverged, "dt_used": dt, "steps": steps}
