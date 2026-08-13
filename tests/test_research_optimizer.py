from ai_lab.dream import frontier_expander
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


def _law(law_id="RLAW-test", *, active=("relation_self", "relation_trend"),
         new_classes=0, closure=False, history=0.4):
    coeffs = {
        "relation_self": 0.0,
        "relation_composition_2": 0.0,
        "relation_contrast": 0.0,
        "relation_trend": 0.0,
    }
    for name in active:
        coeffs[name] = 1.0
    return {
        "id": law_id,
        "priority": 0.4,
        "coefficients": coeffs,
        "runs": [{"counterfactual_history_dependence": history}],
        "root_integrity": {"runs": [{
            "new_classes_beyond_root_event": new_classes,
            "new_robust_closure_after_root_event": closure,
        }]},
    }


def _root(active=("relation_self", "relation_trend")):
    return {"sizes": [8, 12], "steps": 20, "top_laws": [_law(active=active)]}


def _x_row(status, exact, local, contrast):
    return {
        "status": status,
        "exact": {"hit": exact[0], "n": exact[1]},
        "local": {"hit": local[0], "n": local[1]},
        "contrast": {"hit": contrast[0], "n": contrast[1]},
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
    }


def _ranked(pid="X-specific", score=2.8):
    return {
        "pattern_id": pid,
        "score": score,
        "specificity": 1.0,
        "exact_rate": 0.7,
        "nearby_rate": 0.6,
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
    monkeypatch.setattr(research_optimizer, "rank_x_focuses", lambda limit, history: [_ranked()])
    history = [{"f_source_depth": 4, "x_pattern": "X-old"} for _ in range(6)]
    lanes, _, alloc = research_optimizer._lane_plan(_report(4), _root(), total=24, history=history)
    assert lanes["f"]["cap"] <= 6
    assert alloc["x"] > alloc["f"]
    assert alloc["f"] >= 2
    assert lanes["f"]["new_depth_vs_recent"] is False


def test_new_f6_can_gain_budget_without_monopolizing(monkeypatch):
    monkeypatch.setattr(
        research_optimizer, "rank_x_focuses", lambda limit, history: [_ranked(score=2.0)]
    )
    history = [{"f_source_depth": 4} for _ in range(4)]
    lanes, _, alloc = research_optimizer._lane_plan(_report(6), _root(), total=24, history=history)
    assert lanes["f"]["new_depth_vs_recent"] is True
    assert alloc["f"] > 2
    assert alloc["f"] <= 12
    assert alloc["x"] > 0
    assert alloc["root"] > 0


def test_f_novelty_uses_source_depth_not_weaker_followup_depth():
    # Review regression: an F6 source whose perturbations only reached F4 must not look like a new F6
    # again on the next burst.
    history = [{
        "f_best_depth": 6,          # backward-compatible alias now has source semantics
        "f_source_depth": 6,
        "f_followup_best_depth": 4,
    }]
    lane = research_optimizer._f_lane_score(_report(6), history)
    assert lane["new_depth_vs_recent"] is False
    assert lane["recent_same_depth_count"] == 1


def test_root_score_uses_only_the_law_that_will_be_ablated():
    top = _law(
        "RLAW-top", active=("relation_self",), new_classes=0, closure=False, history=0.0
    )
    lower = _law(
        "RLAW-lower", active=("relation_self",), new_classes=3, closure=True, history=0.8
    )
    root = {"top_laws": [top, lower], "sizes": [8, 12], "steps": 20}
    lane = research_optimizer._root_lane_score(root)
    assert lane["source_law_id"] == "RLAW-top"
    assert "new_distinctions" in lane["unresolved"]
    assert "quotient_closure" in lane["unresolved"]
    assert lane["score"] == 1.35


def test_allocation_caps_match_executable_capacity(monkeypatch):
    ranked = [_ranked(f"X-{i}", 2.0 - i * 0.1) for i in range(3)]
    monkeypatch.setattr(research_optimizer, "rank_x_focuses", lambda limit, history: ranked)
    lanes, _, alloc = research_optimizer._lane_plan(
        _report(4), _root(("relation_self",)), total=24, history=[]
    )
    assert lanes["f"]["cap"] <= 12
    assert lanes["root"]["cap"] == 1
    assert lanes["x"]["cap"] <= 36
    assert all(alloc[name] <= lanes[name]["cap"] for name in alloc)
    assert sum(alloc.values()) == 24


def test_balanced_x_specs_pair_low_high_before_truncation():
    entry = {
        "pattern_id": "X-test",
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
    }
    specs = research_optimizer._balanced_x_specs(entry, burst_id="b1", budget=6)
    assert len(specs) == 6
    assert sum(x["intervened_knob"] is None for x in specs) == 2
    interventions = [x for x in specs if x["intervened_knob"] is not None]
    assert interventions[0]["intervened_knob"] == interventions[1]["intervened_knob"]
    assert [interventions[0]["direction"], interventions[1]["direction"]] == ["low", "high"]
    assert interventions[2]["intervened_knob"] == interventions[3]["intervened_knob"]
    assert [interventions[2]["direction"], interventions[3]["direction"]] == ["low", "high"]
    assert all("target_shape" not in x for x in specs)


def test_install_changes_planning_router_only(monkeypatch):
    old = frontier_expander.run_frontier_expansion
    try:
        research_optimizer.install()
        assert frontier_expander.run_frontier_expansion is research_optimizer.run_optimized_frontier_expansion
    finally:
        monkeypatch.setattr(frontier_expander, "run_frontier_expansion", old)
