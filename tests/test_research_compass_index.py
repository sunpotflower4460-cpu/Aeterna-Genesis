"""P5: the canonical research index is well-formed and RESEARCH_COMPASS.md is generated from it."""

import json
import os
import subprocess
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_index_is_well_formed():
    with open(os.path.join(_REPO, "research", "index.json"), encoding="utf-8") as fh:
        idx = json.load(fh)
    assert idx["whites"] and idx["open_questions"] and idx["audits"]
    for w in idx["whites"]:
        assert {"id", "name", "reached", "tier", "ceiling_reason"} <= set(w)
    for a in idx["audits"]:
        assert os.path.exists(os.path.join(_REPO, a["doc"])), a["doc"]
    with open(os.path.join(_REPO, "app", "public", "aquarium", "templates.json"), encoding="utf-8") as fh:
        tpl_ids = {t["id"] for t in json.load(fh)["templates"]}
    assert {w["aquarium"] for w in idx["whites"] if w.get("aquarium")} <= tpl_ids


def test_compass_is_up_to_date():
    r = subprocess.run([sys.executable, "tools/build_compass.py", "--check"], cwd=_REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
