"""Production entry point for Adaptive Dream v8 + NØ + durable epistemic routing.

Strict geometry and Prefix Identity instrumentation remain identical to the existing entry point.
Adaptive Research Yield chooses informative frontier lanes; Progress Ratchet adds durable no-repeat and
route-escape planning from Research Memory. Context-aware X identity prevents a changed start-side search
focus from being mistaken for an already-tested question. None changes physics, truth gates, Rooms or
official Levels.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v8
from ai_lab.dream import dry_run
from ai_lab.dream import environment_fingerprint
from ai_lab.dream import nothing_genesis
from ai_lab.dream import prefix_audit
from ai_lab.dream import progress_context
from ai_lab.dream import progress_ratchet
from ai_lab.dream import protocol_fingerprint
from ai_lab.dream import research_optimizer
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream import why_gate
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry

_REPO = Path(__file__).resolve().parents[2]
_FRONTIER_ALIAS = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"


def _run_adaptive_v8_exact(argv: list[str] | None) -> dict[str, Any]:
    a = adaptive_v8.build_parser().parse_args(argv)
    if a.no_record:
        dry_run.activate()
    return adaptive_v8.run_adaptive_v8(
        trials=max(0, a.trials), native3d_trials=max(0, a.native3d_trials), workers=max(1, a.workers),
        repro_top=max(0, a.repro_top), repro_seeds=max(1, a.repro_seeds),
        compare_native3d_top=max(0, a.compare_native3d_top), geometry_top=max(0, a.geometry_top),
        geometry_broad=max(0, a.geometry_broad), native_variants=max(0, a.native_variants),
        max_jobs=max(0, a.max_jobs), seed=a.seed, quick=a.quick,
        record=not a.no_record, refresh_app=(not a.no_refresh_app and not a.no_record),
        followup_trials_2d=max(0, a.followup_trials_2d), followup_trials_3d=max(0, a.followup_trials_3d),
        followup_max_leads=max(0, a.followup_max_leads),
        fission_path_trials_2d=max(0, a.fission_path_trials_2d),
        fission_path_max_leads=max(0, a.fission_path_max_leads),
        deep_time_max_leads=max(0, a.deep_time_max_leads),
        open_ended_probes=max(0, a.open_ended_probes),
        open_ended_max_episodes=max(0, a.open_ended_max_episodes),
        unknown_followup_max_patterns=max(0, a.unknown_followup_max_patterns),
        max_synthesized_hypotheses=max(0, a.max_synthesized_hypotheses),
        root_law_trials=max(0, a.root_law_trials), root_sizes=adaptive_v8._parse_sizes(a.root_sizes),
        root_steps=max(8, a.root_steps), frontier_experiments=max(0, a.frontier_experiments),
        emergent_field_trials=max(0, a.emergent_field_trials),
    )


def _publish_frontier_alias(report: dict[str, Any]) -> None:
    frontier = report.get("autonomous_frontier_expansion") or {}
    if not frontier:
        return
    _FRONTIER_ALIAS.parent.mkdir(parents=True, exist_ok=True)
    _FRONTIER_ALIAS.write_text(json.dumps(frontier, indent=2, ensure_ascii=False))


def _publish_dry_run_progress_memory(report: dict[str, Any]) -> None:
    """Keep --no-record auditable by writing durable-question memory only into redirected scratch."""
    if not dry_run.is_active():
        return
    frontier = report.get("autonomous_frontier_expansion") or {}
    progress = frontier.get("progress_ratchet") or {}
    keys = progress.get("question_keys") or []
    if keys:
        progress_ratchet._persist_question_memory(
            keys, burst_id=str(report.get("burst_id") or "unknown-burst")
        )


def _print_adaptive_summary(result: dict[str, Any]) -> None:
    r = result["report"]
    root = r.get("pure_genesis_r0") or {}
    field = r.get("emergent_field_frontier") or {}
    port = r.get("hypothesis_portfolio_v7") or {}
    frontier = r.get("autonomous_frontier_expansion") or {}
    critic = (root.get("root_integrity_audit") or {}).get("critic_questions") or []
    budget = frontier.get("budget") or {}
    progress = frontier.get("progress_ratchet") or {}
    print(f"=== Aeterna Adaptive Dream v8: {r['burst_id']} ===")
    print(f"  R0: {why_gate.ROOT_STATEMENT}")
    print(f"  Pure Genesis laws={root.get('law_trials', 0)} top={len(root.get('top_laws') or [])}")
    print(f"  Why Gate accepted={int((root.get('why_gate') or {}).get('accepted', 0))} unexplained physical givens=0")
    print(f"  Root Integrity critic questions={len(critic)} permutation-quotient=True")
    print(
        f"  emergent-field trials={int(field.get('trials') or 0)} "
        f"stable={int((field.get('counts') or {}).get('stable') or 0)}"
    )
    print(
        f"  frontier mechanism experiments={int(budget.get('executed', 0))} "
        f"allocation={budget.get('allocated', {})}"
    )
    if progress:
        print(
            f"  progress={progress.get('status')} new_questions={len(progress.get('new_question_keys') or [])} "
            f"replications={len(progress.get('replicated_question_keys') or [])} "
            f"escape_next={bool(progress.get('next_burst_escape_required'))}"
        )
    print(f"  shared portfolio active={len(port.get('active') or [])} runnable={port.get('runnable_focuses', 0)}")
    print("  NOTE: uniform-field morphology is observation-only; no node/edge/network is seeded or claimed.")
    print("  NOTE: Research Memory prevents routine exact-repeat drift; F0-F7 remains one human-written reference path.")


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    research_optimizer.install()
    progress_ratchet.install()
    progress_context.install()

    result = _run_adaptive_v8_exact(argv)
    _print_adaptive_summary(result)
    report = result["report"]
    burst_id = str(report.get("burst_id") or "unknown-burst")
    _publish_frontier_alias(report)
    _publish_dry_run_progress_memory(report)

    nothing_genesis.run_nothing_research(
        burst_id=burst_id,
        r0_metadata=report.get("pure_genesis_r0") or {},
        persist=True,
    )
    # Persist the exact recognized parser configuration used by this process. If argv is None the
    # fingerprint parser reads this process' sys.argv, including parser defaults. dry_run redirects it.
    protocol_fingerprint.run(burst_id=burst_id, argv=argv, persist=True)
    # Capture the actual package/BLAS/interpreter environment in the same research process. In
    # --no-record mode dry_run redirects this write into scratch, preserving the tracked tree.
    environment_fingerprint.run(burst_id=burst_id, persist=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())