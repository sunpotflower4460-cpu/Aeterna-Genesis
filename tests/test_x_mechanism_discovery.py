from ai_lab.dream import x_mechanism_discovery as xmd


def _snap(mean_amp, amp_std, *, defect_count=0.0):
    return {
        "mean_amp": mean_amp,
        "amp_std": amp_std,
        "high_amp_fraction": 0.2,
        "spectral_k_rms": 0.3,
        "spectral_entropy": 0.4,
        "gradient_rms": 0.5,
        "defect_count": defect_count,
    }


def test_scale_normalization_distinguishes_absolute_growth_from_relative_heterogeneity():
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


def test_mature_nonspecific_pattern_is_not_starved_by_smaller_specific_pattern(monkeypatch):
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
    ledger = {"patterns": {}}

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


def test_mechanism_specs_change_only_start_side_controls_and_use_fresh_seeds():
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
    specs = xmd._specs(pattern_id="X-test", focus=focus, burst_id="b1", budget=8)
    assert len(specs) == 8
    assert len({x["seed"] for x in specs}) == 8
    assert [x["intervened_knob"] for x in specs[:2]] == [None, None]
    assert {x["intervened_knob"] for x in specs[2:]} == {"drive_strength", "diffusion_ratio", "quench_duration"}
    for spec in specs:
        assert spec["target_pattern_seeded"] is False
        assert spec["target_shape_seeded"] is False
        assert "event_time" not in spec
        assert "event_location" not in spec


def test_supported_scale_explanation_stays_simulator_level_and_requires_holdout_pressure():
    entry = {
        "target_events": 20,
        "unique_fresh_seeds": 10,
        "event_classes": {
            "AMPLITUDE_SCALE_TRACKING": 18,
            "RELATIVE_HETEROGENEITY_GROWTH": 1,
            "MIXED_OR_UNRESOLVED": 1,
        },
        "sum_amp_cv_log_gain": 0.1,
        "intervention_stats": {
            "baseline": {"n": 4, "hit": 4},
            "drive_strength": {"n": 4, "hit": 1},
            "diffusion_ratio": {"n": 4, "hit": 3},
        },
    }
    status, plain, driver = xmd._derive_status(entry)
    assert status == "SUPPORTED_SIMULATOR_MECHANISM_CANDIDATE"
    assert driver is not None
    assert driver["knob"] == "drive_strength"
    assert "自然界の基本法則" in plain
    entry["status"] = status
    entry["leading_driver_candidate"] = driver
    assert "holdout" in xmd._next_question(entry)
