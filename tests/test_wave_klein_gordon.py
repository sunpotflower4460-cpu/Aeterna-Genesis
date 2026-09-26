"""Wave white (nonlinear Klein–Gordon): does it behave like light before we ask what grows in it?

    energy is conserved (closed box, leapfrog: bounded error that shrinks like dt²)
    time runs backwards exactly (flip the momentum, run again: back to t = 0)
    nothing travels faster than light (outside r = t + margin the energy stays ~0)
    an absorbing border (a put-in) only removes energy
"""
import numpy as np
import pytest

from genesis.models import wave_klein_gordon as kg


def _run(p, shape=(64, 64), steps=0, seed=1, mask=None):
    phi, pi = kg.make_initial(shape, np.random.default_rng(seed), p)
    for _ in range(steps):
        phi, pi = kg.step(phi, pi, p, mask)
    return phi, pi


def _max_drift(dt):
    p = dict(kg.DEFAULTS, dt=dt)
    phi, pi = kg.make_initial((48, 48), np.random.default_rng(1), p)
    e0, worst = kg.energy(phi, pi, p), 0.0
    for n in range(int(100 / dt)):
        phi, pi = kg.step(phi, pi, p)
        if n % 10 == 0:
            worst = max(worst, abs(kg.energy(phi, pi, p) - e0) / e0)
    return worst


def test_energy_is_conserved_to_second_order():
    d2, d1 = _max_drift(0.2), _max_drift(0.1)
    assert d2 < 0.01 and d1 < d2 / 3            # O(dt²): halving dt cuts the error about four times


@pytest.mark.parametrize("potential", ["phi4", "sine_gordon"])
@pytest.mark.parametrize("shape", [(64, 64), (16, 16, 16)])
def test_time_runs_backwards(potential, shape):
    p = dict(kg.DEFAULTS, potential=potential)
    phi0, pi0 = kg.make_initial(shape, np.random.default_rng(2), p)
    phi, pi = phi0.copy(), pi0.copy()
    for _ in range(300):
        phi, pi = kg.step(phi, pi, p)
    pi = -pi
    for _ in range(300):
        phi, pi = kg.step(phi, pi, p)
    assert np.abs(phi - phi0).max() < 1e-8 and np.abs(pi).max() < 1e-8


def test_nothing_travels_faster_than_light():
    p = dict(kg.DEFAULTS)
    n, c, steps = 121, 60, 100                  # t = steps · dt = 20
    phi, pi = np.ones((n, n)), np.zeros((n, n))  # sitting in a valley (vacuum) ...
    phi[c, c] += 0.1                             # ... with one poke at the centre
    vac = kg.energy_density(np.ones((n, n)), np.zeros((n, n)), p)
    for _ in range(steps):
        phi, pi = kg.step(phi, pi, p)
    e = kg.energy_density(phi, pi, p) - vac
    ys, xs = np.mgrid[:n, :n]
    r = np.hypot(ys - c, xs - c)
    t = steps * p["dt"]
    assert e[r > t + 3].sum() / e.sum() < 1e-9
    assert e[r <= t + 3].sum() / e.sum() > 0.999


def test_absorbing_border_only_removes_energy_and_closed_box_keeps_it():
    p = dict(kg.DEFAULTS, absorb=0.3)
    phi, pi = kg.make_initial((64, 64), np.random.default_rng(1), p)
    mask = kg.damping_mask(phi.shape, 8)
    es = [kg.energy(phi, pi, p)]
    for n in range(1500):
        phi, pi = kg.step(phi, pi, p, mask)
        if n % 50 == 49:
            es.append(kg.energy(phi, pi, p))
    assert es[-1] < 0.5 * es[0]
    assert all(b <= a * (1 + 2e-3) for a, b in zip(es, es[1:]))     # never gains (beyond the leapfrog wobble)


def test_on_the_hill_the_field_falls_into_both_valleys():
    """Measured, not placed: from φ = 0 + noise, both valleys fill (walls appear) -- the 陰陽 split."""
    p = dict(kg.DEFAULTS)
    phi, pi = _run(p, steps=300)
    frac_up = float((phi > 0).mean())
    assert 0.2 < frac_up < 0.8 and kg.wall_density(phi, p) > 0.0
    assert np.all(np.isfinite(phi))


def test_deterministic():
    p = dict(kg.DEFAULTS)
    a, b = _run(p, steps=50), _run(p, steps=50)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
