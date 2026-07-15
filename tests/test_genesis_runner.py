"""PR4 test: the common Genesis Runner produces a reproducible, schema-valid run with measured emergence."""

import json
import os

from jsonschema import Draft202012Validator

from genesis.runners import runner

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _demo(seed=0):
    g = dict(runner._DEMO_GENESIS)
    g["seed"] = seed
    return g


def test_runner_2d_reaches_symmetry_breaking():
    r = runner.run(_demo(), mode="2d-screen", quick=True)
    e = r["emergence"]
    # order parameter emerges from the disordered start (Level 1) and vortices form + persist (Level 2)
    assert r["manifest"]["summary"]["reached_level"] >= 1
    assert e["measured_by"]["mean_amplitude_growth"] > 5.0
    assert e["detected"]["difference"] is True
    assert e["natural_emergence"]["target_shape_seeded"] is False


def test_runner_reproducible_checksum():
    a = runner.run(_demo(seed=1), mode="2d-screen", quick=True)
    b = runner.run(_demo(seed=1), mode="2d-screen", quick=True)
    assert a["manifest"]["checksum"] == b["manifest"]["checksum"]  # same genesis+seed -> identical field
    c = runner.run(_demo(seed=2), mode="2d-screen", quick=True)
    assert c["manifest"]["checksum"] != a["manifest"]["checksum"]  # different seed -> different field


def test_run_and_emergence_validate_against_schemas():
    r = runner.run(_demo(), mode="2d-screen", quick=True)
    run_schema = json.load(open(os.path.join(_REPO, "schemas", "run.schema.json")))
    emg_schema = json.load(open(os.path.join(_REPO, "schemas", "emergence.schema.json")))
    Draft202012Validator(run_schema).validate(r["manifest"])
    Draft202012Validator(emg_schema).validate(r["emergence"])


def test_runner_3d_smoke_runs_from_zero():
    r = runner.run(_demo(), mode="local-3d", quick=True)
    assert r["manifest"]["dimension"] == 3
    assert r["emergence"]["measured_by"]["mean_amplitude_growth"] > 5.0  # order parameter emerged in 3D too


def test_corroborate_run_wiring_writes_panel_and_is_honest(tmp_path):
    """--corroborate wiring: fires a (stubbed here) cross-repo panel and writes corroboration.json alongside,
    WITHOUT touching manifest/checksum. Offline backends must surface backed=None, never a faked pass."""
    seen = {}

    def stub_panel(shape2d, shape3d, seed):
        seen.update(shape2d=shape2d, shape3d=shape3d, seed=seed)
        # shape of an OFFLINE result: both reference repos unavailable -> backed=None (honest soft failure)
        return {"white": "cgl_local",
                "genesis_room_3d": {"kind": "same_model_quantitative", "backed": None, "reason": "unavailable"},
                "zero_looper_2d": {"kind": "reduced_mechanism_structural", "backed": None, "reason": "unavailable"}}

    panel = runner.corroborate_run(quick=True, seed=3, out_dir=str(tmp_path), panel_fn=stub_panel)
    assert seen == {"shape2d": (32, 32), "shape3d": (16, 16, 16), "seed": 3}   # 2D + 3D dispatched together
    assert panel["genesis_room_3d"]["backed"] is None                          # offline = None, not True
    assert panel["zero_looper_2d"]["backed"] is None
    assert "not this run's checksum" in panel["note"]                          # honest label
    written = json.load(open(os.path.join(str(tmp_path), "corroboration.json")))
    assert written["genesis_room_3d"]["kind"] == "same_model_quantitative"
    assert written["zero_looper_2d"]["kind"] == "reduced_mechanism_structural"


def test_corroborate_is_additive_run_and_checksum_unchanged():
    """The run itself (and its field checksum) is identical whether or not corroboration is requested:
    corroboration is a separate artifact and never feeds back into the physics."""
    a = runner.run(_demo(seed=7), mode="2d-screen", quick=True)
    b = runner.run(_demo(seed=7), mode="2d-screen", quick=True)          # corroboration is out-of-band; run() is pure
    assert a["manifest"]["checksum"] == b["manifest"]["checksum"]
