"""The standard map (Chirikov–Taylor), the textbook KAM world: which torus lasts longest? (P16, H7)

    p' = p + (K / 2π) sin(2π x),     x' = x + p'          (x mod 1; area-preserving, the kicked rotor)

For K = 0 every horizontal line p = ω is an invariant circle (a torus of the rotor) turning by ω per kick. As K
grows, circles whose rotation number ω is close to a fraction p/q break first (resonance); the last rotational
circle to survive has the golden rotation number and breaks at K ≈ 0.971635 (Greene 1979; MacKay 1983). Here
that is measured, not assumed:

* `rotation(K, p0, N)`: rotation numbers of orbits started on the symmetry line x = 0 by weighted Birkhoff
  averaging (Das, Sander & Yorke 2016). For a quasi-periodic orbit (an invariant circle) the average converges
  extremely fast -- two successive windows agree to ~1e-12; for a chaotic orbit they differ by ~1e-3. So the
  difference tells regular from chaotic without looking.
* rotational circles = regular orbits whose ω is not a fraction with a small denominator (islands around periodic
  orbits are regular too, but turn at an exact p/q).

A map, not a field: every step is one kick of a rotor. It is the cleanest place where "a rotation that never meets
itself" can be measured.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np


def step(x: np.ndarray, p: np.ndarray, K: float):
    p = p + K / (2.0 * np.pi) * np.sin(2.0 * np.pi * x)
    return x + p, p


def _bump(N: int) -> np.ndarray:
    t = np.arange(1, N + 1) / (N + 1.0)
    w = np.exp(-1.0 / (t * (1.0 - t)))
    return w / w.sum()


def rotation(K: float, p0, N: int = 20000, x0: float = 0.0):
    """(ω, err): weighted Birkhoff averages of the momentum (= rotation number) over two successive windows of N
    kicks each; err = |difference| (tiny for invariant circles, ~1e-3 for chaos)."""
    p = np.asarray(p0, float).copy()
    x = np.full(p.shape, x0)
    w = _bump(N)
    a1 = np.zeros(p.shape)
    a2 = np.zeros(p.shape)
    for n in range(2 * N):
        x, p = step(x, p, K)
        if n < N:
            a1 += w[n] * p
        else:
            a2 += w[n - N] * p
    return a1, np.abs(a1 - a2)


def near_fraction(w: float, qmax: int = 300, tol: float = 1e-7) -> bool:
    f = Fraction(float(w)).limit_denominator(qmax)
    return abs(float(f) - w) < tol


def circles(K: float, n: int = 4001, N: int = 20000, reg_tol: float = 1e-9) -> np.ndarray:
    """Rotation numbers (in [0, 1]) of the rotational invariant circles met by orbits from x = 0, p0 ∈ [0, 1]."""
    om, err = rotation(K, np.linspace(0.0, 1.0, n), N)
    keep = [w for w, e in zip(om, err) if e < reg_tol and 0.0 < w < 1.0 and not near_fraction(w)]
    return np.array(sorted(keep))
