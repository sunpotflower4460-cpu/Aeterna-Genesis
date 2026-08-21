from __future__ import annotations

from ai_lab.dream.free_hypothesis_entrypoint import extract_evidence_context


def test_current_geometry_summary_is_used() -> None:
    easy = {
        "burst_id": "dream-test",
        "geometry_summary": {
            "detector_version": 4,
            "persistent_pair_seen": 32,
            "triad_local_energy_measured": 20,
            "energy_asymmetry_peak_preceded_geometry_collapse": 2,
            "triangle_seen": 4,
            "fission_like_after_triangle": 2,
            "control_seen": 17,
            "fission_like_after_control": 12,
        },
    }
    deep = {"leads": [{}, {}, {}]}
    top_unknown = {"pattern_id": "X-test", "family": "white", "knobs": {}}

    ctx = extract_evidence_context(easy, deep, top_unknown)

    assert ctx["pairs"] == 32
    assert ctx["triads"] == 20
    assert ctx["energy_precedes_geometry"] == 2
    assert ctx["triangle_seen"] == 4
    assert ctx["triangle_split"] == 2
    assert ctx["nontriangle_seen"] == 17
    assert ctx["nontriangle_split"] == 12
    assert ctx["deep_leads"] == 3
    assert ctx["easy_burst_id"] == "dream-test"
    assert ctx["geometry_detector_version"] == 4
    assert ctx["top_unknown"] == top_unknown


def test_legacy_top_level_report_is_still_supported() -> None:
    easy = {
        "persistent_pair_seen": 5,
        "triad_local_energy_measured": 3,
        "energy_asymmetry_peak_preceded_geometry_collapse": 1,
        "triangle_seen": 2,
        "fission_like_after_triangle": 1,
        "control_seen": 7,
        "fission_like_after_control": 4,
    }
    ctx = extract_evidence_context(easy, {"leads": []}, {"pattern_id": None})
    assert ctx["pairs"] == 5
    assert ctx["triads"] == 3
    assert ctx["triangle_split"] == 1
    assert ctx["nontriangle_split"] == 4
