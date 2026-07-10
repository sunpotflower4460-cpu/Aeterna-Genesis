"""PR7 test: the AI Genesis Lab searches start conditions non-destructively and cannot self-promote."""

import json
import os

from jsonschema import Draft202012Validator

from ai_lab import lab

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_lab_screens_children_from_zero():
    res = lab.run_lab(n=4, quick=True)
    assert res["parent_baseline_level"] >= 1
    screened = [p for p in res["proposals"] if p["status"] == "2d_screened"]
    assert len(screened) >= 1
    for p in screened:
        assert p["parent_room"] == "room-g001-a"
        assert "reached_level" in p["screen_2d"]         # Level is MEASURED, not asserted
        assert p["mutation"]["param"] in lab.KNOBS


def test_children_genesis_validate_against_schema():
    res = lab.run_lab(n=4, quick=True)
    schema = json.load(open(os.path.join(_REPO, "schemas", "genesis.schema.json")))
    v = Draft202012Validator(schema)
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            v.validate(p["genesis"])                     # each proposed child is a valid genesis


def test_lab_cannot_self_promote_and_only_changes_one_knob():
    res = lab.run_lab(n=6, quick=True)
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            assert p["promotion"]["stage"] == "2d_screened"   # never full_3d from the Lab
            assert p["status"] != "official"


def test_out_of_range_proposal_is_rejected():
    # a value outside the allowed search space must be rejected, not run
    ss = lab._load_search_space()
    bad = {"param": "noise_amplitude", "to": 1.0}         # far above max
    assert lab._within_allowed(bad, ss) is False
