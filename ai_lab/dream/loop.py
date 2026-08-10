#!/usr/bin/env python3
"""Bounded autonomous research burst for Aeterna-Genesis.

Dream Loop v1 deliberately reuses the repository's existing research engines:

* `ai_lab.lab.search` performs broad 2D start-condition exploration.
* selected 2D candidates are replayed with fresh seeds for reproduction evidence.
* `genesis_orchestrator` runs a small runner-native lane through 2D -> local 3D and then
  stops at the existing human approval gates for coarse/full 3D.
* measured outcomes are translated into Event Ledger records, Night Reports, and
  observation presets.

It never changes success thresholds and never writes `rooms/official/`.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from ai_lab import lab  # noqa: E402
from ai_lab.dream.events import classify_search_candidate, events_from_autopilot  # noqa: E402
from ai_lab.dream.presets import merge_presets  # noqa: E402
from ai_lab.dream.report import build_report, write_report  # noqa: E402
from genesis_orchestrator import campaign, db, worker  # noqa: E402

# The burst counter and the 2D/native-3D search cursors must survive an Actions cache miss, so
# they live in a git-tracked path. Only genuinely disposable runtime artifacts stay under runtime/.
_STATE = _REPO / "ai_lab" / "discoveries" / "dream_state.json"
_LEGACY_STATE = _REPO / "runtime" / "dream" / "state.json"
_DB = _REPO / "runtime" / "dream" / "dream.sqlite3"
_EVENT_LEDGER = _REPO / "ai_lab" / "discoveries" / "event_ledger.json"
_PRESETS = _REPO / "ai_lab" / "discoveries" / "view_presets.json"
_AUTOPILOT = _REPO / "ai_lab" / "discoveries" / "autopilot_ledger.json"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    os.replace(tmp, path)


def load_state() -> dict[str, Any]:
    """Load the Dream counter/cursor state.

    The tracked file is authoritative. The legacy runtime/ copy is still read when the tracked
    file does not exist yet, so migrating does not restart run_number or the search cursors.
    """
    default = {"state_version": 1, "run_number": 0}
    if _STATE.exists():
        return _load_json(_STATE, default)
    return _load_json(_LEGACY_STATE, default)


def save_state(state: dict[str, Any]) -> None:
    _atomic_json(_STATE, state)


def _parent_level() -> int:
    p = _REPO / "rooms" / "official" / "room-g001-a" / "emergence.json"
    if p.exists():
        return int(json.loads(p.read_text()).get("reached_level") or 0)
    return 0


def _load_event_ledger() -> dict[str, Any]:
    return _load_json(
        _EVENT_LEDGER,
        {
            "ledger_version": 1,
            "note": "Dream Loop human-facing events. Measurements remain in their source ledgers.",
            "seen_job_ids": [],
            "events": [],
        },
    )


def _save_event_ledger(ledger: dict[str, Any], new_events: list[dict[str, Any]], seen: set[str], burst_id: str) -> None:
    by_id = {e["event_id"]: e for e in ledger.get("events", []) if e.get("event_id")}
    for event in new_events:
        by_id[event["event_id"]] = event
    ledger["events"] = sorted(by_id.values(), key=lambda e: e["event_id"])
    ledger["seen_job_ids"] = sorted(seen)
    ledger["last_burst"] = burst_id
    _atomic_json(_EVENT_LEDGER, ledger)


def _reproduce(candidates: list[dict[str, Any]], *, master_seed: int, per_candidate: int, quick: bool) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for i, cand in enumerate(candidates):
        key = _candidate_key(cand)
        reruns: list[dict[str, Any]] = []
        for j in range(per_candidate):
            seed = 100_000 + (master_seed % 800_000) + i * 100 + j
            r = lab._screen_ic(cand["family"], cand["knobs"], seed, quick=quick)  # internal Lab replay, same diagnostics
            reruns.append({**r, "seed": seed})
        out[key] = reruns
    return out


def _candidate_key(rec: dict[str, Any]) -> str:
    knobs = json.dumps(rec.get("knobs") or {}, sort_keys=True, separators=(",", ":"))
    return f"{rec.get('family')}|{knobs}|seed={rec.get('seed')}"


def _native_campaign_doc(*, campaign_id: str, seed: int, variant_count: int, repro_seeds: int, quick: bool) -> dict[str, Any]:
    """Small runner-native lane: only knobs the common Runner truly applies.

    This lane exists so some Dream discoveries become recorded candidate Rooms that the Observatory
    can actually replay.  The broader AI Lab keeps exploring the larger start-condition space in 2D.
    """
    rng = random.Random(seed)
    noise = [1.0e-4, 3.0e-4, 1.0e-3, 3.0e-3, 1.0e-2]
    quench = [4.0, 6.0, 8.0, 12.0, 16.0]
    pairs = [(n, q) for n in noise for q in quench]
    rng.shuffle(pairs)
    variants = [
        {"label": f"native-{i:02d}", "overrides": {"noise_amplitude": n, "quench_duration": q}}
        for i, (n, q) in enumerate(pairs[: max(1, variant_count)])
    ]
    seeds = [int((seed + 7000 + i) % 1_000_000) for i in range(max(1, repro_seeds))]
    return {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "title": "Dream Loop native lane — recorded 2D to gated 3D",
        "parent_room": "room-g001-a",
        "quick": bool(quick),
        "seeds": seeds,
        "min_reached_level": 1,
        "stages": ["2d-screen", "local-3d", "coarse-global-3d", "full-3d"],
        "approval_required": ["coarse-global-3d", "full-3d"],
        "hypotheses": [
            {
                "id": "native-window",
                "statement": (
                    "A runner-native noise/quench condition may preserve measured emergence when "
                    "transferred from 2D to local 3D; coarse/full 3D remain human-gated."
                ),
                "search": {"variants": variants},
            }
        ],
    }


def _run_native_lane(
    *,
    campaign_id: str,
    seed: int,
    variant_count: int,
    repro_seeds: int,
    quick: bool,
    max_jobs: int,
) -> list[dict[str, Any]]:
    if variant_count <= 0 or max_jobs <= 0:
        return []
    doc = _native_campaign_doc(
        campaign_id=campaign_id,
        seed=seed,
        variant_count=variant_count,
        repro_seeds=repro_seeds,
        quick=quick,
    )
    cdir = _REPO / "runtime" / "dream" / "campaigns"
    cdir.mkdir(parents=True, exist_ok=True)
    path = cdir / f"{campaign_id}.yaml"
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))
    db.init_db(_DB)
    campaign.submit(path, _DB, root=_REPO)
    return worker.work_until_idle(_DB, root=_REPO, max_jobs=max_jobs, refresh=False)


def _new_autopilot_events(event_ledger: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
    doc = _load_json(_AUTOPILOT, {"discoveries": []})
    return events_from_autopilot(
        doc.get("discoveries", []),
        seen_job_ids=set(event_ledger.get("seen_job_ids", [])),
    )


def _executed_job_ids(native_results: list[dict[str, Any]]) -> set[str]:
    """Return the exact orchestrator jobs processed during this worker burst.

    The persistent queue may carry jobs from an earlier Dream campaign. Those are still part of what
    happened *tonight* if this worker executed them, so the Night Report should follow execution rather
    than campaign creation time.
    """
    out: set[str] = set()
    for result in native_results:
        job = result.get("job") or {}
        if job.get("job_id"):
            out.add(str(job["job_id"]))
    return out


def _refresh_observatory() -> str | None:
    """Refresh catalog/data once after the burst. Failure is reported but does not erase research."""
    try:
        subprocess.run([sys.executable, str(_REPO / "tools" / "build_catalog.py")], cwd=_REPO, check=True)
        subprocess.run([sys.executable, str(_REPO / "tools" / "collect_app_data.py")], cwd=_REPO, check=True)
        return None
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"


def run_burst(
    *,
    mode: str = "random",
    trials: int = 32,
    repro_top: int = 3,
    repro_seeds: int = 3,
    native_variants: int = 3,
    max_jobs: int = 12,
    seed: int | None = None,
    quick: bool = True,
    record: bool = True,
    native: bool = True,
    refresh_app: bool = True,
) -> dict[str, Any]:
    state = load_state()
    run_number = int(state.get("run_number", 0)) + 1
    now = datetime.now(timezone.utc)
    master_seed = int(seed if seed is not None else int(now.strftime("%Y%m%d")) * 100 + run_number)
    burst_id = f"dream-{now.strftime('%Y%m%d')}-{run_number:04d}"
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")

    discovery_before = lab.load_ledger()
    history = list(discovery_before.get("search_discoveries", []))
    parent_level = _parent_level()
    search_events: list[dict[str, Any]] = []
    search_result: dict[str, Any] = {"results": [], "n": 0}

    if trials > 0:
        search_result = lab.search(mode=mode, n=trials, parent="g001", seed=master_seed, quick=quick)
        stable = [r for r in search_result["results"] if r.get("score") is not None]
        selected = stable[: max(0, repro_top)]
        replay = _reproduce(selected, master_seed=master_seed, per_candidate=repro_seeds, quick=quick)
        # Keep the current report readable: classify the leading discoveries + numerical warnings, not every mundane trial.
        inspect = stable[: max(8, repro_top)]
        warnings = [r for r in search_result["results"] if r.get("score") is None][:3]
        for rec in inspect + warnings:
            reruns = replay.get(_candidate_key(rec))
            search_events.extend(
                classify_search_candidate(
                    rec,
                    parent_level=parent_level,
                    history=history,
                    reruns=reruns,
                )
            )
        if record:
            lab.record_search(search_result)

    native_results: list[dict[str, Any]] = []
    if native:
        native_results = _run_native_lane(
            campaign_id=burst_id,
            seed=master_seed,
            variant_count=native_variants,
            repro_seeds=repro_seeds,
            quick=quick,
            max_jobs=max_jobs,
        )
    executed_job_ids = _executed_job_ids(native_results)

    event_ledger = _load_event_ledger()
    autopilot_events, seen_jobs = _new_autopilot_events(event_ledger)
    events = search_events + autopilot_events
    # Assign/merge observation presets before the report so cards can point at them.
    merge_presets(str(_PRESETS), events)

    report = build_report(
        events,
        burst_id=burst_id,
        expanded_trials=int(search_result.get("n", 0)),
        native_jobs=len(native_results),
        generated_at=now.isoformat(),
        executed_job_ids=executed_job_ids,
    )
    report["search"] = {
        "mode": mode,
        "master_seed": master_seed,
        "parent_level": parent_level,
        "reproduction_top": repro_top,
        "reproduction_seeds": repro_seeds,
    }
    report["native_lane"] = {
        "enabled": native,
        "variants": native_variants if native else 0,
        "jobs_executed": len(native_results),
        "executed_job_ids": sorted(executed_job_ids),
        "approval_gate": ["coarse-global-3d", "full-3d"],
    }
    paths = write_report(str(_REPO), report, stamp=stamp)
    _save_event_ledger(event_ledger, events, seen_jobs, burst_id)

    refresh_error = _refresh_observatory() if refresh_app else None
    if refresh_error:
        report["observatory_refresh_warning"] = refresh_error
        _atomic_json(Path(paths["latest"]), report)

    state.update(
        {
            "state_version": 1,
            "run_number": run_number,
            "last_burst": burst_id,
            "last_seed": master_seed,
            "last_generated_at": now.isoformat(),
        }
    )
    save_state(state)
    return {"report": report, "paths": paths, "native_results": native_results}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna Dream Loop — bounded autonomous research burst")
    ap.add_argument("--mode", choices=["random", "grid", "evolutionary"], default="random")
    ap.add_argument("--trials", type=int, default=32, help="expanded AI Lab 2D trials")
    ap.add_argument("--repro-top", type=int, default=3, help="top expanded candidates replayed with fresh seeds")
    ap.add_argument("--repro-seeds", type=int, default=3)
    ap.add_argument("--native-variants", type=int, default=3, help="runner-native variants eligible for recorded 3D lane")
    ap.add_argument("--max-jobs", type=int, default=12, help="hard job-count budget for genesis_orchestrator")
    ap.add_argument("--seed", type=int, default=None, help="optional deterministic master seed")
    ap.add_argument("--quick", action="store_true", help="use repository quick grids/step counts")
    ap.add_argument("--no-record", action="store_true", help="do not update AI Lab search ledger")
    ap.add_argument("--no-native", action="store_true", help="skip the recorded runner-native 2D->3D lane")
    ap.add_argument("--no-refresh-app", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_burst(
        mode=args.mode,
        trials=max(0, args.trials),
        repro_top=max(0, args.repro_top),
        repro_seeds=max(1, args.repro_seeds),
        native_variants=max(0, args.native_variants),
        max_jobs=max(0, args.max_jobs),
        seed=args.seed,
        quick=args.quick,
        record=not args.no_record,
        native=not args.no_native,
        refresh_app=not args.no_refresh_app,
    )
    report = result["report"]
    c = report["counts"]
    print("=== Aeterna Dream Loop: %s ===" % report["burst_id"])
    print("  experiments/jobs=%d new=%d reproduced=%d promotion-ready=%d dimension-fail=%d warnings=%d"
          % (c["experiments"], c["new_behavior"], c["reproduced"], c["promotion_ready"],
             c["dimension_failure"], c["numerical_warning"]))
    if report.get("headline"):
        print("  headline: %s" % report["headline"]["title"])
        print("            %s" % report["headline"]["plain"])
    print("  report: %s" % os.path.relpath(result["paths"]["markdown"], _REPO))
    print("  NOTE: Dream Loop cannot write rooms/official; coarse/full 3D remain human-gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
