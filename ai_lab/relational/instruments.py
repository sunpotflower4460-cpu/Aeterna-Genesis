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
from scipy.signal import hilbert

from ai_lab.relational import winding_precheck


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

# Fixed, disclosed tolerance band for the envelope sustained/decaying/growing classification
# below (PR-R1.5). Same constant for every run regardless of outcome -- not tuned per call.
_ENVELOPE_SUSTAIN_TOL = 0.15

# PR-R1.9: fixed, disclosed tolerance for `settled` (see _envelope_trend docstring) -- a
# narrower, trailing-quarter-only check, deliberately independent of _ENVELOPE_SUSTAIN_TOL's
# whole-window halves comparison. Same constant for every call regardless of outcome.
_ENVELOPE_SETTLED_TOL = 0.10
_ENVELOPE_SETTLED_MIN_LEN = 16  # need >=4 samples per quarter for the trailing-quarter check to mean anything


def _envelope_trend(series: np.ndarray, trim: int) -> Dict[str, Any]:
    """PR-R1.5: is an oscillation SUSTAINED, DECAYING, or GROWING, distinct from whether a
    period was detected at all (R4's own question). PR-R1.9 adds `settled`, a narrower and
    independent check (see below).

    Rationale (per review): with memory=off and no damping term, the classic route to
    "period without memory" is a directed loop whose linear operator has a genuinely
    imaginary eigenvalue (a sustained limit-cycle-like oscillation) -- but a MUCH more common
    outcome for a linear system relaxing toward a fixed point is a damped spiral: the
    envelope shrinks toward zero even though R4's autocorrelation peak still finds a period.
    Reporting only "period: defined=True" would conflate these. This function distinguishes
    them without ever computing or reporting a PHASE angle (forbidden vocabulary, spec
    Sec.5, until R7 exists) -- only the analytic-signal MAGNITUDE (envelope) is used; the
    angle half of the Hilbert transform is discarded unread.

    Method: Hilbert-transform envelope |analytic_signal(series - mean)| over the same
    edge-trimmed interior window R3 already uses (edge-padding bias applies here too), split
    into first/second half, compare mean envelope magnitude between halves. Tolerance
    (_ENVELOPE_SUSTAIN_TOL = 15%) is fixed and disclosed, identical for every call.

    `settled` (PR-R1.9) asks a DIFFERENT question than `sustained`: not "is the whole
    window's amplitude roughly the same at the end as at the start" but "has the amplitude
    actually stopped moving by the time the recording stopped". A trajectory that is still
    climbing toward its eventual limit-cycle amplitude (e.g. shortly after linear instability
    crosses q^2 > p*gamma^2, AUDIT.md Sec.10.3) can pass the whole-window halves check --
    most of the window is already near-plateau -- while its TRAILING quarter is still
    trending upward. Treating that as equivalent to a genuine plateau would make the same
    mistake review flagged for decaying transients, just on the growing side: deriving
    structure (a future PR's phase/winding) from a still-changing amplitude, not a settled
    one. `settled` compares the mean envelope of the LAST quarter of the window against the
    quarter immediately before it (not the whole first half) -- only a node whose amplitude
    has plateaued specifically at the END of the recorded window is settled, independent of
    what the whole-window `sustained` classification says. Fixed tolerance
    _ENVELOPE_SETTLED_TOL=10%, needs >=_ENVELOPE_SETTLED_MIN_LEN=16 interior samples (>=4 per
    quarter) or is reported False (insufficient resolution to judge, not "unsettled").
    """
    y = series - series.mean()
    interior = y[trim: len(y) - trim] if trim > 0 else y
    if len(interior) < 8 or np.allclose(interior, 0.0):
        return {"ratio": None, "classification": "undefined", "sustained": False,
                "settled": False, "settled_ratio": None,
                "note": "interior window too short or flat to estimate an envelope"}
    env = np.abs(hilbert(interior))       # magnitude only -- angle() is never called
    half = len(env) // 2
    a1 = float(env[:half].mean())
    a2 = float(env[half:].mean())
    if a1 <= 0.0:
        return {"ratio": None, "classification": "undefined", "sustained": False,
                "settled": False, "settled_ratio": None,
                "note": "first-half envelope amplitude is zero"}
    ratio = a2 / a1
    if ratio < 1.0 - _ENVELOPE_SUSTAIN_TOL:
        cls = "decaying"
    elif ratio > 1.0 + _ENVELOPE_SUSTAIN_TOL:
        cls = "growing"
    else:
        cls = "sustained"

    settled = False
    settled_ratio = None
    if len(env) >= _ENVELOPE_SETTLED_MIN_LEN:
        quarter = len(env) // 4
        q3 = float(env[-2 * quarter:-quarter].mean())
        q4 = float(env[-quarter:].mean())
        if q3 > 0.0:
            settled_ratio = q4 / q3
            settled = abs(settled_ratio - 1.0) <= _ENVELOPE_SETTLED_TOL

    return {"ratio": _native(ratio), "classification": cls, "sustained": cls == "sustained",
            "settled": bool(settled), "settled_ratio": _native(settled_ratio),
            "note": "second-half/first-half mean Hilbert-envelope magnitude ratio, tol=%.2f; "
                    "settled = last-quarter/third-quarter magnitude ratio within tol=%.2f "
                    "of 1 (trailing-window trend check, independent of the halves ratio "
                    "above)" % (_ENVELOPE_SUSTAIN_TOL, _ENVELOPE_SETTLED_TOL)}


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
    envelopes: List[Dict[str, Any]] = []
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
        else:
            counts[i] = int(np.sum(s_nz[1:] != s_nz[:-1]))
        # PR-R1.5: general envelope trend for this node, independent of whether R4 later
        # finds a period -- lets a caller see "growing/decaying/sustained fluctuation" even
        # on a node R4 will reject for having too few reversals.
        envelopes.append({"node": i, **_envelope_trend(series, trim)})
    return Reading(
        name="reversal",
        value=_native({
            "per_node_count": counts,
            "mean_count": float(counts.mean()),
            "max_count": int(counts.max()),
            "per_node_envelope": envelopes,
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
    # Same window/trim convention as R3 (reversal), so the envelope's edge-trim matches the
    # window this instrument's own precondition (R3) was computed with.
    win = max(5, L // 20)
    trim = min(win, max(0, L // 2 - 1))
    per_node: List[Dict[str, Any]] = []
    any_defined = False
    any_sustained = False
    any_settled_sustained = False
    for i in range(n):
        entry: Dict[str, Any] = {"node": i}
        if counts[i] < 2:
            entry.update(defined=False, T=None, rate=None, sustained=False, settled=False,
                         reason="R3 precondition not met for this node (reversal_count=%d < 2)" % counts[i])
            per_node.append(entry)
            continue
        series = x_traj[:, i, :].sum(axis=-1)
        lag = _first_autocorr_peak(series, max_lag_steps)
        if lag is None:
            entry.update(defined=False, T=None, rate=None, sustained=False, settled=False,
                         reason="no autocorrelation peak found within the expressible window "
                                "(L/2 steps) -- either genuinely aperiodic, or the period "
                                "exceeds what this instrument can represent")
            per_node.append(entry)
            continue
        T = lag * dt
        # PR-R1.5: a period being DETECTED (autocorrelation peak found) does not mean it is
        # SUSTAINED -- a damped spiral relaxing to a fixed point also produces a genuine,
        # detectable autocorrelation peak while its amplitude shrinks to zero. `sustained`
        # is always carried explicitly alongside `defined` so a later PR (R7's phase
        # derivation) does not mistake a decaying transient's ripple for structure.
        # PR-R1.9: `settled` is carried alongside `sustained` for the same reason, on the
        # opposite failure mode -- a node that is still growing into its eventual limit-cycle
        # amplitude can pass the whole-window `sustained` check while its trailing edge is
        # still moving (see _envelope_trend's docstring). R7/R8 must gate on
        # `sustained AND settled`, not `sustained` alone.
        env = _envelope_trend(series, trim)
        sustained_and_settled = bool(env["sustained"]) and bool(env["settled"])
        entry.update(defined=True, T=_native(T), rate=_native(1.0 / T) if T > 0 else None,
                     lag_steps=lag, reason="ok", sustained=bool(env["sustained"]),
                     settled=bool(env["settled"]), sustained_and_settled=sustained_and_settled,
                     envelope=env)
        any_defined = True
        any_sustained = any_sustained or env["sustained"]
        any_settled_sustained = any_settled_sustained or sustained_and_settled
        per_node.append(entry)
    defined_Ts = [e["T"] for e in per_node if e["defined"]]
    sustained_Ts = [e["T"] for e in per_node if e["defined"] and e["sustained"]]
    settled_sustained_Ts = [e["T"] for e in per_node if e["defined"] and e.get("sustained_and_settled")]
    value = {
        "any_sustained": any_sustained,
        "n_sustained_periodic_nodes": len(sustained_Ts),
        "any_settled_sustained": any_settled_sustained,
        "n_settled_sustained_periodic_nodes": len(settled_sustained_Ts),
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


# ---------------------------------------------------------------------------
# R7 -- phase: unwrapped Hilbert-transform phase per node (spec Sec.6/Sec.5). PR-R2.2, the
# first instrument in this codebase licensed to compute/report "phase"/位相 (spec Sec.5's
# forbidden-vocabulary rule) -- gated on R4's `sustained_and_settled`, so only a node R4
# already confirmed to be genuinely oscillating and plateaued (not decaying, not still
# growing) is eligible.
# ---------------------------------------------------------------------------

def _phase_analysis_window(L: int) -> "tuple[int, int]":
    """Fixed rule (PR-R2.2, AUDIT.md Sec.14.4), same location as the R3 moving-average
    edge-bias fix -- NOT a tunable parameter: the phase-analysis window is the LAST HALF of
    the recording (discarding the entire initial transient, not just the Hilbert-transform
    edge), further trimmed by R3/R4's own edge-trim formula at both new boundaries of that
    half (the slice x[L//2:] creates a fresh boundary at L//2 that is not a real edge of the
    physical trajectory, so it needs the same edge-padding-bias trim R3/R4 apply at the
    recording's actual ends).

    Rationale for "last half" specifically (not some other fraction): this is exactly the
    boundary `_envelope_trend`'s `settled` check already treats as "the region worth
    trusting" -- its own trailing-quarter-vs-third-quarter comparison operates entirely
    within this same half. Phase needs a genuinely non-transient signal at least as much as
    `settled`'s coarser flatness check does, so it reuses that already-established boundary
    rather than introducing a second, independently-tunable one.
    """
    half_start = L // 2
    half_len = L - half_start
    win = max(5, L // 20)
    trim = min(win, max(0, half_len // 2 - 1))
    return half_start + trim, L - trim


def phase(x_traj: np.ndarray, dt: float, r4: Optional[Reading] = None) -> Reading:
    """R7: unwrapped analytic-signal phase per node, restricted to `_phase_analysis_window`.

    Precondition: R4(period).value.per_node[i].sustained_and_settled -- a node R4 found
    decaying, still-growing, or simply aperiodic has no repeating structure for "phase" to
    describe. This is this INSTRUMENT's own gate; a caller that wants the stronger,
    interventionally-confirmed claim (AUDIT.md Sec.13's attractor-vs-orbit-family
    distinction) must additionally apply `verify.verify_long_window` /
    `verify.check_attractor_recovery` before trusting a `phase` Reading as describing a
    genuine self-sustaining structure rather than merely a screening-window-sustained one --
    this instrument alone cannot see that distinction (AUDIT.md Sec.13.3/13.7).

    `mean_rate_from_phase` (cycles per time unit, i.e. d(unwrapped_phase)/dt / (2*pi)) is
    reported alongside R4's own `rate` (1/T from the autocorrelation peak) as a built-in
    cross-check -- two independent measurements of the same underlying quantity, from
    different math (peak-picking vs. phase unwrapping), on the same trajectory.
    """
    if r4 is None:
        r4 = period(x_traj, dt)
    precondition = "R4(period).value.per_node[i].sustained_and_settled, for node i"
    L = x_traj.shape[0]
    lo, hi = _phase_analysis_window(L)
    expressible_note = (
        "phase is computed only on the last-half, edge-trimmed interior (steps %d:%d of "
        "%d total) -- the discarded first half is presumed transient, not analyzed; a "
        "period whose transient extends past the halfway point cannot be represented "
        "faithfully by this instrument." % (lo, hi, L)
    )
    if not r4.defined or r4.value is None:
        return Reading(
            name="phase", value=None, defined=False, precondition=precondition,
            expressible_max=hi - lo, expressible_note=expressible_note,
        )
    n = x_traj.shape[1]
    per_node: List[Dict[str, Any]] = []
    any_defined = False
    for i in range(n):
        entry: Dict[str, Any] = {"node": i}
        r4_entry = r4.value["per_node"][i] if i < len(r4.value["per_node"]) else {}
        if not r4_entry.get("sustained_and_settled", False):
            entry.update(defined=False, unwrapped_phase_span=None, mean_rate_from_phase=None,
                         reason="R4 precondition not met for this node (not sustained_and_settled)")
            per_node.append(entry)
            continue
        series = x_traj[:, i, :].sum(axis=-1)
        interior = series[lo:hi]
        if len(interior) < 16 or np.allclose(interior - interior.mean(), 0.0):
            entry.update(defined=False, unwrapped_phase_span=None, mean_rate_from_phase=None,
                         reason="analysis window too short or flat after the transient+edge trim")
            per_node.append(entry)
            continue
        y = interior - interior.mean()
        analytic = hilbert(y)
        wrapped = np.angle(analytic)      # first read of the analytic-signal angle in this codebase
        unwrapped = np.unwrap(wrapped)
        span = float(unwrapped[-1] - unwrapped[0])
        duration = (len(interior) - 1) * dt
        mean_rate = span / (2.0 * np.pi * duration) if duration > 0 else None
        entry.update(defined=True, unwrapped_phase_span=_native(span),
                     mean_rate_from_phase=_native(mean_rate), reason="ok")
        any_defined = True
        per_node.append(entry)
    value = {
        "per_node": per_node,
        "any_defined": any_defined,
        "analysis_window": [int(lo), int(hi)],
        "transient_trim_rule": "last_half_of_recording_plus_edge_trim",
    }
    return Reading(
        name="phase", value=_native(value), defined=any_defined,
        precondition=precondition, expressible_max=hi - lo, expressible_note=expressible_note,
    )


# ---------------------------------------------------------------------------
# R8 -- winding: discrete winding number of the snapshot phase around a caller-supplied
# cycle (PR-R6, AUDIT.md Sec.25.6). Gated on R4's `sustained_and_settled` for every node in
# the cycle, exactly as R7 is gated for a single node -- a cycle containing even one node R4
# found decaying, still-growing, or aperiodic has no settled structure for "winding" to
# describe on that cycle.
# ---------------------------------------------------------------------------

def winding(x_traj: np.ndarray, dt: float, cycles: List[List[int]],
            r4: Optional[Reading] = None) -> Reading:
    """R8: discrete winding number (and smoothness gate) of the single-instant snapshot
    phase around each caller-supplied cycle.

    `cycles` is a list of node-index lists, each already a closed walk in the relation
    graph (e.g. `topology.fundamental_cycles(W)`, or a wider simple-cycle enumeration) --
    this instrument does not itself discover cycles, does not import `topology`, and does
    not judge whether a given list of node indices is actually a cycle of W. That split
    mirrors R7's own division of labor: an instrument measures on what it is given, it does
    not decide what is worth measuring.

    Precondition: R4(period).value.per_node[i].sustained_and_settled must hold for EVERY
    node i in a cycle before that cycle's winding is computed -- a single unsettled node
    anywhere on the loop means the "instantaneous phase" sampled at the window midpoint is
    not describing a plateaued structure for at least one node on the loop, so the whole
    cycle's reading is `defined=False` for that cycle (not silently dropped from `cycles`;
    every cycle passed in gets an entry, with a `reason` when undefined).

    Method (identical to every manual analysis script from PR-R2.3 onward, and to
    `verify`'s own winding-adjacent checks, so this instrument reproduces exactly what has
    already been measured by hand rather than a new formula): for each node in the cycle,
    take the analytic-signal (Hilbert transform) phase angle at the MIDPOINT of
    `_phase_analysis_window(L)` -- a single instantaneous snapshot, not R7's unwrapped span
    -- then feed the resulting phase array (in the cycle's fixed graph order) to
    `winding_precheck.compute_winding` / `is_smooth_winding`.

    CRITICAL DISCLOSURE (mirrors R7's own, and is the entire reason this instrument cannot
    be used alone to report a "winding structure exists" claim): this instrument only sees
    whatever `x_traj` it is given. It has no way to know whether that trajectory came from a
    run long enough to satisfy `winding_precheck.WINDING_CANDIDACY_MIN_EXTEND_FACTOR` (30x
    the base window) -- the STRUCTURAL discipline PR-R6 established after four separate
    short-window false-positive recurrences (605/1200, 116/600, 119 missed-detection nodes,
    3/5 of PR-R5's wide-basis candidates; see `winding_precheck`'s module docstring). A
    caller that wants the disciplined, reportable-as-candidate claim must run `substrate.run`
    at `extend_factor >= WINDING_CANDIDACY_MIN_EXTEND_FACTOR` (or equivalent) BEFORE calling
    this instrument, exactly as `verify.verify_long_window_all_nodes` is the layer that owns
    window-extension/robustness logic for R4 -- this instrument does not, and cannot, verify
    that on its own. A `defined=True, is_smooth_winding=True` entry from THIS instrument
    alone is a raw measurement on the given trajectory, nothing more; it is not, by itself,
    a disciplined candidate report.
    """
    if r4 is None:
        r4 = period(x_traj, dt)
    precondition = ("R4(period).value.per_node[i].sustained_and_settled, for every node i "
                     "in the cycle")
    L = x_traj.shape[0]
    lo, hi = _phase_analysis_window(L)
    mid = (lo + hi) // 2
    expressible_note = (
        "phase is sampled at a single instant (the midpoint of the last-half, edge-trimmed "
        "window used by R7, steps %d:%d of %d total, sampled at step %d); per cycle of "
        "length N, the wrapped-difference sum used by compute_winding cannot exceed N*pi in "
        "magnitude, so |winding| <= N//2 for that cycle (see each entry's "
        "max_possible_abs_winding) -- this is a structural ceiling of the discrete winding "
        "formula itself, independent of what phases actually occur. This instrument also "
        "cannot verify the WINDING_CANDIDACY_MIN_EXTEND_FACTOR (30x) window-robustness "
        "discipline on its own; see docstring." % (lo, hi, L, mid)
    )
    if not r4.defined or r4.value is None:
        return Reading(
            name="winding", value=None, defined=False, precondition=precondition,
            expressible_max=None, expressible_note=expressible_note,
        )
    per_node_r4 = r4.value["per_node"]
    n_nodes = x_traj.shape[1]

    def _sustained_and_settled(node: int) -> bool:
        if node < 0 or node >= len(per_node_r4):
            return False
        return bool(per_node_r4[node].get("sustained_and_settled", False))

    per_cycle: List[Dict[str, Any]] = []
    any_defined = False
    any_smooth = False
    for cycle in cycles:
        entry: Dict[str, Any] = {"cycle": list(cycle), "length": len(cycle)}
        if len(cycle) < 1 or any(node < 0 or node >= n_nodes for node in cycle):
            entry.update(defined=False, reason="cycle references a node index outside [0, N)",
                         all_sustained_and_settled=False, winding=None,
                         max_adjacent_step=None, is_smooth_winding=None,
                         max_possible_abs_winding=None)
            per_cycle.append(entry)
            continue
        all_ok = all(_sustained_and_settled(node) for node in cycle)
        entry["all_sustained_and_settled"] = all_ok
        entry["max_possible_abs_winding"] = len(cycle) // 2
        if not all_ok:
            entry.update(defined=False, winding=None, max_adjacent_step=None,
                         is_smooth_winding=None,
                         reason="R4 precondition not met for at least one node on this cycle "
                                "(not sustained_and_settled)")
            per_cycle.append(entry)
            continue
        phases = []
        for node in cycle:
            series = x_traj[lo:hi, node, :].sum(axis=-1)
            analytic = hilbert(series)
            phases.append(float(np.angle(analytic)[mid - lo]))
        phi = np.array(phases)
        w = winding_precheck.compute_winding(phi)
        max_step = winding_precheck.max_adjacent_step(phi)
        smooth = winding_precheck.is_smooth_winding(phi)
        entry.update(defined=True, reason="ok", winding=int(w),
                     max_adjacent_step=_native(max_step), is_smooth_winding=bool(smooth),
                     phase_at_midpoint=_native(phi))
        any_defined = True
        any_smooth = any_smooth or smooth
        per_cycle.append(entry)

    value = {
        "per_cycle": per_cycle,
        "any_defined": any_defined,
        "any_smooth_winding": any_smooth,
        "n_cycles_checked": len(cycles),
        "n_defined": sum(1 for e in per_cycle if e["defined"]),
        "n_smooth_winding": sum(1 for e in per_cycle if e.get("is_smooth_winding")),
        "analysis_window": [int(lo), int(hi)],
        "phase_sample_index": int(mid),
    }
    return Reading(
        name="winding", value=_native(value), defined=any_defined, precondition=precondition,
        expressible_max=None, expressible_note=expressible_note,
    )


def measure_all(x_traj: np.ndarray, W: np.ndarray, dt: float,
                 cycles: Optional[List[List[int]]] = None) -> Dict[str, Reading]:
    """Run R1..R4, R7, and (if `cycles` is given) R8 in their dependency order and return
    all Readings. `cycles` is optional and caller-supplied (see `winding`'s docstring for
    why this instrument does not discover cycles itself) -- when omitted, R8 is not run at
    all rather than silently defaulting to some cycle basis choice."""
    r1 = difference(x_traj)
    r2 = direction(x_traj, W, r1=r1)
    r3 = reversal(x_traj, r1=r1)
    r4 = period(x_traj, dt, r3=r3)
    r7 = phase(x_traj, dt, r4=r4)
    result = {"R1_difference": r1, "R2_direction": r2, "R3_reversal": r3, "R4_period": r4,
              "R7_phase": r7}
    if cycles is not None:
        result["R8_winding"] = winding(x_traj, dt, cycles, r4=r4)
    return result
