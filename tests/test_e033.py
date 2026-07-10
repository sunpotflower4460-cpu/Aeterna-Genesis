"""Regression test for e033 (field division of labor: Cahn-Hilliard spinodal decomposition, no agents)."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e033_field_division_of_labor", name))
    spec = importlib.util.spec_from_file_location("e033_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_field_division_of_labor_emerges():
    FD = _load("field_division.py")
    r = FD.simulate(quick=True)
    passed, checks = FD.evaluate(r, quick=True)
    assert passed, checks
    assert r["op_mixed"] < 0.05           # homogeneous below the critical point (convex free energy)
    assert r["both_phases_sep"] > 0.9     # two coexisting phases above it
    assert r["binodal_err"] < 0.05        # coexistence matches the Flory-Huggins binodal


def test_cahn_hilliard_conserves_mass():
    """Cahn-Hilliard is a CONSERVED gradient flow: the clip to (0,1) must not leak mass. The field starts
    at uniform 0.5 + zero-mean noise, so the conserved mean must stay at ~0.5 through demixing -- else the
    clip (not the physics) would be moving the field (LAW.md audit 7: code must not silently drive it)."""
    FD = _load("field_division.py")
    p = dict(FD.DEFAULT)
    p.update({"L": 96, "steps": 3000})
    phi = FD._evolve(3.0, p, 0)                     # chi=3.0: strong demixing regime
    assert abs(float(phi.mean()) - 0.5) < 1e-3     # conserved mean stays at its 0.5 start


def test_flory_huggins_critical_point_and_binodal():
    """The critical point is chi_c=2 (theory binodal is a point below it, split above) -- never put in."""
    FD = _load("field_division.py")
    lo2, hi2 = FD._theory_binodal(2.0)
    assert abs(lo2 - 0.5) < 1e-6 and abs(hi2 - 0.5) < 1e-6      # no splitting at chi_c=2
    lo, hi = FD._theory_binodal(3.0)
    assert lo < 0.1 and hi > 0.9                                # strong split above the critical point
    assert abs((lo + hi) - 1.0) < 1e-9                          # symmetric binodal


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e033_field_division_of_labor",
        "results", "field_division.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["op_mixed"] < 0.05 and r["both_phases_sep"] > 0.9 and r["binodal_err"] < 0.05
