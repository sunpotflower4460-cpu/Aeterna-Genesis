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


def test_no_primary_match_spends_no_replication_compute(monkeypatch):
    monkeypatch.setattr(crossworld_replication, "_read", lambda path, default: {})
    called = {"n": 0}

    def probe(*args, **kwargs):
        called["n"] += 1
        return {"finite": True}

    monkeypatch.setattr(cross_world_emergence, "common_probe", probe)
    out = crossworld_replication.replicate_current_leads(base_seed=7, replicates=3, quick=True)
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
    monkeypatch.setattr(cross_world_emergence, "detect_common_episodes", lambda probe, max_episodes: [{"fingerprint": "fp"}])
    monkeypatch.setattr(cross_world_emergence, "compare_g001_patterns", lambda episodes, g001_ledger: [{
        "g001_pattern_id": "X-test",
        "matched_world_zero_pairs": ["o3-vector@Z-A"],
        "status": "CROSS_WORLD_ZERO_ALIGNED_LEAD",
        "projection_coverage": 1.0,
        "strict_ZA_alignment": True,
    }])

    out = crossworld_replication.replicate_current_leads(base_seed=19, replicates=3, quick=True)
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
        crossworld_replication, "_read",
        lambda path, default: primary if path == crossworld_replication._CURRENT else {"patterns": [], "recent_episodes": []},
    )
    monkeypatch.setattr(
        cross_world_emergence, "common_probe",
        lambda world_id, zero_id, seed, quick: {"finite": True, "world_id": world_id, "zero_id": zero_id, "seed": seed},
    )
    monkeypatch.setattr(cross_world_emergence, "detect_common_episodes", lambda probe, max_episodes: [])
    monkeypatch.setattr(cross_world_emergence, "compare_g001_patterns", lambda episodes, g001_ledger: [])

    out = crossworld_replication.replicate_current_leads(base_seed=2, replicates=2, quick=True)
    row = out["results"][0]
    assert row["finite_replicates"] == 2
    assert row["repeat_hits"] == 0
    assert row["repeat_hit_rate"] == 0.0