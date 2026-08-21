"""Production entry point for Adaptive Dream v8 + NØ + durable epistemic routing.

Strict geometry and Prefix Identity instrumentation remain identical to the existing entry point.
Adaptive Research Yield chooses informative frontier lanes; Progress Ratchet adds durable no-repeat and
route-escape planning from Research Memory. Context-aware X identity prevents a changed start-side search
focus from being mistaken for an already-tested question. Mature recurrent X-patterns also receive a
persistent paired-control mechanism-dissection lane so recurrence count does not become the research goal.
Pure Genesis relation states additionally receive observation-only metric/identity/lineage instruments;
these never alter root dynamics, law ranking, truth gates, Rooms or official Levels.
"""
from __future__ import annotations

import json
import os
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
from ai_lab.dream import relation_instrument_adapter
from ai_lab.dream import research_optimizer
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream import why_gate
from ai_lab.dream import x_mechanism_discovery
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


def _write_json_if_present(path_value: Any, payload: dict[str, Any]) -> None:
    if not path_value:
        return
    path = Path(str(path_value))
    if not path.exists() or not path.is_file():
        return
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _x_mechanism_budget() -> int:
    profile = str(os.environ.get("AETERNA_EXPLORATION_PROFILE") or "baseline").lower()
    return {
        "native3d": 2,
        "novelty": 6,
        "mechanism": 12,
        "baseline": 4,
    }.get(profile, 4)


def _attach_x_mechanism(result: dict[str, Any]) -> dict[str, Any]:
    """Attach additive mechanism evidence without mutating historical X fingerprints or strict gates."""
    report = result["report"]
    burst_id = str(report.get("burst_id") or "unknown-burst")
    mechanism = x_mechanism_discovery.run_mechanism_discovery(
        burst_id=burst_id,
        budget=_x_mechanism_budget(),
        persist=True,
    )
    report["x_mechanism_discovery"] = mechanism
    frontier = report.setdefault("autonomous_frontier_expansion", {})
    if isinstance(frontier, dict):
        frontier["x_identity_mechanism"] = mechanism

    paths = result.get("paths") or {}
    _write_json_if_present(paths.get("latest"), report)
    _write_json_if_present(paths.get("json"), report)

    easy_paths = result.get("easy_paths") or {}
    latest_easy_value = easy_paths.get("latest")
    if latest_easy_value:
        latest_easy = Path(str(latest_easy_value))
        easy: dict[str, Any] | None = None
        if latest_easy.exists() and latest_easy.is_file():
            try:
                easy = json.loads(latest_easy.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                easy = None
        if isinstance(easy, dict):
            easy["x_mechanism_discovery"] = {
                "pattern_id": mechanism.get("pattern_id"),
                "observations_seen": mechanism.get("observations_seen"),
                "experiments": mechanism.get("experiments"),
                "status": mechanism.get("status"),
                "leading_explanation": mechanism.get("leading_explanation"),
                "leading_sensitivity_candidate": mechanism.get("leading_sensitivity_candidate"),
                "next_question": mechanism.get("next_question"),
                "counts_as_strict_zero_evidence": False,
                "policy": mechanism.get("policy") or {},
            }
            latest_easy.write_text(json.dumps(easy, indent=2, ensure_ascii=False), encoding="utf-8")
            _write_json_if_present(easy_paths.get("json"), easy)
    return mechanism


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
    relation_instruments = root.get("relation_instrument_summary") or {}
    field = r.get("emergent_field_frontier") or {}
    port = r.get("hypothesis_portfolio_v7") or {}
    frontier = r.get("autonomous_frontier_expansion") or {}
    mechanism = r.get("x_mechanism_discovery") or {}
    critic = (root.get("root_integrity_audit") or {}).get("critic_questions") or []
    budget = frontier.get("budget") or {}
    progress = frontier.get("progress_ratchet") or {}
    print(f"=== Aeterna Adaptive Dream v8: {r['burst_id']} ===")
    print(f"  R0: {why_gate.ROOT_STATEMENT}")
    print(f"  Pure Genesis laws={root.get('law_trials', 0)} top={len(root.get('top_laws') or [])}")
    print(f"  Why Gate accepted={int((root.get('why_gate') or {}).get('accepted', 0))} unexplained physical givens=0")
    print(f"  Root Integrity critic questions={len(critic)} permutation-quotient=True")
    if relation_instruments:
        caps = relation_instruments.get("capabilities") or {}
        print(
            "  relation instruments="
            f"metric:{(caps.get('emergent_metric_geometry') or {}).get('instrument_status')} "
            f"identity:{(caps.get('persistent_individual_identity') or {}).get('instrument_status')} "
            f"lineage:{(caps.get('division_with_inheritance') or {}).get('instrument_status')}"
        )
    print(
        f"  emergent-field trials={int(field.get('trials') or 0)} "
        f"stable={int((field.get('counts') or {}).get('stable') or 0)}"
    )
    print(
        f"  frontier mechanism experiments={int(budget.get('executed', 0))} "
        f"allocation={budget.get('allocated', {})}"
    )
    if mechanism.get("ran"):
        print(
            f"  X why-lane pattern={mechanism.get('pattern_id')} "
            f"experiments={mechanism.get('experiments', 0)} status={mechanism.get('status')}"
        )
        if mechanism.get("leading_sensitivity_candidate"):
            print(f"  X paired sensitivity={mechanism.get('leading_sensitivity_candidate')}")
    if progress:
        print(
            f"  progress={progress.get('status')} new_questions={len(progress.get('new_question_keys') or [])} "
            f"replications={len(progress.get('replicated_question_keys') or [])} "
            f"escape_next={bool(progress.get('next_burst_escape_required'))}"
        )
    print(f"  shared portfolio active={len(port.get('active') or [])} runnable={port.get('runnable_focuses', 0)}")
    print("  NOTE: relation metric/identity/lineage outputs are candidates only; no physical space, life or biological division is claimed.")
    print("  NOTE: mature X counts are not a target; paired-control why-lane tests scale-normalized explanations and interventions.")
    print("  NOTE: intervened X-mechanism runs are exploratory and never count as strict-zero evidence.")
    print("  NOTE: uniform-field morphology is observation-only; no node/edge/network is seeded or claimed.")
    print("  NOTE: Research Memory prevents routine exact-repeat drift; F0-F7 remains one human-written reference path.")


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    relation_instrument_adapter.install()
    research_optimizer.install()
    progress_ratchet.install()
    progress_context.install()

    result = _run_adaptive_v8_exact(argv)
    _attach_x_mechanism(result)
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
