"""Light-and-phase white in 3D (vortex strings): the gates, and a cross-check with the 2D module."""
import numpy as np

from genesis.models import abelian_higgs as a2
from genesis.models import abelian_higgs_nd as an


def test_same_as_the_2d_module_bit_for_bit():
    p = dict(a2.DEFAULTS)
    s2 = a2.make_initial((32, 32), np.random.default_rng(1), p)
    sn = s2
    for _ in range(200):
        s2, sn = a2.step(*s2, p), an.step(*sn, p)
    assert all(np.array_equal(x, y) for x, y in zip(s2, sn))
    assert np.array_equal(a2.winding(s2[0], s2[2]), an.winding(sn[0], sn[2])[(0, 1)])


def test_gauss_gauge_and_reversal_in_3d():
    p = dict(an.DEFAULTS)
    s0 = an.make_initial((12, 12, 12), np.random.default_rng(2), p)
    s0 = (s0[0] + 0.3, s0[1], s0[2], s0[3])
    s = s0
    for _ in range(150):
        s = an.step(*s, p)
    assert np.abs(an.gauss_residual(s[0], s[1], s[3])).max() < 1e-12
    # gauge invariance
    alpha = np.random.default_rng(3).uniform(-np.pi, np.pi, (12, 12, 12))
    g = (np.exp(1j * alpha) * s0[0], np.exp(1j * alpha) * s0[1],
         np.stack([s0[2][i] + np.roll(alpha, -1, i) - alpha for i in range(3)]), s0[3].copy())
    for _ in range(150):
        g = an.step(*g, p)
    assert abs(an.energy(*s, p) - an.energy(*g, p)) < 1e-8 * an.energy(*s, p)
    assert np.allclose(np.abs(s[0]), np.abs(g[0]), atol=1e-9)
    # time runs backwards
    r = (s[0], -s[1], s[2], -s[3])
    for _ in range(150):
        r = an.step(*r, p)
    assert np.abs(r[0] - s0[0]).max() < 1e-8


def test_a_straight_string_pair_carries_2pi_through_every_slice():
    """Two antiparallel strings along z (phase winding put in, no gauge field put in), relaxed with cooling:
    in every z-slice each string is pierced once and carries ±2π of flux (the tube's tail needs a wide disk)."""
    p = dict(an.DEFAULTS, gamma=0.05)
    n, nz = 48, 2
    yy, xx = np.mgrid[:n, :n].astype(float)
    cy, x1, x2 = 23.5, 11.5, 35.5
    phase = sum(np.arctan2(yy - cy + k * n, xx - x1 + m * n) - np.arctan2(yy - cy + k * n, xx - x2 + m * n)
                for m in range(-2, 3) for k in range(-2, 3))
    xi = 1.0 / np.sqrt(p["lam"])
    sl = np.tanh(np.hypot(yy - cy, xx - x1) / xi) * np.tanh(np.hypot(yy - cy, xx - x2) / xi) * np.exp(1j * phase)
    phi = np.repeat(sl[:, :, None], nz, axis=2)                  # axes (y, x, z): strings along z
    s = (phi, np.zeros(phi.shape, complex), np.zeros((3,) + phi.shape), np.zeros((3,) + phi.shape))
    for _ in range(1500):
        s = an.step(*s, p)
    w = an.winding(s[0], s[2])[(0, 1)]                            # the (y, x) plane: pierced by z-strings
    assert an.string_length(s[0], s[2]) == 2 * nz
    F = an.wrap(an.plaquette(s[2], 0, 1))
    for z in range(nz):
        ys, xs = np.nonzero(w[:, :, z])
        assert sorted(w[ys, xs, z].tolist()) == [-1, 1]
        for y, x in zip(ys, xs):
            dy = np.minimum(abs(yy - y), n - abs(yy - y))
            dx = np.minimum(abs(xx - x), n - abs(xx - x))
            flux = F[:, :, z][(dy ** 2 + dx ** 2) <= 11 ** 2].sum() / (2 * np.pi)
            assert abs(flux - w[y, x, z]) < 0.05
    # both strings run around the box along z: every z-slice is pierced once each way
    assert an.wrapped_axes(s[0], s[2]) == [2]
    assert an.slice_piercings(s[0], s[2], 2).tolist() == [[1, 1]] * nz
    from tools.higgs3d_first_look import slice_flux
    sf = slice_flux(s[0], s[2], 2)
    assert sf["piercings"] == 2 * nz and sf["worst"] < 0.05
