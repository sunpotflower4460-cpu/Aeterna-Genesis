"""Regression test for e045 (field endogenous: NEGATIVE result -- niche construction does not beat neutral)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e045_field_endogenous", name))
    spec = importlib.util.spec_from_file_location("e045_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_endogenous_route_is_a_robust_negative():
    E = _load("endogenous.py")
    r = E.simulate(quick=True)
    passed, checks = E.evaluate(r, quick=True)
    assert passed, checks
    assert r["endogenous"]["occupied"] > 0.15 and r["neutral"]["occupied"] > 0.15  # fair comparison
    assert r["local_var_excess"] <= 0.001                     # NEGATIVE: no diversity gain over neutral
    assert r["strong_penalty_occupied"] < 0.02                # NEGATIVE: strong penalty kills the field


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e045_field_endogenous",
        "results", "endogenous.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["local_var_excess"] <= 0.001 and r["strong_penalty_occupied"] < 0.02
