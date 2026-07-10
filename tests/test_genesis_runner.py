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
