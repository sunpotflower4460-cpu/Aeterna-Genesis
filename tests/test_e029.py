"""Regression tests for e029 (frontier: endogenous demand + the major transition).

Both stages are FRONTIER agent models with intrinsic run-to-run variance, so the gates are on ENSEMBLE
statistics; the tests re-check those ensemble gates on the quick config and the committed JSONs.
"""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e029_openended_frontier", name))
    spec = importlib.util.spec_from_file_location("e029_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_coevolution_endogenous_demand_removes_plateau():
    C = _load("coevolution.py")
    r = C.simulate(quick=True)
    passed, checks = C.evaluate(r, quick=True)
    assert passed, checks
    # static plateaus (flat), coevolution keeps climbing, demand rose endogenously
    assert abs(r["median_static_late_slope"]) < 0.02
    assert r["median_coev_late_slope"] > 0.01
    assert r["median_coev_pspread"] > 2.0 * r["median_static_pspread"]


def test_major_transition_group_reproduction_rescues():
    M = _load("major_transition.py")
    r = M.simulate(quick=True)
    passed, checks = M.evaluate(r, quick=True)
    assert passed, checks
    assert r["individual_collapses_all_b"] and r["group_rescues_all_b"]
    assert r["coop_tight_bottleneck"] > r["coop_loose_bottleneck"]


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e029_openended_frontier", "results"))
    with open(os.path.join(base, "coevolution.json")) as f:
        c = json.load(f)["result"]
    assert c["median_coev_late_slope"] > 0.01 and abs(c["median_static_late_slope"]) < 0.02
    assert c["median_coev_pspread"] > 2.0 * c["median_static_pspread"]
    with open(os.path.join(base, "major_transition.json")) as f:
        m = json.load(f)["result"]
    assert m["individual_collapses_all_b"] and m["group_rescues_all_b"]
