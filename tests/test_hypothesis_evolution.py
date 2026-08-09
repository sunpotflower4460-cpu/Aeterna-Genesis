from ai_lab.dream import adaptive_v7
from ai_lab.dream import evidence_cards
from ai_lab.dream import goal_engine
from ai_lab.dream import hypothesis_evolution
from ai_lab.dream import hypothesis_synthesizer
from ai_lab.dream import portfolio_director


def _legacy():
    return {
        "version": 1,
        "hypotheses": [
            {
                "id": "three-vortex-triangle-fission",
                "statement": "triangle may matter",
                "counter_statement": "triangle may be incidental",
                "falsification_condition": "matched controls show no excess",
                "status": "UNCERTAIN",
                "support": 2,
                "contradiction": 3,
                "confidence": 0.4,
            },
            {
                "id": "triangle-balance-break-fission",
                "statement": "balance break may matter",
                "counter_statement": "balance break may be incidental",
                "falsification_condition": "matched controls show no excess",
                "status": "TESTING",
                "support": 0,
                "contradiction": 0,
                "confidence": 0.5,
            },
        ],
    }


def _focus(pattern="X-test", drive=2.0):
    return {
        "family": "white",
        "knobs": {
            "noise_amplitude": 0.001,
            "correlation_length": 4.0,
            "diffusion_ratio": 1.0,
            "drive_strength": drive,
            "quench_duration": 8.0,
        },
        "source_pattern_id": pattern,
        "source_trial_index": 12,
        "captured_burst": "b0",
        "target_shape_seeded": False,
    }


def _unknown_specific():
    return {
        "version": 1,
        "patterns": {
            "X-test": {
                "pattern_id": "X-test",
                "status": "REPEATED_SPECIFIC_CANDIDATE",
                "exact": {"n": 6, "hit": 5},
                "local": {"n": 6, "hit": 4},
                "contrast": {"n": 6, "hit": 0},
                "search_focus": _focus(),
            }
        },
    }


def test_quarantined_deep_time_evidence_has_zero_weight():
    report = {
        "burst_id": "b1",
        "deep_time_followup": {
            "results": [
                {
                    "lead_id": "deep-x",
                    "prefix_identity_audit": {
                        "scientific_usable": False,
                        "status": "FIELD_RECONSTRUCTION_MISMATCH_QUARANTINED",
                    },
                }
            ]
        },
    }
    cards = evidence_cards.from_deep_time(report, burst_id="b1")
    assert len(cards) == 1
    assert cards[0]["weight"] == 0.0
    assert cards[0]["scientific_usable"] is False


def test_specific_x_pattern_automatically_branches_and_keeps_only_start_side_focus(tmp_path):
    graph_path = tmp_path / "graph.json"
    history_path = tmp_path / "history.json"
    report = {"burst_id": "b1", "deep_time_followup": {"results": []}}
    unknown = _unknown_specific()
    cards = evidence_cards.build_cards(report=report, legacy_hypotheses=_legacy(), unknown_followups=unknown)
    result = hypothesis_evolution.evolve(
        legacy=_legacy(), unknown=unknown, cards=cards, burst_id="b1",
        graph_path=graph_path, history_path=history_path, persist=True,
    )
    nodes = result["graph"]["nodes"]
    assert "xpattern:X-test" in nodes
    assert "xpattern:X-test:condition-specific" in nodes
    child = nodes["xpattern:X-test:condition-specific"]
    assert child["origin"] == "automatic-branch"
    assert child["status"] in {"CONDITIONAL", "TESTING"}
    assert child["search_focus"]["family"] == "white"
    assert child["search_focus"]["target_shape_seeded"] is False
    assert "seed" not in child["search_focus"]
    assert any(e["relation"] == "refines" for e in result["graph"]["edges"])


def test_synthesizer_creates_falsifiable_route_question_and_inherits_start_focus():
    unknown = _unknown_specific()
    graph = hypothesis_evolution.empty_graph()
    hypothesis_evolution.ingest_unknown_patterns(graph, unknown, burst_id="b1")
    proposals = hypothesis_synthesizer.propose_from_unknown(unknown, burst_id="b1", max_proposals=3)
    assert len(proposals) == 1
    p = proposals[0]
    ok, problems = hypothesis_synthesizer.validate_proposal(p)
    assert ok, problems
    assert p["confidence"] == 0.5
    assert p["causal_claim"] is False
    assert p["falsification_condition"]
    assert p["next_test"]
    hypothesis_synthesizer.insert_proposals(graph, proposals, burst_id="b1")
    route = graph["nodes"]["route-question:X-test"]
    assert route["search_focus"]["family"] == "white"
    assert route["search_focus"]["target_shape_seeded"] is False


def test_validator_rejects_threshold_or_target_seeding_shortcuts():
    p = {
        "id": "bad",
        "statement": "change threshold and seed target",
        "counter_statement": "none",
        "falsification_condition": "test",
        "next_test": "seed triangle",
        "confidence": 0.5,
    }
    ok, problems = hypothesis_synthesizer.validate_proposal(p)
    assert ok is False
    assert any("forbidden" in x for x in problems)


def test_portfolio_preserves_global_anti_bias_lanes_and_strong_belief_gets_more_challenge():
    graph = hypothesis_evolution.empty_graph()
    graph["nodes"] = {
        "h-low": {
            "id": "h-low", "status": "TESTING", "confidence": 0.5,
            "goal_relevance": 0.5, "novelty": 0.5, "evidence_ids": [],
            "support_weight": 0.0, "search_focus": _focus("X-low", 1.5),
        },
        "h-high": {
            "id": "h-high", "status": "GROWING", "confidence": 0.8,
            "goal_relevance": 0.5, "novelty": 0.5, "evidence_ids": ["e1", "e2"],
            "support_weight": 2.0, "search_focus": _focus("X-high", 3.0),
        },
    }
    portfolio = portfolio_director.build_portfolio(graph)
    assert portfolio["hypothesis_budget_cap"] <= 0.35
    assert portfolio["runnable_focuses"] == 2
    assert all(x["runnable_focus"] for x in portfolio["active"])
    anti = portfolio["anti_bias"]
    assert anti["minimum_unexplored_fraction"] >= 0.20
    assert anti["minimum_assumption_breaker_fraction"] >= 0.10
    assert anti["minimum_random_fraction"] >= 0.10
    assert portfolio_director.challenge_pressure(graph["nodes"]["h-high"]) > portfolio_director.challenge_pressure(graph["nodes"]["h-low"])

    decision = {
        "next_plan": {
            "allocation": {"unexplored": 0.25, "breaker": 0.15, "random": 0.10, "hypothesis": 0.30, "boundary": 0.20}
        }
    }
    out = portfolio_director.attach_to_decision(decision, portfolio)
    assert out["next_plan"]["allocation"] == decision["next_plan"]["allocation"]
    assert sum(x["effective_lane_share"] for x in out["next_plan"]["hypothesis_portfolio"]) <= 0.300001


def test_weighted_integer_budget_never_loses_trials():
    items = [
        {"hypothesis_id": "a", "w": 0.6},
        {"hypothesis_id": "b", "w": 0.3},
        {"hypothesis_id": "c", "w": 0.1},
    ]
    split = adaptive_v7._weighted_counts(17, items, weight_key="w")
    assert sum(n for _, n in split) == 17
    counts = {item["hypothesis_id"]: n for item, n in split}
    assert counts["a"] > counts["b"] > counts["c"]


def test_route_plan_preserves_exact_global_lane_counts_while_splitting_hypotheses():
    allocation = {"unexplored": 0.25, "boundary": 0.20, "hypothesis": 0.30, "breaker": 0.15, "random": 0.10}
    portfolio = {
        "active": [
            {
                "hypothesis_id": "h1", "hypothesis_budget_share": 0.25, "challenge_pressure": 0.9,
                "search_focus": _focus("X-1", 2.0),
            },
            {
                "hypothesis_id": "h2", "hypothesis_budget_share": 0.10, "challenge_pressure": 0.2,
                "search_focus": _focus("X-2", 4.0),
            },
        ]
    }
    plan = adaptive_v7.build_portfolio_route_plan(
        n=100, allocation=allocation, ordinary_focus=_focus("ordinary"), portfolio=portfolio,
    )
    assert plan["enabled"] is True
    assert sum(x["n"] for x in plan["blocks"]) == 100
    by_lane = {}
    for block in plan["blocks"]:
        by_lane[block["lane"]] = by_lane.get(block["lane"], 0) + block["n"]
    assert by_lane == adaptive_v7._lane_counts(100, allocation)
    exploit = [x for x in plan["blocks"] if x["role"] == "exploit"]
    challenge = [x for x in plan["blocks"] if x["role"] == "challenge"]
    assert len(exploit) == 2
    assert len(challenge) == 2
    assert sum(x["n"] for x in exploit) == 30
    assert sum(x["n"] for x in challenge) == 15
    assert plan["global_lane_counts_changed"] is False
    assert plan["target_outcome_seeded"] is False


def test_route_plan_falls_back_cleanly_without_runnable_focus():
    allocation = {"unexplored": 0.35, "boundary": 0.20, "hypothesis": 0.20, "breaker": 0.15, "random": 0.10}
    plan = adaptive_v7.build_portfolio_route_plan(
        n=37,
        allocation=allocation,
        ordinary_focus=_focus("ordinary"),
        portfolio={"active": [{"hypothesis_id": "h", "hypothesis_budget_share": 0.35, "challenge_pressure": 0.8}]},
    )
    assert plan["enabled"] is False
    assert sum(x["n"] for x in plan["blocks"]) == 37
    assert sum(x["n"] for x in plan["blocks"] if x["lane"] == "hypothesis") == adaptive_v7._lane_counts(37, allocation)["hypothesis"]


def test_goal_engine_never_treats_f7_alone_as_cell_division():
    contract = {
        "mission_id": "test",
        "requirements": [
            {"id": "strict_start_purity", "label": "strict", "required": True},
            {"id": "identity_continuity", "label": "identity", "required": True},
        ],
    }
    report = {"zero_to_fission_path": {"deepest_code": "F7"}}
    result = goal_engine.evaluate(report, contract)
    assert result["goal_reached"] is False
    assert result["required_satisfied"] == 0
    assert result["important_interpretation"]["F7_alone_is_cell_division"] is False

    report["goal_observations"] = {
        "strict_start_purity": {"satisfied": True, "scientific_usable": True},
        "identity_continuity": {"satisfied": True, "scientific_usable": True},
    }
    result2 = goal_engine.evaluate(report, contract)
    assert result2["goal_reached"] is True
