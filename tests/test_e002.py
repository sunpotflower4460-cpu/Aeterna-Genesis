"""Regression test for experiment e002 (two-vortex interaction).

A short ("quick") run is enough to assert the qualitative emergence: same-sign
vortices co-rotate (cumulative rotation grows, no net translation) while an
opposite-sign pair translates (centroid drifts, rotation ~ 0). Both conserve
energy/norm and keep quantized circulation. Also checks the committed
result.json stays in the expected reference ranges.
"""

import importlib.util
import json
import os

_E002_DIR = os.path.join(
    os.path.dirname(__file__), "..", "experiments", "e002_gpe_two_vortex"
)


def _load_run_module():
    path = os.path.abspath(os.path.join(_E002_DIR, "run.py"))
    spec = importlib.util.spec_from_file_location("e002_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_e002_quick_run_emerges():
    run = _load_run_module()
    result = run.simulate(quick=True)
    ss, op = result["same_sign"], result["opposite_sign"]

    # same-sign: co-rotation, fixed separation, no translation
    assert ss["rotation_monotonic"]
    assert ss["rotation_final_deg"] > 90.0
    assert ss["centroid_drift_max"] < 2.5
    assert ss["charge_set"] == [1]
    assert ss["circulation_quantized"]
    assert ss["energy_drift"] < 1e-4 and ss["norm_drift"] < 1e-6

    # opposite-sign: translation, no rotation
    assert abs(op["rotation_final_deg"]) < 40.0
    assert op["centroid_drift_final"] > 6.0
    assert op["charge_set"] == [-1, 1]
    assert op["circulation_quantized"]
    assert op["energy_drift"] < 1e-4 and op["norm_drift"] < 1e-6


def test_e002_result_is_json_serializable():
    run = _load_run_module()
    result = run.simulate(quick=True)
    json.dumps(result)


def test_committed_result_json_in_range():
    path = os.path.abspath(os.path.join(_E002_DIR, "result.json"))
    if not os.path.exists(path):
        return
    with open(path) as f:
        result = json.load(f)
    run = _load_run_module()
    passed, checks = run.evaluate(result)
    assert passed, f"committed result.json out of range: {checks}"
