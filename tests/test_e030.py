"""Regression test for e030 (division of labor from convex fitness returns) [frontier]."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e030_division_of_labor", name))
    spec = importlib.util.spec_from_file_location("e030_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_convex_returns_drive_division_of_labor():
    D = _load("division_of_labor.py")
    r = D.simulate(quick=True)
    passed, checks = D.evaluate(r, quick=True)
    assert passed, checks
    assert r["spec_convex"] > 0.6
    assert r["spec_convex"] > 1.5 * r["spec_concave"]
    assert r["both_roles_convex"] > 0.9


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e030_division_of_labor",
        "results", "division_of_labor.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["spec_convex"] > 0.6 and r["both_roles_convex"] > 0.9
    assert r["monotone_in_convexity"]
