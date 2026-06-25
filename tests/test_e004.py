"""Regression test for e004 (octave hierarchy / folding / holography).

Checks the MEASURED signatures are present and stable. These are graph/spiral
facts about hand-built structures; they do NOT certify GREEN (the honest 7-audit
verdict is YELLOW -- see AUDIT.md). The test guards the numbers, not the claim.
"""

import importlib.util
import json
import os

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e004_octave_holography")


def _load():
    path = os.path.abspath(os.path.join(_DIR, "run.py"))
    spec = importlib.util.spec_from_file_location("e004_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_part_a_hierarchy_is_hyperbolic_and_method_discriminates():
    run = _load()
    a = run.part_a(256, [128, 256, 512])
    # the hierarchy classifies as hyperbolic ...
    assert a["r2_ball_exponential"] > a["r2_ball_power"]      # exp beats power
    assert a["dimension_slope"] < 0.3                         # 1/d_eff ~ 0
    # ... AND the SAME method classifies a known-flat lattice as flat,
    # so the classification is a real discriminator, not a fit artifact.
    assert a["control_flat_power_wins"]                       # flat -> power
    assert a["control_flat_dimension_slope"] > 0.4            # flat -> 1/d ~ 0.5
    assert a["method_discriminates"]
    assert a["radial_increases_with_octave"]                  # (tautological)


def test_power_of_two_required():
    run = _load()
    import pytest
    with pytest.raises(ValueError):
        run.build_octave_hierarchy(100)                       # not a power of 2


def test_part_b_spiral_closes_then_progresses():
    run = _load()
    b = run.part_b(32, eps=0.02, turns=6)
    assert b["closes_when_symmetric"]                         # eps=0 -> circle
    assert b["progresses_when_asymmetric"]                    # eps>0 -> spiral
    # slope of log-radius equals log(1+eps) exactly (construction check)
    assert abs(b["logradius_slope"] - b["logradius_slope_expected"]) < 1e-9
    assert b["one_octave_per_turn"]                           # octave bridge


def test_part_c_bundle_is_connected_and_holographic():
    run = _load()
    c = run.part_c(256)
    assert c["connected"]
    # boundary-to-boundary distance grows logarithmically (geodesics via bulk)
    assert c["boundary_distance_is_logarithmic"]
    assert c["r2_boundary_vs_log_separation"] > c["r2_boundary_vs_linear_separation"]


def test_quick_result_is_json_serializable_and_signals_present():
    run = _load()
    result = run.simulate(quick=True)
    json.dumps(result)                                        # no numpy types
    all_signals, checks = run.evaluate(result)
    assert all_signals, checks


def test_committed_result_json_signals():
    path = os.path.abspath(os.path.join(_DIR, "result.json"))
    if not os.path.exists(path):
        return
    with open(path) as f:
        result = json.load(f)
    run = _load()
    ok, checks = run.evaluate(result)
    assert ok, checks
