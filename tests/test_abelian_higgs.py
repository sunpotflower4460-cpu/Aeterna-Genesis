"""Light-and-phase white (lattice Abelian Higgs): the gates before asking what grows in it.

    Gauss's law holds exactly (round-off), with and without the uniform cooling
    gauge invariance: a random gauge transformation at t = 0 changes no gauge-invariant quantity, ever
    energy is conserved to O(dt²); time runs backwards; a poke spreads no faster than light
    flux is quantized: an isolated vortex carries 2π
"""
import numpy as np
import pytest

from genesis.diagnostics.influence import twin_influence
from genesis.models import abelian_higgs as ah


def _run(p, n=48, steps=0, seed=1):
    s = ah.make_initial((n, n), np.random.default_rng(seed), p)
    for _ in range(steps):
        s = ah.step(*s, p)
    return s


@pytest.mark.parametrize("gamma", [0.0, 0.05])
def test_gauss_law_is_kept_exactly(gamma):
    p = dict(ah.DEFAULTS, gamma=gamma)
    phi, pi, th, E = ah.make_initial((48, 48), np.random.default_rng(3), p)
    worst = 0.0
    for n in range(2000):
        phi, pi, th, E = ah.step(phi, pi, th, E, p)
        if n % 100 == 0:
            worst = max(worst, float(np.abs(ah.gauss_residual(phi, pi, E)).max()))
    assert worst < 1e-10


def test_gauge_invariance():
    p = dict(ah.DEFAULTS)
    a = ah.make_initial((32, 32), np.random.default_rng(4), p)
    a = (a[0] + 0.3, a[1], a[2], a[3])                          # break the tiny-noise symmetry a little
    alpha = np.random.default_rng(5).uniform(-np.pi, np.pi, (32, 32))
    phi, pi, th, E = a
    b = (np.exp(1j * alpha) * phi, np.exp(1j * alpha) * pi,
         np.stack([th[i] + np.roll(alpha, -1, i) - alpha for i in (0, 1)]), E.copy())
    for n in range(300):
        a, b = ah.step(*a, p), ah.step(*b, p)
        if n % 50 == 49:
            assert abs(ah.energy(*a, p) - ah.energy(*b, p)) < 1e-8 * ah.energy(*a, p)
            assert np.allclose(np.abs(a[0]), np.abs(b[0]), atol=1e-9)
            assert np.allclose(np.cos(ah.plaquette(a[2])), np.cos(ah.plaquette(b[2])), atol=1e-9)
            assert np.array_equal(ah.winding(a[0], a[2]), ah.winding(b[0], b[2]))


def _drift(dt):
    p = dict(ah.DEFAULTS, dt=dt)
    s = ah.make_initial((32, 32), np.random.default_rng(1), p)
    e0, worst = ah.energy(*s, p), 0.0
    for n in range(int(60 / dt)):
        s = ah.step(*s, p)
        if n % 10 == 0:
            worst = max(worst, abs(ah.energy(*s, p) - e0) / e0)
    return worst


def test_energy_conserved_to_second_order():
    d1, d2 = _drift(0.1), _drift(0.05)
    assert d1 < 0.01 and d2 < d1 / 3


def test_time_runs_backwards():
    p = dict(ah.DEFAULTS)
    s0 = ah.make_initial((32, 32), np.random.default_rng(2), p)
    s = s0
    for _ in range(300):
        s = ah.step(*s, p)
    s = (s[0], -s[1], s[2], -s[3])
    for _ in range(300):
        s = ah.step(*s, p)
    assert np.abs(s[0] - s0[0]).max() < 1e-8 and np.abs(s[2] - s0[2]).max() < 1e-8


def test_a_poke_spreads_no_faster_than_light():
    p = dict(ah.DEFAULTS)
    n = 81
    state = {"E": np.zeros((2, n, n)), "phi": np.ones((n, n), complex), "pi": np.zeros((n, n), complex),
             "th": np.zeros((2, n, n))}

    def adv(s, k):
        phi, pi, th, E = s["phi"], s["pi"], s["th"], s["E"]
        for _ in range(k):
            phi, pi, th, E = ah.step(phi, pi, th, E, p)
        return {"E": E, "phi": phi, "pi": pi, "th": th}

    # poke the magnetic side (a link angle): Gauss's law is untouched by it
    state["th"][0][40, 40] += 1e-6
    base = {k: np.array(v, copy=True) for k, v in state.items()}
    base["th"][0][40, 40] -= 1e-6
    r = twin_influence({"phi": base["phi"], "pi": base["pi"], "th0": base["th"][0], "th1": base["th"][1],
                        "E0": base["E"][0], "E1": base["E"][1]},
                       lambda s, k: _flat(adv(_unflat(s), k)), "th0", (40, 40), 1e-6, 8, 25, p["dt"])
    # a link poke already touches the plaquettes on both sides, and the lattice stencil adds a fringe:
    # measured front − t = 2.2 … 4.1 cells; the speed of the front itself stays below 1
    assert all(x["front"] <= x["t"] + 5 for x in r["rows"])
    assert r["front_speed"] <= 1.02


def _unflat(s):
    return {"phi": s["phi"], "pi": s["pi"], "th": np.stack([s["th0"], s["th1"]]), "E": np.stack([s["E0"], s["E1"]])}


def _flat(s):
    return {"phi": s["phi"], "pi": s["pi"], "th0": s["th"][0], "th1": s["th"][1], "E0": s["E"][0], "E1": s["E"][1]}


def test_flux_of_an_isolated_vortex_is_quantized():
    """A vortex–antivortex pair (phase winding put in, NO gauge field put in) relaxed with cooling: the gauge
    field itself gathers into tubes, and the flux around each is ±2π (the tube's tail needs a wide enough disk)."""
    p = dict(ah.DEFAULTS, gamma=0.05)
    n = 64
    yy, xx = np.mgrid[:n, :n].astype(float)
    cy, x1, x2 = 31.5, 16.5, 47.5                              # cores between grid points: phase defined everywhere
    phase = sum(np.arctan2(yy - cy + k * n, xx - x1 + m * n) - np.arctan2(yy - cy + k * n, xx - x2 + m * n)
                for m in range(-2, 3) for k in range(-2, 3))       # periodic images: no seam at the box edge
    xi = 1.0 / np.sqrt(p["lam"])
    phi = np.tanh(np.hypot(yy - cy, xx - x1) / xi) * np.tanh(np.hypot(yy - cy, xx - x2) / xi) * np.exp(1j * phase)
    s = (phi, np.zeros((n, n), complex), np.zeros((2, n, n)), np.zeros((2, n, n)))
    assert np.abs(ah.flux(s[2])).max() == 0.0                    # no flux was put in
    for _ in range(1500):
        s = ah.step(*s, p)
    w = ah.winding(s[0], s[2])
    around = ah.flux_around(s[2], w, 15)
    assert sorted(k for k, _, _ in around) == [-1, 1]
    for k, f, _ in around:
        assert abs(f / (2 * np.pi) - k) < 0.02
    assert abs(np.abs(ah.flux(s[2])).sum() / (2 * np.pi) / 2 - 1.0) < 0.01
    assert np.abs(ah.flux(s[2])).max() < 0.5                     # far from the compact-link wrap at ±π


def test_deterministic():
    p = dict(ah.DEFAULTS)
    a, b = _run(p, steps=50), _run(p, steps=50)
    assert all(np.array_equal(x, y) for x, y in zip(a, b))
