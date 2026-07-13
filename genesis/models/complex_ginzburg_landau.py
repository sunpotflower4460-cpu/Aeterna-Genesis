#!/usr/bin/env python3
"""Complex Ginzburg-Landau (CGL) -- a SINGLE complex oscillatory field, a distinct "white" from TDGL.

    A_t = A + (1 + i b) lap(A) - (1 + i c) |A|^2 A          (periodic, spectral integrating-factor)

Unlike relaxational TDGL (real coefficients -> domains + frozen defects, ceiling L2), CGL has an
oscillatory / dispersive character (b, c != 0). In the Benjamin-Feir regime it produces spiral waves and
DEFECT TURBULENCE -- phase-winding defects that persist AND MOVE. The question this white asks:
**can spontaneous motion (L3) emerge from a scalar field alone, with NO velocity field added?**
(Adding a velocity field would be a different white -- see docs/ANTI_DRIFT.md.)

IC = uniform + tiny complex noise (種・ノイズのみ; no spirals seeded). 「同じ数学 != 同じもの」: this is a
field's phase dynamics, not life/motion of a body.
"""

import numpy as np

MODEL_ID = "cgl_complex_ginzburg_landau"

# Benjamin-Feir-unstable (1 + b*c < 0) -> defect turbulence with moving defects.
DEFAULTS = {"b": 2.0, "c": -1.0, "dt": 0.05}


def make_initial(shape, noise_amplitude, rng):
    """Uniform + tiny complex noise (NO spiral / defect seeded)."""
    return (1.0 + noise_amplitude * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))).astype(
        np.complex128)


def _k2(shape):
    ks = [np.fft.fftfreq(n) * n * (2 * np.pi / n) for n in shape]   # unit spacing -> physical k
    grids = np.meshgrid(*ks, indexing="ij")
    return sum(g ** 2 for g in grids)


def step(A, p, k2=None):
    """One integrating-factor step: exact linear (1 + (1+ib)lap) part, explicit cubic."""
    if k2 is None:
        k2 = _k2(A.shape)
    L = 1.0 - (1.0 + 1j * p["b"]) * k2                # linear operator in Fourier space
    N = -(1.0 + 1j * p["c"]) * (np.abs(A) ** 2) * A   # nonlinear term (real space)
    Ah = np.fft.fftn(A)
    E = np.exp(L * p["dt"])
    Ah = E * Ah + (E - 1.0) / L * np.fft.fftn(N)
    return np.fft.ifftn(Ah)


def winding_defects(A):
    """(count, centroids) of phase-winding defects (spiral cores) via plaquette circulation, masked to
    low-|A| cores. Returns the count and the list of (y,x) centroids for motion tracking."""
    from genesis.diagnostics import measures
    n = measures.winding_defect_count(A)
    amp = np.abs(A)
    thr = 0.5 * float(amp.mean())
    cores = amp < thr                                 # spiral / defect cores are amplitude holes
    from scipy import ndimage
    lbl, m = ndimage.label(cores)
    cents = ndimage.center_of_mass(cores, lbl, range(1, m + 1)) if m else []
    return n, [tuple(float(x) for x in c) for c in cents]
