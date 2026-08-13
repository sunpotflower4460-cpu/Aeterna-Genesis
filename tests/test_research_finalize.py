from ai_lab.dream import research_finalize


def test_finalize_orders_view_health_backlog_then_manifest(monkeypatch):
    calls = []

    monkeypatch.setattr(
        research_finalize.research_compass,
        "run",
        lambda persist: calls.append(("compass", persist)) or {"burst_id": "b1"},
    )
    monkeypatch.setattr(
        research_finalize.research_health,
        "run",
        lambda persist: calls.append(("health", persist)) or {"burst_id": "b1", "healthy": True},
    )
    monkeypatch.setattr(
        research_finalize.research_backlog,
        "run",
        lambda persist: calls.append(("backlog", persist)) or {"last_burst": "b1", "active_count": 2},
    )
    monkeypatch.setattr(
        research_finalize.research_manifest,
        "run",
        lambda persist: calls.append(("manifest", persist)) or {
            "burst_id": "b1", "manifest_content_sha256": "abc"
        },
    )

    out = research_finalize.run(persist=True)
    assert calls == [
        ("compass", True),
        ("health", True),
        ("backlog", True),
        ("manifest", True),
    ]
    assert out["healthy"] is True
    assert out["backlog"]["active_count"] == 2


def test_finalize_preserves_unhealthy_state_without_turning_it_into_science(monkeypatch):
    monkeypatch.setattr(research_finalize.research_compass, "run", lambda persist: {})
    monkeypatch.setattr(
        research_finalize.research_health,
        "run",
        lambda persist: {
            "healthy": False,
            "strict_failure_count": 1,
            "integrity": {"changes_scientific_truth_gate": False},
        },
    )
    monkeypatch.setattr(research_finalize.research_backlog, "run", lambda persist: {})
    monkeypatch.setattr(
        research_finalize.research_manifest,
        "run",
        lambda persist: {"burst_id": "b1", "manifest_content_sha256": "abc"},
    )
    out = research_finalize.run(persist=False)
    assert out["healthy"] is False
    assert out["health"]["strict_failure_count"] == 1
    assert out["health"]["integrity"]["changes_scientific_truth_gate"] is False
