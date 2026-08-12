"""Production-compatible entry point for Adaptive Dream v8 + NØ + progress-ratcheted planning.

Strict geometry and Prefix Identity instrumentation remain identical to the v6/v7 entry point.
Adaptive Dream still performs the same physical experiments and truth gates; the research optimizer and
progress ratchet only route the bounded extra frontier budget toward falsifiable questions that add new
controls, independent replications, or an explicit route change when a target saturates.
NØ remains a separate stricter meta-control with zero physical givens.
"""
from __future__ import annotations

from typing import Any

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v8
from ai_lab.dream import dry_run
from ai_lab.dream import nothing_genesis
from ai_lab.dream import prefix_audit
from ai_lab.dream import progress_ratchet
from ai_lab.dream import research_optimizer
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream import why_gate
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def _run_adaptive_v8_exact(argv: list[str] | None) -> dict[str, Any]:
    """Run the v8 CLI path while retaining the exact in-memory report for the NØ comparison."""
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
    )


def _print_adaptive_summary(result: dict[str, Any]) -> None:
    r = result["report"]
    root = r.get("pure_genesis_r0") or {}
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
    print(f"  frontier mechanism experiments={int(budget.get('executed', 0))} allocation={budget.get('allocated', {})}")
    if progress:
        print(
            f"  frontier progress={progress.get('status')} "
            f"new_questions={len(progress.get('new_question_keys') or [])} "
            f"replications={len(progress.get('replicated_question_keys') or [])}"
        )
    print(f"  shared portfolio active={len(port.get('active') or [])} runnable={port.get('runnable_focuses', 0)}")
    print("  NOTE: frontier compute is progress-ratcheted; repeated zero-gain routes cool down, F0-F7 remains one reference path.")


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    # Planning-only patches. Physics, gates and evidence definitions remain in their existing modules.
    research_optimizer.install()
    progress_ratchet.install()

    result = _run_adaptive_v8_exact(argv)
    _print_adaptive_summary(result)
    report = result["report"]

    # NØ runs after the ordinary/R0 burst and receives only exact bookkeeping/comparison metadata.
    # It never borrows the burst's state, seed, geometry, law or clock as NØ physics. Persist=True is
    # also used for --no-record because dry_run redirects the audit artifact into runtime/dry-run/.
    nothing_genesis.run_nothing_research(
        burst_id=str(report.get("burst_id") or "unknown-burst"),
        r0_metadata=report.get("pure_genesis_r0") or {},
        persist=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())