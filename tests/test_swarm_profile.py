from __future__ import annotations

import pytest

from ai_lab.dream.swarm_profile import PROFILES, choose_profile, daily_budget_summary


def test_hourly_and_watchdog_keep_baseline_budget() -> None:
    for schedule in ("17 * * * *", "47 * * * *"):
        profile = choose_profile(event_name="schedule", schedule=schedule)
        assert profile.name == "baseline"
        assert profile.trials == 2048
        assert profile.native3d_trials == 100
        assert profile.open_ended_probes == 24
        assert profile.frontier_experiments == 24


def test_specialist_schedule_rotates_three_independent_questions() -> None:
    assert choose_profile(event_name="schedule", schedule="7 0,12 * * *").name == "novelty"
    assert choose_profile(event_name="schedule", schedule="7 4,16 * * *").name == "native3d"
    assert choose_profile(event_name="schedule", schedule="7 8,20 * * *").name == "mechanism"

    assert PROFILES["novelty"].open_ended_probes > PROFILES["baseline"].open_ended_probes
    assert PROFILES["native3d"].native3d_trials > PROFILES["baseline"].native3d_trials
    assert PROFILES["mechanism"].frontier_experiments > PROFILES["baseline"].frontier_experiments
    assert PROFILES["mechanism"].root_law_trials > PROFILES["baseline"].root_law_trials


def test_manual_dispatch_can_select_a_profile_without_changing_schedule_policy() -> None:
    profile = choose_profile(event_name="workflow_dispatch", manual_profile="native3d")
    assert profile.name == "native3d"
    assert choose_profile(event_name="workflow_dispatch", manual_profile="auto").name == "baseline"
    with pytest.raises(ValueError):
        choose_profile(event_name="workflow_dispatch", manual_profile="target-shape")


def test_profiles_only_allocate_existing_search_knobs() -> None:
    forbidden = (
        "target",
        "morphology",
        "location",
        "event-time",
        "vortex-charge",
        "desired-outcome",
    )
    for profile in PROFILES.values():
        args = " ".join(profile.cli_args()).lower()
        for token in forbidden:
            assert token not in args
        assert "--seed" not in args
        assert "--quick" in args


def test_daily_swarm_adds_six_specialist_runs_and_increases_information_lanes() -> None:
    summary = daily_budget_summary()
    totals = summary["nominal_budget_totals"]

    assert summary["scheduled_research_opportunities_per_day"] == 30
    assert summary["hourly_baseline_runs"] == 24
    assert summary["specialist_runs"] == 6
    assert summary["specialist_runs_by_profile"] == {
        "novelty": 2,
        "native3d": 2,
        "mechanism": 2,
    }

    baseline = PROFILES["baseline"]
    assert totals["trials"] > baseline.trials * 24
    assert totals["native3d_trials"] > baseline.native3d_trials * 24
    assert totals["open_ended_probes"] > baseline.open_ended_probes * 24
    assert totals["unknown_followup_max_patterns"] > baseline.unknown_followup_max_patterns * 24
    assert totals["frontier_experiments"] > baseline.frontier_experiments * 24
    assert totals["root_law_trials"] > baseline.root_law_trials * 24
    assert totals["deep_time_max_leads"] > baseline.deep_time_max_leads * 24

    assert summary["changes_physics"] is False
    assert summary["changes_truth_gates"] is False
    assert summary["seeds_target_outcomes"] is False
