"""Regression test for e044 (field unification: cooperation joins the one field via a local public good)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e044_field_unification", name))
    spec = importlib.util.spec_from_file_location("e044_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cooperation_persists_via_local_good_vs_control():
    U = _load("unification.py")
    r = U.simulate(quick=True)
    passed, checks = U.evaluate(r, quick=True)
    assert passed, checks
    assert r["coop_with_good"] > 0.5                           # cooperation persists with the local good
    assert r["coop_advantage"] > 0.15                          # no-benefit control collapses (contrast)
    assert r["coop_with_good"] > r["coop_control_no_benefit"]
    assert r["occupied"] > 0.25 and r["corr_with_optimum"] > 0.6   # body still adapts


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e044_field_unification",
        "results", "unification.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["coop_with_good"] > 0.5 and r["coop_advantage"] > 0.15
