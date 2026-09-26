"""A torus that grows by itself (P11): the ring detector, the local superfluid law, and rings / ± pairs from noise."""
import numpy as np

from genesis.diagnostics import vortex_rings as vr
from genesis.models import gpe_local as gl
from tools import torus_birth as tb


def _ring(L, R, shift=(0, 0, 0)):
    """One vortex ring of radius R about the z axis (the far field goes to phase 0, so no seam sheet)."""
    c = (L - 1) / 2.0
    X, Y, Z = np.meshgrid(*(np.arange(L, dtype=float),) * 3, indexing="ij")
    rho = np.hypot(X - c, Y - c)
    th = np.arctan2(Z - c, rho - R) - np.arctan2(Z - c, rho + R)
    return np.roll(np.exp(1j * th), shift, (0, 1, 2))


def test_detector_finds_one_torus_across_the_seams_and_not_a_line_around_the_box():
    rs = vr.rings(_ring(40, 7.0, shift=(17, -11, 20)))
    assert len(rs) == 1
    r = rs[0]
    assert r["ring"] and r["genus"] == 1 and not r["wraps"] and abs(r["radius"] - 7.0) < 1.0
    assert abs(abs(r["axis"][2]) - 1.0) < 1e-6
    y, x = np.mgrid[:32, :32]
    ph = np.arctan2(y - 15.5, x - 7.5) - np.arctan2(y - 15.5, x - 23.5)            # two opposite straight lines
    pieces = vr.rings(np.repeat(np.exp(1j * ph)[:, :, None], 16, axis=2))          # along z, around the box
    assert len(pieces) == 2 and all(pc["wraps"] and not pc["ring"] for pc in pieces)


def test_local_law_conserves_energy_without_the_bath_and_condenses_with_it():
    p = dict(gl.DEFAULTS, gamma=0.0, dt=0.1)
    psi = _ring(24, 5.0)
    E0 = gl.energy(psi, p)
    for _ in range(100):
        psi = gl.step(psi, p)
    assert abs(gl.energy(psi, p) - E0) < 1e-3 * E0
    q = dict(gl.DEFAULTS, gamma=0.1)
    phi = gl.make_initial((24, 24), np.random.default_rng(0), q)
    for _ in range(600):
        phi = gl.step(phi, q)
    assert abs(np.abs(phi).mean() - 1.0) < 0.2


def test_a_ring_travels_along_its_axis_the_way_the_flow_goes_through_its_hole():
    L, R = 32, 6.0
    p = dict(gl.DEFAULTS, gamma=0.0, dt=0.1)
    psi = _ring(L, R)
    (r0,) = [r for r in vr.rings(psi) if r["ring"]]
    flow = tb.flow_through_hole(gl.velocity(psi), r0["centroid"], r0["axis"], L)
    for _ in range(200):                                                     # t = 20
        psi = gl.step(psi, p)
    (r1,) = [r for r in vr.rings(psi) if r["ring"]]
    along = float(np.dot(tb._mi(r1["centroid"], r0["centroid"], L), r0["axis"]))
    assert np.sign(along) == np.sign(flow) != 0
    assert 0.6 < abs(along) / 20.0 / tb.kelvin(R) < 1.4                     # Kelvin's law for a vortex ring


def test_isolated_pairs_are_found_in_2d():
    y, x = np.mgrid[:64, :64].astype(float)
    psi = np.exp(1j * (np.arctan2(y - 31.5, x - 29.5) - np.arctan2(y - 31.5, x - 33.5)))
    prs = tb.pairs_2d(tb.vortices_2d(psi), 64)
    assert len(prs) == 1 and abs(prs[0]["d"] - 4.0) < 1e-9


def test_rings_are_born_from_noise_in_3d():
    """48³, γ = 0.03, seed 1: at least one tracked ring (born from ψ ≈ 0 + noise) that travels with its hole flow."""
    r = tb.run3d(48, 0.03, 1, 600.0)
    long = [tr for tr in r["tracks"] if tr["last"] - tr["born"] >= 20]
    assert long and all(tr["moves_with_the_flow"] for tr in long)
