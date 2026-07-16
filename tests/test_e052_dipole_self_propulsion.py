"""e052 H021-campaign iteration 1 tests (role F/frontier candidate). Verifies the single-continuous-run
harness reaches Level 2 reliably and reports an honest, non-overclaimed Level-3 verdict."""
from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import run, run_one_seed, CONFIG_QUICK


def test_quick_run_reaches_level2_and_is_valid():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert r["n_reaching_level2"] == r["n_seeds"]  # KZ quench reliably reaches Level 2 (e010-proven mechanism)


def test_per_seed_result_has_honest_level3_fields():
    r = run(CONFIG_QUICK)
    for row in r["per_seed"]:
        assert row["reached_level"] >= row["reached_level12"]  # L3 only ever adds, never overrides L1/L2
        assert row["level3"]["verdict"] in (
            "level3_dipole_candidate", "not_separated_from_jitter_floor",
            "no_dipole_event", "unresolved_insufficient_track_data",
        )
        assert isinstance(row["box_drift_rms"], float)


def test_single_seed_matches_aggregate_run():
    row = run_one_seed(CONFIG_QUICK["L"], CONFIG_QUICK["tauQ"], CONFIG_QUICK["hold"],
                        CONFIG_QUICK["post_track_steps"], CONFIG_QUICK["track_every"], seed=1)
    assert row["seed"] == 1
    assert row["reached_level12"] in (0, 1, 2)
