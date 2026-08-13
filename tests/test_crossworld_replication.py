import json

from ai_lab.dream import cross_world_emergence
from ai_lab.dream import crossworld_replication


def _primary_match():
    return {
        "strict_zero_aligned_matches": 1,
        "signature_overlap_only_matches": 0,
        "g001_pattern_matches": [{
            "g001_pattern_id": "X-test",
            "status": "CROSS_WORLD_ZERO_ALIGNED_LEAD",
            "g001_start_purities": ["Z-A:minimal-white"],
            "matched_world_zero_pairs": ["o3-vector@Z-A"],
            "projection_coverage": 1.0,
        }],
    }


def test_prime_report_is_current_burst_incomplete_not_scientific_negative():
    out = crossworld_replication.prime_report(burst_id="dream-now", base_seed=7)
    assert out["burst_id"] == "dream-now"
    assert out["completed"] is False
    assert out["completion_status"] == "NOT_COMPLETED"
    assert out["results"] == []
    assert out["integrity"]["incomplete_or_failed_run_is_physical_negative_evidence"] is False


def test_failure_report_remains_operational_not_physical_miss():
    out = crossworld_replication.failure_report(
        burst_id="dream-now", reason="Timeout", base_seed=9
    )
    assert out["completed"] is False
    assert out["completion_status"] == "FAILED_OR_INTERRUPTED"
    assert out["errors"][0]["error"] == "Timeout"
    assert "not evidence" in out["interpretation"]


def test_placeholder_overwrites_stale_alias_before_expensive_compute(tmp_path, monkeypatch):
    output = tmp_path / "replication_latest.json"
    current = tmp_path / "latest.json"
    current.write_text(json.dumps({"mode": "cross-world-open-ended-shadow"}))
    monkeypatch.setattr(crossworld_replication, "_CURRENT", current)

    output.write_text(json.dumps({"burst_id": "old-burst", "completed": True}))
    report = crossworld_replication.prime_report(burst_id="new-burst", base_seed=3)
    crossworld_replication.write_report(report, output=output)

    saved = json.loads(output.read_text())
    attached = json.loads(current.read_text())["independent_replication_shadow"]
    assert saved["burst_id"] == "new-burst"
    assert saved["completed"] is False
    assert attached["burst_id"] == "new-burst"
    assert attached["completion_status"] == "NOT_COMPLETED"


def test_no_primary_match_spends_no_replication_compute(monkeypatch):
    monkeypatch.setattr(crossworld_replication, "_read", lambda path, default: {})
    called = {"n": 0}

    def probe(*args, **kwargs):
        called["n"] += 1
        return {"finite": True}

    monkeypatch.setattr(cross_world_emergence, "common_probe", probe)
    out = crossworld_replication.replicate_current_leads(
        base_seed=7, replicates=3, quick=True, burst_id="b"
    )
    assert out["completed"] is True
    assert out["triggered"] is False
    assert out["results"] == []
    assert called["n"] == 0


def test_current_lead_gets_fresh_independent_replication_without_ledger_update(monkeypatch):
    primary = _primary_match()
    g001 = {"patterns": [{"pattern_id": "X-test"}], "recent_episodes": []}

    def read(path, default):
        return primary if path == crossworld_replication._CURRENT else g001

    monkeypatch.setattr(crossworld_replication, "_read", read)
    seeds = []

    def probe(world_id, zero_id, seed, quick):
        seeds.append(seed)
        assert world_id == "o3-vector"
        assert zero_id == "Z-A"
        return {"finite": True, "world_id": world_id, "zero_id": zero_id, "seed": seed}

    monkeypatch.setattr(cross_world_emergence, "common_probe", probe)
    monkeypatch.setattr(
        cross_world_emergence, "detect_common_episodes",
        lambda probe, max_episodes: [{"fingerprint": "fp"}],
    )
    monkeypatch.setattr(
        cross_world_emergence, "compare_g001_patterns",
        lambda episodes, g001_ledger: [{
            "g001_pattern_id": "X-test",
            "matched_world_zero_pairs": ["o3-vector@Z-A"],
            "status": "CROSS_WORLD_ZERO_ALIGNED_LEAD",
            "projection_coverage": 1.0,
            "strict_ZA_alignment": True,
        }],
    )

    out = crossworld_replication.replicate_current_leads(
        base_seed=19, replicates=3, quick=True, burst_id="b"
    )
    assert out["completed"] is True
    assert out["triggered"] is True
    assert len(seeds) == 3
    assert len(set(seeds)) == 3
    row = out["results"][0]
    assert row["repeat_hits"] == 3
    assert row["strict_ZA_repeat_hits"] == 3
    assert row["repeat_hit_rate"] == 1.0
    assert out["integrity"]["updates_cumulative_CWX_ledger"] is False
    assert out["integrity"]["universality_claim"] is False


def test_replication_miss_is_preserved_as_negative_evidence(monkeypatch):
    primary = _primary_match()
    monkeypatch.setattr(
        crossworld_replication,
        "_read",
        lambda path, default: (
            primary if path == crossworld_replication._CURRENT
            else {"patterns": [], "recent_episodes": []}
        ),
    )
    monkeypatch.setattr(
        cross_world_emergence,
        "common_probe",
        lambda world_id, zero_id, seed, quick: {
            "finite": True, "world_id": world_id, "zero_id": zero_id, "seed": seed
        },
    )
    monkeypatch.setattr(
        cross_world_emergence, "detect_common_episodes", lambda probe, max_episodes: []
    )
    monkeypatch.setattr(
        cross_world_emergence, "compare_g001_patterns", lambda episodes, g001_ledger: []
    )

    out = crossworld_replication.replicate_current_leads(
        base_seed=2, replicates=2, quick=True, burst_id="b"
    )
    row = out["results"][0]
    assert row["finite_replicates"] == 2
    assert row["repeat_hits"] == 0
    assert row["repeat_hit_rate"] == 0.0


def test_nonfinite_attempt_is_not_counted_as_physical_miss(monkeypatch):
    primary = _primary_match()
    monkeypatch.setattr(
        crossworld_replication,
        "_read",
        lambda path, default: (
            primary if path == crossworld_replication._CURRENT
            else {"patterns": [], "recent_episodes": []}
        ),
    )
    monkeypatch.setattr(
        cross_world_emergence,
        "common_probe",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("solver failed")),
    )
    out = crossworld_replication.replicate_current_leads(
        base_seed=2, replicates=1, quick=True, burst_id="b"
    )
    attempt = out["results"][0]["attempts"][0]
    assert attempt["finite"] is False
    assert attempt["counts_as_physical_miss"] is False
    assert out["results"][0]["repeat_hit_rate"] is None
