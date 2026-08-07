from ai_lab.dream import fission_path
from ai_lab.dream import strict_geometry as strict
from genesis.diagnostics import geometry_events as geom


def _knobs():
    return {
        "noise_amplitude": 1e-3,
        "correlation_length": 1.0,
        "diffusion_ratio": 1.0,
        "drive_strength": 1.0,
        "quench_duration": 8.0,
    }


def test_scaffolded_start_cannot_claim_strict_zero_path():
    p = fission_path.assess_probe({
        "family": "sparse_seeds",
        "reached_level": 2,
        "persistent_relation_seen": True,
        "triangle_seen": True,
        "balance_collapse_seen": True,
        "pre_split_instability_candidate": True,
        "network_fission_candidate": True,
    })
    assert p["strict_zero_eligible"] is False
    assert p["depth"] == -1


def test_path_depth_is_contiguous_and_cannot_skip_balance_loss():
    p = fission_path.assess_probe({
        "family": "white",
        "reached_level": 2,
        "persistent_relation_seen": True,
        "triangle_seen": True,
        "balance_collapse_seen": False,
        "pre_split_instability_candidate": True,
        "network_fission_candidate": True,
    })
    assert p["depth"] == 4
    assert p["flags"]["7"] is True
    # A later-looking event cannot be stitched over a missing earlier stage.
    assert p["next_stage"] == 5


def test_summary_keeps_multiple_deep_frontiers():
    probes = []
    for i, depth_flags in enumerate([
        (True, False, False),
        (True, True, False),
        (True, True, True),
    ]):
        collapse, unstable, fission = depth_flags
        probe = {
            "trial_index": i,
            "family": "white",
            "knobs": _knobs(),
            "seed": 100 + i,
            "reached_level": 2,
            "persistent_relation_seen": True,
            "triangle_seen": True,
            "balance_collapse_seen": collapse,
            "pre_split_instability_candidate": unstable,
            "network_fission_candidate": fission,
        }
        probe["zero_to_fission"] = fission_path.assess_probe(probe)
        probes.append(probe)
    summary = fission_path.summarize(probes)
    assert summary["deepest_contiguous_stage"] == 7
    assert len(summary["frontier_candidates"]) == 3
    assert summary["frontier_candidates"][0]["depth"] == 7
    assert summary["triangle_is_required"] is False


def test_balanced_triangle_can_be_followed_by_connected_collapse_then_split():
    shape = (48, 48)
    triangle_points = [
        {"y": 10.0, "x": 10.0, "charge": 1},
        {"y": 10.0, "x": 13.0, "charge": -1},
        {"y": 12.598, "x": 11.5, "charge": 1},
    ]
    anchor = geom.best_triangle(triangle_points, shape)
    assert anchor is not None

    # Still one connected chain, but the balanced triangle has collapsed into a nearly straight triad.
    collapsed_points = [
        {"y": 10.0, "x": 10.0, "charge": 1},
        {"y": 10.0, "x": 13.0, "charge": -1},
        {"y": 10.0, "x": 16.0, "charge": 1},
    ]
    collapsed = geom.best_mutual_triad(collapsed_points, shape)
    assert collapsed is not None

    # Two connected subgroups inside the remembered neighbourhood.
    split_points = [
        {"y": 9.0, "x": 10.0, "charge": 1},
        {"y": 9.0, "x": 13.0, "charge": -1},
        {"y": 14.0, "x": 12.0, "charge": 1},
    ]
    snapshots = [
        {"step": 0, "points": triangle_points, "triad": geom.best_mutual_triad(triangle_points, shape), "triangle": anchor},
        {"step": 1, "points": triangle_points, "triad": geom.best_mutual_triad(triangle_points, shape), "triangle": anchor},
        {"step": 2, "points": collapsed_points, "triad": collapsed, "triangle": None},
        {"step": 3, "points": collapsed_points, "triad": collapsed, "triangle": None},
        # After balance loss is established, require the same one-group instability to persist again.
        {"step": 4, "points": collapsed_points, "triad": collapsed, "triangle": None},
        {"step": 5, "points": split_points, "triad": geom.best_mutual_triad(split_points, shape), "triangle": None},
        {"step": 6, "points": split_points, "triad": geom.best_mutual_triad(split_points, shape), "triangle": None},
    ]
    transition = strict._triangle_transition_after(snapshots, 0, anchor, shape)
    assert transition["balance_collapse_seen"] is True
    assert transition["pre_split_instability_candidate"] is True
    assert transition["persistent_split_seen"] is True
    assert transition["network_fission_candidate"] is True


def test_balance_hypothesis_needs_matched_triangle_samples(tmp_path, monkeypatch):
    path = tmp_path / "hypotheses.json"
    monkeypatch.setattr(strict, "_HYPOTHESES", path)
    out = strict.update_triangle_hypothesis(
        {"version": 1, "hypotheses": []},
        burst_id="b1",
        summary={
            "comparison_ready": False,
            "balance_comparison_ready": True,
            "balance_collapse_excess_rate": 0.5,
            "balance_collapse_seen": 5,
            "split_after_balance_collapse": 4,
            "triangle_without_balance_collapse": 5,
            "split_without_balance_collapse": 1,
        },
    )
    h = next(x for x in out["hypotheses"] if x["id"] == "triangle-balance-break-fission")
    assert h["support"] == 1
    assert h["contradiction"] == 0
    assert h["confidence"] <= 0.65
