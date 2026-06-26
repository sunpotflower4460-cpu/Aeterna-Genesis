"""Regression test for e013 (vessel+content: circulation load-bearing inside)."""

import importlib.util
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e013_vessel_content", name))
    spec = importlib.util.spec_from_file_location("e013_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e013_dead_core_and_inner_vs_Pe():
    run = _load("run.py")
    r = run.simulate(quick=True)
    assert r["dead_core_no_flow"]            # no flow -> dead core
    assert r["inner_b_monotone_in_Pe"]       # inner biomass rises with Pe
    assert r["inner_b_rises_with_flow"]
    assert r["total_b_rel_spread"] < 0.25    # total nearly flat (load-bearing internal)


def test_e013_self_organized_convection_feeds_interior():
    rb = _load("rayleigh_benard.py")
    r = rb.simulate(quick=True)
    assert r["convection_self_organizes"]    # KE jumps above Ra_c (flow not put in)
    assert r["interior_fed_by_convection"]   # self-organized flow feeds interior


def test_e013_committed_result_sane():
    import json
    import pytest
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e013_vessel_content", "result.json"))
    if not os.path.exists(path):
        pytest.skip("committed result.json missing (run the module to generate)")
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["dead_core_no_flow"]
    assert r["inner_b_monotone_in_Pe"]
