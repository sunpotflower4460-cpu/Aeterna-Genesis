"""e050 P07/S2 robustness tests (role S). Verifies the coupling/resolution/seed/3D robustness harness."""
from experiments.e050_field_slow_field_basin_s2.field_slow_field_basin_s2 import run, excess, FROZEN, CONFIG_QUICK, MARGIN


def test_coupling_band_has_onset_and_grows():
    r = run(CONFIG_QUICK)
    ex = [x["excess"] for x in r["g_band"]]
    assert ex[0] <= MARGIN                       # g=0 has no excess by construction
    assert ex[-1] > MARGIN                       # strong coupling -> memory
    assert r["onset_g"] is not None


def test_excess_survives_resolution_and_seeds_and_3d():
    r = run(CONFIG_QUICK)
    assert all(x["excess"] > MARGIN for x in r["resolution"])
    assert (r["seed_mean"] - r["seed_std"]) > MARGIN
    assert r["excess_3d"] > MARGIN               # the memory survives promotion to 3D


def test_off_control_zero_excess_and_energy_bounded():
    ex0, emax = excess((28, 28), 0.0, CONFIG_QUICK["K"], FROZEN, 0)   # g=0 vs g=0 -> ~0
    assert abs(ex0) < 1e-9
    _ex, emax3 = excess((16, 16, 16), FROZEN["g_ref"], CONFIG_QUICK["K3"], FROZEN, 0)
    assert emax3 < 1e6
