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
    assert r["result"]["result_is_control_construction_not_independent_measurement"] is True


def test_all_things_possible_zero_is_not_smuggled_into_strict_nothing():
    z = nothing_genesis.possibility_zero_boundary()
    assert z["strict_nothing"] is False
    assert z["instantiated_in_strict_arm"] is False
    assert z["why_not_identical_to_nothing"]


def test_boundary_enumeration_is_exhaustive_but_not_called_physical_audit():
    names = ("a", "b", "c", "d")
    b = nothing_genesis.audit_first_given_boundary(names)
    assert b["candidate_count"] == 4
    assert b["nonempty_combinations_enumerated"] == 15
    assert b["expected_nonempty_combinations"] == 15
    assert b["per_combination_physical_simulation_performed"] is False
    assert b["per_combination_outcome_audit_performed"] is False
    assert b["every_nonempty_combination_is_strict_nothing"] is False
    assert b["every_nonempty_combination_counts_as_from_nothing_evidence"] is False
    assert len(b["canonical_enumeration_sha256"]) == 64


def test_full_nothing_report_keeps_exact_r0_metadata_and_no_metaphysical_claim():
    supplied_r0 = {
        "mode": "pure-genesis-r0-shadow-research",
        "root": {"id": "R0-test"},
        "law_trials": 7,
        "sizes": [6, 8],
        "steps": 20,
        "why_gate": {"accepted": 7},
        "root_integrity_audit": {"permutation_quotient_enabled": True},
        "not_claimed": ["physical_space"],
    }
    r = nothing_genesis.run_nothing_research(
        burst_id="test-nothing",
        persist=False,
        boundary_names=("distinguishability", "relation", "change"),
        r0_metadata=supplied_r0,
    )
    assert r["strict_trial_count"] == 1
    assert r["strict_nothing"]["physical_layer"]["physical_givens"] == []
    assert r["comparison_to_R0"]["R0_is_downstream_of_NØ"] is True
    assert r["comparison_to_R0"]["R0_results_count_as_strict_nothing_results"] is False
    meta = r["comparison_to_R0"]["triggering_R0_metadata"]
    assert meta["supplied_by_triggering_run"] is True
    assert meta["law_trials"] == 7
    assert meta["root"]["id"] == "R0-test"
    assert r["claim_limits"]["proves_metaphysical_nothing_cannot_create_something"] is False
    assert r["claim_limits"]["proves_metaphysical_nothing_can_create_something"] is False


def test_eighth_audit_is_not_falsely_marked_passed():
    r = nothing_genesis.run_nothing_research(
        burst_id="audit-nothing", persist=False, boundary_names=("a", "b", "c")
    )
    audit = r["technical_audit"]
    assert audit["role"]["primary"] != "E"
    assert "frontier" in audit["claim_tier"]
    assert audit["no_touch"]["physics_dynamics_invoked"] is False
    eighth = audit["eighth_audit"]
    assert eighth["independent_physical_outcome_detector_exists"] is False
    assert eighth["constructor_sets_null_result"] is True
    assert eighth["verdict"] == "DECLARATIVE_NULL_CONTROL_NOT_A_PASSED_EIGHTH_AUDIT"
    assert eighth["invariant_checks"]["physical_givens_are_empty"] is True
    assert audit["determinism"]["passed"] is True
    assert audit["reproduction"]["standalone_command"]


def test_boundary_enumeration_digest_is_deterministic():
    names = ("a", "b", "c", "d", "e")
    a = nothing_genesis.enumerate_first_given_boundary(names)
    b = nothing_genesis.enumerate_first_given_boundary(names)
    assert a["canonical_enumeration_sha256"] == b["canonical_enumeration_sha256"]
    assert a["nonempty_combinations_enumerated"] == 31


def test_recording_writes_latest_and_immutable_human_screenshot_package(tmp_path, monkeypatch):
    easy = tmp_path / "easy"
    monkeypatch.setattr(nothing_genesis, "_REPO", tmp_path)
    monkeypatch.setattr(nothing_genesis, "_REPORT", easy / "nothing_latest.json")
    monkeypatch.setattr(nothing_genesis, "_HUMAN", easy / "nothing_latest.md")
    monkeypatch.setattr(nothing_genesis, "_SCREENSHOT", easy / "nothing_latest.png")
    monkeypatch.setattr(nothing_genesis, "_ARCHIVE", easy / "nothing")

    r = nothing_genesis.run_nothing_research(
        burst_id="dream-test-0001", persist=True, boundary_names=("a", "b", "c", "d")
    )
    archive = easy / "nothing" / "dream-test-0001"
    assert (easy / "nothing_latest.json").exists()
    assert (easy / "nothing_latest.md").exists()
    assert (easy / "nothing_latest.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (archive / "report.json").exists()
    assert (archive / "human.md").exists()
    assert (archive / "boundary.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert r["visualization"]["separated_from_physics_data"] is True
    assert r["visualization"]["physical_data_visualized"] is False
    human = (archive / "human.md").read_text()
    assert "次にできること" in human
    assert "推奨" in human
    assert "物理実験ではなく" in human