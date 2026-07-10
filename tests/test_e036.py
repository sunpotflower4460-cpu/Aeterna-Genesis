"""Regression test for e036 (field adaptation: replicator-mutator / Crow-Kimura, no agents)."""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e036_field_adaptation", name))
    spec = importlib.util.spec_from_file_location("e036_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_adaptation_field_emerges():
    AD = _load("adaptation.py")
    r = AD.simulate(quick=True)
    passed, checks = AD.evaluate(r, quick=True)
    assert passed, checks
    assert r["variance_err"] < 0.02        # mutation-selection balance = sqrt(2D/k)
    assert abs(r["adapt_end"]) < 0.05      # climbs to the fitness peak
    assert r["lag_theory_err"] < 0.03      # lag load L = v/(k sigma^2)


def test_balance_variance_matches_closed_form():
    """The equilibrium variance sits on sqrt(2D/k) for several D -- never put in."""
    AD = _load("adaptation.py")
    p = dict(AD.DEFAULT)
    x, dx, dt = AD._grid(p)
    for D in [0.05, 0.1]:
        pf, _ = AD._evolve(x, dx, dt, AD._gaussian(x, dx, 0.0, 1.0), D, p["k"], p["steps"])
        mean = np.sum(x * pf) * dx
        var = np.sum((x - mean) ** 2 * pf) * dx
        assert abs(var - np.sqrt(2 * D / p["k"])) < 0.02


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e036_field_adaptation",
        "results", "adaptation.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["variance_err"] < 0.02 and abs(r["adapt_end"]) < 0.05 and r["lag_theory_err"] < 0.03
