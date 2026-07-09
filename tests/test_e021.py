"""Regression tests for e021 (self-reception + driven-droplet annihilation threshold)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e021_self_receiver", name))
    spec = importlib.util.spec_from_file_location("e021_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_self_receiver_reads_own_core():
    S = _load("self_receiver.py")
    r = S.simulate(quick=True)
    passed, checks = S.evaluate(r, quick=True)
    assert passed, checks
    # ring winding equals core winding for each w, and is position/radius invariant
    assert all(abs(rd["ring_winding"] - rd["w"]) < 0.1 for rd in r["reads"])
    assert r["position_invariant"] and r["radius_quantized"]


def test_vessel_alive_annihilation_threshold():
    V = _load("vessel_alive.py")
    r = V.simulate(quick=True)
    passed, checks = V.evaluate(r, quick=True)
    assert passed, checks
    # a near anti annihilates (winding->0, core heals); a far anti leaves it intact
    assert r["near_annihilates"] and r["far_survives"]
    assert abs(r["winding_under_drive"]) > 0.5 and r["core_amp_under_drive"] < 0.5


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e021_self_receiver", "results"))
    with open(os.path.join(base, "self_receiver.json")) as f:
        s = json.load(f)["result"]
    assert all(abs(rd["ring_winding"] - rd["w"]) < 0.1 for rd in s["reads"])
    with open(os.path.join(base, "vessel_alive.json")) as f:
        v = json.load(f)["result"]
    assert v["near_annihilates"] and v["far_survives"]
