"""P14 (ladder R3): two replicators on one food -- purification, division, inheritance, mutation control."""
import numpy as np
import pytest

from genesis.models import gray_scott_two as g2
from tools import cell_inherit as ci


def _blob(shape, center, q, r=3.0):
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing="ij")
    d2 = sum((g - c) ** 2 for g, c in zip(grids, center))
    b = np.exp(-d2 / (2 * r * r))
    return 1.0 - 0.5 * b, 0.5 * q * b, 0.5 * (1 - q) * b


def test_without_seeds_nothing_happens():
    p = dict(g2.DEFAULTS_2D, n_seeds=0)
    U, V1, V2, mix = g2.make_initial((32, 32), np.random.default_rng(0), p)
    for _ in range(200):
        U, V1, V2 = g2.step(U, V1, V2, p)
    assert mix == [] and np.allclose(U, 1.0) and not V1.any() and not V2.any()


def test_the_law_treats_both_kinds_the_same():
    p = dict(g2.DEFAULTS_2D, mu=0.002)
    U, V1, V2, _ = g2.make_initial((32, 32), np.random.default_rng(3), dict(p, n_seeds=3))
    for _ in range(50):
        a = g2.step(U, V1, V2, p)
        b = g2.step(U, V2, V1, p)
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[2]) and np.array_equal(a[2], b[1])
        U, V1, V2 = a


@pytest.mark.parametrize("q", [0.62, 0.38])
def test_a_mixed_spot_becomes_pure_and_the_majority_wins(q):
    p = dict(g2.DEFAULTS_2D)
    U, V1, V2 = _blob((48, 48), (24, 24), q)
    for _ in range(400):
        U, V1, V2 = g2.step(U, V1, V2, p)
    _, sp = g2.spots(V1, V2)
    assert sp and all(g2.purity(s["kind1"]) > 0.95 for s in sp)
    assert all((s["kind1"] > 0.5) == (q > 0.5) for s in sp)


def test_strong_mixing_kills_the_spots():
    """With fast V1 <-> V2 exchange a spot is always half and half, copies itself half as well, and dies."""
    r = ci.run(2, seed=1, T=1500.0, mu=0.02, n=64)
    assert not r["alive_at_end"]


def test_daughters_carry_the_parent_kind_in_2d():
    r = ci.run(2, seed=1, T=3000.0, n=128)
    assert r["n_divisions_pure"] >= 10
    assert r["inheritance_pure"] >= 0.95 and r["inheritance_pure"] > r["null_pure"] + 0.1
    assert r["flips"] == 0
    assert r["frames"][-1]["pure_fraction"] == 1.0
    assert r["spots_start_end"][1] > r["spots_start_end"][0]


def test_deterministic():
    a = ci.run(2, seed=2, T=600.0, n=64)
    b = ci.run(2, seed=2, T=600.0, n=64)
    assert a == b


@pytest.mark.slow
def test_daughters_carry_the_parent_kind_in_3d():
    r = ci.run(3, seed=1, T=2500.0, n=48)
    assert r["n_divisions_pure"] >= 3 and r["inheritance_pure"] == 1.0 and r["flips"] == 0
