"""Regression test for e018 (three-arm vessel + phase-field membrane vesicle)."""

import importlib.util
import json
import os

import pytest


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e018_membrane_vesicle", name))
    spec = importlib.util.spec_from_file_location("e018_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e018_three_arm_death():
    vm = _load("vessel_membrane.py")
    r = vm.simulate(quick=True)
    assert r["alive_when_intact"]
    assert r["dies_on_cut_metabolism"]
    assert r["dies_on_cut_membrane"]
    assert r["dies_on_cut_drive"]
    assert r["critical_drive_curve_rises_with_loss"]


def test_e018_phase_field_vesicle():
    mv = _load("membrane_vesicle.py")
    r = mv.simulate(quick=True)
    assert r["vesicle_forms_when_driven"]        # bounded single droplet with a membrane
    assert r["dissolves_without_drive"]          # cut the drive -> dissolves
    assert r["drive_threshold_rises_with_leak"]  # leak up -> drive up


def test_e018_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e018_membrane_vesicle", "results"))
    for name, key in [("vessel_membrane.json", "alive_when_intact"),
                      ("membrane_vesicle.json", "vesicle_forms_when_driven")]:
        path = os.path.join(base, name)
        if not os.path.exists(path):
            pytest.skip("committed %s missing" % name)
        with open(path) as f:
            r = json.load(f)["result"]
        assert r[key]
