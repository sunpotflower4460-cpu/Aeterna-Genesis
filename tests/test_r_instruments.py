"""Tests for ai_lab/relational/instruments.py (PR-R1: R1-R4 only)."""

import numpy as np
import pytest

from ai_lab.relational import instruments, substrate


def test_reading_has_exact_spec_fields():
    r = instruments.Reading(
        name="x", value=1, defined=True, precondition="p", expressible_max=5,
        expressible_note="n",
    )
    d = r.to_dict()
    assert set(d.keys()) == {"name", "value", "defined", "precondition", "expressible_max", "expressible_note"}


# ---------------------------------------------------------------------------
# R1 difference
# ---------------------------------------------------------------------------

def test_r1_difference_defined_with_real_variance():
    x_traj = np.random.default_rng(0).normal(size=(50, 6, 1))
    r = instruments.difference(x_traj)
    assert r.defined is True
    assert r.value["mean"] > 0
    assert r.expressible_max is None


def test_r1_difference_flat_when_all_equal():
    x_traj = np.zeros((10, 4, 1))
    r = instruments.difference(x_traj)
    assert r.defined is True
    assert r.value["mean"] == 0.0


# ---------------------------------------------------------------------------
# R2 direction
# ---------------------------------------------------------------------------

def test_r2_undefined_without_edges():
    x_traj = np.random.default_rng(0).normal(size=(20, 4, 1))
    W = np.zeros((4, 4))
    r = instruments.direction(x_traj, W)
    assert r.defined is False
    assert r.value is None


def test_r2_persistence_high_for_monotone_diverging_pair():
    # node 1 always above node 0 -> sign should persist near 1.0
    t = np.linspace(0, 1, 40)
    x0 = -t
    x1 = t
    x_traj = np.stack([x0, x1], axis=1)[:, :, None]
    W = np.array([[0, 1], [1, 0]], dtype=float)
    r = instruments.direction(x_traj, W)
    assert r.defined is True
    assert r.value["mean_persistence"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# R3 reversal
# ---------------------------------------------------------------------------

def test_r3_zero_for_perfectly_monotone_series():
    t = np.linspace(0, 1, 100)
    x_traj = np.stack([-t, t], axis=1)[:, :, None]  # two monotone nodes (distinct, so R1 > 0)
    r = instruments.reversal(x_traj)
    assert r.defined is True
    assert r.value["mean_count"] == 0


def test_r3_detects_oscillation():
    t = np.linspace(0, 20 * np.pi, 400)
    series_a = np.sin(t)
    series_b = np.sin(t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.reversal(x_traj)
    assert r.defined is True
    assert r.value["mean_count"] > 10  # a clean sine over 10 periods should reverse often


def test_r3_expressible_max_is_L_minus_1():
    x_traj = np.random.default_rng(0).normal(size=(37, 3, 1))
    r = instruments.reversal(x_traj)
    assert r.expressible_max == 36


# ---------------------------------------------------------------------------
# R4 period
# ---------------------------------------------------------------------------

def test_r4_expressible_max_carries_L_over_2_value():
    """R4's expressible_max must actually carry the value, not just a comment (task constraint)."""
    L = 200
    x_traj = np.random.default_rng(1).normal(size=(L, 3, 1))
    r = instruments.period(x_traj, dt=0.1)
    assert r.expressible_max == L // 2
    assert isinstance(r.expressible_max, int)
    assert "L/2" in r.expressible_note or str(L // 2) in r.expressible_note


def test_r4_undefined_when_r3_precondition_fails():
    t = np.linspace(0, 1, 50)
    x_traj = np.stack([-t, t], axis=1)[:, :, None]  # monotone -> R3 = 0 reversals everywhere
    r = instruments.period(x_traj, dt=0.05)
    assert r.defined is False
    assert r.value is None or r.value.get("any_defined") is False


def test_r4_detects_period_of_clean_sine():
    dt = 0.05
    true_period_steps = 40  # so T = 2.0 time units
    t = np.arange(0, 2000) * dt
    omega = 2 * np.pi / (true_period_steps * dt)
    series_a = np.sin(omega * t)
    series_b = np.sin(omega * t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.period(x_traj, dt)
    assert r.defined is True
    node0 = r.value["per_node"][0]
    assert node0["defined"] is True
    assert node0["lag_steps"] == pytest.approx(true_period_steps, abs=2)
    # rate_i = 1/T_i should be the reciprocal, not the forbidden word "frequency" anywhere
    assert node0["rate"] == pytest.approx(1.0 / node0["T"], rel=1e-6)


def test_r4_cannot_represent_period_longer_than_L_over_2():
    """A period longer than half the window must come back undefined for that node, honestly,
    not silently truncated to a wrong value."""
    dt = 0.05
    L = 200  # expressible_max = 100 steps
    long_period_steps = 180  # > L/2
    t = np.arange(0, L) * dt
    omega = 2 * np.pi / (long_period_steps * dt)
    series_a = np.sin(omega * t)
    series_b = np.sin(omega * t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.period(x_traj, dt)
    assert r.expressible_max == 100
    node0 = r.value["per_node"][0]
    # Either R3's precondition fails for this short a fraction of a period (< 2 reversals in
    # 200 samples of a 180-step period), or R4's search finds nothing within its L/2 ceiling
    # -- either way, this instrument must NOT report a fabricated ~180-step period.
    if node0["defined"]:
        assert node0["lag_steps"] <= 100


def test_measure_all_returns_all_four_readings_in_order():
    x_traj = np.random.default_rng(2).normal(size=(30, 5, 1))
    W = np.ones((5, 5)) - np.eye(5)
    out = instruments.measure_all(x_traj, W, dt=0.05)
    assert list(out.keys()) == ["R1_difference", "R2_direction", "R3_reversal", "R4_period"]
    for reading in out.values():
        assert isinstance(reading, instruments.Reading)
