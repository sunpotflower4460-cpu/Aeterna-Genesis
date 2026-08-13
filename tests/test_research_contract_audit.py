import json

from ai_lab.dream import research_contract_audit


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _valid_protocol():
    return {
        "valid": True,
        "protocol_sha256": "p",
        "workflow_sha256": "w",
        "recognized_option_count": 10,
        "disabled_required_lanes": [],
        "errors": [],
    }


def test_contract_audit_accepts_registered_safe_requests(monkeypatch, tmp_path):
    frontier = tmp_path / "frontier.json"
    backlog = tmp_path / "backlog.json"
    _write(frontier, {
        "burst_id": "dream-test",
        "instrument_requests": [{
            "id": "identity-continuity",
            "new_physical_axiom": False,
            "target_morphology_seeded": False,
            "may_use_scaffolded_analogy_lane": True,
            "scaffolded_lane_cannot_count_as_pure_genesis_proof": True,
        }],
    })
    _write(backlog, {
        "entries": [{
            "kind": "instrument_request",
            "request_id": "identity-continuity",
            "new_physical_axiom": False,
            "target_morphology_seeded": False,
            "scaffolded_only": False,
            "scaffolded_lane_cannot_count_as_pure_genesis_proof": False,
        }]
    })
    monkeypatch.setattr(research_contract_audit, "_FRONTIER", frontier)
    monkeypatch.setattr(research_contract_audit, "_BACKLOG", backlog)
    monkeypatch.setattr(research_contract_audit.production_protocol, "build_contract", _valid_protocol)
    report = research_contract_audit.build_audit()
    assert report["valid"] is True
    assert report["errors"] == []
    assert report["integrity"]["instrument_request_is_evidence_of_phenomenon"] is False


def test_unregistered_durable_instrument_or_protocol_drift_fails(monkeypatch, tmp_path):
    frontier = tmp_path / "frontier.json"
    backlog = tmp_path / "backlog.json"
    _write(frontier, {"burst_id": "dream-test", "instrument_requests": []})
    _write(backlog, {
        "entries": [{"kind": "instrument_request", "request_id": "unknown-old-request"}]
    })
    monkeypatch.setattr(research_contract_audit, "_FRONTIER", frontier)
    monkeypatch.setattr(research_contract_audit, "_BACKLOG", backlog)
    monkeypatch.setattr(
        research_contract_audit.production_protocol,
        "build_contract",
        lambda: {
            **_valid_protocol(),
            "valid": False,
            "disabled_required_lanes": [{"option": "open_ended_probes"}],
            "errors": ["one or more production research lanes are accidentally disabled"],
        },
    )
    report = research_contract_audit.build_audit()
    assert report["valid"] is False
    assert "unknown-old-request" in report["unregistered_backlog_instrument_ids"]
    assert any("accidentally disabled" in error for error in report["errors"])


def test_missing_or_malformed_contract_input_fails_closed(monkeypatch, tmp_path):
    missing = tmp_path / "missing-frontier.json"
    malformed = tmp_path / "bad-backlog.json"
    malformed.write_text("{not-json")
    monkeypatch.setattr(research_contract_audit.production_protocol, "build_contract", _valid_protocol)
    report = research_contract_audit.build_audit(frontier_path=missing, backlog_path=malformed)
    assert report["valid"] is False
    assert any("frontier report is missing" in error for error in report["errors"])
    assert any("research backlog is unreadable or malformed" in error for error in report["errors"])


def test_unsafe_durable_backlog_request_is_validated_not_reduced_to_id(monkeypatch, tmp_path):
    frontier = tmp_path / "frontier.json"
    backlog = tmp_path / "backlog.json"
    _write(frontier, {"burst_id": "dream-test", "instrument_requests": []})
    _write(backlog, {"entries": [{
        "kind": "instrument_request",
        "request_id": "identity-continuity",
        "new_physical_axiom": True,
        "target_morphology_seeded": True,
        "scaffolded_only": False,
        "scaffolded_lane_cannot_count_as_pure_genesis_proof": False,
    }]})
    monkeypatch.setattr(research_contract_audit.production_protocol, "build_contract", _valid_protocol)
    report = research_contract_audit.build_audit(frontier_path=frontier, backlog_path=backlog)
    assert report["valid"] is False
    assert any("new physical axiom" in error for error in report["errors"])
    assert any("target morphology" in error for error in report["errors"])
