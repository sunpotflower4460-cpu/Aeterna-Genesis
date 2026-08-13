"""Infrastructure health audit for the autonomous Aeterna research loop.

This module answers a narrow question: "is the research machinery preserving provenance, memory and
cross-report consistency?"  It does *not* grade whether nature produced an interesting result.  A null,
negative, weakened, non-replicating or low-gain scientific outcome is allowed and must never fail this
audit merely for being scientifically disappointing.

``--strict`` exits non-zero only for infrastructure/integrity contract breaks such as stale aliases,
corrupt durable-memory metadata, impossible budget accounting, or a scientific-shadow flag that would
silently promote a claim.  Migration debt and incomplete but honestly-labelled science are warnings.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_FRONTIER = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"
_MEMORY = _REPO / "ai_lab" / "discoveries" / "research_memory.json"
_CROSS = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"
_CROSS_REPLICATION = _REPO / "ai_lab" / "reports" / "crossworld" / "replication_latest.json"
_NOTHING = _REPO / "ai_lab" / "reports" / "easy" / "nothing_latest.json"
_REPORT_JSON = _REPO / "ai_lab" / "reports" / "easy" / "research_health_latest.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "research_health_latest.md"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _add(
    checks: list[dict[str, Any]], check_id: str, ok: bool, *,
    severity: str = "ERROR", message: str, observed: Any = None,
) -> None:
    checks.append({
        "id": check_id,
        "status": "PASS" if ok else severity,
        "message": message,
        "observed": observed,
    })


def _progress_entries(memory: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in (memory.get("entries") or [])
        if isinstance(row, dict) and row.get("kind") == "progress_question"
    ]


def _budget_checks(frontier: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    budget = frontier.get("budget") or {}
    requested = int(budget.get("requested", 0) or 0)
    allocations = budget.get("allocated") or {}
    allocated_values = [int(v or 0) for v in allocations.values()]
    allocated = sum(allocated_values)
    executed = int(budget.get("executed", 0) or 0)
    unallocated = int(budget.get("unallocated_due_to_capacity", 0) or 0)
    execution_gap = int(budget.get("allocated_but_not_executed", 0) or 0)

    _add(
        checks, "frontier-budget-nonnegative",
        requested >= 0 and executed >= 0 and all(v >= 0 for v in allocated_values),
        message="frontier budget fields must be non-negative",
        observed={"requested": requested, "allocated": allocations, "executed": executed},
    )
    _add(
        checks, "frontier-allocation-within-request",
        allocated <= requested,
        message="allocated frontier compute must not exceed the requested bounded budget",
        observed={"requested": requested, "allocated_total": allocated},
    )
    _add(
        checks, "frontier-execution-within-allocation",
        executed <= allocated,
        message="executed frontier experiments must not exceed allocated compute",
        observed={"allocated_total": allocated, "executed": executed},
    )
    _add(
        checks, "frontier-unallocated-accounting",
        unallocated == max(0, requested - allocated),
        message="unallocated_due_to_capacity must close the requested-vs-allocated accounting identity",
        observed={"recorded": unallocated, "expected": max(0, requested - allocated)},
    )
    _add(
        checks, "frontier-execution-gap-accounting",
        execution_gap == max(0, allocated - executed),
        message="allocated_but_not_executed must close the allocation-vs-execution identity",
        observed={"recorded": execution_gap, "expected": max(0, allocated - executed)},
    )

    progress = frontier.get("progress_ratchet") or {}
    keys = [str(x) for x in progress.get("question_keys") or [] if x]
    _add(
        checks, "frontier-current-question-keys-unique",
        len(keys) == len(set(keys)),
        message="a current burst must not count the same progress question twice",
        observed={"count": len(keys), "unique": len(set(keys))},
    )
    current_legacy_x = [key for key in keys if key.startswith("x|") and "|ctx:" not in key]
    _add(
        checks, "frontier-x-context-identity-migration",
        not current_legacy_x,
        severity="WARN",
        message=(
            "current X progress keys should carry start-context identity; legacy keys remain valid history "
            "but are not safe as cross-context coverage"
        ),
        observed={"legacy_current_keys": len(current_legacy_x)},
    )


def _memory_checks(memory: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    entries = [row for row in (memory.get("entries") or []) if isinstance(row, dict)]
    keys = [str(row.get("key")) for row in entries if row.get("key")]
    progress = _progress_entries(memory)
    actual_progress = len(progress)
    counts = memory.get("counts") or {}
    policy = memory.get("policy") or {}

    _add(
        checks, "research-memory-keys-unique",
        len(keys) == len(set(keys)),
        message="Research Memory entry keys must be unique",
        observed={"count": len(keys), "unique": len(set(keys))},
    )
    if progress:
        _add(
            checks, "research-memory-schema-durable",
            int(memory.get("version", 0) or 0) >= 2,
            message="progress_question entries require durable Research Memory schema version >=2",
            observed=memory.get("version"),
        )
        _add(
            checks, "research-memory-progress-count",
            int(counts.get("progress_questions", -1) or 0) == actual_progress,
            message="counts.progress_questions must equal the actual durable progress_question entries",
            observed={"recorded": counts.get("progress_questions"), "actual": actual_progress},
        )
        _add(
            checks, "research-memory-ratchet-policy",
            policy.get("progress_ratchet_reads_memory") is True
            and policy.get("progress_question_history_is_durable") is True,
            message="durable progress memory contract must survive later reporting layers",
            observed={
                "progress_ratchet_reads_memory": policy.get("progress_ratchet_reads_memory"),
                "progress_question_history_is_durable": policy.get("progress_question_history_is_durable"),
            },
        )
    _add(
        checks, "research-memory-total-count",
        int(counts.get("total", len(entries)) or 0) == len(entries),
        message="counts.total must match the number of Research Memory entries",
        observed={"recorded": counts.get("total"), "actual": len(entries)},
    )
    legacy_x = [
        str(row.get("question_key") or "") for row in progress
        if str(row.get("question_key") or "").startswith("x|")
        and "|ctx:" not in str(row.get("question_key") or "")
    ]
    _add(
        checks, "research-memory-legacy-x-context-debt",
        not legacy_x,
        severity="WARN",
        message=(
            "legacy contextless X progress entries are migration debt only; they must remain preserved "
            "but must not suppress a new context-aware question"
        ),
        observed={"legacy_entries": len(legacy_x)},
    )


def _crossworld_checks(
    easy_burst: str, cross: dict[str, Any], replication: dict[str, Any], checks: list[dict[str, Any]],
) -> None:
    shadow = cross.get("independent_replication_shadow") or {}
    if shadow:
        _add(
            checks, "crossworld-shadow-current-burst",
            str(shadow.get("burst_id") or "") == easy_burst,
            message="embedded Cross-World replication shadow must belong to the current easy-report burst",
            observed={"easy": easy_burst, "shadow": shadow.get("burst_id")},
        )
    if replication:
        _add(
            checks, "crossworld-replication-current-burst",
            str(replication.get("burst_id") or "") == easy_burst,
            message="replication_latest must never silently point at a previous burst",
            observed={"easy": easy_burst, "replication": replication.get("burst_id")},
        )
        _add(
            checks, "crossworld-replication-completion-labelled",
            bool(replication.get("completed"))
            or str(replication.get("completion_status") or "") in {"NOT_COMPLETED", "SKIPPED_NO_CURRENT_MATCH"},
            severity="WARN",
            message="an incomplete Cross-World replication is allowed only when explicitly labelled incomplete/skipped",
            observed={
                "completed": replication.get("completed"),
                "completion_status": replication.get("completion_status"),
            },
        )

    forbidden_true = {
        "universality_claim": cross.get("universality_claim"),
        "official_level_effect": cross.get("official_level_effect"),
        "promotion_effect": cross.get("promotion_effect"),
        "hypothesis_confidence_effect": cross.get("hypothesis_confidence_effect"),
        "changes_world_dynamics": cross.get("changes_world_dynamics"),
        "same_fingerprint_means_same_physics": cross.get("same_fingerprint_means_same_physics"),
    }
    _add(
        checks, "crossworld-shadow-cannot-promote-science",
        not any(value is True for value in forbidden_true.values()),
        message="Cross-World shadow must not promote Rooms/Levels/confidence or equate matching fingerprints with physics",
        observed=forbidden_true,
    )
    rep_integrity = replication.get("integrity") or {}
    rep_forbidden = {
        key: rep_integrity.get(key) for key in (
            "updates_cumulative_CWX_ledger", "changes_world_dynamics", "changes_hypothesis_confidence",
            "changes_official_level", "promotes_rooms", "same_fingerprint_means_same_physics",
            "universality_claim", "target_outcome_seeded",
        )
    }
    if replication:
        _add(
            checks, "crossworld-replication-cannot-promote-science",
            not any(value is True for value in rep_forbidden.values()),
            message="independent replication is a shadow and must not mutate scientific promotion/confidence state",
            observed=rep_forbidden,
        )


def _nothing_checks(easy_burst: str, nothing: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    if not nothing:
        _add(
            checks, "strict-nothing-report-present", False,
            message="NØ control report must be present for a completed production burst",
        )
        return
    strict = nothing.get("strict_nothing") or {}
    result = strict.get("result") or {}
    _add(
        checks, "strict-nothing-current-burst",
        str(nothing.get("burst_id") or "") == easy_burst,
        message="NØ control report must belong to the current easy-report burst",
        observed={"easy": easy_burst, "nothing": nothing.get("burst_id")},
    )
    _add(
        checks, "strict-nothing-remains-null-control",
        nothing.get("mode") == "strict-nothing-genesis-meta-control"
        and int(nothing.get("strict_trial_count", 0) or 0) == 1
        and strict.get("strict_nothing") is True
        and result.get("physical_transition_executed") is False
        and result.get("something_observed") is False
        and result.get("nothing_to_something_claim") is False
        and result.get("result_is_control_construction_not_independent_measurement") is True,
        message="NØ must remain a single declarative null-control, not a seeded dynamical or emergence success arm",
        observed={
            "mode": nothing.get("mode"),
            "strict_trial_count": nothing.get("strict_trial_count"),
            "physical_transition_executed": result.get("physical_transition_executed"),
            "something_observed": result.get("something_observed"),
            "nothing_to_something_claim": result.get("nothing_to_something_claim"),
        },
    )


def build_health() -> dict[str, Any]:
    easy = _read(_EASY, {})
    frontier = _read(_FRONTIER, {})
    memory = _read(_MEMORY, {})
    cross = _read(_CROSS, {})
    replication = _read(_CROSS_REPLICATION, {})
    nothing = _read(_NOTHING, {})
    checks: list[dict[str, Any]] = []

    burst = str(easy.get("burst_id") or "")
    _add(
        checks, "easy-current-burst-present", bool(burst),
        message="easy/latest.json must identify the current completed burst",
        observed=burst or None,
    )
    if frontier:
        _add(
            checks, "frontier-alias-current-burst",
            str(frontier.get("burst_id") or "") == burst,
            message="frontier_latest must belong to the same burst as easy/latest",
            observed={"easy": burst, "frontier": frontier.get("burst_id")},
        )
        _budget_checks(frontier, checks)
    else:
        _add(
            checks, "frontier-alias-present", False,
            message="frontier_latest must exist for a completed Adaptive research burst",
        )

    _memory_checks(memory, checks)
    _crossworld_checks(burst, cross, replication, checks)
    _nothing_checks(burst, nothing, checks)

    errors = [row for row in checks if row["status"] == "ERROR"]
    warnings = [row for row in checks if row["status"] == "WARN"]
    return {
        "version": 1,
        "mode": "research-infrastructure-health",
        "burst_id": burst,
        "healthy": not errors,
        "strict_failure_count": len(errors),
        "warning_count": len(warnings),
        "checks": checks,
        "semantics": {
            "negative_scientific_result_is_failure": False,
            "low_gain_scientific_result_is_failure": False,
            "non_replication_is_failure": False,
            "infrastructure_or_integrity_contract_break_is_failure": True,
            "warnings_change_scientific_truth": False,
        },
        "integrity": {
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
            "health_score_is_physical_observable": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    icon = "✅" if report.get("healthy") else "❌"
    lines = [
        "# Research Infrastructure Health",
        "",
        f"{icon} burst `{report.get('burst_id') or 'unknown'}` — strict errors: "
        f"{report.get('strict_failure_count', 0)}, warnings: {report.get('warning_count', 0)}",
        "",
        "これは研究インフラの整合性監査です。科学的な負の結果・未再現・低gainを失敗扱いしません。",
        "",
    ]
    for row in report.get("checks") or []:
        marker = {"PASS": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(str(row.get("status")), "•")
        lines.append(f"- {marker} `{row.get('id')}` — {row.get('message')}")
    lines.extend([
        "",
        "科学的主張、物理方程式、初期条件、Room/公式Levelはこの監査では変更しません。",
        "",
    ])
    return "\n".join(lines)


def run(*, persist: bool = True) -> dict[str, Any]:
    report = build_health()
    if persist:
        _write_json(_REPORT_JSON, report)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(render_markdown(report))
    return report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Audit autonomous research infrastructure without grading scientific outcomes")
    p.add_argument("--strict", action="store_true", help="exit non-zero on infrastructure/integrity ERROR checks")
    p.add_argument("--no-record", action="store_true", help="audit only; do not write report files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(persist=not args.no_record)
    print(
        f"Research Health: burst={report.get('burst_id')} healthy={report.get('healthy')} "
        f"errors={report.get('strict_failure_count')} warnings={report.get('warning_count')}"
    )
    return 2 if args.strict and not report.get("healthy") else 0


if __name__ == "__main__":
    raise SystemExit(main())
