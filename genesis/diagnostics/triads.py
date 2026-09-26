"""Triads: relations of THREE waves (P9-Q3). The measure does not know which pattern to expect.

For a real 2D field u on a periodic box (spacing dx):
* `peaks`: the strongest Fourier modes in the ring |k| ∈ [kmin, kmax] (one of each ±k pair), with amplitude and phase.
* `triads`: all triples of those modes (or their mirrors) whose integer wave-vector indices sum EXACTLY to zero,
  with their angles and the triangle phase Φ = φ₁ + φ₂ + φ₃ (translation invariant by construction).
* `pair_phases`: the phase differences φ₂ − φ₁ of pairs (NOT translation invariant -- the contrast).
* `triad_skewness`: ⟨w³⟩ / ⟨w²⟩^{3/2} of the ring-filtered field w. Σ_x w³ is exactly the amplitude-weighted sum
  over all closed triangles in the ring of û₁û₂û₃, so its sign is the weighted mean cos Φ: > 0 ↔ Φ ≈ 0,
  < 0 ↔ Φ ≈ π, ≈ 0 for stripes (no closed triangle).
The FFT here is a measuring instrument only (the laws stay local).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np


def _grid(shape, dx):
    ky = np.fft.fftfreq(shape[0], d=dx) * 2 * np.pi
    kx = np.fft.fftfreq(shape[1], d=dx) * 2 * np.pi
    return np.meshgrid(ky, kx, indexing="ij")


def ring_filter(u: np.ndarray, dx: float, kmin: float = 0.7, kmax: float = 1.3) -> np.ndarray:
    KY, KX = _grid(u.shape, dx)
    k = np.hypot(KY, KX)
    return np.real(np.fft.ifft2(np.fft.fft2(u) * ((k >= kmin) & (k <= kmax))))


def triad_skewness(u: np.ndarray, dx: float, kmin: float = 0.7, kmax: float = 1.3) -> float:
    w = ring_filter(u, dx, kmin, kmax)
    m2 = float((w * w).mean())
    return float((w ** 3).mean() / m2 ** 1.5) if m2 > 0 else 0.0


def peaks(u: np.ndarray, dx: float, count: int = 6, kmin: float = 0.7, kmax: float = 1.3) -> list[dict]:
    """The `count` strongest modes in the ring, one per ±k pair (index (i, j) as signed integers)."""
    uh = np.fft.fft2(u) / u.size
    KY, KX = _grid(u.shape, dx)
    k = np.hypot(KY, KX)
    iy = np.fft.fftfreq(u.shape[0], d=1.0 / u.shape[0]).astype(int)
    ix = np.fft.fftfreq(u.shape[1], d=1.0 / u.shape[1]).astype(int)
    ring = (k >= kmin) & (k <= kmax)
    order = np.argsort(-np.abs(uh) * ring, axis=None)
    out, seen = [], set()
    for flat in order:
        a, b = np.unravel_index(flat, u.shape)
        if not ring[a, b]:
            break
        key = (int(iy[a]), int(ix[b]))
        if key in seen or (-key[0], -key[1]) in seen:
            continue
        seen.add(key)
        out.append({"n": key, "k": (float(KY[a, b]), float(KX[a, b])), "amp": float(np.abs(uh[a, b])),
                    "phase": float(np.angle(uh[a, b]))})
        if len(out) >= count:
            break
    return out


def triads(ps: list[dict]) -> list[dict]:
    """Closed triangles among the peaks and their mirrors (−k has phase −φ): exact integer sum zero."""
    modes = []
    for p in ps:
        modes.append((p["n"], p["k"], p["phase"], p["amp"]))
        modes.append(((-p["n"][0], -p["n"][1]), (-p["k"][0], -p["k"][1]), -p["phase"], p["amp"]))
    out = []
    for a, b, c in combinations(range(len(modes)), 3):
        (n1, k1, f1, a1), (n2, k2, f2, a2), (n3, k3, f3, a3) = modes[a], modes[b], modes[c]
        if n1[0] + n2[0] + n3[0] or n1[1] + n2[1] + n3[1]:
            continue
        ang = [float(np.degrees(np.arccos(np.clip(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)), -1, 1))))
               for x, y in ((k1, k2), (k2, k3), (k3, k1))]
        phi = float(np.angle(np.exp(1j * (f1 + f2 + f3))))
        out.append({"modes": [n1, n2, n3], "angles": ang, "Phi": phi, "weight": a1 * a2 * a3})
    # a triangle and its mirror image carry Φ and −Φ: keep one of each
    uniq, seen = [], set()
    for t in out:
        key = frozenset(t["modes"])
        mirror = frozenset((-m[0], -m[1]) for m in t["modes"])
        if key in seen or mirror in seen:
            continue
        seen.add(key)
        uniq.append(t)
    return uniq


def pair_phases(ps: list[dict]) -> list[float]:
    return [float(np.angle(np.exp(1j * (q["phase"] - p["phase"])))) for p, q in combinations(ps, 2)]
