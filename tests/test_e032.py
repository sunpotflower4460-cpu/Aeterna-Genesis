"""Regression test for e032 (3D Dou-Sorkin: 2+1 area law, density-dependent coefficient) [frontier]."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e032_ds_horizon_3d", name))
    spec = importlib.util.spec_from_file_location("e032_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_area_law_holds_but_coefficient_drifts():
    H = _load("horizon_3d.py")
    r = H.simulate(quick=True)
    passed, checks = H.evaluate(r, quick=True)
    assert passed, checks
    assert all(row["r2"] > 0.85 for row in r["rows"])     # 2+1 area law (linear in cut width)
    assert r["coefficient_ratio"] > 1.3                  # coefficient drifts with density (d>2 pathology)


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e032_ds_horizon_3d",
        "results", "horizon_3d.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["area_law_all_linear"] and r["coefficient_ratio"] > 1.3
