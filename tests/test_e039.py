"""Regression test for e039 (field differentiation: French flag morphogen + Turing, no agents)."""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e039_field_differentiation", name))
    spec = importlib.util.spec_from_file_location("e039_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_differentiation_field_emerges():
    D = _load("differentiation.py")
    r = D.simulate(quick=True)
    passed, checks = D.evaluate(r, quick=True)
    assert passed, checks
    assert all(d > 0 for d in r["domains"]) and r["french_flag_ordered"]     # 3 ordered domains
    assert r["turing_std_start"] < 0.1 and r["turing_std_end"] > 0.5         # Turing symmetry breaking


def test_morphogen_relaxes_to_monotone_gradient():
    """The morphogen relaxes to a monotone (exponential) gradient away from the source -- never put in."""
    D = _load("differentiation.py")
    p = dict(D.DEFAULT)
    p.update({"N": 60, "mor_steps": 2500})
    M = D._morphogen(p)
    col = M[:, p["N"] // 2]
    # the source is at the top rows; with periodic BC it also wraps to the bottom, so the gradient is
    # monotone DECREASING only over the descending half (rows 3 .. N/2). That descent is the French-flag
    # positional signal and is NOT put in (it emerges from diffusion+decay).
    half = col[3:p["N"] // 2]
    assert np.all(np.diff(half) <= 1e-9)                                     # monotone decreasing over the descent
    assert half[0] > half[-1]                                                # high near source, low far


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e039_field_differentiation",
        "results", "differentiation.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["french_flag_ordered"] and r["turing_std_end"] > 0.5
