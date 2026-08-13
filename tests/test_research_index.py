import json

import pytest

from ai_lab.dream import research_index


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _valid_manifest(*, version=3, source_sha="source-sha"):
    manifest = {
        "version": version,
        "burst_id": "dream-b1",
        "burst_generated_at": "2026-08-13T00:00:00+00:00",
        "source_code": {
            "research_source_git_sha": source_sha,
            "evidence_snapshot_git_sha": "evidence-sha",
            "research_workflow_run_id": "77",
            "research_workflow_run_number": "12",
        },
    }
    manifest["manifest_content_sha256"] = research_index.research_manifest._content_identity(manifest)
    return manifest


def _install(monkeypatch, tmp_path):
    paths = {
        "_MANIFEST": tmp_path / "manifest.json",
        "_HEALTH": tmp_path / "health.json",
        "_BACKLOG": tmp_path / "backlog.json",
        "_FRONTIER": tmp_path / "frontier.json",
        "_ENVIRONMENT": tmp_path / "environment.json",
        "_OUTPUT": tmp_path / "index.json",
        "_REPORT_MD": tmp_path / "history.md",
    }
    for name, path in paths.items():
        monkeypatch.setattr(research_index, name, path)
    _write(paths["_MANIFEST"], _valid_manifest())
    _write(paths["_HEALTH"], {"healthy": True, "strict_failure_count": 0, "warning_count": 1})
    _write(paths["_BACKLOG"], {"active_count": 3, "recommended_next": "instrument:identity-continuity"})
    _write(paths["_FRONTIER"], {
        "progress_ratchet": {
            "status": "ADVANCED",
            "new_question_keys": ["q1", "q2"],
            "replicated_question_keys": ["q0"],
            "next_burst_escape_required": False,
        }
    })
    _write(paths["_ENVIRONMENT"], {
        "burst_id": "dream-b1",
        "python": {"version_info": [3, 11, 9]},
        "core_versions": {"numpy": "2.1.0", "scipy": "1.14.0"},
        "contracts": {"requirements_txt_sha256": "req-sha"},
    })
    return paths


def test_index_points_to_manifest_and_exact_evidence_commit(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    expected_hash = json.loads(paths["_MANIFEST"].read_text())["manifest_content_sha256"]
    index = research_index.build_index(existing={"entries": []})
    assert index["count"] == 1
    row = index["entries"][0]
    assert row["burst_id"] == "dream-b1"
    assert row["manifest_content_sha256"] == expected_hash
    assert row["evidence_snapshot_git_sha"] == "evidence-sha"
    assert row["environment_anchor"]["burst_id"] == "dream-b1"
    assert row["planning_progress"]["new_question_count"] == 2
    assert row["semantics"]["navigation_summary_is_scientific_evidence"] is False
    assert index["policy"]["manifest_self_identity_is_recomputed_before_indexing"] is True


def test_manifest_v3_requires_current_environment_fingerprint(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    paths["_ENVIRONMENT"].unlink()
    with pytest.raises(RuntimeError, match="has no execution environment fingerprint"):
        research_index.build_index(existing={"entries": []})


def test_manifest_v3_rejects_stale_environment_burst(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    environment = json.loads(paths["_ENVIRONMENT"].read_text())
    environment["burst_id"] = "dream-old"
    _write(paths["_ENVIRONMENT"], environment)
    with pytest.raises(RuntimeError, match="environment fingerprint burst mismatch"):
        research_index.build_index(existing={"entries": []})


def test_manifest_metadata_tampering_is_rejected_before_indexing(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    manifest = json.loads(paths["_MANIFEST"].read_text())
    manifest["source_code"]["research_source_git_sha"] = "tampered"
    # Keep the old declared manifest_content_sha256 on purpose.
    _write(paths["_MANIFEST"], manifest)
    with pytest.raises(RuntimeError, match="manifest content identity mismatch"):
        research_index.build_index(existing={"entries": []})


def test_legacy_manifest_remains_readable_without_environment(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    _write(paths["_MANIFEST"], _valid_manifest(version=2))
    paths["_ENVIRONMENT"].unlink()
    index = research_index.build_index(existing={"entries": []})
    assert index["count"] == 1
    assert index["entries"][0]["environment_anchor"]["burst_id"] is None


def test_same_burst_same_manifest_is_idempotent(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    expected_hash = json.loads(paths["_MANIFEST"].read_text())["manifest_content_sha256"]
    first = research_index.build_index(existing={"entries": []})
    second = research_index.build_index(existing=first)
    assert second["count"] == 1
    assert second["entries"][0]["manifest_content_sha256"] == expected_hash


def test_same_burst_different_valid_manifest_fails_closed(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    first = research_index.build_index(existing={"entries": []})
    _write(paths["_MANIFEST"], _valid_manifest(source_sha="different-valid-source"))
    with pytest.raises(RuntimeError, match="research index collision"):
        research_index.build_index(existing=first)


def test_index_preserves_older_bursts_and_writes_human_view(monkeypatch, tmp_path):
    paths = _install(monkeypatch, tmp_path)
    old = {
        "entries": [{
            "burst_id": "dream-b0",
            "burst_generated_at": "2026-08-12T23:00:00+00:00",
            "manifest_content_sha256": "manifest-zero",
        }]
    }
    monkeypatch.setattr(research_index, "_OUTPUT", paths["_OUTPUT"])
    _write(paths["_OUTPUT"], old)
    index = research_index.run(persist=True)
    assert [row["burst_id"] for row in index["entries"]] == ["dream-b0", "dream-b1"]
    assert paths["_REPORT_MD"].exists()
    text = paths["_REPORT_MD"].read_text()
    assert "evidence-sha" in text
    assert "not a scientific confidence ranking" in text
