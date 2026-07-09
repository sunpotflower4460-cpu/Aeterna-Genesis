"""Regression tests for e028 (topological memory: static receiver + dynamic ring)."""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e028_topological_memory", name))
    spec = importlib.util.spec_from_file_location("e028_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_memory_nonlocality_protection_capacity():
    M = _load("memory.py")
    r = M.simulate(quick=True)
    passed, checks = M.evaluate(r, quick=True)
    assert passed, checks
    # a fixed small reader recovers more bits than its own boundary dof
    assert r["max_perfect_capacity"] > r["dof"]
    # a big loop reads the sum of the enclosed bits; a between-holes loop reads ~0
    assert r["big_loop_winding"] == r["sum_bits"]
    assert abs(r["between_holes_winding"]) < 0.5


def test_memory_ccw_box_winding_single_vortex():
    """A CCW box loop around a single +1 hole reads +1 (guards the CCW convention)."""
    M = _load("memory.py")
    N = 120
    X, Y = M._grid(N)
    ph = M._make_phase([(60, 60)], [1], X, Y)
    assert abs(M._box_winding(ph, 60, 60, 30) - 1.0) < 1e-6


def test_ring_quantized_gauge_barrier():
    R = _load("ring.py")
    r = R.simulate(quick=True)
    passed, checks = R.evaluate(r, quick=True)
    assert passed, checks
    # the ring's winding is the nearest integer to Phi at every sampled flux
    assert all(abs(s["n"] - s["phi"]) <= 0.5 + 1e-6 for s in r["sweep"])
    assert r["gauge_dE"] < 1e-4
    assert r["barrier_node_E"] > 2 * r["barrier_ground_E"]


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e028_topological_memory", "results"))
    with open(os.path.join(base, "memory.json")) as f:
        m = json.load(f)["result"]
    assert m["max_perfect_capacity"] > m["dof"]
    assert m["big_loop_winding"] == m["sum_bits"]
    with open(os.path.join(base, "ring.json")) as f:
        rg = json.load(f)["result"]
    assert rg["n_max"] >= 2 and rg["gauge_dE"] < 1e-4
