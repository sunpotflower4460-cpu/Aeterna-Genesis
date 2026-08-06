"""SQLite-backed campaign and physics-job queue."""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1


def now() -> float:
    return time.time()


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def loads(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    return json.loads(value)


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=30.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=30000")
    return con


def init_db(path: str | Path) -> None:
    with connect(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                campaign_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_path TEXT,
                document_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
                hypothesis_id TEXT NOT NULL,
                trial_id TEXT NOT NULL,
                parent_room TEXT NOT NULL,
                model TEXT NOT NULL,
                stage TEXT NOT NULL,
                stage_index INTEGER NOT NULL,
                pipeline_json TEXT NOT NULL,
                approval_stages_json TEXT NOT NULL,
                seed INTEGER NOT NULL,
                quick INTEGER NOT NULL DEFAULT 0,
                genesis_json TEXT NOT NULL,
                overrides_json TEXT NOT NULL,
                min_reached_level INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                priority INTEGER NOT NULL DEFAULT 100,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL,
                result_room TEXT,
                reached_level INTEGER,
                checksum TEXT,
                measured_json TEXT,
                output_dir TEXT,
                error TEXT,
                UNIQUE(campaign_id, trial_id, stage, seed)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_claim
                ON jobs(status, approved, priority, created_at);
            CREATE INDEX IF NOT EXISTS idx_jobs_campaign
                ON jobs(campaign_id, trial_id, stage_index, seed);
            """
        )
        con.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(SCHEMA_VERSION),),
        )


def add_campaign(
    path: str | Path,
    *,
    campaign_id: str,
    title: str,
    document: dict[str, Any],
    source_path: str | None,
) -> None:
    stamp = now()
    with connect(path) as con:
        con.execute(
            """
            INSERT INTO campaigns(campaign_id, title, source_path, document_json, status, created_at, updated_at)
            VALUES(?, ?, ?, ?, 'active', ?, ?)
            ON CONFLICT(campaign_id) DO UPDATE SET
                title=excluded.title,
                source_path=excluded.source_path,
                document_json=excluded.document_json,
                updated_at=excluded.updated_at
            """,
            (campaign_id, title, source_path, dumps(document), stamp, stamp),
        )


def add_jobs(path: str | Path, jobs: Iterable[dict[str, Any]]) -> int:
    inserted = 0
    with connect(path) as con:
        for job in jobs:
            cur = con.execute(
                """
                INSERT OR IGNORE INTO jobs(
                    job_id, campaign_id, hypothesis_id, trial_id, parent_room, model,
                    stage, stage_index, pipeline_json, approval_stages_json, seed, quick,
                    genesis_json, overrides_json, min_reached_level, status, approved,
                    priority, attempts, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    job["job_id"], job["campaign_id"], job["hypothesis_id"], job["trial_id"],
                    job["parent_room"], job["model"], job["stage"], job["stage_index"],
                    dumps(job["pipeline"]), dumps(job["approval_stages"]), int(job["seed"]),
                    int(bool(job.get("quick", False))), dumps(job["genesis"]), dumps(job["overrides"]),
                    int(job.get("min_reached_level", 1)), job["status"], int(bool(job.get("approved", False))),
                    int(job.get("priority", 100)), float(job.get("created_at", now())),
                ),
            )
            inserted += int(cur.rowcount > 0)
    return inserted


def row_to_job(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    out = dict(row)
    for key in ("pipeline_json", "approval_stages_json", "genesis_json", "overrides_json", "measured_json"):
        out[key.removesuffix("_json")] = loads(out.pop(key), None)
    out["quick"] = bool(out["quick"])
    out["approved"] = bool(out["approved"])
    return out


@contextmanager
def immediate(con: sqlite3.Connection):
    con.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        con.rollback()
        raise
    else:
        con.commit()


def claim_next(path: str | Path) -> dict[str, Any] | None:
    """Atomically claim one runnable job.

    Jobs waiting for human approval remain `waiting_approval`; only `queued` jobs are claimable.
    """
    con = connect(path)
    try:
        with immediate(con):
            row = con.execute(
                """
                SELECT * FROM jobs
                WHERE status='queued'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            stamp = now()
            changed = con.execute(
                """
                UPDATE jobs
                SET status='running', started_at=?, attempts=attempts+1, error=NULL
                WHERE job_id=? AND status='queued'
                """,
                (stamp, row["job_id"]),
            )
            if changed.rowcount != 1:
                return None
            return row_to_job(con.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone())
    finally:
        con.close()


def get_job(path: str | Path, job_id: str) -> dict[str, Any] | None:
    with connect(path) as con:
        return row_to_job(con.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())


def list_jobs(path: str | Path, campaign_id: str | None = None) -> list[dict[str, Any]]:
    with connect(path) as con:
        if campaign_id:
            rows = con.execute(
                "SELECT * FROM jobs WHERE campaign_id=? ORDER BY created_at, stage_index, seed",
                (campaign_id,),
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM jobs ORDER BY created_at, stage_index, seed").fetchall()
    return [row_to_job(r) for r in rows if r is not None]


def list_campaigns(path: str | Path) -> list[dict[str, Any]]:
    with connect(path) as con:
        rows = con.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        rec["document"] = loads(rec.pop("document_json"), {})
        out.append(rec)
    return out


def finish_job(
    path: str | Path,
    job_id: str,
    *,
    result_room: str,
    reached_level: int,
    checksum: str,
    measured: dict[str, Any],
    output_dir: str,
) -> None:
    with connect(path) as con:
        con.execute(
            """
            UPDATE jobs SET status='done', finished_at=?, result_room=?, reached_level=?,
                            checksum=?, measured_json=?, output_dir=?, error=NULL
            WHERE job_id=?
            """,
            (now(), result_room, int(reached_level), checksum, dumps(measured), output_dir, job_id),
        )


def fail_job(path: str | Path, job_id: str, error: str) -> None:
    with connect(path) as con:
        con.execute(
            "UPDATE jobs SET status='failed', finished_at=?, error=? WHERE job_id=?",
            (now(), error[:4000], job_id),
        )


def add_next_stage(path: str | Path, previous: dict[str, Any], genesis: dict[str, Any]) -> dict[str, Any] | None:
    pipeline = list(previous["pipeline"])
    next_index = int(previous["stage_index"]) + 1
    if next_index >= len(pipeline):
        return None
    stage = pipeline[next_index]
    approval_stages = list(previous["approval_stages"])
    needs_approval = stage in approval_stages
    job_id = make_job_id(previous["campaign_id"], previous["trial_id"], stage, int(previous["seed"]))
    job = {
        "job_id": job_id,
        "campaign_id": previous["campaign_id"],
        "hypothesis_id": previous["hypothesis_id"],
        "trial_id": previous["trial_id"],
        "parent_room": previous["parent_room"],
        "model": previous["model"],
        "stage": stage,
        "stage_index": next_index,
        "pipeline": pipeline,
        "approval_stages": approval_stages,
        "seed": previous["seed"],
        "quick": previous["quick"],
        "genesis": genesis,
        "overrides": previous["overrides"],
        "min_reached_level": previous["min_reached_level"],
        "status": "waiting_approval" if needs_approval else "queued",
        "approved": not needs_approval,
        "priority": previous["priority"] + next_index,
        "created_at": now(),
    }
    add_jobs(path, [job])
    return get_job(path, job_id)


def approve(
    path: str | Path,
    *,
    job_id: str | None = None,
    campaign_id: str | None = None,
    stage: str | None = None,
) -> int:
    if not job_id and not campaign_id:
        raise ValueError("job_id or campaign_id is required")
    clauses = ["status='waiting_approval'"]
    params: list[Any] = []
    if job_id:
        clauses.append("job_id=?")
        params.append(job_id)
    if campaign_id:
        clauses.append("campaign_id=?")
        params.append(campaign_id)
    if stage:
        clauses.append("stage=?")
        params.append(stage)
    with connect(path) as con:
        cur = con.execute(
            f"UPDATE jobs SET approved=1, status='queued' WHERE {' AND '.join(clauses)}",
            params,
        )
        return cur.rowcount


def retry(path: str | Path, job_id: str) -> bool:
    with connect(path) as con:
        cur = con.execute(
            """
            UPDATE jobs SET status='queued', approved=1, started_at=NULL, finished_at=NULL, error=NULL
            WHERE job_id=? AND status IN ('failed','rejected')
            """,
            (job_id,),
        )
        return cur.rowcount == 1


def make_job_id(campaign_id: str, trial_id: str, stage: str, seed: int) -> str:
    stage_token = stage.replace("-", "")
    raw = f"job-auto-{campaign_id}-{trial_id}-{stage_token}-s{seed:04d}".lower()
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)
