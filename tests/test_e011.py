"""Regression test for e011 (defect chemistry: binding laws + finite-T dissociation)."""

import importlib.util
import os

import numpy as np

from core import field
from core.fft import k_squared

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e011_defect_chemistry")


def _load(name):
    path = os.path.abspath(os.path.join(_DIR, name))
    spec = importlib.util.spec_from_file_location("e011_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sgpe_noise_scales_with_T():
    # The stochastic kick variance must rise with T (fluctuation-dissipation):
    # one step on a uniform field, T>0 spreads the density more than T=0.
    L = 48
    k2 = k_squared(L)
    V = np.zeros((L, L))
    base = np.ones((L, L), complex)
    cold = field.step_sgpe_2d(base.copy(), V, k2, 1.0, 1.0, 0.02, 0.3, 0.0,
                              np.random.default_rng(0))
    hot = field.step_sgpe_2d(base.copy(), V, k2, 1.0, 1.0, 0.02, 0.3, 0.5,
                             np.random.default_rng(0))
    assert np.std(np.abs(hot)) > np.std(np.abs(cold))


def test_e011_pair_binding_laws():
    pb = _load("x_pair_binding.py")
    r = pb.simulate(quick=True)
    # +/- dipole: v*d constant; ++ pair: w*d^2 ~ const (point-vortex 2)
    assert r["v_times_d_cv"] < 0.15
    assert r["omega_d2_cv"] < 0.15
    # selectivity: +/- barely rotates, ++ barely drifts
    assert r["dipole_rotation_small"] < 0.01
    assert r["corotation_drift_small"] < 8.0


def test_e011_finite_T_dissociation():
    fT = _load("finite_T_dissociation.py")
    r = fT.simulate(quick=True)
    # lifetime falls with temperature (thermal dissociation)
    assert r["lifetime_vs_T_slope"] < 0
    assert r["monotone_decreasing"]
    assert r["lifetime_drop_frac"] >= 0.10


def test_e011_committed_results_sane():
    import json
    import pytest
    for name, key, lo in [("pair_binding.json", "omega_d2_mean", 1.0)]:
        path = os.path.abspath(os.path.join(_DIR, "results", name))
        if not os.path.exists(path):
            pytest.skip("committed artifact %s missing (run the module to generate)" % name)
        with open(path) as f:
            r = json.load(f)["result"]
        assert r[key] > lo
