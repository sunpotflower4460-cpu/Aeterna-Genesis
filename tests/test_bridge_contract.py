"""Synthetic validation for genesis/diagnostics/bridge_contract.py (Vertical Emergence Contract
Gate I/II/III scaffolding, PR-1, role V). Checks the frozen arithmetic against hand-computed cases
-- no P10 physics data, no bridge is ever silently passed by omission.
"""
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


def test_gate_ii_pass_requires_all_four_criteria():
    status, detail = bc.gate_ii_effective_law(
        r_pred=0.05, seed_coeff_cv=0.10, n_seeds=6, closure_residual=0.10,
        n_scales=3, scale_ratio=4.0)
    assert status == "PASS"
    assert all(detail.values())


def test_gate_ii_fails_if_prediction_residual_too_large():
    status, detail = bc.gate_ii_effective_law(
        r_pred=0.20, seed_coeff_cv=0.10, n_seeds=6, closure_residual=0.10,
        n_scales=3, scale_ratio=4.0)
    assert status == "FAIL"
    assert detail["prediction"] is False
    assert detail["reproducibility"] is True   # other criteria still individually visible


def test_gate_ii_fails_if_too_few_seeds_even_with_low_cv():
    status, detail = bc.gate_ii_effective_law(
        r_pred=0.05, seed_coeff_cv=0.01, n_seeds=2, closure_residual=0.10,
        n_scales=3, scale_ratio=4.0)
    assert status == "FAIL"
    assert detail["reproducibility"] is False


def test_gate_ii_fails_if_scale_span_too_small():
    status, detail = bc.gate_ii_effective_law(
        r_pred=0.05, seed_coeff_cv=0.10, n_seeds=6, closure_residual=0.10,
        n_scales=3, scale_ratio=2.0)   # ratio below the frozen 4.0x minimum
    assert status == "FAIL"
    assert detail["scale_robustness"] is False


def test_gate_ii_uses_strict_less_than_at_the_boundary():
    # exactly AT the frozen threshold must FAIL (frozen contract says strict '<', not '<=').
    status, detail = bc.gate_ii_effective_law(
        r_pred=0.10, seed_coeff_cv=0.10, n_seeds=6, closure_residual=0.10,
        n_scales=3, scale_ratio=4.0)
    assert status == "FAIL"
    assert detail["prediction"] is False


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
