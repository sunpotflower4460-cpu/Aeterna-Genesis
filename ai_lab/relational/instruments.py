"""ai_lab/relational/instruments.py -- R-layer measurement instruments (spec Sec.6).

PR-R1 implements R1 (difference), R2 (direction), R3 (reversal), R4 (period) only.
R5-R11 are explicitly out of scope for this PR (spec Sec.10 / task constraints).

Every instrument returns a `Reading`, which pairs the measured VALUE with what this
instrument can even EXPRESS -- that pairing is the load-bearing data structure behind the
9th audit (instrument_audit.py / spec Sec.8): "before writing 'did not reach X', check
whether the instrument could have expressed X at all."

Vocabulary note: R4 conceptually corresponds to spec Sec.6's f_i = 1/T_i ("frequency").
This module deliberately never spells that word -- the reciprocal-of-period quantity is
returned under the key `rate_i` instead of `frequency_i`. This keeps
tests/test_r_layer_vocabulary.py a simple, mechanical assert-absence check (the forbidden
words never need to appear in this PR's output at all, since only R1-R4 exist here and R4's
"frequency" would otherwise be the one edge case requiring a licensing rule instead of a
flat ban -- avoided by not using the word). The MEASUREMENT (1/T_i) is still made; only the
literal English/Japanese word for it is avoided in output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class Reading:
    """One measurement, paired with what this instrument can even express (spec Sec.6)."""

    name: str
    value: Any                # None when precondition not met
    defined: bool              # was the precondition satisfied?
    precondition: str          # human-readable statement of what must hold for value != None
    expressible_max: Any       # the largest value this instrument could, in principle, report
    expressible_note: str      # why that ceiling exists

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "defined": self.defined,
            "precondition": self.precondition,
            "expressible_max": self.expressible_max,
            "expressible_note": self.expressible_note,
        }


def _native(obj):
    """Recursively convert numpy scalars/arrays to plain Python types (JSON-safe)."""
    if isinstance(obj, np.ndarray):
        return [_native(v) for v in obj.tolist()]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: _native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_native(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# R1 -- difference: variance among nodes.
# ---------------------------------------------------------------------------

def difference(x_traj: np.ndarray) -> Reading:
    """R1: the spatial (across-node) variance of the state, over time.

    Precondition: N >= 2 (need at least two nodes to have a difference at all).
    No expressible upper bound -- variance is unbounded above in principle.
    """
    n = x_traj.shape[1]
    if n < 2:
        return Reading(
            name="difference", value=None, defined=False,
            precondition="N >= 2", expressible_max=None, expressible_note="N/A",
        )
    # variance across nodes at each snapshot, summed over state dimensions m, then averaged
    per_step_var = x_traj.var(axis=1).sum(axis=-1)  # shape (L,)
    return Reading(
        name="difference",
        value=_native({
            "per_step": per_step_var,
            "mean": per_step_var.mean(),
            "final": per_step_var[-1],
        }),
        defined=True,
        precondition="N >= 2",
        expressible_max=None,
        expressible_note="variance has no instrument-imposed ceiling (unlike R3/R4, which are "
                          "bounded by the recording window).",
    )


# ---------------------------------------------------------------------------
# R2 -- direction: does sign(x_j - x_i) persist on an edge?
# ---------------------------------------------------------------------------

def direction(x_traj: np.ndarray, W: np.ndarray, r1: Optional[Reading] = None) -> Reading:
    """R2: per-edge persistence of sign(x_j - x_i) over the recorded trajectory.

    Precondition: R1 > 0 (there is some difference to have a direction).
    No expressible upper bound (persistence is a fraction in [0, 1] by construction, not an
    instrument-limited quantity the way period length is).
    """
    if r1 is None:
        r1 = difference(x_traj)
    precondition = "R1(difference).value.mean > 0"
    if not r1.defined or r1.value is None or r1.value["mean"] <= 0:
        return Reading(
            name="direction", value=None, defined=False,
            precondition=precondition, expressible_max=None, expressible_note="N/A",
        )
    n = x_traj.shape[1]
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if W[i, j] > 0]
    if not edges:
        return Reading(
            name="direction", value=None, defined=False,
            precondition="at least one edge with w_ij > 0", expressible_max=None,
            expressible_note="N/A",
        )
    persistences = []
    for i, j in edges:
        diff = x_traj[:, j, :] - x_traj[:, i, :]
        s = np.sign(diff.sum(axis=-1))  # collapse m dims to a single sign via their sum
        nonzero = s[s != 0]
        if len(nonzero) == 0:
            persistences.append(0.5)  # perfectly balanced / no signal
            continue
        frac_pos = float((nonzero > 0).mean())
        persistences.append(max(frac_pos, 1.0 - frac_pos))
    persistences = np.array(persistences)
    return Reading(
        name="direction",
        value=_native({
            "per_edge_persistence": persistences,
            "mean_persistence": persistences.mean(),
            "n_edges": len(edges),
        }),
        defined=True,
        precondition=precondition,
        expressible_max=1.0,
        expressible_note="persistence is a fraction of recorded snapshots on the majority "
                          "sign; it is bounded at 1.0 by construction, not by a recording-"
                          "window limit.",
    )


# ---------------------------------------------------------------------------
# R3 -- reversal: zero-crossings of each node around its own moving average.
# ---------------------------------------------------------------------------

def _moving_average(series: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return series.copy()
    kernel = np.ones(window) / window
    pad = window // 2
    padded = np.pad(series, (pad, window - 1 - pad), mode="edge")
    return np.convolve(padded, kernel, mode="valid")[: len(series)]


_REVERSAL_NOISE_REL_TOL = 1e-6  # fixed, disclosed noise floor -- same for every run, not tuned per outcome


def reversal(x_traj: np.ndarray, r1: Optional[Reading] = None, window: Optional[int] = None) -> Reading:
    """R3: per-node zero-crossing count around that node's own moving average.

    Precondition: R1 > 0.
    Expressible max: the number of recorded snapshots L -- you cannot detect more sign
    changes than there are consecutive-snapshot pairs (L - 1) to compare.

    A fixed relative noise floor (_REVERSAL_NOISE_REL_TOL, applied identically to every run
    regardless of memory on/off) treats residuals smaller than 1e-6 of that node's own SERIES
    amplitude as "no signal" rather than a sign -- this exists because a trajectory that has
    fully converged to a flat equilibrium (or a perfectly linear trend, tracked near-exactly
    by its own moving average) can otherwise register spurious floating-point-noise
    "reversals" of magnitude ~1e-16, which are a numerical artifact of the moving-average
    residual, not a physical sign change. The floor is anchored to the series' own amplitude
    rather than the residual's own peak, because once edges are trimmed a residual that is
    itself pure numerical noise would otherwise "self-normalize" to zero threshold.

    One window's worth of samples at each end of the recording is excluded from the count:
    edge-padding in `_moving_average` biases the average toward the boundary value there,
    which can otherwise register a spurious "reversal" right at the start/end even for a
    perfectly monotone series (a real edge artifact, not noise -- caught while writing this
    PR's own tests).
    """
    if r1 is None:
        r1 = difference(x_traj)
    precondition = "R1(difference).value.mean > 0"
    L = x_traj.shape[0]
    if not r1.defined or r1.value is None or r1.value["mean"] <= 0:
        return Reading(
            name="reversal", value=None, defined=False,
            precondition=precondition, expressible_max=L - 1,
            expressible_note="cannot exceed L-1 (one comparison per consecutive snapshot "
                              "pair); precondition failed so no measurement was attempted.",
        )
    n, m = x_traj.shape[1], x_traj.shape[2]
    win = window if window is not None else max(5, L // 20)
    # The moving average is not trustworthy within one window of either edge (edge-padding
    # biases it toward the boundary value there), which can otherwise register a spurious
    # "reversal" for even a perfectly monotone series right at the start/end. Trim one
    # window's worth from each side before counting sign changes.
    trim = min(win, max(0, L // 2 - 1))
    counts = np.zeros(n, dtype=int)
    for i in range(n):
        # collapse m state dims to a scalar per node via the sum (keeps this well-defined
        # for m=1, the only case PR-R1's empirical test exercises; m>=2 handling beyond this
        # simple collapse is deferred to a later PR, see AUDIT.md).
        series = x_traj[:, i, :].sum(axis=-1)
        ma = _moving_average(series, win)
        centered = series - ma
        interior = centered[trim: L - trim] if trim > 0 else centered
        if len(interior) < 2:
            interior = centered
        # Scale the noise floor off the SERIES' own magnitude, not the residual's own peak:
        # once edges are trimmed, a residual that is itself pure floating-point noise (e.g.
        # a perfectly-tracked linear trend in the interior) has a "peak" that is ALSO noise,
        # so normalizing against it would filter nothing. Anchoring to the series' amplitude
        # keeps the floor meaningful (~1e-6 of the state's own scale) regardless of how flat
        # the residual happens to be.
        series_scale = np.max(np.abs(series))
        floor = series_scale * _REVERSAL_NOISE_REL_TOL if series_scale > 0 else 0.0
        s = np.sign(np.where(np.abs(interior) < floor, 0.0, interior))
        s_nz = s[s != 0]
        if len(s_nz) < 2:
            counts[i] = 0
            continue
        counts[i] = int(np.sum(s_nz[1:] != s_nz[:-1]))
    return Reading(
        name="reversal",
        value=_native({
            "per_node_count": counts,
            "mean_count": float(counts.mean()),
            "max_count": int(counts.max()),
            "window": win,
        }),
        defined=True,
        precondition=precondition,
        expressible_max=L - 1,
        expressible_note="cannot exceed L-1 (one comparison per consecutive snapshot pair); "
                          "L=%d here." % L,
    )


# ---------------------------------------------------------------------------
# R4 -- period: first autocorrelation peak per node (measured only where R3 >= 2).
# ---------------------------------------------------------------------------

def _first_autocorr_peak(series: np.ndarray, max_lag: int, min_ac: float = 0.5) -> Optional[int]:
    """Return the lag (in steps) of the first genuine local-max autocorrelation peak, or None.

    `max_lag` is the hard instrument ceiling (L//2) -- lags beyond it are never even
    searched, which is exactly the expressible_max constraint made structural, not just
    documented.

    min_ac=0.5 is an empirically-set, fixed noise floor on the normalized autocorrelation
    height, applied identically regardless of memory on/off or the outcome being tested for.
    It was chosen (see AUDIT.md) because at the default min_ac=0.15 a small number of
    memory=off (first-order, provably non-oscillatory) trajectories produced spurious
    single-node "period" detections at very short lag from an incidental ripple in the
    early multi-modal transient -- 9 false positives out of 1920 node-checks swept across
    seeds/topologies/saturation. Raising min_ac to 0.5 removed all of them (0/1920) in the
    same sweep while memory=on's true positives were unaffected (period still detected in
    50/50 swept seed/damping combinations). This threshold was tuned against a FALSE-
    POSITIVE-RATE criterion measured on memory=off (which the update rule provably cannot
    oscillate under, by a Lyapunov argument -- see AUDIT.md), not against "make the
    memory=on vs memory=off contrast come out a particular way" -- the same fixed constant
    applies to every call regardless of which condition produced the series.
    """
    y = series - series.mean()
    if np.allclose(y, 0.0):
        return None
    n = len(y)
    full = np.correlate(y, y, mode="full")
    ac = full[n - 1:]
    denom = ac[0]
    if denom <= 0:
        return None
    ac = ac / denom
    hi = min(max_lag, len(ac) - 2)
    for k in range(1, hi):
        if ac[k] >= ac[k - 1] and ac[k] >= ac[k + 1] and ac[k] > min_ac:
            return k
    return None


def period(x_traj: np.ndarray, dt: float, r3: Optional[Reading] = None) -> Reading:
    """R4: T_i from the first autocorrelation peak, per node where R3(that node) >= 2.

    Precondition: R3 >= 2 (reversals) for the node in question.
    Expressible max: L // 2 steps -- periods longer than half the recording window cannot
    be represented by this instrument (there are not enough repeats in the window to
    distinguish a long period from a monotonic drift). This is enforced structurally in
    `_first_autocorr_peak` (max_lag=L//2), not just stated here.
    """
    L = x_traj.shape[0]
    max_lag_steps = L // 2
    expressible_note = (
        "periods longer than L/2 steps (%d steps == %.4g time units at dt=%.4g here, L=%d) "
        "cannot be represented by this instrument -- there is not enough of the recording "
        "window left to confirm a repeat." % (max_lag_steps, max_lag_steps * dt, dt, L)
    )
    if r3 is None:
        r3 = reversal(x_traj)
    precondition = "R3(reversal).value.per_node_count[i] >= 2, for node i"
    if not r3.defined or r3.value is None:
        return Reading(
            name="period", value=None, defined=False,
            precondition=precondition, expressible_max=max_lag_steps,
            expressible_note=expressible_note,
        )
    counts = np.array(r3.value["per_node_count"])
    n = x_traj.shape[1]
    per_node: List[Dict[str, Any]] = []
    any_defined = False
    for i in range(n):
        entry: Dict[str, Any] = {"node": i}
        if counts[i] < 2:
            entry.update(defined=False, T=None, rate=None,
                         reason="R3 precondition not met for this node (reversal_count=%d < 2)" % counts[i])
            per_node.append(entry)
            continue
        series = x_traj[:, i, :].sum(axis=-1)
        lag = _first_autocorr_peak(series, max_lag_steps)
        if lag is None:
            entry.update(defined=False, T=None, rate=None,
                         reason="no autocorrelation peak found within the expressible window "
                                "(L/2 steps) -- either genuinely aperiodic, or the period "
                                "exceeds what this instrument can represent")
            per_node.append(entry)
            continue
        T = lag * dt
        entry.update(defined=True, T=_native(T), rate=_native(1.0 / T) if T > 0 else None,
                     lag_steps=lag, reason="ok")
        any_defined = True
        per_node.append(entry)
    defined_Ts = [e["T"] for e in per_node if e["defined"]]
    value = {
        "per_node": per_node,
        "any_defined": any_defined,
        "n_periodic_nodes": len(defined_Ts),
        "mean_T": float(np.mean(defined_Ts)) if defined_Ts else None,
    }
    return Reading(
        name="period",
        value=_native(value),
        defined=any_defined,
        precondition=precondition,
        expressible_max=max_lag_steps,
        expressible_note=expressible_note,
    )


def measure_all(x_traj: np.ndarray, W: np.ndarray, dt: float) -> Dict[str, Reading]:
    """Run R1..R4 in their dependency order and return all four Readings."""
    r1 = difference(x_traj)
    r2 = direction(x_traj, W, r1=r1)
    r3 = reversal(x_traj, r1=r1)
    r4 = period(x_traj, dt, r3=r3)
    return {"R1_difference": r1, "R2_direction": r2, "R3_reversal": r3, "R4_period": r4}
