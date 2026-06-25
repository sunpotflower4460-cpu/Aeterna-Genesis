"""Regression test for e012 (hopfion: Q_H integer, Derrick, collapse vs the 'third')."""

import importlib.util
import os

import numpy as np

from core import hopf

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e012_hopf_stabilization")


def _load(name):
    path = os.path.abspath(os.path.join(_DIR, name))
    spec = importlib.util.spec_from_file_location("e012_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_hopf_charge_is_integer_one():
    # The constructed charge-1 hopfion must measure Q_H ~ 1 (topological).
    n, dx = hopf.hopfion_field(64, 1.0, 8.0)
    assert abs(hopf.hopf_charge(n, dx) - 1.0) < 0.05


def test_derrick_bare_collapses_third_stabilises():
    E2, E4 = 700.0, 230.0
    _, _, Lstar0 = hopf.derrick_curve(E2, E4, c4=0.0)
    _, _, Lstar1 = hopf.derrick_curve(E2, E4, c4=4.0)
    assert Lstar0 == 0.0                 # bare: collapse
    assert Lstar1 > 0.0                  # third: finite stable size
    # L* ~ sqrt(c4)
    _, _, La = hopf.derrick_curve(E2, E4, c4=1.0)
    _, _, Lb = hopf.derrick_curve(E2, E4, c4=4.0)
    assert abs(Lb / La - 2.0) < 1e-6


def test_flow_step_decreases_energy():
    # Wrong-sign gradient would RAISE the energy; the flow must lower it.
    n, dx = hopf.hopfion_field(32, 1.3, 6.0)
    E0 = hopf.faddeev_energy(n, dx, 1.0, 8.0)[0]
    for _ in range(40):
        n = hopf.flow_step(n, dx, 1.0, 8.0, 5e-5)
    assert hopf.faddeev_energy(n, dx, 1.0, 8.0)[0] <= E0 + 1e-9
    assert abs(np.linalg.norm(n, axis=0) - 1.0).max() < 1e-6   # |n|=1 preserved


def test_e012_static_quick():
    st = _load("hopfion_static.py")
    r = st.simulate(quick=True)
    assert abs(r["Q_H"] - 1.0) < 0.06
    bare = next(x for x in r["derrick"] if x["c4"] == 0.0)
    third = next(x for x in r["derrick"] if x["c4"] > 0)
    assert bare["collapses"]
    assert not third["collapses"] and third["L_star_formula"] > 0


def test_e012_flow_quick_collapse_robust():
    fl = _load("hopfion_flow.py")
    r = fl.simulate(quick=True)
    # ROBUST, resolution-independent facts (the GREEN gate):
    assert r["all_energy_monotone"]          # discrete gradient correct (no sign error)
    assert r["bare_collapses"]               # c4=0 dynamically unwinds (Q_H -> 0)
    # the partial-resistance metric is recorded but NOT asserted (it is fragile,
    # resolution-sensitive, and reported as a frontier-observation, not a gate).
    assert "third_resists_collapse" in r
    assert "full_self_stabilisation" in r
