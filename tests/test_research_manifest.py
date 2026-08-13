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
    _write(tmp_path / "ai_lab/reports/easy/environment_latest.json", {
        "burst_id": "dream-test", "core_versions": {"numpy": "2.1.0"}
    })
    _write(tmp_path / "requirements.txt", "numpy>=1.24\n")
    _write(tmp_path / ".github/workflows/dream-loop.yml", "name: Genesis Dream Loop\n")
    _write(tmp_path / "ai_lab/reports/easy/frontier_latest.json", {"burst_id": "dream-test"})
    _write(tmp_path / "ai_lab/discoveries/research_memory.json", {"version": 2})
    _write(tmp_path / "ai_lab/discoveries/research_backlog.json", {"active_count": 2})
    _write(tmp_path / "ai_lab/reports/easy/research_backlog_latest.md", "operations only")
    _write(tmp_path / "CURRENT_RESEARCH.md", "human view")


def test_manifest_separates_evidence_environment_planning_and_views(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.build_manifest()
    assert manifest["burst_id"] == "dream-test"
    assert manifest["source_code"]["git_sha"] == "source-sha"
    assert manifest["source_code"]["research_source_git_sha"] == "source-sha"
    assert manifest["source_code"]["evidence_snapshot_git_sha"] == "evidence-sha"
    scientific = {row["path"] for row in manifest["scientific_evidence"]}
    environment = {row["path"] for row in manifest["execution_environment"]}
    planning = {row["path"] for row in manifest["planning_and_integrity_state"]}
    views = {row["path"] for row in manifest["derived_human_views"]}
    assert "ai_lab/reports/easy/latest.json" in scientific
    assert "ai_lab/reports/easy/environment_latest.json" in environment
    assert "requirements.txt" in environment
    assert ".github/workflows/dream-loop.yml" in environment
    assert "ai_lab/reports/easy/frontier_latest.json" in planning
    assert "ai_lab/discoveries/research_memory.json" in planning
    assert "ai_lab/discoveries/research_backlog.json" in planning
    assert "ai_lab/reports/easy/research_backlog_latest.md" in views
    assert "CURRENT_RESEARCH.md" in views
    assert manifest["semantics"]["manifest_is_scientific_evidence"] is False
    assert manifest["semantics"]["environment_match_proves_scientific_claim"] is False
    assert manifest["semantics"]["evidence_snapshot_git_sha_is_exact_scientific_evidence_recovery_anchor"] is True


def test_manifest_hash_changes_when_evidence_changes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest()
    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 4})
    after = research_manifest.build_manifest()
    assert before["manifest_content_sha256"] != after["manifest_content_sha256"]
    before_emergence = next(
        row for row in before["scientific_evidence"]
        if row["path"] == "ai_lab/reports/emergence/latest.json"
    )
    after_emergence = next(
        row for row in after["scientific_evidence"]
        if row["path"] == "ai_lab/reports/emergence/latest.json"
    )
    assert before_emergence["sha256"] != after_emergence["sha256"]


def test_manifest_hash_changes_when_environment_contract_changes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    before = research_manifest.build_manifest()
    _write(tmp_path / "requirements.txt", "numpy>=2.0\n")
    after = research_manifest.build_manifest()
    assert before["manifest_content_sha256"] != after["manifest_content_sha256"]


def test_same_manifest_is_idempotent_but_same_burst_different_provenance_fails(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.build_manifest()
    archive = research_manifest.persist_manifest(manifest)
    assert archive.exists()
    assert research_manifest.persist_manifest(manifest) == archive

    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 999})
    changed = research_manifest.build_manifest()
    with pytest.raises(RuntimeError, match="immutable manifest collision"):
        research_manifest.persist_manifest(changed)


def test_latest_alias_matches_immutable_archive(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.run(persist=True)
    archive = research_manifest._ARCHIVE_DIR / "dream-test.json"
    assert archive.exists()
    assert research_manifest._LATEST.exists()
    assert json.loads(archive.read_text()) == manifest
    assert json.loads(research_manifest._LATEST.read_text()) == manifest


def test_verify_existing_manifest_detects_hash_drift_without_rewriting(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manifest = research_manifest.run(persist=True)
    archive = research_manifest._ARCHIVE_DIR / "dream-test.json"
    before = archive.read_text()
    verified = research_manifest.verify_existing_manifest()
    assert verified["valid"] is True
    assert verified["checked_files"] > 0
    assert verified["evidence_snapshot_git_sha"] == "evidence-sha"

    _write(tmp_path / "ai_lab/reports/emergence/latest.json", {"episodes": 404})
    drifted = research_manifest.verify_existing_manifest()
    assert drifted["valid"] is False
    assert any("hash mismatch: ai_lab/reports/emergence/latest.json" in x for x in drifted["errors"])
    assert archive.read_text() == before
    assert json.loads(archive.read_text()) == manifest
