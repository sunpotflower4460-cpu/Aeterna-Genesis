"""Reduced 2D symmetric-traceless nematic Q-tensor relaxation model.

Q is represented by its two independent components

    Q = [[qxx, qxy],
         [qxy,-qxx]]

and follows a simple Landau-de-Gennes relaxational quench generated from an isotropic Q=0 state plus
unbiased symmetric-traceless noise.  Head/tail orientation is therefore encoded in Q rather than by
placing directors.  This is a nematic tensor-field frontier and is explicitly NOT a spacetime metric
or a model of gravity.
"""
from __future__ import annotations

import numpy as np

MODEL_ID = "q2_nematic_landau_de_gennes_relaxation"
DEFAULTS = {
    "K": 0.8,
    "C": 1.0,
    "Gamma": 1.0,
    "dt": 0.04,
    "eps_final": 1.0,  # eps=-A; positive eps favours ordered Q
    "quench_start": 0.0,
    "quench_duration": 8.0,
    "noise_amplitude": 1.0e-2,
}


def make_initial(shape: tuple[int, int], noise_amplitude: float, rng: np.random.Generator) -> np.ndarray:
    """Q=0 plus unbiased noise in the two independent symmetric-traceless components."""
    return (noise_amplitude * rng.standard_normal(tuple(shape) + (2,))).astype(np.float64)


def laplacian(q: np.ndarray) -> np.ndarray:
    out = -4.0 * q
    for ax in (0, 1):
        out = out + np.roll(q, 1, ax) + np.roll(q, -1, ax)
    return out


def eps_of_t(t: float, p: dict) -> float:
    q0, qd, ef = float(p["quench_start"]), float(p["quench_duration"]), float(p["eps_final"])
    if qd <= 0:
        return ef
    frac = min(max((t - q0) / qd, 0.0), 1.0)
    return ef * (2.0 * frac - 1.0)


def step(q: np.ndarray, t: float, p: dict) -> np.ndarray:
    # Tr(Q^2)=2(qxx^2+qxy^2).  Gradient descent of
    # F = integral[A/2 TrQ2 + C/4 (TrQ2)^2 + K/2 |grad Q|^2], with eps=-A.
    r2 = np.sum(q * q, axis=-1, keepdims=True)
    return q + float(p["dt"]) * float(p["Gamma"]) * (
        eps_of_t(t, p) * q - 2.0 * float(p["C"]) * r2 * q + float(p["K"]) * laplacian(q)
    )


def metrics(q: np.ndarray) -> dict[str, float]:
    amp = np.sqrt(np.sum(q * q, axis=-1))
    z = q[..., 0] + 1j * q[..., 1]  # phase is 2*director angle, respecting n == -n
    unit = np.where(amp > 1e-12, z / np.maximum(amp, 1e-12), 0.0j)
    return {
        "mean_tensor_amplitude": float(np.mean(amp)),
        "tensor_amplitude_variance": float(np.var(amp)),
        "global_nematic_order": float(np.abs(np.mean(unit))),
        "rms_tensor_component": float(np.sqrt(np.mean(q * q))),
    }


def tensor_invariants(q: np.ndarray) -> dict[str, float]:
    """Numerical representation audit: Q is symmetric/traceless by construction."""
    # The reconstructed 2x2 tensor has trace qxx + (-qxx) exactly zero and off-diagonals equal.
    return {"max_abs_trace": 0.0, "max_symmetry_error": 0.0}


def run(
    shape: tuple[int, int] = (48, 48), *, steps: int = 260, seed: int = 0,
    params: dict | None = None, snapshots: int = 8,
) -> dict:
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    rng = np.random.default_rng(seed)
    q = make_initial(shape, float(p["noise_amplitude"]), rng)
    traj = [{"step": 0, "time": 0.0, **metrics(q)}]
    every = max(1, steps // max(1, snapshots))
    for i in range(1, steps + 1):
        q = step(q, (i - 1) * float(p["dt"]), p)
        if not np.isfinite(q).all():
            return {"finite": False, "traj": traj, "field": q, "params": p, "nsteps": i}
        if i % every == 0 or i == steps:
            traj.append({"step": i, "time": i * float(p["dt"]), **metrics(q)})
    return {
        "finite": True,
        "traj": traj,
        "field": q,
        "params": p,
        "nsteps": steps,
        "tensor_invariants": tensor_invariants(q),
    }
