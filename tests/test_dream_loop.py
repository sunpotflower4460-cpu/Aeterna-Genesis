import json

from jsonschema import Draft202012Validator

from ai_lab.dream.events import (
    classify_search_candidate,
    events_from_autopilot,
    novelty_score,
)
from ai_lab.dream.loop import _native_campaign_doc
from ai_lab.dream.presets import make_view_preset
from ai_lab.dream.report import build_report, render_markdown


def sample(seed=1, level=2, defects=4, knobs=None):
    return {
        "family": "white",
        "seed": seed,
        "status": "2d_screened",
        "reached_level": level,
        "score": float(level) + 0.4,
        "complexity": 0.55,
        "knobs": knobs or {
            "noise_amplitude": 0.003,
            "correlation_length": 3.0,
            "diffusion_ratio": 1.0,
            "drive_strength": 2.0,
            "quench_duration": 8.0,
        },
        "measured_by": {
            "mean_amplitude_growth": 120.0,
            "structure_factor_prominence": 3.0,
            "defect_count": defects,
        },
    }


def test_novelty_is_low_against_same_history_and_not_a_gate():
    c = sample()
    n_same = novelty_score(c, [dict(c)])
    n_new = novelty_score(
        sample(
            seed=2,
            level=4,
            defects=18,
            knobs={
                "noise_amplitude": 1.0e-4,
                "correlation_length": 12.0,
                "diffusion_ratio": 8.0,
                "drive_strength": 5.0,
                "quench_duration": 20.0,
            },
        ),
        [c],
    )
    assert n_same < 0.01
    assert n_new > n_same


def test_reproduction_event_requires_two_thirds_of_three_seeds():
    c = sample(level=2)
    reruns = [
        {**sample(seed=11, level=2), "seed": 11},
        {**sample(seed=12, level=2), "seed": 12},
        {**sample(seed=13, level=1), "seed": 13},
    ]
    events = classify_search_candidate(c, parent_level=1, history=[], reruns=reruns)
    kinds = {e["kind"] for e in events}
    assert "REPRODUCED" in kinds
    reproduced = next(e for e in events if e["kind"] == "REPRODUCED")
    assert reproduced["facts"]["reproduction"]["matched"] == 2
    assert reproduced["scientific_status"] == "2d_reproducible"


def test_autopilot_local3d_pass_and_failure_become_human_events():
    base = {
        "campaign_id": "dream-x",
        "hypothesis_id": "native-window",
        "trial_id": "native-window-v000",
        "parent_room": "room-g001-a",
        "seed": 9,
        "overrides": {"noise_amplitude": 0.003},
        "reached_level": 2,
        "min_reached_level": 1,
        "measured_by": {"defect_count": 3},
    }
    discoveries = [
        {**base, "job_id": "j-pass", "stage": "local-3d", "survived_stage": True, "result_room": "room-pass"},
        {**base, "job_id": "j-fail", "stage": "local-3d", "survived_stage": False, "result_room": "room-fail"},
    ]
    events, seen = events_from_autopilot(discoveries)
    assert {e["kind"] for e in events} == {"PROMOTION_READY", "DIMENSION_FAILURE"}
    assert seen == {"j-pass", "j-fail"}
    ready = next(e for e in events if e["kind"] == "PROMOTION_READY")
    assert ready["room_id"] == "room-pass"
    assert "coarse 3D" in ready["plain"]


def test_view_preset_is_observation_only():
    event = {
        "event_id": "evt-123",
        "room_id": "room-cand",
        "parent_room": "room-g001-a",
        "facts": {"measured_by": {"defect_count": 5}},
    }
    p = make_view_preset(event)
    assert p["ready"] is True
    assert p["lens"] == "phase"
    assert p["comparison"]["mode"] == "parent_vs_candidate"
    assert p["honesty"]["changes_physics"] is False
    assert p["honesty"]["scientific_promotion"] is False


def test_native_campaign_stops_at_existing_human_gates():
    doc = _native_campaign_doc(campaign_id="dream-20260807-0001", seed=7, variant_count=3, repro_seeds=3, quick=True)
    schema = json.load(open("schemas/campaign.schema.json"))
    Draft202012Validator(schema).validate(doc)
    assert doc["approval_required"] == ["coarse-global-3d", "full-3d"]
    assert len(doc["hypotheses"][0]["search"]["variants"]) == 3
    assert len(doc["seeds"]) == 3


def test_night_report_is_plain_language_and_marks_honesty():
    event = {
        "event_id": "evt-a",
        "kind": "REPRODUCED",
        "title": "別seedでも再現",
        "plain": "3 seed中2 seedで再現しました。",
        "why": "偶然依存を減らすためです。",
        "facts": {"reached_level": 2, "reproduction": {"matched": 2, "tested": 3}},
        "scientific_status": "2d_reproducible",
        "visual_interest": "high",
        "room_id": None,
        "parent_room": "room-g001-a",
        "view_preset_id": "view-a",
    }
    report = build_report([event], burst_id="dream-test", expanded_trials=10, native_jobs=2,
                          generated_at="2026-08-07T00:00:00+00:00")
    assert report["counts"]["experiments"] == 12
    assert report["counts"]["reproduced"] == 1
    assert report["honesty"]["llm_required"] is False
    assert report["honesty"]["novelty_is_success_gate"] is False
    md = render_markdown(report)
    assert "Genesis Night Report" in md
    assert "再現成功" in md
    assert "official" in md
