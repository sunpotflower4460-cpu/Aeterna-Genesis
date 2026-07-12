#!/usr/bin/env python3
"""Gray-Scott reaction-diffusion (two-species) -- a law class that self-replicates from noise seeds.

    U_t = Du lap(U) - U V^2 + F (1 - U)
    V_t = Dv lap(V) + U V^2 - (F + k) V

In the "mitosis" regime (F~0.035, k~0.062) a few seed spots of V GROW and DIVIDE, so the number of
localized spots climbs over time (self-replication = growth/division). The starting condition is
U=1 everywhere, V=0, plus a FEW small noise seeds of V -- NOT the replicated pattern (第8監査): the spot
COUNT is measured, never seeded. Periodic, explicit (dt=1.0 is the standard stable GS step; dx=1).

「同じ数学 ≠ 同じもの」: these are reaction-diffusion spots, NOT cells/life. The self-replication is a
measured field phenomenon (Pearson 1993, Science), reported as such -- no life language.
"""

import numpy as np

MODEL_ID = "gray_scott_reaction_diffusion"

# mitosis / self-replicating-spot regime (Pearson class-lambda/mu neighbourhood)
DEFAULTS = {"Du": 0.16, "Dv": 0.08, "F": 0.035, "k": 0.062, "dt": 1.0, "n_seeds": 8, "seed_radius": 3.0}


def laplacian(Z):
    """Periodic 5-point Laplacian, unit spacing."""
    return (np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4.0 * Z)


def make_initial(shape, n_seeds, rng, seed_radius=3.0, noise_amplitude=0.0):
    """U=1, V=0 background + a FEW small V seed spots at random positions (seeds, NOT the pattern)."""
    U = np.ones(shape)
    V = np.zeros(shape)
    ys, xs = np.arange(shape[0])[:, None], np.arange(shape[1])[None, :]
    for _ in range(int(n_seeds)):
        cy, cx = rng.integers(0, shape[0]), rng.integers(0, shape[1])
        d2 = (np.minimum(np.abs(ys - cy), shape[0] - np.abs(ys - cy)) ** 2
              + np.minimum(np.abs(xs - cx), shape[1] - np.abs(xs - cx)) ** 2)
        blob = np.exp(-d2 / (2.0 * seed_radius ** 2))
        U -= 0.5 * blob
        V += 0.5 * blob                                  # seed V above the spot threshold so it registers
    if noise_amplitude:
        U = U + noise_amplitude * rng.standard_normal(shape)
        V = np.clip(V + noise_amplitude * rng.standard_normal(shape), 0.0, None)
    return U, V


def step(U, V, p):
    """One explicit reaction-diffusion step."""
    uvv = U * V * V
    U = U + p["dt"] * (p["Du"] * laplacian(U) - uvv + p["F"] * (1.0 - U))
    V = V + p["dt"] * (p["Dv"] * laplacian(V) + uvv - (p["F"] + p["k"]) * V)
    return U, V


def spot_count(V, thresh=0.25, min_size=2):
    """Number of localized V spots = connected components of V>thresh (self-replication counter).
    Uses scipy.ndimage.label with periodic wrap merged so a spot across the boundary counts once."""
    from scipy import ndimage
    mask = V > thresh
    lbl, n = ndimage.label(mask)
    if n == 0:
        return 0
    # merge components that touch across the periodic boundary (left<->right, top<->bottom)
    remap = {}

    def _union(a, b):
        ra, rb = _find(a), _find(b)
        if ra != rb:
            remap[max(ra, rb)] = min(ra, rb)

    def _find(a):
        while a in remap:
            a = remap[a]
        return a
    for i in range(V.shape[0]):
        a, b = lbl[i, 0], lbl[i, -1]
        if a and b:
            _union(a, b)
    for j in range(V.shape[1]):
        a, b = lbl[0, j], lbl[-1, j]
        if a and b:
            _union(a, b)
    roots = {}
    for c in range(1, n + 1):
        r = _find(c)
        roots[r] = roots.get(r, 0) + int(np.count_nonzero(lbl == c))
    return int(sum(1 for r, sz in roots.items() if sz >= min_size))
