from ai_lab.dream import pure_genesis, why_gate


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
    assert report["law_trials"] == 4
    assert report["brain_from_zero"]["brain_claim"] is False
    assert report["honesty"]["geometry_seeded"] is False
    assert report["honesty"]["frequency_seeded"] is False
    assert report["honesty"]["vortex_seeded"] is False
    assert report["why_gate"]["physical_givens_beyond_R0"] == []
    for law in report["top_laws"]:
        assert law["why_gate"]["accepted"] is True
        assert law["observations"]["brain_claim"] is False
        assert law["observations"]["physical_frequency_claim"] is False


def test_root_alignment_prefers_observation_first_over_human_reference():
    x = {"origin": "open-ended-x-pattern", "statement": "X-pattern repeats"}
    f = {"origin": "human-reference-hypothesis", "statement": "triangle route"}
    assert why_gate.root_alignment(x)["root_relevance"] > why_gate.root_alignment(f)["root_relevance"]
