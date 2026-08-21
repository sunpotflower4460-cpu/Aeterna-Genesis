from __future__ import annotations

from ai_lab.dream import x_mechanism_discovery as xmd


def _snap(mean_amp: float, amp_std: float, *, defect_count: float = 0.0) -> dict:
    return {
        "mean_amp": mean_amp,
        "amp_std": amp_std,
        "high_amp_fraction": 0.2,
        "spectral_k_rms": 0.3,
        "spectral_entropy": 0.4,
        "gradient_rms": 0.5,
        "defect_count": defect_count,
    }


def test_scale_normalization_distinguishes_absolute_growth_from_relative_heterogeneity() -> None:
    scale = xmd._classify_event(
        _snap(1.0, 0.2), _snap(2.0, 0.4), event_time=7.0, quench_duration=8.0,
    )
    assert scale["explanation_class"] == "AMPLITUDE_SCALE_TRACKING"
    assert abs(scale["amp_cv_log_gain"]) < 1e-9
    assert scale["quench_phase"] == "DURING_QUENCH"

    hetero = xmd._classify_event(
        _snap(1.0, 0.2), _snap(2.0, 0.8), event_time=10.0, quench_duration=8.0,
    )
    assert hetero["explanation_class"] == "RELATIVE_HETEROGENEITY_GROWTH"
    assert hetero["amp_cv_log_gain"] > 0
    assert hetero["quench_phase"] == "POST_QUENCH"


def test_mature_nonspecific_pattern_is_not_starved_by_smaller_specific_pattern(monkeypatch) -> None:
    unknown = {
        "patterns": {
            "X-big": {
                "status": "REPEATED_NONSPECIFIC",
                "exact": {"n": 10, "hit": 8},
                "local": {"n": 10, "hit": 5},
                "search_focus": {"family": "white", "knobs": {"drive_strength": 1.0}},
            },
            "X-small": {
                "status": "REPEATED_SPECIFIC_CANDIDATE",
                "exact": {"n": 10, "hit": 9},
                "local": {"n": 10, "hit": 7},
                "search_focus": {"family": "white_highk", "knobs": {"drive_strength": 1.0}},
            },
        }
    }
    ledger = {"patterns": {}, "history": []}

    def fake_read(path, default):
        if path == xmd._UNKNOWN:
            return unknown
        if path == xmd._LEDGER:
            return ledger
        return default

    monkeypatch.setattr(xmd, "_read", fake_read)
    monkeypatch.setattr(xmd, "_observation_counts", lambda: {"X-big": 500, "X-small": 40})
    selected = xmd._select_focus()
    assert selected is not None
    assert selected[0] == "X-big"
    assert selected[2] == 500


def test_supported_pattern_returns_for_periodic_holdout(monkeypatch) -> None:
    unknown = {"patterns": {
        "X-supported": {
            "status": "REPEATED_NONSPECIFIC",
            "exact": {"n": 100, "hit": 70},
            "search_focus": {"family": "white", "knobs": {"drive_strength": 1.0}},
        },
        "X-unresolved": {
            "status": "REPEATED_SPECIFIC_CANDIDATE",
            "exact": {"n": 20, "hit": 10},
            "search_focus": {"family": "white", "knobs": {"drive_strength": 1.0}},
        },
    }}
    # Six other mechanism runs have occurred since X-supported was last challenged.
    ledger = {
        "patterns": {
            "X-supported": {"status": "SUPPORTED_SIMULATOR_EXPLANATION"},
            "X-unresolved": {"status": "UNRESOLVED"},
        },
        "history": [
            {"pattern_id": "X-supported"},
            *({"pattern_id": "other"} for _ in range(6)),
        ],
    }

    def fake_read(path, default):
        if path == xmd._UNKNOWN:
            return unknown
        if path == xmd._LEDGER:
            return ledger
        return default

    monkeypatch.setattr(xmd, "_read", fake_read)
    monkeypatch.setattr(xmd, "_observation_counts", lambda: {"X-supported": 1000, "X-unresolved": 50})
    selected = xmd._select_focus()
    assert selected is not None
    assert selected[0] == "X-supported"


def test_specs_use_paired_controls_and_rotate_intervention_tail() -> None:
    focus = {
        "family": "white_highk",
        "knobs": {
            "noise_amplitude": 1e-4,
            "correlation_length": 3.0,
            "diffusion_ratio": 1.0,
            "drive_strength": 2.0,
            "quench_duration": 8.0,
        },
    }
    first = xmd._specs(
        pattern_id="X-test", focus=focus, burst_id="b1", budget=8,
        entry={"intervention_cursor": 0},
    )
    assert len(first) == 8
    baseline_seeds = {row["seed"] for row in first[:2]}
    assert len(baseline_seeds) == 2
    assert all(row["intervened_knob"] is None for row in first[:2])
    assert all(row["seed"] in baseline_seeds for row in first[2:])
    assert [row["intervention"] for row in first[2:]] == [
        "drive-weaker", "drive-stronger", "diffusion-weaker",
        "diffusion-stronger", "quench-faster", "quench-slower",
    ]

    later = xmd._specs(
        pattern_id="X-test", focus=focus, burst_id="b2", budget=8,
        entry={"intervention_cursor": 6},
    )
    labels = [row["intervention"] for row in later[2:]]
    assert "noise-lower" in labels
    assert "noise-higher" in labels
    assert "correlation-shorter" in labels
    assert "correlation-longer" in labels
    for spec in first + later:
        assert spec["target_pattern_seeded"] is False
        assert spec["target_shape_seeded"] is False
        assert "event_time" not in spec
        assert "event_location" not in spec


def test_directional_paired_interventions_are_not_merged_into_one_knob_bucket() -> None:
    entry: dict = {}
    rows = [
        {"seed": 1, "intervention": "baseline-0", "intervened_knob": None, "same_pattern_seen": True, "target_event_metrics": []},
        {"seed": 2, "intervention": "baseline-1", "intervened_knob": None, "same_pattern_seen": True, "target_event_metrics": []},
        {"seed": 1, "intervention": "drive-weaker", "intervened_knob": "drive_strength", "factor": 0.55, "same_pattern_seen": False, "target_event_metrics": []},
        {"seed": 2, "intervention": "drive-stronger", "intervened_knob": "drive_strength", "factor": 1.55, "same_pattern_seen": True, "target_event_metrics": []},
    ]
    xmd._update_entry(entry, pattern_id="X", observations=100, burst_id="b", rows=rows)
    stats = entry["intervention_stats"]
    assert "drive-weaker" in stats
    assert "drive-stronger" in stats
    assert stats["drive-weaker"]["paired_hit_delta_sum"] == -1.0
    assert stats["drive-stronger"]["paired_hit_delta_sum"] == 0.0


def test_supported_explanation_can_be_weakened_by_recent_holdout() -> None:
    entry = {
        "target_events": 30,
        "unique_fresh_seed_groups": 12,
        "event_classes": {
            "AMPLITUDE_SCALE_TRACKING": 24,
            "RELATIVE_HETEROGENEITY_GROWTH": 6,
        },
        "sum_amp_cv_log_gain": 0.1,
        "recent_events": [
            {"explanation_class": "RELATIVE_HETEROGENEITY_GROWTH"}
            for _ in range(8)
        ],
        "intervention_stats": {},
    }
    status, plain, _ = xmd._derive_status(entry, prior_status="SUPPORTED_SIMULATOR_EXPLANATION")
    assert status == "WEAKENED_SIMULATOR_EXPLANATION"
    assert "holdout" in plain


def test_paired_sensitivity_candidate_stays_simulator_level() -> None:
    entry = {
        "target_events": 20,
        "unique_fresh_seed_groups": 10,
        "event_classes": {"AMPLITUDE_SCALE_TRACKING": 18, "MIXED_OR_UNRESOLVED": 2},
        "sum_amp_cv_log_gain": 0.1,
        "recent_events": [{"explanation_class": "AMPLITUDE_SCALE_TRACKING"} for _ in range(12)],
        "intervention_stats": {
            "baseline": {"n": 8, "hit": 8},
            "drive-weaker": {
                "knob": "drive_strength", "factor": 0.55,
                "paired_n": 4, "paired_hit_delta_sum": -3.0,
            },
        },
    }
    status, plain, sensitivity = xmd._derive_status(entry)
    assert status == "SUPPORTED_SIMULATOR_SENSITIVITY_CANDIDATE"
    assert sensitivity is not None
    assert sensitivity["intervention"] == "drive-weaker"
    assert "自然界" in plain
