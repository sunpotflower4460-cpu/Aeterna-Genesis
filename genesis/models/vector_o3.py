"""Minimal O(3) vector order-parameter quench for Multi-World Genesis.

This is a Frontier/Validation-style world, not an official Room.  The field phi(x,t) has three REAL
internal components and evolves by the rotationally symmetric relaxational law

    d phi / dt = eps(t) phi - |phi|^2 phi + D lap(phi)

The initial state is an isotropic near-zero vector field plus unbiased noise.  No direction, defect,
object, motion or target texture is seeded.  This is the vector analogue of the g001 TDGL reference,
useful for asking which observations depend on field type rather than on a complex scalar.
"""
from __future__ import annotations

import numpy as np

MODEL_ID = "o3_vector_tdgl_quench"
DEFAULTS = {
    "D": 1.0,
    "dt": 0.05,
    "eps_final": 1.0,
    "quench_start": 0.0,
    "quench_duration": 8.0,
    "noise_amplitude": 1.0e-2,
}


def make_initial(shape: tuple[int, ...], noise_amplitude: float, rng: np.random.Generator) -> np.ndarray:
    """Isotropic near-zero O(3) field; last axis stores the three internal components."""
    return (noise_amplitude * rng.standard_normal(tuple(shape) + (3,))).astype(np.float64)


def laplacian(phi: np.ndarray) -> np.ndarray:
    """Unit-spacing periodic Laplacian over spatial axes only (never across component axis)."""
    ndim = phi.ndim - 1
    out = -2.0 * ndim * phi
    for ax in range(ndim):
        out = out + np.roll(phi, 1, ax) + np.roll(phi, -1, ax)
    return out


def eps_of_t(t: float, p: dict) -> float:
    q0, qd, ef = float(p["quench_start"]), float(p["quench_duration"]), float(p["eps_final"])
    if qd <= 0:
        return ef
    frac = min(max((t - q0) / qd, 0.0), 1.0)
    return ef * (2.0 * frac - 1.0)


def step(phi: np.ndarray, t: float, p: dict) -> np.ndarray:
    mag2 = np.sum(phi * phi, axis=-1, keepdims=True)
    return phi + float(p["dt"]) * (
        eps_of_t(t, p) * phi - mag2 * phi + float(p["D"]) * laplacian(phi)
    )


def metrics(phi: np.ndarray) -> dict[str, float]:
    mag = np.linalg.norm(phi, axis=-1)
    mean_vec = np.mean(phi.reshape(-1, 3), axis=0)
    return {
        "mean_magnitude": float(np.mean(mag)),
        "magnitude_variance": float(np.var(mag)),
        "global_vector_order": float(np.linalg.norm(mean_vec)),
        "rms_field": float(np.sqrt(np.mean(phi * phi))),
    }


def run(
    shape: tuple[int, ...] = (48, 48), *, steps: int = 240, seed: int = 0,
    params: dict | None = None, snapshots: int = 8,
) -> dict:
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    phi = make_initial(shape, float(p["noise_amplitude"]), rng)
    traj = [{"step": 0, "time": 0.0, **metrics(phi)}]
    every = max(1, steps // max(1, snapshots))
    for i in range(1, steps + 1):
        phi = step(phi, (i - 1) * float(p["dt"]), p)
        if not np.isfinite(phi).all():
            return {"finite": False, "traj": traj, "field": phi, "params": p, "nsteps": i}
        if i % every == 0 or i == steps:
            traj.append({"step": i, "time": i * float(p["dt"]), **metrics(phi)})
    return {"finite": True, "traj": traj, "field": phi, "params": p, "nsteps": steps}
