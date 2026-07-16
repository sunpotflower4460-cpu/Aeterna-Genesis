"""Synthetic tests for genesis/diagnostics/vortex_lines_3d.py (Observer 3D, role V).

Key claims under test:
  1. A single well-separated vortex ring traces as exactly ONE closed loop with the correct
     effective radius (length / 2pi) and zero ambiguous cubes / divergence violations / open paths.
  2. Gauge invariance: a global phase offset does not change the traced loop.
  3. Translation invariance: shifting the ring shifts the traced loop's centroid by the same amount.
  4. A field with no defects traces zero loops (no crash, no spurious loops).
"""
import numpy as np

import genesis.diagnostics.vortex_lines_3d as vl3d
from genesis.diagnostics.vortex_lines_3d import trace_vortex_lines
from genesis.diagnostics.plaquette_ledger import _z_vortex_line

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


def test_ring_radius_robustness():
    # AUDIT.md/experiment.yaml claim robustness across R=6..18, but until now that claim was
    # backed by nothing beyond this module-level R=12 constant -- no parametrized test or
    # persisted artifact actually exercised other radii (found by external review, 2026-07-16).
    # Verify the claim directly rather than asserting it only in prose.
    for R_test in (6.0, 9.0, 12.0, 15.0, 18.0):
        psi = _ring_field(R=R_test)
        r = trace_vortex_lines(psi)
        assert len(r["loops"]) == 1, "R=%g: expected exactly 1 loop, got %d" % (R_test, len(r["loops"]))
        loop = r["loops"][0]
        assert abs(loop["effective_radius"] - R_test) < max(0.75, 0.1 * R_test), \
            "R=%g: effective_radius=%g" % (R_test, loop["effective_radius"])


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


def test_open_chain_at_seam_is_one_path_not_two():
    # a straight vortex line uniform in z: this module's cube construction does not wrap the
    # z-direction seam (see module docstring), so this line hits it and must be reported as ONE
    # open path spanning the full line, not fragmented into two duplicate/reversed fragments --
    # regression test for the walk() terminal-endpoint-not-marked-visited bug (external review,
    # 2026-07-16): without the fix, the far endpoint of the first walk was left unvisited and got
    # walked again (backwards), producing a second spurious fragment.
    psi = _z_vortex_line(20, +1)
    r = trace_vortex_lines(psi)
    assert len(r["loops"]) == 0
    assert len(r["open_paths"]) == 1
    assert r["open_paths"][0]["n_points"] == 20


def test_no_defects_no_loops():
    psi = np.ones((N, N, N), dtype=complex)
    r = trace_vortex_lines(psi)
    assert r["loops"] == []
    assert r["open_paths"] == []
    assert r["n_cubes_overloaded"] == 0
    assert r["n_unhealed_dangling"] == 0


def test_same_sign_two_face_cube_is_overloaded_not_clean(monkeypatch):
    # a cube with exactly 2 pierced faces whose fluxes have the SAME sign (here, both z-faces
    # outward-flux +1) cannot be a valid single-line pass-through -- entry and exit must cancel
    # to zero net divergence. Pairing them anyway (as an earlier version of this module did,
    # requiring only abs(f)==1 on both faces) would silently wire together two faces that don't
    # actually connect via one line -- regression test for the same-sign-pair bug (external
    # review, 2026-07-16). Bypasses face_windings/psi to directly control the single cube's faces.
    W_xy = np.zeros((1, 1, 2), dtype=int)
    W_xy[0, 0, 0] = -1   # bottom (z=0) outward flux = -W_xy[0,0,0] = +1
    W_xy[0, 0, 1] = +1   # top    (z=1) outward flux = +W_xy[0,0,1] = +1  (SAME sign as bottom)
    W_yz = np.zeros((2, 1, 1), dtype=int)
    W_zx = np.zeros((1, 2, 1), dtype=int)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((3, 3, 3), dtype=complex))
    assert r["n_cubes_overloaded"] == 1
    assert r["n_cubes_dangling"] == 0
    assert r["loops"] == []
    assert r["open_paths"] == []


def test_isolated_unhealed_dangling_face_is_a_single_point_open_path(monkeypatch):
    # a single dangling face (1 pierced face in its only candidate cube) with no OTHER dangling
    # face nearby to heal with, and no clean-cube-side neighbor either, must still be surfaced in
    # open_paths (as a 1-point entry) rather than silently vanishing from the returned geometry
    # while only being counted in n_unhealed_dangling -- regression test for the isolated-dangling
    # bug (external review, 2026-07-16).
    W_xy = np.zeros((1, 1, 2), dtype=int)
    W_xy[0, 0, 0] = -1   # the only nonzero face: bottom (z=0) outward flux = +1
    W_yz = np.zeros((2, 1, 1), dtype=int)
    W_zx = np.zeros((1, 2, 1), dtype=int)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((3, 3, 3), dtype=complex))
    assert r["n_cubes_dangling"] == 1
    assert r["n_healed_connections"] == 0
    assert r["n_unhealed_dangling"] == 1
    assert r["loops"] == []
    assert len(r["open_paths"]) == 1
    assert r["open_paths"][0]["n_points"] == 1


def test_duplicate_healing_edge_is_skipped_not_double_counted(monkeypatch):
    # Two faces of the SAME clean 2-pierced cube can each also be the sole pierced face of their
    # OTHER neighboring cube (making them "dangling" too) and are geometrically close enough for
    # the healing pass to reconsider pairing them -- adding a second edge on top of the existing
    # clean-pairing edge would create a duplicate degree-2 connection that collapses into a
    # spurious 2-node closed loop and gets silently dropped by the len(path)>=3 filter, instead of
    # being reported as the small open fragment it actually is (found by external review,
    # 2026-07-16).
    W_xy = np.zeros((3, 3, 4), dtype=int)
    W_xy[1, 1, 1] = -1   # cube (1,1,1)'s bottom z-face outward flux = +1
    W_xy[1, 1, 2] = -1   # cube (1,1,1)'s top z-face outward flux = -1 -- clean pair (sum=0)
    # cube (1,1,0)'s only pierced face is the shared face with (1,1,1) -> dangling
    # cube (1,1,2)'s only pierced face is the shared face with (1,1,1) -> dangling
    W_yz = np.zeros((4, 3, 3), dtype=int)
    W_zx = np.zeros((3, 4, 3), dtype=int)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((4, 4, 4), dtype=complex))
    assert r["loops"] == []
    assert len(r["open_paths"]) == 1
    assert r["open_paths"][0]["n_points"] == 2
    assert r["n_healed_connections"] == 0   # already-connected pair must not be double-counted


def test_n_cubes_dangling_counts_cubes_not_unique_faces(monkeypatch):
    # A single face can be the sole pierced face of BOTH its neighboring cubes independently --
    # that's 2 dangling CUBES (matching n_divergence_violations, which counts per-cube) sharing 1
    # unique face (deduplicated for pairing purposes only). n_cubes_dangling must report the cube
    # count its name promises, not the deduplicated face count (found by external review,
    # 2026-07-16).
    W_xy = np.zeros((1, 1, 3), dtype=int)
    W_xy[0, 0, 1] = 1   # the only nonzero face: shared between cube (0,0,0) and cube (0,0,1)
    W_yz = np.zeros((2, 1, 2), dtype=int)
    W_zx = np.zeros((1, 2, 2), dtype=int)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((3, 3, 3), dtype=complex))
    assert r["n_cubes_dangling"] == 2
    assert r["n_divergence_violations"] == 2
    assert r["n_cubes_dangling"] == r["n_divergence_violations"]


def _two_isolated_dangling_cubes(sign_a, sign_b):
    # Two separate, single-pierced-face cubes a few cells apart along x, each with no OTHER
    # pierced face (no clean pair anywhere) -- their bottom z-face outward-flux sign is controlled
    # independently via W_xy[i,0,0] = -sign (bottom face flux = -W_xy[i,0,0]).
    W_xy = np.zeros((3, 1, 2), dtype=int)
    W_xy[0, 0, 0] = -sign_a
    W_xy[2, 0, 0] = -sign_b
    W_yz = np.zeros((4, 1, 1), dtype=int)
    W_zx = np.zeros((3, 2, 1), dtype=int)
    return W_xy, W_yz, W_zx


def test_same_sign_dangling_faces_are_not_healed(monkeypatch):
    # Two dangling half-edges with the SAME outward-flux sign (both "entries" or both "exits")
    # cannot represent one continuous line crossing the gap between them -- pairing them anyway
    # (as an earlier version of this module's healing pass did, ignoring sign and pairing purely
    # by distance) would fabricate a segment joining two unrelated sources/sinks, the same
    # physical inconsistency the same-sign clean-pair fix addresses for a single cube (found by
    # external review, 2026-07-16).
    W_xy, W_yz, W_zx = _two_isolated_dangling_cubes(+1, +1)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((4, 4, 4), dtype=complex))
    assert r["n_healed_connections"] == 0
    assert r["n_unhealed_dangling"] == 2
    assert r["loops"] == []
    assert len(r["open_paths"]) == 2
    assert all(p["n_points"] == 1 for p in r["open_paths"])


def test_opposite_sign_dangling_faces_are_healed(monkeypatch):
    # Same geometry as test_same_sign_dangling_faces_are_not_healed but with opposite signs (one
    # "exit", one "entry") -- this DOES represent a single continuous line crossing the gap and
    # must be healed.
    W_xy, W_yz, W_zx = _two_isolated_dangling_cubes(+1, -1)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((4, 4, 4), dtype=complex))
    assert r["n_healed_connections"] == 1
    assert r["n_unhealed_dangling"] == 0
    assert r["loops"] == []
    assert len(r["open_paths"]) == 1
    assert r["open_paths"][0]["n_points"] == 2


def test_two_sided_dangling_face_is_excluded_from_healing_pool(monkeypatch):
    # A face that is dangling from BOTH its neighboring cubes (a complete tangent pass-through,
    # needing no external connection) must be excluded from the healing PAIRING POOL entirely --
    # not merely deduplicated to one arbitrarily-signed entry (an earlier version of this fix did
    # only that), which left it eligible to be healed to an unrelated nearby endpoint purely
    # depending on which of its two opposite signs happened to survive dedup. Here a genuinely
    # single-sided dangling face (cube R) sits within healing range of the two-sided face (shared
    # by cubes P and Q) but must NEVER be paired to it (found by external review, 2026-07-16).
    W_xy = np.zeros((3, 1, 3), dtype=int)
    W_xy[0, 0, 1] = 1    # shared face between cube (0,0,0) [sign +1] and cube (0,0,1) [sign -1]
    W_xy[2, 0, 0] = -1   # cube (2,0,0)'s only pierced face, sign +1 -- genuinely single-sided
    W_yz = np.zeros((4, 1, 2), dtype=int)
    W_zx = np.zeros((3, 2, 2), dtype=int)
    monkeypatch.setattr(vl3d, "face_windings", lambda *a, **k: (W_xy, W_yz, W_zx, 0.1))
    r = vl3d.trace_vortex_lines(np.zeros((4, 4, 4), dtype=complex))
    assert r["n_cubes_dangling"] == 3          # cubes (0,0,0), (0,0,1), (2,0,0)
    assert r["n_healed_connections"] == 0      # the two-sided face must never be healed to R
    assert r["n_unhealed_dangling"] == 1       # only R's genuinely single-sided face
    assert r["loops"] == []
    assert len(r["open_paths"]) == 2           # the two-sided face, and R's face, both isolated
    assert all(p["n_points"] == 1 for p in r["open_paths"])
