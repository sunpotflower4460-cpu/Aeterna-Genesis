"""Two replicators on one food (P14, ladder R3): do dividing spots pass their KIND on to their daughters?

    U_t  = Du ∇²U − U V1² − U V2² + F (1 − U)
    V1_t = Dv ∇²V1 + U V1² − (F + k1) V1 − μ (V1 − V2)
    V2_t = Dv ∇²V2 + U V2² − (F + k2) V2 − μ (V2 − V1)            (periodic, local stencil, explicit Euler)

Gray–Scott with TWO versions of the same self-copying chemistry (V1, V2) eating the same food U. Each copies
itself in proportion to its own amount squared, so inside a spot the one that is ahead grows faster and takes
the spot over: a mixed spot becomes pure (a two-state "kind" that the law makes, nobody paints it). When a pure
spot divides, both halves carry the same kind -- inheritance, if it holds, is measured, not imposed.
μ (default 0) turns V1 into V2 and back ("mutation"); k1 ≠ k2 makes one kind die a little faster (selection).

Put in: the law (Du, Dv, F, k1, k2, μ), that there are two versions of the chemistry, and t = 0: U = 1, a few
seed blobs, each a RANDOM mixture of V1 and V2 (fraction q ~ uniform(0, 1)). Kinds are not assigned to seeds.
Local × parallel × no central solver. Spots are reaction–diffusion patterns, not cells (no boundary, R4).
"""
from __future__ import annotations

from typing import Any

import numpy as np

# 3D: blobs keep dividing at F = 0.03, k = 0.065 (at k = 0.062 they mostly merge into a few big blobs);
# 2D: the classic mitosis regime F = 0.035, k = 0.062
DEFAULTS: dict[str, Any] = {"Du": 0.16, "Dv": 0.08, "F": 0.03, "k1": 0.065, "k2": 0.065, "mu": 0.0, "dt": 0.9,
                            "n_seeds": 12, "seed_radius": 3.0}
DEFAULTS_2D: dict[str, Any] = dict(DEFAULTS, F=0.035, k1=0.062, k2=0.062, dt=1.0)
THRESH = 0.2                        # V1 + V2 above this = inside a spot


def laplacian(f: np.ndarray) -> np.ndarray:
    out = -2.0 * f.ndim * f
    for ax in range(f.ndim):
        out = out + np.roll(f, 1, ax) + np.roll(f, -1, ax)
    return out


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]):
    """U = 1, V = 0, plus `n_seeds` Gaussian blobs at random places; each blob is a random mixture of V1 and V2."""
    U = np.ones(shape)
    V1 = np.zeros(shape)
    V2 = np.zeros(shape)
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing="ij")
    mix = []
    for _ in range(int(p["n_seeds"])):
        c = [int(rng.integers(0, n)) for n in shape]
        q = float(rng.random())
        d2 = sum(np.minimum(np.abs(g - ci), n - np.abs(g - ci)) ** 2 for g, ci, n in zip(grids, c, shape))
        b = np.exp(-d2 / (2.0 * p["seed_radius"] ** 2))
        U -= 0.5 * b
        V1 += 0.5 * q * b
        V2 += 0.5 * (1.0 - q) * b
        mix.append(q)
    return U, V1, V2, mix


def step(U, V1, V2, p: dict[str, Any]):
    dt = p["dt"]
    a1, a2 = U * V1 * V1, U * V2 * V2
    ex = p["mu"] * (V1 - V2)
    Un = U + dt * (p["Du"] * laplacian(U) - (a1 + a2) + p["F"] * (1.0 - U))
    V1n = V1 + dt * (p["Dv"] * laplacian(V1) + a1 - (p["F"] + p["k1"]) * V1 - ex)
    V2n = V2 + dt * (p["Dv"] * laplacian(V2) + a2 - (p["F"] + p["k2"]) * V2 + ex)
    return Un, V1n, V2n


def labels(V: np.ndarray, thresh: float = THRESH) -> np.ndarray:
    """Connected spots (V > thresh), merged across the periodic boundary; 0 = background."""
    from scipy import ndimage
    lab, _ = ndimage.label(V > thresh)
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for ax in range(V.ndim):
        a, b = np.take(lab, 0, axis=ax), np.take(lab, -1, axis=ax)
        m = (a > 0) & (b > 0)
        for x, y in set(zip(a[m].ravel().tolist(), b[m].ravel().tolist())):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[max(rx, ry)] = min(rx, ry)
    if parent:
        mp = np.arange(lab.max() + 1)
        for x in range(1, lab.max() + 1):
            mp[x] = find(x)
        lab = mp[lab]
    return lab


def spots(V1: np.ndarray, V2: np.ndarray, thresh: float = THRESH):
    """(labels, [{id, size, kind1}]) -- kind1 = V1 / (V1 + V2) summed over the spot (1 = pure V1, 0 = pure V2)."""
    V = V1 + V2
    lab = labels(V, thresh)
    ids, inv = np.unique(lab.ravel(), return_inverse=True)
    s1 = np.bincount(inv, V1.ravel())
    s = np.bincount(inv, V.ravel())
    n = np.bincount(inv)
    out = [{"id": int(i), "size": int(n[j]), "kind1": float(s1[j] / max(s[j], 1e-12))}
           for j, i in enumerate(ids) if i != 0]
    return lab, out


def purity(kind1: float) -> float:
    """0 = half and half, 1 = only one kind."""
    return abs(kind1 - 0.5) * 2.0
