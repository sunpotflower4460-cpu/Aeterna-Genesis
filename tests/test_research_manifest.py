import json

import pytest

from ai_lab.dream import research_manifest


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        path.write_text(json.dumps(content))
    else:
        path.write_text(str(content))


def _install(monkeypatch, tmp_path):
    monkeypatch.setattr(research_manifest, "_REPO", tmp_path)
    monkeypatch.setattr(research_manifest, "_EASY", tmp_path / "ai_lab/reports/easy/latest.json")
    monkeypatch.setattr(research_manifest, "_ENVIRONMENT", tmp_path / "ai_lab/reports/easy/environment_latest.json")
    monkeypatch.setattr(research_manifest, "_PROTOCOL", tmp_path / "ai_lab/reports/easy/protocol_latest.json")
    monkeypatch.setattr(research_manifest, "_LATEST", tmp_path / "ai_lab/reports/easy/research_manifest_latest.json")
    monkeypatch.setattr(research_manifest, "_ARCHIVE_DIR", tmp_path / "ai_lab/reports/easy/manifests")
    monkeypatch.setattr(research_manifest, "_repo_git_sha", lambda: "evidence-sha")
    monkeypatch.setenv("GITHUB_SHA", "source-sha")
    monkeypatch.setenv("GITHUB_RUN_ID", "77")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "12")
    _write(research_manifest._EASY, {
        "burst_id": "dream-test",
        "generated_at": "2026-08-13T00:00:00+00:00",
    })
    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 3})
    _write(research_manifest._ENVIRONMENT, {
        "burst_id": "dream-test",
        "core_versions": {"numpy": "2.1.0"},
        "contracts": {
            "requirements_txt_sha256": "req-one",
            "dream_loop_workflow_sha256": "workflow-one",
        },
    })
    _write(research_manifest._PROTOCOL, {
        "burst_id": "dream-test",
        "protocol_sha256": "protocol-one",
        "parsed_config": {"trials": 8},
    })
    _write(tmp_path / "requirements.txt", "numpy>=1.24\n")
    _write(tmp_path / ".github/workflows/dream-loop.yml", "name: Genesis Dream Loop\n")
    _write(tmp_path / "ai_lab/reports/easy/frontier_latest.json", {"burst_id": "dream-test"})
    _write(tmp_path / "ai_lab/discoveries/research_memory.json", {"version": 2})
    _write(tmp_path / "ai_lab/discoveries/research_backlog.json", {"active_count": 2})
    _write(tmp_path / "ai_lab/reports/easy/research_backlog_latest.md", "operations only")
    _write(tmp_path / "CURRENT_RESEARCH.md", "human view")


def test_manifest_separates_evidence_environment_protocol_planning_and_views(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    assert manifest["version"] == 4
    assert manifest["burst_id"] == "dream-test"
    assert manifest["source_code"]["git_sha"] == "source-sha"
    assert manifest["source_code"]["research_source_git_sha"] == "source-sha"
    assert manifest["source_code"]["evidence_snapshot_git_sha"] == "evidence-sha"
    scientific = {row["path"] for row in manifest["scientific_evidence"]}
    environment = {row["path"] for row in manifest["execution_environment"]}
    protocol = {row["path"] for row in manifest["execution_protocol"]}
    planning = {row["path"] for row in manifest["planning_and_integrity_state"]}
    views = {row["path"] for row in manifest["derived_human_views"]}
    assert "ai_lab/reports/easy/latest.json" in scientific
    assert environment == {"ai_lab/reports/easy/environment_latest.json"}
    assert protocol == {"ai_lab/reports/easy/protocol_latest.json"}
    assert "requirements.txt" not in environment
    assert ".github/workflows/dream-loop.yml" not in environment
    assert "ai_lab/reports/easy/frontier_latest.json" in planning
    assert "ai_lab/discoveries/research_memory.json" in planning
    assert "ai_lab/discoveries/research_backlog.json" in planning
    assert "ai_lab/reports/easy/research_backlog_latest.md" in views
    assert "CURRENT_RESEARCH.md" in views
    assert manifest["semantics"]["manifest_is_scientific_evidence"] is False
    assert manifest["semantics"]["environment_match_proves_scientific_claim"] is False
    assert manifest["semantics"]["protocol_match_proves_scientific_claim"] is False
    assert manifest["semantics"]["environment_report_required_for_production_v4_archive"] is True
    assert manifest["semantics"]["protocol_report_required_for_production_v4_archive"] is True
    assert manifest["semantics"]["evidence_snapshot_git_sha_is_exact_scientific_evidence_recovery_anchor"] is True


def test_production_v4_requires_current_burst_environment(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    research_manifest._ENVIRONMENT.unlink()
    with pytest.raises(RuntimeError, match="requires a current environment fingerprint"):
        research_manifest.build_manifest(require_environment=True, require_protocol=True)


def test_production_v4_requires_current_burst_protocol(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    research_manifest._PROTOCOL.unlink()
    with pytest.raises(RuntimeError, match="requires a current protocol fingerprint"):
        research_manifest.build_manifest(require_environment=True, require_protocol=True)


def test_stale_environment_or_protocol_is_rejected_even_in_migration_mode(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    environment = json.loads(research_manifest._ENVIRONMENT.read_text())
    environment["burst_id"] = "dream-old"
    _write(research_manifest._ENVIRONMENT, environment)
    with pytest.raises(RuntimeError, match="environment fingerprint burst mismatch"):
        research_manifest.build_manifest(require_environment=False, require_protocol=False)
    environment["burst_id"] = "dream-test"
    _write(research_manifest._ENVIRONMENT, environment)
    protocol = json.loads(research_manifest._PROTOCOL.read_text())
    protocol["burst_id"] = "dream-old"
    _write(research_manifest._PROTOCOL, protocol)
    with pytest.raises(RuntimeError, match="protocol fingerprint burst mismatch"):
        research_manifest.build_manifest(require_environment=False, require_protocol=False)


def test_read_only_migration_can_inspect_old_evidence_without_environment_or_protocol(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    research_manifest._ENVIRONMENT.unlink()
    research_manifest._PROTOCOL.unlink()
    manifest = research_manifest.build_manifest(require_environment=False, require_protocol=False)
    assert manifest["version"] == 4
    assert manifest["execution_environment"] == []
    assert manifest["execution_protocol"] == []
    assert manifest["counts"]["execution_environment_files"] == 0
    assert manifest["counts"]["execution_protocol_files"] == 0


def test_manifest_hash_changes_when_evidence_changes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 4})
    after = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    assert before["manifest_content_sha256"] != after["manifest_content_sha256"]
    before_emergence = next(row for row in before["scientific_evidence"] if row["path"] == "ai_lab/reports/emergence/latest.json")
    after_emergence = next(row for row in after["scientific_evidence"] if row["path"] == "ai_lab/reports/emergence/latest.json")
    assert before_emergence["sha256"] != after_emergence["sha256"]


def test_manifest_hash_changes_when_research_time_environment_contract_changes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    environment = json.loads(research_manifest._ENVIRONMENT.read_text())
    environment["contracts"]["requirements_txt_sha256"] = "req-two"
    _write(research_manifest._ENVIRONMENT, environment)
    after = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    assert before["manifest_content_sha256"] != after["manifest_content_sha256"]


def test_manifest_hash_changes_when_parsed_protocol_changes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    protocol = json.loads(research_manifest._PROTOCOL.read_text())
    protocol["protocol_sha256"] = "protocol-two"
    protocol["parsed_config"]["trials"] = 9
    _write(research_manifest._PROTOCOL, protocol)
    after = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    assert before["manifest_content_sha256"] != after["manifest_content_sha256"]


def test_postflight_checkout_contract_change_alone_does_not_relabel_old_burst(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    _write(tmp_path / "requirements.txt", "numpy>=99\n")
    _write(tmp_path / ".github/workflows/dream-loop.yml", "name: unrelated-later-checkout\n")
    after = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    assert before["manifest_content_sha256"] == after["manifest_content_sha256"]


def test_same_manifest_is_idempotent_but_same_burst_different_provenance_fails(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    archive = research_manifest.persist_manifest(manifest)
    assert archive.exists()
    assert research_manifest.persist_manifest(manifest) == archive
    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 999})
    changed = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    with pytest.raises(RuntimeError, match="immutable manifest collision"):
        research_manifest.persist_manifest(changed)


def test_persist_rejects_declared_manifest_identity_tampering(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.build_manifest(require_environment=True, require_protocol=True)
    manifest["source_code"]["research_ref"] = "tampered-after-hash"
    with pytest.raises(RuntimeError, match="manifest content identity mismatch"):
        research_manifest.persist_manifest(manifest)


def test_latest_alias_matches_immutable_archive(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.run(persist=True, require_environment=True, require_protocol=True)
    archive = research_manifest._ARCHIVE_DIR / "dream-test.json"
    assert archive.exists()
    assert research_manifest._LATEST.exists()
    assert json.loads(archive.read_text()) == manifest
    assert json.loads(research_manifest._LATEST.read_text()) == manifest


def test_verify_existing_manifest_detects_hash_drift_without_rewriting(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.run(persist=True, require_environment=True, require_protocol=True)
    archive = research_manifest._ARCHIVE_DIR / "dream-test.json"
    before = archive.read_text()
    verified = research_manifest.verify_existing_manifest()
    assert verified["valid"] is True
    assert verified["checked_files"] > 0
    assert verified["evidence_snapshot_git_sha"] == "evidence-sha"
    assert verified["declared_manifest_content_sha256"] == verified["recomputed_manifest_content_sha256"]
    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 404})
    drifted = research_manifest.verify_existing_manifest()
    assert drifted["valid"] is False
    assert any("hash mismatch: ai_lab/reports/emergence/latest.json" in x for x in drifted["errors"])
    assert archive.read_text() == before
    assert json.loads(archive.read_text()) == manifest


def test_verify_existing_manifest_detects_protocol_hash_drift(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    research_manifest.run(persist=True, require_environment=True, require_protocol=True)
    protocol = json.loads(research_manifest._PROTOCOL.read_text())
    protocol["protocol_sha256"] = "changed-after-archive"
    _write(research_manifest._PROTOCOL, protocol)
    verified = research_manifest.verify_existing_manifest()
    assert verified["valid"] is False
    assert any("hash mismatch: ai_lab/reports/easy/protocol_latest.json" in x for x in verified["errors"])


def test_verify_existing_manifest_detects_metadata_tampering_even_when_file_hashes_are_unchanged(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    research_manifest.run(persist=True, require_environment=True, require_protocol=True)
    archive = research_manifest._ARCHIVE_DIR / "dream-test.json"
    tampered = json.loads(archive.read_text())
    tampered["source_code"]["research_ref"] = "refs/heads/fake"
    _write(archive, tampered)
    verified = research_manifest.verify_existing_manifest()
    assert verified["valid"] is False
    assert "manifest content identity mismatch" in verified["errors"]
