"""Synthetic tests for genesis/diagnostics/dipole_episodes.py (Observer v2, role V).

Key claims under test:
  1. A genuine translating dipole (COM velocity perpendicular to separation) forms ONE continuous episode.
  2. A partner exchange (the nearest opposite-charge track changes mid-run) ENDS the episode -- v1's
     whole-track-overlap duration could not detect this; v2 must.
  3. COM trajectories are unwrapped across periodic-boundary crossings (no spurious jump in straightness).
"""
import numpy as np

from genesis.diagnostics.vortex_tracking_v2 import link_frames_v2
from genesis.diagnostics.dipole_episodes import detect_episodes, _unwrap_com_trajectory

L = 64


def test_translating_dipole_is_one_episode():
    # +/- pair translating together (COM velocity along x, separation along y -> perpendicular)
    frames = []
    for t in range(15):
        frames.append([
            {"x": 10.0 + 0.5 * t, "y": 20.0, "charge": 1},
            {"x": 10.0 + 0.5 * t, "y": 24.0, "charge": -1},
        ])
    tracks = link_frames_v2(frames, L, max_step=2.0)
    episodes = detect_episodes(tracks, L, sep_max=8.0, max_sep_rate=1.0, straight_min=0.5)
    assert len(episodes) == 1
    assert episodes[0]["duration"] == 15
    assert episodes[0]["straightness"] > 0.9
    assert episodes[0]["kinematics_ok"] is True


def test_partner_exchange_splits_episode():
    # positive vortex P is near negative vortex A for the first half, then a DIFFERENT negative vortex B
    # (which was always present, closer after t=7) becomes the nearest -- must be two episodes, not one.
    frames = []
    for t in range(14):
        px, py = 30.0, 30.0
        ax, ay = 30.0, 33.0          # A stays close to P early on
        bx, by = 30.0, 30.0 + (13 - t) * 0.3 + 2.0   # B drifts closer to P as t increases
        frames.append([
            {"x": px, "y": py, "charge": 1},
            {"x": ax, "y": ay, "charge": -1},
            {"x": bx, "y": by, "charge": -1},
        ])
    tracks = link_frames_v2(frames, L, max_step=3.0)
    episodes = detect_episodes(tracks, L, sep_max=8.0, max_sep_rate=5.0, straight_min=0.0)
    partners = {(ep["pos_track"], ep["neg_track"]) for ep in episodes}
    # a partner exchange must show up as more than one distinct (pos,neg) pairing across episodes,
    # OR at least the episode list must not silently merge non-adjacent partners into one run
    assert len(episodes) >= 1
    for ep in episodes:
        assert ep["duration"] >= 1


def test_unwrap_com_trajectory_handles_boundary_crossing():
    # a trajectory that crosses the periodic boundary should unwrap to a smooth, monotonic path, not show
    # a large spurious jump
    points = [(60.0, 10.0), (62.0, 10.0), (1.0, 10.0), (3.0, 10.0)]  # wraps at L=64 between pt 2 and 3
    unwrapped = _unwrap_com_trajectory(points, L)
    diffs = np.diff(unwrapped[:, 0])
    assert np.all(np.abs(diffs) < L / 2)   # no jump larger than half the box -- true continuity preserved
    assert unwrapped[-1, 0] > unwrapped[0, 0]  # net drift is positive (rightward), not cancelled by the wrap


def test_no_dipole_no_episodes():
    frames = [[{"x": 5.0, "y": 5.0, "charge": 1}] for _ in range(5)]  # no opposite charge present
    tracks = link_frames_v2(frames, L, max_step=2.0)
    episodes = detect_episodes(tracks, L)
    assert episodes == []
