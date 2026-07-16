"""e058 H021-campaign tests (role V/N -- censoring-aware re-measurement of e055/e056's question)."""
from experiments.e058_dipole_survival_km.dipole_survival_km import run, run_one_seed, CONFIG_QUICK


def test_quick_run_is_valid_and_finds_episodes():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert r["n_episodes_total"] > 0


def test_km_summary_reports_censoring_honestly():
    r = run(CONFIG_QUICK)
    km = r["km_summary"]
    assert km is not None
    assert 0.0 <= km["censoring_fraction"] <= 1.0
    assert km["n"] == r["n_episodes_total"]
    assert km["n_events"] + km["n_censored"] == km["n"]


def test_single_seed_episodes_have_start_before_end():
    row = run_one_seed(CONFIG_QUICK["seed_start"], CONFIG_QUICK["post_track_steps"])
    assert row["n_episodes"] == len(row["durations"]) == len(row["censored"])
    for d in row["durations"]:
        assert d >= 1
