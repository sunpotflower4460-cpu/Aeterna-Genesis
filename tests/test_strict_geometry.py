from ai_lab.dream import strict_geometry as strict
from genesis.diagnostics import geometry_events as geom


def test_dense_cloud_does_not_make_arbitrary_triangle_without_mutual_nearest_triad():
    # The equilateral-looking outer points are not each other's two nearest neighbours because of
    # the dense centre cloud; they must not be promoted just because a combination of three looks nice.
    points = [
        {"y": 5.0, "x": 5.0, "charge": 1},
        {"y": 5.0, "x": 25.0, "charge": -1},
        {"y": 22.3, "x": 15.0, "charge": 1},
        {"y": 12.0, "x": 12.0, "charge": 1},
        {"y": 12.5, "x": 12.5, "charge": -1},
        {"y": 13.0, "x": 12.0, "charge": 1},
        {"y": 12.0, "x": 13.0, "charge": -1},
    ]
    tri = geom.best_triangle(points, (48, 48))
    if tri is not None:
        ids = set(tri["indices"])
        assert ids != {0, 1, 2}
        assert tri["mutual_nearest"] is True


def test_nontriangle_mutual_triad_is_available_as_control():
    points = [
        {"y": 10.0, "x": 10.0, "charge": 1},
        {"y": 10.0, "x": 13.0, "charge": -1},
        {"y": 10.2, "x": 18.0, "charge": 1},
    ]
    assert geom.best_triangle(points, (48, 48)) is None
    control = geom.best_control_triad(points, (48, 48))
    assert control is not None
    assert control["kind"] == "control"


def test_hypothesis_does_not_move_without_triangle_and_control_samples(tmp_path, monkeypatch):
    path = tmp_path / "hypotheses.json"
    monkeypatch.setattr(strict, "_HYPOTHESES", path)
    doc = {"version": 1, "hypotheses": []}
    out = strict.update_triangle_hypothesis(
        doc, burst_id="b1",
        summary={
            "triangle_seen": 5, "fission_like_after_triangle": 3,
            "control_seen": 0, "fission_like_after_control": 0,
            "comparison_ready": False,
        },
    )
    h = next(x for x in out["hypotheses"] if x["id"] == "three-vortex-triangle-fission")
    assert h["support"] == 0
    assert h["contradiction"] == 0
    assert h["confidence"] == 0.5
    assert h["status"] == "TESTING"


def test_one_burst_is_only_one_support_unit_even_with_many_split_events(tmp_path, monkeypatch):
    path = tmp_path / "hypotheses.json"
    monkeypatch.setattr(strict, "_HYPOTHESES", path)
    doc = {"version": 1, "hypotheses": []}
    out = strict.update_triangle_hypothesis(
        doc, burst_id="b1",
        summary={
            "triangle_seen": 10, "fission_like_after_triangle": 8,
            "control_seen": 10, "fission_like_after_control": 2,
            "rate_given_triangle": 0.8, "rate_given_control": 0.2,
            "triangle_excess_rate": 0.6, "comparison_ready": True,
        },
    )
    h = next(x for x in out["hypotheses"] if x["id"] == "three-vortex-triangle-fission")
    assert h["support"] == 1
    assert h["contradiction"] == 0
    assert h["status"] == "TESTING"
    assert h["confidence"] <= 0.65


def test_control_equal_or_higher_rate_counts_against_triangle_hypothesis(tmp_path, monkeypatch):
    path = tmp_path / "hypotheses.json"
    monkeypatch.setattr(strict, "_HYPOTHESES", path)
    doc = {"version": 1, "hypotheses": []}
    out = strict.update_triangle_hypothesis(
        doc, burst_id="b1",
        summary={
            "triangle_seen": 8, "fission_like_after_triangle": 2,
            "control_seen": 8, "fission_like_after_control": 3,
            "rate_given_triangle": 0.25, "rate_given_control": 0.375,
            "triangle_excess_rate": -0.125, "comparison_ready": True,
        },
    )
    h = next(x for x in out["hypotheses"] if x["id"] == "three-vortex-triangle-fission")
    assert h["support"] == 0
    assert h["contradiction"] == 1
