from ai_lab.dream import frontier_expander
from ai_lab.dream import human_report


def _f6_report():
    return {
        "zero_to_fission_path": {
            "deepest_contiguous_stage": 6,
            "best_frontier_candidate": {
                "trial_index": 7,
                "family": "white_highk",
                "depth": 6,
                "knobs": {
                    "noise_amplitude": 4e-5,
                    "correlation_length": 2.0,
                    "diffusion_ratio": 0.3,
                    "drive_strength": 2.0,
                    "quench_duration": 8.0,
                },
            },
        },
        "geometry_summary": {"persistent_pair_seen": 2, "triad_local_energy_measured": 1},
        "open_ended_emergence": {"recurrent_unlabeled_patterns": 1},
        "counts": {"reproduced": 1},
    }


def _root_report():
    return {
        "sizes": [8, 12],
        "steps": 16,
        "top_laws": [
            {
                "id": "RLAW-test",
                "priority": 0.4,
                "coefficients": {
                    "relation_self": 1.0,
                    "relation_composition_2": 1.0,
                    "relation_contrast": 0.0,
                    "relation_trend": 1.0,
                },
                "runs": [{"counterfactual_history_dependence": 0.25}],
                "root_integrity": {
                    "runs": [
                        {
                            "new_classes_beyond_root_event": 2,
                            "new_robust_closure_after_root_event": True,
                        }
                    ]
                },
            }
        ],
    }


def test_one_factor_specs_only_change_start_side_regulators_and_never_encode_target():
    specs = frontier_expander._one_factor_specs(
        family="white_highk",
        knobs=_f6_report()["zero_to_fission_path"]["best_frontier_candidate"]["knobs"],
        burst_id="b1",
        source_id="frontier",
        limit=12,
    )
    assert len(specs) == 12
    assert len({x["seed"] for x in specs}) == len(specs)
    for spec in specs:
        assert "target_shape" not in spec
        assert "triangle" not in spec
        assert "division_location" not in spec
        assert "division_time" not in spec
        assert set(spec["knobs"]) == set(frontier_expander._KNOB_RANGES)


def test_capability_map_keeps_big_destination_gaps_open_even_with_f6_and_root_leads():
    rows = frontier_expander._capability_map(_f6_report(), _root_report())
    by_id = {x["id"]: x for x in rows}
    assert by_id["endogenous_distinction"]["status"] == "LEAD"
    assert by_id["relational_closure"]["status"] == "LEAD"
    assert by_id["history_dependence"]["status"] == "LEAD"
    assert by_id["connected_instability"]["status"] == "LEAD"
    assert by_id["persistent_individual_identity"]["status"] == "UNMEASURED"
    assert by_id["self_repair"]["status"] == "UNMEASURED"
    assert by_id["adaptive_prediction"]["status"] == "UNMEASURED"
    assert by_id["division_with_inheritance"]["status"] == "UNMEASURED"


def test_missing_capabilities_create_new_instrument_requests_without_new_physical_axioms():
    rows = frontier_expander._capability_map(_f6_report(), _root_report())
    requests = frontier_expander._instrument_requests(rows)
    ids = {x["id"] for x in requests}
    assert "metric-from-relations" in ids
    assert "identity-continuity" in ids
    assert "damage-recovery" in ids
    assert "growth-accounting" in ids
    assert "predictive-holdout" in ids
    assert "lineage-accounting" in ids
    assert all(x["new_physical_axiom"] is False for x in requests)
    assert all(x["target_morphology_seeded"] is False for x in requests)
    scaffolded = [x for x in requests if x["may_use_scaffolded_analogy_lane"]]
    assert scaffolded
    assert all(x["scaffolded_lane_cannot_count_as_pure_genesis_proof"] for x in scaffolded)


def test_dynamic_frontier_expansion_donates_budget_to_current_evidence(monkeypatch):
    monkeypatch.setattr(frontier_expander, "_best_x_focus", lambda: (
        "X-test",
        {"search_focus": {"family": "white", "knobs": _f6_report()["zero_to_fission_path"]["best_frontier_candidate"]["knobs"]}},
    ))
    monkeypatch.setattr(frontier_expander, "_f_frontier_study", lambda report, burst_id, budget: {
        "ran": True, "experiments": budget, "best_depth_seen": 6,
        "relation_network_fission_candidates": 0, "sensitivity": [{"knob": "drive_strength", "delta_from_fresh_baseline": -1.0}],
    })
    monkeypatch.setattr(frontier_expander, "_x_mechanism_study", lambda burst_id, budget: {
        "ran": True, "experiments": budget, "pattern_id": "X-test",
        "sensitivity": [{"knob": "diffusion_ratio", "delta_from_fresh_baseline": -0.5}],
    })
    monkeypatch.setattr(frontier_expander, "_root_ablation_study", lambda root_report, burst_id, budget: {
        "ran": True, "experiments": budget, "ablations": [{"operator_removed": "relation_trend"}],
        "most_needed_operator_candidate": "relation_trend",
    })
    out = frontier_expander.run_frontier_expansion(
        report=_f6_report(), root_report=_root_report(), burst_id="b1",
        max_experiments=24, persist=False,
    )
    assert out["budget"]["executed"] <= 24
    assert out["budget"]["allocated"]["f"] > 0
    assert out["budget"]["allocated"]["x"] > 0
    assert out["budget"]["allocated"]["root"] > 0
    assert out["policy"]["destination_fixed_methods_adaptive"] is True
    assert out["policy"]["scaffolded_results_count_as_pure_genesis_proof"] is False
    assert out["integrity"]["new_unexplained_physical_axiom_added"] is False
    assert out["integrity"]["target_morphology_seeded"] is False
    assert out["integrity"]["F_path_is_assumed_natural_route"] is False


def test_frontier_mechanism_nodes_are_planning_only_and_do_not_seed_outcomes():
    expansion = {
        "source_path_candidate": {
            "family": "white_highk",
            "knobs": _f6_report()["zero_to_fission_path"]["best_frontier_candidate"]["knobs"],
        },
        "source_x_focus": {
            "family": "white",
            "knobs": _f6_report()["zero_to_fission_path"]["best_frontier_candidate"]["knobs"],
        },
        "f_frontier_mechanism": {
            "ran": True,
            "sensitivity": [{"knob": "drive_strength", "delta_from_fresh_baseline": -1.0}],
        },
        "x_pattern_mechanism": {
            "ran": True,
            "pattern_id": "X-test",
            "sensitivity": [{"knob": "diffusion_ratio", "delta_from_fresh_baseline": -0.5}],
        },
        "root_operator_ablation": {
            "ran": True,
            "most_needed_operator_candidate": "relation_trend",
        },
    }
    graph = {"version": 1, "nodes": {}, "edges": []}
    frontier_expander.inject_planning_hypotheses(graph, expansion, burst_id="b1")
    assert len(graph["nodes"]) == 3
    for node in graph["nodes"].values():
        assert node["causal_claim"] is False
        focus = node.get("search_focus")
        if focus:
            assert focus["target_shape_seeded"] is False
            assert "seed" not in focus


def test_human_report_leads_with_destination_progress_not_internal_ids():
    report = _f6_report()
    report["pure_genesis_r0"] = _root_report()
    report["autonomous_frontier_expansion"] = {
        "human": {
            "destination": "形を先に与えず、最小の出発点から宇宙・脳・種の成長に必要な働きが生まれるところまで進みます。",
            "current_position": "いまは違い・関係・履歴の候補があり、個体性や自己修復はまだ先です。",
            "advances": ["繰り返す変化について、何を変えると消えるかを調べ始めました。"],
            "largest_gaps": ["まとまりが個体として自分を保つ"],
        },
        "instrument_requests": [
            {"purpose": "自己維持を介入で確かめる"}
        ],
    }
    summary = human_report.build_summary(report)
    text = human_report.render_markdown(summary)
    assert "目的地" in text
    assert "現在地" in text
    assert human_report.first_read_violations(text) == []
