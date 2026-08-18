import numpy as np

from ai_lab.dream import adaptive_v8, emergent_field, strict_goal_loop


def test_uniform_noise_plan_is_deterministic_and_inside_registered_space():
    a = emergent_field.trial_parameters(3, seed=17)
    b = emergent_field.trial_parameters(3, seed=17)
    c = emergent_field.trial_parameters(4, seed=17)
    assert a == b
    assert a != c
    for key, value in a.items():
        lo, hi = emergent_field.SPACE[key]
        assert lo <= value <= hi


def test_uniform_initial_condition_has_no_hand_placed_founder_spots():
    rng = np.random.default_rng(5)
    U, V = emergent_field.make_uniform_noise_initial(
        (32, 32), v_background=0.04, noise_amplitude=1.0e-3, rng=rng,
    )
    assert U.shape == (32, 32)
    assert V.shape == (32, 32)
    assert np.all(np.isfinite(U)) and np.all(np.isfinite(V))
    assert float(np.std(V)) > 0.0
    # The IC is distributed noise around one homogeneous background, not a few painted Gaussian seeds.
    assert 0.02 < float(np.mean(V)) < 0.06
    assert float(np.max(V) - np.min(V)) < 0.02


def test_observer_does_not_force_features_into_a_uniform_field():
    initial = np.full((24, 24), 0.05)
    final = np.full((24, 24), 0.05)
    obs = emergent_field.observe_morphology(initial, final, previous_v=final)
    assert obs["localized_region_count"] == 0
    assert obs["strong_core_count"] == 0
    assert obs["corridor_candidate_count"] == 0
    assert obs["observer_semantics"]["network_claim"] is False
    assert obs["observer_semantics"]["node_claim"] is False
    assert obs["observer_semantics"]["edge_claim"] is False


def test_small_frontier_run_is_observation_only_and_keeps_negative_results():
    report = emergent_field.run_emergent_field_research(
        burst_id="unit-field", trials=2, seed=9, quick=True, persist=False,
    )
    assert report["trials"] == 2
    assert len(report["results"]) == 2
    assert report["initial_condition"]["founder_spots"] == 0
    assert report["initial_condition"]["target_morphology_seeded"] is False
    assert report["law"]["law_variant"] is False
    assert report["search_policy"]["feedback_from_morphology_to_dynamics"] is False
    assert report["honesty"]["observer_metrics_are_success_criteria"] is False
    assert report["honesty"]["negative_results_are_retained"] is True
    assert report["honesty"]["this_is_pure_genesis_R0_proof"] is False
    assert "network" in report["not_claimed"]
    assert "brain" in report["not_claimed"]


def test_adaptive_v8_parser_enables_frontier_by_default_and_can_disable_explicitly():
    parser = adaptive_v8.build_parser()
    default = parser.parse_args([])
    disabled = parser.parse_args(["--emergent-field-trials", "0"])
    assert default.emergent_field_trials > 0
    assert disabled.emergent_field_trials == 0


def test_strict_goal_loop_forwards_emergent_field_budget(monkeypatch):
    seen = {}

    def fake_run(**kwargs):
        seen.update(kwargs)
        return {"report": {"burst_id": "unit"}}

    monkeypatch.setattr(strict_goal_loop.adaptive_v8, "run_adaptive_v8", fake_run)
    strict_goal_loop._run_adaptive_v8_exact(["--emergent-field-trials", "7", "--no-refresh-app"])
    assert seen["emergent_field_trials"] == 7
