"""Read-only audit for future-safe autonomous research expansion.

This audit focuses on two classes of drift that are especially easy to introduce while extending Aeterna:

* a new/mutated instrument request that has no claim-safe measurement contract;
* a production workflow change that silently disables one of the intentionally broad research lanes.

It does not grade scientific outcomes and does not write evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_lab.dream import instrument_registry
from ai_lab.dream import production_protocol

_REPO = Path(__file__).resolve().parents[2]
_FRONTIER = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"
_BACKLOG = _REPO / "ai_lab" / "discoveries" / "research_backlog.json"


def _read_required(path: Path, *, label: str) -> dict[str, Any]:
    """Read a tracked contract input fail-closed; absence/corruption is itself an audit error."""
    if not path.exists():
        raise RuntimeError(f"required {label} is missing: {path}")
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"required {label} is unreadable or malformed: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"required {label} must be a JSON object: {path}")
    return value


def _backlog_request(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize durable backlog schema into the same safety contract used by frontier requests."""
    scaffolded = bool(row.get("scaffolded_only", row.get("may_use_scaffolded_analogy_lane", False)))
    return {
        "id": row.get("request_id") or row.get("id"),
        "new_physical_axiom": row.get("new_physical_axiom"),
        "target_morphology_seeded": row.get("target_morphology_seeded"),
        "may_use_scaffolded_analogy_lane": scaffolded,
        "scaffolded_lane_cannot_count_as_pure_genesis_proof": row.get(
            "scaffolded_lane_cannot_count_as_pure_genesis_proof"
        ),
    }


def build_audit(
    *, frontier_path: Path | None = None, backlog_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    frontier: dict[str, Any] = {}
    backlog: dict[str, Any] = {}
    try:
        frontier = _read_required(frontier_path or _FRONTIER, label="frontier report")
    except RuntimeError as exc:
        errors.append(str(exc))
    try:
        backlog = _read_required(backlog_path or _BACKLOG, label="research backlog")
    except RuntimeError as exc:
        errors.append(str(exc))

    registry = instrument_registry.validate_frontier_requests(frontier) if frontier else {
        "registry_version": instrument_registry.REGISTRY_VERSION,
        "request_count": 0,
        "registered_request_count": 0,
        "errors": ["frontier request registry audit unavailable because frontier input is invalid"],
        "valid": False,
        "request_is_evidence_of_phenomenon": False,
        "registry_changes_scientific_truth": False,
    }
    errors.extend(str(x) for x in registry.get("errors") or [])

    backlog_rows = [
        row for row in (backlog.get("entries") or [])
        if isinstance(row, dict) and row.get("kind") == "instrument_request"
    ] if backlog else []
    backlog_instrument_ids = {
        str(row.get("request_id") or row.get("id") or "") for row in backlog_rows
        if row.get("request_id") or row.get("id")
    }
    backlog_request_errors: list[str] = []
    for row in backlog_rows:
        backlog_request_errors.extend(instrument_registry.validate_request(_backlog_request(row)))
    errors.extend(f"durable backlog: {err}" for err in backlog_request_errors)
    unregistered_backlog = sorted(
        rid for rid in backlog_instrument_ids if instrument_registry.get(rid) is None
    )

    try:
        protocol = production_protocol.build_contract()
        errors.extend(str(x) for x in protocol.get("errors") or [])
    except Exception as exc:  # fail closed: malformed/missing workflow is a contract failure
        protocol = {"valid": False, "errors": [str(exc)]}
        errors.append(f"production protocol audit failed: {exc}")

    return {
        "version": 2,
        "mode": "autonomous-research-expansion-contract-audit",
        "burst_id": frontier.get("burst_id"),
        "valid": not errors,
        "errors": errors,
        "instrument_registry": registry,
        "backlog_instrument_ids": sorted(backlog_instrument_ids),
        "backlog_request_errors": backlog_request_errors,
        "unregistered_backlog_instrument_ids": unregistered_backlog,
        "production_protocol": {
            "valid": protocol.get("valid"),
            "protocol_sha256": protocol.get("protocol_sha256"),
            "workflow_sha256": protocol.get("workflow_sha256"),
            "recognized_option_count": protocol.get("recognized_option_count"),
            "disabled_required_lanes": protocol.get("disabled_required_lanes") or [],
        },
        "integrity": {
            "audit_writes_scientific_evidence": False,
            "audit_changes_physics": False,
            "audit_changes_initial_conditions": False,
            "audit_changes_scientific_truth_gate": False,
            "audit_promotes_rooms": False,
            "audit_changes_official_levels": False,
            "instrument_request_is_evidence_of_phenomenon": False,
            "protocol_lane_presence_is_scientific_success": False,
            "missing_contract_inputs_fail_closed": True,
            "durable_backlog_preserves_claim_safety_fields": True,
        },
    }


def main() -> int:
    report = build_audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
