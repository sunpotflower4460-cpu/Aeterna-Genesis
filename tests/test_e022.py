"""Regression tests for e022 (AB gap reception + Dou-Sorkin horizon ledger)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e022_horizon_ledger", name))
    spec = importlib.util.spec_from_file_location("e022_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ab_gap_passes_one_number():
    A = _load("ab_gap.py")
    r = A.simulate(quick=True)
    passed, checks = A.evaluate(r, quick=True)
    assert passed, checks
    assert r["gauge_dE"] < 1e-9 and r["period_dE"] < 1e-9 and r["density_std"] < 1e-9


def test_ledger_ds_curve_and_horizon_profile():
    L = _load("ledger.py")
    r = L.simulate(quick=True)
    passed, checks = L.evaluate(r, quick=True)
    assert passed, checks
    # the ledger reads only the horizon-line profile: spot == ridge, both differ from flat
    assert abs(r["ledger_spot_on"] - r["ledger_ridge"]) < 0.1
    assert abs(r["ledger_spot_on"] - r["ledger_flat"]) > 0.1
    # density-independence: the count at beta=1 is stable across densities
    assert r["density_spread"] < 0.2


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e022_horizon_ledger", "results"))
    with open(os.path.join(base, "ab_gap.json")) as f:
        a = json.load(f)["result"]
    assert a["gauge_dE"] < 1e-9 and a["density_std"] < 1e-9
    with open(os.path.join(base, "ledger.json")) as f:
        l = json.load(f)["result"]
    assert abs(l["ledger_spot_on"] - l["ledger_ridge"]) < 0.1
    assert l["density_spread"] < 0.2
