"""Damped Gross–Pitaevskii (superfluid) with a LOCAL Laplacian, any dimension (P11: does a torus grow by itself?).

    ψ_t = −(i + γ) [ −½∇²ψ + g(|ψ|² − μ)ψ ]              (periodic, nearest-neighbour Laplacian, RK4)

The same law as the damped GPE of e052–e058 (2D, spectral), written with a nearest-neighbour stencil so that it
runs in 3D and 2D alike (local × parallel × no central solver; the FFT is not used).
* γ = 0: the conservative GPE (a superfluid: vortices are quantized, vortex rings move by themselves).
* γ > 0: a small coupling to a bath at chemical potential μ (put in). Starting from ψ ≈ 0 the modes with
  ½k² < μ grow at rate γ(μ − ½k²): a quench. The bulk density settles at n = μ/g, healing length ξ = 1/√(gn).
Put in: the law (g, μ, γ), t = 0 = ψ ≈ 0 + tiny complex noise. No vortex, ring or shape is put in.
"""
from __future__ import annotations

from typing import Any

import numpy as np

DEFAULTS: dict[str, Any] = {"g": 1.0, "mu": 1.0, "gamma": 0.03, "dt": 0.2, "noise": 0.01}


def laplacian(psi: np.ndarray) -> np.ndarray:
    out = -2.0 * psi.ndim * psi
    for ax in range(psi.ndim):
        out = out + np.roll(psi, 1, ax) + np.roll(psi, -1, ax)
    return out


def rhs(psi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    H = -0.5 * laplacian(psi) + p["g"] * (np.abs(psi) ** 2 - p["mu"]) * psi
    return -(1j + p["gamma"]) * H


def step(psi: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    dt = p["dt"]
    k1 = rhs(psi, p)
    k2 = rhs(psi + 0.5 * dt * k1, p)
    k3 = rhs(psi + 0.5 * dt * k2, p)
    k4 = rhs(psi + dt * k3, p)
    return psi + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]) -> np.ndarray:
    return p["noise"] * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))


def energy(psi: np.ndarray, p: dict[str, Any]) -> float:
    """Σ ½|∇ψ|² + (g/2)(|ψ|² − μ)²  (forward differences) -- conserved when γ = 0 (up to the RK4 error)."""
    grad = sum(np.abs(np.roll(psi, -1, ax) - psi) ** 2 for ax in range(psi.ndim))
    return float((0.5 * grad + 0.5 * p["g"] * (np.abs(psi) ** 2 - p["mu"]) ** 2).sum())


def velocity(psi: np.ndarray) -> np.ndarray:
    """Superfluid velocity v = Im(ψ* ∇ψ)/|ψ|² (central differences), shape (ndim, *grid)."""
    a2 = np.maximum(np.abs(psi) ** 2, 1e-12)
    return np.stack([np.imag(np.conj(psi) * (np.roll(psi, -1, ax) - np.roll(psi, 1, ax)) / 2.0) / a2
                     for ax in range(psi.ndim)])
