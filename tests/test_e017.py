"""Regression test for e017 (walled RB linear stability: textbook Ra_c)."""

import importlib.util
import json
import os

import pytest


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e017_walled_convection", name))
    spec = importlib.util.spec_from_file_location("e017_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e017_critical_rayleigh_numbers():
    rb = _load("rb_linear_stability.py")
    r = rb.simulate(quick=True)
    by = {row["bc"]: row for row in r["rows"]}
    assert by["noslip"]["within_0p4pct"]        # no-slip ~ 1708 to <0.4%
    assert by["freeslip"]["within_0p4pct"]      # free-slip ~ 657.5 to <0.4%
    assert by["noslip"]["Ra_c"] > by["freeslip"]["Ra_c"]   # rigid is harder


def test_e017_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e017_walled_convection",
        "results", "rb_linear_stability.json"))
    if not os.path.exists(path):
        pytest.skip("committed rb_linear_stability.json missing")
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["both_within_0p4pct"]
