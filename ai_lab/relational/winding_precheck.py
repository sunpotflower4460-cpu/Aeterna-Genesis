"""ai_lab/relational/winding_precheck.py -- R8 PRECONDITION measurement, NOT R8 itself
(PR-R2.3 + PR-R2.4, AUDIT.md Sec.15-16).

Review's instruction after PR-R2.2's cycle-coverage finding: do not start R8 (winding
number) yet. The blocker is not sample size (only 3 fully-covered fundamental cycles found
so far) -- it is that all 3 are TRIANGLES (length 3), and triangles are structurally
unsuited to a bare winding-number measurement (PR-R2.3, Sec.15.2): the plain null rate is
substantial (0.25 at N=3) and, non-obviously, RISES with cycle length under a fixed
(graph-determined, not phase-sorted) traversal order (0.57 by N=10) -- a longer cycle is not
automatically easier to interpret on the null-rate axis.

PR-R2.4 (Sec.16.1) adds the missing piece review identified: a bare nonzero winding number
is not enough, because noise can produce a large single jump that "wraps around" in one
step just as easily as genuine smooth phase progression can. A SMOOTHNESS GATE is required:
winding != 0 AND every adjacent wrapped phase step has |step| < a fixed threshold
(pi/2 by default). This is not a redundant restatement of the plain null-rate problem --
it is a SEPARATE necessary condition with its own consequence: N steps each strictly
under pi/2 sum to strictly under N*pi/2, so representing one full loop (2*pi) requires
N*pi/2 > 2*pi, i.e. N > 4, i.e. **N >= 5 is a hard necessary condition** for a cycle to
ever satisfy the smoothness gate at all -- independent of whatever phases actually occur.
Triangles (N=3) and squares (N=4) cannot pass the smoothness gate under ANY phase
assignment; this is a structural fact about the gate, not a probabilistic one.

`compute_winding` and `is_smooth_winding` are deliberately generic (any phase array, any N)
so they can be reused by a future R8; nothing here is wired into `instruments.py` or
`measure_all()`, and this module does not itself claim to measure R-layer winding
structure -- it only characterizes the measurement's own error floor and necessary
preconditions.

STANDING DISCIPLINE (PR-R6, AUDIT.md Sec.25.4, review's explicit instruction): a
smooth-winding CANDIDATE must not be reported -- not even provisionally -- unless it has
been checked at `WINDING_CANDIDACY_MIN_EXTEND_FACTOR` (30x the base window) or wider. This
is baked into the definition of "candidate," not treated as an optional follow-up
robustness check. Reason, stated plainly because it recurred a fourth time before being
made structural: this exact short-window failure mode -- something that looks settled/
smooth at a shorter window and stops being so once the window is extended -- has now
appeared at 605/1200 (PR-R1.5's memory=on sweep), 116/600 (Sec.11's settled-vs-sustained
correction), 119 missed-detection node-checks (PR-R2.6's screening false-negative work),
and 3/5 of PR-R5's wide-basis winding candidates (Sec.24.2, 15x->30x). Every prior
occurrence was caught by a follow-up check after the fact; this constant exists so the next
occurrence is caught by construction instead.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

WINDING_CANDIDACY_MIN_EXTEND_FACTOR = 30


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


# Fixed, disclosed default -- same threshold for every call, not tuned per cycle.
DEFAULT_SMOOTHNESS_THRESHOLD = np.pi / 2.0

# N*threshold must exceed 2*pi for a cycle of length N to be able to pass the smoothness
# gate at all (N steps each strictly < threshold must sum to >= 2*pi in magnitude for a
# nonzero winding). At the default threshold (pi/2), this requires N > 4, i.e. N >= 5.
MIN_LENGTH_FOR_SMOOTH_WINDING = int(np.ceil(2.0 * np.pi / DEFAULT_SMOOTHNESS_THRESHOLD)) + 1


def max_adjacent_step(phases: np.ndarray) -> float:
    """Largest |wrapped consecutive phase difference| around the loop (radians) -- the
    "how big was the biggest single jump" companion to `compute_winding`'s "what did all
    the jumps sum to."""
    phases = np.asarray(phases, dtype=float)
    diffs = np.diff(phases, append=phases[:1])
    wrapped = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    return float(np.max(np.abs(wrapped)))


def is_smooth_winding(phases: np.ndarray, threshold: float = DEFAULT_SMOOTHNESS_THRESHOLD) -> bool:
    """AUDIT.md Sec.16.1's composite criterion (review's instruction, PR-R2.4): a winding
    counts only if BOTH (a) `compute_winding(phases) != 0` AND (b) every adjacent wrapped
    phase step has |step| < `threshold`. A single large jump can produce a nonzero winding
    on pure noise just as easily as a genuine gradual phase progression can -- this gate is
    what tells the two apart. Structural consequence: no cycle shorter than
    `MIN_LENGTH_FOR_SMOOTH_WINDING` (5, at the default pi/2 threshold) can EVER satisfy this
    gate, for any phase assignment -- N*threshold must exceed 2*pi.
    """
    phases = np.asarray(phases, dtype=float)
    if len(phases) < MIN_LENGTH_FOR_SMOOTH_WINDING and threshold == DEFAULT_SMOOTHNESS_THRESHOLD:
        return False  # structurally impossible; short-circuit without computing
    return compute_winding(phases) != 0 and max_adjacent_step(phases) < threshold


def monte_carlo_smooth_null_rate(n: int, threshold: float = DEFAULT_SMOOTHNESS_THRESHOLD,
                                  trials: int = 200_000, seed: Optional[int] = None) -> float:
    """Empirical P(is_smooth_winding) for N i.i.d. Uniform(0, 2*pi) phases in a fixed cyclic
    order -- the composite-criterion null rate review asked to be re-measured, not assumed
    from the rough (1/2)^N approximation. Vectorized for the same N/trials scale as
    `monte_carlo_null_rate`.
    """
    rng = np.random.default_rng(seed)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(trials, n))
    diffs = np.diff(phases, axis=1, append=phases[:, :1])
    wrapped = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    windings = np.round(wrapped.sum(axis=1) / (2.0 * np.pi)).astype(int)
    max_step = np.max(np.abs(wrapped), axis=1)
    smooth_nonzero = (windings != 0) & (max_step < threshold)
    return float(np.mean(smooth_nonzero))
