"""Rotations that never meet: continued fractions, near returns, and harmonics above a gap.

A measuring instrument only.

    continued_fraction(x, n)      [a0; a1, a2, ...] of a Decimal / float x
    convergents(cf)               the best rational approximations p/q, in order
    two_arm_returns(c, t_max)     z(t) = e^{it} + e^{ict}: at t = 2πq the first arm is home; how far is the second?
                                  distance 2|sin(π c q)|, near returns at the convergents' q, petals p − q
    mode_returns(omegas, times)   D(t) = rms_k |e^{iω_k t} − 1| for independent rotations (modes) with the given
                                  frequencies: how close the whole state comes back to its start
    harmonics_above(omega, gap)   the smallest k with k·ω above the gap (the first harmonic that can radiate)

Two frequencies with a rational ratio p/q return exactly (period 2πq); an irrational ratio never does, and its
near returns come at the denominators of its convergents (π: 7, 106, 113, 33102, ...). Many incommensurate
frequencies return (Poincaré) only after times that grow very fast with their number -- which is why a reversible
many-mode universe looks as if it never comes back.
"""
from __future__ import annotations

from decimal import Decimal, getcontext
from fractions import Fraction
from typing import Any

import numpy as np


def continued_fraction(x, n: int = 12) -> list[int]:
    out = []
    getcontext().prec = max(getcontext().prec, 80)
    y = Decimal(x) if not isinstance(x, Decimal) else x
    for _ in range(n):
        a = int(y.to_integral_value(rounding="ROUND_FLOOR"))
        out.append(a)
        frac = y - a
        if frac == 0:
            break
        y = 1 / frac
    return out


def convergents(cf: list[int]) -> list[Fraction]:
    out, h0, h1, k0, k1 = [], 1, cf[0], 0, 1
    out.append(Fraction(h1, k1))
    for a in cf[1:]:
        h0, h1 = h1, a * h1 + h0
        k0, k1 = k1, a * k1 + k0
        out.append(Fraction(h1, k1))
    return out


def two_arm_returns(c: float, q_max: int) -> list[dict[str, Any]]:
    """Every q ≤ q_max that brings the second arm closer to home than all smaller q (record near returns)."""
    rows, best = [], float("inf")
    for q in range(1, q_max + 1):
        d = abs(2.0 * np.sin(np.pi * ((c * q) % 1.0)))
        if d < best - 1e-15:
            best = d
            p = round(c * q)
            rows.append({"q": q, "t": round(2 * np.pi * q, 4), "p": p, "distance": d, "petals": abs(p - q)})
    return rows


def mode_returns(omegas: np.ndarray, times: np.ndarray, chunk: int = 20000) -> np.ndarray:
    """rms over modes of |e^{iωt} − 1| at each time (0 = the whole state is back where it started)."""
    om = np.asarray(omegas, float)[None, :]
    out = np.empty(len(times))
    for i in range(0, len(times), chunk):
        t = np.asarray(times[i:i + chunk], float)[:, None]
        out[i:i + chunk] = np.sqrt(np.mean(np.abs(np.exp(1j * om * t) - 1.0) ** 2, axis=1))
    return out


def harmonics_above(omega: float, gap: float) -> int:
    """Smallest k ≥ 1 with k·ω > gap (k = 1 means ω itself is above the gap and radiates directly)."""
    return int(np.floor(gap / omega)) + 1 if omega > 0 else 0
