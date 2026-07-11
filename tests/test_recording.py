"""Phase 0 test: the field-recording pipeline is honest and non-destructive.

The recorder saves DOWNSAMPLED, quantized snapshots of fields the simulation already computes so the
Observatory can replay the REAL measured fields (no fake particles). These tests check the recorder
round-trips, and that every official Room ships a decodable field.json + a render-manifest whose lenses
map to measured physics with honesty flags (changes_physics=false, decorative_particles=false)."""

import os
import sys

import numpy as np
import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.recording.recorder import FieldRecorder, downsample  # noqa: E402

OFFICIAL = os.path.join(_REPO, "rooms", "official")


def test_downsample_exact_shape_2d_and_3d():
    assert downsample(np.random.rand(128, 90), (48, 48)).shape == (48, 48)
    assert downsample(np.random.rand(64, 64, 64), (20, 20, 20)).shape == (20, 20, 20)


def test_recorder_roundtrip_reconstructs_within_quantization():
    rng = np.random.default_rng(0)
    rec = FieldRecorder(2, (32, 32)).declare("f", "src", "u")
    truth = [rng.standard_normal((80, 80)) for _ in range(4)]
    for i, a in enumerate(truth):
        rec.add(float(i), {"f": a})
    doc = rec.field_doc()
    dec = FieldRecorder.decode_lens(doc, "f")
    assert dec.shape == (4, 32, 32)
    # quantization error is bounded by one step of the stored [vmin,vmax] range
    L = doc["lenses"]["f"]
    step = (L["vmax"] - L["vmin"]) / 255.0
    ref = np.stack([downsample(a, (32, 32)) for a in truth], 0)
    assert np.max(np.abs(dec - ref)) <= step + 1e-9


def test_recorder_marks_physics_unchanged():
    rec = FieldRecorder(2, (16, 16)).declare("f", "src", "u")
    rec.add(0.0, {"f": np.zeros((16, 16))})
    doc = rec.field_doc()
    assert doc["honesty"]["changes_physics"] is False
    assert doc["honesty"]["decorative_particles"] is False


def _official_rooms():
    if not os.path.isdir(OFFICIAL):
        return []
    return [d for d in sorted(os.listdir(OFFICIAL)) if os.path.isdir(os.path.join(OFFICIAL, d))]


def test_every_official_room_has_decodable_recorded_fields():
    import json
    rooms = _official_rooms()
    assert rooms, "no official rooms found"
    for room in rooms:
        rdir = os.path.join(OFFICIAL, room)
        fp = os.path.join(rdir, "runs", "seed-0000", "field.json")
        assert os.path.exists(fp), "%s missing recorded field.json" % room
        doc = json.load(open(fp))
        assert doc["honesty"]["changes_physics"] is False
        assert doc["honesty"]["decorative_particles"] is False
        lens = next(iter(doc["lenses"]))
        dec = FieldRecorder.decode_lens(doc, lens)
        assert dec.shape == (doc["nframes"],) + tuple(doc["grid"])
        assert np.isfinite(dec).all()


def test_every_official_room_render_manifest_maps_to_measured_physics():
    for room in _official_rooms():
        rm = os.path.join(OFFICIAL, room, "render-manifest.yaml")
        assert os.path.exists(rm), "%s missing render-manifest.yaml" % room
        man = yaml.safe_load(open(rm))
        assert man["data_source"] == "physics"
        assert man["separated_from_physics_data"] is True
        assert man["lenses"], "%s: no lenses" % room
        for l in man["lenses"]:
            assert l["source"]["field"], "%s: lens %s has no source field" % (room, l["lens"])
            assert l["honesty"]["changes_physics"] is False
            assert l["honesty"]["decorative_particles"] is False
