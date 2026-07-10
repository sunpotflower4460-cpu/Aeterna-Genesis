"""Regression test for e037 (ecological public goods: persistent cooperation in a pure PDE, no agents)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e037_ecological_pgg", name))
    spec = importlib.util.spec_from_file_location("e037_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ecological_cooperation_persists_vs_classical():
    EP = _load("ecological_pgg.py")
    r = EP.simulate(quick=True)
    passed, checks = EP.evaluate(r, quick=True)
    assert passed, checks
    assert r["eco_spatial"]["coop_fraction"] > 0.3        # ecological persists in the pure PDE
    assert r["classical_spatial"]["coop_fraction"] < 0.1  # classical constant-cost collapses
    assert r["eco_wellmixed"]["coop_fraction"] > 0.3      # mechanism is the feedback, not space


def test_ecological_payoff_favours_cooperators_at_low_density():
    """P_C - P_D = c*(r*A(rho) - 1) > 0 at low density -- the ecological mechanism, never put in as a result."""
    EP = _load("ecological_pgg.py")
    import numpy as np
    p = dict(EP.DEFAULT)
    lo = np.array([[0.05]]); hi = np.array([[0.95]])       # low vs high total density (all cooperators)
    pc_lo, pd_lo = EP._payoff(lo, np.zeros_like(lo), p, ecological=True)
    pc_hi, pd_hi = EP._payoff(hi, np.zeros_like(hi), p, ecological=True)
    adv_lo = float((pc_lo - pd_lo).item())
    adv_hi = float((pc_hi - pd_hi).item())
    assert adv_lo > 0            # cooperators favoured at low density (r*A(rho)-1 > 0)
    assert adv_lo > adv_hi       # the advantage shrinks as density rises


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e037_ecological_pgg",
        "results", "ecological_pgg.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["eco_spatial"]["coop_fraction"] > 0.3
    assert r["classical_spatial"]["coop_fraction"] < 0.1
    assert r["eco_wellmixed"]["coop_fraction"] > 0.3
