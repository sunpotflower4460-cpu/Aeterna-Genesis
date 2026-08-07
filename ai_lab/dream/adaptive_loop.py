"""Dream Loop v2: mass 2D + direct native 3D + adaptive Research Director.

This is a separate entry point so Dream Loop v1 remains a stable fallback.  Each burst uses the
previous report to choose a bounded search mix, runs direct 3D independently of 2D, compresses
mundane trials into Coverage Atlas, then writes the "this happened -> next try this" decision.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab import lab
from ai_lab.dream import adaptive
from ai_lab.dream.events import classify_search_candidate
from ai_lab.dream.loop import (
    _EVENT_LEDGER,
    _PRESETS,
    _candidate_key,
    _executed_job_ids,
    _load_event_ledger,
    _new_autopilot_events,
    _parent_level,
    _refresh_observatory,
    _reproduce,
    _run_native_lane,
    _save_event_ledger,
    load_state,
    save_state,
)
from ai_lab.dream.presets import merge_presets
from ai_lab.dream.report import build_report, write_report

_REPO = Path(__file__).resolve().parents[2]
_LATEST = _REPO / "ai_lab" / "reports" / "nightly" / "latest.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _next_cycle(cycle: str) -> str:
    return {"A": "B", "B": "C", "C": "D", "D": "A"}.get(cycle, "A")


def run_adaptive_burst(
    *,
    trials: int = 2048,
    native3d_trials: int = 100,
    workers: int = 4,
    repro_top: int = 8,
    repro_seeds: int = 3,
    compare_native3d_top: int = 12,
    native_variants: int = 1,
    max_jobs: int = 12,
    seed: int | None = None,
    quick: bool = True,
    record: bool = True,
    refresh_app: bool = True,
) -> dict[str, Any]:
    state = load_state()
    run_number = int(state.get("run_number", 0)) + 1
    now = datetime.now(timezone.utc)
    master_seed = int(seed if seed is not None else int(now.strftime("%Y%m%d")) * 100 + run_number)
    burst_id = f"dream-{now.strftime('%Y%m%d')}-{run_number:04d}"
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    cycle = adaptive.cycle_slot(now)

    previous_report = _read_json(_LATEST, None)
    hypotheses = adaptive.load_hypotheses()
    plan_used = adaptive.build_research_decision(
        previous_report=previous_report,
        hypotheses=hypotheses,
        cycle=cycle,
        burst_id=burst_id,
        trials_2d=trials,
        trials_3d=native3d_trials,
    )

    history_doc = lab.load_ledger()
    history = list(history_doc.get("search_discoveries", []))
    parent_level = _parent_level()

    mass = adaptive.run_mass_2d(
        start_index=int(state.get("mass_2d_cursor", 0)),
        n=max(0, trials),
        workers=max(1, workers),
        allocation=plan_used["next_plan"]["allocation"],
        focus=plan_used.get("focus"),
        master_seed=master_seed,
        quick=quick,
    )
    stable = [r for r in mass["results"] if r.get("score") is not None]
    selected = stable[: max(0, repro_top)]
    replay = _reproduce(selected, master_seed=master_seed, per_candidate=max(1, repro_seeds), quick=quick)
    search_events: list[dict[str, Any]] = []
    inspect = stable[: max(12, repro_top)]
    warnings = [r for r in mass["results"] if r.get("score") is None][:3]
    for rec in inspect + warnings:
        search_events.extend(
            classify_search_candidate(
                rec,
                parent_level=parent_level,
                history=history,
                reruns=replay.get(_candidate_key(rec)),
            )
        )

    # Persist only the leading stable observations for novelty/reproduction memory.  Mundane/negative
    # mass trials are represented by Coverage Atlas instead of thousands of ledger rows/files.
    if record and stable:
        keep = stable[: min(24, len(stable))]
        lab.record_search({"mode": "adaptive-mass", "parent_room": "room-g001-a", "n": len(keep), "results": keep})

    native3d = adaptive.run_native_3d(
        start_index=int(state.get("native_3d_cursor", 0)),
        n=max(0, native3d_trials),
        workers=max(1, workers),
        master_seed=master_seed,
        quick=quick,
    )
    paired3d = adaptive.compare_native3d_top(native3d["results"], top=max(0, compare_native3d_top), workers=max(1, workers))
    native3d_events = adaptive.native3d_events(paired3d, parent_level=parent_level)
    adaptive.record_native3d(native3d_events, burst_id=burst_id)

    # Keep the existing promotion pipeline alive, but small.  This is separate from the direct-3D lane:
    # direct 3D is discovery; orchestrator remains the recorded 2D->3D promotion chain with human gates.
    native_results = _run_native_lane(
        campaign_id=burst_id,
        seed=master_seed,
        variant_count=max(0, native_variants),
        repro_seeds=max(1, repro_seeds),
        quick=quick,
        max_jobs=max(0, max_jobs),
    ) if native_variants > 0 and max_jobs > 0 else []
    executed_job_ids = _executed_job_ids(native_results)

    event_ledger = _load_event_ledger()
    autopilot_events, seen_jobs = _new_autopilot_events(event_ledger)
    events = search_events + native3d_events + autopilot_events
    merge_presets(str(_PRESETS), events)

    report = build_report(
        events,
        burst_id=burst_id,
        expanded_trials=int(mass.get("n", 0)),
        native_jobs=len(native_results),
        generated_at=now.isoformat(),
        executed_job_ids=executed_job_ids,
    )
    # build_report predates the independent Native 3D lane; preserve compatibility and add explicit counts.
    report["counts"]["mass_2d_trials"] = int(mass.get("n", 0))
    report["counts"]["native_3d_trials"] = int(native3d.get("n", 0))
    report["counts"]["experiments"] += int(native3d.get("n", 0))

    atlas = adaptive.load_coverage()
    before = copy.deepcopy(atlas)
    adaptive.update_coverage(atlas, records=mass["results"], dimension="2d", burst_id=burst_id)
    adaptive.update_coverage(atlas, records=native3d["results"], dimension="native_3d", burst_id=burst_id)
    adaptive.save_coverage(atlas)
    coverage = adaptive.coverage_progress(before, atlas)
    native_summary = adaptive.native_summary(native3d["results"], paired3d)
    hypotheses = adaptive.update_hypotheses(hypotheses, burst_id=burst_id, native_summary=native_summary)
    progress = adaptive.progress_certificate(coverage=coverage, events=events, native=native_summary)

    # This is the actual "that happened, therefore next do this" step.  It sees the current measured report,
    # updated Coverage Atlas and updated hypotheses, and prepares the next cycle without changing truth gates.
    next_decision = adaptive.build_research_decision(
        previous_report=report,
        hypotheses=hypotheses,
        cycle=_next_cycle(cycle),
        burst_id=burst_id,
        trials_2d=trials,
        trials_3d=native3d_trials,
    )
    next_decision.update({
        "generated_at": now.isoformat(),
        "based_on_cycle": cycle,
        "coverage_progress": coverage,
        "native_3d_summary": native_summary,
        "progress_certificate": progress,
    })
    adaptive.save_decision(next_decision)

    report["adaptive_research"] = {
        "cycle": cycle,
        "plan_used": plan_used,
        "coverage_progress": coverage,
        "native_3d": native_summary,
        "progress_certificate": progress,
        "next_decision": next_decision,
    }
    report["search"] = {
        "mode": "adaptive-mass",
        "master_seed": master_seed,
        "parent_level": parent_level,
        "reproduction_top": repro_top,
        "reproduction_seeds": repro_seeds,
        "mass_2d_cursor": [int(state.get("mass_2d_cursor", 0)), int(mass["next_index"])],
        "native_3d_cursor": [int(state.get("native_3d_cursor", 0)), int(native3d["next_index"])],
    }
    report["native_lane"] = {
        "direct_3d_trials": int(native3d.get("n", 0)),
        "direct_3d_is_gated_by_2d": False,
        "promotion_pipeline_variants": native_variants,
        "promotion_jobs_executed": len(native_results),
        "executed_job_ids": sorted(executed_job_ids),
        "approval_gate": ["coarse-global-3d", "full-3d"],
    }

    paths = write_report(str(_REPO), report, stamp=stamp)
    _save_event_ledger(event_ledger, events, seen_jobs, burst_id)
    refresh_error = _refresh_observatory() if refresh_app else None
    if refresh_error:
        report["observatory_refresh_warning"] = refresh_error
        Path(paths["latest"]).write_text(json.dumps(report, indent=2, ensure_ascii=False))

    state.update({
        "state_version": 2,
        "run_number": run_number,
        "last_burst": burst_id,
        "last_seed": master_seed,
        "last_generated_at": now.isoformat(),
        "last_cycle": cycle,
        "mass_2d_cursor": int(mass["next_index"]),
        "native_3d_cursor": int(native3d["next_index"]),
    })
    save_state(state)
    return {"report": report, "paths": paths, "native_results": native_results}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna Adaptive Dream Cycle v2")
    ap.add_argument("--trials", type=int, default=2048)
    ap.add_argument("--native3d-trials", type=int, default=100)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--repro-top", type=int, default=8)
    ap.add_argument("--repro-seeds", type=int, default=3)
    ap.add_argument("--compare-native3d-top", type=int, default=12)
    ap.add_argument("--native-variants", type=int, default=1)
    ap.add_argument("--max-jobs", type=int, default=12)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--no-refresh-app", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    result = run_adaptive_burst(
        trials=max(0, a.trials), native3d_trials=max(0, a.native3d_trials), workers=max(1, a.workers),
        repro_top=max(0, a.repro_top), repro_seeds=max(1, a.repro_seeds),
        compare_native3d_top=max(0, a.compare_native3d_top), native_variants=max(0, a.native_variants),
        max_jobs=max(0, a.max_jobs), seed=a.seed, quick=a.quick,
        record=not a.no_record, refresh_app=not a.no_refresh_app,
    )
    r = result["report"]; c = r["counts"]; ar = r["adaptive_research"]
    print(f"=== Aeterna Adaptive Dream: {r['burst_id']} / Cycle {ar['cycle']} ===")
    print(f"  2D={c['mass_2d_trials']} direct-3D={c['native_3d_trials']} orchestrator-jobs={c['native_jobs']}")
    print(f"  progress={ar['progress_certificate']['status']} new-regions={ar['coverage_progress']['new_regions']}")
    print(f"  dimension-emergence={ar['native_3d']['dimension_emergence']}/{ar['native_3d']['paired_compared']} paired top candidates")
    if r.get("headline"): print(f"  headline: {r['headline']['title']}")
    print(f"  next: {ar['next_decision']['observation']}")
    print("  NOTE: Research Director chooses search direction only; success gates and official Rooms remain human/deterministic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
