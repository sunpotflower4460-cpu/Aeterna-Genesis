from ai_lab.dream import nothing_genesis


def test_strict_nothing_has_no_physical_givens_or_dynamics():
    r = nothing_genesis.strict_nothing_control()
    p = r["physical_layer"]
    assert r["strict_nothing"] is True
    assert p["physical_givens"] == []
    assert p["entities_seeded"] is False
    assert p["state_space_defined"] is False
    assert p["initial_state_defined"] is False
    assert p["relations_defined"] is False
    assert p["transition_rule_defined"] is False
    assert p["time_defined"] is False
    assert p["randomness_defined"] is False
    assert p["probability_measure_defined"] is False
    assert p["possibility_space_defined"] is False
    assert r["result"]["physical_transition_executed"] is False
    assert r["result"]["something_observed"] is False
    assert r["result"]["nothing_to_something_claim"] is False


def test_all_things_possible_zero_is_not_smuggled_into_strict_nothing():
    z = nothing_genesis.possibility_zero_boundary()
    assert z["strict_nothing"] is False
    assert z["instantiated_in_strict_arm"] is False
    assert z["why_not_identical_to_nothing"]


def test_boundary_audit_is_exhaustive_and_never_counts_as_from_nothing():
    names = ("a", "b", "c", "d")
    b = nothing_genesis.audit_first_given_boundary(names)
    assert b["candidate_count"] == 4
    assert b["nonempty_combinations_exhaustively_audited"] == 15
    assert b["expected_nonempty_combinations"] == 15
    assert b["every_nonempty_combination_is_strict_nothing"] is False
    assert b["every_nonempty_combination_counts_as_from_nothing_evidence"] is False
    assert len(b["canonical_enumeration_sha256"]) == 64


def test_full_nothing_report_keeps_r0_downstream_and_no_metaphysical_claim():
    r = nothing_genesis.run_nothing_research(
        burst_id="test-nothing",
        persist=False,
        boundary_names=("distinguishability", "relation", "change"),
    )
    assert r["strict_trial_count"] == 1
    assert r["strict_nothing"]["physical_layer"]["physical_givens"] == []
    assert r["comparison_to_R0"]["R0_is_downstream_of_NØ"] is True
    assert r["comparison_to_R0"]["R0_results_count_as_strict_nothing_results"] is False
    assert r["claim_limits"]["proves_metaphysical_nothing_cannot_create_something"] is False
    assert r["claim_limits"]["proves_metaphysical_nothing_can_create_something"] is False
