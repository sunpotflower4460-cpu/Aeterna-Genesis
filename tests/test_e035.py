"""Regression test for e035 (field Red Queen: predator-prey Hopf bifurcation, no agents)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e035_field_red_queen", name))
    spec = importlib.util.spec_from_file_location("e035_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_red_queen_hopf_emerges():
    RQ = _load("red_queen.py")
    r = RQ.simulate(quick=True)
    passed, checks = RQ.evaluate(r, quick=True)
    assert passed, checks
    assert r["amp_plateau"] < 0.05        # static plateau below the Hopf point
    assert r["amp_cycle"] > 0.3           # sustained endogenous oscillation above it
    assert r["onset_err"] < 0.1           # onset matches the analytic Hopf point


def test_onset_tracks_hopf_when_parameters_shift():
    """Move the mortality m -> the Hopf point moves, and the measured onset moves with it (not put in)."""
    RQ = _load("red_queen.py")
    p_lo = dict(RQ.DEFAULT); p_lo.update({"m": 0.35})
    p_hi = dict(RQ.DEFAULT); p_hi.update({"m": 0.40})
    hopf_lo = RQ._analytic_hopf(p_lo)
    hopf_hi = RQ._analytic_hopf(p_hi)
    assert hopf_lo < hopf_hi              # lowering mortality lowers the Hopf enrichment threshold
    # below each Hopf point the fixed point is stable (trace<0), above it unstable (trace>0)
    assert RQ._jac_trace(hopf_hi - 0.2, p_hi) < 0 < RQ._jac_trace(hopf_hi + 0.2, p_hi)


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e035_field_red_queen",
        "results", "red_queen.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["amp_plateau"] < 0.05 and r["amp_cycle"] > 0.3 and r["onset_err"] < 0.1
