"""Regression test for e008 (co-emergence: KZ matter, arrow, echo)."""

import importlib.util
import json
import os

import numpy as np

from core import field, vortex
from core.fft import k_squared

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e008_coemergence")


def _load():
    path = os.path.abspath(os.path.join(_DIR, "run.py"))
    spec = importlib.util.spec_from_file_location("e008_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_damped_step_condenses_from_noise():
    # The damped GPE must drive white noise to a condensate (rho -> mu/g ~ 1).
    L = 96
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(0)
    psi = 0.05 * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    for _ in range(600):
        psi = field.step_damped_2d(psi, V, k2, 1.0, 1.0, 0.05, 0.4)
    assert np.median(np.abs(psi) ** 2) > 0.7      # condensed near mu/g = 1


def test_count_defects_gates_on_density():
    # A smooth vortex-free condensate must register ~0 defects (no sound cores).
    L = 64
    x, y = field.index_grid(L)
    psi = np.sqrt(np.maximum(0.0, 1.0)) * np.ones((L, L), complex)
    n, net = vortex.count_defects(psi)
    assert n == 0


def test_e008_quick_kz_and_echo():
    run = _load()
    result = run.simulate(quick=True)
    m, t = result["matter_kz"], result["time_arrow"]
    # KZ power law: negative slope -> b in a physical band, clean log-log
    assert 0.1 < m["kz_exponent_b"] < 1.0
    assert m["kz_loglog_r2"] > 0.9
    assert m["net_winding_absmean"] < 20            # balanced +/-
    assert m["circulation_quantized"]
    # arrow + echo
    assert t["coarsening"]["spacing_grows"]
    assert t["echo_fidelity"] > 0.99                # reversible law


def test_e008_committed_result_sane():
    path = os.path.abspath(os.path.join(_DIR, "result.json"))
    if not os.path.exists(path):
        return
    with open(path) as f:
        result = json.load(f)
    run = _load()
    ok, checks = run.evaluate(result)
    assert ok, checks
