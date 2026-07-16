"""Synthetic tests for genesis/diagnostics/vortex_lines_3d.py (Observer 3D, role V).

Key claims under test:
  1. A single well-separated vortex ring traces as exactly ONE closed loop with the correct
     effective radius (length / 2pi) and zero ambiguous cubes / divergence violations / open paths.
  2. Gauge invariance: a global phase offset does not change the traced loop.
  3. Translation invariance: shifting the ring shifts the traced loop's centroid by the same amount.
  4. A field with no defects traces zero loops (no crash, no spurious loops).
"""
import numpy as np

from genesis.diagnostics.vortex_lines_3d import trace_vortex_lines

N = 48
CENTER = (N - 1) / 2.0
R = 12.0
CORE_WIDTH = 1.5


def _grid(n):
    i = np.arange(n, dtype=float)
    return np.meshgrid(i, i, i, indexing="ij")


def _ring_field(n=N, R=R, center=CENTER, charge=1, core_width=CORE_WIDTH):
    # same phase formula as core.field.vortex_ring_phase: charge * atan2(z-cz, rho-R)
    X, Y, Z = _grid(n)
    rho = np.sqrt((X - center) ** 2 + (Y - center) ** 2)
    phase = charge * np.arctan2(Z - center, rho - R)
    dist_to_core = np.sqrt((rho - R) ** 2 + (Z - center) ** 2)
    amp = np.tanh(dist_to_core / core_width)
    return amp * np.exp(1j * phase)


def test_single_ring_traces_as_one_closed_loop_with_correct_radius():
    psi = _ring_field()
    r = trace_vortex_lines(psi)
    assert r["n_cubes_overloaded"] == 0
    assert r["n_unhealed_dangling"] == 0
    assert len(r["open_paths"]) == 0
    assert len(r["loops"]) == 1
    loop = r["loops"][0]
    assert abs(loop["effective_radius"] - R) < 0.75          # sub-cell accuracy expected
    cx, cy, cz = loop["centroid"]
    assert abs(cx - CENTER) < 1.0 and abs(cy - CENTER) < 1.0 and abs(cz - CENTER) < 1.0
    assert loop["mean_curvature"] > 0.0                        # a circle has nonzero curvature
    assert loop["n_points"] > 10                               # a R=12 ring must have many piercings
    # every remaining divergence violation must come from an (inherently unbalanced) 1-pierced
    # dangling cube, never from a "clean" 2-pierced pair -- this is the regression test for the
    # zx face sign bug (external review, 2026-07-16): before the fix, cubes mixing a yz-face and a
    # zx-face (common near a curved ring's tangent regions) had non-canceling flux even though
    # exactly 2 faces were pierced, inflating this count with false positives.
    assert r["n_divergence_violations"] == r["n_cubes_dangling"]


def test_heal_distance_cap_limits_reconnection():
    # a tiny max_heal_distance (smaller than the few-cell tangent-region gaps this ring produces)
    # must leave those gaps unhealed rather than reconnecting them anyway -- regression test for
    # the healing-radius cap (external review, 2026-07-16: unbounded nearest-neighbor healing
    # could in principle bridge two unrelated distant defects into a fake closed loop).
    psi = _ring_field()
    generous = trace_vortex_lines(psi, max_heal_distance=3.0)
    strict = trace_vortex_lines(psi, max_heal_distance=0.1)
    assert generous["n_healed_connections"] > 0
    assert strict["n_healed_connections"] == 0
    assert strict["n_unhealed_dangling"] == generous["n_cubes_dangling"]


def test_gauge_invariance():
    psi = _ring_field()
    r0 = trace_vortex_lines(psi)
    r1 = trace_vortex_lines(np.exp(1j * 1.7) * psi)
    assert len(r0["loops"]) == len(r1["loops"]) == 1
    assert abs(r0["loops"][0]["length"] - r1["loops"][0]["length"]) < 1e-9


def test_translation_invariance():
    psi = _ring_field()
    shift = 3
    psi_shifted = np.roll(psi, shift, axis=0)
    r0 = trace_vortex_lines(psi)
    r1 = trace_vortex_lines(psi_shifted)
    assert len(r0["loops"]) == len(r1["loops"]) == 1
    c0 = np.array(r0["loops"][0]["centroid"])
    c1 = np.array(r1["loops"][0]["centroid"])
    delta = c1 - c0
    assert abs(delta[0] - shift) < 0.5 and abs(delta[1]) < 0.5 and abs(delta[2]) < 0.5
    assert abs(r0["loops"][0]["length"] - r1["loops"][0]["length"]) < 1e-6


def test_no_defects_no_loops():
    psi = np.ones((N, N, N), dtype=complex)
    r = trace_vortex_lines(psi)
    assert r["loops"] == []
    assert r["open_paths"] == []
    assert r["n_cubes_overloaded"] == 0
    assert r["n_unhealed_dangling"] == 0
