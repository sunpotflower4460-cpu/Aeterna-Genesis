import json

from ai_lab.dream import research_backlog


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _paths(monkeypatch, tmp_path):
    paths = {
        "_FRONTIER": tmp_path / "frontier.json",
        "_HEALTH": tmp_path / "health.json",
        "_OUTPUT": tmp_path / "backlog.json",
        "_REPORT_MD": tmp_path / "backlog.md",
    }
    for name, path in paths.items():
        monkeypatch.setattr(research_backlog, name, path)
    return paths


def _frontier(burst="b1", *, requests=None, capability_status="UNMEASURED"):
    return {
        "burst_id": burst,
        "instrument_requests": requests if requests is not None else [{
            "id": "identity-continuity",
            "question": "same individual?",
            "purpose": "measure identity",
            "new_physical_axiom": False,
            "target_morphology_seeded": False,
            "may_use_scaffolded_analogy_lane": False,
            "scaffolded_lane_cannot_count_as_pure_genesis_proof": False,
        }],
        "capability_map": [{
            "id": "persistent_individual_identity",
            "status": capability_status,
        }],
    }


def test_instrument_request_is_durable_and_idempotent_within_same_burst(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _write(paths["_FRONTIER"], _frontier("b1"))
    _write(paths["_HEALTH"], {"burst_id": "b1", "checks": []})
    first = research_backlog.build_backlog(existing={"entries": []})
    row = next(x for x in first["entries"] if x["key"] == "instrument:identity-continuity")
    assert row["status"] == "OPEN"
    assert row["times_requested"] == 1

    second = research_backlog.build_backlog(existing=first)
    row2 = next(x for x in second["entries"] if x["key"] == "instrument:identity-continuity")
    assert row2["times_requested"] == 1


def test_missing_next_burst_does_not_delete_instrument_request(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _write(paths["_FRONTIER"], _frontier("b1"))
    _write(paths["_HEALTH"], {"burst_id": "b1", "checks": []})
    first = research_backlog.build_backlog(existing={"entries": []})

    _write(paths["_FRONTIER"], _frontier("b2", requests=[]))
    _write(paths["_HEALTH"], {"burst_id": "b2", "checks": []})
    second = research_backlog.build_backlog(existing=first)
    row = next(x for x in second["entries"] if x["key"] == "instrument:identity-continuity")
    assert row["status"] == "DORMANT_NOT_REQUESTED_THIS_BURST"
    assert row["times_requested"] == 1


def test_capability_lead_marks_request_satisfied_but_preserves_history(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _write(paths["_FRONTIER"], _frontier("b1"))
    _write(paths["_HEALTH"], {"burst_id": "b1", "checks": []})
    first = research_backlog.build_backlog(existing={"entries": []})

    _write(paths["_FRONTIER"], _frontier("b2", requests=[], capability_status="LEAD"))
    _write(paths["_HEALTH"], {"burst_id": "b2", "checks": []})
    second = research_backlog.build_backlog(existing=first)
    row = next(x for x in second["entries"] if x["key"] == "instrument:identity-continuity")
    assert row["status"] == "CAPABILITY_LEAD_REPORTED"
    assert row["first_requested_burst"] == "b1"
    assert second["policy"]["resolved_entries_are_deleted"] is False


def test_health_warning_is_preserved_then_resolved(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _write(paths["_FRONTIER"], _frontier("b1", requests=[]))
    _write(paths["_HEALTH"], {
        "burst_id": "b1",
        "checks": [{"id": "memory-contract", "status": "WARN", "message": "check memory"}],
    })
    first = research_backlog.build_backlog(existing={"entries": []})
    row = next(x for x in first["entries"] if x["key"] == "infra:memory-contract")
    assert row["status"] == "WARN"
    assert row["times_seen"] == 1

    _write(paths["_FRONTIER"], _frontier("b2", requests=[]))
    _write(paths["_HEALTH"], {
        "burst_id": "b2",
        "checks": [{"id": "memory-contract", "status": "PASS", "message": "ok"}],
    })
    second = research_backlog.build_backlog(existing=first)
    resolved = next(x for x in second["entries"] if x["key"] == "infra:memory-contract")
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_burst"] == "b2"


def test_historical_contextless_x_warning_is_not_permanent_active_debt(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _write(paths["_FRONTIER"], _frontier("b1", requests=[]))
    _write(paths["_HEALTH"], {
        "burst_id": "b1",
        "checks": [{
            "id": "research-memory-legacy-x-context-debt",
            "status": "WARN",
            "message": "legacy entries are intentionally preserved",
        }],
    })
    backlog = research_backlog.build_backlog(existing={"entries": []})
    assert not any(
        row.get("key") == "infra:research-memory-legacy-x-context-debt"
        for row in backlog["entries"]
    )
    assert backlog["active_count"] == 0
    assert backlog["policy"]["historical_contextless_x_warning_is_actionable_debt"] is False


def test_scaffolded_request_stays_explicitly_non_proof(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    request = {
        "id": "growth-accounting",
        "question": "growth?",
        "purpose": "measure growth",
        "new_physical_axiom": False,
        "target_morphology_seeded": False,
        "may_use_scaffolded_analogy_lane": True,
        "scaffolded_lane_cannot_count_as_pure_genesis_proof": True,
    }
    _write(paths["_FRONTIER"], _frontier("b1", requests=[request]))
    _write(paths["_HEALTH"], {"burst_id": "b1", "checks": []})
    backlog = research_backlog.build_backlog(existing={"entries": []})
    row = next(x for x in backlog["entries"] if x["key"] == "instrument:growth-accounting")
    assert row["scaffolded_only"] is True
    assert row["scaffolded_lane_cannot_count_as_pure_genesis_proof"] is True
    assert backlog["policy"]["instrument_request_is_evidence_of_phenomenon"] is False
