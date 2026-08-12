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


def _report(depth=4):
    return {
        "zero_to_fission_path": {
            "deepest_contiguous_stage": depth,
            "best_frontier_candidate": {
                "trial_index": 11,
                "family": "white",
                "depth": depth,
                "knobs": dict(KNOBS),
            },
        },
        "geometry_summary": {
            "persistent_pair_seen": 2,
            "triad_local_energy_measured": 1,
            "balance_collapse_seen": 0,
            "pre_split_instability_candidate": 0,
            "network_fission_candidate": 0,
        },
        "open_ended_emergence": {"recurrent_unlabeled_patterns": 10},
    }


def _root(active=("relation_self", "relation_trend")):
    coeffs = {
        "relation_self": 0.0,
        "relation_composition_2": 0.0,
        "relation_contrast": 0.0,
        "relation_trend": 0.0,
    }
    for name in active:
        coeffs[name] = 1.0
    return {
        "sizes": [8, 12],
        "steps": 20,
        "top_laws": [{
            "id": "RLAW-test",
            "priority": 0.4,
            "coefficients": coeffs,
            "runs": [{"counterfactual_history_dependence": 0.4}],
            "root_integrity": {"runs": [{
                "new_classes_beyond_root_event": 0,
                "new_robust_closure_after_root_event": False,
            }]},
        }],
    }


def _x_row(status, exact, local, contrast):
    return {
        "status": status,
        "exact": {"hit": exact[0], "n": exact[1]},
        "local": {"hit": local[0], "n": local[1]},
        "contrast": {"hit": contrast[0], "n": contrast[1]},
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
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


def test_specific_x_outranks_huge_nonspecific_recurrence(monkeypatch):
    doc = {"patterns": {
        "X-huge": _x_row("REPEATED_NONSPECIFIC", (27, 35), (21, 35), (1, 35)),
        "X-specific": _x_row("REPEATED_SPECIFIC_CANDIDATE", (9, 13), (8, 13), (0, 13)),
    }}
    monkeypatch.setattr(frontier_expander, "_read", lambda path, default: doc)
    ranked = research_optimizer.rank_x_focuses(limit=2, history=[])
    assert [x["pattern_id"] for x in ranked] == ["X-specific", "X-huge"]
    assert ranked[0]["specificity"] > 0


def test_recently_studied_x_is_discounted_so_other_specific_leads_rotate(monkeypatch):
    doc = {"patterns": {
        "X-a": _x_row("REPEATED_SPECIFIC_CANDIDATE", (7, 10), (5, 10), (0, 10)),
        "X-b": _x_row("REPEATED_SPECIFIC_CANDIDATE", (6, 10), (5, 10), (0, 10)),
    }}
    monkeypatch.setattr(frontier_expander, "_read", lambda path, default: doc)
    history = [{"x_patterns": ["X-a"]} for _ in range(5)]
    ranked = research_optimizer.rank_x_focuses(limit=2, history=history)
    assert ranked[0]["pattern_id"] == "X-b"
    assert ranked[1]["recent_studies"] == 5


def test_repeated_f4_does_not_receive_first_refusal(monkeypatch):
    ranked = [{
        "pattern_id": "X-specific", "score": 2.8, "specificity": 1.0,
        "exact_rate": 0.7, "nearby_rate": 0.6, "contrast_rate": 0.0,
        "recent_studies": 0, "status": "REPEATED_SPECIFIC_CANDIDATE",
        "search_focus": {"family": "white", "knobs": dict(KNOBS)}, "row": {},
    }]
    monkeypatch.setattr(research_optimizer, "rank_x_focuses", lambda limit, history: ranked)
    history = [{"f_best_depth": 4, "x_pattern": "X-old"} for _ in range(6)]
    lanes, _, alloc = research_optimizer._lane_plan(_report(4), _root(), total=24, history=history)
    assert lanes["f"]["cap"] <= 6
    assert alloc["x"] > alloc["f"]
    assert alloc["f"] >= 2
    assert lanes["f"]["new_depth_vs_recent"] is False


def test_new_f6_can_gain_budget_without_monopolizing(monkeypatch):
    ranked = [{
        "pattern_id": "X-specific", "score": 2.0, "specificity": 0.8,
        "exact_rate": 0.6, "nearby_rate": 0.5, "contrast_rate": 0.0,
        "recent_studies": 0, "status": "REPEATED_SPECIFIC_CANDIDATE",
        "search_focus": {"family": "white", "knobs": dict(KNOBS)}, "row": {},
    }]
    monkeypatch.setattr(research_optimizer, "rank_x_focuses", lambda limit, history: ranked)
    history = [{"f_best_depth": 4} for _ in range(4)]
    lanes, _, alloc = research_optimizer._lane_plan(_report(6), _root(), total=24, history=history)
    assert lanes["f"]["new_depth_vs_recent"] is True
    assert alloc["f"] > 2
    assert alloc["f"] <= 12
    assert alloc["x"] > 0
    assert alloc["root"] > 0
    assert sum(alloc.values()) <= 24


def test_allocation_caps_match_executable_capacity(monkeypatch):
    ranked = [
        {
            "pattern_id": f"X-{i}", "score": 2.0 - i * 0.1, "specificity": 0.8,
            "exact_rate": 0.6, "nearby_rate": 0.5, "contrast_rate": 0.0,
            "recent_studies": 0, "status": "REPEATED_SPECIFIC_CANDIDATE",
            "search_focus": {"family": "white", "knobs": dict(KNOBS)}, "row": {},
        }
        for i in range(3)
    ]
    monkeypatch.setattr(research_optimizer, "rank_x_focuses", lambda limit, history: ranked)
    lanes, _, alloc = research_optimizer._lane_plan(_report(4), _root(("relation_self",)), total=24, history=[])
    assert lanes["f"]["cap"] <= 12
    assert lanes["root"]["cap"] == 1
    assert lanes["x"]["cap"] <= 36
    assert all(alloc[name] <= lanes[name]["cap"] for name in alloc)
    assert sum(alloc.values()) == 24


def test_balanced_x_specs_cover_multiple_knobs_with_small_budget():
    entry = {
        "pattern_id": "X-test",
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
    }
    specs = research_optimizer._balanced_x_specs(entry, burst_id="b1", budget=8)
    assert len(specs) == 8
    assert sum(x["intervened_knob"] is None for x in specs) == 2
    touched = {x["intervened_knob"] for x in specs if x["intervened_knob"] is not None}
    assert len(touched) >= 3
    assert all("target_shape" not in x for x in specs)


def test_install_changes_planning_router_only(monkeypatch):
    old = frontier_expander.run_frontier_expansion
    try:
        research_optimizer.install()
        assert frontier_expander.run_frontier_expansion is research_optimizer.run_optimized_frontier_expansion
    finally:
        monkeypatch.setattr(frontier_expander, "run_frontier_expansion", old)


def test_progress_ratchet_saturated_x_rotates_behind_uncovered_candidate(monkeypatch):
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


def test_progress_ratchet_uses_unseen_cells_before_routine_repeat():
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


def test_progress_ratchet_two_zero_gain_bursts_remove_lane_floor(monkeypatch):
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
    lanes, _, _ = progress_ratchet._lane_plan(_report(4), {"top_laws": []}, total=6, history=history)
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


def test_progress_audit_replication_only_requires_next_route_escape():
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


def test_progress_ratchet_install_stays_in_planning_layer(monkeypatch):
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
