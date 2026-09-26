"""Wave white: a real scalar field obeying a nonlinear Klein–Gordon equation (light-like, reversible).

    φ_tt = ∇²φ − V'(φ) − γ(x) φ_t          (c = 1, lattice spacing dx = 1)

    potential "phi4":         V(φ) = (λ/4)(φ² − 1)²     two valleys φ = ±1, a hill at φ = 0 (height λ/4)
    potential "sine_gordon":  V(φ) = λ(1 − cos φ)       valleys at 2πk, hills at π + 2πk

Why this white (docs/reports, P7 "光から考え直す白"):
* waves travel at a FINITE speed (the light cone), unlike diffusion, where every point feels every other at once;
* with γ = 0 the dynamics is time-reversible and conserves energy: no arrow of time is put in;
* it is computed the way AGENTS.md asks: local (nearest-neighbour stencil) × parallel × no central solver.

Put in:
* the law (the shape of V: which valleys exist);
* t = 0: the field sits on the hill (φ = 0 for φ⁴, φ = π for sine-Gordon) with tiny white noise (`noise`), at rest;
* optional absorbing border (γ > 0 in a strip of width `absorb_width`): energy leaves through the edge.
  This is an explicit put-in (an open boundary, i.e. an arrow of time at the edge); γ = 0 (the default)
  leaves a closed, periodic, reversible universe.

Integrator: leapfrog / velocity-Verlet (symplectic, time-reversible for γ = 0), periodic boundaries,
works for 1D, 2D and 3D arrays. Stable for dt < 1/sqrt(ndim) (CFL); DEFAULTS use dt = 0.2.
"""
from __future__ import annotations

from typing import Any

import numpy as np

DEFAULTS: dict[str, Any] = {
    "potential": "phi4",
    "lam": 1.0,            # strength of the potential
    "dt": 0.2,
    "noise": 0.01,         # t = 0 noise amplitude (put in)
    "bias": 0.0,           # t = 0 mean offset from the hilltop (0 = exactly symmetric; put in)
    "absorb": 0.0,         # γ in the absorbing border (0 = closed universe)
    "absorb_width": 8,
}


def hilltop(p: dict[str, Any]) -> float:
    return float(np.pi) if p["potential"] == "sine_gordon" else 0.0


def dV(phi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    lam = p["lam"]
    if p["potential"] == "sine_gordon":
        return lam * np.sin(phi)
    return lam * phi * (phi * phi - 1.0)


def V(phi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    lam = p["lam"]
    if p["potential"] == "sine_gordon":
        return lam * (1.0 - np.cos(phi))
    return 0.25 * lam * (phi * phi - 1.0) ** 2


def laplacian(phi: np.ndarray) -> np.ndarray:
    """Nearest-neighbour (2·ndim+1)-point Laplacian, periodic: each cell only looks at its neighbours."""
    out = -2.0 * phi.ndim * phi
    for ax in range(phi.ndim):
        out += np.roll(phi, 1, ax) + np.roll(phi, -1, ax)
    return out


def damping_mask(shape: tuple[int, ...], width: int) -> np.ndarray:
    """1 inside the absorbing border strip (distance to the box edge < width), 0 elsewhere."""
    m = np.zeros(shape, dtype=bool)
    for ax, n in enumerate(shape):
        idx = np.arange(n)
        edge = np.minimum(idx, n - 1 - idx) < width
        sl = [None] * len(shape)
        sl[ax] = slice(None)
        m |= edge[tuple(sl)]
    return m.astype(float)


def make_initial(shape: tuple[int, ...], rng: np.random.Generator, p: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """On the hill, at rest, plus tiny white noise. Nothing else is placed."""
    phi = hilltop(p) + p.get("bias", 0.0) + p["noise"] * rng.standard_normal(shape)
    return phi, np.zeros(shape)


def step(phi: np.ndarray, pi: np.ndarray, p: dict[str, Any], mask: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """One velocity-Verlet step. With absorb > 0, the border's momentum is damped by exp(−γ dt) (split step)."""
    dt = p["dt"]
    pi = pi + 0.5 * dt * (laplacian(phi) - dV(phi, p))
    phi = phi + dt * pi
    pi = pi + 0.5 * dt * (laplacian(phi) - dV(phi, p))
    if p.get("absorb", 0.0) > 0.0 and mask is not None:
        pi = pi * np.exp(-p["absorb"] * dt * mask)
    return phi, pi


# ---------------------------------------------------------------------------------------- measures
def energy_density(phi: np.ndarray, pi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    """½π² + ½Σ(forward differences)² + V. Its sum is the energy the leapfrog conserves (to O(dt²), bounded)."""
    grad2 = np.zeros_like(phi)
    for ax in range(phi.ndim):
        grad2 += (np.roll(phi, -1, ax) - phi) ** 2
    return 0.5 * pi * pi + 0.5 * grad2 + V(phi, p)


def energy(phi: np.ndarray, pi: np.ndarray, p: dict[str, Any]) -> float:
    return float(energy_density(phi, pi, p).sum())


def vacuum_index(phi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    """Which valley each cell is in: sign of φ (φ⁴), or the nearest 2πk (sine-Gordon)."""
    if p["potential"] == "sine_gordon":
        return np.floor((phi + np.pi) / (2.0 * np.pi)).astype(int)
    return (phi >= 0.0).astype(int)


def wall_density(phi: np.ndarray, p: dict[str, Any]) -> float:
    """Fraction of neighbour links whose two ends sit in different valleys (how much wall there is)."""
    k = vacuum_index(phi, p)
    diff = 0
    for ax in range(phi.ndim):
        diff += int(np.count_nonzero(k != np.roll(k, -1, ax)))
    return diff / (phi.ndim * phi.size)


def lumps(phi: np.ndarray, pi: np.ndarray, p: dict[str, Any], frac: float = 0.5) -> tuple[int, float]:
    """Connected regions (periodic) whose energy density exceeds `frac` × the hill height: (count, mean size).
    Walls and localized lumps (oscillon candidates) both show up; the mean size tells them apart."""
    from scipy import ndimage
    hill = 2.0 * p["lam"] if p["potential"] == "sine_gordon" else 0.25 * p["lam"]
    mask = energy_density(phi, pi, p) > frac * hill
    lab, n = ndimage.label(mask)
    if n == 0:
        return 0, 0.0
    for ax in range(phi.ndim):                      # join labels across the periodic edges
        a = np.take(lab, 0, axis=ax)
        b = np.take(lab, -1, axis=ax)
        for x, y in zip(a[(a > 0) & (b > 0)], b[(a > 0) & (b > 0)]):
            if x != y:
                lab[lab == y] = x
    ids = np.unique(lab[lab > 0])
    sizes = ndimage.sum(np.ones_like(lab), lab, ids)
    return int(len(ids)), float(np.mean(sizes))
