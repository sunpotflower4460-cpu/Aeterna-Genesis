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


def test_candidate_carries_jobs_diff_and_promotion():
    # Phase 3/4: Live Runner jobs + Discovery Inbox metadata flow into the single catalog source.
    cat = _load().build()
    jobs = {j["job_id"]: j for j in cat.get("jobs", [])}
    assert "job-0001" in jobs and jobs["job-0001"]["result_room"] == "room-g001-a-job-0001"
    cand = {c["room_id"]: c for c in cat["candidate_rooms"]}
    cr = cand["room-g001-a-job-0001"]
    # honest parent diff computed from genesis docs (not a stored label)
    assert cr["diff_vs_parent"]["noise_amplitude"]["from"] == 0.01
    assert cr["diff_vs_parent"]["noise_amplitude"]["to"] == 0.005
    assert cr["parent_reached_level"] == 2 and cr["delta_level"] == cr["reached_level"] - 2
    # promotion pipeline mirrors dimension_status; a candidate is never official / self-promoted
    prom = cr["promotion"]
    assert prom["is_official"] is False
    assert "exploration_2d" in prom["passed"]
    assert prom["current"] in _load().PROMOTION_STAGES
    # replayable (Live Runner recorded fields)
    assert cr["frames_ref"] and cr["lenses"]


def test_genesis_diff_reports_only_changed_knobs():
    m = _load()
    parent = {"initial_state": {"noise_amplitude": 0.01, "correlation_length": 1.0}, "seed": 0}
    child = {"initial_state": {"noise_amplitude": 0.001, "correlation_length": 1.0},
             "protocol": {"quench": {"duration": 8.0}}, "seed": 0}
    kp, kc = m._genesis_knobs(parent), m._genesis_knobs(child)
    diff = {k: {"from": kp.get(k), "to": kc.get(k)} for k in set(kp) | set(kc) if kp.get(k) != kc.get(k)}
    assert set(diff) == {"noise_amplitude", "quench_duration"}  # correlation_length + seed unchanged/added
    assert diff["noise_amplitude"] == {"from": 0.01, "to": 0.001}


def test_catalog_js_assigns_window_catalog(tmp_path):
    m = _load()
    cat = m.build()
    m.write(cat, str(tmp_path))
    js = open(os.path.join(str(tmp_path), "catalog.js")).read()
    assert js.startswith("//") and "window.CATALOG = " in js
    data = json.load(open(os.path.join(str(tmp_path), "catalog.json")))
    assert data["rooms"][0]["room_id"] == "room-g001-a"
