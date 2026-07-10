"""Regression test for e038 (field objtrack: continuous-trait evolution via object tracking, no agents)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e038_field_objtrack", name))
    spec = importlib.util.spec_from_file_location("e038_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_de_novo_climb_in_field():
    O = _load("objtrack.py")
    r = O.simulate(quick=True)
    passed, checks = O.evaluate(r, quick=True)
    assert passed, checks
    assert r["trait_start"] < 0.35 and r["trait_end"] > 0.6    # climbs from a low seed, no standing variation
    assert r["occupied_bins"] >= 4                             # trait stays continuous
    assert r["moving_optimum_lag"] < 0.35                      # tracks a moving optimum


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e038_field_objtrack",
        "results", "objtrack.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["trait_end"] > 0.6 and r["occupied_bins"] >= 4 and r["moving_optimum_lag"] < 0.35
