#!/usr/bin/env python3
"""Swift-Hohenberg (cubic-quintic) -- a bistable pattern-forming scalar field whose white supports
STABLE LOCALIZED STATES. A distinct "white" probing the map's missing rung: L4 persistent individuality.

    u_t = r u - (1 + lap)^2 u + b u^3 - u^5        (periodic, semi-implicit spectral)

Every white in the ceiling map either localizes-but-freezes (TDGL: pinned defects), moves-but-globally
(Boussinesq coherent rolls / CGL turbulence), or divides (Gray-Scott). NONE is a persistent, self-healing
LOCALIZED INDIVIDUAL. Swift-Hohenberg localized states (Pomeau pinning) are exactly that: from a generic
symmetric seed a bounded structure forms that PERSISTS, has inside/outside contrast, and -- the L4
discriminator -- RECOVERS its form after a perturbation (self-heals). You cannot PLACE self-healing.

The question this white asks: **can a persistent INDIVIDUAL (L4: inside/outside + tracked ID + recovery
after perturbation, EMERGENCE_LEVELS.md) emerge from t=0 IC-only?**  Honest answer (measured): yes, but it
is STATIC -- SH is variational (gradient flow) so the individual does NOT self-move. Self-propelled
individuality (L4 individual that also spontaneously MOVES, L3-motion) needs a non-variational white and is
frontier. 「同じ数学 != 同じもの」: this is a localized attractor of a field, not a cell/organism.

IC = one radially-symmetric Gaussian bump + tiny noise (NOT a completed boundary/membrane; the boundary,
size, amplitude, persistence and self-healing all EMERGE and are attractor-selected -- seed-independent).
"""

import numpy as np

MODEL_ID = "sh_swift_hohenberg"

# r<0 (linearly stable background) inside the pinning range with b -> stable localized states.
DEFAULTS = {"r": -0.4, "b": 2.0, "dx": 0.5, "dt": 0.2, "seed_amp": 1.2, "seed_width": 3.0}


def _k2(N, dx):
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    KX, KY = np.meshgrid(k, k, indexing="ij")
    return KX ** 2 + KY ** 2


def make_initial(shape, noise_amplitude, rng, p=None):
    """One symmetric Gaussian bump on the u~0 background + tiny noise (NO pattern / boundary seeded)."""
    p = dict(DEFAULTS if p is None else p)
    N = shape[0]
    x = (np.arange(N) - N / 2) * p["dx"]
    X, Y = np.meshgrid(x, x, indexing="ij")
    bump = p["seed_amp"] * np.exp(-(X ** 2 + Y ** 2) / (2.0 * p["seed_width"] ** 2))
    return bump + noise_amplitude * rng.standard_normal(shape)


def step(u, p, k2=None):
    """One semi-implicit spectral step: linear (1+lap)^2 implicit, cubic-quintic nonlinearity explicit."""
    if k2 is None:
        k2 = _k2(u.shape[0], p["dx"])
    lin = p["r"] - (1.0 - k2) ** 2                       # multiplier of the linear operator in Fourier space
    N = p["b"] * u ** 3 - u ** 5
    uh = np.fft.fft2(u) + p["dt"] * np.fft.fft2(N)
    uh = uh / (1.0 - p["dt"] * lin)                      # unconditionally-stable linear split (lin<=r<0 region)
    return np.real(np.fft.ifft2(uh))


def support_mask(u, thr=0.3):
    """Inside/outside: the bounded region where the field departs from the ~0 background."""
    return np.abs(u) > thr


def individual_stats(u, thr=0.3):
    """(area, centroid(y,x), peak_count, amax) of the localized individual -- for tracking and contrast."""
    from scipy import ndimage
    m = support_mask(u, thr)
    area = int(m.sum())
    if area == 0:
        return {"area": 0, "centroid": (np.nan, np.nan), "peaks": 0, "amax": 0.0}
    idx = np.indices(u.shape)
    cy = float((idx[0] * m).sum() / m.sum())
    cx = float((idx[1] * m).sum() / m.sum())
    _, peaks = ndimage.label(np.abs(u) > 0.6)
    return {"area": area, "centroid": (cy, cx), "peaks": int(peaks), "amax": float(np.abs(u).max())}
