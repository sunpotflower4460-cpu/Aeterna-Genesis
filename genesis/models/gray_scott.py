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
DEFAULTS = {"Du": 0.16, "Dv": 0.08, "F": 0.035, "k": 0.062, "dt": 1.0, "n_seeds": 8, "seed_radius": 3.0,
            "DT": 0.10, "gT": 4.0}   # heritable bistable tag: diffusion DT, bistable gain gT


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


def _merged_labels(V, thresh=0.25):
    """Label connected V>thresh components, merging pieces that touch across the periodic boundary.
    Returns (root_label_array, {root: size})."""
    from scipy import ndimage
    lbl, n = ndimage.label(V > thresh)
    if n == 0:
        return lbl, {}
    remap = {}

    def _find(a):
        while a in remap:
            a = remap[a]
        return a

    def _union(a, b):
        ra, rb = _find(a), _find(b)
        if ra != rb:
            remap[max(ra, rb)] = min(ra, rb)
    for i in range(V.shape[0]):
        a, b = lbl[i, 0], lbl[i, -1]
        if a and b:
            _union(a, b)
    for j in range(V.shape[1]):
        a, b = lbl[0, j], lbl[-1, j]
        if a and b:
            _union(a, b)
    roots = np.zeros_like(lbl)
    sizes = {}
    for c in range(1, n + 1):
        r = _find(c)
        m = lbl == c
        roots[m] = r
        sizes[r] = sizes.get(r, 0) + int(np.count_nonzero(m))
    return roots, sizes


def spot_count(V, thresh=0.25, min_size=2):
    """Number of localized V spots = connected components of V>thresh (self-replication counter),
    with periodic-boundary pieces merged so a spot across the wrap counts once."""
    _, sizes = _merged_labels(V, thresh)
    return int(sum(1 for sz in sizes.values() if sz >= min_size))


# ---- heritable bistable TAG (FULL L7 = division + inheritance): daughters carry the parent's tag ----

def make_initial_tagged(shape, n_seeds, rng, seed_radius=3.0, mix=0.5):
    """Seed n_seeds founders, each carrying a bistable TAG (0 or 1) painted onto its own V region; the
    background tag is a neutral 0.5. The tag is a START condition on the FOUNDERS only -- daughters are
    NOT assigned tags; they must INHERIT via the dynamics (that is what we measure). 第8監査-safe."""
    U = np.ones(shape)
    V = np.zeros(shape)
    T = np.full(shape, 0.5)
    ys, xs = np.arange(shape[0])[:, None], np.arange(shape[1])[None, :]
    founder_tags = []
    for _ in range(int(n_seeds)):
        cy, cx = rng.integers(0, shape[0]), rng.integers(0, shape[1])
        d2 = (np.minimum(np.abs(ys - cy), shape[0] - np.abs(ys - cy)) ** 2
              + np.minimum(np.abs(xs - cx), shape[1] - np.abs(xs - cx)) ** 2)
        blob = np.exp(-d2 / (2.0 * seed_radius ** 2))
        tag = 1.0 if rng.random() < mix else 0.0
        founder_tags.append(tag)
        U -= 0.5 * blob
        V += 0.5 * blob
        core = blob > 0.2
        T[core] = tag                                     # paint the founder's tag onto its core
    return U, V, T, founder_tags


def step_tagged(U, V, T, p):
    """One RD step plus a bistable tag update: T is pushed toward {0,1} where V is present (spots), and
    diffuses slightly so a dividing spot carries its tag into both daughters (inheritance, not command)."""
    U, V = step(U, V, p)
    T = T + p["dt"] * (p["DT"] * laplacian(T) + p["gT"] * V * T * (1.0 - T) * (T - 0.5))
    T = np.clip(T, 0.0, 1.0)
    return U, V, T


def spot_tags(V, T, thresh=0.25, min_size=2):
    """Per-spot inherited tag + bistable purity. Returns a list of {tag, purity, size}; purity =
    |mean_tag - 0.5| * 2 in [0,1] (1 = a clean 0-or-1 heritable state; 0 = smeared at 0.5)."""
    roots, sizes = _merged_labels(V, thresh)
    out = []
    for r, sz in sizes.items():
        if sz < min_size:
            continue
        mt = float(np.mean(T[roots == r]))
        out.append({"tag": int(round(mt)), "purity": float(abs(mt - 0.5) * 2.0), "size": int(sz)})
    return out


def v_mass(V, thresh=0.25):
    """Total V-mass above threshold (independent accounting check against the spot count)."""
    return float(np.sum(V[V > thresh]))
