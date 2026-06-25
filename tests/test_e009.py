"""Regression test for e009 exploratory (X1 current, X2 growth, open menu)."""

import importlib.util
import os

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e009_exploratory")


def _load(name):
    path = os.path.abspath(os.path.join(_DIR, name))
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_x1_persistent_current_quick():
    x1 = _load("x1_toroidal_current.py")
    r = x1.simulate(quick=True)
    A = r["tierA_persistent_current"]
    # Tier A anchor: quantized current persists + survives noise (no phase slip)
    assert A["n=1"]["persists"] and A["n=2"]["persists"]
    assert A["noise_n=2"]["protected"]
    assert A["n=2"]["energy_drift"] < 1e-6


def test_x2_seed_growth_quick():
    x2 = _load("x2_seed_growth.py")
    r = x2.simulate(quick=True)
    # self-replication (mitosis) and branching growth from one seed
    assert r["tierA_mitosis"]["components"] > 3
    assert r["tierA_coral"]["area_grows"]


def test_open_menu_universality_quick():
    om = _load("open_menu.py")
    u = om.open1_universality(quick=True)
    # KZ vortices emerge in a NON-GPE (relativistic) substrate => universality
    assert u["vortices_emerge"]
    assert u["power_law_negative"]
