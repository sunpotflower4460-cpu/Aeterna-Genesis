"""Rhythm: how fast the phase of a complex field turns, point by point (P9-Q1). Knows nothing about spirals.

* `frequencies(phase_stack, dt)`: ω at every site = −slope of the unwrapped phase over a time window
  (phase_stack[t, ...] = angle(A) sampled every dt; the window must be long compared with 2π/ω and the sampling
  fine enough that the phase moves < π per sample).
* `local_wavenumber(A)`: |∇φ| from Im(A* ∇A)/|A|² (central differences, periodic).
* `mode(x, bins)`: the most common value (histogram peak) -- robust against cores and shocks.
"""
from __future__ import annotations

import numpy as np


def frequencies(phase_stack: np.ndarray, dt: float) -> np.ndarray:
    ph = np.unwrap(np.asarray(phase_stack), axis=0)
    t = np.arange(len(ph)) * dt
    return -np.polyfit(t, ph.reshape(len(ph), -1), 1)[0].reshape(ph.shape[1:])


def local_wavenumber(A: np.ndarray) -> np.ndarray:
    a2 = np.maximum(np.abs(A) ** 2, 1e-12)
    g2 = np.zeros(A.shape)
    for ax in range(A.ndim):
        d = (np.roll(A, -1, ax) - np.roll(A, 1, ax)) / 2.0
        g2 += (np.imag(np.conj(A) * d) / a2) ** 2
    return np.sqrt(g2)


def mode(x: np.ndarray, bins: int = 80) -> float:
    h, e = np.histogram(np.asarray(x).ravel(), bins=bins)
    i = int(np.argmax(h))
    return float(0.5 * (e[i] + e[i + 1]))
