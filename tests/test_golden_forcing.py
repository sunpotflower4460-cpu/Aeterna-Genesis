"""P16 (H7): the golden ratio -- the last torus of the standard map, and a medium under an outside beat."""
import numpy as np
import pytest

from genesis.models import forced_oscillator as fo
from genesis.models import standard_map as sm
from tools import golden_forcing as gf

GOLDEN = (np.sqrt(5.0) - 1.0) / 2.0


def test_the_golden_torus_outlives_the_pi_torus():
    c = sm.circles(0.95, 1601, 8000)
    assert c.size > 0
    assert np.min(np.abs(c - GOLDEN)) < 1e-3                  # a circle turning at the golden ratio survives
    assert np.min(np.abs(c - 1.0 / np.pi)) > 0.02             # the one near 1/π (close to 1/3 and 7/22) is gone
    assert sm.circles(0.98, 1601, 8000).size == 0             # beyond Greene's K ≈ 0.9716 none is left


def test_birkhoff_tells_circles_from_chaos():
    om, err = sm.rotation(0.0, np.array([GOLDEN]), 2000)       # K = 0: a straight circle, ω = p0
    assert abs(om[0] - GOLDEN) < 1e-12 and err[0] < 1e-12
    om, err = sm.rotation(2.0, np.array([0.123]), 4000)       # strong kicks: chaos
    assert err[0] > 1e-6


def test_free_period():
    assert abs(fo.free_period() - fo.T0) < 0.01


def test_lock_of_reads_exact_fractions():
    k = np.arange(60)[:, None]
    exact = -2 * np.pi * (k / 3.0) - 0.3 * np.sin(2 * np.pi * k / 3.0)       # 1/3 per beat, uneven inside
    golden = -2 * np.pi * GOLDEN * k
    rho, p, q, locked = gf.lock_of(np.concatenate([exact, golden], axis=1), qmax=8, tol=0.05)
    assert locked[0] and (p[0], q[0]) == (1, 3)
    assert not locked[1] and abs(rho[1] - GOLDEN) < 1e-9


def test_one_cell_under_a_beat():
    s = np.array([1.0, 1 / np.pi, 1 / np.pi, GOLDEN])
    g = np.array([0.05, 0.02, 0.05, 0.05])
    rho, p, q, locked = gf.run_cells(s, g, n_trans=30.0, n_beats=60)
    assert locked[0] and (p[0], q[0]) == (1, 1)               # the beat at its own tempo captures it
    assert not locked[1]                                      # 1/π, weak beat: free
    assert locked[2] and (p[2], q[2]) == (1, 3)               # 1/π, stronger beat: captured by 1/3 (three phases)
    assert not locked[3]                                      # the golden ratio, same beat: still free


def test_the_medium_is_deterministic():
    a = gf.run_medium(2, 0.5, 0.05, seed=2, n=24, n_trans=5.0, n_beats=8)
    b = gf.run_medium(2, 0.5, 0.05, seed=2, n=24, n_trans=5.0, n_beats=8)
    assert a == b


@pytest.mark.slow
def test_a_half_beat_captures_the_2d_medium():
    r = gf.run_medium(2, 0.5, 0.05, seed=1, n=64, n_trans=40.0, n_beats=30)
    assert r["captured_share"] > 0.9 and list(r["captured_at"]) == ["1/2"]
