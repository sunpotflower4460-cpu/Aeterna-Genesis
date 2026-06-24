"""Regression test for experiment e001.

A short ("quick") run is enough to assert the qualitative emergence: the
vortex precesses (monotonic cumulative rotation past a third of a turn),
the radius stays nearly constant, circulation is a quantized +1, and the
conservative integrator preserves energy and norm. Also checks the committed
result.json stays in the expected reference ranges.
"""

import importlib.util
import json
import os

_E001_DIR = os.path.join(
    os.path.dirname(__file__), "..", "experiments", "e001_gpe_vortex_precession"
)


def _load_run_module():
    path = os.path.abspath(os.path.join(_E001_DIR, "run.py"))
    spec = importlib.util.spec_from_file_location("e001_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e001_quick_run_emerges():
    run = _load_run_module()
    result = run.simulate({"n_imag": 120, "n_real": 4000, "sample": 50})
    assert result["radius_spread"] < 2.0
    assert 9.0 <= result["radius_mean"] <= 11.5
    assert result["rotation_monotonic"]
    assert result["cumulative_rotation_deg"] > 120.0   # clear precession
    assert result["charge"] == 1
    assert result["circulation_quantized"]
    assert result["energy_drift"] < 1e-4
    assert result["norm_drift"] < 1e-6


def test_quick_result_is_json_serializable():
    # result dicts are written to result.json -- guard against numpy scalar
    # types (np.int64/np.bool_) sneaking in and breaking json.dump.
    run = _load_run_module()
    result = run.simulate({"n_imag": 120, "n_real": 1000, "sample": 50})
    json.dumps(result)  # raises TypeError if any value is not JSON-native


def test_committed_result_json_in_range():
    path = os.path.abspath(os.path.join(_E001_DIR, "result.json"))
    if not os.path.exists(path):
        return  # not generated yet; the quick run above is the real guard
    with open(path) as f:
        result = json.load(f)
    run = _load_run_module()
    passed, checks = run.evaluate(result)
    assert passed, f"committed result.json out of range: {checks}"
