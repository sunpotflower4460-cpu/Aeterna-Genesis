"""Write non-official candidate rooms, compatible job status, and discovery ledgers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
import numpy as np
from jsonschema import Draft202012Validator

STAGES = ("2d-screen", "local-3d", "coarse-global-3d", "full-3d")
STAGE_TO_DIM_KEY = {
    "2d-screen": "exploration_2d",
    "local-3d": "local_3d",
    "coarse-global-3d": "coarse_global_3d",
    "full-3d": "full_3d",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _atomic_json(path: Path, value: Any, *, indent: int | None = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(_jsonable(value), handle, indent=indent, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _atomic_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            yaml.safe_dump(value, handle, allow_unicode=True, sort_keys=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in value.lower()).strip("-")


def room_id_for(job: dict[str, Any]) -> str:
    stage = job["stage"].replace("-", "")
    raw = f"room-auto-{job['campaign_id']}-{job['trial_id']}-{stage}-s{int(job['seed']):04d}"
    return _slug(raw)[:120]


def dimension_status(stage: str, passed: bool) -> dict[str, str]:
    status = {
        "exploration_2d": "not_started",
        "local_3d": "not_started",
        "coarse_global_3d": "not_started",
        "full_3d": "not_started",
    }
    idx = STAGES.index(stage)
    for earlier in STAGES[:idx]:
        status[STAGE_TO_DIM_KEY[earlier]] = "passed"
    status[STAGE_TO_DIM_KEY[stage]] = "passed" if passed else "failed"
    return status


def write_candidate(
    root: Path,
    job: dict[str, Any],
    result: dict[str, Any],
    *,
    passed: bool,
) -> tuple[str, Path]:
    room_id = room_id_for(job)
    is_3d_rejection = job["stage"] != "2d-screen" and not passed
    base = "rejected_in_3d" if is_3d_rejection else "candidates"
    room_dir = root / "rooms" / base / room_id
    run_name = "%s-seed-%04d" % (job["stage"].replace("-", "_"), int(job["seed"]))
    run_dir = room_dir / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    reached = int(result["manifest"]["summary"]["reached_level"])
    status = "rejected_in_3d" if is_3d_rejection else "candidate"
    room = {
        "room_id": room_id,
        "title": "Autopilot: %s / %s / %s" % (job["campaign_id"], job["trial_id"], job["stage"]),
        "parent_room": job["parent_room"],
        "favorite": False,
        "official": False,
        "genesis_model": job["model"],
        "emergence": {"reached_level": reached, "candidate_level": min(reached + 1, 8)},
        "dimension_status": dimension_status(job["stage"], passed),
        "physics_status": {
            "conservation": "pending",
            "convergence": "pending",
            "reproducibility": "pending",
            "integrity_audit": "passed",
        },
        "status": status,
    }
    _atomic_yaml(room_dir / "room.yaml", room)
    _atomic_yaml(room_dir / "genesis.yaml", result["genesis"])
    _atomic_json(room_dir / "emergence.json", result["emergence"])

    manifest = dict(result["manifest"])
    manifest["room_id"] = room_id
    checksum = manifest["checksum"]
    summary = manifest["summary"]
    _atomic_json(run_dir / "manifest.json", manifest)
    _atomic_json(run_dir / "summary.json", summary)
    _atomic_json(run_dir / "checksum.json", checksum)
    _atomic_json(run_dir / "emergence.json", result["emergence"])
    result["recorder"].write_field(str(run_dir))
    frames_ref = f"runs/{run_name}/field.json"
    _atomic_yaml(room_dir / "render-manifest.yaml", result["recorder"].render_manifest(room_id, frames_ref))
    (room_dir / "README.md").write_text(
        "# %s — Genesis Autopilot candidate\n\n" % room_id
        + "Campaign `%s`, trial `%s`, stage `%s`, seed `%s`.\n\n"
        % (job["campaign_id"], job["trial_id"], job["stage"], job["seed"])
        + "This is **non-official**. It was computed from t=0 by the repository's reference stepper, "
        + "with no runtime intervention. Promotion remains gated; this artifact never writes `rooms/official/`.\n"
    )
    validate_candidate(root, room_dir, run_dir)
    return room_id, room_dir


def validate_candidate(root: Path, room_dir: Path, run_dir: Path) -> None:
    def validate(schema_name: str, doc: Any) -> None:
        schema = json.loads((root / "schemas" / schema_name).read_text())
        Draft202012Validator(schema).validate(doc)

    validate("room.schema.json", yaml.safe_load((room_dir / "room.yaml").read_text()))
    validate("genesis.schema.json", yaml.safe_load((room_dir / "genesis.yaml").read_text()))
    validate("emergence.schema.json", json.loads((room_dir / "emergence.json").read_text()))
    validate("field-index.schema.json", json.loads((run_dir / "field.json").read_text()))
    validate("render-manifest.schema.json", yaml.safe_load((room_dir / "render-manifest.yaml").read_text()))


def _first_override(job: dict[str, Any]) -> dict[str, Any]:
    overrides = job.get("overrides") or {}
    if overrides:
        key = sorted(overrides)[0]
        return {"param": key, "to": float(overrides[key])}
    # Campaign schema requires a mutation; defensive fallback keeps the legacy job schema valid.
    return {"param": "noise_amplitude", "to": float(job["genesis"]["initial_state"]["noise_amplitude"])}


def sync_job_status(root: Path, job: dict[str, Any], *, status: str | None = None) -> None:
    internal = status or job["status"]
    public_status = {
        "waiting_approval": "queued",
        "failed": "rejected",
        "blocked": "rejected",
    }.get(internal, internal)
    if public_status not in ("queued", "running", "done", "rejected"):
        public_status = "queued"
    doc: dict[str, Any] = {
        "job_id": job["job_id"],
        "parent_room": job["parent_room"],
        "override": _first_override(job),
        "seed": int(job["seed"]),
        "requested_at": float(job["created_at"]),
        "status": public_status,
        "progress": 1.0 if public_status in ("done", "rejected") else (0.1 if public_status == "running" else 0.0),
    }
    if internal == "waiting_approval":
        doc["reason"] = f"waiting_approval:{job['stage']}"
    elif job.get("error"):
        doc["reason"] = str(job["error"])
    if job.get("result_room"):
        doc["result_room"] = job["result_room"]
    if job.get("reached_level") is not None:
        doc["reached_level"] = int(job["reached_level"])
    if job.get("checksum"):
        doc["checksum"] = str(job["checksum"])[:16]
    if job.get("measured"):
        doc["measured_by"] = {
            key: value for key, value in job["measured"].items()
            if isinstance(value, (int, float, bool))
        }
    jobs_dir = root / "rooms" / "jobs"
    _atomic_json(jobs_dir / f"{job['job_id']}.json", doc)

    ledger_path = jobs_dir / "ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"jobs": []}
    by_id = {item["job_id"]: item for item in ledger.get("jobs", []) if item.get("job_id")}
    by_id[job["job_id"]] = doc
    ledger["jobs"] = sorted(by_id.values(), key=lambda item: item["job_id"])
    _atomic_json(ledger_path, ledger)


def append_discovery(root: Path, job: dict[str, Any], *, passed: bool) -> None:
    path = root / "ai_lab" / "discoveries" / "autopilot_ledger.json"
    ledger = json.loads(path.read_text()) if path.exists() else {
        "ledger_version": 1,
        "note": "Genesis Autopilot stage results. Non-official; append/update by deterministic job_id.",
        "discoveries": [],
    }
    by_id = {item["job_id"]: item for item in ledger.get("discoveries", [])}
    by_id[job["job_id"]] = {
        "job_id": job["job_id"],
        "campaign_id": job["campaign_id"],
        "hypothesis_id": job["hypothesis_id"],
        "trial_id": job["trial_id"],
        "parent_room": job["parent_room"],
        "stage": job["stage"],
        "seed": int(job["seed"]),
        "overrides": job["overrides"],
        "reached_level": job.get("reached_level"),
        "min_reached_level": int(job["min_reached_level"]),
        "survived_stage": bool(passed),
        "result_room": job.get("result_room"),
        "checksum": job.get("checksum"),
        "measured_by": job.get("measured") or {},
    }
    ledger["discoveries"] = sorted(by_id.values(), key=lambda item: item["job_id"])
    _atomic_json(path, ledger)
