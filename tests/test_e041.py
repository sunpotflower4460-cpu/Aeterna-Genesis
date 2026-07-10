"""Regression test for e041 (field bottleneck: neck geometry -> founder number -> clonality)."""
import importlib.util, json, os


def _load(name):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "experiments",
                                        "e041_field_bottleneck", name))
    spec = importlib.util.spec_from_file_location("e041_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_neck_geometry_sets_clonality():
    B = _load("bottleneck.py")
    r = B.simulate(quick=True)
    passed, checks = B.evaluate(r, quick=True)
    assert passed, checks
    assert r["narrow"]["founders"] < 3 and r["narrow"]["relatedness"] > 0.5    # narrow -> ~1 founder, clonal
    assert r["wide"]["relatedness"] < 0.1 and r["wide"]["founders"] > 100      # wide -> many founders, mixed
    assert r["relatedness_monotone_in_width"]                                  # relatedness falls as neck widens


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "experiments",
                                        "e041_field_bottleneck", "results", "bottleneck.json"))
    assert os.path.exists(path)
    r = json.load(open(path))["result"]
    assert r["narrow"]["relatedness"] > 0.5 and r["wide"]["relatedness"] < 0.1
