"""One chemistry for the replicators and their container (P17, ladder R4): the container material is what the
replicators turn into when they break down -- not a second, separately made substance.

    k'   = k (1 − h·m),  m = clip((1 + c)/2, 0, 1)                                 breakdown needs water
    Vi_t = s Dv ∇²Vi + s g(c) U Vi² − s (F + k') Vi                                 two replicators (as P14/P15)
    U_t  = s Du ∇²U − s g(c) U (V1² + V2²) + s F (1 − U)                             food
    c_t  = M ∇²(c³ − c − κ∇²c) + y s k' (V1 + V2)(1 − c) − s F (1 + c)             material (m = its share)

Compared with P15 (genesis/models/protocell.py), placed pieces are replaced by the chemistry that is already there:
* the material is not made by a separate rule (α): the replicators' own breakdown V → y·W (the Gray–Scott k-term)
  becomes material; y is how many material units one broken replicator gives (a stoichiometric number; the factor
  (1 − c) = 2(1 − m) only stops m from passing 1);
* the material is not broken down by a separate rule (β): it is washed out at the same rate F as every species of
  the flow reactor;
* copying does not work better inside (g0 = 1, so g ≡ 1). Instead the breakdown is a hydrolysis: it needs water, so
  inside the material (share m) it is slower by the factor (1 − h·m). h = 0 is the passive case in which the
  replicators never feel the material.
What is still placed: the Gray–Scott chemistry and the flow (as P14; k is set just above where replicators stop
multiplying in open water), that the breakdown product does not mix with water (Cahn–Hilliard, M, κ), y, and h.
Whether closed containers grow, hold one spot each, keep the inside apart from the outside, divide with their
content and pass the kind on -- and whether the replicators come to need them -- is measured, not placed.

t = 0 as P15: c = −1 + tiny noise (no material anywhere), U = 1, seed blobs of V1/V2 in random mixtures.
Local stencils, explicit Euler, periodic; no FFT. The boundary is a phase interface, not a lipid bilayer.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from genesis.models.gray_scott_two import labels, laplacian, purity  # noqa: F401  (re-exported for tools)
from genesis.models.protocell import THRESH_V, catalysis, containers, make_initial  # noqa: F401  (same measure)

DEFAULTS_2D: dict[str, Any] = {"kappa": 1.0, "M": 1.0, "y": 2.0, "hyd": 0.1, "g0": 1.0, "s": 10.0, "F": 0.035,
                               "k": 0.066, "Du": 0.16, "Dv": 0.08, "dt": 0.02, "n_seeds": 12, "seed_radius": 3.0, "noise": 0.02}
DEFAULTS: dict[str, Any] = dict(DEFAULTS_2D, F=0.03, k=0.070, dt=0.01)   # 3D (∇⁴: dt ≤ ~0.014)


def spectral_laplacian(shape):
    """A second, independent discretisation of ∇² (FFT, periodic) -- used only to corroborate the local stencil
    (genesis/diagnostics/corroborate_protocell.py); the main line is the local stencil."""
    k2 = sum(np.meshgrid(*[(2.0 * np.pi * np.fft.fftfreq(n)) ** 2 for n in shape], indexing="ij"))

    def lap(f):
        return np.real(np.fft.ifftn(-k2 * np.fft.fftn(f)))
    return lap


def step(c, U, V1, V2, p: dict[str, Any], lap=laplacian):
    dt, s = p["dt"], p["s"]
    g = catalysis(c, p["g0"])
    a1, a2 = g * U * V1 * V1, g * U * V2 * V2
    V = V1 + V2
    kv = p["k"] * (1.0 - p["hyd"] * np.clip(0.5 * (1.0 + c), 0.0, 1.0))    # breakdown needs water (h = hyd)
    mu = c * c * c - c - p["kappa"] * lap(c)
    cn = c + dt * (p["M"] * lap(mu) + p["y"] * s * kv * V * (1.0 - c) - s * p["F"] * (1.0 + c))
    Un = U + dt * (s * p["Du"] * lap(U) - s * (a1 + a2) + s * p["F"] * (1.0 - U))
    V1n = V1 + dt * (s * p["Dv"] * lap(V1) + s * a1 - s * (p["F"] + kv) * V1)
    V2n = V2 + dt * (s * p["Dv"] * lap(V2) + s * a2 - s * (p["F"] + kv) * V2)
    return cn, Un, V1n, V2n
