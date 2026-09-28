"""P18 (ladder R4): no law says the material helps the replicators (h = 0); every dissolved species is a little more
soluble in the material (one number aff for all) and the reactions follow mass action."""
import numpy as np

from genesis.models import protocell_one as po
from genesis.models import protocell_partition as pp
from genesis.models.gray_scott_two import laplacian
from tools import protocell_dependence as dep


def _slab(n=32, w=2.5):
    x = np.arange(n)
    prof = np.tanh((x - n / 4) / w) * np.tanh((3 * n / 4 - x) / w)
    return prof[:, None] * np.ones((1, 2)), prof


def test_without_partition_the_replicators_never_feel_the_material():
    p = dict(pp.DEFAULTS_2D, aff=0.0)
    s = pp.make_initial((32, 32), np.random.default_rng(1), p)
    a, b = s, s
    for _ in range(300):
        a = pp.step(*a, p)
        b = pp.step(np.full_like(b[0], -1.0), *b[1:], p)          # the same, with the material wiped every step
        assert np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2]) and np.array_equal(a[3], b[3])


def test_without_partition_it_is_p17_without_hydrolysis():
    p = dict(pp.DEFAULTS_2D, aff=0.0)
    q = dict(po.DEFAULTS_2D, hyd=0.0, g0=1.0, k=p["k"])
    s = pp.make_initial((32, 32), np.random.default_rng(2), p)
    a, b = s, s
    for _ in range(100):
        a, b = pp.step(*a, p), po.step(*b, q)
    for x, y in zip(a, b):
        assert np.allclose(x, y, rtol=0, atol=1e-13)


def test_the_partition_term_is_the_face_flux_and_conserves():
    rng = np.random.default_rng(0)
    X, c = rng.random((24, 24)), rng.uniform(-1, 1, (24, 24))
    m = 0.5 * (1.0 + c)
    face = sum(0.5 * (X + np.roll(X, s, a)) * (np.roll(m, s, a) - m) for a in (0, 1) for s in (1, -1))
    got = pp.partition_flux(X, m, laplacian)
    assert np.allclose(got, face, atol=1e-12) and abs(got.sum()) < 1e-10


def test_food_settles_e_to_the_aff_times_richer_inside():
    """A fixed smooth slab of material (M = 0, no flow, no reactions): food shares itself as exp(aff·m)."""
    c, prof = _slab()
    for aff in (0.5, 1.0):
        p = dict(pp.DEFAULTS_2D, M=0.0, F=0.0, k=0.0, aff=aff, back=0.0)
        U, V = np.ones_like(c), np.zeros_like(c)
        cc = c
        for _ in range(8000):
            cc, U, _, _ = pp.step(cc, U, V, V, p)
        assert np.array_equal(cc, c)
        want = np.exp(aff * (prof[16] - prof[0]) / 2)
        assert abs(U[16].mean() / U[0].mean() / want - 1) < 0.01
        assert abs(U.mean() - 1.0) < 1e-12                        # nothing made or lost


def test_the_law_treats_both_kinds_the_same():
    p = dict(pp.DEFAULTS_2D)
    c, U, V1, V2 = pp.make_initial((32, 32), np.random.default_rng(3), dict(p, n_seeds=3))
    for _ in range(50):
        a = pp.step(c, U, V1, V2, p)
        b = pp.step(c, U, V2, V1, p)
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[2], b[3]) and np.array_equal(a[3], b[2])
        c, U, V1, V2 = a


def test_deterministic():
    p = dict(pp.DEFAULTS_2D)
    runs = []
    for _ in range(2):
        s = pp.make_initial((32, 32), np.random.default_rng(5), p)
        for _ in range(200):
            s = pp.step(*s, p)
        runs.append(s)
    assert all(np.array_equal(x, y) for x, y in zip(*runs))


def test_the_dependence_tool_reads_zero_without_partition():
    """aff = 0: the replicators' equations do not contain c, so neither way of measuring may find a dependence."""
    r = dep.point(2, 48, k=0.060, aff=0.0, seed=1, T=60.0)
    assert r["v_with"] > 0 and r["D_y"] == 0.0 and r["class"] == "anywhere"
    ko = dep.knockout(2, 32, k=0.060, aff=0.0, seed=1, t0=20.0, dt_after=20.0)
    assert ko["D_ko"] == 0.0 and ko["recovered"]


def test_without_material_every_aff_is_the_same_run():
    """The control of the dependence tool: with no material at all (c ≡ −1) the partition term is exactly zero."""
    runs = []
    for aff in (0.0, 0.5, 2.0):
        p = dict(pp.DEFAULTS_2D, aff=aff, **dep.NO_MATERIAL)
        s = pp.make_initial((32, 32), np.random.default_rng(4), p)
        for _ in range(300):
            s = pp.step(*s, p)
        assert np.all(s[0] == -1.0)
        runs.append(s)
    assert all(np.array_equal(a, b) for r in runs[1:] for a, b in zip(runs[0][1:], r[1:]))


def test_classify():
    assert dep.classify(0.0, 0.0) == "dead"
    assert dep.classify(0.1, 0.1) == "anywhere"
    assert dep.classify(0.1, 0.0) == "dependent"
