"""Regression tests for e026 (topological division accounting)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e026_vessel_division", name))
    spec = importlib.util.spec_from_file_location("e026_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_split_conserves_one_wound_one_empty():
    """(A) one +1 splits into (+1, 0); (B) two wound daughters need a shed anti, total conserved."""
    D = _load("division.py")
    r = D.simulate(quick=True)
    passed, checks = D.evaluate(r, quick=True)
    assert passed, checks
    # (A) one daughter wound, the other empty
    assert abs(r["A"]["left"]) > 0.5 and abs(r["A"]["right"]) < 0.5
    # (B) both wound; loop around both = +2; loop around all (incl shed -1) = +1 (conserved)
    assert abs(r["B"]["both_daughters"] - 2) < 0.5
    assert abs(r["B"]["all_incl_anti"] - 1) < 0.5


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e026_vessel_division",
        "results", "division.json"))
    assert os.path.exists(path), "committed division.json missing"
    with open(path) as f:
        r = json.load(f)["result"]
    assert abs(r["A"]["left"]) > 0.5 and abs(r["A"]["right"]) < 0.5
    assert abs(r["B"]["left"]) > 0.5 and abs(r["B"]["right"]) > 0.5
    assert abs(r["B"]["all_incl_anti"] - 1) < 0.5
