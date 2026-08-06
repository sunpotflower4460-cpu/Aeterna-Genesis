#!/usr/bin/env python3
"""Deterministic reporting and integrity checks for Genesis Autopilot campaigns."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from genesis_orchestrator import db  # noqa: E402


TERMINAL = {"done", "failed", "rejected"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_tree(path: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    if path.exists():
        for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
            files[file_path.relative_to(path).as_posix()] = _sha256_file(file_path)
    aggregate = hashlib.sha256()
    for rel, digest in files.items():
        aggregate.update(rel.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
    return {
        "path": str(path),
        "file_count": len(files),
        "tree_sha256": aggregate.hexdigest(),
        "files": files,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def mean_or_none(values: Iterable[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return round(statistics.fmean(clean), 6) if clean else None


def min_or_none(values: Iterable[int | None]) -> int | None:
    clean = [int(v) for v in values if v is not None]
    return min(clean) if clean else None


def job_passed(job: dict[str, Any]) -> bool:
    level = job.get("reached_level")
    return (
        job.get("status") == "done"
        and level is not None
        and int(level) >= int(job.get("min_reached_level", 1))
    )


def condition_row(
    trial_id: str,
    initial: list[dict[str, Any]],
    local: list[dict[str, Any]],
    expected_seeds: int,
) -> dict[str, Any]:
    initial_done = [j for j in initial if j["status"] == "done"]
    local_done = [j for j in local if j["status"] == "done"]
    initial_passes = sum(job_passed(j) for j in initial)
    local_passes = sum(job_passed(j) for j in local)
    local_defects = [
        (j.get("measured") or {}).get("defect_count")
        for j in local_done
    ]
    overrides = initial[0].get("overrides", {}) if initial else {}
    initial_terminal = all(j["status"] in TERMINAL for j in initial)
    local_terminal = all(j["status"] in TERMINAL for j in local)
    return {
        "condition_id": trial_id,
        "noise_amplitude": overrides.get("noise_amplitude"),
        "quench_duration": overrides.get("quench_duration"),
        "expected_seeds": expected_seeds,
        "initial_seed_count": len(initial),
        "initial_seed_values": sorted(int(j["seed"]) for j in initial),
        "2d_done": len(initial_done),
        "2d_failed": sum(j["status"] == "failed" for j in initial),
        "2d_passes": initial_passes,
        "2d_pass_rate": round(initial_passes / expected_seeds, 6),
        "2d_mean_level": mean_or_none(j.get("reached_level") for j in initial_done),
        "local_3d_created": len(local),
        "local_3d_done": len(local_done),
        "local_3d_failed": sum(j["status"] == "failed" for j in local),
        "local_3d_passes": local_passes,
        "local_3d_pass_rate_expected": round(local_passes / expected_seeds, 6),
        "local_3d_mean_level": mean_or_none(j.get("reached_level") for j in local_done),
        "local_3d_min_level": min_or_none(j.get("reached_level") for j in local_done),
        "local_3d_mean_defects": mean_or_none(local_defects),
        "condition_complete": (
            len(initial) == expected_seeds
            and initial_terminal
            and local_terminal
            and len(local) == initial_passes
        ),
    }


def ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    # Transparent lexicographic ranking: robustness first, then measured strength.
    return (
        -float(row["local_3d_passes"]),
        -float(row["local_3d_min_level"] if row["local_3d_min_level"] is not None else -1),
        -float(row["local_3d_mean_level"] if row["local_3d_mean_level"] is not None else -1),
        -float(row["2d_passes"]),
        -float(row["local_3d_mean_defects"] if row["local_3d_mean_defects"] is not None else -1),
        float(row["quench_duration"] if row["quench_duration"] is not None else 1e99),
        float(row["noise_amplitude"] if row["noise_amplitude"] is not None else 1e99),
    )


def command_snapshot(args: argparse.Namespace) -> int:
    write_json(Path(args.output), snapshot_tree(Path(args.path)))
    print(f"wrote tree snapshot: {args.output}")
    return 0


def command_report(args: argparse.Namespace) -> int:
    database = Path(args.db)
    jobs = db.list_jobs(database, args.campaign)
    initial = [j for j in jobs if j["stage"] == "2d-screen"]
    local = [j for j in jobs if j["stage"] == "local-3d"]

    by_trial_initial: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_trial_local: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in initial:
        by_trial_initial[job["trial_id"]].append(job)
    for job in local:
        by_trial_local[job["trial_id"]].append(job)

    rows = [
        condition_row(
            trial_id,
            sorted(trial_jobs, key=lambda j: int(j["seed"])),
            sorted(by_trial_local.get(trial_id, []), key=lambda j: int(j["seed"])),
            args.expected_seeds,
        )
        for trial_id, trial_jobs in sorted(by_trial_initial.items())
    ]
    rows.sort(key=ranking_key)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    status_counts = Counter(j["status"] for j in jobs)
    stage_counts = Counter(j["stage"] for j in jobs)
    job_ids = [j["job_id"] for j in jobs]
    failures = [
        {
            "job_id": j["job_id"],
            "trial_id": j["trial_id"],
            "stage": j["stage"],
            "seed": j["seed"],
            "error": j.get("error"),
        }
        for j in jobs
        if j["status"] == "failed"
    ]

    official_check: dict[str, Any] | None = None
    if args.official_baseline:
        baseline = json.loads(Path(args.official_baseline).read_text())
        current = snapshot_tree(ROOT / "rooms" / "official")
        official_check = {
            "baseline_tree_sha256": baseline.get("tree_sha256"),
            "current_tree_sha256": current.get("tree_sha256"),
            "unchanged": baseline.get("tree_sha256") == current.get("tree_sha256"),
            "baseline_file_count": baseline.get("file_count"),
            "current_file_count": current.get("file_count"),
        }

    checks = {
        "initial_job_count_matches": len(initial) == args.expected_initial,
        "unique_job_ids": len(job_ids) == len(set(job_ids)),
        "condition_count_matches": len(rows) * args.expected_seeds == args.expected_initial,
        "every_condition_has_expected_seeds": all(
            row["initial_seed_count"] == args.expected_seeds for row in rows
        ),
        "no_official_output_paths": all(
            not str(j.get("output_dir") or "").startswith("rooms/official")
            for j in jobs
        ),
        "official_tree_unchanged": (
            official_check["unchanged"] if official_check is not None else None
        ),
    }
    integrity_ok = all(value is not False for value in checks.values())
    no_active_jobs = not any(
        status_counts.get(status, 0)
        for status in ("queued", "running", "waiting_approval")
    )
    all_conditions_complete = bool(rows) and all(row["condition_complete"] for row in rows)
    campaign_complete = (
        len(initial) == args.expected_initial
        and no_active_jobs
        and all_conditions_complete
    )

    summary = {
        "campaign_id": args.campaign,
        "database": str(database),
        "expected_initial_2d_jobs": args.expected_initial,
        "expected_seeds_per_condition": args.expected_seeds,
        "parameter_condition_count": len(rows),
        "job_count_total": len(jobs),
        "stage_counts": dict(sorted(stage_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "2d_passes": sum(row["2d_passes"] for row in rows),
        "local_3d_passes": sum(row["local_3d_passes"] for row in rows),
        "conditions_with_5_of_5_local_3d_passes": sum(
            row["local_3d_passes"] == args.expected_seeds for row in rows
        ),
        "failed_job_count": len(failures),
        "campaign_complete": campaign_complete,
        "integrity_ok": integrity_ok,
        "integrity_checks": checks,
        "official_tree_check": official_check,
        "ranking_rule": [
            "local_3d_passes descending",
            "local_3d_min_level descending",
            "local_3d_mean_level descending",
            "2d_passes descending",
            "local_3d_mean_defects descending",
            "quench_duration ascending",
            "noise_amplitude ascending",
        ],
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "failures.json", failures)
    write_json(
        out_dir / "haiku_context.json",
        {
            "summary": summary,
            "top_conditions": rows[: min(20, len(rows))],
            "caveat": (
                "This is a quick-grid screening campaign. Rankings are measured associations, "
                "not proof of a universal causal optimum."
            ),
        },
    )

    csv_fields = [
        "rank",
        "condition_id",
        "noise_amplitude",
        "quench_duration",
        "expected_seeds",
        "initial_seed_count",
        "2d_done",
        "2d_failed",
        "2d_passes",
        "2d_pass_rate",
        "2d_mean_level",
        "local_3d_created",
        "local_3d_done",
        "local_3d_failed",
        "local_3d_passes",
        "local_3d_pass_rate_expected",
        "local_3d_mean_level",
        "local_3d_min_level",
        "local_3d_mean_defects",
        "condition_complete",
    ]
    with (out_dir / "ranked_conditions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if not integrity_ok:
        return 3
    if args.require_complete and not campaign_complete:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="hash a directory tree before a campaign")
    snap.add_argument("--path", required=True)
    snap.add_argument("--output", required=True)
    snap.set_defaults(func=command_snapshot)

    report = sub.add_parser("report", help="write deterministic campaign reports")
    report.add_argument(
        "--db",
        default=str(ROOT / "runtime" / "genesis_autopilot.sqlite3"),
    )
    report.add_argument("--campaign", required=True)
    report.add_argument("--expected-initial", type=int, required=True)
    report.add_argument("--expected-seeds", type=int, required=True)
    report.add_argument("--official-baseline")
    report.add_argument("--out-dir", required=True)
    report.add_argument("--require-complete", action="store_true")
    report.set_defaults(func=command_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
