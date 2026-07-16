"""e053 H021-campaign robustness follow-up tests. Verifies the resolution sweep + Wilson-CI statistics
harness runs validly and reports honest, non-overclaimed verdicts (structural checks only -- the
QUICK config is not expected to reproduce e052's L=96 candidate, since it uses smaller/faster grids)."""
from experiments.e053_dipole_robustness.dipole_robustness import run, run_resolution, CONFIG_QUICK, _wilson_interval


def test_wilson_interval_bounds():
    p, lo, hi = _wilson_interval(0, 10)
    assert p == 0.0 and lo == 0.0 and hi < 1.0
    p, lo, hi = _wilson_interval(10, 10)
    assert p == 1.0 and hi == 1.0
    p, lo, hi = _wilson_interval(5, 10)
    assert p == 0.5 and lo < 0.5 < hi


def test_run_resolution_uses_disjoint_fresh_seeds():
    row = run_resolution(CONFIG_QUICK[0])
    assert row["n_seeds"] == CONFIG_QUICK[0]["n_seeds"]
    assert row["seeds"] == list(range(CONFIG_QUICK[0]["seed_start"],
                                       CONFIG_QUICK[0]["seed_start"] + CONFIG_QUICK[0]["n_seeds"]))
    assert 0.0 <= row["level3_fraction"] <= 1.0
    assert row["level3_fraction_ci95"][0] <= row["level3_fraction"] <= row["level3_fraction_ci95"][1]


def test_quick_run_is_valid_and_reaches_level2():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    for row in r["by_resolution"]:
        assert row["n_reaching_level2"] == row["n_seeds"]  # KZ quench reliably reaches Level 2
    assert r["verdict"] in (
        "robust_level3_candidate_confirmed", "finite_size_artifact_suspected",
        "level3_not_reproduced", "marginal_not_resolved",
    )
