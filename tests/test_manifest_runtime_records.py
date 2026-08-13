import json

from ai_lab.dream import research_manifest


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) if isinstance(value, (dict, list)) else str(value))


def test_v4_manifest_hashes_protocol_and_postflight_runtime_records(monkeypatch, tmp_path):
    monkeypatch.setattr(research_manifest, "_REPO", tmp_path)
    monkeypatch.setattr(research_manifest, "_EASY", tmp_path / "ai_lab/reports/easy/latest.json")
    monkeypatch.setattr(research_manifest, "_ENVIRONMENT", tmp_path / "ai_lab/reports/easy/environment_latest.json")
    monkeypatch.setattr(research_manifest, "_PROTOCOL", tmp_path / "ai_lab/reports/easy/protocol_latest.json")
    monkeypatch.setattr(research_manifest, "_repo_git_sha", lambda: "evidence-sha")
    monkeypatch.setattr(research_manifest, "_evidence_git_sha", lambda: "evidence-sha")
    monkeypatch.setattr(research_manifest, "_research_git_sha", lambda: "source-sha")

    _write(research_manifest._EASY, {"burst_id": "dream-test", "generated_at": "now"})
    _write(research_manifest._ENVIRONMENT, {"burst_id": "dream-test"})
    _write(research_manifest._PROTOCOL, {"burst_id": "dream-test", "protocol_sha256": "p"})
    _write(tmp_path / "ai_lab/reports/easy/research_contract_latest.json", {"burst_id": "dream-test", "valid": True})
    _write(tmp_path / "ai_lab/reports/easy/runtime_context_latest.json", {"burst_id": "dream-test", "valid": True})

    manifest = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    protocol_paths = {row["path"] for row in manifest["execution_protocol"]}
    planning_paths = {row["path"] for row in manifest["planning_and_integrity_state"]}
    assert "ai_lab/reports/easy/protocol_latest.json" in protocol_paths
    assert "ai_lab/reports/easy/research_contract_latest.json" in planning_paths
    assert "ai_lab/reports/easy/runtime_context_latest.json" in planning_paths
    assert manifest["semantics"]["postflight_integrity_records_are_manifest_hashed"] is True
