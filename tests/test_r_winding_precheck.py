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


# ---------------------------------------------------------------------------
# PR-R2.4 (AUDIT.md Sec.16.1): the smoothness gate
# ---------------------------------------------------------------------------

def test_min_length_for_smooth_winding_is_five_at_default_threshold():
    """N*threshold must exceed 2*pi; at threshold=pi/2 this requires N > 4, i.e. N >= 5."""
    assert wp.MIN_LENGTH_FOR_SMOOTH_WINDING == 5


def test_triangle_and_square_can_never_pass_the_smoothness_gate():
    """Structural fact, not probabilistic: no phase assignment on N=3 or N=4 can satisfy
    the smoothness gate, since 3*(pi/2) and 4*(pi/2) both fail to exceed 2*pi."""
    rng = np.random.default_rng(0)
    for n in (3, 4):
        for _ in range(200):
            phases = rng.uniform(0, 2 * np.pi, size=n)
            assert wp.is_smooth_winding(phases) is False


def test_smooth_winding_true_for_genuinely_gradual_full_loop():
    n = 8
    phases = np.linspace(0, 2 * np.pi, n, endpoint=False)
    assert wp.compute_winding(phases) == 1
    assert wp.max_adjacent_step(phases) < wp.DEFAULT_SMOOTHNESS_THRESHOLD
    assert wp.is_smooth_winding(phases) is True


def test_smooth_winding_false_for_one_large_jump_even_if_winding_nonzero():
    """A single large jump can produce a nonzero winding without any genuine gradual
    progression -- this is exactly the failure mode the gate exists to catch."""
    n = 8
    phases = np.zeros(n)
    phases[-1] = np.pi + 0.1  # one big jump, rest flat -- winding likely nonzero via wraparound
    w = wp.compute_winding(phases)
    if w != 0:
        assert wp.is_smooth_winding(phases) is False


def test_monte_carlo_smooth_null_rate_is_far_below_naive_approximation():
    """AUDIT.md Sec.16.1: the true composite null rate is much lower than the user's own
    (1/2)^N back-of-envelope estimate -- re-measured, not assumed."""
    rate_n6 = wp.monte_carlo_smooth_null_rate(6, trials=100_000, seed=1)
    naive_approx = 0.5 ** 6  # ~0.0156
    assert rate_n6 < naive_approx / 5  # measured rate is at least 5x lower than the naive guess


def test_monte_carlo_smooth_null_rate_zero_below_min_length():
    assert wp.monte_carlo_smooth_null_rate(3, trials=50_000, seed=1) == 0.0
    assert wp.monte_carlo_smooth_null_rate(4, trials=50_000, seed=1) == 0.0
