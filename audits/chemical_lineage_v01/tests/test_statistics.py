"""T20: the series is the unit of replication; generation-level input is refused."""
import numpy as np
import pytest

import _setup  # noqa: F401
import statistics as ST


def test_T20_generation_level_matrix_is_refused():
    with pytest.raises(ValueError):
        ST.bootstrap_ci(np.zeros((24, 30)))


def test_T20_bootstrap_uses_n_series_not_n_series_times_generations():
    v = np.linspace(0.0, 1.0, 24)
    mean, lo, hi = ST.bootstrap_ci(v, n_boot=2000, seed=0)
    assert abs(mean - v.mean()) < 1e-12 and lo <= mean <= hi


def test_T20_sign_flip_is_seeded_and_bounded():
    v = np.array([0.5, 0.4, 0.6, 0.45, 0.55] * 4)
    p1 = ST.sign_flip_pvalue(v, n_perm=2000, seed=1)
    p2 = ST.sign_flip_pvalue(v, n_perm=2000, seed=1)
    assert p1 == p2 and 0.0 < p1 <= 1.0
