"""PR8 test: the catalog generator is the single source; official rooms stay distinct from candidates."""

import importlib.util
import json
import os

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load():
    path = os.path.join(_REPO, "tools", "build_catalog.py")
    spec = importlib.util.spec_from_file_location("build_catalog", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_catalog_has_official_room_level_2():
    cat = _load().build()
    assert len(cat["rooms"]) >= 1
    room = next(r for r in cat["rooms"] if r["room_id"] == "room-g001-a")
    assert room["kind"] == "official_3d_room" and room["official"] is True
    assert room["reached_level"] == 2
    assert all(v == "passed" for v in room["physics_status"].values())
    assert len(room["runs"]) >= 3                        # multi-seed


def test_evidence_counts_consistent():
    cat = _load().build()
    ev = cat["evidence_library"]
    assert ev["count"] == len(ev["experiments"])
    assert sum(ev["role_counts"].values()) == ev["count"]


def test_official_and_candidates_are_distinct():
    cat = _load().build()
    # AI candidates never appear inside the official rooms list
    assert isinstance(cat["ai_candidates"], list)
    assert all(r["kind"] == "official_3d_room" for r in cat["rooms"])
    # candidate rooms are surfaced but marked non-official and distinct from the official rooms
    assert isinstance(cat.get("candidate_rooms"), list)
    official_ids = {r["room_id"] for r in cat["rooms"]}
    for cr in cat["candidate_rooms"]:
        assert cr["official"] is False
        assert cr["room_id"] not in official_ids


def test_ai_discovery_ledger_surfaces_in_catalog():
    cat = _load().build()
    assert len(cat["ai_candidates"]) >= 1                # the accumulated ledger is visible in the app
    for c in cat["ai_candidates"]:
        assert c["kind"] == "ai_candidate" and "screen_2d_level" in c


def test_catalog_js_assigns_window_catalog(tmp_path):
    m = _load()
    cat = m.build()
    m.write(cat, str(tmp_path))
    js = open(os.path.join(str(tmp_path), "catalog.js")).read()
    assert js.startswith("//") and "window.CATALOG = " in js
    data = json.load(open(os.path.join(str(tmp_path), "catalog.json")))
    assert data["rooms"][0]["room_id"] == "room-g001-a"
