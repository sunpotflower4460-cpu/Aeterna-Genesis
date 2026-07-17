#!/usr/bin/env python3
"""Vertical Emergence Contract Gate I/II/III check scaffolding (`docs/VERTICAL_EMERGENCE_CONTRACT.md`
Section 2), implemented as code so a bridge's Bridge-Level is MACHINE-CHECKED against the frozen,
pre-registered thresholds, never eyeballed from prose or set by hand.

WHAT IT IS
Three gate-check functions plus a conservative Bridge-Level (B0-B3) summarizer. No bridge is ever
reported 'passed'/'B2'/'B3' by this module unless real, caller-supplied measurements pass EVERY
frozen criterion; a missing or incomplete measurement is always 'FAIL' (never silently 'PASS' by
omission). This directly encodes the caution the P10 F0 itself states: "V0は固定球なので、器の
Bridge Gateをpassedにしない" ("V0 is a fixed sphere, so the vessel's Bridge Gate is never passed") --
i.e. even a working measurement instrument does not, by itself, pass any gate about the vessel's
formation; only actual S1/E2/E3 physics data can.

Frozen Gate II thresholds (contract Section 2, "決定的閾値", not to be loosened after seeing results):
  R_pred < 0.10 (normalized prediction residual)
  >= 5 independent seeds, coefficient CV < 0.15, AND function form invariant across seeds
  closure residual < 0.20
  >= 3 coarse-graining scales, spanning >= 4x in block length, AND function form invariant
    across scales

WHAT IT IS NOT
Not a physics model, not an automatic upgrader -- callers must supply real measured quantities;
this module only applies the frozen arithmetic honestly and reports which specific criterion, if
any, failed.
"""
import numpy as np
import types

# Frozen thresholds (VERTICAL_EMERGENCE_CONTRACT.md Section 2, Gate II). Not overridable at
# call-time by design -- see gate_ii_effective_law's docstring. MappingProxyType enforces that
# immutability at RUNTIME too (CodeRabbit): a plain dict stays mutable even though the module's
# whole point is that these thresholds never change after being seen.
GATE_II_DEFAULTS = types.MappingProxyType(dict(
    r_pred_max=0.10, min_seeds=5, coeff_cv_max=0.15,
    closure_residual_max=0.20, min_scales=3, min_scale_ratio=4.0))


def gate_i_derivation(is_target_encoded):
    """Gate I: PASS iff the upper variable was derived from lower state (target_encoded=False) --
    the 8th-audit `target_encoded` discipline generalized across scales (contract Section 2, I).
    Fails CLOSED on anything but an explicit bool: a missing/None measurement must never read as
    PASS by a falsy-value accident (this module's own no-silent-pass principle, Section headline)."""
    if not isinstance(is_target_encoded, bool):
        return "FAIL"
    return "FAIL" if is_target_encoded else "PASS"


def _num_lt(x, bound):
    """True iff x is a real number (NOT a bool) strictly less than bound; False (never a raised
    TypeError) for None/missing/non-numeric/boolean x -- a missing measurement must FAIL the
    criterion, not crash gate evaluation (Codex: bare `x < bound` on a None metric aborts the
    whole audit with a TypeError instead of returning the conservative FAIL this module's own
    no-silent-omission rule promises). Booleans are rejected explicitly: `bool` is a Python `int`
    subclass, so `float(True)==1.0`/`float(False)==0.0` would otherwise let a mistakenly-passed
    pass/fail flag silently satisfy a numeric threshold (Codex)."""
    if isinstance(x, bool):
        return False
    try:
        return x is not None and float(x) < bound
    except (TypeError, ValueError):
        return False


def _num_ge(x, bound):
    """True iff x is a real number (NOT a bool) >= bound; False for None/missing/non-numeric/
    boolean x (see `_num_lt`)."""
    if isinstance(x, bool):
        return False
    try:
        return x is not None and float(x) >= bound
    except (TypeError, ValueError):
        return False


def gate_ii_effective_law(r_pred, seed_coeff_cv, n_seeds, closure_residual, n_scales, scale_ratio,
                           form_invariant_across_seeds, form_invariant_across_scales):
    """Gate II: PASS iff ALL FOUR frozen criteria hold simultaneously (contract Section 2, II).
    Returns (status, detail) where `detail` is a dict of {criterion: bool} -- callers always see
    exactly which criterion failed, never a bare boolean that hides partial credit. Thresholds are
    NOT overridable by callers (no `thresholds` parameter): a per-call override would let a result
    seen after the fact quietly loosen the frozen decision criteria, defeating the exact discipline
    this module exists to enforce ("結果を見た後の成功条件変更を禁止する"). Comparisons use the
    frozen contract's strict `<` (not `<=`) at every boundary, and fail closed (never raise) on a
    missing/non-numeric measurement.

    `reproducibility` and `scale_robustness` are each TWO-part criteria per the frozen contract
    (§2 II, points 2 and 4): the numeric CV/span check ALONE is insufficient -- the measured
    effective law's FUNCTIONAL FORM (not just its coefficients) must also stay invariant across
    seeds (point 2: "かつ関数形が同一") and across coarse-graining scales (point 4: "関数形が不変").
    Callers must explicitly measure and pass `form_invariant_across_seeds`/`form_invariant_across_
    scales` as real booleans (Codex: an earlier version of this gate would PASS a coarse-graining
    that silently changed functional form as long as the CV/span numbers alone looked fine --
    exactly the "特定粗視化の見かけ" (an artifact of one particular coarse-graining, not a real
    effective law) the frozen contract's FAIL condition explicitly warns against)."""
    t = GATE_II_DEFAULTS
    checks = dict(
        prediction=_num_lt(r_pred, t["r_pred_max"]),
        reproducibility=bool(_num_ge(n_seeds, t["min_seeds"]) and _num_lt(seed_coeff_cv, t["coeff_cv_max"])
                              and form_invariant_across_seeds is True),
        closure=_num_lt(closure_residual, t["closure_residual_max"]),
        scale_robustness=bool(_num_ge(n_scales, t["min_scales"]) and _num_ge(scale_ratio, t["min_scale_ratio"])
                               and form_invariant_across_scales is True),
    )
    status = "PASS" if all(checks.values()) else "FAIL"
    return status, checks


def _safe_float(x):
    """float(x), or None for None/non-numeric/boolean x (never raises) -- used so a missing Gate
    III metric can still be reported in `detail` without crashing (see `gate_iii_downward`).
    Booleans rejected explicitly (see `_num_lt`): a stray pass/fail flag must not silently convert
    to `1.0`/`0.0` and be treated as a real measured effect magnitude (Codex)."""
    if isinstance(x, bool):
        return None
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def gate_iii_downward(effect_full, effect_matched_control, control_removes_downward_path=False,
                       tol=1e-9):
    """Gate III: PASS iff the claimed downward (upper-state -> lower-level) effect is present in
    the Full run AND ABSENT under the matched control that removes the U->lower-level pathway
    while preserving lower-level statistics (contract Section 2, III). The caller must explicitly
    confirm `control_removes_downward_path=True` -- i.e. the EXPERIMENT DESIGN (not this function)
    guarantees the control targets the correct (downward, not upward) pathway; this refuses to
    pass a Gate III claim built on the wrong control (see F0's Codex #5: an earlier P10 draft
    accidentally froze the upward m->interface path instead of the downward one). Fails closed
    (never raises) on a None/non-numeric effect metric, matching `gate_ii_effective_law`'s
    `_num_lt`/`_num_ge` discipline -- a missing measurement must FAIL, not abort the audit with a
    TypeError (Codex)."""
    if not control_removes_downward_path:
        return "FAIL", "control does not remove the claimed downward pathway (matched control mismatch)"
    ef = _safe_float(effect_full)
    emc = _safe_float(effect_matched_control)
    effect_present = ef is not None and abs(ef) > tol
    effect_absent_under_control = emc is not None and abs(emc) <= tol
    status = "PASS" if (effect_present and effect_absent_under_control) else "FAIL"
    return status, dict(effect_full=ef, effect_matched_control=emc)


def bridge_level(gate_i_status, gate_ii_status, gate_iii_status):
    """Conservative summary Bridge-Level (B0-B3): each gate must PASS for its level to be claimed;
    a non-PASS gate caps the level at the last one actually passed -- never guesses upward from an
    untested gate (contract Section 1)."""
    if gate_i_status != "PASS":
        return "B0"
    if gate_ii_status != "PASS":
        return "B1"
    if gate_iii_status != "PASS":
        return "B2"
    return "B3"
