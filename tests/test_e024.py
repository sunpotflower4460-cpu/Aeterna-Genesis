"""Regression tests for e024 (vessel engine: ratchet -> motor -> vessel motor).

The heavy Langevin sweeps live in the modules' simulate(); here we unit-test the
light, fast invariants that guard the traps (CCW-free physical gates, the
smoothed-net-rotation death, the three-phase rotation) and the committed JSONs.
"""

import importlib.util
import json
import os

import numpy as np


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e024_vessel_engine", name))
    spec = importlib.util.spec_from_file_location("e024_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ratchet_asymmetric_rectifies_symmetric_null():
    """The trap: an asymmetric potential rectifies symmetric rocking; a symmetric one does not."""
    R = _load("ratchet.py")
    p = dict(R.DEFAULT)
    p.update({"Np": 800, "T": 60.0})
    rng = np.random.default_rng(0)
    rect_ratchet = R._rectification(4.5, 1.0, p, rng)
    rect_symmetric = R._rectification(4.5, 0.0, p, rng)
    assert rect_ratchet > 0.3            # asym=1 clearly rectifies (~+0.6)
    assert abs(rect_symmetric) < 0.05    # asym=0 gives no net current


def test_motor_three_is_minimum_rotation():
    """Fast, deterministic: field rotates (ripple<0.05) iff N>=3; triplen = 3,6,9."""
    M = _load("motor.py")
    r = M.simulate(quick=True)
    assert r["three_is_min"]
    assert r["n3_balanced"]
    assert r["triplen_are_369"]
    # a rotor in the rotating field self-spins; the pulsing field only wobbles
    assert r["rev_three_phase"] > 5.0 and abs(r["rev_single_phase"]) < 0.5


def test_vessel_dies_on_fuel_cutoff():
    """The trap: smoothed net rotation must let the vessel actually die when fuel is cut."""
    V = _load("vessel_motor.py")
    p = dict(V.DEFAULT)
    p.update({"Np": 350, "T": 110.0, "fuel_cut": 55.0})
    rng = np.random.default_rng(0)
    _, _, psi_fueled, _ = V.run(5.0, p, rng, vessel=True)
    _, _, psi_cut, _ = V.run(5.0, p, rng, vessel=True, fuel_cut=p["fuel_cut"])
    assert psi_fueled > 0.5
    assert psi_cut < 0.2
    # direction is set by the fuel sign
    assert V.run(-5.0, p, rng)[0] < -0.1


def test_committed_results_sane():
    base = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e024_vessel_engine", "results"))
    for name, gate_keys in [
        ("ratchet.json", ["rect_ratchet", "rect_symmetric"]),
        ("motor.json", ["ripple", "rev_three_phase"]),
        ("vessel_motor.json", ["psi_fueled", "psi_cut"]),
    ]:
        path = os.path.join(base, name)
        assert os.path.exists(path), "committed %s missing" % name
        with open(path) as f:
            r = json.load(f)["result"]
        for k in gate_keys:
            assert k in r
    # spot-check the committed gate values reproduce the sandbox canon
    with open(os.path.join(base, "vessel_motor.json")) as f:
        vm = json.load(f)["result"]
    assert vm["psi_fueled"] > 0.5 and vm["psi_cut"] < 0.2
    assert vm["rate_plus5"] > 0.1 and vm["rate_minus5"] < -0.1
