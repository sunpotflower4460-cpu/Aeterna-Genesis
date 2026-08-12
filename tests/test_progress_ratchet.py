from ai_lab.dream import frontier_expander
from ai_lab.dream import progress_ratchet
from ai_lab.dream import research_optimizer


KNOBS = {
    "noise_amplitude": 4e-5,
    "correlation_length": 3.0,
    "diffusion_ratio": 0.4,
    "drive_strength": 2.0,
    "quench_duration": 8.0,
}


def _ranked(pid, score=2.0):
    return {
        "pattern_id": pid,
        "score": score,
        "specificity": 0.8,
        "exact_rate": 0.7,
        "nearby_rate": 0.5,
        "contrast_rate": 0.0,
        "recent_studies": 0,
        "status": "REPEATED_SPECIFIC_CANDIDATE",
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
        "row": {},
    }


def test_saturated_x_rotates_behind_equally_specific_uncovered_candidate(monkeypatch):
    monkeypatch.setattr(
        progress_ratchet,
        "_V9_RANK_X",
        lambda limit, history: [_ranked("X-a", 2.1), _ranked("X-b", 2.0)],
    )
    covered = progress_ratchet._candidate_question_keys("x", "X-a")
    history = [{"progress": {"question_keys": covered}}]
    ranked = progress_ratchet.rank_x_focuses(limit=2, history=history)
    assert ranked[0]["pattern_id"] == "X-b"
    assert ranked[0]["intervention_coverage"]["unseen"] > 0
    assert ranked[1]["intervention_coverage"]["unseen"] == 0


def test_intervention_scheduler_uses_unseen_cells_before_routine_repeat():
    seen_key = progress_ratchet._question_key("x", "X-test", "noise_amplitude", 0.60)
    history = [{"progress": {"question_keys": [seen_key]}}]
    specs = progress_ratchet._ordered_intervention_specs(
        lane="x",
        target="X-test",
        family="white",
        knobs=dict(KNOBS),
        burst_id="b-progress",
        budget=8,
        history=history,
    )
    assert len(specs) == 8
    assert sum(s["intervened_knob"] is None for s in specs) == 2
    intervention_keys = [s["progress_question_key"] for s in specs if s["progress_question_key"]]
    assert seen_key not in intervention_keys
    assert len(set(intervention_keys)) == len(intervention_keys)


def test_two_zero_gain_bursts_remove_lane_floor_and_trigger_cooldown(monkeypatch):
    base_lanes = {
        "f": {"eligible": True, "score": 1.0, "floor": 2, "cap": 6, "reason": "f"},
        "x": {"eligible": False, "score": 0.0, "floor": 0, "cap": 0, "reason": "x"},
        "root": {"eligible": False, "score": 0.0, "floor": 0, "cap": 0, "reason": "root"},
    }
    monkeypatch.setattr(
        progress_ratchet,
        "_V9_LANE_PLAN",
        lambda report, root_report, total, history: (base_lanes, [], {"f": 6, "x": 0, "root": 0}),
    )
    history = [
        {"progress": {"lane_knowledge_units": {"f": 0.0}}},
        {"progress": {"lane_knowledge_units": {"f": 0.0}}},
    ]
    report = {
        "zero_to_fission_path": {
            "best_frontier_candidate": {
                "family": "white",
                "trial_index": 1,
                "depth": 4,
                "knobs": dict(KNOBS),
            }
        }
    }
    lanes, _, _ = progress_ratchet._lane_plan(report, {"top_laws": []}, total=6, history=history)
    assert lanes["f"]["progress_cooldown"] is True
    assert lanes["f"]["floor"] == 0
    assert lanes["f"]["score"] < 1.0


def test_progress_audit_distinguishes_new_question_from_replication():
    old = progress_ratchet._question_key("x", "X-a", "drive_strength", 0.75)
    new = progress_ratchet._question_key("x", "X-a", "drive_strength", 1.30)
    history = [{"progress": {"question_keys": [old]}, "f_best_depth": 4}]
    expansion = {
        "budget": {"executed": 4},
        "f_frontier_mechanism": {"best_depth_seen": 4, "results": []},
        "x_pattern_mechanism": {
            "patterns": [{
                "pattern_id": "X-a",
                "sensitivity": [],
                "results": [
                    {"intervened_knob": "drive_strength", "factor": 0.75},
                    {"intervened_knob": "drive_strength", "factor": 1.30},
                ],
            }]
        },
        "root_operator_ablation": {"ablations": []},
    }
    audit = progress_ratchet._progress_audit(expansion, history)
    assert old in audit["replicated_question_keys"]
    assert new in audit["new_question_keys"]
    assert audit["status"] == "ADVANCED"
    assert audit["raw_recurrence_alone_counts_as_progress"] is False
    assert audit["changes_scientific_truth_gate"] is False


def test_replication_only_is_recorded_but_requests_escape_when_novelty_is_exhausted():
    key = progress_ratchet._question_key("x", "X-a", "drive_strength", 0.75)
    history = [{"progress": {"question_keys": [key]}}]
    expansion = {
        "budget": {"executed": 2},
        "f_frontier_mechanism": {"best_depth_seen": -1, "results": []},
        "x_pattern_mechanism": {
            "patterns": [{
                "pattern_id": "X-a",
                "sensitivity": [],
                "results": [{"intervened_knob": "drive_strength", "factor": 0.75}],
            }]
        },
        "root_operator_ablation": {"ablations": []},
    }
    audit = progress_ratchet._progress_audit(expansion, history)
    assert audit["status"] == "ADVANCED_BY_REPLICATION_ONLY"
    assert audit["next_burst_escape_required"] is True
    assert "NEXT_BURST_ROUTE_ROTATION_REQUIRED" in audit["advance_events"]


def test_install_keeps_changes_in_planning_layer(monkeypatch):
    old_router = frontier_expander.run_frontier_expansion
    old_rank = research_optimizer.rank_x_focuses
    old_plan = research_optimizer._lane_plan
    old_specs = research_optimizer._balanced_x_specs
    old_f = frontier_expander._f_frontier_study
    old_root = frontier_expander._root_ablation_study
    try:
        progress_ratchet.install()
        assert frontier_expander.run_frontier_expansion is progress_ratchet.run_progressive_frontier_expansion
        assert research_optimizer.rank_x_focuses is progress_ratchet.rank_x_focuses
        assert research_optimizer._lane_plan is progress_ratchet._lane_plan
        assert research_optimizer._balanced_x_specs is progress_ratchet._balanced_x_specs
        assert frontier_expander._f_frontier_study is progress_ratchet._f_frontier_study
        assert frontier_expander._root_ablation_study is progress_ratchet._root_ablation_study
    finally:
        monkeypatch.setattr(frontier_expander, "run_frontier_expansion", old_router)
        monkeypatch.setattr(research_optimizer, "rank_x_focuses", old_rank)
        monkeypatch.setattr(research_optimizer, "_lane_plan", old_plan)
        monkeypatch.setattr(research_optimizer, "_balanced_x_specs", old_specs)
        monkeypatch.setattr(frontier_expander, "_f_frontier_study", old_f)
        monkeypatch.setattr(frontier_expander, "_root_ablation_study", old_root)
