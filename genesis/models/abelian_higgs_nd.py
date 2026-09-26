"""Light-and-phase white in any dimension (2D or 3D): lattice Abelian Higgs, temporal gauge, compact links.

The same law as `genesis/models/abelian_higgs.py` (2D), written for d dimensions so that in 3D vortices become
STRINGS (flux tubes) and in 2D the two modules can be cross-checked against each other.

    sites: complex φ, π                links (d directions): angle θ_i, electric field E_i     shapes (d, *grid)
    oriented plaquette  P_ij(x) = θ_i(x) + θ_j(x+î) − θ_i(x+ĵ) − θ_j(x)        (P_ji = −P_ij)

    H = Σ|π|² + (e²/2)ΣE² + Σ_i|e^{-iθ_i(x)}φ(x+î) − φ(x)|² + (λ/4)Σ(|φ|²−v²)² + (1/e²)Σ_{i<j}(1 − cos P_ij)
    φ̇ = π,  π̇ = D²φ − (λ/2)(|φ|²−v²)φ,  θ̇_i = e²E_i,
    Ė_i = −(1/e²) Σ_{j≠i}[sin P_ij(x) − sin P_ij(x−ĵ)] + 2 Im(e^{-iθ_i}φ(x+î)φ*(x))

Gauss's law Σ_i[E_i(x) − E_i(x−î)] = 2 Im(φ*π) is kept exactly by the kick–drift–kick leapfrog; uniform
friction γ (cooling, put in) scales π and E together and keeps it too. Local: nearest neighbours only, no FFT.
Resolution as in the 2D module: e = 0.3, λ = 0.36 (β = 2) so that core and flux tube span cells.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np

DEFAULTS: dict[str, Any] = {"lam": 0.36, "e": 0.3, "v": 1.0, "dt": 0.2, "noise": 0.01, "gamma": 0.0}


def _sh(a: np.ndarray, ax: int, k: int = 1) -> np.ndarray:
    return np.roll(a, -k, ax)


def plaquette(th: np.ndarray, i: int, j: int) -> np.ndarray:
    return th[i] + _sh(th[j], i) - _sh(th[i], j) - th[j]


def planes(d: int) -> list[tuple[int, int]]:
    return list(combinations(range(d), 2))


def link_z(phi: np.ndarray, th: np.ndarray) -> np.ndarray:
    return np.stack([np.exp(-1j * th[i]) * _sh(phi, i) * np.conj(phi) for i in range(phi.ndim)])


def cov_laplacian(phi: np.ndarray, th: np.ndarray) -> np.ndarray:
    out = -2.0 * phi.ndim * phi
    for i in range(phi.ndim):
        out = out + np.exp(-1j * th[i]) * _sh(phi, i) + np.exp(1j * _sh(th[i], i, -1)) * _sh(phi, i, -1)
    return out


def forces(phi, th, p):
    d = phi.ndim
    dpi = cov_laplacian(phi, th) - 0.5 * p["lam"] * (np.abs(phi) ** 2 - p["v"] ** 2) * phi
    inv_e2 = 1.0 / p["e"] ** 2
    cur = 2.0 * np.imag(link_z(phi, th))
    sins = {(i, j): np.sin(plaquette(th, i, j)) for i, j in planes(d)}
    dE = np.empty_like(th)
    for i in range(d):
        acc = np.zeros(phi.shape)
        for j in range(d):
            if j == i:
                continue
            s = sins[(i, j)] if i < j else -sins[(j, i)]      # sin P_ij, with P_ji = −P_ij
            acc = acc + s - _sh(s, j, -1)
        dE[i] = -inv_e2 * acc + cur[i]
    return dpi, dE


def make_initial(shape, rng: np.random.Generator, p):
    d = len(shape)
    phi = p["noise"] * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return phi, np.zeros(shape, complex), np.zeros((d,) + tuple(shape)), np.zeros((d,) + tuple(shape))


def step(phi, pi, th, E, p):
    dt, e2 = p["dt"], p["e"] ** 2
    dpi, dE = forces(phi, th, p)
    pi = pi + 0.5 * dt * dpi
    E = E + 0.5 * dt * dE
    phi = phi + dt * pi
    th = th + dt * e2 * E
    dpi, dE = forces(phi, th, p)
    pi = pi + 0.5 * dt * dpi
    E = E + 0.5 * dt * dE
    if p.get("gamma", 0.0) > 0.0:
        f = np.exp(-p["gamma"] * dt)
        pi, E = pi * f, E * f
    return phi, pi, th, E


# ---------------------------------------------------------------------------------------- measures
def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def energy_density(phi, pi, th, E, p) -> np.ndarray:
    d = phi.ndim
    grad = sum(np.abs(np.exp(-1j * th[i]) * _sh(phi, i) - phi) ** 2 for i in range(d))
    mag = sum(1.0 - np.cos(plaquette(th, i, j)) for i, j in planes(d))
    return (np.abs(pi) ** 2 + 0.5 * p["e"] ** 2 * (E ** 2).sum(0) + grad
            + 0.25 * p["lam"] * (np.abs(phi) ** 2 - p["v"] ** 2) ** 2 + mag / p["e"] ** 2)


def energy(phi, pi, th, E, p) -> float:
    return float(energy_density(phi, pi, th, E, p).sum())


def gauss_residual(phi, pi, E) -> np.ndarray:
    div = sum(E[i] - _sh(E[i], i, -1) for i in range(phi.ndim))
    return div - 2.0 * np.imag(np.conj(phi) * pi)


def winding(phi, th) -> dict[tuple[int, int], np.ndarray]:
    """Gauge-invariant integer winding through every plaquette, per plane (i, j): where a vortex line pierces."""
    chi = np.angle(link_z(phi, th))
    out = {}
    for i, j in planes(phi.ndim):
        loop = chi[i] + _sh(chi[j], i) - _sh(chi[i], j) - chi[j]
        out[(i, j)] = np.rint((loop + wrap(plaquette(th, i, j))) / (2 * np.pi)).astype(int)
    return out


def string_length(phi, th) -> int:
    """Number of pierced plaquettes = total length of vortex lines, in lattice units (2D: number of vortices)."""
    return int(sum(int(np.count_nonzero(w)) for w in winding(phi, th).values()))


def flux_magnitude(th) -> np.ndarray:
    """|B| per site from the wrapped plaquette angles of all planes (display / measure)."""
    return np.sqrt(sum(wrap(plaquette(th, i, j)) ** 2 for i, j in planes(th.shape[0])))


def slice_piercings(phi, th, axis: int) -> np.ndarray:
    """For every slice perpendicular to `axis`: how many strings pierce it, as rows (# +1, # −1).
    A string that runs once around the periodic box along `axis` pierces every such slice."""
    i, j = [a for a in range(phi.ndim) if a != axis]
    w = np.moveaxis(winding(phi, th)[(i, j)], axis, 0).reshape(phi.shape[axis], -1)
    return np.stack([(w > 0).sum(1), (w < 0).sum(1)], axis=1)


def wrapped_axes(phi, th) -> list[int]:
    """Axes along which strings run all the way around the box (every perpendicular slice is pierced).
    Such strings cannot shrink away on their own; they can only meet a partner of the opposite sign."""
    return [a for a in range(phi.ndim) if phi.ndim > 2 and bool((slice_piercings(phi, th, a).sum(1) > 0).all())]
