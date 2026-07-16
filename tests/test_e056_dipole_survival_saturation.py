"""e056 H021-campaign saturation-check tests (role N -- unbounded persistence via pair lifetime not supported)."""
from experiments.e056_dipole_survival_saturation.dipole_survival_saturation import (
    run, run_window_point, CONFIG_QUICK, E055_REFERENCE,
)


def test_quick_run_is_valid():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert len(r["by_window"]) == len(CONFIG_QUICK)


def test_points_include_cited_e055_reference_not_recomputed():
    r = run(CONFIG_QUICK)
    multiples = [p["multiple"] for p in r["points"]]
    assert E055_REFERENCE["multiple"] in multiples
    cited = [p for p in r["points"] if p["source"] == "e055_cited"]
    assert len(cited) == 1
    assert cited[0]["global_max_duration_snapshots"] == E055_REFERENCE["global_max_duration_snapshots"]


def test_growth_ratios_are_computed_between_consecutive_points():
    r = run(CONFIG_QUICK)
    assert len(r["growth_ratios"]) == len(r["points"]) - 1
    for g in r["growth_ratios"]:
        assert g["window_ratio"] > 0
        assert isinstance(g["sublinear"], bool)


def test_window_point_uses_disjoint_fresh_seeds():
    row = run_window_point(CONFIG_QUICK[0])
    assert row["n_seeds"] == CONFIG_QUICK[0]["n_seeds"]
    assert row["seeds"] == list(range(CONFIG_QUICK[0]["seed_start"],
                                       CONFIG_QUICK[0]["seed_start"] + CONFIG_QUICK[0]["n_seeds"]))
