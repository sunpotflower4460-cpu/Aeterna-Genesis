import json

from ai_lab.dream import research_contract_audit


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


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
        }]
    })
    monkeypatch.setattr(research_contract_audit, "_FRONTIER", frontier)
    monkeypatch.setattr(research_contract_audit, "_BACKLOG", backlog)
    monkeypatch.setattr(
        research_contract_audit.production_protocol,
        "build_contract",
        lambda: {
            "valid": True,
            "protocol_sha256": "p",
            "workflow_sha256": "w",
            "recognized_option_count": 10,
            "disabled_required_lanes": [],
            "errors": [],
        },
    )
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
            "valid": False,
            "protocol_sha256": "p",
            "workflow_sha256": "w",
            "recognized_option_count": 10,
            "disabled_required_lanes": [{"option": "open_ended_probes"}],
            "errors": ["one or more production research lanes are accidentally disabled"],
        },
    )
    report = research_contract_audit.build_audit()
    assert report["valid"] is False
    assert "unknown-old-request" in report["unregistered_backlog_instrument_ids"]
    assert any("accidentally disabled" in error for error in report["errors"])
