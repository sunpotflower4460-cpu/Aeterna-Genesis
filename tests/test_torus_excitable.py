"""Excitable white (P13): waves that fire, rest and fire again; spirals (2D) and scroll rings (3D) from patchy noise."""
import numpy as np

from genesis.models import excitable_barkley as eb
from tools import torus_excitable as te


def test_the_resting_medium_stays_at_rest():
    p = dict(eb.DEFAULTS, noise=0.0)
    u, v = eb.make_initial((32, 32), np.random.default_rng(0), p)
    for _ in range(500):
        u, v = eb.step(u, v, p)
    assert np.abs(u).max() < 1e-12 and np.abs(v).max() < 1e-12


def test_a_pulse_travels_at_a_constant_speed():
    p = dict(eb.DEFAULTS)
    n = 800
    u, v = np.zeros(n), np.zeros(n)
    u[395:405] = 1.0                                    # a kick in the middle (put in): two pulses go out
    front = []
    for k in range(int(30 / p["dt"]) + 1):
        if k % int(10 / p["dt"]) == 0:
            ex = np.nonzero(u[400:] > 0.5)[0]
            front.append(ex.max() * p["dx"])
        u, v = eb.step(u, v, p)
    s1, s2 = (front[2] - front[1]) / 10, (front[3] - front[2]) / 10
    assert s1 > 1.0 and abs(s1 - s2) < 0.05 * s1


def test_spirals_grow_from_patchy_noise_in_2d_and_keep_one_rhythm():
    r = te.run(2, 6.0, 1, 150.0, n=96)
    tips = [f["tips"] for f in r["frames"]]
    assert min(tips[len(tips) // 2:]) > 0                  # still there in the second half
    lo, mid, hi = r["rhythm"]["period_p5_50_95"]
    assert r["rhythm"]["cells_firing_periodically"] > 0.99 and hi - lo < 0.15 * mid


def test_scroll_rings_grow_from_patchy_noise_in_3d():
    """48³, patch size 10, seed 1, t = 150: filaments remain, at least one scroll ring (a torus) lives ≥ 50 t."""
    r = te.run(3, 10.0, 1, 150.0, n=48)
    assert r["frames"][-1]["filaments"] >= 1
    assert any(tr["lifetime"] >= 50 for tr in r["tracks"])
