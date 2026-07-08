"""Regression test for e020 (phase-field vesicle division: an honest negative)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e020_vesicle_division", name))
    spec = importlib.util.spec_from_file_location("e020_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e020_passive_no_spontaneous_division():
    """Passive phase-field (Allen-Cahn + Cahn-Hilliard) relaxes to a single droplet;
    no spontaneous division emerges (measured, not scripted)."""
    div = _load("division.py")
    r = div.simulate(quick=True)
    assert r["all_finite"]
    assert not r["any_spontaneous_division"]        # honest negative
    assert r["all_relax_to_single_droplet"]
    assert r["measured_no_division_passive"]


def test_e020_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e020_vesicle_division",
        "results", "division.json"))
    assert os.path.exists(path), "committed division.json missing"
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["measured_no_division_passive"]
    assert all(run["final_components"] == 1 for run in r["allen_cahn"] + r["cahn_hilliard"])
