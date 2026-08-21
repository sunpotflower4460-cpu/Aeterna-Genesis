from __future__ import annotations

from ai_lab.dream import frontier_expander
from ai_lab.dream import pure_genesis
from ai_lab.dream import relation_frontier_adapter
from ai_lab.dream import relation_instrument_adapter as ria


def test_instrumented_run_preserves_original_root_observables_and_score() -> None:
    kwargs = dict(
        n=8,
        steps=16,
        pair_index=2,
        event_sign=1,
        event_fraction=0.05,
        normalization="fro",
    )
    coeffs = {
        "relation_self": 1.0,
        "relation_composition_2": 0.0,
        "relation_contrast": 1.0,
        "relation_trend": 0.0,
    }
    original = ria._ORIGINAL_RUN_ONE(coeffs, **kwargs)
    measured = ria._instrumented_run_one(coeffs, **kwargs)
    for key in (
        "finite", "n", "steps", "normalization", "root_event_pair", "root_event_sign",
        "initial_differentiation", "final_differentiation", "differentiation_gain", "late_activity",
        "relation_pattern_persistence", "effective_relation_rank", "counterfactual_history_dependence",
    ):
        assert measured[key] == original[key]
    assert pure_genesis._run_score(measured) == pure_genesis._run_score(original)
    instruments = measured["relation_structure_instruments"]
    assert instruments["integrity"]["coordinate_input_used"] is False
    assert instruments["integrity"]["changes_dynamics"] is False


def test_root_report_gets_bounded_relation_instrument_summary_without_truth_upgrade() -> None:
    ria.install()
    try:
        report = pure_genesis.run_root_research(
            burst_id="relation-instrument-test",
            law_trials=2,
            sizes=(6, 8),
            steps=12,
            seed=13,
            persist=False,
        )
    finally:
        ria.uninstall_for_tests()
    summary = report["relation_instrument_summary"]
    assert summary["mode"] == "pure-genesis-relation-instrument-summary"
    assert summary["integrity"]["coordinate_input_used"] is False
    assert summary["integrity"]["changes_root_dynamics"] is False
    assert summary["integrity"]["changes_law_score_or_ranking"] is False
    assert summary["integrity"]["planner_lead_is_physical_truth"] is False
    assert "relation_metric_candidate" in report["observed_not_seeded"]
    assert report["honesty"]["lineage_detector_seeds_division"] is False


def test_frontier_marks_active_instrument_measured_without_requesting_it_again() -> None:
    root_report = {
        "top_laws": [],
        "relation_instrument_summary": {
            "capabilities": {
                "emergent_metric_geometry": {"instrument_status": "MEASURED"},
                "persistent_individual_identity": {"instrument_status": "MEASURED"},
                "division_with_inheritance": {"instrument_status": "MEASURED"},
            }
        },
    }
    relation_frontier_adapter.install()
    try:
        capabilities = frontier_expander._capability_map({}, root_report)
        status = {row["id"]: row["status"] for row in capabilities}
        assert status["emergent_metric_geometry"] == "MEASURED"
        assert status["persistent_individual_identity"] == "MEASURED"
        assert status["division_with_inheritance"] == "MEASURED"
        requests = frontier_expander._instrument_requests(capabilities)
        ids = {row["id"] for row in requests}
        assert "metric-from-relations" not in ids
        assert "identity-continuity" not in ids
        assert "lineage-accounting" not in ids
        # Unimplemented instruments remain requested.
        assert "damage-recovery" in ids
        assert "growth-accounting" in ids
        assert "predictive-holdout" in ids
    finally:
        relation_frontier_adapter.uninstall_for_tests()


def test_planner_lead_requires_repeated_multi_size_candidates() -> None:
    fake_runs = []
    for size in (8, 12):
        for _ in range(2):
            fake_runs.append({
                "n": size,
                "relation_structure_instruments": {
                    "metric": {"measured_frames": 6, "status": "RELATIONAL_METRIC_SERIES_CANDIDATE"},
                    "identity": {"status": "MEASURED_NO_IDENTITY_LEAD"},
                    "lineage": {"status": "MEASURED_NO_LINEAGE_LEAD"},
                },
            })
    report = {"top_laws": [{"id": "law", "runs": fake_runs, "observations": {}}]}
    summary = ria._aggregate(report)
    metric = summary["capabilities"]["emergent_metric_geometry"]
    assert metric["instrument_status"] == "LEAD"
    assert metric["candidate_sizes"] == [8, 12]
    assert summary["integrity"]["physical_space_claim"] is False
    assert summary["integrity"]["fundamental_dimension_claim"] is False
