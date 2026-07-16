"""Synthetic tests for genesis/diagnostics/level3_motion.py (Level-3 spontaneous-motion observer, role V).

Three scenarios that any honest discriminator must separate correctly:
  1. a genuine translating +/- dipole among many jittery decoy pairs -> level3_reached=True.
  2. the WHOLE population drifting together (global/numerical advection, not a local structure) ->
     level3_reached=False (the jitter floor rises with the population and absorbs it).
  3. pure jitter, no coherent pair at all -> no candidates, level3_reached=False.
"""
import numpy as np

from genesis.diagnostics.level3_motion import (
    link_frames, dipole_events, level3_verdict, track_step_sizes, box_centroid_drift,
    mutual_neighbor_durations,
)

L = 64
PERSIST_MIN = 10


def _make_frames(rng, n_decoys=20, bulk=False, dipole_speed=2.0, n_frames=20):
    x0, y0 = 10.0, 10.0
    decoy_x = rng.uniform(15, 55, n_decoys)
    decoy_y = rng.uniform(5, 55, n_decoys)
    frames = []
    for t in range(n_frames):
        drift = dipole_speed * t if bulk else 0.0
        cores = [
            {"x": (x0 + drift + (dipole_speed * t if not bulk else 0)) % L, "y": y0, "charge": 1},
            {"x": (x0 + drift + (dipole_speed * t if not bulk else 0) + 3.0) % L, "y": y0, "charge": -1},
        ]
        for i in range(n_decoys):
            cores.append({"x": (decoy_x[i] + drift + rng.normal(0, 0.3)) % L,
                          "y": (decoy_y[i] + rng.normal(0, 0.3)) % L,
                          "charge": 1 if i % 2 == 0 else -1})
        frames.append(cores)
    return frames


def _run(frames):
    tracks = link_frames(frames, L, max_step=3.0)
    cands, others = dipole_events(tracks, L, persist_min=PERSIST_MIN, sep_max=6.0, straight_min=0.5)
    steps = track_step_sizes(tracks, L)
    verdict = level3_verdict(cands, steps, persist_min=PERSIST_MIN, speed_margin=3.0, straight_margin=2.0)
    return tracks, cands, verdict


def test_true_dipole_reaches_level3():
    rng = np.random.default_rng(1)
    frames = _make_frames(rng, n_decoys=20, bulk=False, dipole_speed=2.0)
    tracks, cands, v = _run(frames)
    assert v["level3_reached"] is True
    assert v["verdict"] == "level3_dipole_candidate"
    assert v["best"]["mean_sep"] < 6.0


def test_bulk_drift_is_not_a_dipole():
    # the WHOLE population drifts together -- a global/numerical artifact, not a local self-formed pair.
    rng = np.random.default_rng(1)
    frames = _make_frames(rng, n_decoys=20, bulk=True, dipole_speed=2.0)
    _tracks, _cands, v = _run(frames)
    assert v["level3_reached"] is False


def test_pure_jitter_has_no_dipole_event():
    rng = np.random.default_rng(2)
    frames = [cores[2:] for cores in _make_frames(rng, n_decoys=20, bulk=False, dipole_speed=2.0)]
    _tracks, cands, v = _run(frames)
    assert cands == []
    assert v["level3_reached"] is False
    assert v["verdict"] == "no_dipole_event"


def test_box_centroid_drift_is_informational_only():
    rng = np.random.default_rng(3)
    frames = _make_frames(rng, n_decoys=5, bulk=False, dipole_speed=1.0, n_frames=8)
    d = box_centroid_drift(frames, L)
    assert d.shape[1] == 2
    assert np.all(np.isfinite(d))


def test_mutual_neighbor_durations_includes_short_lived_pairs():
    # dipole_events would drop this pair below persist_min; durations should still see it
    rng = np.random.default_rng(4)
    frames = _make_frames(rng, n_decoys=10, bulk=False, dipole_speed=1.5, n_frames=6)
    tracks = link_frames(frames, L, max_step=3.0)
    durations = mutual_neighbor_durations(tracks, L, sep_max=6.0)
    assert any(d >= 5 for d in durations)  # the true pair overlaps for ~the full 6-frame window


def test_periodic_wrap_delta_is_shortest_path():
    from genesis.diagnostics.level3_motion import _wrap_delta
    assert abs(_wrap_delta(1.0, 64) - 1.0) < 1e-9
    assert abs(_wrap_delta(63.0, 64) - (-1.0)) < 1e-9
    assert abs(_wrap_delta(-63.0, 64) - 1.0) < 1e-9
