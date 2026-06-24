"""Unit tests for core/measure.py: cumulative rotation and drift."""

import numpy as np

from core import measure


def test_unwrap_cumulative_monotonic_full_turns():
    # Two full counter-clockwise turns sampled at 0..4pi.
    angles = np.linspace(0, 4 * np.pi, 200)
    wrapped = (angles + np.pi) % (2 * np.pi) - np.pi
    cum = measure.unwrap_cumulative(wrapped)
    assert cum[0] == 0.0
    assert np.all(np.diff(cum) >= -1e-9)         # monotonic
    assert abs(cum[-1] - 4 * np.pi) < 1e-6        # recovers total rotation


def test_unwrap_cumulative_negative_direction():
    angles = np.linspace(0, -2 * np.pi, 100)
    wrapped = (angles + np.pi) % (2 * np.pi) - np.pi
    cum = measure.unwrap_cumulative(wrapped)
    assert cum[-1] < 0
    assert abs(cum[-1] + 2 * np.pi) < 1e-6


def test_relative_drift():
    assert measure.relative_drift([10.0, 10.0, 10.0]) == 0.0
    assert abs(measure.relative_drift([10.0, 11.0]) - 0.1) < 1e-12
