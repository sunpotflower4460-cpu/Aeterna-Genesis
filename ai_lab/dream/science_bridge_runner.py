"""Run curated Science Bridge directions through the separated Free Hypothesis Lab.

The same exploratory simulator/provenance guards are reused rather than creating another truth path.
A dedicated Science-Bridge result/ledger is also written so literature-inspired outcomes do not become
indistinguishable from ordinary Free-Lab runs. Nothing here is strict-zero evidence.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab.dream import free_hypothesis_entrypoint
from ai_lab.dream import free_hypothesis_lab as lab

_REPO = Path(__file__).resolve().parents[2]
_SCIENCE_DIRECTIONS = _REPO / "ai_lab" / "discoveries" / "science_bridge_directions.json"
_RESULT = _REPO / "ai_lab" / "reports" / "easy" / "science_bridge_experiment_latest.json"
_LEDGER = _REPO / "ai_lab" / "discoveries" / "science_bridge_experiment_ledger.json"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def direction_count() -> int:
    doc = _read(_SCIENCE_DIRECTIONS, {"directions": []})
    return sum(
        1 for row in (doc.get("directions") or [])
        if isinstance(row, dict) and row.get("enabled") is not False and row.get("experiment_type")
    )


def _science_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in report.get("hypotheses") or []:
        if not isinstance(row, dict):
            continue
        rows.append({
            "hypothesis_id": row.get("hypothesis_id"),
            "experiment_type": row.get("experiment_type"),
            "source": row.get("source"),
            "source_reference": row.get("source_reference"),
            "strict_transfer_question": row.get("strict_transfer_question"),
            "finite_runs": row.get("finite_runs"),
            "delta_vs_unmodified_control": row.get("delta_vs_unmodified_control"),
            "orientation_priority_only": row.get("orientation_priority_only"),
            "counts_as_strict_zero_evidence": False,
        })
    return {
        "version": 1,
        "mode": "science-bridge-experimental-results",
        "generated_at": report.get("generated_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_evidence_context": report.get("source_evidence_context"),
        "matched_control_runs": report.get("matched_control_runs"),
        "literature_inspired_hypotheses": rows,
        "top_literature_inspired_result": rows[0] if rows else None,
        "integrity": {
            "counts_as_strict_zero_evidence": False,
            "may_promote_rooms": False,
            "may_change_official_levels": False,
            "paper_claim_is_aeterna_evidence": False,
            "similar_result_means_same_physics": False,
            "translation_is_analogy_not_reproduction": True,
        },
    }


def _record_snapshot(snapshot: dict[str, Any]) -> None:
    _write(_RESULT, snapshot)
    ledger = _read(_LEDGER, {"version": 1, "runs": []})
    top = snapshot.get("top_literature_inspired_result") or {}
    ledger.setdefault("runs", []).append({
        "generated_at": snapshot.get("generated_at"),
        "top": top,
        "experiment_count": len(snapshot.get("literature_inspired_hypotheses") or []),
        "counts_as_strict_zero_evidence": False,
    })
    # Keep a compact hot history. Git remains authoritative for older snapshots.
    ledger["runs"] = ledger["runs"][-240:]
    ledger["policy"] = {
        "negative_results_are_preserved": True,
        "literature_experiment_is_strict_zero": False,
        "may_promote_rooms_or_levels": False,
    }
    _write(_LEDGER, ledger)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run curated Science Bridge directions in Free Hypothesis Lab")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--no-record", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    count = direction_count()
    if count <= 0:
        print("Science Bridge Runner: no executable curated directions; nothing to run.")
        return 0

    free_hypothesis_entrypoint.install_context_adapter()
    original = lab._DIRECTIONS
    try:
        lab._DIRECTIONS = _SCIENCE_DIRECTIONS
        report = lab.run(
            max_hypotheses=count,
            replicates=max(1, args.replicates),
            seed=args.seed,
            quick=args.quick,
            persist=not args.no_record,
        )
    finally:
        lab._DIRECTIONS = original

    snapshot = _science_snapshot(report)
    if not args.no_record:
        _record_snapshot(snapshot)
    print(
        f"Science Bridge Runner: executed curated_directions={count} "
        f"finite_result_rows={len(snapshot.get('literature_inspired_hypotheses') or [])}."
    )
    print("NOTE: literature-inspired results remain exploratory and never count as strict-zero evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
