#!/usr/bin/env python3
"""End-to-end Autopilot smoke test in an isolated temporary repository copy.

The smoke performs real quick 2D and local-3D calculations. All generated Rooms,
SQLite state, and ledgers stay inside the temporary copy, so a developer's
working tree remains untouched.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(str(file.relative_to(path)).encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def ignore_copy(directory: str, names: list[str]) -> set[str]:
    ignored = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "runtime",
        "ci-artifacts",
    }
    return set(names) & ignored


def run(repo: Path, *argv: str, capture: bool = False) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    result = subprocess.run(
        [sys.executable, *argv],
        cwd=repo,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return result.stdout or ""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aeterna-ci-") as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(ROOT, repo, ignore=ignore_copy)
        official_before = tree_digest(repo / "rooms" / "official")
        database = repo / "runtime" / "smoke.sqlite3"
        campaign = repo / "ci" / "autopilot_smoke.yaml"

        run(repo, "-m", "genesis_orchestrator", "--db", str(database), "init")
        run(repo, "-m", "genesis_orchestrator", "--db", str(database), "submit", str(campaign))
        run(
            repo,
            "-m",
            "genesis_orchestrator",
            "--db",
            str(database),
            "work",
            "--max-jobs",
            "2",
            "--no-refresh-app",
        )
        raw = run(
            repo,
            "-m",
            "genesis_orchestrator",
            "--db",
            str(database),
            "status",
            "--campaign",
            "ci-autopilot-smoke",
            "--json",
            capture=True,
        )
        jobs = json.loads(raw)
        assert len(jobs) == 2, jobs
        by_stage = {job["stage"]: job for job in jobs}
        assert set(by_stage) == {"2d-screen", "local-3d"}, by_stage
        assert all(job["status"] == "done" for job in jobs), jobs

        room_id = by_stage["local-3d"]["result_room"]
        room_dir = repo / "rooms" / "candidates" / room_id
        room = yaml.safe_load((room_dir / "room.yaml").read_text())
        assert room["official"] is False
        assert room["dimension_status"]["local_3d"] == "passed"
        render_manifest = yaml.safe_load((room_dir / "render-manifest.yaml").read_text())
        field = json.loads((room_dir / render_manifest["frames_ref"]).read_text())
        run_manifest_path = next((room_dir / "runs").glob("local_3d-*/manifest.json"))
        run_manifest = json.loads(run_manifest_path.read_text())
        assert render_manifest["dimension"] == 3
        assert run_manifest["manifest"]["grid"] == [20, 20, 20]
        assert field["dimension"] == 3
        assert field["grid"] == [28, 28, 28]
        assert field["honesty"]["interpolated_for_display"] is True
        assert tree_digest(repo / "rooms" / "official") == official_before

        print(
            json.dumps(
                {
                    "status": "passed",
                    "jobs": {stage: job["job_id"] for stage, job in by_stage.items()},
                    "local_3d_room": room_id,
                    "simulation_grid": run_manifest["manifest"]["grid"],
                    "display_grid": field["grid"],
                    "official_tree_unchanged": True,
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
