"""e055 H021-campaign survival-time tests (role F -- open frontier, saturation not resolved)."""
from experiments.e055_dipole_survival_time.dipole_survival_time import (
    run, run_one_seed_survival, CONFIG_QUICK, PRIOR_WINDOW_SNAPSHOTS,
)


def test_quick_run_is_valid():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert r["n_seeds"] == CONFIG_QUICK["n_seeds"]


def test_per_seed_reports_absolute_and_fractional_duration():
    row = run_one_seed_survival(CONFIG_QUICK["seed_start"], CONFIG_QUICK["post_track_steps"])
    assert row["max_duration_snapshots"] >= 0
    assert 0.0 <= row["max_survival_fraction"] <= 1.0
    if row["durations"]:
        assert row["max_duration_snapshots"] == max(row["durations"])


def test_verdict_is_honest_about_unresolved_saturation():
    r = run(CONFIG_QUICK)
    assert "saturation_unresolved" in r["verdict"] or r["verdict"] == "no_long_lived_compound_in_budget"
    assert r["prior_window_snapshots"] == PRIOR_WINDOW_SNAPSHOTS
