from datetime import datetime, timezone

from ai_lab.dream import adaptive


def _report(with_discovery=True):
    return {
        "counts": {"new_behavior": 1 if with_discovery else 0, "reproduced": 0},
        "headline": {
            "event_id": "evt-x",
            "title": "candidate",
            "plain": "candidate",
            "facts": {
                "family": "white",
                "knobs": {
                    "noise_amplitude": 0.003,
                    "correlation_length": 3.0,
                    "diffusion_ratio": 1.0,
                    "drive_strength": 2.0,
                    "quench_duration": 8.0,
                },
            },
        },
    }


def _hyp(confidence=0.5):
    return {
        "version": 1,
        "hypotheses": [{
            "id": "dimension-specific-emergence",
            "statement": "3D may differ",
            "counter_statement": "3D advantage may disappear",
            "falsification_condition": "paired comparisons",
            "status": "TESTING",
            "support": 0,
            "contradiction": 0,
            "support_cycles": [],
            "confidence": confidence,
        }],
    }


def test_director_keeps_hard_anti_bias_budget_floors():
    d = adaptive.build_research_decision(
        previous_report=_report(), hypotheses=_hyp(0.8), cycle="B", burst_id="dream-test",
        trials_2d=2048, trials_3d=100,
    )
    a = d["next_plan"]["allocation"]
    assert a["unexplored"] >= adaptive.LANE_FLOORS["unexplored"] - 1e-6
    assert a["breaker"] >= adaptive.LANE_FLOORS["breaker"] - 1e-6
    assert a["random"] >= adaptive.LANE_FLOORS["random"] - 1e-6
    assert a["hypothesis"] <= adaptive.HYPOTHESIS_MAX + 1e-6
    assert d["anti_bias"]["2d_failure_never_blocks_native_3d"] is True
    assert len(d["alternative_hypotheses"]) >= 3


def test_stronger_belief_increases_challenge_not_exploitation():
    low = adaptive.build_research_decision(
        previous_report=_report(), hypotheses=_hyp(0.5), cycle="B", burst_id="low", trials_2d=100, trials_3d=10,
    )["next_plan"]["allocation"]
    high = adaptive.build_research_decision(
        previous_report=_report(), hypotheses=_hyp(0.8), cycle="B", burst_id="high", trials_2d=100, trials_3d=10,
    )["next_plan"]["allocation"]
    assert high["breaker"] > low["breaker"]
    assert high["random"] > low["random"]
    assert high["hypothesis"] < low["hypothesis"]


def test_trial_plan_contains_independent_breaker_random_and_unexplored_lanes():
    d = adaptive.build_research_decision(
        previous_report=_report(), hypotheses=_hyp(), cycle="A", burst_id="x", trials_2d=100, trials_3d=10,
    )
    plan = adaptive.make_trial_plan(
        start_index=0, n=100, allocation=d["next_plan"]["allocation"], focus=d["focus"], master_seed=42,
    )
    assert len(plan) == 100
    lanes = {x["lane"] for x in plan}
    assert {"unexplored", "breaker", "random", "hypothesis", "boundary"} <= lanes
    assert len({x["trial_index"] for x in plan}) == 100


def test_native3d_dimension_emergence_is_recorded_without_2d_gate():
    event = adaptive.native3d_events([
        {
            "trial_index": 12,
            "family": "uniform_plus_noise",
            "knobs": {"noise_amplitude": 0.003, "quench_duration": 8.0},
            "seed": 7,
            "reached_level": 2,
            "paired_2d_level": 1,
            "dimension_delta": 1,
            "measured_by": {"defect_count": 2},
            "checksum": "abc",
        }
    ], parent_level=2)[0]
    assert event["source"] == "native-3d-discovery"
    assert event["facts"]["dimension_emergence"] is True
    assert event["facts"]["paired_2d_level"] == 1
    assert "3D" in event["title"]


def test_hypothesis_confidence_is_capped_until_independent_cycles_accumulate(tmp_path, monkeypatch):
    monkeypatch.setattr(adaptive, "_HYPOTHESES", tmp_path / "hyp.json")
    h = _hyp()
    adaptive.update_hypotheses(h, burst_id="b1", native_summary={"dimension_emergence": 4, "paired_compared": 4})
    assert h["hypotheses"][0]["confidence"] <= 0.65
    adaptive.update_hypotheses(h, burst_id="b2", native_summary={"dimension_emergence": 4, "paired_compared": 4})
    assert h["hypotheses"][0]["confidence"] <= 0.85


def test_coverage_aggregates_failures_instead_of_per_trial_files():
    atlas = {"version": 1, "regions": {}, "totals": {"2d": 0, "native_3d": 0}}
    rows = [{
        "family": "white", "status": "2d_screened", "reached_level": 0, "score": 0.1,
        "knobs": {"noise_amplitude": 0.003, "correlation_length": 3.0, "diffusion_ratio": 1.0, "drive_strength": 2.0, "quench_duration": 8.0},
    } for _ in range(50)]
    adaptive.update_coverage(atlas, records=rows, dimension="2d", burst_id="b1")
    assert atlas["totals"]["2d"] == 50
    assert len(atlas["regions"]) == 1
    cell = next(iter(atlas["regions"].values()))
    assert cell["tested"] == 50
    assert cell["interesting"] == 0


def test_cycle_slots_follow_four_jst_research_times():
    # UTC 18:17 == JST 03:17 the next day.
    assert adaptive.cycle_slot(datetime(2026, 8, 7, 18, 17, tzinfo=timezone.utc)) == "A"
    assert adaptive.cycle_slot(datetime(2026, 8, 7, 0, 17, tzinfo=timezone.utc)) == "B"
    assert adaptive.cycle_slot(datetime(2026, 8, 7, 6, 17, tzinfo=timezone.utc)) == "C"
    assert adaptive.cycle_slot(datetime(2026, 8, 7, 12, 17, tzinfo=timezone.utc)) == "D"
