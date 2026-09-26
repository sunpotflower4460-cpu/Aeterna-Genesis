"""Triangle white (P9-Q3): three waves closing a triangle carry a phase that two waves cannot."""
import numpy as np

from genesis.diagnostics import triads as td
from genesis.models import swift_hohenberg_quadratic as sq


def _hexagons(n, dx, Phi, shift=(0.0, 0.0)):
    """Three |k|≈1 waves on the grid whose integer indices sum to zero, with phases summing to Phi."""
    y, x = np.mgrid[:n, :n] * dx
    y, x = y - shift[0], x - shift[1]
    L = n * dx
    ks = [np.array([0, 8]), np.array([7, -4]), np.array([-7, -4])]        # integer modes, sum = 0, ~120°
    ph = [0.3, 1.1, Phi - 1.4]
    return sum(np.cos(2 * np.pi * (k[0] * y + k[1] * x) / L + f) for k, f in zip(ks, ph))


def test_triangle_phase_is_translation_invariant_pair_phase_is_not():
    n, dx = 64, np.pi / 4
    for Phi in (0.0, np.pi, 1.0):
        u = _hexagons(n, dx, Phi)
        us = np.roll(u, (13, 29), (0, 1))
        t0, t1 = td.triads(td.peaks(u, dx, 3)), td.triads(td.peaks(us, dx, 3))
        assert len(t0) == 1 and len(t1) == 1
        # a triangle and its mirror image carry ±Φ: |Φ| is the orientation-free invariant
        assert abs(abs(t0[0]["Phi"]) - abs(Phi)) < 1e-9 and abs(abs(t1[0]["Phi"]) - abs(Phi)) < 1e-9
        assert all(80 < a < 160 for a in t0[0]["angles"])
    p0, p1 = td.pair_phases(td.peaks(u, dx, 3)), td.pair_phases(td.peaks(us, dx, 3))
    assert max(abs(np.angle(np.exp(1j * (a - b)))) for a, b in zip(p0, p1)) > 0.5
    # the skewness carries the sign of cos Φ
    assert td.triad_skewness(_hexagons(n, dx, 0.0), dx) > 0.5
    assert td.triad_skewness(_hexagons(n, dx, np.pi), dx) < -0.5


def _grow(g, seed, steps=20000, n=48):
    p = dict(sq.DEFAULTS, g=g)
    u = sq.make_initial((n, n), np.random.default_rng(seed), p)
    for _ in range(steps):
        u = sq.step(u, p)
    return u, p


def test_from_noise_stripes_without_g_and_locked_triangles_with_g():
    dx = sq.DEFAULTS["dx"]
    u0, _ = _grow(0.0, 1)
    assert td.triads(td.peaks(u0, dx, 6)) == [] and abs(td.triad_skewness(u0, dx)) < 0.1
    for g, target, sign in ((0.5, 0.0, 1), (-0.5, np.pi, -1)):
        u, _ = _grow(g, 1)
        tri = td.triads(td.peaks(u, dx, 6))
        best = max(tri, key=lambda t: t["weight"])
        assert abs(np.angle(np.exp(1j * (best["Phi"] - target)))) < 0.2
        assert all(110 < a < 130 for a in best["angles"])
        assert sign * td.triad_skewness(u, dx) > 0.5


def test_quick_triangles_lock_to_0_or_pi_by_the_sign_of_g():
    """Small box (4 wavelengths), t = 100: the fast version of the test above (without the stripes)."""
    dx = sq.DEFAULTS["dx"]
    for g, target, sign in ((0.5, 0.0, 1), (-0.5, np.pi, -1)):
        u, _ = _grow(g, 1, steps=10000, n=32)
        best = max(td.triads(td.peaks(u, dx, 6)), key=lambda t: t["weight"])
        assert abs(np.angle(np.exp(1j * (best["Phi"] - target)))) < 0.2
        assert sign * td.triad_skewness(u, dx) > 0.3


def test_stable_dt_and_determinism():
    assert sq.DEFAULTS["dt"] <= sq.stable_dt(sq.DEFAULTS["dx"])
    a, _ = _grow(0.5, 7, steps=300)
    b, _ = _grow(0.5, 7, steps=300)
    assert np.array_equal(a, b)
