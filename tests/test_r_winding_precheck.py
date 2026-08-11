"""Tests for ai_lab/relational/winding_precheck.py (PR-R2.3, AUDIT.md Sec.15).

This module is explicitly NOT R8 -- these tests check the null-rate measurement tooling
itself, not any claim about real R-layer winding structure.
"""

import numpy as np
import pytest

from ai_lab.relational import winding_precheck as wp


def test_compute_winding_zero_for_clustered_phases():
    """Phases all within a semicircle can never wind, for any cyclic connection order."""
    phases = np.array([0.1, 0.3, 0.5])
    assert wp.compute_winding(phases) == 0


def test_compute_winding_nonzero_for_evenly_spread_phases():
    """Phases evenly spread around the full circle in ascending order wind exactly once."""
    phases = np.array([0.0, 2 * np.pi / 3, 4 * np.pi / 3])
    assert wp.compute_winding(phases) == 1


def test_compute_winding_sign_flips_with_direction():
    phases = np.array([0.0, 2 * np.pi / 3, 4 * np.pi / 3])
    assert wp.compute_winding(phases[::-1].copy()) == -wp.compute_winding(phases)


def test_compute_winding_double_loop():
    """A phase sequence that visibly winds twice around should report winding=2."""
    n = 12
    phases = np.linspace(0, 4 * np.pi, n, endpoint=False) % (2 * np.pi)
    assert wp.compute_winding(phases) == 2


def test_analytic_semicircle_null_rate_matches_known_values():
    assert wp.analytic_semicircle_null_rate(3) == pytest.approx(0.25)
    assert wp.analytic_semicircle_null_rate(1) == pytest.approx(0.0)
    assert wp.analytic_semicircle_null_rate(2) == pytest.approx(0.0)


def test_monte_carlo_null_rate_matches_analytic_at_n3():
    """N=3 is the one length where a fixed cyclic order is topologically forced to match
    the angularly-sorted order (any 3 points form a unique triangle) -- this is the
    cross-validation of compute_winding against a known closed form."""
    rate = wp.monte_carlo_null_rate(3, trials=100_000, seed=42)
    assert abs(rate - 0.25) < 0.01


def test_monte_carlo_null_rate_increases_with_n():
    """AUDIT.md Sec.15.2's non-obvious finding: the null rate RISES with cycle length under
    a fixed (graph-determined) traversal order, unlike the naive expectation that a longer
    cycle would be easier to interpret."""
    rates = [wp.monte_carlo_null_rate(n, trials=50_000, seed=n) for n in (3, 6, 10)]
    assert rates[0] < rates[1] < rates[2]


def test_shuffled_null_rate_zero_for_clustered_observed_phases():
    """Permuting phase values among cycle positions cannot create a winding if every value
    is within a semicircle to begin with, regardless of which permutation is drawn."""
    observed = np.array([2.1, 1.6, 1.0])  # AUDIT.md Sec.15.2's real example, span < pi
    rate = wp.shuffled_null_rate(observed, trials=10_000, seed=1)
    assert rate == 0.0


def test_shuffled_null_rate_nonzero_for_spread_observed_phases():
    observed = np.array([0.0, 2.0, 4.0, 5.5])  # spans most of the circle
    rate = wp.shuffled_null_rate(observed, trials=20_000, seed=1)
    assert rate > 0.0
