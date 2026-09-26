"""Yin and yang that become one (P9-Q2): the breather instrument, and breathers grown from a near-uniform start."""
import numpy as np

from genesis.models import wave_klein_gordon as kg
from tools import yinyang_breathers as yb


def _placed_breather(wm):
    m = np.sqrt(yb.LAM)
    w = wm * m
    kap = np.sqrt(m * m - w * w)
    x = np.arange(yb.N) - yb.N / 2
    pi = 4 * kap / np.cosh(kap * x)                    # φ = 0, φ_t = 4 a ω / cosh(κx) with a = κ/ω
    p = dict(kg.DEFAULTS, potential="sine_gordon", lam=yb.LAM, noise=0.0, absorb=0.05, absorb_width=yb.B)
    _, _, _, fr, ed = yb.window(np.zeros(yb.N), pi, p, kg.damping_mask((yb.N,), yb.B), 0.0, 200, 800)
    return yb.lumps(fr, ed, m), 4 * np.arctan(kap / w)


def test_the_instrument_reads_an_exact_breather():
    for wm in (0.4, 0.6):
        L, A_exact = _placed_breather(wm)
        (r,) = L["lumps"]
        assert r["breather"] and r["net_charge"] == [0]
        assert abs(r["omega_over_m"] - wm) < 0.04                    # FFT resolution 2π/800 → 0.039 m
        assert abs(r["A"] - A_exact) < 0.15
        assert r["pair_cycles"] >= 15 and r["dipole_flips"] >= 15    # the ± pair swaps sides every half beat
    L, _ = _placed_breather(0.8)
    (small,) = L["lumps"]
    assert small["pair_cycles"] == 0 and not small["breather"]       # A < π: the pair never crosses the hill


def test_breathers_grow_from_a_near_uniform_start():
    r = yb.run(1.5, 1, windows=((1500, 600),))
    w = r["windows"][0]
    br = [x for x in w["lumps"] if x["breather"]]
    assert len(br) >= 5
    assert all(x["omega_over_m"] < 1.0 and x["net_charge"] == [0] for x in br)
