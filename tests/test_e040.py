"""Regression test for e040 (field RPS cooperation: cyclic-dominance spiral waves, no agents)."""
import importlib.util, json, os


def _load(name):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "experiments",
                                        "e040_field_rps_cooperation", name))
    spec = importlib.util.spec_from_file_location("e040_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_rps_spirals_sustain_cooperation():
    R = _load("rps_cooperation.py")
    r = R.simulate(quick=True)
    passed, checks = R.evaluate(r, quick=True)
    assert passed, checks
    assert r["spatial_all_present"]                       # all three (incl coop) persist in spirals
    assert r["spatial"]["coop_std"] > 0.03                # spatial spiral pattern
    assert r["wellmixed_dominant"] > 0.8                  # well-mixed collapses to one type


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "experiments",
                                        "e040_field_rps_cooperation", "results", "rps_cooperation.json"))
    assert os.path.exists(path)
    r = json.load(open(path))["result"]
    assert r["spatial_all_present"] and r["wellmixed_dominant"] > 0.8
