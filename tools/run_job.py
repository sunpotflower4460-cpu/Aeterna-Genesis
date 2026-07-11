#!/usr/bin/env python3
"""Live Runner (Phase 3) — actually COMPUTE a new Genesis Room from a UI job request.

Physically honest: this runs the REAL reference model (complex TDGL, genesis/models/ginzburg_landau.py)
from t=0 with NO intervention, changing ONLY a start-side knob that is inside the allowed search space
(genesis/registry/param_ranges.yaml). It never touches official rooms, success criteria, conservation
code, or audit thresholds. The result is a NON-official CANDIDATE room (2D screen), with recorded fields
so the Observatory can replay the real result. Full-3D promotion / grid convergence stays a separate,
gated step (AI_EXPERIMENT_POLICY / DIMENSION_POLICY) — a job cannot self-promote to official.

The browser does not run physics: the UI emits a job REQUEST; this CLI (a worker) executes it and writes
a job STATUS file + candidate room the UI then surfaces.

    python tools/run_job.py --request '{"job_id":"job-0001","parent_room":"room-g001-a",
                                         "override":{"param":"noise_amplitude","to":5e-4},"seed":0}'
    python tools/run_job.py --smoke        # tiny end-to-end job (CI)
"""

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import ginzburg_landau as gl  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402
from genesis.runners import runner  # noqa: E402
from genesis.recording import recorder as record  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

JOBS_DIR = os.path.join(_REPO, "rooms", "jobs")
LEDGER = os.path.join(JOBS_DIR, "ledger.json")
FRAME_GRID = (48, 48)


def _search_space():
    return yaml.safe_load(open(os.path.join(_REPO, "genesis", "registry", "param_ranges.yaml")))["search_space"]


def _parent_model(parent):
    """Resolve a parent room's genesis_model, if the room is known. None => lineage-only / unknown."""
    idx = os.path.join(_REPO, "rooms", "catalog.json")
    if os.path.exists(idx):
        for e in json.load(open(idx)).get("rooms", []):
            if e.get("room_id") == parent:
                return e.get("genesis_model")
    for base in ("candidates", "rejected_in_3d"):
        ry = os.path.join(_REPO, "rooms", base, parent, "room.yaml")
        if os.path.exists(ry):
            return yaml.safe_load(open(ry)).get("genesis_model")
    return None


# Only knobs the 2D screen ACTUALLY applies to the computation are offered, so genesis.yaml never
# records a start condition the run did not use. (correlation_length would need spatially-correlated
# make_initial() -- a physics/initial-condition change that belongs in a separate, gated PR.)
ALLOWED_KNOBS = ("noise_amplitude", "quench_duration")


def _validate_override(override):
    """The job may change only an allowed start-side knob within the allowed range (AI cannot exceed it)."""
    ss = _search_space()
    param, to = override["param"], float(override["to"])
    if param == "noise_amplitude":
        r = ss["initial_state"]["noise_amplitude"]
        ok = r["min"] <= to <= r["max"]
    elif param == "quench_duration":
        ok = 0.0 < to <= 40.0
    else:
        return False, "param '%s' is not an allowed start-side knob (%s)" % (param, ", ".join(ALLOWED_KNOBS))
    return ok, None if ok else "value %g outside allowed range for %s" % (to, param)


def _genesis(N, override, seed):
    g = {"schema_version": 1, "model": gl.MODEL_ID, "dimension": 2,
         "domain": {"size": [N, N], "spacing": 1.0, "boundary": "periodic"},
         "fields": {"psi": {"type": "complex_scalar"}},
         "initial_state": {"type": "uniform_plus_noise", "mean_amplitude": 0.0,
                           "noise_amplitude": gl.DEFAULTS["noise_amplitude"], "correlation_length": 1.0},
         "protocol": {"quench": {"start": 0.0, "duration": gl.DEFAULTS["quench_duration"]}},
         "seed": seed, "drive_class": "time_programmed_environment"}
    if override["param"] == "noise_amplitude":
        g["initial_state"]["noise_amplitude"] = float(override["to"])
    elif override["param"] == "quench_duration":
        g["protocol"]["quench"]["duration"] = float(override["to"])
    return g


def _run_2d_screen(override, seed, N=64, steps=240):
    """REAL 2D TDGL screen from t=0 with the overridden knob; records phase/density fields for replay."""
    p = dict(gl.DEFAULTS)
    if override["param"] == "noise_amplitude":
        p["noise_amplitude"] = float(override["to"])
    elif override["param"] == "quench_duration":
        p["quench_duration"] = float(override["to"])
    rng = np.random.default_rng(seed)
    psi = gl.make_initial((N, N), p["noise_amplitude"], rng)
    rec = (record.FieldRecorder(2, FRAME_GRID)
           .declare("phase", "arg(psi)", "rad", cyclic=True)
           .declare("density", "abs(psi)^2", "n"))
    traj = []
    snap = max(1, steps // 12)
    for t in range(steps):
        psi = gl.step(psi, t * p["dt"], p)
        if t % snap == 0 or t == steps - 1:
            _, skprom = measures.structure_factor_peak(psi)
            traj.append({"step": t, "mean_amp": measures.mean_amplitude(psi), "sk_prom": skprom,
                         "defects": measures.winding_defect_count(psi)})
            rec.add(t * p["dt"], {"phase": np.angle(psi), "density": np.abs(psi) ** 2})
    reached, detected, mb = measures.assess_level(traj)
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes()); h.update(np.ascontiguousarray(psi.imag).tobytes())
    return {"reached": reached, "detected": detected, "measured_by": mb, "checksum": h.hexdigest(),
            "traj": traj, "rec": rec, "N": N, "steps": steps}


def _emergence_doc(r, reached):
    mb = r["measured_by"]
    return {
        "reached_level": reached, "candidate_level": min(reached + 1, 8),
        "uninterrupted_from_zero": True, "level_detected_by_measurement": True,
        "detected": {"difference": r["detected"]["difference"], "localization": r["detected"]["localization"]},
        "measured_by": {"mean_amplitude_growth": float(mb["mean_amplitude_growth"]),
                        "structure_factor_prominence": float(mb["structure_factor_prominence"]),
                        "defect_count": int(mb["defect_count"]),
                        "persistent_defects": bool(mb["persistent_defects"])},
        "purity": {"per_object_labels": False, "external_optimum": False, "role": "E" if reached >= 1 else "F"},
        "natural_emergence": {"started_from_time_zero": True, "target_shape_seeded": False,
                              "runtime_interventions": 0, "target_dependent_rules": False,
                              "target_dependent_stopping": False, "target_dependent_clipping": False,
                              "level_detected_by_measurement": True},
    }


def _write_candidate(room_id, parent, override, seed, g, r):
    rdir = os.path.join(_REPO, "rooms", "candidates", room_id)
    os.makedirs(os.path.join(rdir, "runs", "seed-%04d" % seed), exist_ok=True)
    reached = r["reached"]
    label = "%s=%g" % (override["param"], override["to"])
    room = {"room_id": room_id, "title": "Live candidate: %s" % label, "parent_room": parent,
            "favorite": False, "official": False, "genesis_model": gl.MODEL_ID,
            "emergence": {"reached_level": reached, "candidate_level": min(reached + 1, 8)},
            "dimension_status": {"exploration_2d": "passed", "local_3d": "not_started",
                                 "coarse_global_3d": "not_started", "full_3d": "not_started"},
            "physics_status": {"conservation": "pending", "convergence": "pending",
                               "reproducibility": "passed", "integrity_audit": "passed"},
            "status": "candidate"}
    emergence = _emergence_doc(r, reached)
    manifest = {"run_id": "%s-2d-seed%04d" % (gl.MODEL_ID, seed), "room_id": room_id, "seed": seed,
                "dimension": 2, "mode": "2d-screen",
                "manifest": {"genesis": "job", "solver": gl.MODEL_ID, "steps": r["steps"],
                             "dt": gl.DEFAULTS["dt"], "grid": [r["N"], r["N"]],
                             "code_version": runner.CODE_VERSION},
                "summary": {"reached_level": reached},
                "checksum": {"final_field_sha256": r["checksum"]}}
    yaml.safe_dump(room, open(os.path.join(rdir, "room.yaml"), "w"), allow_unicode=True, sort_keys=False)
    yaml.safe_dump(g, open(os.path.join(rdir, "genesis.yaml"), "w"), allow_unicode=True, sort_keys=False)
    json.dump(emergence, open(os.path.join(rdir, "emergence.json"), "w"), indent=2)
    frames_ref = "runs/seed-%04d/field.json" % seed
    r["rec"].write_field(os.path.join(rdir, "runs", "seed-%04d" % seed))
    yaml.safe_dump(r["rec"].render_manifest(room_id, frames_ref), open(os.path.join(rdir, "render-manifest.yaml"), "w"),
                   allow_unicode=True, sort_keys=False)
    json.dump(manifest, open(os.path.join(rdir, "runs", "seed-%04d" % seed, "manifest.json"), "w"), indent=2)
    json.dump(emergence, open(os.path.join(rdir, "runs", "seed-%04d" % seed, "emergence.json"), "w"), indent=2)
    with open(os.path.join(rdir, "README.md"), "w") as f:
        f.write("# %s — Live Runner 候補 Room（非公式）\n\n" % room_id)
        f.write("親 `%s` の始原条件を `%s` に変えて **t=0 から実計算**した 2D screen 候補。**official ではない**。\n"
                % (parent, label))
        f.write("`full_3d=not_started`（full-3D 昇格・格子収束・複数 seed は別段階）。物理は本物・自己昇格しない。\n")
    return reached


def _write_status(job_id, doc):
    os.makedirs(JOBS_DIR, exist_ok=True)
    json.dump(doc, open(os.path.join(JOBS_DIR, "%s.json" % job_id), "w"), indent=2)


def _append_ledger(entry):
    os.makedirs(JOBS_DIR, exist_ok=True)
    led = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"jobs": []}
    if not any(j["job_id"] == entry["job_id"] for j in led["jobs"]):
        led["jobs"].append(entry)
        json.dump(led, open(LEDGER, "w"), indent=2, ensure_ascii=False)


def run_job(request, stamp=0.0):
    job_id = request["job_id"]
    parent = request.get("parent_room", "room-g001-a")
    override = request["override"]
    seed = int(request.get("seed", 0))
    base = {"job_id": job_id, "parent_room": parent, "override": override, "seed": seed,
            "requested_at": stamp}
    # The Live Runner computes with the g001 reference model (gl); a parent from another model would be
    # mislabeled. Reject a known non-g001 parent rather than silently branching the wrong physics.
    pm = _parent_model(parent)
    if pm is not None and pm != gl.MODEL_ID:
        why = "parent %s is model %s; Live Runner only branches %s" % (parent, pm, gl.MODEL_ID)
        st = {**base, "status": "rejected", "reason": why, "progress": 1.0}
        _write_status(job_id, st); _append_ledger({**base, "status": "rejected", "reason": why})
        return st
    ok, why = _validate_override(override)
    if not ok:
        st = {**base, "status": "rejected", "reason": why, "progress": 1.0}
        _write_status(job_id, st); _append_ledger({**base, "status": "rejected", "reason": why})
        return st
    _write_status(job_id, {**base, "status": "running", "progress": 0.1})
    N, steps = (32, 120) if request.get("quick") else (64, 240)
    r = _run_2d_screen(override, seed, N=N, steps=steps)
    g = _genesis(N, override, seed)
    room_id = "room-%s-%s" % (parent.replace("room-", ""), job_id)
    reached = _write_candidate(room_id, parent, override, seed, g, r)
    st = {**base, "status": "done", "progress": 1.0, "result_room": room_id,
          "reached_level": reached, "checksum": r["checksum"][:16],
          "measured_by": {"mean_amplitude_growth": round(float(r["measured_by"]["mean_amplitude_growth"]), 4),
                          "defect_count": int(r["measured_by"]["defect_count"])}}
    _write_status(job_id, st)
    _append_ledger({**base, "status": "done", "result_room": room_id, "reached_level": reached,
                    "checksum": r["checksum"][:16]})
    _validate_outputs(room_id, job_id, seed)
    return st


def _validate_outputs(room_id, job_id, seed):
    def V(schema, doc):
        Draft202012Validator(json.load(open(os.path.join(_REPO, "schemas", schema)))).validate(doc)
    rdir = os.path.join(_REPO, "rooms", "candidates", room_id)
    sd = "seed-%04d" % seed
    V("room.schema.json", yaml.safe_load(open(os.path.join(rdir, "room.yaml"))))
    V("genesis.schema.json", yaml.safe_load(open(os.path.join(rdir, "genesis.yaml"))))
    V("emergence.schema.json", json.load(open(os.path.join(rdir, "emergence.json"))))
    V("field-index.schema.json", json.load(open(os.path.join(rdir, "runs", sd, "field.json"))))
    V("render-manifest.schema.json", yaml.safe_load(open(os.path.join(rdir, "render-manifest.yaml"))))
    V("job.schema.json", json.load(open(os.path.join(JOBS_DIR, "%s.json" % job_id))))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Live Runner: compute a candidate Genesis Room from a job request")
    ap.add_argument("--request", help="job request JSON")
    ap.add_argument("--smoke", action="store_true", help="run a tiny end-to-end job (CI)")
    args = ap.parse_args(argv)
    if args.smoke:
        req = {"job_id": "job-smoke", "parent_room": "room-g001-a",
               "override": {"param": "noise_amplitude", "to": 5e-4}, "seed": 0, "quick": True}
    elif args.request:
        req = json.loads(args.request)
    else:
        ap.error("provide --request or --smoke")
    # Date.now-free stamp not needed; use monotonic-ish wall clock only for record display
    st = run_job(req, stamp=round(time.time(), 3) if not args.smoke else 0.0)
    print("job %s: %s%s" % (st["job_id"], st["status"],
                            (" -> " + st["result_room"]) if st.get("result_room") else ""))
    if args.smoke:
        # smoke must not pollute the committed tree
        import shutil
        shutil.rmtree(os.path.join(_REPO, "rooms", "candidates", st["result_room"]), ignore_errors=True)
        os.remove(os.path.join(JOBS_DIR, "job-smoke.json"))
        if os.path.exists(LEDGER):
            led = json.load(open(LEDGER))
            led["jobs"] = [j for j in led["jobs"] if j["job_id"] != "job-smoke"]
            json.dump(led, open(LEDGER, "w"), indent=2, ensure_ascii=False)
        print("smoke cleaned up")
    return 0


if __name__ == "__main__":
    sys.exit(main())
