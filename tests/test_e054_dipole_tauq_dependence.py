"""e054 H021-campaign tauQ-sweep tests (quench-rate phase-diagram context for e052/e053)."""
from experiments.e054_dipole_tauq_dependence.dipole_tauq_dependence import run, run_tauq_point, CONFIG_QUICK


def test_quick_run_is_valid_and_reaches_level2_everywhere():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    for row in r["by_tauq"]:
        assert row["n_reaching_level2"] == row["n_seeds"]


def test_tauq_point_uses_disjoint_fresh_seeds():
    row = run_tauq_point(CONFIG_QUICK[0])
    assert row["n_seeds"] == CONFIG_QUICK[0]["n_seeds"]
    assert row["seeds"] == list(range(CONFIG_QUICK[0]["seed_start"],
                                       CONFIG_QUICK[0]["seed_start"] + CONFIG_QUICK[0]["n_seeds"]))
    assert 0.0 <= row["level3_fraction"] <= 1.0


def test_verdict_field_is_present_and_honest():
    r = run(CONFIG_QUICK)
    assert r["verdict"] in ("level3_present_across_tauQ_range", "level3_vanishes_at_some_tauQ")
    assert r["trend"] in ("increasing_with_tauQ", "decreasing_with_tauQ", "no_clear_monotone_trend")
