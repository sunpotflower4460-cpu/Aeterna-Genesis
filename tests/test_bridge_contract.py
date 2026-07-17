"""Synthetic validation for genesis/diagnostics/bridge_contract.py (Vertical Emergence Contract
Gate I/II/III scaffolding, PR-1, role V). Checks the frozen arithmetic against hand-computed cases
-- no P10 physics data, no bridge is ever silently passed by omission.
"""
import numpy as np

import genesis.diagnostics.bridge_contract as bc


def test_gate_i_pass_when_not_target_encoded():
    assert bc.gate_i_derivation(is_target_encoded=False) == "PASS"


def test_gate_i_fail_when_target_encoded():
    assert bc.gate_i_derivation(is_target_encoded=True) == "FAIL"


def test_gate_i_fails_closed_on_missing_or_non_bool_measurement():
    # a None/missing target_encoded measurement must never silently read as PASS.
    assert bc.gate_i_derivation(is_target_encoded=None) == "FAIL"
    assert bc.gate_i_derivation(is_target_encoded=0) == "FAIL"
    assert bc.gate_i_derivation(is_target_encoded="") == "FAIL"


def _gate_ii_pass_kwargs(**overrides):
    kwargs = dict(r_pred=0.05, seed_coeff_cv=0.10, n_seeds=6, closure_residual=0.10,
                  n_scales=3, scale_ratio=4.0, form_invariant_across_seeds=True,
                  form_invariant_across_scales=True)
    kwargs.update(overrides)
    return kwargs


def test_gate_ii_pass_requires_all_four_criteria():
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs())
    assert status == "PASS"
    assert all(detail.values())


def test_gate_ii_fails_if_prediction_residual_too_large():
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(r_pred=0.20))
    assert status == "FAIL"
    assert detail["prediction"] is False
    assert detail["reproducibility"] is True   # other criteria still individually visible


def test_gate_ii_fails_if_too_few_seeds_even_with_low_cv():
    status, detail = bc.gate_ii_effective_law(
        **_gate_ii_pass_kwargs(seed_coeff_cv=0.01, n_seeds=2))
    assert status == "FAIL"
    assert detail["reproducibility"] is False


def test_gate_ii_fails_if_scale_span_too_small():
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(scale_ratio=2.0))
    assert status == "FAIL"
    assert detail["scale_robustness"] is False


def test_gate_ii_uses_strict_less_than_at_the_boundary():
    # exactly AT the frozen threshold must FAIL (frozen contract says strict '<', not '<=').
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(r_pred=0.10))
    assert status == "FAIL"
    assert detail["prediction"] is False


def test_gate_ii_fails_closed_on_missing_numeric_metrics_without_raising():
    # a None metric must FAIL that criterion, never raise TypeError and abort the audit.
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(r_pred=None))
    assert status == "FAIL"
    assert detail["prediction"] is False
    status2, detail2 = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(closure_residual=None))
    assert status2 == "FAIL"
    assert detail2["closure"] is False
    status3, detail3 = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(n_scales=None))
    assert status3 == "FAIL"
    assert detail3["scale_robustness"] is False


def test_gate_ii_fails_closed_on_boolean_numeric_metrics():
    # a stray pass/fail flag passed where a real measurement was expected must FAIL, never
    # silently convert via float(True)==1.0 / float(False)==0.0 and satisfy the threshold.
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(r_pred=False))
    assert status == "FAIL"
    assert detail["prediction"] is False
    status2, detail2 = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(n_seeds=True))
    assert status2 == "FAIL"
    assert detail2["reproducibility"] is False


def test_gate_ii_fails_closed_on_numpy_boolean_metrics():
    # np.bool_ is NOT a Python bool subclass, so a naive isinstance(x, bool) check misses it --
    # must still be rejected, not silently converted via float(np.bool_(False))==0.0.
    status, detail = bc.gate_ii_effective_law(**_gate_ii_pass_kwargs(r_pred=np.bool_(False)))
    assert status == "FAIL"
    assert detail["prediction"] is False


def test_gate_ii_fails_if_function_form_not_invariant_across_seeds_despite_good_cv():
    # good CV/span numbers alone are NOT sufficient -- the frozen contract also requires the
    # measured effective law's functional FORM to stay the same across seeds (§2 II point 2).
    status, detail = bc.gate_ii_effective_law(
        **_gate_ii_pass_kwargs(form_invariant_across_seeds=False))
    assert status == "FAIL"
    assert detail["reproducibility"] is False


def test_gate_ii_fails_if_function_form_not_invariant_across_scales_despite_good_span():
    # same requirement across coarse-graining scales (§2 II point 4): a coarse-graining that
    # changes the effective law's functional form is "a specific coarse-graining's appearance,
    # not a real effective law" per the frozen contract's own FAIL condition.
    status, detail = bc.gate_ii_effective_law(
        **_gate_ii_pass_kwargs(form_invariant_across_scales=False))
    assert status == "FAIL"
    assert detail["scale_robustness"] is False


def test_gate_iii_pass_when_effect_present_and_absent_under_control():
    status, detail = bc.gate_iii_downward(
        effect_full=0.5, effect_matched_control=0.0, control_removes_downward_path=True)
    assert status == "PASS"
    assert detail["effect_full"] == 0.5


def test_gate_iii_fail_when_effect_also_present_under_control():
    status, _ = bc.gate_iii_downward(
        effect_full=0.5, effect_matched_control=0.3, control_removes_downward_path=True)
    assert status == "FAIL"


def test_gate_iii_fail_when_effect_absent_even_without_control():
    status, _ = bc.gate_iii_downward(
        effect_full=0.0, effect_matched_control=0.0, control_removes_downward_path=True)
    assert status == "FAIL"


def test_gate_iii_fails_closed_by_default_without_explicit_control_confirmation():
    # the caller must explicitly opt in with control_removes_downward_path=True; the default
    # must never silently PASS a Gate III claim (this was the exact class of bug caught once
    # already on the F0 -- Codex #5 -- and must not recur here).
    status, reason = bc.gate_iii_downward(effect_full=0.5, effect_matched_control=0.0)
    assert status == "FAIL"
    assert "matched control" in reason or "pathway" in reason


def test_gate_iii_fails_closed_on_missing_numeric_effect_without_raising():
    # a None/missing effect metric must FAIL, never raise TypeError and abort the audit.
    status, detail = bc.gate_iii_downward(
        effect_full=None, effect_matched_control=0.0, control_removes_downward_path=True)
    assert status == "FAIL"
    assert detail["effect_full"] is None
    status2, detail2 = bc.gate_iii_downward(
        effect_full=0.5, effect_matched_control=None, control_removes_downward_path=True)
    assert status2 == "FAIL"
    assert detail2["effect_matched_control"] is None


def test_gate_iii_fails_closed_on_boolean_effect_metrics():
    # if metadata plumbing passes pass/fail booleans instead of measured effect magnitudes,
    # float(True)==1.0/float(False)==0.0 must NOT let an unmeasured bridge silently reach PASS.
    status, detail = bc.gate_iii_downward(
        effect_full=True, effect_matched_control=False, control_removes_downward_path=True)
    assert status == "FAIL"
    assert detail["effect_full"] is None
    assert detail["effect_matched_control"] is None


def test_gate_iii_refuses_wrong_direction_control():
    # even if the numbers "look right", a control that does not target the claimed downward
    # pathway must never pass Gate III (the exact mistake caught by external review on the F0).
    status, reason = bc.gate_iii_downward(
        effect_full=0.5, effect_matched_control=0.0, control_removes_downward_path=False)
    assert status == "FAIL"
    assert "matched control" in reason or "pathway" in reason


def test_bridge_level_caps_at_last_passed_gate():
    assert bc.bridge_level("FAIL", "PASS", "PASS") == "B0"
    assert bc.bridge_level("PASS", "FAIL", "PASS") == "B1"
    assert bc.bridge_level("PASS", "PASS", "FAIL") == "B2"
    assert bc.bridge_level("PASS", "PASS", "PASS") == "B3"


def test_bridge_level_never_guesses_upward_from_pending():
    # a 'pending' (not yet measured) gate must never be treated as PASS.
    assert bc.bridge_level("PASS", "pending", "PASS") == "B1"
