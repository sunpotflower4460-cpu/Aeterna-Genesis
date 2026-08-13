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


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def build_audit() -> dict[str, Any]:
    frontier = _read(_FRONTIER, {})
    backlog = _read(_BACKLOG, {})
    registry = instrument_registry.validate_frontier_requests(frontier)
    protocol = production_protocol.build_contract()

    backlog_instrument_ids = {
        str(row.get("request_id") or "")
        for row in (backlog.get("entries") or [])
        if isinstance(row, dict) and row.get("kind") == "instrument_request" and row.get("request_id")
    }
    unregistered_backlog = sorted(
        rid for rid in backlog_instrument_ids if instrument_registry.get(rid) is None
    )
    errors = [*registry.get("errors", [])]
    errors.extend(f"durable backlog contains unregistered instrument id: {rid}" for rid in unregistered_backlog)
    errors.extend(str(x) for x in protocol.get("errors") or [])

    return {
        "version": 1,
        "mode": "autonomous-research-expansion-contract-audit",
        "burst_id": frontier.get("burst_id"),
        "valid": not errors,
        "errors": errors,
        "instrument_registry": registry,
        "backlog_instrument_ids": sorted(backlog_instrument_ids),
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
        },
    }


def main() -> int:
    report = build_audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
