"""P17 (ladder R4): one chemistry -- the container material is the replicators' own breakdown product, washed out
like everything else; with a breakdown that needs water, the replicators come to need the containers they make."""
import numpy as np
import pytest

from genesis.models import protocell_one as po
from tools import protocell_run as pr


def run(T, n=64, **kw):
    return pr.run(2, seed=1, T=T, n=n, model=po, **kw)


def test_without_seeds_nothing_forms():
    p = dict(po.DEFAULTS_2D, n_seeds=0)
    c, U, V1, V2 = po.make_initial((32, 32), np.random.default_rng(0), p)
    for _ in range(3000):
        c, U, V1, V2 = po.step(c, U, V1, V2, p)
    assert c.max() < -0.9 and np.allclose(U, 1.0) and not V1.any()


def test_the_law_treats_both_kinds_the_same():
    p = dict(po.DEFAULTS_2D)
    c, U, V1, V2 = po.make_initial((32, 32), np.random.default_rng(3), dict(p, n_seeds=3))
    for _ in range(50):
        a = po.step(c, U, V1, V2, p)
        b = po.step(c, U, V2, V1, p)
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[2], b[3]) and np.array_equal(a[3], b[2])
        c, U, V1, V2 = a


def test_without_hydrolysis_the_replicators_never_feel_the_material():
    p = dict(po.DEFAULTS_2D, hyd=0.0)
    s = po.make_initial((32, 32), np.random.default_rng(1), p)
    a, b = s, (s[0], s[1], s[2], s[3])
    for _ in range(300):
        a = po.step(*a, p)
        b = po.step(np.full_like(b[0], -1.0), *b[1:], p)          # the same, with the material wiped every step
        assert np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2])


def test_containers_grow_from_nothing_and_hold_one_spot_each():
    r = run(200.0)
    first, last = r["containers_first_last"]
    assert r["frames"][0]["containers"] == 0 and first >= 3 and last > first
    assert all(f["occupied"] == f["containers"] for f in r["frames"])
    fr = r["frames"][1:]                                           # spots straddle the wall; few are half out
    assert sum(f["spots_outside"] for f in fr) <= 0.05 * sum(f["spots"] for f in fr)
    assert min(f["spot_min_inside"] for f in fr) >= 0.45
    assert r["late_in_out_ratio"] > 3 and r["late_one_spot_each"] > 0.9


def test_without_their_own_containers_the_replicators_stop_multiplying():
    walls = run(200.0)["frames"][-1]["replicators"]
    for ov in ({"y": 0.0}, {"hyd": 0.0}):                        # no material made / material that does not protect
        r = run(200.0, overrides=ov)
        assert r["frames"][-1]["replicators"] < walls / 5


def test_without_replicators_the_containers_wash_out():
    r = run(200.0, kill=120.0)
    at_kill = next(f for f in r["frames"] if f["t"] >= 100.0)
    assert at_kill["containers"] >= 3 and r["frames"][-1]["containers"] == 0


def test_deterministic():
    assert run(60.0, n=48) == run(60.0, n=48)


@pytest.mark.slow
def test_containers_divide_with_their_kind_in_2d():
    r = run(300.0, n=96)
    assert r["n_inherit"] >= 10 and r["inheritance"] == 1.0 and r["inheritance"] > r["null"] + 0.2


def test_without_flow_and_reactions_the_material_is_conserved():
    p = dict(po.DEFAULTS, n_seeds=0, F=0.0)                         # Cahn–Hilliard alone: ∫c is conserved (3D)
    _, U, V1, V2 = po.make_initial((16, 16, 16), np.random.default_rng(2), p)
    c = 0.1 * np.random.default_rng(2).standard_normal(U.shape)           # a 50/50 mixture, inside the spinodal
    total = c.sum()
    for _ in range(3000):
        c, U, V1, V2 = po.step(c, U, V1, V2, p)
    assert abs(c.sum() - total) < 1e-8 * c.size and c.std() > 0.5          # it separated, and kept its amount


def test_the_3d_audit_sees_closed_balls():
    from tools.protocell_run import three_d_audit
    g = np.indices((24, 24, 24)) - 12
    c = np.where((g ** 2).sum(0) < 25, 1.0, -1.0)
    c = c + 0.01 * np.random.default_rng(0).standard_normal(c.shape)
    a = three_d_audit(np.roll(c, 12, axis=0), np.zeros_like(c))          # a ball cut by the periodic edge
    assert a["containers"] == 1 and a["solid_balls"] == 1 and a["material"]["genuinely_3d"]
    sheet = np.where(np.abs(g[2]) < 3, 1.0, -1.0)                          # a slab spanning x and y
    s = three_d_audit(sheet, np.zeros_like(sheet))
    assert s["solid_balls"] == 0 and s["not_balls"][0]["spans"] == [0, 1]


def test_a_spot_half_outside_counts_as_outside():
    spots = np.zeros((8, 8), int)
    spots[2:4, 2:6] = 1                                            # 8 voxels
    box = np.zeros((8, 8), bool)
    box[2:4, 2:4] = True                                           # exactly half of them inside
    inside = pr.inside_shares(spots, box)
    assert inside.tolist() == [0.5] and int((inside <= 0.5).sum()) == 1


def test_the_last_frame_is_at_T_when_T_is_not_a_multiple_of_every():
    r = pr.run(3, seed=1, T=60.0, n=24, model=po)                  # every = 25
    assert [f["t"] for f in r["frames"]][-2:] == [50.0, 60.0]
    assert r["three_d"]["containers"] == r["frames"][-1]["containers"] > 0     # the audit sees the last frame


def test_a_spot_clipping_a_neighbour_is_assigned_once():
    lab = np.zeros((10, 10), int)
    lab[1:5, 1:5] = 1
    lab[1:5, 6:9] = 2
    spots = np.zeros((10, 10), int)
    spots[2:4, 2:7] = 7                                             # 10 voxels: 6 in container 1, 2 in container 2
    per, unassigned = pr.assign_spots(spots, lab)
    assert per == {1: 1, 2: 0} and unassigned == 0


def test_the_grid_spacing_cannot_be_set_as_a_law_override():
    with pytest.raises(ValueError):
        pr.run(2, seed=1, T=1.0, n=16, model=po, overrides={"dx": 0.5})
