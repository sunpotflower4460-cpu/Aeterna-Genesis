"""Regression test for e016 (Hopf basin: size law + Q_H=2).

The full stabilized flow is expensive (3D), so we unit-test the light pieces
(the sqrt fit and the Q_H=2 field construction at a small grid) and check the
committed result.json, rather than re-running the heavy sweep here (CI runs
hopf_basin.py --quick separately)."""

import importlib.util
import json
import os

import numpy as np
import pytest


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e016_hopf_basin", name))
    spec = importlib.util.spec_from_file_location("e016_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e016_sqrt_fit_recovers_slope():
    hb = _load("hopf_basin.py")
    c4 = [9.0, 16.0, 25.0, 36.0]
    sizes = [0.8 * np.sqrt(c) for c in c4]        # perfect size = 0.8*sqrt(c4)
    k, r2, cv, _ = hb._fit_sqrt(c4, sizes)
    assert abs(k - 0.8) < 1e-6
    assert r2 > 0.999
    assert cv < 1e-6


def test_e016_qh2_field_has_charge_two():
    from core import hopf
    hb = _load("hopf_basin.py")
    n, dx = hb.qh_field_mn(28, 2.4, 7.0, m=1, n=2)   # small grid, fast
    q = hopf.hopf_charge(n, dx)
    assert abs(abs(q) - 2.0) < 0.25                  # |Q_H| ~ 2 (doubled winding)


def test_e016_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e016_hopf_basin",
        "results", "hopf_basin.json"))
    if not os.path.exists(path):
        pytest.skip("committed hopf_basin.json missing (run the module to generate)")
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["law_fit_good"]
    assert r["size_cv"] < 0.05 and r["fit_R2"] > 0.90   # CV<5% is the tightness measure
    assert r["qh2_held"]
    assert r["all_held_monotone"]


def test_e016_arrested_newton_v2_smoke():
    """Exercise the v2 code paths (import + accel flow + _law_at_L + _basin) on a
    tiny fast config, so a broken arrested_newton_v2.py fails CI even though the
    heavy full run is not in CI (Codex: check the code path, not just the JSON)."""
    an = _load("arrested_newton_v2.py")
    p = {"box": 6.0, "c2": 1.0, "kappa": 40.0, "dt": 8e-3, "start_frac": 0.9,
         "n_steps": 3, "c4_list": [9.0, 12.0], "momentum": 0.85,
         "basin_L": 20, "basin_c4": 9.0, "basin_mults": [1.0, 1.5]}
    Q, s, mono = an.accel_converge(20, p["box"], 9.0, 2.0, 3, p["kappa"], p["dt"], p["momentum"])
    assert np.isfinite(Q) and s >= 0.0 and isinstance(mono, bool)
    row = an._law_at_L(p, 20)
    assert set(["L", "n_held", "all_c4_held", "CV", "energy_monotone"]).issubset(row)
    b = an._basin(p, accel=True)
    assert "all_held_energy_monotone" in b and "width" in b


def test_e016_arrested_newton_v2_committed_sane():
    """H001 v2: matched-protocol L-series shows the catastrophic L=56 does not
    reproduce (all L CV<5%); the residual is a mild monotone trend, honestly flagged."""
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e016_hopf_basin",
        "results", "arrested_newton_v2.json"))
    assert os.path.exists(path), "committed arrested_newton_v2.json missing"   # hard fail (Codex/CodeRabbit)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["all_L_tight(CV<5%)"]                 # size law holds at every L (all c4 held)
    assert r["L56_sampled"] and r["catastrophic_L56_not_reproduced"]   # from the L=56 row itself
    # every L-series CV is genuinely < 5% AND every matched c4 held
    assert all(row["CV"] < 0.05 and row["all_c4_held"] for row in r["l_series"])
