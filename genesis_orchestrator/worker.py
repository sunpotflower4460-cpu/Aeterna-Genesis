"""Execute queued campaigns through 2D and gated 3D stages."""

from __future__ import annotations

import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from genesis.runners.recorded_runner import run_recorded

from . import artifacts, db


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def refresh_app(root: Path) -> None:
    subprocess.run([sys.executable, str(root / "tools" / "build_catalog.py")], cwd=root, check=True)
    subprocess.run([sys.executable, str(root / "tools" / "collect_app_data.py")], cwd=root, check=True)


def execute_one(database: str | Path, *, root: Path | None = None, refresh: bool = True) -> dict[str, Any] | None:
    root = root or repo_root()
    job = db.claim_next(database)
    if job is None:
        return None
    artifacts.sync_job_status(root, job, status="running")
    try:
        result = run_recorded(job["genesis"], mode=job["stage"], quick=job["quick"])
        reached = int(result["manifest"]["summary"]["reached_level"])
        passed = reached >= int(job["min_reached_level"])
        room_id, room_dir = artifacts.write_candidate(root, job, result, passed=passed)
        checksum = result["manifest"]["checksum"]["final_field_sha256"]
        measured = result["emergence"]["measured_by"]
        db.finish_job(
            database,
            job["job_id"],
            result_room=room_id,
            reached_level=reached,
            checksum=checksum,
            measured=measured,
            output_dir=str(room_dir.relative_to(root)),
        )
        finished = db.get_job(database, job["job_id"])
        assert finished is not None
        artifacts.sync_job_status(root, finished)
        artifacts.append_discovery(root, finished, passed=passed)
        next_job = None
        if passed:
            next_job = db.add_next_stage(database, finished, result["genesis"])
            if next_job is not None:
                artifacts.sync_job_status(root, next_job)
        if refresh:
            refresh_app(root)
        return {"job": finished, "passed": passed, "next_job": next_job}
    except Exception as exc:  # noqa: BLE001 -- worker must persist the failure and continue later
        detail = "%s: %s\n%s" % (type(exc).__name__, exc, traceback.format_exc(limit=8))
        db.fail_job(database, job["job_id"], detail)
        failed = db.get_job(database, job["job_id"])
        if failed is not None:
            artifacts.sync_job_status(root, failed)
        return {"job": failed or job, "passed": False, "error": detail}


def work_until_idle(
    database: str | Path,
    *,
    root: Path | None = None,
    max_jobs: int | None = None,
    refresh: bool = True,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    while max_jobs is None or len(results) < max_jobs:
        result = execute_one(database, root=root, refresh=refresh)
        if result is None:
            break
        results.append(result)
    return results
