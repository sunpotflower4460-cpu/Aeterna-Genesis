"""Regression test for e014 (causal -> dimension: Myrheim-Meyer + spectral)."""

import importlib.util
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e014_causal_dimension", name))
    spec = importlib.util.spec_from_file_location("e014_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e014_denominator_two_formula():
    cd = _load("causal_dimension.py")
    # the correct (denominator-2) Myrheim-Meyer fraction is exactly 0.5 in 2D
    assert abs(cd.relation_fraction_theory(2) - 0.5) < 1e-9
    # a one-direction (denominator-4) form would give 0.25 -- guard against it
    assert cd.relation_fraction_theory(2) > 0.4


def test_e014_myrheim_meyer_recovers_dimension():
    cd = _load("causal_dimension.py")
    r = cd.simulate(quick=True)
    for row in r["rows"]:
        assert row["abs_err"] < 0.15        # d_MM recovers the true dimension
    assert abs(r["denominator2_check_r2"] - 0.5) < 1e-6


def test_e014_spectral_dimension_of_geometry():
    sp = _load("spectral.py")
    r = sp.simulate(quick=True)
    assert abs(r["grid_3d_d_s"] - 3.0) < 0.3
    assert abs(r["grid_2d_d_s"] - 2.0) < 0.3
