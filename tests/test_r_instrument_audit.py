"""Tests for ai_lab/relational/instrument_audit.py -- the 9th audit (spec Sec.8)."""

import numpy as np
import pytest

from ai_lab.relational import instrument_audit, instruments, substrate


def _defined_reading(expressible_max=100):
    return instruments.Reading(
        name="R4_period", value={"mean_T": 3.0}, defined=True,
        precondition="R3 >= 2", expressible_max=expressible_max,
        expressible_note="periods longer than L/2 steps cannot be represented",
    )


def _undefined_reading(expressible_max=100):
    return instruments.Reading(
        name="R4_period", value=None, defined=False,
        precondition="R3 >= 2", expressible_max=expressible_max,
        expressible_note="periods longer than L/2 steps cannot be represented",
    )


def test_q1_precondition_not_met_is_instrument_limited():
    """A None from an unmet precondition must never license 'did not reach X'."""
    r = _undefined_reading()
    v = instrument_audit.audit_nonachievement_claim(r, claimed_target=5.0)
    assert v.instrument_limited is True
    assert v.may_assert_nonachievement is False
    assert v.allowed_phrasing is not None
    assert "must not be asserted" in v.allowed_phrasing


def test_q2_target_beyond_expressible_max_is_instrument_limited():
    """Claiming 'did not reach T=500' against an instrument whose ceiling is 100 is illegitimate."""
    r = _defined_reading(expressible_max=100)
    v = instrument_audit.audit_nonachievement_claim(r, claimed_target=500)
    assert v.instrument_limited is True
    assert v.may_assert_nonachievement is False


def test_legitimate_nonachievement_claim_within_expressible_range():
    r = _defined_reading(expressible_max=100)
    v = instrument_audit.audit_nonachievement_claim(r, claimed_target=50)
    assert v.instrument_limited is False
    assert v.may_assert_nonachievement is True
    assert v.allowed_phrasing is None


def test_no_claimed_target_just_checks_precondition():
    r = _defined_reading()
    v = instrument_audit.audit_nonachievement_claim(r, claimed_target=None)
    assert v.instrument_limited is False
    assert v.may_assert_nonachievement is True


def test_audit_readings_over_real_measure_all_output():
    res = substrate.run(n=12, steps=200, seed=1, memory="off")
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    verdicts = instrument_audit.audit_readings(readings)
    assert set(verdicts.keys()) == set(readings.keys())
    for name, v in verdicts.items():
        assert v.instrument == readings[name].name


def test_r4_undefined_for_memory_off_is_correctly_flagged_instrument_limited():
    """For a memory=off run where R4 never becomes defined, the 9th audit must forbid
    asserting 'period did not emerge' outright -- it must be phrased as an instrument/
    precondition limitation instead, UNLESS the precondition genuinely was met (defined=True)
    and the claimed target is simply out of range.
    """
    res = substrate.run(n=16, steps=400, dt=0.05, seed=3, epsilon=0.05, memory="off")
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    r4 = readings["R4_period"]
    verdict = instrument_audit.audit_nonachievement_claim(r4, claimed_target=1.0)
    if not r4.defined:
        assert verdict.instrument_limited is True
        assert verdict.may_assert_nonachievement is False


def test_registry_covers_all_pr_r1_instruments():
    for name in ("R1_difference", "R2_direction", "R3_reversal", "R4_period"):
        assert name in instrument_audit.INSTRUMENT_EXPRESSIBLE_MAX_RULES


def test_instrument_limited_is_json_serializable_flag_on_run_output():
    import json

    from ai_lab.relational.run import build_result, _parser

    args = _parser().parse_args(["--n", "10", "--steps", "50", "--seed", "1"])
    result = build_result(args)
    assert "instrument_limited" in result
    assert isinstance(result["instrument_limited"], bool)
    json.dumps(result)  # must not raise -- everything must be JSON-serializable
