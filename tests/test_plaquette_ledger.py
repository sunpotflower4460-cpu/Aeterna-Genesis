"""Orientation plaquette ledger (LT-3) — synthetic known-answer tests. role V, physics-free.

Also pins the responsibility boundaries: plaquette (complex-phase) winding is DISTINCT from volume Betti
(topology_betti) and from global line winding (winding_reliability).
"""
import numpy as np

from genesis.diagnostics.plaquette_ledger import plaquette_ledger as pl, ledger_map_distance
from genesis.diagnostics import topology_betti as tb


def _grid(n):
    x = np.arange(n) - (n - 1) / 2.0
    return np.meshgrid(x, x, x, indexing="ij")


def _z_vortex_line(n=20, charge=1):
    X, Y, Z = _grid(n)
    return np.tanh(np.sqrt(X ** 2 + Y ** 2) / 2.0) * np.exp(1j * charge * np.arctan2(Y, X))


def test_uniform_field_has_no_defects():
    r = pl(np.ones((18, 18, 18), complex))
    assert r["total"]["absolute"] == 0 and r["total"]["net"] == 0


def test_z_vortex_line_is_orientation_specific():
    n = 20
    r = pl(_z_vortex_line(n, +1))
    xy, yz, zx = (r["orientations"][k] for k in ("xy", "yz", "zx"))
    assert xy["net"] >= n - 2 and xy["positive"] >= n - 2       # one +1 per z-slice
    assert yz["absolute"] <= 2 and zx["absolute"] <= 2          # line lies in / parallel to these planes


def test_negative_line_flips_sign():
    r = pl(_z_vortex_line(20, -1))
    assert r["orientations"]["xy"]["net"] <= -18


def test_gauge_invariance_counts_and_hash():
    v = _z_vortex_line(20, +1)
    r0 = pl(v)
    r1 = pl(np.exp(1j * 1.3) * v)
    assert r0["total"] == r1["total"] and r0["map_hash"] == r1["map_hash"]


def test_plus_minus_pair_nets_to_zero():
    n = 20
    X, Y, Z = _grid(n)
    pair = np.exp(1j * (np.arctan2(Y, X - 4) - np.arctan2(Y, X + 4))) * np.ones((n, n, n))
    r = pl(pair)
    assert r["orientations"]["xy"]["net"] == 0 and r["orientations"]["xy"]["absolute"] > 0


def test_global_line_winding_is_not_plaquette_winding():
    """Smooth phase ramp e^{i 2pi x/L}: global line winding W=1 but ZERO plaquette winding everywhere."""
    n = 18
    ramp = np.exp(1j * 2 * np.pi * (np.arange(n)[:, None, None] / n) * np.ones((n, n, n)))
    r = pl(ramp)
    assert r["total"]["absolute"] == 0


def test_low_amplitude_plaquettes_flagged_invalid():
    n = 20
    v = _z_vortex_line(n, +1)
    amp = np.abs(v).copy()
    amp[8:12, 8:12, :] = 1e-3                                 # punch a genuine low-amplitude tube
    holed = amp * np.exp(1j * np.angle(v))
    r = pl(holed, amp_threshold=0.1)                          # fixed gate -> the tube is below it
    assert r["total"]["invalid"] > 0


def test_ledger_map_distance_zero_for_same_field_and_gauge():
    v = _z_vortex_line(20, +1)
    assert ledger_map_distance(v, v)["total"] == 0
    assert ledger_map_distance(v, np.exp(1j * 0.5) * v)["total"] == 0     # gauge-invariant
    assert ledger_map_distance(v, np.roll(v, 4, axis=0))["total"] > 0     # a shifted line differs


def test_plaquette_ledger_is_distinct_from_volume_betti():
    """A solid torus of MATERIAL (real amplitude, uniform phase) has volume b1=1 but NO phase winding."""
    mask = tb.solid_torus()                                    # boolean material torus
    field = mask.astype(np.complex128)                         # amplitude only, phase = 0 everywhere
    betti = tb.betti3d(mask)
    ledger = pl(field)
    assert betti["b1"] == 1 and betti["genus"] == 1            # material topology sees the handle
    assert ledger["total"]["absolute"] == 0                    # phase-defect ledger sees nothing (correct)
