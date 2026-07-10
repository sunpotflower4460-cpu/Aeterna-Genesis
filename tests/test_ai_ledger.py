"""PR-A test: the AI discovery ledger persists+accumulates, and candidate rooms stay non-official."""

import json
import os

import yaml
from jsonschema import Draft202012Validator

from ai_lab import lab

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_ledger_record_is_idempotent(tmp_path):
    path = str(tmp_path / "ledger.json")
    res = lab.run_lab(n=6, quick=True)
    a = lab.record_ledger(res, path=path)
    b = lab.record_ledger(res, path=path)                    # re-record same run
    assert len(a["discoveries"]) == len(b["discoveries"])    # append-only-by-key: no churn
    keys = [d["key"] for d in b["discoveries"]]
    assert keys == sorted(set(keys))                         # deduped + sorted
    for d in b["discoveries"]:
        assert "screen_2d" in d and "stage" in d


def test_committed_ledger_is_reviewable():
    path = os.path.join(_REPO, "ai_lab", "discoveries", "ledger.json")
    assert os.path.exists(path), "the committed discovery ledger must exist for the AI to review"
    led = json.load(open(path))
    assert led["parent_room"] == "room-g001-a"
    assert len(led["discoveries"]) >= 1
    for d in led["discoveries"]:
        assert d["stage"] in ("2d_screened", "local_3d", "rejected_in_3d")


def test_committed_candidate_room_is_non_official():
    cdir = os.path.join(_REPO, "rooms", "candidates")
    rooms = [d for d in os.listdir(cdir) if os.path.isdir(os.path.join(cdir, d))] if os.path.isdir(cdir) else []
    assert rooms, "expected at least one AI candidate room"
    room_schema = Draft202012Validator(json.load(open(os.path.join(_REPO, "schemas", "room.schema.json"))))
    for rid in rooms:
        r = yaml.safe_load(open(os.path.join(cdir, rid, "room.yaml")))
        room_schema.validate(r)
        assert r["official"] is False                        # never official
        assert r["parent_room"] == "room-g001-a"             # parent is preserved, not overwritten
        assert r["dimension_status"]["full_3d"] != "passed"  # full-3D NOT claimed (not promoted)


def test_best_proposal_excludes_the_noop():
    res = lab.run_lab(n=6, quick=True)
    best = lab._best_proposal(res)
    if best is not None:
        assert best["mutation"]["to"] != best["mutation"]["from"]   # a real change, not the parent value
