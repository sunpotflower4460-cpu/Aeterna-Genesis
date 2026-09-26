"""Excitable white (P13): the Barkley model -- a medium that fires, rests and can fire again, like heart or nerve
tissue. Do spiral waves (2D) and scroll waves / scroll rings (3D, vortex lines and tori of the wave) grow?

    u_t = ∇²u + u(1 − u)(u − (v + b)/a)/ε,      v_t = u − v            (periodic, local stencil, explicit Euler)

u is the fast "excitation" (a nerve cell firing), v the slow "recovery". A kick above the threshold (v + b)/a sends
u up to 1 (it fires), then v rises and brings u back to 0 (it rests), and after a while it can fire again. Waves of
firing travel at a fixed speed and annihilate when they meet; a broken wave end curls into a rotating SPIRAL
(2D), in 3D into a SCROLL wave whose axis (the filament) is a vortex line, and a closed filament is a scroll ring
-- a torus (Winfree). The phase angle of (u − u*, v − v*) winds by 2π around a filament.
Put in: the law (a, b, ε; grid spacing dx), t = 0 (see `make_initial`). Local × parallel × no central solver.
"""
from __future__ import annotations

from typing import Any

import numpy as np

DEFAULTS: dict[str, Any] = {"a": 0.75, "b": 0.06, "eps": 0.02, "dx": 0.8, "dt": 0.015, "noise": 1.0, "corr": 6.0}
U_STAR, V_STAR = 0.5, 0.35          # the point in the (u, v) plane that the phase angle turns around


def laplacian(f: np.ndarray, dx: float) -> np.ndarray:
    out = -2.0 * f.ndim * f
    for ax in range(f.ndim):
        out = out + np.roll(f, 1, ax) + np.roll(f, -1, ax)
    return out / (dx * dx)


def step(u: np.ndarray, v: np.ndarray, p: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    dt = p["dt"]
    th = (v + p["b"]) / p["a"]
    du = laplacian(u, p["dx"]) + u * (1.0 - u) * (u - th) / p["eps"]
    return u + dt * du, v + dt * (u - v)


def smooth_noise(shape, rng: np.random.Generator, corr: float) -> np.ndarray:
    """White noise smoothed by repeated local averaging (≈ Gaussian blur of width `corr` cells), scaled to [0, 1]."""
    f = rng.standard_normal(shape)
    for _ in range(int(round(corr * corr))):
        f = sum(np.roll(f, s, ax) for ax in range(f.ndim) for s in (1, -1)) / (2 * f.ndim) * 0.5 + 0.5 * f
    f = (f - f.min()) / max(f.max() - f.min(), 1e-12)
    return f


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """t = 0: patchy random excitation -- u and v are independent smooth random fields (correlation `corr` cells)
    times `noise`. No wave, spiral or ring is put in; `noise` = 0 is the resting medium (nothing ever happens)."""
    return p["noise"] * smooth_noise(shape, rng, p["corr"]), p["noise"] * 0.5 * smooth_noise(shape, rng, p["corr"])


def phase_field(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """(u − u*) + i(v − v*): its angle winds by ±2π around a spiral tip / scroll filament."""
    return (u - U_STAR) + 1j * (v - V_STAR)
