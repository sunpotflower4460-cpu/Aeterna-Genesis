"""A medium with its own rhythm under an outside beat (P16, H7): is it captured by the beat, or does it keep its own
rhythm? Does the golden ratio stay free?

    u_t = D ∇²u + u − u³/3 − v + I0 + γ cos(Ω t)
    v_t = ε (u + a − b v)                                         (FitzHugh–Nagumo, periodic, local, explicit Euler)

With I0 = 0.5 every point oscillates on its own (a relaxation oscillator, period T0 ≈ 39.5 time units with the
defaults). The outside beat γ cos(Ω t) is the same everywhere (like day and night) -- it is PUT IN. Its period is
Tf = 2π/Ω; the knob is s = Tf / T0 (s = 1/2: the beat is twice as fast as the medium; s = 1/3: three times).

Known physics (Arnold tongues, devil's staircase; resonant patterns in the forced BZ reaction, Petrov, Ouyang &
Swinney 1997): near simple ratios the medium is captured -- every point turns an exact rational number of times per
beat -- and at n : 1 it splits into n phase domains; far from simple fractions it keeps its own rhythm. The golden
ratio is the number farthest from all fractions. Whether this medium is captured, how many domains it makes and
where, and whether its own spirals / scroll waves survive, is measured, not placed.

Put in: the law (a, b, ε, I0, D, grid spacing), the beat (γ, s), t = 0: patchy random u, v
(`excitable_barkley.smooth_noise`). D = 0 gives independent oscillators (used for the 0D staircase, where Ω may
be an array: one forcing frequency per oscillator).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from genesis.models.excitable_barkley import smooth_noise

DEFAULTS: dict[str, Any] = {"a": 0.7, "b": 0.8, "eps": 0.08, "I0": 0.5, "D": 1.0, "dx": 1.0, "dt": 0.02,
                            "gamma": 0.1, "s": 0.5, "corr": 6.0}
T0 = 39.4888                    # free period with the defaults (D = 0), measured by `free_period`
U_STAR, V_STAR = 0.4, 0.8      # a point inside the limit cycle: the phase angle turns around it


def laplacian(f: np.ndarray, dx: float) -> np.ndarray:
    out = -2.0 * f.ndim * f
    for ax in range(f.ndim):
        out = out + np.roll(f, 1, ax) + np.roll(f, -1, ax)
    return out / (dx * dx)


def omega(p: dict[str, Any], T0_: float = T0):
    """Angular frequency of the beat for s = Tf / T0 (s may be an array)."""
    return 2.0 * np.pi / (np.asarray(p["s"], float) * T0_)


def step(u, v, t: float, p: dict[str, Any], Om=None):
    dt = p["dt"]
    Om = omega(p) if Om is None else Om
    drive = p["I0"] + p["gamma"] * np.cos(Om * t)
    du = u - u * u * u / 3.0 - v + drive
    if p["D"]:
        du = du + p["D"] * laplacian(u, p["dx"])
    return u + dt * du, v + dt * p["eps"] * (u + p["a"] - p["b"] * v)


def make_initial(shape, rng: np.random.Generator, p: dict[str, Any]):
    """Patchy random start: u in [−2, 2], v in [−0.5, 1.5], smooth patches of `corr` cells."""
    u = -2.0 + 4.0 * smooth_noise(shape, rng, p["corr"])
    v = -0.5 + 2.0 * smooth_noise(shape, rng, p["corr"])
    return u, v


def phase(u, v):
    """Angle of the point on the limit cycle, turning by 2π per own cycle."""
    return np.arctan2(v - V_STAR, u - U_STAR)


def free_period(p: dict[str, Any] | None = None, T: float = 2000.0) -> float:
    """Period of one unforced oscillator (upward crossings of u = 0, linearly interpolated)."""
    p = dict(DEFAULTS, **(p or {}), gamma=0.0, D=0.0)
    u, v = np.array(-1.0), np.array(-0.5)
    t, last, per = 0.0, None, []
    for _ in range(int(T / p["dt"])):
        un, vn = step(u, v, t, p, Om=0.0)
        if u < 0 <= un:
            tc = t + p["dt"] * float(-u / (un - u))
            if last is not None:
                per.append(tc - last)
            last = tc
        u, v, t = un, vn, t + p["dt"]
    return float(np.mean(per[-5:]))
