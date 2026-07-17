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
  >= 5 independent seeds, coefficient CV < 0.15
  closure residual < 0.20
  >= 3 coarse-graining scales, spanning >= 4x in block length

WHAT IT IS NOT
Not a physics model, not an automatic upgrader -- callers must supply real measured quantities;
this module only applies the frozen arithmetic honestly and reports which specific criterion, if
any, failed.
"""
import numpy as np

# Frozen defaults (VERTICAL_EMERGENCE_CONTRACT.md Section 2, Gate II). Do not loosen after seeing
# results -- override only via an explicit, documented `thresholds` argument, per-run.
GATE_II_DEFAULTS = dict(r_pred_max=0.10, min_seeds=5, coeff_cv_max=0.15,
                         closure_residual_max=0.20, min_scales=3, min_scale_ratio=4.0)


def gate_i_derivation(is_target_encoded):
    """Gate I: PASS iff the upper variable was derived from lower state (target_encoded=False) --
    the 8th-audit `target_encoded` discipline generalized across scales (contract Section 2, I)."""
    return "FAIL" if is_target_encoded else "PASS"


def gate_ii_effective_law(r_pred, seed_coeff_cv, n_seeds, closure_residual, n_scales, scale_ratio,
                           thresholds=None):
    """Gate II: PASS iff ALL FOUR frozen criteria hold simultaneously (contract Section 2, II).
    Returns (status, detail) where `detail` is a dict of {criterion: bool} -- callers always see
    exactly which criterion failed, never a bare boolean that hides partial credit."""
    t = dict(GATE_II_DEFAULTS)
    if thresholds:
        t.update(thresholds)
    checks = dict(
        prediction=bool(r_pred <= t["r_pred_max"]),
        reproducibility=bool(n_seeds >= t["min_seeds"] and seed_coeff_cv <= t["coeff_cv_max"]),
        closure=bool(closure_residual <= t["closure_residual_max"]),
        scale_robustness=bool(n_scales >= t["min_scales"] and scale_ratio >= t["min_scale_ratio"]),
    )
    status = "PASS" if all(checks.values()) else "FAIL"
    return status, checks


def gate_iii_downward(effect_full, effect_matched_control, control_removes_downward_path=True,
                       tol=1e-9):
    """Gate III: PASS iff the claimed downward (upper-state -> lower-level) effect is present in
    the Full run AND ABSENT under the matched control that removes the U->lower-level pathway
    while preserving lower-level statistics (contract Section 2, III). The caller must explicitly
    confirm `control_removes_downward_path=True` -- i.e. the EXPERIMENT DESIGN (not this function)
    guarantees the control targets the correct (downward, not upward) pathway; this refuses to
    pass a Gate III claim built on the wrong control (see F0's Codex #5: an earlier P10 draft
    accidentally froze the upward m->interface path instead of the downward one)."""
    if not control_removes_downward_path:
        return "FAIL", "control does not remove the claimed downward pathway (matched control mismatch)"
    effect_present = abs(effect_full) > tol
    effect_absent_under_control = abs(effect_matched_control) <= tol
    status = "PASS" if (effect_present and effect_absent_under_control) else "FAIL"
    return status, dict(effect_full=float(effect_full), effect_matched_control=float(effect_matched_control))


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
