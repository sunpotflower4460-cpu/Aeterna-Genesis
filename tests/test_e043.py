"""Regression test for e043 (field universe: division+inheritance+mutation+selection+adaptation+differentiation)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e043_field_universe", name))
    spec = importlib.util.spec_from_file_location("e043_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_differentiated_body_self_organizes():
    U = _load("universe.py")
    r = U.simulate(quick=True)
    passed, checks = U.evaluate(r, quick=True)
    assert passed, checks
    assert r["occupied"] > 0.25                                # division fills the field
    assert r["corr_with_optimum"] > 0.6                        # cells adapt to the local optimum
    assert r["left"] < r["mid"] < r["right"]                   # ordered spatial trait domains
    assert r["domain_contrast"] > 0.3


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e043_field_universe",
        "results", "universe.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["corr_with_optimum"] > 0.6 and r["domain_contrast"] > 0.3
