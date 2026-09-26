"""A torus that does not disappear (P12): an obstacle pushed through the superfluid feeds vortices -- and only
when it is pushed fast enough."""
import numpy as np

from genesis.diagnostics import vortex_rings as vr
from genesis.models import gpe_local as gl
from tools import torus_feed as tf


def test_no_potential_is_the_old_law_bit_for_bit_and_a_zero_potential_too():
    p = dict(gl.DEFAULTS)
    a = gl.make_initial((6, 6, 6), np.random.default_rng(3), p)
    assert np.array_equal(gl.step(a, p), gl.step(a, p, None))
    assert np.array_equal(gl.step(a, p), gl.step(a, p, np.zeros(a.shape)))


def test_the_obstacle_inside_is_excluded_from_the_vortex_search():
    rng = np.random.default_rng(0)
    psi = np.ones((24, 24, 24), complex)
    V, _ = tf.obstacle(psi.shape, np.array([12.0, 12.0, 12.0]))
    inside = V > 0.5
    psi[inside] = 0.01 * np.exp(1j * rng.uniform(-np.pi, np.pi, inside.sum()))     # meaningless phase inside
    assert len(vr.rings(psi)) > 0 and vr.rings(psi, exclude=inside) == []


def test_a_resting_obstacle_feels_no_drag_and_makes_no_vortex():
    r = tf.run(2, 0.0, 1, 60.0, shape=(48, 96))
    # switching the obstacle on sends sound round the box, so the drag swings a little; on average it is zero
    assert abs(np.mean([f["drag"] for f in r["frames"]])) < 0.02
    assert max(f["vortices"] for f in r["frames"]) == 0


def test_slow_makes_nothing_fast_keeps_shedding():
    slow = tf.run(2, 0.2, 1, 200.0, shape=(48, 96))
    assert max(f["vortices"] for f in slow["frames"]) == 0
    fast = tf.run(2, 0.8, 1, 200.0, shape=(48, 96))
    late = [f for f in fast["frames"] if f["t"] >= 100]
    assert min(f["vortices"] for f in late) > 0 and fast["mean_power_late"] > 0
