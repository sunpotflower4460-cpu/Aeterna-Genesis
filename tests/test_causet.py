"""Unit tests for core.causet (order-only causal-set measures)."""

import numpy as np

from core.causet import (
    sprinkle, causal_relation, transitive_percolation, rank,
    interval_dimension, bd_action_2d,
)


def _chain(N):
    R = np.zeros((N, N), bool)
    for i in range(N):
        for j in range(i + 1, N):
            R[i, j] = True
    return R


def _antichain(N):
    return np.zeros((N, N), bool)


def _complete_bilayer(N):
    """N/2 bottom elements, each below every one of N/2 top elements."""
    assert N % 2 == 0
    h = N // 2
    R = np.zeros((N, N), bool)
    R[:h, h:] = True
    return R


def test_bd_action_chain_equals_N():
    for N in (6, 10, 20):
        assert bd_action_2d(_chain(N)) == N


def test_bd_action_antichain_equals_N():
    for N in (6, 10, 20):
        assert bd_action_2d(_antichain(N)) == N


def test_bd_action_complete_bilayer():
    for N in (6, 10, 20):
        assert bd_action_2d(_complete_bilayer(N)) == N - N * N // 2


def test_rank_of_chain_is_0_to_N_minus_1():
    N = 8
    r = rank(_chain(N))
    assert sorted(r.tolist()) == list(range(N))


def test_rank_of_antichain_is_all_zero():
    assert np.all(rank(_antichain(9)) == 0)


def test_transitive_percolation_is_closed():
    R = transitive_percolation(40, 0.15, seed=1)
    # a<b and b<c must imply a<c (bitmask closure leaves no gap)
    RR = (R.astype(int) @ R.astype(int)) > 0
    assert np.all(R[RR])


def test_sprinkle_2d_diamond_dimension_near_two():
    R = causal_relation(sprinkle(1500, dim=2, region="diamond", seed=0))
    d = interval_dimension(R)
    assert abs(d - 2.0) < 0.15, d


def test_sprinkle_3d_diamond_dimension_near_three():
    R = causal_relation(sprinkle(1500, dim=3, region="diamond", seed=0))
    d = interval_dimension(R)
    assert abs(d - 3.0) < 0.25, d
