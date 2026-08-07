from datetime import datetime, timezone

from ai_lab.dream import hourly_features as hourly
from ai_lab.dream.adaptive_loop import _director_due
from genesis.diagnostics import geometry_events as geom


def test_balanced_three_vortex_geometry_is_detected_without_seeding_logic():
    points = [
        {"y": 10.0, "x": 10.0, "charge": 1},
        {"y": 10.0, "x": 18.0, "charge": 1},
        {"y": 16.9, "x": 14.0, "charge": -1},
    ]
    tri = geom.best_triangle(points, (48, 48))
    assert tri is not None
    assert tri["qualified"] is True
    assert tri["regularity"] > 0.8
    assert sorted(tri["charge_pattern"]) == ["+", "+", "-"]


def test_nearly_collinear_three_vortices_do_not_count_as_triangle_hypothesis_hit():
    points = [
        {"y": 10.0, "x": 10.0, "charge": 1},
        {"y": 10.0, "x": 16.0, "charge": -1},
        {"y": 10.1, "x": 22.0, "charge": 1},
    ]
    tri = geom.best_triangle(points, (48, 48))
    assert tri is None or tri["qualified"] is False


def test_local_vortex_group_can_split_into_two_groups():
    centre = {"y": 24.0, "x": 24.0}
    joined = [
        {"y": 23.0, "x": 22.0, "charge": 1},
        {"y": 24.0, "x": 24.0, "charge": -1},
        {"y": 25.0, "x": 26.0, "charge": 1},
    ]
    split = [
        {"y": 20.0, "x": 20.0, "charge": 1},
        {"y": 20.5, "x": 20.5, "charge": -1},
        {"y": 28.0, "x": 28.0, "charge": 1},
    ]
    a = geom.local_cluster_count(joined, centre=centre, shape=(48, 48), neighbourhood_radius=12, link_radius=3)
    b = geom.local_cluster_count(split, centre=centre, shape=(48, 48), neighbourhood_radius=12, link_radius=3)
    assert a["clusters"] == 1
    assert b["clusters"] == 2


def test_research_director_only_rethinks_at_four_jst_hours():
    # UTC 18:17 = JST 03:17; UTC 19:17 = JST 04:17.
    assert _director_due(datetime(2026, 8, 7, 18, 17, tzinfo=timezone.utc)) is True
    assert _director_due(datetime(2026, 8, 7, 19, 17, tzinfo=timezone.utc)) is False
    assert _director_due(datetime(2026, 8, 8, 0, 17, tzinfo=timezone.utc)) is True  # JST 09:17


def test_triangle_hypothesis_keeps_counter_hypothesis_and_can_weaken(tmp_path, monkeypatch):
    target = tmp_path / "hypothesis.json"
    monkeypatch.setattr(hourly, "_HYPOTHESES", target)
    doc = {"version": 1, "hypotheses": []}
    out = hourly.update_triangle_hypothesis(
        doc,
        burst_id="dream-test",
        summary={"fission_like_after_triangle": 0, "triangle_without_fission": 4},
    )
    h = next(x for x in out["hypotheses"] if x["id"] == "three-vortex-triangle-fission")
    assert h["status"] == "WEAKENED"
    assert h["counter_statement"]
    assert h["confidence"] <= 0.5


def test_geometry_summary_never_calls_split_event_biological_cell_division():
    summary = hourly.geometry_summary([
        {
            "triangle_seen": True,
            "fission_like_after_triangle": True,
            "strongest_triangle": {"triangle_score": 0.9},
            "trial_index": 1,
            "family": "white",
            "seed": 7,
        }
    ])
    assert summary["fission_like_after_triangle"] == 1
    assert "not biological cell division" in summary["note"]
