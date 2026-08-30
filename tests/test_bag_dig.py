"""The bag ruler must not treat holes, triangles, or a filled room as a body.

Geometry-only controls. No physics run. Gates are frozen in replay.BAG_CRITERION.
"""
import importlib.util
from pathlib import Path

import numpy as np

_REPLAY = Path(__file__).resolve().parents[1] / "ai_lab/reports/easy/verify-20260829-bag-dig/replay.py"
_spec = importlib.util.spec_from_file_location("bag_dig_replay", _REPLAY)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_filled_bulk_with_holes_is_not_a_bag():
    a = np.ones((48, 48))
    a[10, 10] = 0.0
    a[30, 22] = 0.0
    cls = _mod.classify_amp(a, windings=2)
    assert cls["dense_is_room_bulk"] is True
    assert cls["bag_candidate"] is False
    assert cls["n_hole_components"] >= 2
    assert cls["bag_rescued_by_holes"] is False
    assert cls["holes_are_not_the_body"] is True


def test_localized_square_is_a_bag_candidate_on_the_ruler_only():
    a = np.full((48, 48), 0.05)
    a[16:28, 16:28] = 1.0
    cls = _mod.classify_amp(a)
    assert cls["bag_candidate"] is True
    assert cls["dense_is_room_bulk"] is False


def test_hole_count_does_not_flip_a_fill_into_a_bag():
    a = np.ones((48, 48))
    for i in range(8):
        a[6 + 4 * i, 8] = 0.0
    cls = _mod.classify_amp(a, windings=8)
    assert cls["n_hole_components"] >= 8
    assert cls["bag_candidate"] is False


def test_stripes_two_grounds_are_not_one_body():
    phi = np.ones((48, 48))
    phi[:, 24:] = -1.0
    cls = _mod.classify_signed_two_ground(phi)
    assert cls["two_grounds_present"] is True
    assert cls["one_body_bag"] is False
    assert cls["not_promoted_to_bag_mainline"] is True


def test_not_success_tokens_exclude_holes_and_triangles():
    assert "hole_count_as_body" in _mod.NOT_SUCCESS
    assert "triangle" in _mod.NOT_SUCCESS
    assert "ring_pinch_1_to_2" in _mod.NOT_SUCCESS
