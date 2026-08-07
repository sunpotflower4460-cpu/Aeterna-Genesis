import json

import numpy as np

from ai_lab.dream import deep_time_v2
from ai_lab.dream import open_ended
from ai_lab.dream import prefix_audit
from ai_lab.dream import question_critic
from ai_lab.dream import unknown_followups


def _snapshot(t, *, amp=1.0, coh=0.2, ent=0.8, kr=0.1, anis=0.1, grad=0.1, defects=4.0, charge=0.0, high=0.2):
    return {
        "physical_time": float(t),
        "mean_amp": amp,
        "amp_std": 0.1,
        "phase_coherence": coh,
        "spectral_entropy": ent,
        "spectral_k_rms": kr,
        "spectral_anisotropy": anis,
        "gradient_rms": grad,
        "defect_count": defects,
        "net_topological_charge": charge,
        "high_amp_fraction": high,
        "relation_present": False,
        "triangle_present": False,
    }


def test_candidate_sampling_is_not_top_only():
    results = [
        {"score": float(100 - i), "trial_index": i, "family": "white", "knobs": {}, "seed": i}
        for i in range(40)
    ]
    chosen = open_ended.select_diverse_candidates(results, n=8, seed=7)
    scores = [x["score"] for x in chosen]
    assert max(scores) > 90
    assert min(scores) < 70
    assert len({x["trial_index"] for x in chosen}) == 8


def test_change_point_fingerprint_is_found_without_F_path_labels():
    snaps = [_snapshot(i) for i in range(5)]
    snaps += [
        _snapshot(5, coh=0.85, ent=0.25, kr=0.35, grad=0.35, defects=1.0),
        _snapshot(6, coh=0.86, ent=0.24, kr=0.36, grad=0.36, defects=1.0),
        _snapshot(7, coh=0.86, ent=0.24, kr=0.36, grad=0.36, defects=1.0),
    ]
    probe = {
        "snapshots": snaps,
        "analysis_start_time": 2.0,
        "trial_index": 1,
        "family": "white",
        "seed": 10,
        "condition_id": "c1",
        "zero_purity": "Z-A:minimal-white",
        "world_id": "g001-tdgl",
    }
    episodes = open_ended.detect_episodes(probe, max_episodes=3)
    assert episodes
    assert episodes[0]["pattern_id"].startswith("X-")
    assert "phase_coherence" in episodes[0]["fingerprint"]


def test_recurrent_unknown_requires_independent_seeds_and_conditions():
    ledger = {"version": 1, "patterns": [], "transitions": [], "recent_episodes": []}
    base = {
        "pattern_id": "X-test",
        "fingerprint": "spectral_entropy:-L|phase_coherence:+L",
        "change_score": 1.0,
        "physical_time": 5.0,
        "before_state": "a",
        "after_state": "b",
        "known_context": [],
        "unlabeled_transition": True,
        "trial_index": 1,
        "family": "white",
        "zero_purity": "Z-A:minimal-white",
        "world_id": "g001-tdgl",
    }
    episodes = [
        {**base, "seed": 1, "condition_id": "c1"},
        {**base, "seed": 2, "condition_id": "c1"},
        {**base, "seed": 3, "condition_id": "c2"},
    ]
    updated = open_ended._update_ledger(ledger, burst_id="b1", episodes=episodes)["ledger"]
    pattern = updated["patterns"][0]
    assert pattern["status"] == "CROSS_CONDITION_RECURRENT"
    assert len(pattern["seeds"]) == 3
    assert len(pattern["conditions"]) == 2


def test_unknown_followup_variants_only_change_allowed_start_side_knobs():
    source = {
        "family": "white",
        "trial_index": 12,
        "score": 3.0,
        "knobs": {
            "noise_amplitude": 1e-4,
            "correlation_length": 4.0,
            "diffusion_ratio": 0.5,
            "drive_strength": 3.0,
            "quench_duration": 8.0,
        },
    }
    rows = unknown_followups.variants(source, pattern_id="X-test", burst_id="b1")
    assert [x["followup_mode"] for x in rows] == [
        "fresh-seed-exact", "fresh-seed-local", "fresh-seed-contrast"
    ]
    allowed = {
        "noise_amplitude", "correlation_length", "diffusion_ratio", "drive_strength", "quench_duration"
    }
    assert len({x["seed"] for x in rows}) == 3
    for row in rows:
        assert row["family"] == "white"
        assert set(row["knobs"]) == allowed
        assert not ({"triangle", "vortex_charge", "division_site", "division_time"} & set(row))


def test_prefix_digest_tolerates_last_bit_noise_but_not_real_change():
    a = np.array([[1.0 + 2.0j, 3.0 - 1.0j]])
    b = a + (1e-14 + 1e-14j)
    c = a.copy()
    c[0, 0] += 1e-5
    assert prefix_audit.field_digest(a)["value"] == prefix_audit.field_digest(b)["value"]
    assert prefix_audit.field_digest(a)["value"] != prefix_audit.field_digest(c)["value"]


def test_historical_F_depth_never_erases_verified_prefix():
    assert deep_time_v2._historical_F_depth(4, {}) == 4
    assert deep_time_v2._historical_F_depth(4, {"balance_collapse_seen": True}) == 5
    assert deep_time_v2._historical_F_depth(4, {
        "balance_collapse_seen": True,
        "pre_split_instability_candidate": True,
        "network_fission_candidate": True,
    }) == 7


def test_legacy_deep_time_regression_is_quarantined_not_rewritten(tmp_path, monkeypatch):
    ledger = tmp_path / "deep_time.json"
    ledger.write_text(json.dumps({
        "version": 1,
        "leads": [{
            "lead_id": "deep-old",
            "baseline_F_depth": 4,
            "last_rung": 16.0,
            "status": "VERIFYING",
            "history": [{"burst_id": "old", "rung": 16.0, "F_depth": 1, "finite": True}],
        }],
    }))
    monkeypatch.setattr(deep_time_v2.legacy, "_LEDGER", ledger)
    flagged = deep_time_v2._flag_legacy_semantic_regressions()
    saved = json.loads(ledger.read_text())
    lead = saved["leads"][0]
    old = lead["history"][0]
    assert flagged == 1
    assert old["F_depth"] == 1  # provenance stays untouched
    assert old["scientific_usable"] is False
    assert old["legacy_semantics_unverified"] is True
    assert lead["status"] == "PREFIX_REAUDIT_REQUIRED"
    assert lead["last_rung_before_reaudit"] == 16.0
    assert lead["last_rung"] == 0.0


def test_question_critic_challenges_route_and_treats_stability_as_branch(tmp_path, monkeypatch):
    hyp = tmp_path / "hyp.json"
    deep = tmp_path / "deep.json"
    ledger = tmp_path / "critic.json"
    hyp.write_text(json.dumps({"hypotheses": [
        {"id": "three-vortex-triangle-fission", "status": "UNCERTAIN", "confidence": 0.34},
        {"id": "dimension-specific-emergence", "status": "WEAKENED", "confidence": 0.15},
    ]}))
    deep.write_text(json.dumps({"leads": [{"status": "STABLE_THROUGH_64TAU"}]}))
    monkeypatch.setattr(question_critic, "_HYPOTHESES", hyp)
    monkeypatch.setattr(question_critic, "_DEEP", deep)
    monkeypatch.setattr(question_critic, "_LEDGER", ledger)
    out = question_critic.run_question_critic(
        burst_id="b1",
        report={"deep_time_followup": {"results": []}},
        open_summary={"recurrent_unlabeled_patterns": 1},
        director_refreshed=True,
    )
    ids = {q["id"] for q in out["questions"]}
    assert "Q-route-is-not-the-route" in ids
    assert "Q-stability-is-a-branch" in ids
    assert "Q-vocabulary-may-be-missing" in ids
    assert out["posture"]["F_path_role"] == "one-known-reference-route"
