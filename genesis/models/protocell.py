"""Replicators that build their own container (P15, ladder R4): does a closed boundary grow, hold the inside apart
from the outside, and divide together with what it holds?

    c_t  = ∇²(c³ − c − κ∇²c) + α (V1 + V2)(1 − c) − β (1 + c)                      container material (conserved
                                                                                     motion + made / broken down)
    U_t  = s Du ∇²U − s g(c) U (V1² + V2²) + s F (1 − U)                             food
    Vi_t = s Dv ∇²Vi + s g(c) U Vi² − s (F + k) Vi                                  two replicators (as P14)
    g(c) = g0 + (1 − g0)·clip((1 + c)/2, 0, 1)                                       copying works better inside

c separates like oil and water (Cahn–Hilliard; c ≈ +1 inside a container, −1 outside). The replicators MAKE the
container material where they are (α), the material breaks down everywhere (β), and copying works better inside a
container (g0 < 1 outside). So neither lasts without the other: that mutual dependence is put in as a LAW; whether
closed containers actually grow from nothing, hold one replicator spot each, keep the inside apart from the
outside, and divide together with their spot (and pass the kind on) is measured, not placed.
s rescales the Gray–Scott clock (s = 1 is P14's chemistry) so that both parts move on similar times.

Put in: the law (κ, α, β, g0, s, F, k, diffusions), t = 0: c = −1 + tiny noise (no container anywhere), U = 1 and
seed blobs of V1/V2 in random mixtures (as P14). Local stencils, explicit Euler, periodic; no FFT.
The boundary is a phase interface, not a lipid bilayer; the containers are not cells.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from genesis.models.gray_scott_two import labels, laplacian, purity  # noqa: F401  (re-exported for tools)

DEFAULTS_2D: dict[str, Any] = {"kappa": 1.0, "alpha": 1.0, "beta": 0.1, "g0": 0.9, "s": 10.0, "F": 0.035,
                               "k": 0.062, "Du": 0.16, "Dv": 0.08, "dt": 0.02, "n_seeds": 12, "seed_radius": 3.0,
                               "noise": 0.02}
DEFAULTS: dict[str, Any] = dict(DEFAULTS_2D, F=0.03, k=0.065, dt=0.01)     # 3D (explicit stability of ∇⁴: dt ≤ ~0.014)
THRESH_V = 0.2


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]):
    c = -1.0 + p["noise"] * rng.standard_normal(shape)
    U = np.ones(shape)
    V1 = np.zeros(shape)
    V2 = np.zeros(shape)
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing="ij")
    for _ in range(int(p["n_seeds"])):
        cc = [int(rng.integers(0, n)) for n in shape]
        q = float(rng.random())
        d2 = sum(np.minimum(np.abs(g - ci), n - np.abs(g - ci)) ** 2 for g, ci, n in zip(grids, cc, shape))
        b = np.exp(-d2 / (2.0 * p["seed_radius"] ** 2))
        U -= 0.5 * b
        V1 += 0.5 * q * b
        V2 += 0.5 * (1.0 - q) * b
    return c, U, V1, V2


def catalysis(c: np.ndarray, g0: float) -> np.ndarray:
    return g0 + (1.0 - g0) * np.clip(0.5 * (1.0 + c), 0.0, 1.0)


def step(c, U, V1, V2, p: dict[str, Any]):
    dt, s = p["dt"], p["s"]
    g = catalysis(c, p["g0"])
    a1, a2 = g * U * V1 * V1, g * U * V2 * V2
    V = V1 + V2
    mu = c * c * c - c - p["kappa"] * laplacian(c)
    cn = c + dt * (laplacian(mu) + p["alpha"] * V * (1.0 - c) - p["beta"] * (1.0 + c))
    Un = U + dt * (s * p["Du"] * laplacian(U) - s * (a1 + a2) + s * p["F"] * (1.0 - U))
    V1n = V1 + dt * (s * p["Dv"] * laplacian(V1) + s * a1 - s * (p["F"] + p["k"]) * V1)
    V2n = V2 + dt * (s * p["Dv"] * laplacian(V2) + s * a2 - s * (p["F"] + p["k"]) * V2)
    return cn, Un, V1n, V2n


def containers(c, V1, V2):
    """(labels, [{id, size, v_in, kind1, spots}]) of containers (c > 0, periodic); spots = replicator spots
    (V > THRESH_V) whose voxels lie mostly in this container."""
    lab = labels(c + 1.0, 1.0)                      # c > 0
    V = V1 + V2
    slab = labels(V, THRESH_V)
    out = []
    ids, inv = np.unique(lab.ravel(), return_inverse=True)
    n = np.bincount(inv)
    sv = np.bincount(inv, V.ravel())
    s1 = np.bincount(inv, V1.ravel())
    for j, i in enumerate(ids):
        if i == 0:
            continue
        inside = slab[lab == i]
        spots = int(len(set(np.unique(inside)) - {0}))
        out.append({"id": int(i), "size": int(n[j]), "v_in": float(sv[j] / n[j]),
                    "kind1": float(s1[j] / max(sv[j], 1e-12)), "spots": spots})
    return lab, out
