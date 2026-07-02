"""Regression test for e019 (circulation carries a particle; U_c).

The full 3D transport is expensive, so we unit-test the light pieces (velocity
field shape, centroid over spatial axes -- guarding the AxisError trap) and check
the committed result.json (CI runs coupling.py --quick separately)."""

import importlib.util
import json
import os

import numpy as np
import pytest


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e019_coupling", name))
    spec = importlib.util.spec_from_file_location("e019_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e019_centroid_uses_spatial_axes():
    """The centroid must be a sum over the 3 SPATIAL axes of the (3,L,L,L) field
    (the trap: using a component/4D axis raises AxisError or gives a wrong value)."""
    from core import hopf
    cp = _load("coupling.py")
    n, dx = hopf.hopfion_field(24, 2.0, 6.0)
    cx, cz = cp._centroid(n, dx)                   # must not raise; centred hopfion ~ origin
    assert abs(cx) < 1.0 and abs(cz) < 1.0
    ux, uz = cp._roll_velocity(24, 6.0, 5.0, 5.0, -4.0)
    assert ux.shape == (24, 24, 24) and uz.shape == (24, 24, 24)


def test_e019_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e019_coupling",
        "results", "coupling.json"))
    if not os.path.exists(path):
        pytest.skip("committed coupling.json missing (run the module to generate)")
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["centroid_moves_with_U"]
    assert r["low_U_holds_QH"]
    assert r["high_U_torn"]
    assert r["U_c"] is not None
