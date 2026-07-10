"""Regression test for e034 (field cooperation: bistable reaction-diffusion front, no agents)."""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e034_field_cooperation_front", name))
    spec = importlib.util.spec_from_file_location("e034_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cooperation_front_emerges():
    CF = _load("cooperation_front.py")
    r = CF.simulate(quick=True)
    passed, checks = CF.evaluate(r, quick=True)
    assert passed, checks
    assert r["wellmixed_below_final"] < 0.1            # well-mixed sub-threshold seed collapses
    assert r["front_below_maxwell"] > 0.02             # cooperator domain invades below a=1/2
    assert r["front_above_maxwell"] < -0.02            # defect invades above a=1/2
    assert abs(r["maxwell_point"] - 0.5) < 0.03        # emergent threshold at the Maxwell point


def test_front_speed_matches_nagumo_law():
    """Front speed tracks c = sqrt(D/2)(1-2a); symmetric about a=1/2 -- never put in."""
    CF = _load("cooperation_front.py")
    p = dict(CF.DEFAULT)
    p.update({"steps": 2500})
    c_lo = CF._front_velocity(0.40, p)
    c_hi = CF._front_velocity(0.60, p)
    assert c_lo > 0 and c_hi < 0                       # sign flips across a=1/2
    assert abs(c_lo + c_hi) < 0.03                     # antisymmetric about the Maxwell point
    assert abs(c_lo - np.sqrt(p["D"] / 2) * (1 - 2 * 0.40)) < 0.03    # matches Nagumo speed


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e034_field_cooperation_front",
        "results", "cooperation_front.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["wellmixed_below_final"] < 0.1 and abs(r["maxwell_point"] - 0.5) < 0.03
    assert r["nagumo_speed_err"] < 0.03
