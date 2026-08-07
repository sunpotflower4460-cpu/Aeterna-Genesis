import numpy as np

from ai_lab.dream import cross_world_emergence as cwe
from ai_lab.dream.multiworld import build_shadow_report
from genesis.models import q_tensor_nematic as q2
from genesis.models import vector_o3 as o3
from genesis.worlds.integrity import audit_plan
from genesis.worlds.registry import get_world, list_worlds
from genesis.worlds.spec import validate_world_spec
from genesis.worlds.time_horizon import HorizonPlan, next_horizon_multiplier
from genesis.worlds.zero_registry import get_zero, list_zeros


def test_world_registry_is_structurally_valid():
    worlds = list_worlds()
    assert {"g001-tdgl", "g003-model-h", "o3-vector", "q2-nematic", "relational-c4"} <= {w.world_id for w in worlds}
    for world in worlds:
        assert validate_world_spec(world) == []
        for zero_id in world.zero_ids:
            assert get_zero(zero_id)
    assert get_world("relational-c4").causal_closure == "C4"
    assert get_world("relational-c4").runnable_probe is None


def test_zero_registry_distinguishes_unbiased_and_correlated_starts():
    zeros = {z.zero_id: z for z in list_zeros()}
    assert zeros["Z-A"].strict_zero_candidate
    assert not zeros["Z-A"].imposed_length_scale
    assert zeros["Z-B"].strict_zero_candidate
    assert zeros["Z-B"].imposed_length_scale
    assert not zeros["Z-D"].strict_zero_candidate
    assert zeros["Z-R"].generation == "relational_substrate"


def test_o3_initial_state_is_unbiased_and_finite():
    rng = np.random.default_rng(1)
    phi = o3.make_initial((16, 16), 1e-3, rng)
    assert phi.shape == (16, 16, 3)
    assert np.isfinite(phi).all()
    assert np.max(np.abs(np.mean(phi, axis=(0, 1)))) < 5e-4
    r = o3.run((16, 16), steps=10, seed=2, snapshots=2)
    assert r["finite"]


def test_q_tensor_representation_is_symmetric_traceless_by_construction():
    r = q2.run((16, 16), steps=10, seed=3, snapshots=2)
    assert r["finite"]
    inv = r["tensor_invariants"]
    assert inv["max_abs_trace"] == 0.0
    assert inv["max_symmetry_error"] == 0.0


def test_deep_time_is_world_relative_and_predeclared():
    p = HorizonPlan(8.0)
    assert p.physical_times() == (8.0, 32.0, 128.0, 512.0)
    assert next_horizon_multiplier(1.0) == 4.0
    assert next_horizon_multiplier(64.0) is None


def test_integrity_plan_does_not_change_science_gates():
    plan = audit_plan(solver_alternative_available=True)
    kinds = {x["kind"] for x in plan["variants"]}
    assert {"dt", "dx", "box_size", "seed", "solver"} <= kinds
    assert plan["promotion_effect"] is False
    assert plan["changes_success_thresholds"] is False


def test_g001_fingerprint_projects_only_shared_observables():
    projected = cwe.project_g001_fingerprint(
        "amp_std:+L|defect_count:-M|gradient_rms:+S|net_topological_charge:+M"
    )
    assert projected["fingerprint"] == "order_std:+L|spatial_gradient:+S"
    assert projected["coverage"] == 0.5
    assert set(projected["dropped_parts"]) == {"defect_count:-M", "net_topological_charge:+M"}


def test_cross_world_match_keeps_scaffolded_source_as_overlap_only():
    target = [{
        "pattern_id": "CWX-test", "fingerprint": "order_std:+L", "world_id": "o3-vector",
        "zero_id": "Z-A", "seed": 2, "strict_zero_candidate": True,
    }]
    ledger = {
        "patterns": [{
            "pattern_id": "X-test", "fingerprint": "amp_std:+L", "status": "ROBUST_RECURRENT_CANDIDATE",
            "representative": {"zero_purity": "scaffolded-start"},
        }],
        "recent_episodes": [],
    }
    match = cwe.compare_g001_patterns(episodes=target, g001_ledger=ledger)[0]
    assert match["status"] == "SIGNATURE_OVERLAP_ONLY"
    assert match["strict_ZA_alignment"] is False
    assert match["universality_claim"] is False
    assert match["identical_physics_claim"] is False


def test_cross_world_match_can_be_zero_aligned_without_becoming_universality_claim():
    target = [{
        "pattern_id": "CWX-test", "fingerprint": "order_std:+L", "world_id": "q2-nematic",
        "zero_id": "Z-A", "seed": 9, "strict_zero_candidate": True,
    }]
    ledger = {
        "patterns": [{
            "pattern_id": "X-test", "fingerprint": "amp_std:+L", "status": "CROSS_CONDITION_RECURRENT",
            "representative": {"zero_purity": "Z-A:minimal-white"},
        }],
        "recent_episodes": [{"pattern_id": "X-test", "zero_purity": "Z-A:minimal-white"}],
    }
    match = cwe.compare_g001_patterns(episodes=target, g001_ledger=ledger)[0]
    assert match["status"] == "CROSS_WORLD_ZERO_ALIGNED_LEAD"
    assert match["strict_ZA_alignment"] is True
    assert match["universality_claim"] is False


def test_common_change_detector_uses_neutral_feature_names():
    snaps = []
    for i in range(5):
        snaps.append({
            "physical_time": float(i), "order_mean": 1.0, "order_std": 0.1,
            "global_alignment": 0.1, "spectral_entropy": 0.8, "spectral_k_rms": 0.1,
            "spectral_anisotropy": 0.1, "spatial_gradient": 0.1, "high_order_fraction": 0.2,
        })
    for i in range(5, 9):
        snaps.append({
            "physical_time": float(i), "order_mean": 1.0, "order_std": 0.9,
            "global_alignment": 0.1, "spectral_entropy": 0.8, "spectral_k_rms": 0.1,
            "spectral_anisotropy": 0.1, "spatial_gradient": 0.1, "high_order_fraction": 0.2,
        })
    probe = {"snapshots": snaps, "analysis_start_time": 1.0, "world_id": "o3-vector", "zero_id": "Z-A", "seed": 4}
    episodes = cwe.detect_common_episodes(probe, max_episodes=2)
    assert episodes
    assert "order_std:+" in episodes[0]["fingerprint"]
    assert "amp_std" not in episodes[0]["fingerprint"]


def test_multiworld_shadow_report_is_non_promoting_and_cross_law():
    report = build_shadow_report(seed=7, quick=True)
    assert report["mode"] == "shadow"
    assert report["errors"] == []
    assert report["director_policy"]["promotion_effect"] is False
    assert report["director_policy"]["official_level_effect"] is False
    assert report["director_policy"]["single_success_score_across_worlds"] is False
    observed = {(x["world_id"], x["zero_id"]) for x in report["observations"]}
    assert ("g001-tdgl", "Z-A") in observed
    assert ("g001-tdgl", "Z-B") in observed
    assert ("g003-model-h", "Z-A") in observed
    assert ("o3-vector", "Z-A") in observed
    assert ("q2-nematic", "Z-A") in observed
    assert all(x["official_emergence_level"] is None for x in report["observations"])
    cross = report["open_ended_cross_world"]
    assert not cross.get("comparator_failed", False)
    assert cross["promotion_effect"] is False
    assert cross["official_level_effect"] is False
    assert cross["hypothesis_confidence_effect"] is False
    assert cross["same_fingerprint_means_same_physics"] is False
    assert cross["universality_claim"] is False
    assert cross["finite_probes"] == len(report["observations"])
