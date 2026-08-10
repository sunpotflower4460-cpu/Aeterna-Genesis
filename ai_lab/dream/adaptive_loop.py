"""Adaptive Dream v3: hourly experiments, four-times-daily Research Director.

Every hourly burst gathers evidence.  Only the 03:17 / 09:17 / 15:17 / 21:17 JST bursts are
allowed to change the large search plan.  This separation reduces overreaction to one lucky hour.
Scientific truth remains in deterministic diagnostics; the Director only chooses where to search.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab import lab
from ai_lab.dream import adaptive
from ai_lab.dream import hourly_features as hourly
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
_DECISIONS = _REPO / "ai_lab" / "discoveries" / "research_decisions.json"
_DIRECTOR_HOURS_JST = {3, 9, 15, 21}


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _run_number_from_report(path: Path) -> int:
    """Recover the burst counter from the last completed report.

    dream_state.json is the primary counter, but a lost or rolled-back state must never restart burst
    ids at 0001. That would collide with an existing burst id, reuse its derived seed, and reset the
    2D/native-3D search cursors so already-covered regions are searched again.
    """
    doc = _read_json(path, None)
    if not isinstance(doc, dict):
        return 0
    match = re.search(r"-(\d+)\s*$", str(doc.get("burst_id") or ""))
    return int(match.group(1)) if match else 0


def _next_cycle(cycle: str) -> str:
    return {"A": "B", "B": "C", "C": "D", "D": "A"}.get(cycle, "A")


def _director_due(now: datetime) -> bool:
    return now.astimezone(adaptive.JST).hour in _DIRECTOR_HOURS_JST


def _latest_saved_decision() -> dict[str, Any] | None:
    doc = _read_json(_DECISIONS, {"decisions": []})
    items = doc.get("decisions") or []
    return copy.deepcopy(items[-1]) if items else None


def _held_plan(
    saved: dict[str, Any], *, burst_id: str, cycle: str, trials: int, native3d_trials: int,
) -> dict[str, Any]:
    """Reuse the last Director decision between the four deliberate rethink points."""
    plan = copy.deepcopy(saved)
    plan["burst_id"] = burst_id
    plan["cycle"] = cycle
    plan["observation"] = "前回の大きな見直しで決めた方針を継続し、追加データを集めます。"
    plan["director_rethink_this_burst"] = False
    plan.setdefault("next_plan", {})["mass_2d_trials"] = int(trials)
    plan["next_plan"]["native_3d_trials"] = int(native3d_trials)
    return plan


def _geometry_events(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only split-like observations become durable events; triangles alone stay hypothesis evidence."""
    out: list[dict[str, Any]] = []
    for p in probes:
        if not p.get("fission_like_after_triangle"):
            continue
        key = f"triangle-fission|{p.get('trial_index')}|seed={p.get('seed')}"
        tri = p.get("triangle") or {}
        out.append({
            "event_id": "evt-" + hashlib.sha256(f"RARE_EVENT|{key}".encode()).hexdigest()[:16],
            "kind": "RARE_EVENT",
            "source": "geometry-probe",
            "source_key": key,
            "title": "3つの渦が三角に並んだ後、近くのまとまりが分かれる変化を観測",
            "plain": "自然にできた3つの渦が三角っぽく並んだあと、近くの渦の集まりが2つ以上に分かれるような変化が続けて見えました。",
            "why": "三角形は最初から置いていません。偶然の1回かどうかを別の条件とseedで確かめる候補です。",
            "facts": {
                "trial_index": p.get("trial_index"),
                "family": p.get("family"),
                "knobs": p.get("knobs") or {},
                "seed": p.get("seed"),
                "triangle_score": tri.get("triangle_score"),
                "triangle_regularity": tri.get("regularity"),
                "triangle_charge_pattern": tri.get("charge_pattern"),
                "fission_like_after_triangle": True,
                "biological_cell_division_claim": False,
            },
            "scientific_status": "fission_like_geometry_candidate",
            "visual_interest": "high",
            "room_id": None,
            "parent_room": "room-g001-a",
            "view_preset_id": None,
        })
    return out


def run_adaptive_burst(
    *,
    trials: int = 2048,
    native3d_trials: int = 100,
    workers: int = 4,
    repro_top: int = 8,
    repro_seeds: int = 3,
    compare_native3d_top: int = 12,
    geometry_top: int = 12,
    geometry_broad: int = 12,
    native_variants: int = 1,
    max_jobs: int = 12,
    seed: int | None = None,
    quick: bool = True,
    record: bool = True,
    refresh_app: bool = True,
) -> dict[str, Any]:
    state = load_state()
    run_number = max(int(state.get("run_number", 0)), _run_number_from_report(_LATEST)) + 1
    now = datetime.now(timezone.utc)
    master_seed = int(seed if seed is not None else int(now.strftime("%Y%m%d")) * 100 + run_number)
    burst_id = f"dream-{now.strftime('%Y%m%d')}-{run_number:04d}"
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    cycle = adaptive.cycle_slot(now)
    director_refreshed = _director_due(now)

    previous_report = _read_json(_LATEST, None)
    hypotheses = adaptive.load_hypotheses()
    saved_plan = _latest_saved_decision()
    if director_refreshed or saved_plan is None:
        plan_used = adaptive.build_research_decision(
            previous_report=previous_report,
            hypotheses=hypotheses,
            cycle=cycle,
            burst_id=burst_id,
            trials_2d=trials,
            trials_3d=native3d_trials,
        )
        plan_used["director_rethink_this_burst"] = True
    else:
        plan_used = _held_plan(
            saved_plan, burst_id=burst_id, cycle=cycle,
            trials=trials, native3d_trials=native3d_trials,
        )

    allocation = plan_used["next_plan"]["allocation"]
    focus = plan_used.get("focus")
    history_doc = lab.load_ledger()
    history = list(history_doc.get("search_discoveries", []))
    parent_level = _parent_level()

    mass = adaptive.run_mass_2d(
        start_index=int(state.get("mass_2d_cursor", 0)),
        n=max(0, trials),
        workers=max(1, workers),
        allocation=allocation,
        focus=focus,
        master_seed=master_seed,
        quick=quick,
    )
    stable = [r for r in mass["results"] if r.get("score") is not None]
    selected = stable[:max(0, repro_top)]
    replay = _reproduce(selected, master_seed=master_seed, per_candidate=max(1, repro_seeds), quick=quick)
    search_events: list[dict[str, Any]] = []
    inspect = stable[:max(12, repro_top)]
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

    if record and stable:
        keep = stable[:min(24, len(stable))]
        lab.record_search({"mode": "adaptive-mass", "parent_room": "room-g001-a", "n": len(keep), "results": keep})

    # Direct 3D now uses the SAME five allowed knobs + honest IC families as the expanded 2D Lab.
    # It still starts in 3D from t=0 and is never filtered by a 2D result.
    native3d = hourly.run_full_native_3d(
        start_index=int(state.get("native_3d_cursor", 0)),
        n=max(0, native3d_trials),
        workers=max(1, workers),
        allocation=allocation,
        focus=focus,
        master_seed=master_seed,
        quick=quick,
    )
    paired3d = hourly.compare_full3d_top(
        native3d["results"], top=max(0, compare_native3d_top), workers=max(1, workers)
    )
    native3d_events = adaptive.native3d_events(paired3d, parent_level=parent_level)
    adaptive.record_native3d(native3d_events, burst_id=burst_id)

    # Geometry hypothesis lane: half follows top candidates, half samples broadly to avoid only seeing
    # triangles where the score already told us to look.
    probes = hourly.run_geometry_probes(
        mass["results"], top=max(0, geometry_top), broad=max(0, geometry_broad),
        workers=max(1, workers), quick=quick, seed=master_seed,
    )
    triangle_summary = hourly.geometry_summary(probes)
    geometry_events = _geometry_events(probes)

    # Existing recorded promotion pipeline remains small and human-gated at coarse/full 3D.
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
    events = search_events + native3d_events + geometry_events + autopilot_events
    merge_presets(str(_PRESETS), events)

    report = build_report(
        events,
        burst_id=burst_id,
        expanded_trials=int(mass.get("n", 0)),
        native_jobs=len(native_results),
        generated_at=now.isoformat(),
        executed_job_ids=executed_job_ids,
    )
    report["counts"]["mass_2d_trials"] = int(mass.get("n", 0))
    report["counts"]["native_3d_trials"] = int(native3d.get("n", 0))
    report["counts"]["geometry_probes"] = int(triangle_summary.get("probed", 0))
    report["counts"]["triangle_seen"] = int(triangle_summary.get("triangle_seen", 0))
    report["counts"]["fission_like_after_triangle"] = int(triangle_summary.get("fission_like_after_triangle", 0))
    report["counts"]["experiments"] += int(native3d.get("n", 0))

    atlas = adaptive.load_coverage()
    before = copy.deepcopy(atlas)
    adaptive.update_coverage(atlas, records=mass["results"], dimension="2d", burst_id=burst_id)
    adaptive.update_coverage(atlas, records=native3d["results"], dimension="native_3d", burst_id=burst_id)
    adaptive.save_coverage(atlas)
    coverage = adaptive.coverage_progress(before, atlas)
    native_summary = adaptive.native_summary(native3d["results"], paired3d)
    hypotheses = adaptive.update_hypotheses(hypotheses, burst_id=burst_id, native_summary=native_summary)
    hypotheses = hourly.update_triangle_hypothesis(hypotheses, burst_id=burst_id, summary=triangle_summary)
    progress = adaptive.progress_certificate(coverage=coverage, events=events, native=native_summary)
    if triangle_summary.get("triangle_seen"):
        progress.setdefault("reasons", []).append(f"3つの渦の三角配置を {triangle_summary['triangle_seen']} 件観察した")
    if triangle_summary.get("fission_like_after_triangle"):
        progress.setdefault("reasons", []).append(
            f"三角配置の後の分裂っぽい変化を {triangle_summary['fission_like_after_triangle']} 件観察した"
        )

    # Only four bursts per JST day are allowed to rewrite the large research direction.  Other hourly
    # bursts keep gathering evidence under the last decision.
    if director_refreshed:
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
            "triangle_hypothesis_summary": triangle_summary,
            "progress_certificate": progress,
            "director_rethink_this_burst": True,
        })
        adaptive.save_decision(next_decision)
    else:
        next_decision = copy.deepcopy(plan_used)
        next_decision.update({
            "generated_at": now.isoformat(),
            "based_on_cycle": cycle,
            "coverage_progress": coverage,
            "native_3d_summary": native_summary,
            "triangle_hypothesis_summary": triangle_summary,
            "progress_certificate": progress,
            "director_rethink_this_burst": False,
            "held_until_next_director_cycle": True,
        })

    report["adaptive_research"] = {
        "cycle": cycle,
        "jst_hour": now.astimezone(adaptive.JST).hour,
        "director_refreshed": director_refreshed,
        "director_hours_jst": sorted(_DIRECTOR_HOURS_JST),
        "plan_used": plan_used,
        "coverage_progress": coverage,
        "native_3d": native_summary,
        "triangle_hypothesis": triangle_summary,
        "progress_certificate": progress,
        "next_decision": next_decision,
    }
    report["search"] = {
        "mode": "adaptive-hourly-mass",
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
        "direct_3d_full_knobs": True,
        "direct_3d_ic_families": True,
        "promotion_pipeline_variants": native_variants,
        "promotion_jobs_executed": len(native_results),
        "executed_job_ids": sorted(executed_job_ids),
        "approval_gate": ["coarse-global-3d", "full-3d"],
    }
    report["geometry_honesty"] = {
        "triangle_was_seeded": False,
        "fission_like_equals_cell_division": False,
        "geometry_changes_success_gate": False,
    }

    easy_paths = hourly.write_easy_report(
        report, geometry=triangle_summary, director_refreshed=director_refreshed, stamp=stamp
    )
    report["easy_report_paths"] = easy_paths
    paths = write_report(str(_REPO), report, stamp=stamp)
    _save_event_ledger(event_ledger, events, seen_jobs, burst_id)

    refresh_error = _refresh_observatory() if refresh_app else None
    if refresh_error:
        report["observatory_refresh_warning"] = refresh_error
        Path(paths["latest"]).write_text(json.dumps(report, indent=2, ensure_ascii=False))

    since_director = 0 if director_refreshed else int(state.get("hourly_runs_since_director", 0)) + 1
    state.update({
        "state_version": 3,
        "run_number": run_number,
        "last_burst": burst_id,
        "last_seed": master_seed,
        "last_generated_at": now.isoformat(),
        "last_cycle": cycle,
        "last_director_refresh": now.isoformat() if director_refreshed else state.get("last_director_refresh"),
        "hourly_runs_since_director": since_director,
        "mass_2d_cursor": int(mass["next_index"]),
        "native_3d_cursor": int(native3d["next_index"]),
    })
    save_state(state)
    return {"report": report, "paths": paths, "easy_paths": easy_paths, "native_results": native_results}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna Adaptive Dream v3 — hourly evidence, 4x/day Director")
    ap.add_argument("--trials", type=int, default=2048)
    ap.add_argument("--native3d-trials", type=int, default=100)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--repro-top", type=int, default=8)
    ap.add_argument("--repro-seeds", type=int, default=3)
    ap.add_argument("--compare-native3d-top", type=int, default=12)
    ap.add_argument("--geometry-top", type=int, default=12)
    ap.add_argument("--geometry-broad", type=int, default=12)
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
        compare_native3d_top=max(0, a.compare_native3d_top),
        geometry_top=max(0, a.geometry_top), geometry_broad=max(0, a.geometry_broad),
        native_variants=max(0, a.native_variants), max_jobs=max(0, a.max_jobs),
        seed=a.seed, quick=a.quick, record=not a.no_record, refresh_app=not a.no_refresh_app,
    )
    r = result["report"]
    c = r["counts"]
    ar = r["adaptive_research"]
    tri = ar["triangle_hypothesis"]
    print(f"=== Aeterna Adaptive Dream v3: {r['burst_id']} ===")
    print(f"  2D={c['mass_2d_trials']} direct-3D={c['native_3d_trials']} geometry-probes={tri['probed']}")
    print(f"  director-refreshed={ar['director_refreshed']} new-regions={ar['coverage_progress']['new_regions']}")
    print(f"  triangle={tri['triangle_seen']} fission-like={tri['fission_like_after_triangle']}")
    print(f"  easy-report: {result['easy_paths']['markdown']}")
    print("  NOTE: triangles are observed, never seeded; fission-like is not a biological cell-division claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
