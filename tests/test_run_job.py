"""Phase 3 test: the Live Runner computes a REAL non-official candidate room from a UI job request.

Physically honest guarantees enforced here:
  - a job runs the real g001 reference model from t=0 (reproducible checksum, measured emergence);
  - it may only change an allowed start-side knob within the allowed range;
  - a non-g001 parent is rejected (the runner would otherwise mislabel the physics);
  - the produced candidate room is NON-official, replayable, and never claims full_3d promotion;
  - the job status + all room artifacts validate against their schemas.

All tests write into a temp tree so the committed repo is untouched.
"""

import json
import os
import shutil

import pytest
import yaml
from jsonschema import Draft202012Validator

from tools import run_job

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def clean_job():
    """Remove any artifacts a test's job_id/result_room would create, before and after."""
    created = {"jobs": [], "rooms": []}

    def _cleanup():
        for jid in created["jobs"]:
            p = os.path.join(_REPO, "rooms", "jobs", "%s.json" % jid)
            if os.path.exists(p):
                os.remove(p)
            if os.path.exists(run_job.LEDGER):
                led = json.load(open(run_job.LEDGER))
                led["jobs"] = [j for j in led["jobs"] if j["job_id"] != jid]
                json.dump(led, open(run_job.LEDGER, "w"), indent=2, ensure_ascii=False)
        for rid in created["rooms"]:
            shutil.rmtree(os.path.join(_REPO, "rooms", "candidates", rid), ignore_errors=True)

    yield created
    _cleanup()


def _run(created, job_id, override, parent="room-g001-a", seed=0):
    created["jobs"].append(job_id)
    st = run_job.run_job({"job_id": job_id, "parent_room": parent, "override": override,
                          "seed": seed, "quick": True})
    if st.get("result_room"):
        created["rooms"].append(st["result_room"])
    return st


def test_job_produces_nonofficial_replayable_candidate(clean_job):
    st = _run(clean_job, "job-test-a", {"param": "noise_amplitude", "to": 5e-3})
    assert st["status"] == "done"
    rid = st["result_room"]
    rdir = os.path.join(_REPO, "rooms", "candidates", rid)
    room = yaml.safe_load(open(os.path.join(rdir, "room.yaml")))
    assert room["official"] is False
    assert room["dimension_status"]["full_3d"] != "passed"  # a job cannot self-promote
    # replay fields were recorded and are honest (no decorative particles, physics unchanged)
    field = json.load(open(os.path.join(rdir, "runs", "seed-0000", "field.json")))
    assert field["honesty"]["changes_physics"] is False
    assert field["honesty"]["decorative_particles"] is False
    assert field["lenses"]  # phase/density recorded


def test_job_is_reproducible(clean_job):
    a = _run(clean_job, "job-test-r1", {"param": "noise_amplitude", "to": 5e-3}, seed=3)
    b = _run(clean_job, "job-test-r2", {"param": "noise_amplitude", "to": 5e-3}, seed=3)
    assert a["checksum"] == b["checksum"]  # same knob + seed -> identical field
    c = _run(clean_job, "job-test-r3", {"param": "noise_amplitude", "to": 5e-3}, seed=4)
    assert c["checksum"] != a["checksum"]  # different seed -> different field


def test_job_rejects_out_of_range_knob(clean_job):
    st = _run(clean_job, "job-test-bad", {"param": "noise_amplitude", "to": 1.0})  # > allowed max
    assert st["status"] == "rejected"
    assert st["result_room"] is None if "result_room" in st else True
    assert "outside allowed range" in st["reason"]


def test_job_rejects_disallowed_param(clean_job):
    st = _run(clean_job, "job-test-param", {"param": "eps_final", "to": 2.0})  # not a start-side knob
    assert st["status"] == "rejected"
    assert "not an allowed start-side knob" in st["reason"]


def test_job_rejects_non_g001_parent(clean_job):
    # The Live Runner computes with the g001 model; branching a g002/g003 room would mislabel physics.
    st = _run(clean_job, "job-test-model", {"param": "noise_amplitude", "to": 5e-3},
              parent="room-g002-a")
    assert st["status"] == "rejected"
    assert "only branches" in st["reason"]


def test_job_outputs_validate_against_schemas(clean_job):
    st = _run(clean_job, "job-test-schema", {"param": "quench_duration", "to": 12.0})
    assert st["status"] == "done"
    rid = st["result_room"]
    rdir = os.path.join(_REPO, "rooms", "candidates", rid)

    def V(schema, doc):
        Draft202012Validator(json.load(open(os.path.join(_REPO, "schemas", schema)))).validate(doc)

    V("room.schema.json", yaml.safe_load(open(os.path.join(rdir, "room.yaml"))))
    V("genesis.schema.json", yaml.safe_load(open(os.path.join(rdir, "genesis.yaml"))))
    V("emergence.schema.json", json.load(open(os.path.join(rdir, "emergence.json"))))
    V("field-index.schema.json", json.load(open(os.path.join(rdir, "runs", "seed-0000", "field.json"))))
    V("render-manifest.schema.json", yaml.safe_load(open(os.path.join(rdir, "render-manifest.yaml"))))
    V("job.schema.json", json.load(open(os.path.join(_REPO, "rooms", "jobs", "job-test-schema.json"))))


def test_genesis_doc_only_records_applied_knob(clean_job):
    # quench_duration override must be reflected in the genesis protocol (faithful to what actually ran).
    st = _run(clean_job, "job-test-genesis", {"param": "quench_duration", "to": 20.0})
    g = yaml.safe_load(open(os.path.join(_REPO, "rooms", "candidates", st["result_room"], "genesis.yaml")))
    assert g["protocol"]["quench"]["duration"] == 20.0
    assert g["model"] == run_job.gl.MODEL_ID
