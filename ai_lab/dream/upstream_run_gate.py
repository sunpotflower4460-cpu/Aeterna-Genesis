from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


RESEARCH_JOB = "research-burst"
WATCHDOG_STEP = "Decide whether backup burst is needed"
NOOP_STEP = "Backup not needed"
CORE_RESEARCH_STEP = "Run hourly Adaptive Dream v8 Pure Genesis R0 + NØ research"

NOOP = "NOOP"
EXECUTED = "RESEARCH_EXECUTED"
UNKNOWN = "UNKNOWN"


def _step_map(job: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(step.get("name")): step
        for step in (job.get("steps") or [])
        if isinstance(step, dict) and step.get("name")
    }


def classify_jobs_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify one completed Genesis Dream Loop from its Actions jobs payload.

    A run is a safe NOOP only when the watchdog and explicit "Backup not needed" step both
    completed successfully AND the actual research step was skipped. Anything incomplete,
    renamed, missing or otherwise ambiguous is UNKNOWN so callers can fail closed rather than
    accidentally suppressing integrity checks for a real research burst.
    """
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return {"classification": UNKNOWN, "reason": "jobs payload missing a jobs list", "noop": False}

    research_job = next(
        (job for job in jobs if isinstance(job, dict) and job.get("name") == RESEARCH_JOB),
        None,
    )
    if research_job is None:
        return {"classification": UNKNOWN, "reason": "research-burst job not found", "noop": False}

    steps = _step_map(research_job)
    watchdog = steps.get(WATCHDOG_STEP)
    noop_step = steps.get(NOOP_STEP)
    core = steps.get(CORE_RESEARCH_STEP)
    if watchdog is None or core is None:
        return {
            "classification": UNKNOWN,
            "reason": "required watchdog/core step not found",
            "noop": False,
        }

    core_conclusion = core.get("conclusion")
    if core_conclusion == "success":
        return {
            "classification": EXECUTED,
            "reason": "core research step completed successfully",
            "noop": False,
        }

    if (
        core_conclusion == "skipped"
        and watchdog.get("conclusion") == "success"
        and noop_step is not None
        and noop_step.get("conclusion") == "success"
    ):
        return {
            "classification": NOOP,
            "reason": "watchdog explicitly skipped a fresh burst because recent evidence exists",
            "noop": True,
        }

    return {
        "classification": UNKNOWN,
        "reason": (
            "core research did not complete successfully, but the explicit no-op contract "
            "was not fully satisfied"
        ),
        "noop": False,
    }


def fetch_jobs_payload(repository: str, run_id: str, token: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/jobs?per_page=100"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aeterna-research-postflight",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - fixed GitHub API host
        return json.load(response)


def _write_github_output(path: str | None, result: dict[str, Any]) -> None:
    if not path:
        return
    p = Path(path)
    with p.open("a", encoding="utf-8") as f:
        f.write(f"classification={result['classification']}\n")
        f.write(f"noop={'true' if result['noop'] else 'false'}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify an upstream Genesis Dream Loop as research or explicit no-op.")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--run-id", default=os.environ.get("UPSTREAM_RUN_ID"))
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    parser.add_argument("--payload", help="Optional local jobs JSON fixture instead of GitHub API access")
    args = parser.parse_args(argv)

    if args.payload:
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not args.repository or not args.run_id or not token:
            parser.error("repository, run id and GITHUB_TOKEN are required for API mode")
        payload = fetch_jobs_payload(args.repository, str(args.run_id), token)

    result = classify_jobs_payload(payload)
    _write_github_output(args.github_output, result)
    print(json.dumps(result, ensure_ascii=False))

    # UNKNOWN must fail closed: a renamed/missing step must never be silently treated as a no-op.
    return 2 if result["classification"] == UNKNOWN else 0


if __name__ == "__main__":
    raise SystemExit(main())
