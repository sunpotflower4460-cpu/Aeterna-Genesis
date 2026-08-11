"""ai_lab/relational/winding_precheck.py -- R8 PRECONDITION measurement, NOT R8 itself
(PR-R2.3, AUDIT.md Sec.15).

Review's instruction after PR-R2.2's cycle-coverage finding: do not start R8 (winding
number) yet. The blocker is not sample size (only 3 fully-covered fundamental cycles found
so far) -- it is that all 3 are TRIANGLES (length 3), and triangles are structurally
unsuited to a winding-number measurement for two independent reasons:

1. The null rate is too high. For N phases placed independently at random around a circle,
   connected in a fixed cyclic order (the order fixed by the relation graph's own edges,
   NOT re-sorted by phase value), the probability the resulting winding number is nonzero
   is substantial even with no real structure at all -- for N=3 this is exactly 0.25 (the
   classical "probability N random points do not all lie in a semicircle" result,
   1 - N/2^(N-1)), so across the 3 found triangles, P(at least one shows nonzero winding
   with NO real structure) = 1 - 0.75^3 = ~58%. A nonzero winding number on a triangle is
   the EXPECTED outcome of noise, not evidence of anything.
2. Resolution is insufficient. A winding number is only meaningful if phase changes
   gradually as you go around the loop; going around in 3 steps means each step is 1/3 of a
   full loop, so |winding| > 1 cannot be distinguished from |winding| = 1 (aliasing) -- the
   instrument would be blind to anything but the coarsest possible structure even if the
   null-rate problem were solved.

This module measures the null rate (review's point 2, "mandatory work before building R8")
so that a FUTURE R8, once fed cycles of length >= 6 (review's stated minimum), has a
pre-established baseline to compare against -- a positive winding-number rate is only
evidence of structure when it significantly exceeds this null, never on its own.

`compute_winding` is deliberately generic (any phase array, any N) so it can be reused
by a future R8; nothing here is wired into `instruments.py` or `measure_all()`, and this
module does not itself claim to measure R-layer winding structure -- it only characterizes
the measurement's own error floor.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


def compute_winding(phases: np.ndarray) -> int:
    """Discrete winding number of `phases` (an array of N angles, radians, in a FIXED
    cyclic order -- e.g. the order nodes appear around a relation-graph cycle, NOT
    re-sorted by phase value). Sums wrapped consecutive differences (each wrapped to
    (-pi, pi]) around the full loop (including the wraparound edge from the last phase back
    to the first) and divides by 2*pi. This sum is, up to floating-point error, always an
    exact integer multiple of 2*pi -- that integer is the winding number.
    """
    phases = np.asarray(phases, dtype=float)
    diffs = np.diff(phases, append=phases[:1])
    wrapped = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    return int(round(float(wrapped.sum()) / (2.0 * np.pi)))


def analytic_semicircle_null_rate(n: int) -> float:
    """Closed-form P(winding != 0) for N ANGULARLY-SORTED i.i.d. uniform phases connected
    in sorted order (the classical "not all in one semicircle" result, 1 - N/2^(N-1)).
    Provided for cross-checking `monte_carlo_null_rate` at the ONE cycle length (N=3) where
    a fixed arbitrary cyclic order is topologically forced to coincide with the angularly-
    sorted order (any two distinct cyclic traversals of 3 points are the same triangle, up
    to orientation). NOT valid as a general-N formula for a fixed, graph-determined order
    (see module docstring) -- `monte_carlo_null_rate` is the correct tool for N >= 4.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    return 1.0 - n / (2.0 ** (n - 1))


def monte_carlo_null_rate(n: int, trials: int = 200_000, seed: Optional[int] = None) -> float:
    """Empirical P(winding != 0) for N i.i.d. Uniform(0, 2*pi) phases connected in a FIXED
    (not re-sorted) cyclic order -- matching how a real relation-graph cycle's node order is
    fixed by the graph, independent of whatever phase values later land on those nodes.
    """
    rng = np.random.default_rng(seed)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(trials, n))
    diffs = np.diff(phases, axis=1, append=phases[:, :1])
    wrapped = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    windings = np.round(wrapped.sum(axis=1) / (2.0 * np.pi)).astype(int)
    return float(np.mean(windings != 0))


def shuffled_null_rate(observed_phases: np.ndarray, trials: int = 200_000,
                        seed: Optional[int] = None) -> float:
    """Empirical P(winding != 0) when the ACTUAL observed phases on a real cycle are
    randomly permuted among that same cycle's node positions (a permutation-test null,
    per review's second suggested method: "同じ閉路上で位相をシャッフルした場合"). Uses the
    real phase VALUES (preserving whatever marginal distribution they actually have -- not
    necessarily uniform), only destroying any relationship between phase and graph position.
    """
    observed_phases = np.asarray(observed_phases, dtype=float)
    n = len(observed_phases)
    rng = np.random.default_rng(seed)
    nonzero = 0
    for _ in range(trials):
        perm = rng.permutation(n)
        w = compute_winding(observed_phases[perm])
        if w != 0:
            nonzero += 1
    return nonzero / trials
