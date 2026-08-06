#!/usr/bin/env python3
"""Portable Linux CI runner for Aeterna Genesis.

This runner is deliberately independent of GitHub Actions. It executes a named
profile, streams each command, and writes machine-readable results under
CI_ARTIFACTS (default: ci-artifacts/).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]


def command(name: str, argv: Sequence[str]) -> dict:
    return {"name": name, "argv": list(argv)}


AUTOPILOT_STEPS = [
    command(
        "compile-python",
        [sys.executable, "-m", "compileall", "-q", "genesis_orchestrator", "genesis/runners/recorded_runner.py", "ci"],
    ),
    command("autopilot-tests", [sys.executable, "-m", "pytest", "tests/test_genesis_orchestrator.py", "-q"]),
    command("schema-validation", [sys.executable, "tools/validate_schemas.py"]),
    command("autopilot-e2e-smoke", [sys.executable, "ci/smoke_autopilot.py"]),
]

APP_STEPS = [
    command("app-install", ["npm", "--prefix", "app", "ci", "--no-audit", "--no-fund"]),
    command("app-typecheck", ["npm", "--prefix", "app", "run", "typecheck"]),
    command("app-build", ["npm", "--prefix", "app", "run", "build"]),
]

PROFILES = {
    "autopilot": AUTOPILOT_STEPS,
    "quick": AUTOPILOT_STEPS + APP_STEPS,
    "full": [
        AUTOPILOT_STEPS[0],
        command("all-python-tests", [sys.executable, "-m", "pytest", "tests/", "-q"]),
        AUTOPILOT_STEPS[2],
        AUTOPILOT_STEPS[3],
    ]
    + APP_STEPS,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_step(step: dict, log_dir: Path, env: dict[str, str]) -> dict:
    name = step["name"]
    argv = step["argv"]
    log_path = log_dir / f"{name}.log"
    started = time.monotonic()
    print(f"\n=== {name} ===")
    print("+", " ".join(argv), flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            argv,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
        return_code = process.wait()
    duration = round(time.monotonic() - started, 3)
    return {
        "name": name,
        "argv": argv,
        "return_code": return_code,
        "status": "passed" if return_code == 0 else "failed",
        "duration_seconds": duration,
        "log": str(log_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run portable Linux CI without GitHub Actions.")
    parser.add_argument("profile", nargs="?", choices=sorted(PROFILES), default="autopilot")
    parser.add_argument(
        "--artifacts",
        default=os.environ.get("CI_ARTIFACTS", str(ROOT / "ci-artifacts")),
        help="directory for logs and report.json",
    )
    args = parser.parse_args(argv)

    if args.profile in {"quick", "full"} and shutil.which("npm") is None:
        parser.error("npm is required for quick/full profiles; use ci/Dockerfile or install Node.js")

    artifact_root = Path(args.artifacts).resolve()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = artifact_root / run_id
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "AETERNA_CI": "1",
        }
    )

    report = {
        "schema_version": 1,
        "profile": args.profile,
        "started_at": utc_now(),
        "platform": platform.platform(),
        "python": sys.version,
        "root": str(ROOT),
        "steps": [],
    }
    exit_code = 0
    for step in PROFILES[args.profile]:
        result = run_step(step, log_dir, env)
        report["steps"].append(result)
        if result["return_code"] != 0:
            exit_code = result["return_code"] or 1
            break

    report["finished_at"] = utc_now()
    report["status"] = "passed" if exit_code == 0 else "failed"
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    latest = artifact_root / "latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nCI {report['status']}: {run_dir / 'report.json'}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
