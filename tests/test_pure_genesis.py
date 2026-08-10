from ai_lab.dream import adaptive_v8, pure_genesis, root_integrity, why_gate


def test_why_gate_rejects_brain_as_root_given():
    p = pure_genesis.law_proposal({"relation_self": 1.0})
    p["givens"].append({"name": "brain", "kind": "physical"})
    result = why_gate.validate_proposal(p)
    assert not result.accepted
    assert result.target_encoded


def test_root_state_has_no_geometry_and_pair_choice_is_permutation_equivalent():
    _, a, _ = pure_genesis.root_state(8, pair_index=0, event_sign=1, normalization="fro")
    _, b, _ = pure_genesis.root_state(8, pair_index=7, event_sign=1, normalization="fro")
    assert sorted(a.ravel().round(12)) == sorted(b.ravel().round(12))


def test_root_law_uses_only_why_gated_operators():
    proposal = pure_genesis.law_proposal({
        "relation_self": 1.0,
        "relation_composition_2": 1.0,
        "relation_contrast": 0.0,
        "relation_trend": -1.0,
    })
    gate = why_gate.validate_proposal(proposal)
    assert gate.accepted
    assert not proposal["target_encoded"]


def test_root_research_never_claims_brain_geometry_frequency_or_vortex():
    report = pure_genesis.run_root_research(
        burst_id="unit", law_trials=4, sizes=(6,), steps=16, seed=3, persist=False,
    )
    report = root_integrity.audit_report(report, persist=False)
    assert report["law_trials"] == 4
    assert report["brain_from_zero"]["brain_claim"] is False
    assert report["honesty"]["geometry_seeded"] is False
    assert report["honesty"]["frequency_seeded"] is False
    assert report["honesty"]["vortex_seeded"] is False
    assert report["honesty"]["latent_slot_count_is_physical_entity_count"] is False
    assert report["why_gate"]["physical_givens_beyond_R0"] == []
    assert report["root_integrity_audit"]["permutation_quotient_enabled"] is True
    assert report["root_integrity_audit"]["raw_label_graph_closure_accepted_as_emergence"] is False
    for law in report["top_laws"]:
        assert law["why_gate"]["accepted"] is True
        assert law["observations"]["brain_claim"] is False
        assert law["observations"]["physical_frequency_claim"] is False
        assert law["root_integrity"]["raw_slot_closure_used_for_priority"] is False


def test_root_integrity_rejects_global_sign_flip_and_raw_slot_closure_shortcuts():
    proposal = pure_genesis.law_proposal({"relation_self": -1.0})
    proposal["why_gate"] = why_gate.validate_proposal(proposal).as_dict()
    law = pure_genesis.evaluate_law(proposal, sizes=(6,), steps=12, seed=7)
    raw_priority = law["priority"]
    report = {
        "burst_id": "integrity-unit",
        "all_laws": [law],
        "top_laws": [law],
        "observed_not_seeded": ["closure"],
        "honesty": {},
    }
    audited = root_integrity.audit_report(report, persist=False)
    out = audited["top_laws"][0]
    flags = out["root_integrity"]["flags"]
    assert "GLOBAL_SIGN_FLIP_GAUGE_ALIAS" in flags
    assert "RAW_SLOT_GRAPH_CLOSURE_REJECTED" in flags
    assert out["priority"] < raw_priority
    assert "closure" not in audited["observed_not_seeded"]
    assert audited["root_integrity_audit"]["step_recurrence_is_physical_frequency"] is False


def test_root_integrity_distinguishability_is_label_free():
    _, a, _ = pure_genesis.root_state(8, pair_index=0, event_sign=1, normalization="fro")
    perm = [3, 7, 1, 5, 0, 6, 2, 4]
    b = a[perm][:, perm]
    ca = sorted(len(x) for x in root_integrity._profile_classes(a))
    cb = sorted(len(x) for x in root_integrity._profile_classes(b))
    assert ca == cb


def test_root_alignment_prefers_observation_first_over_human_reference():
    x = {"origin": "open-ended-x-pattern", "statement": "X-pattern repeats"}
    f = {"origin": "human-reference-hypothesis", "statement": "triangle route"}
    assert why_gate.root_alignment(x)["root_relevance"] > why_gate.root_alignment(f)["root_relevance"]


def test_production_unspecified_seed_becomes_reproducible_sampling_regulator():
    a = adaptive_v8._root_seed(None, burst_id="dream-test-001")
    b = adaptive_v8._root_seed(None, burst_id="dream-test-001")
    c = adaptive_v8._root_seed(None, burst_id="dream-test-002")
    assert isinstance(a, int)
    assert a == b
    assert a != c
    assert adaptive_v8._root_seed(43, burst_id="ignored") == 43


def test_final_observatory_sync_runs_only_when_enabled(monkeypatch):
    calls = []

    def fake_refresh():
        calls.append("refresh")
        return None

    monkeypatch.setattr(adaptive_v8.v3, "_refresh_observatory", fake_refresh)
    assert adaptive_v8._refresh_final_observatory(False) is None
    assert calls == []
    assert adaptive_v8._refresh_final_observatory(True) is None
    assert calls == ["refresh"]
