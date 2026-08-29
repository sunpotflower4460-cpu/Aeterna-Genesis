"""Synthetic controls for the one-body-bag classifier.

Validators only — not an emergence claim. A filled bulk with holes must NOT
score as a bag. A localized blob may. Doughnut topology is measured, not required.
"""
import importlib.util
from pathlib import Path

import numpy as np

_REPLAY = Path(__file__).resolve().parents[1] / "ai_lab" / "reports" / "easy" / "verify-20260829-one-body-bag" / "replay.py"
_spec = importlib.util.spec_from_file_location("one_body_bag_replay", _REPLAY)
bag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bag)


def test_filled_bulk_with_two_holes_is_not_a_bag():
    amp = np.ones((32, 32))
    amp[8:11, 8:11] = 0.0
    amp[20:23, 20:23] = 0.0
    out = bag.classify_amp(amp)
    assert out["grown"] is True
    assert out["dense_is_room_bulk"] is True
    assert out["bag_candidate"] is False
    assert out["n_hole_components"] == 2
    assert out["body_topology"]["kind"] == "not_applicable_no_bounded_body"
    assert out["holes_are_not_the_body"] is True


def test_localized_square_is_bag_candidate_balloon():
    amp = np.full((32, 32), 0.05)
    amp[10:22, 10:22] = 1.0
    out = bag.classify_amp(amp)
    assert out["bag_candidate"] is True
    assert out["dense_is_room_bulk"] is False
    assert out["n_significant_dense"] == 1
    assert out["body_topology"]["kind"] == "balloon"


def test_localized_annulus_is_bag_with_doughnut_topology_not_required():
    yy, xx = np.ogrid[:40, :40]
    r = np.sqrt((yy - 20.0) ** 2 + (xx - 20.0) ** 2)
    amp = np.full((40, 40), 0.05)
    amp[(r >= 6) & (r <= 12)] = 1.0
    out = bag.classify_amp(amp)
    assert out["bag_candidate"] is True
    assert out["body_topology"]["kind"] == "doughnut"
    # doughnut is measured, never a success gate
    assert "doughnut" not in bag.NOT_SUCCESS


def test_two_blobs_are_not_one_body():
    amp = np.full((32, 32), 0.05)
    amp[4:12, 4:12] = 1.0
    amp[20:28, 20:28] = 1.0
    out = bag.classify_amp(amp)
    assert out["n_significant_dense"] == 2
    assert out["bag_candidate"] is False


def test_3d_ball_is_balloon_and_solid_torus_is_doughnut():
    N = 28
    x = np.arange(N) - (N - 1) / 2.0
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    ball = np.where(X ** 2 + Y ** 2 + Z ** 2 < 8 ** 2, 1.0, 0.05)
    out_ball = bag.classify_amp(ball)
    assert out_ball["bag_candidate"] is True
    assert out_ball["body_topology"]["kind"] == "balloon"

    torus = np.where((np.sqrt(X ** 2 + Y ** 2) - 8) ** 2 + Z ** 2 < 3.5 ** 2, 1.0, 0.05)
    out_t = bag.classify_amp(torus)
    assert out_t["bag_candidate"] is True
    assert out_t["body_topology"]["kind"] == "doughnut"


def test_criterion_frozen_keys():
    need = {
        "amp_max_grown", "mean_amp_grown", "dense_rel_max", "min_body_frac", "max_body_frac",
        "max_span_frac", "persist_snapshots", "hole_rel_max", "min_hole_voxels",
    }
    assert set(bag.BAG_CRITERION) == need
    assert bag.NOT_SUCCESS == ("triangle", "ring_pinch_1_to_2", "F7", "hole_count_as_body")
