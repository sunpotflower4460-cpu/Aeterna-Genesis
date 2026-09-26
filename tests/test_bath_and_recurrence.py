"""H8 (a border that takes and gives back) and H7 (rotations that never meet): the instruments' own gates."""
from fractions import Fraction

import numpy as np

from genesis.diagnostics.exchange import ExchangeMeter
from genesis.diagnostics.recurrence import (continued_fraction, convergents, harmonics_above, mode_returns,
                                             two_arm_returns)
from genesis.models import wave_klein_gordon as kg


def test_bath_gives_equipartition():
    """Whole box as the bath: the kinetic temperature <π²> equals the bath temperature (fluctuation–dissipation)."""
    p = dict(kg.DEFAULTS, absorb=0.5, bath_T=0.1)
    phi, pi = kg.make_initial((32, 32), np.random.default_rng(1), p)
    mask, rng, acc = np.ones((32, 32)), np.random.default_rng(7), []
    for n in range(5000):
        phi, pi = kg.step(phi, pi, p, mask, rng)
        if n > 1500:
            acc.append(float((pi ** 2).mean()))
    assert abs(np.mean(acc) - 0.1) < 0.005


def test_bath_off_is_the_plain_absorber_bit_for_bit():
    q = dict(kg.DEFAULTS, absorb=0.3)
    a = kg.make_initial((32, 32), np.random.default_rng(2), q)
    b = a
    m = kg.damping_mask((32, 32), 8)
    for _ in range(200):
        a = kg.step(*a, q, m)
        b = kg.step(*b, dict(q, bath_T=0.0), m, np.random.default_rng(3))
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_lab_bath_replays():
    from tools.lab.universe import Universe, replay
    u = Universe("wave-phi4", 3, {"absorb": 0.3, "bath_T": 0.05})
    u.advance(100)
    assert u.sha256() == replay(u.recipe(), 100).sha256()
    v = Universe("wave-phi4", 4, {"absorb": 0.3, "bath_T": 0.05})
    v.advance(100)
    assert u.sha256() != v.sha256()                      # each seed has its own bath noise


def test_exchange_meter_keeps_directions_apart():
    m = ExchangeMeter()
    for t, e in enumerate([10, 8, 9, 7, 7.5]):
        m.add(float(t), e)
    s = m.summary()
    assert s["inflow"] == 1.5 and s["outflow"] == 4.0 and s["net"] == -2.5


def test_pi_convergents_and_two_arm_returns():
    cf = continued_fraction("3.14159265358979323846264338327950288419716939937510", 5)
    assert cf == [3, 7, 15, 1, 292]
    assert convergents(cf)[:4] == [Fraction(3), Fraction(22, 7), Fraction(333, 106), Fraction(355, 113)]
    rows = {r["q"]: r for r in two_arm_returns(np.pi, 200)}
    assert 7 in rows and 113 in rows and rows[7]["petals"] == 15
    assert rows[113]["distance"] < 2e-4 < rows[7]["distance"]
    exact = {r["q"]: r for r in two_arm_returns(22 / 7, 50)}
    assert exact[7]["distance"] < 1e-9                  # a fraction closes exactly


def test_mode_returns_and_harmonics():
    t = np.array([2 * np.pi, np.pi])
    d = mode_returns(np.array([1.0, 2.0]), t)           # commensurate: both home at t = 2π
    assert d[0] < 1e-12 and d[1] > 1.0
    assert harmonics_above(1.3, np.sqrt(2)) == 2 and harmonics_above(1.5, np.sqrt(2)) == 1
