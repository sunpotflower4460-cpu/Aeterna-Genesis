"""PR6 test: the committed official 3D Genesis Room room-g001-a is valid and reached Level 2 in full 3D."""

import json
import os

import yaml
from jsonschema import Draft202012Validator

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ROOM = os.path.join(_REPO, "rooms", "official", "room-g001-a")


def _schema(name):
    return Draft202012Validator(json.load(open(os.path.join(_REPO, "schemas", name))))


def test_room_artifacts_exist_and_validate():
    for fn, schema in [("genesis.yaml", "genesis.schema.json"), ("room.yaml", "room.schema.json"),
                       ("dimension-transfer.yaml", "dimension-transfer.schema.json"),
                       ("render.yaml", "render.schema.json")]:
        doc = yaml.safe_load(open(os.path.join(_ROOM, fn)))
        _schema(schema).validate(doc)
    _schema("emergence.schema.json").validate(json.load(open(os.path.join(_ROOM, "emergence.json"))))


def test_room_reached_level_2_full_3d():
    room = yaml.safe_load(open(os.path.join(_ROOM, "room.yaml")))
    assert room["official"] is True
    assert room["dimension_status"]["full_3d"] == "passed"
    assert room["emergence"]["reached_level"] == 2          # vortex lines in full 3D
    for k in ("conservation", "convergence", "reproducibility", "integrity_audit"):
        assert room["physics_status"][k] == "passed"


def test_room_runs_validate_and_are_level_2():
    runs = os.path.join(_ROOM, "runs")
    seeds = sorted(d for d in os.listdir(runs) if d.startswith("seed-"))
    assert len(seeds) >= 3                                    # multi-seed reproducibility
    for s in seeds:
        man = json.load(open(os.path.join(runs, s, "manifest.json")))
        emg = json.load(open(os.path.join(runs, s, "emergence.json")))
        _schema("run.schema.json").validate(man)
        _schema("emergence.schema.json").validate(emg)
        assert man["dimension"] == 3 and man["mode"] == "full-3d"
        assert emg["reached_level"] == 2
        assert emg["natural_emergence"]["target_shape_seeded"] is False


def test_room_convergence_and_reproducibility():
    conv = json.load(open(os.path.join(_ROOM, "convergence.json")))
    assert conv["level_converged"] is True                   # Level 2 across 48/64/80^3
    assert conv["reproducible_checksum"] is True
    assert conv["free_energy_monotone_post_quench"] is True
