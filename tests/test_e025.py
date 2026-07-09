"""Regression tests for e025 (the living vessel: three organs, two deaths, closure).

The full CGL sweeps live in the modules' simulate(); here we run one SHORT field
scenario to guard the traps (fuel cut collapses the bulk; closure couples winding
loss to bulk collapse) and check the committed JSONs.
"""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e025_vessel_life", name))
    spec = importlib.util.spec_from_file_location("e025_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_complete_fuel_cut_collapses_bulk_winding_held():
    """Short run: fueled bulk stays high with winding +1; a fuel cut collapses the bulk."""
    C = _load("complete.py")
    p = dict(C.DEFAULT)
    p.update({"T": 70.0, "Nr": 250, "fuel_cut": 35.0, "event_t": 24.0})
    rng = np.random.default_rng(0)
    b_live, w_live, _ = C.run(p, rng)
    b_fuel, w_fuel, _ = C.run(p, rng, fuel_cut=p["fuel_cut"])
    assert b_live > 0.5 and abs(w_live) > 0.5      # living: bulk + identity
    assert b_fuel < 0.2                            # metabolic collapse
    assert abs(w_fuel) > 0.5                       # winding held until collapse


def test_autopoietic_closure_couples_winding_loss_to_bulk():
    """The decisive trap: an anti-vortex collapses the bulk ONLY under closure."""
    A = _load("autopoietic.py")
    p = dict(A.DEFAULT)
    p.update({"T": 80.0, "Nr": 250, "event_t": 26.0})
    rng = np.random.default_rng(0)
    b_open, _, _ = A.run(p, rng, anti=True, closure=False)
    b_closed, _, _ = A.run(p, rng, anti=True, closure=True)
    assert b_open > 0.5           # without closure the body lives on
    assert b_closed < 0.2         # with closure, losing the winding collapses the bulk


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e025_vessel_life", "results"))
    with open(os.path.join(base, "complete.json")) as f:
        c = json.load(f)["result"]
    assert c["living"]["bulk"] > 0.5 and abs(c["living"]["winding"]) > 0.5
    assert c["fuel_cut"]["bulk"] < 0.2
    assert abs(c["anti"]["winding"]) < 0.5 and c["anti"]["bulk"] > 0.5
    with open(os.path.join(base, "autopoietic.json")) as f:
        a = json.load(f)["result"]
    assert a["anti_open"]["bulk"] > 0.5 and a["anti_closed"]["bulk"] < 0.2
