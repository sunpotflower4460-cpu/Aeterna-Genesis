"""Light-and-phase white: 2D lattice Abelian Higgs model (a U(1) gauge field = 2D light, and a complex field).

Hamiltonian form, temporal gauge (A₀ = 0), compact links. Lattice spacing 1, periodic box.

    sites  x : complex φ(x) and its momentum π(x)
    links  i : angle θ_i(x) (U_i = e^{iθ_i}, link from x to x+î) and electric field E_i(x)

    H = Σ|π|² + (e²/2) ΣE² + Σ_i |e^{-iθ_i(x)} φ(x+î) − φ(x)|² + (λ/4) Σ(|φ|² − v²)² + (1/e²) Σ_plaq (1 − cos F)
        F(x) = θ_x(x) + θ_y(x+x̂) − θ_x(x+ŷ) − θ_y(x)          (magnetic flux through the plaquette at x)

    φ̇ = π                        π̇ = D²φ − (λ/2)(|φ|² − v²) φ          (D² = covariant Laplacian)
    θ̇_i = e² E_i                 Ė_i = −(1/e²) ∂_θ Σ(1 − cos F) + 2 Im(e^{-iθ_i} φ(x+î) φ*(x))   (current)

Gauge symmetry φ → e^{iα}φ, θ_i(x) → θ_i(x) + α(x+î) − α(x) leaves H unchanged; its generator is Gauss's law

    Σ_i [E_i(x) − E_i(x−î)] = ρ(x),  ρ = 2 Im(φ* π)

which the kick–drift–kick leapfrog below keeps EXACTLY (to round-off) once it holds at t = 0. The photon moves at
speed 1 (θ̈ = −curl-curl θ + …); in the Higgs phase it gets a mass m_A² = 2e²v², the Higgs field m_H² = λv².
β = m_H²/m_A² = λ/(2e²): β < 1 type I, β > 1 type II (β = 1 is the critical, BPS point).

Put in: the law (λ, e, v); t = 0 = φ on the hill (φ ≈ 0) with tiny noise, θ = E = π = 0 (which satisfies Gauss);
optional UNIFORM friction γ (cooling of the whole box; it scales π and E by the same factor, so Gauss stays exact).
Computed locally (nearest neighbours only, no FFT, no central solver).
"""
from __future__ import annotations

from typing import Any

import numpy as np

# Resolution: the Higgs core ξ = 1/(√λ v) and the flux-tube width 1/(√2 e v) must span several cells. With
# e = v = 1 the flux of a vortex squeezes into one plaquette, where the compact link cannot tell 2π from 0 and
# the vortex unwinds (a lattice artefact, measured). Defaults: e = 0.3, λ = 0.36 → β = 2 (type II),
# ξ ≈ 1.7 cells, flux-tube width ≈ 2.4 cells; dt = 0.2 is well inside the CFL bound (1/√2).
DEFAULTS: dict[str, Any] = {
    "lam": 0.36,      # Higgs self-coupling λ
    "e": 0.3,         # gauge coupling e
    "v": 1.0,         # vacuum value |φ| = v
    "dt": 0.2,
    "noise": 0.01,    # t = 0 noise amplitude of φ (put in)
    "gamma": 0.0,     # uniform friction on π and E (cooling; put in)
}

X, Y = 0, 1


def _sh(a: np.ndarray, ax: int, k: int = 1) -> np.ndarray:
    """a(x + k·axis) on the periodic lattice."""
    return np.roll(a, -k, ax)


def plaquette(th: np.ndarray) -> np.ndarray:
    """F(x) = θ_x(x) + θ_y(x+x̂) − θ_x(x+ŷ) − θ_y(x). th has shape (2, N, M)."""
    return th[X] + _sh(th[Y], X) - _sh(th[X], Y) - th[Y]


def link_z(phi: np.ndarray, th: np.ndarray) -> np.ndarray:
    """z_i(x) = e^{-iθ_i(x)} φ(x+î) φ*(x) (gauge invariant). Shape (2, N, M)."""
    return np.stack([np.exp(-1j * th[i]) * _sh(phi, i) * np.conj(phi) for i in (X, Y)])


def cov_laplacian(phi: np.ndarray, th: np.ndarray) -> np.ndarray:
    out = -4.0 * phi
    for i in (X, Y):
        out = out + np.exp(-1j * th[i]) * _sh(phi, i) + np.exp(1j * _sh(th[i], i, -1)) * _sh(phi, i, -1)
    return out


def forces(phi: np.ndarray, th: np.ndarray, p: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """(π̇, Ė) at fixed (φ, θ)."""
    dpi = cov_laplacian(phi, th) - 0.5 * p["lam"] * (np.abs(phi) ** 2 - p["v"] ** 2) * phi
    sF = np.sin(plaquette(th))
    inv_e2 = 1.0 / p["e"] ** 2
    cur = 2.0 * np.imag(link_z(phi, th))
    dEx = -inv_e2 * (sF - _sh(sF, Y, -1)) + cur[X]
    dEy = -inv_e2 * (-sF + _sh(sF, X, -1)) + cur[Y]
    return dpi, np.stack([dEx, dEy])


def make_initial(shape: tuple[int, int], rng: np.random.Generator, p: dict[str, Any]):
    """On the hill with tiny complex noise, no gauge field, at rest: Gauss's law holds (ρ = 0, E = 0)."""
    phi = p["noise"] * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    return phi, np.zeros(shape, complex), np.zeros((2,) + tuple(shape)), np.zeros((2,) + tuple(shape))


def step(phi, pi, th, E, p: dict[str, Any]):
    """Kick–drift–kick (velocity Verlet). Uniform friction γ multiplies π and E by exp(−γ dt) (Gauss stays exact)."""
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
def energy_density(phi, pi, th, E, p) -> np.ndarray:
    grad = sum(np.abs(np.exp(-1j * th[i]) * _sh(phi, i) - phi) ** 2 for i in (X, Y))
    return (np.abs(pi) ** 2 + 0.5 * p["e"] ** 2 * (E[X] ** 2 + E[Y] ** 2) + grad
            + 0.25 * p["lam"] * (np.abs(phi) ** 2 - p["v"] ** 2) ** 2 + (1.0 - np.cos(plaquette(th))) / p["e"] ** 2)


def energy(phi, pi, th, E, p) -> float:
    return float(energy_density(phi, pi, th, E, p).sum())


def gauss_residual(phi, pi, E) -> np.ndarray:
    div = (E[X] - _sh(E[X], X, -1)) + (E[Y] - _sh(E[Y], Y, -1))
    return div - 2.0 * np.imag(np.conj(phi) * pi)


def wrap(a: np.ndarray) -> np.ndarray:
    return (a + np.pi) % (2 * np.pi) - np.pi


def winding(phi, th) -> np.ndarray:
    """Gauge-invariant integer vortex number per plaquette: (Σ_loop χ + wrap F) / 2π, χ_i = arg z_i."""
    chi = np.angle(link_z(phi, th))
    loop = chi[X] + _sh(chi[Y], X) - _sh(chi[X], Y) - chi[Y]
    return np.rint((loop + wrap(plaquette(th))) / (2 * np.pi)).astype(int)


def flux(th) -> np.ndarray:
    """Magnetic flux per plaquette, wrap(F) in (−π, π]."""
    return wrap(plaquette(th))


def flux_around(th, n: np.ndarray, radius: float) -> list[tuple[int, float, tuple[int, int]]]:
    """For each vortex plaquette (n ≠ 0): (n, total flux within `radius` cells, position). Periodic distances."""
    F = flux(th)
    N, M = F.shape
    ys, xs = np.nonzero(n)
    yy, xx = np.mgrid[:N, :M]
    out = []
    for y, x in zip(ys, xs):
        dy = np.minimum(abs(yy - y), N - abs(yy - y))
        dx = np.minimum(abs(xx - x), M - abs(xx - x))
        out.append((int(n[y, x]), float(F[(dy ** 2 + dx ** 2) <= radius ** 2].sum()), (int(y), int(x))))
    return out
