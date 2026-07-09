"""Regression tests for e027 (evolution, rising complexity, major transition)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e027_evolution_transition", name))
    spec = importlib.util.spec_from_file_location("e027_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_evolution_mutation_enables_adaptation():
    E = _load("evolution.py")
    r = E.simulate(quick=True)
    passed, checks = E.evaluate(r, quick=True)
    assert passed, checks
    assert abs(r["mean_on"] - 1.5) < 0.3 and abs(r["mean_off"]) < 0.1


def test_openended_demand_raises_complexity():
    O = _load("openended.py")
    r = O.simulate(quick=True)
    passed, checks = O.evaluate(r, quick=True)
    assert passed, checks
    assert r["len_rich"] > r["len_simple"] + 2


def test_transition_spatial_cooperation_vs_wellmixed():
    T = _load("transition.py")
    r = T.simulate(quick=True)
    passed, checks = T.evaluate(r, quick=True)
    assert passed, checks
    assert r["coop_wellmixed"] < 0.1 and r["coop_spatial"] > 0.2


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e027_evolution_transition", "results"))
    with open(os.path.join(base, "evolution.json")) as f:
        e = json.load(f)["result"]
    assert abs(e["mean_on"] - 1.5) < 0.3 and abs(e["mean_off"]) < 0.1
    with open(os.path.join(base, "openended.json")) as f:
        o = json.load(f)["result"]
    assert o["len_rich"] > o["len_simple"] + 2
    with open(os.path.join(base, "transition.json")) as f:
        t = json.load(f)["result"]
    assert t["coop_wellmixed"] < 0.1 and t["coop_spatial"] > 0.2 and t["assortment"] > 0.1
