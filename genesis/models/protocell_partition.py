"""The dependence is not written into the law (P18, ladder R4): P17's chemistry without the rule "the material
protects the replicators" (h = 0), plus one piece of generic physics -- everything dissolved is a little more
soluble in the material phase (partitioning), and the reactions follow mass action as before.

    m    = (1 + c)/2                                                                  material share
    X_t  = s D_X [∇²X − aff ∇·(X ∇m)] + reactions            X ∈ {U, V1, V2}, the same aff for all three
    Vi_t = … + s U Vi² − s (F + k) Vi                                                 two replicators (as P14)
    U_t  = … − s U (V1² + V2²) + s F (1 − U)                                          food
    c_t  = M ∇²(c³ − c − κ∇²c − back·aff (U + V1 + V2)/2) + y s k (V1 + V2)(1 − c) − s F (1 + c)

The flux J = −D(∇X − aff X ∇m) comes from the free energy −aff·X·m of a solute X in the material: at rest
X ∝ exp(aff·m), so the inside is e^aff times as concentrated as the outside (like anything shared between oil and
water). The same free energy gives the material its reaction (back = 1): the dissolved species make the phase they
prefer a little more stable. back = 0 switches that off (a control only). Optional aff_U / aff_V (controls only;
absent = aff) partition only the food or only the replicators, to see which of the two carries the dependence; the
back-reaction then uses the same species-specific numbers, so a species that does not partition does not push c either.

Nothing here says "the material helps the replicators": aff treats food and both replicators alike, and the
breakdown rate k is the same everywhere. Whether the replicators come to need their containers (a dependence) --
or are harmed by them (food used up faster inside) -- is measured (tools/protocell_dependence.py), not placed.
Still placed: the Gray–Scott chemistry and the flow; that the breakdown product becomes material with a yield that
saturates, y·(1 − c) = 2y(1 − m) (this is a placed production rule, not mass conservation: where the material is
already full, broken replicators are lost instead of becoming material), and that the material does not mix with
water (Cahn–Hilliard, M, κ); aff (the material can dissolve things); and how harsh the water is (k),
which is scanned rather than chosen.

∇·(X∇m) is computed as ½[∇²(Xm) − m∇²X + X∇²m]; with the 5/7-point ∇² this is exactly the face flux
½Σ(X_i + X_j)(m_j − m_i), so it conserves X, and the same `lap` (local, scaled by dx, or spectral) is used for
every term. t = 0 as P15/P17 (make_initial). Local stencils, explicit Euler, periodic; no FFT in the main line.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from genesis.models.gray_scott_two import labels, laplacian, purity  # noqa: F401  (re-exported for tools)
from genesis.models.protocell import THRESH_V, containers, make_initial  # noqa: F401  (same measure)
from genesis.models.protocell_one import spectral_laplacian  # noqa: F401  (corroboration)

# 2D: the k × aff map (128²), aff = 0.5: dependent (dies without material) for k 0.074–0.086; strongly enhanced
# (open water keeps a trace) for 0.066–0.070. The default k = 0.070 is in the enhanced part
DEFAULTS_2D: dict[str, Any] = {"kappa": 1.0, "M": 1.0, "y": 2.0, "aff": 0.5, "back": 1.0, "s": 10.0, "F": 0.035,
                               "k": 0.070, "Du": 0.16, "Dv": 0.08, "dt": 0.02, "n_seeds": 12, "seed_radius": 3.0,
                               "noise": 0.02, "dx": 1.0}
# 3D (∇⁴: dt ≤ ~0.014). aff and k: the middle of the band where the replicators need their material (the k × aff map
# of tools/protocell_dependence.py, 32³, aff = 0.5: dependent -- dies without material -- for k 0.075–0.095;
# strongly enhanced for 0.0675–0.0725; open water alone fails from 0.075)
DEFAULTS: dict[str, Any] = dict(DEFAULTS_2D, F=0.03, k=0.080, aff=0.5, dt=0.01)


def partition_flux(X, m, lap):
    """∇·(X∇m), conservative (see the module docstring)."""
    return 0.5 * (lap(X * m) - m * lap(X) + X * lap(m))


def step(c, U, V1, V2, p: dict[str, Any], lap=laplacian):
    """One explicit Euler step. p["dx"] != 1: the same law on a finer grid (∇² scaled by 1/dx²); pass
    lap=spectral_laplacian(shape, dx) already scaled to use the FFT Laplacian."""
    dt, s, aff = p["dt"], p["s"], p["aff"]
    if p.get("dx", 1.0) != 1.0 and lap is laplacian:
        h2 = p["dx"] ** 2

        def lap(f):
            return laplacian(f) / h2
    a1, a2 = U * V1 * V1, U * V2 * V2
    V = V1 + V2
    k = p["k"]
    m = 0.5 * (1.0 + c)
    aU, aV = p.get("aff_U", aff), p.get("aff_V", aff)       # optional, controls only: which partition matters
    mu = c * c * c - c - p["kappa"] * lap(c)
    if p["back"] and (aU or aV):                             # the same free energy −(aU·U + aV·V)·m, both ways
        mu = mu - p["back"] * 0.5 * (aff * (U + V) if aU == aV == aff else aU * U + aV * V)
    cn = c + dt * (p["M"] * lap(mu) + p["y"] * s * k * V * (1.0 - c) - s * p["F"] * (1.0 + c))

    def move(X, D, a):
        out = lap(X)
        if a:
            out = out - a * partition_flux(X, m, lap)
        return s * D * out
    Un = U + dt * (move(U, p["Du"], aU) - s * (a1 + a2) + s * p["F"] * (1.0 - U))
    V1n = V1 + dt * (move(V1, p["Dv"], aV) + s * a1 - s * (p["F"] + k) * V1)
    V2n = V2 + dt * (move(V2, p["Dv"], aV) + s * a2 - s * (p["F"] + k) * V2)
    return cn, Un, V1n, V2n
