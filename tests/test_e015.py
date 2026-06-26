"""Regression test for e015 (vessel closure: drive-dependence + two-arm autopoiesis)."""

import importlib.util
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e015_vessel_closure", name))
    spec = importlib.util.spec_from_file_location("e015_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e015_drive_dependence_and_self_heal():
    vc = _load("vessel_closure.py")
    r = vc.simulate(quick=True)
    assert r["self_maintains"]           # driven -> self-maintain/proliferate
    assert r["death_on_cut"]             # cut drive (F->0) -> death
    assert r["self_heals"]               # excise -> regrow
    assert r["has_critical_F"]           # survival window in F


def test_e015_two_arm_autopoiesis():
    ap = _load("autopoiesis.py")
    r = ap.simulate(quick=True)
    assert r["alive_when_intact"]        # intact + driven -> coexistence
    assert r["dies_on_break_membrane"]   # cut membrane arm -> death
    assert r["dies_on_stop_metabolism"]  # cut metabolism arm -> death
    assert r["has_critical_drive"]       # critical drive S_c
