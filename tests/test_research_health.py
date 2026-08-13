import json

from ai_lab.dream import research_health


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _paths(monkeypatch, tmp_path):
    values = {
        "_EASY": tmp_path / "easy.json",
        "_FRONTIER": tmp_path / "frontier.json",
        "_MEMORY": tmp_path / "memory.json",
        "_CROSS": tmp_path / "cross.json",
        "_CROSS_REPLICATION": tmp_path / "replication.json",
        "_NOTHING": tmp_path / "nothing.json",
        "_REPORT_JSON": tmp_path / "health.json",
        "_REPORT_MD": tmp_path / "health.md",
    }
    for name, path in values.items():
        monkeypatch.setattr(research_health, name, path)
    return values


def _fixture(paths):
    q = "x|X-a|ctx:0123456789abcdef|drive_strength|1.5"
    _write(paths["_EASY"], {"burst_id": "dream-test", "generated_at": "2026-08-13T00:00:00Z"})
    _write(paths["_FRONTIER"], {
        "burst_id": "dream-test",
        "budget": {
            "requested": 4,
            "allocated": {"f": 0, "x": 4, "root": 0},
            "executed": 4,
            "unallocated_due_to_capacity": 0,
            "allocated_but_not_executed": 0,
        },
        "progress_ratchet": {"question_keys": [q]},
    })
    _write(paths["_MEMORY"], {
        "version": 2,
        "entries": [{
            "key": f"progress-question:{q}",
            "kind": "progress_question",
            "question_key": q,
            "times_seen": 1,
        }],
        "counts": {"total": 1, "progress_questions": 1},
        "policy": {
            "progress_ratchet_reads_memory": True,
            "progress_question_history_is_durable": True,
        },
    })
    _write(paths["_CROSS"], {
        "universality_claim": False,
        "official_level_effect": False,
        "promotion_effect": False,
        "hypothesis_confidence_effect": False,
        "changes_world_dynamics": False,
        "same_fingerprint_means_same_physics": False,
        "independent_replication_shadow": {"burst_id": "dream-test"},
    })
    _write(paths["_CROSS_REPLICATION"], {
        "burst_id": "dream-test",
        "completed": True,
        "completion_status": "COMPLETED",
        "results": [{"repeat_hits": 0, "finite_replicates": 3}],
        "integrity": {
            "updates_cumulative_CWX_ledger": False,
            "changes_world_dynamics": False,
            "changes_hypothesis_confidence": False,
            "changes_official_level": False,
            "promotes_rooms": False,
            "same_fingerprint_means_same_physics": False,
            "universality_claim": False,
            "target_outcome_seeded": False,
        },
    })
    _write(paths["_NOTHING"], {
        "mode": "strict-nothing-genesis-meta-control",
        "burst_id": "dream-test",
        "strict_trial_count": 1,
        "strict_nothing": {
            "strict_nothing": True,
            "result": {
                "physical_transition_executed": False,
                "something_observed": False,
                "nothing_to_something_claim": False,
                "result_is_control_construction_not_independent_measurement": True,
            },
        },
    })


def test_healthy_infrastructure_allows_zero_replication_hits(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    report = research_health.build_health()
    assert report["healthy"] is True
    assert report["strict_failure_count"] == 0
    assert report["semantics"]["non_replication_is_failure"] is False


def test_stale_crossworld_replication_is_strict_error(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    replication = json.loads(paths["_CROSS_REPLICATION"].read_text())
    replication["burst_id"] = "dream-old"
    _write(paths["_CROSS_REPLICATION"], replication)
    report = research_health.build_health()
    assert report["healthy"] is False
    assert any(
        row["id"] == "crossworld-replication-current-burst" and row["status"] == "ERROR"
        for row in report["checks"]
    )


def test_legacy_x_question_is_migration_warning_not_scientific_failure(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    legacy = "x|X-a|drive_strength|1.5"
    frontier = json.loads(paths["_FRONTIER"].read_text())
    frontier["progress_ratchet"]["question_keys"] = [legacy]
    _write(paths["_FRONTIER"], frontier)
    memory = json.loads(paths["_MEMORY"].read_text())
    memory["entries"][0]["key"] = f"progress-question:{legacy}"
    memory["entries"][0]["question_key"] = legacy
    _write(paths["_MEMORY"], memory)
    report = research_health.build_health()
    assert report["healthy"] is True
    assert report["warning_count"] >= 1
    assert any(row["id"] == "research-memory-legacy-x-context-debt" for row in report["checks"])


def test_impossible_frontier_budget_fails_closed(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    frontier = json.loads(paths["_FRONTIER"].read_text())
    frontier["budget"]["executed"] = 5
    _write(paths["_FRONTIER"], frontier)
    report = research_health.build_health()
    assert report["healthy"] is False
    assert any(
        row["id"] == "frontier-execution-within-allocation" and row["status"] == "ERROR"
        for row in report["checks"]
    )


def test_durable_memory_metadata_corruption_fails_closed(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    memory = json.loads(paths["_MEMORY"].read_text())
    memory["version"] = 1
    memory["counts"]["progress_questions"] = 0
    memory["policy"].pop("progress_question_history_is_durable")
    _write(paths["_MEMORY"], memory)
    report = research_health.build_health()
    assert report["healthy"] is False
    failed = {row["id"] for row in report["checks"] if row["status"] == "ERROR"}
    assert "research-memory-schema-durable" in failed
    assert "research-memory-progress-count" in failed
    assert "research-memory-ratchet-policy" in failed


def test_run_writes_human_and_machine_health_reports(monkeypatch, tmp_path):
    paths = _paths(monkeypatch, tmp_path)
    _fixture(paths)
    report = research_health.run(persist=True)
    assert report["healthy"] is True
    assert paths["_REPORT_JSON"].exists()
    assert paths["_REPORT_MD"].exists()
    assert "科学的な負の結果" in paths["_REPORT_MD"].read_text()
