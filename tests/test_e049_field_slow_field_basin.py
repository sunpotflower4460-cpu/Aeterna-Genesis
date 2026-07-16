"""e049 P07/S1 slow-field basin memory tests (role S). Verifies the matched-control mechanism harness."""
from experiments.e049_field_slow_field_basin.field_slow_field_basin import run, sweep, FROZEN, CONFIG_QUICK


def test_slow_field_adds_hysteresis_vs_matched_off_control():
    r = run(CONFIG_QUICK)
    # the ON coupling must produce more hysteresis than the matched g=0 OFF control (control-separated memory)
    assert r["area_on"] > r["area_off"]
    assert r["hysteresis_excess"] > 0.0
    # and sustain more order at the neutral point
    assert r["retain_on"] > r["retain_off"]


def test_off_control_is_the_no_feedback_baseline():
    """g=0: the slow field is passive, so alpha0 enters only additively -> lower hysteresis than ON."""
    on = sweep(FROZEN["g_on"], CONFIG_QUICK, FROZEN, seed=0)
    off = sweep(0.0, CONFIG_QUICK, FROZEN, seed=0)
    assert on["area"] >= off["area"]
    assert on["retain"] >= off["retain"]


def test_energy_bounded_and_not_a_copy():
    r = run(CONFIG_QUICK)
    assert r["energy_ok"]
    assert r["not_copy"]                       # s lags |psi|^2, not an instantaneous copy


def test_verdict_is_a_clean_classified_outcome():
    r = run(CONFIG_QUICK)
    assert r["verdict"] in ("slow_field_basin_memory_candidate", "common_attractor_relaxation_candidate")
    # exactly one classification flag is set
    assert sum(bool(v) for v in r["classification"].values()) == 1
