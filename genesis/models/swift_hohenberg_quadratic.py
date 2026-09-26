"""Triangle white (P9-Q3): Swift–Hohenberg with a quadratic term -- where three waves close a triangle.

    u_t = r u − (1 + ∇²)² u + g u² − u³          (periodic, LOCAL 5-point Laplacian applied twice, explicit Euler)

Near onset (small r > 0) waves of wavelength 2π (|k| = 1) grow out of noise. With g = 0 the pattern is STRIPES:
one wave and its mirror, a relation between two. The quadratic term g u² couples three waves whose wave vectors
close a triangle, k₁ + k₂ + k₃ = 0 (three |k| = 1 vectors at 120°), and the pattern becomes HEXAGONS.

What only three can carry: shifting the pattern by s multiplies each wave by e^{−ik·s}. The phase difference of two
waves then changes by (k₂ − k₁)·s -- it can be removed by moving the origin, it is not a property of the pattern.
The SUM of the three phases of a closed triangle, Φ = φ₁ + φ₂ + φ₃, changes by −(k₁+k₂+k₃)·s = 0: it is a real,
translation-invariant property. Known result (amplitude equations): Φ locks to 0 for g > 0 (spots of high u) and
to π for g < 0 (spots of low u). Measured in `genesis/diagnostics/triads.py` (FFT used only to measure).

Put in: the law (r, g), the lattice spacing dx (≈ 8 cells per wavelength), t = 0 = u ≈ 0 + noise.
Grows: stripes vs hexagons, the triangle's locked phase. Local × parallel × no central solver (no FFT in the law).
"""
from __future__ import annotations

from typing import Any

import numpy as np

DEFAULTS: dict[str, Any] = {"r": 0.05, "g": 0.5, "dx": np.pi / 4, "dt": 0.01, "noise": 0.01}


def laplacian(u: np.ndarray, dx: float) -> np.ndarray:
    out = -2.0 * u.ndim * u
    for ax in range(u.ndim):
        out = out + np.roll(u, 1, ax) + np.roll(u, -1, ax)
    return out / (dx * dx)


def stable_dt(dx: float, ndim: int = 2, safety: float = 0.8) -> float:
    """Explicit Euler: the stiffest lattice mode has (1+∇²)² ≈ (4·ndim/dx² − 1)²."""
    return safety * 2.0 / (4.0 * ndim / dx ** 2 - 1.0) ** 2


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]) -> np.ndarray:
    return p["noise"] * rng.standard_normal(shape)


def rhs(u: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    L = u + laplacian(u, p["dx"])
    return p["r"] * u - (L + laplacian(L, p["dx"])) + p["g"] * u * u - u ** 3


def step(u: np.ndarray, p: dict[str, Any]) -> np.ndarray:
    return u + p["dt"] * rhs(u, p)
