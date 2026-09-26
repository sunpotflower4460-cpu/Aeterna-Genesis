"""P15 (ladder R4): replicators that build their own container -- containers grow from nothing, hold one spot each,
keep the inside apart, divide with it, and neither lasts without the other."""
import numpy as np
import pytest

from genesis.models import protocell as pc
from tools import protocell_run as pr


def test_without_seeds_no_container_ever_forms():
    p = dict(pc.DEFAULTS_2D, n_seeds=0)
    c, U, V1, V2 = pc.make_initial((32, 32), np.random.default_rng(0), p)
    for _ in range(3000):
        c, U, V1, V2 = pc.step(c, U, V1, V2, p)
    assert c.max() < -0.9 and np.allclose(U, 1.0) and not V1.any()


def test_the_law_treats_both_kinds_the_same():
    p = dict(pc.DEFAULTS_2D)
    s = pc.make_initial((32, 32), np.random.default_rng(3), dict(p, n_seeds=3))
    c, U, V1, V2 = s
    for _ in range(50):
        a = pc.step(c, U, V1, V2, p)
        b = pc.step(c, U, V2, V1, p)
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[2], b[3]) and np.array_equal(a[3], b[2])
        c, U, V1, V2 = a


def test_containers_grow_from_nothing_and_hold_the_replicators():
    r = pr.run(2, seed=1, T=200.0, n=64)
    first, last = r["containers_first_last"]
    assert r["frames"][0]["containers"] == 0 and first >= 3 and last >= first
    assert all(f["occupied"] == f["containers"] for f in r["frames"])
    assert r["late_in_out_ratio"] > 5
    assert r["late_one_spot_each"] > 0.7


def test_without_building_the_replicators_die():
    r = pr.run(2, seed=1, T=100.0, n=64, overrides={"alpha": 0.0})
    assert r["frames"][-1]["replicators"] == 0.0 and all(f["containers"] == 0 for f in r["frames"])


def test_without_replicators_the_containers_dissolve():
    r = pr.run(2, seed=1, T=250.0, n=64, kill=150.0)
    at_kill = next(f for f in r["frames"] if f["t"] >= 150.0)
    assert at_kill["containers"] >= 3 and r["frames"][-1]["containers"] == 0


def test_deterministic():
    a = pr.run(2, seed=2, T=60.0, n=48)
    b = pr.run(2, seed=2, T=60.0, n=48)
    assert a == b


@pytest.mark.slow
def test_containers_divide_with_their_kind_in_2d():
    r = pr.run(2, seed=1, T=300.0, n=96)
    assert r["n_inherit"] >= 10 and r["inheritance"] == 1.0 and r["inheritance"] > r["null"] + 0.2
