import numpy as np

from ai_lab.dream import strict_geometry
from genesis.diagnostics import geometry_events as geom
from genesis.diagnostics import vortex_energy as veng
from genesis.models import ginzburg_landau as gl


def _point(y, x, charge=1):
    return {"y": float(y), "x": float(x), "charge": int(charge)}


def test_instantaneous_density_preserves_legacy_quench_independent_mean():
    rng = np.random.default_rng(4)
    psi = rng.normal(size=(12, 12)) + 1j * rng.normal(size=(12, 12))
    p = dict(gl.DEFAULTS)
    d = veng.instantaneous_energy_density(psi, t=3.25, p=p)
    assert np.isfinite(d["total"]).all()
    assert np.isclose(float(np.mean(d["quench_independent"])), gl.free_energy(psi, p), rtol=1e-12, atol=1e-12)
    assert np.allclose(d["total"], d["quadratic"] + d["quartic"] + d["gradient"])


def test_uniform_field_has_zero_gradient_energy_and_expected_instantaneous_potential():
    psi = np.full((10, 10), 0.5 + 0.0j)
    p = dict(gl.DEFAULTS)
    t = 20.0  # after the quench, eps=eps_final
    d = veng.instantaneous_energy_density(psi, t=t, p=p)
    assert np.max(np.abs(d["gradient"])) == 0.0
    amp2 = 0.25
    expected = -0.5 * p["eps_final"] * amp2 + 0.25 * amp2 * amp2
    assert np.allclose(d["total"], expected)


def test_best_mutual_pair_is_geometric_and_charge_aware():
    points = [_point(2, 2, 1), _point(2, 4, -1), _point(12, 12, 1)]
    pair = geom.best_mutual_pair(points, (16, 16))
    assert pair is not None
    assert set(pair["indices"]) == {0, 1}
    assert pair["charge_pattern"] == "+-"
    assert pair["separation"] == 2.0
    assert pair["kind"] == "pair"


def test_pair_energy_measures_cores_bridge_and_outer_ring_without_claiming_force():
    rng = np.random.default_rng(5)
    psi = (0.2 * (rng.normal(size=(24, 24)) + 1j * rng.normal(size=(24, 24)))).astype(np.complex128)
    points = [_point(12.5, 8.5, 1), _point(12.5, 15.5, -1)]
    pair = {
        "indices": [0, 1], "kind": "pair", "centroid": {"y": 12.5, "x": 12.0},
        "separation": 7.0, "max_side": 7.0,
    }
    e = veng.relation_energy_landscape(
        psi, t=12.0, p=dict(gl.DEFAULTS), points=points, relation=pair, shape=(24, 24),
    )
    assert e is not None
    assert e["relation_size"] == 2
    assert e["bridge"]["total"]["cells"] > 0
    assert e["outer_ring"]["total"]["cells"] > 0
    assert len(e["cores"]) == 2
    assert e["measurement_only"] is True
    assert e["binding_energy_claim"] is False
    assert e["force_claim"] is False
    compact = veng.compact_energy_features(e)
    assert "energy_bridge_minus_outer" in compact
    assert compact["energy_charge_pattern"] == "+-"


def test_triad_energy_handles_periodic_boundary_and_has_interior_edge_stats():
    rng = np.random.default_rng(6)
    psi = (0.15 * (rng.normal(size=(24, 24)) + 1j * rng.normal(size=(24, 24)))).astype(np.complex128)
    points = [_point(1.5, 1.5, 1), _point(1.5, 22.5, 1), _point(22.5, 1.5, -1)]
    triad = {
        "indices": [0, 1, 2], "kind": "mutual", "centroid": {"y": 0.5, "x": 0.5},
        "side_lengths": [3.0, 3.0, 4.2426], "max_side": 4.2426,
    }
    e = veng.relation_energy_landscape(
        psi, t=12.0, p=dict(gl.DEFAULTS), points=points, relation=triad, shape=(24, 24),
    )
    assert e is not None
    assert e["relation_size"] == 3
    assert e["edges"]["total"]["cells"] > 0
    # Very small triangles can have no core-excluded interior cell, but the statistic must remain explicit.
    assert "cells" in e["interior"]["total"]
    assert len(e["cores"]) == 3
    compact = veng.compact_energy_features(e)
    assert "energy_interior_minus_outer" in compact
    assert "energy_edges_minus_outer" in compact


def test_geometry_summary_keeps_energy_observational_and_separate_from_F_path():
    probes = [
        {
            "persistent_pair_seen": True,
            "persistent_pair_only_seen": True,
            "pair": {"charge_pattern": "+-"},
            "pair_energy_summary": {"measured": True},
            "persistent_relation_seen": True,
            "relation": {"charge_pattern": "++-"},
            "triad_energy_summary": {
                "measured": True,
                "baseline_vertex_energy_asymmetry": 0.2,
                "energy_asymmetry_peak_precedes_geometry_collapse": True,
            },
            "triangle_seen": True,
            "control_seen": False,
            "fission_like_after_triangle": False,
            "fission_like_after_control": False,
            "balance_collapse_seen": True,
            "pre_split_instability_candidate": False,
            "network_fission_candidate": False,
            "zero_to_fission": {
                "depth": 4, "strict_zero_eligible": True, "path_id": "relation-fission-F",
                "depth_code": "F4", "start_purity": "Z-A:minimal-white",
            },
            "trial_index": 1, "family": "white", "knobs": {}, "seed": 1,
        }
    ]
    s = strict_geometry.geometry_summary(probes)
    assert s["persistent_pair_seen"] == 1
    assert s["pair_local_energy_measured"] == 1
    assert s["triad_local_energy_measured"] == 1
    assert s["pair_charge_patterns_measured"] == {"+-": 1}
    assert s["energy_asymmetry_peak_preceded_geometry_collapse"] == 1
    assert s["local_energy_observation"]["energy_used_to_select_relation"] is False
    assert s["local_energy_observation"]["binding_energy_claim"] is False
    assert s["zero_to_fission_path"]["official_emergence_levels_unchanged"] is True
