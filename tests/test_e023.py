"""Regression tests for e023 (causal action: order->time, directed vs undirected)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e023_causal_action", name))
    spec = importlib.util.spec_from_file_location("e023_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_order_recovers_time_and_finite_dimension():
    O = _load("order_time.py")
    r = O.simulate(quick=True)
    passed, checks = O.evaluate(r, quick=True)
    assert passed, checks
    assert r["rank_time_spearman"] > 0.8
    assert all(abs(dd["measured"] - dd["d"]) < 0.3 for dd in r["dimensions"])


def test_directed_vs_undirected_contrast():
    D = _load("directed_vs_undirected.py")
    r = D.simulate(quick=True)
    passed, checks = D.evaluate(r, quick=True)
    assert passed, checks
    # directed: finite dimension; undirected: small-world (reaches ~all N in 2 hops) with cycles
    assert abs(r["directed_dimension"] - 2.0) < 0.3
    assert r["undirected_reach_2hops_frac"] > 0.9
    assert r["undirected_triangles"] > 0


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e023_causal_action", "results"))
    with open(os.path.join(base, "order_time.json")) as f:
        o = json.load(f)["result"]
    assert o["rank_time_spearman"] > 0.8 and o["dimension_finite"]
    with open(os.path.join(base, "directed_vs_undirected.json")) as f:
        d = json.load(f)["result"]
    assert d["undirected_reach_2hops_frac"] > 0.9 and d["undirected_triangles"] > 0
