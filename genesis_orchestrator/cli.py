"""Command-line interface for Genesis Autopilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import campaign, db, worker


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_db(root: Path) -> Path:
    return root / "runtime" / "genesis_autopilot.sqlite3"


def _print_job(job: dict) -> None:
    suffix = ""
    if job.get("reached_level") is not None:
        suffix += f" L{job['reached_level']}"
    if job.get("result_room"):
        suffix += f" -> {job['result_room']}"
    if job.get("error"):
        suffix += f" ({str(job['error']).splitlines()[0]})"
    print(f"{job['job_id']}: {job['status']} [{job['stage']}] seed={job['seed']}{suffix}")


def build_parser() -> argparse.ArgumentParser:
    root = repo_root()
    parser = argparse.ArgumentParser(
        prog="python -m genesis_orchestrator",
        description="Schema-gated, deterministic 2D -> 3D campaign runner for Aeterna Genesis.",
    )
    parser.add_argument("--db", default=str(default_db(root)), help="SQLite queue path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="initialize the SQLite queue")

    p_submit = sub.add_parser("submit", help="validate and submit a campaign YAML")
    p_submit.add_argument("campaign")

    p_work = sub.add_parser("work", help="execute queued jobs until idle")
    p_work.add_argument("--max-jobs", type=int, default=None)
    p_work.add_argument("--once", action="store_true")
    p_work.add_argument("--no-refresh-app", action="store_true")

    p_status = sub.add_parser("status", help="show campaigns and jobs")
    p_status.add_argument("--campaign", default=None)
    p_status.add_argument("--json", action="store_true")

    p_approve = sub.add_parser("approve", help="approve gated coarse/full 3D jobs")
    target = p_approve.add_mutually_exclusive_group(required=True)
    target.add_argument("--job")
    target.add_argument("--campaign")
    p_approve.add_argument("--stage", choices=("coarse-global-3d", "full-3d"))

    p_retry = sub.add_parser("retry", help="retry a failed job")
    p_retry.add_argument("job_id")

    sub.add_parser("refresh-app", help="rebuild Observatory catalog and copy recorded fields")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    database = Path(args.db)

    if args.command == "init":
        db.init_db(database)
        print(f"initialized {database}")
        return 0
    if args.command == "submit":
        doc, inserted = campaign.submit(args.campaign, database, root=root)
        print(f"submitted {doc['campaign_id']}: {inserted} initial 2D job(s)")
        return 0
    if args.command == "work":
        db.init_db(database)
        limit = 1 if args.once else args.max_jobs
        results = worker.work_until_idle(database, root=root, max_jobs=limit, refresh=not args.no_refresh_app)
        for result in results:
            _print_job(result["job"])
            if result.get("next_job"):
                nxt = result["next_job"]
                print(f"  next: {nxt['stage']} ({nxt['status']})")
        if not results:
            print("queue idle (or waiting for 3D approval)")
        return 0
    if args.command == "status":
        db.init_db(database)
        jobs = db.list_jobs(database, args.campaign)
        if args.json:
            print(json.dumps(jobs, indent=2, ensure_ascii=False))
        else:
            for item in jobs:
                _print_job(item)
            if not jobs:
                print("no jobs")
        return 0
    if args.command == "approve":
        db.init_db(database)
        count = db.approve(database, job_id=args.job, campaign_id=args.campaign, stage=args.stage)
        print(f"approved {count} job(s)")
        return 0 if count else 1
    if args.command == "retry":
        db.init_db(database)
        ok = db.retry(database, args.job_id)
        print("queued" if ok else "job not retryable")
        return 0 if ok else 1
    if args.command == "refresh-app":
        worker.refresh_app(root)
        print("Observatory data refreshed")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
