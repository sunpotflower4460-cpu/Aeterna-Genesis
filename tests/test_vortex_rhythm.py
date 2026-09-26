"""A vortex's own rhythm (P9-Q1): spirals from noise set one frequency for the whole medium."""
import numpy as np

from genesis.diagnostics import rhythm as rh
from tools.vortex_rhythm import run


def test_frequency_and_wavenumber_of_a_known_plane_wave():
    n, k, om, dt = 64, 2 * np.pi * 5 / 64, 0.7, 0.1
    x = np.arange(n)[None, :].repeat(n, 0)
    stack = [np.angle(np.exp(1j * (k * x - om * t * dt))) for t in range(200)]
    assert np.allclose(rh.frequencies(np.array(stack), dt), om, atol=1e-9)
    A = np.exp(1j * k * x)
    assert np.allclose(rh.local_wavenumber(A), np.sin(k), atol=1e-9)    # central difference of e^{ikx}
    assert abs(rh.mode(np.r_[np.zeros(10), np.ones(3)], bins=2) - 0.25) < 1e-9


def test_spirals_lock_the_box_to_one_frequency_below_the_vortex_free_one():
    ctrl = run(1.2, 1, n=64, T=300.0, win=60.0, uniform=True)
    assert ctrl["vortices"] == 0
    om = []
    for seed in (1, 2):
        r = run(1.2, seed, n=64, T=300.0, win=60.0)
        assert r["vortices"] >= 2
        lo, mid, hi = r["omega_p5_50_95"]
        assert hi - lo < 0.03 * mid                                   # one rhythm for the whole box
        assert mid < 0.92 * ctrl["omega_p5_50_95"][1]                  # not the vortex-free rhythm
        om.append(mid)
    assert abs(om[0] - om[1]) < 0.01 * om[0]                          # the same rhythm for both seeds
