"""e051 P07/E-candidate tests (result role N). Verifies the copy-collapse discriminator and honest exit."""
from experiments.e051_grown_slow_field.grown_slow_field import run, hysteresis_area, FROZEN, CONFIG_QUICK, MARGIN


def test_off_control_is_a_clean_baseline():
    a_off, e_off, s0, ss, hold = hysteresis_area((24, 24), 0.0, CONFIG_QUICK["K"], FROZEN, 0, "off")
    assert e_off < 1e6                              # energy bounded
    assert s0 == (0.0, 0.0)                         # OFF/grown start undifferentiated: zero structure


def test_grown_structure_grows_from_zero():
    # the SLOW FIELD's spatial structure must grow from an undifferentiated s(t=0)=0 (育った, even if not memory)
    r = run(CONFIG_QUICK)
    assert r["grown_struct_t0"] == 0.0
    assert r["grown_struct_settle"] > 1e-3
    assert r["checks"]["E3 structure GREW: struct(s;t0)=0 -> struct(s;settle)>0"]


def test_copy_collapse_history_gain_is_small():
    # the honest finding: an instantaneous copy (tau->0) reproduces the excess -> lag adds ~no memory
    r = run(CONFIG_QUICK)
    assert r["excess_copy"] > MARGIN               # coupling alone already produces the excess
    assert r["history_gain"] <= MARGIN             # grown - copy: lag adds no measurable memory
    assert r["e_candidate"] is False
    assert r["verdict"] == "memory_copy_collapse"


def test_run_is_valid_despite_negative_verdict():
    # a negative-capable run: valid + energy-bounded => exit 0 / STATUS GREEN, science reported separately
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert r["energy_ok"] is True
