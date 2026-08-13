"""Durable operational backlog for research instruments and infrastructure debt.

Frontier instrument requests are valuable but burst-local; an hourly report can stop mentioning one and a
future agent may accidentally forget that the measurement gap still exists.  This module preserves those
requests across bursts and also records Research Health warnings/errors until they are resolved.

The backlog is *operational planning only*.  Its score cannot allocate physical search budget, change a
scientific status, promote a Room/Level, or turn an instrument request into evidence that a phenomenon
exists.  Scaffolded-only requests stay explicitly labelled.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_FRONTIER = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"
_HEALTH = _REPO / "ai_lab" / "reports" / "easy" / "research_health_latest.json"
_OUTPUT = _REPO / "ai_lab" / "discoveries" / "research_backlog.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "research_backlog_latest.md"

_REQUEST_TO_CAPABILITY = {
    "metric-from-relations": "emergent_metric_geometry",
    "identity-continuity": "persistent_individual_identity",
    "damage-recovery": "self_repair",
    "growth-accounting": "growth_and_specialization",
    "predictive-holdout": "adaptive_prediction",
    "lineage-accounting": "division_with_inheritance",
}

# This warning documents historical keys that are intentionally preserved forever. It is migration
# context, not an actionable recurring defect once the current router has become context-aware.
_INFORMATIONAL_HEALTH_IDS = {"research-memory-legacy-x-context-debt"}


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _score(row: dict[str, Any]) -> float:
    kind = str(row.get("kind") or "")
    status = str(row.get("status") or "")
    if kind == "infrastructure_debt":
        base = 100.0 if status == "ERROR" else (70.0 if status == "WARN" else 0.0)
        return base + min(20.0, float(row.get("times_seen", 0) or 0))
    if kind == "instrument_request":
        if status == "CAPABILITY_LEAD_REPORTED":
            return 5.0
        if status == "DORMANT_NOT_REQUESTED_THIS_BURST":
            return 25.0 + min(15.0, float(row.get("times_requested", 0) or 0))
        base = 50.0 + min(30.0, float(row.get("times_requested", 0) or 0))
        if row.get("scaffolded_only"):
            base -= 5.0
        return base
    return 0.0


def build_backlog(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    frontier = _read(_FRONTIER, {})
    health = _read(_HEALTH, {})
    existing = _read(_OUTPUT, {"entries": []}) if existing is None else existing
    burst = str(frontier.get("burst_id") or health.get("burst_id") or "unknown-burst")
    old = {
        str(row.get("key")): dict(row)
        for row in (existing.get("entries") or [])
        if isinstance(row, dict) and row.get("key")
    }

    capabilities = {
        str(row.get("id")): str(row.get("status") or "")
        for row in (frontier.get("capability_map") or [])
        if isinstance(row, dict) and row.get("id")
    }
    current_request_ids: set[str] = set()
    for request in frontier.get("instrument_requests") or []:
        if not isinstance(request, dict) or not request.get("id"):
            continue
        rid = str(request["id"])
        current_request_ids.add(rid)
        key = f"instrument:{rid}"
        prior = old.get(key, {})
        new_burst = str(prior.get("last_requested_burst") or "") != burst
        row = {
            **prior,
            "key": key,
            "kind": "instrument_request",
            "request_id": rid,
            "question": request.get("question"),
            "purpose": request.get("purpose"),
            "status": "OPEN",
            "scaffolded_only": bool(request.get("may_use_scaffolded_analogy_lane")),
            "scaffolded_lane_cannot_count_as_pure_genesis_proof": bool(
                request.get("scaffolded_lane_cannot_count_as_pure_genesis_proof")
            ),
            "new_physical_axiom": bool(request.get("new_physical_axiom", False)),
            "target_morphology_seeded": bool(request.get("target_morphology_seeded", False)),
            "related_capability": _REQUEST_TO_CAPABILITY.get(rid),
            "related_capability_status": capabilities.get(_REQUEST_TO_CAPABILITY.get(rid, "")),
            "first_requested_burst": prior.get("first_requested_burst") or burst,
            "last_requested_burst": burst,
            "times_requested": int(prior.get("times_requested", 0) or 0) + int(new_burst),
        }
        old[key] = row

    for key, row in list(old.items()):
        if row.get("kind") != "instrument_request":
            continue
        rid = str(row.get("request_id") or key.split(":", 1)[-1])
        if rid in current_request_ids:
            continue
        capability = _REQUEST_TO_CAPABILITY.get(rid)
        capability_status = capabilities.get(capability or "")
        row["related_capability"] = capability
        row["related_capability_status"] = capability_status
        row["status"] = (
            "CAPABILITY_LEAD_REPORTED"
            if capability_status == "LEAD"
            else "DORMANT_NOT_REQUESTED_THIS_BURST"
        )
        old[key] = row

    for check in health.get("checks") or []:
        if not isinstance(check, dict) or not check.get("id"):
            continue
        cid = str(check["id"])
        key = f"infra:{cid}"
        prior = old.get(key, {})
        status = str(check.get("status") or "PASS")
        if status == "PASS" or cid in _INFORMATIONAL_HEALTH_IDS:
            if prior:
                prior["status"] = "RESOLVED"
                prior["resolved_burst"] = burst
                prior["last_seen_burst"] = burst
                old[key] = prior
            continue
        new_burst = str(prior.get("last_seen_burst") or "") != burst
        old[key] = {
            **prior,
            "key": key,
            "kind": "infrastructure_debt",
            "check_id": cid,
            "status": status,
            "message": check.get("message"),
            "observed": check.get("observed"),
            "first_seen_burst": prior.get("first_seen_burst") or burst,
            "last_seen_burst": burst,
            "times_seen": int(prior.get("times_seen", 0) or 0) + int(new_burst),
        }

    entries = list(old.values())
    for row in entries:
        row["operational_priority_score"] = round(_score(row), 3)
    entries.sort(
        key=lambda row: (
            float(row.get("operational_priority_score", 0.0)),
            str(row.get("key")),
        ),
        reverse=True,
    )
    active = [
        row for row in entries
        if row.get("status") not in {"RESOLVED", "CAPABILITY_LEAD_REPORTED"}
    ]
    return {
        "version": 1,
        "mode": "durable-research-operations-backlog",
        "last_burst": burst,
        "entries": entries,
        "active_count": len(active),
        "recommended_next": active[0].get("key") if active else None,
        "policy": {
            "burst_local_instrument_requests_are_preserved": True,
            "resolved_entries_are_deleted": False,
            "historical_contextless_x_warning_is_actionable_debt": False,
            "operational_score_routes_physical_compute": False,
            "operational_score_changes_scientific_truth": False,
            "instrument_request_is_evidence_of_phenomenon": False,
            "scaffolded_lane_counts_as_pure_genesis_proof": False,
        },
        "integrity": {
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }


def render_markdown(backlog: dict[str, Any]) -> str:
    lines = [
        "# Research Operations Backlog",
        "",
        f"burst `{backlog.get('last_burst')}` — active operational items: {backlog.get('active_count', 0)}",
        "",
        "これは測定器・研究インフラの作業待ちリストです。物理的な発見の順位ではありません。",
        "",
    ]
    for row in (backlog.get("entries") or [])[:16]:
        lines.append(
            f"- **{row.get('status')}** `{row.get('key')}` "
            f"(ops score {row.get('operational_priority_score')}) — "
            f"{row.get('question') or row.get('message') or row.get('purpose') or ''}"
        )
    lines.extend([
        "",
        "Instrument request は『その現象が存在する証拠』ではありません。scaffolded-only lane は Pure Genesis の証明に使いません。",
        "",
    ])
    return "\n".join(lines)


def run(*, persist: bool = True) -> dict[str, Any]:
    backlog = build_backlog()
    if persist:
        _write(_OUTPUT, backlog)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(render_markdown(backlog))
    return backlog


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Preserve burst-local instrument and infrastructure debt")
    p.add_argument("--no-record", action="store_true", help="build only; do not write backlog files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    backlog = run(persist=not args.no_record)
    print(
        f"Research Backlog: burst={backlog.get('last_burst')} active={backlog.get('active_count')} "
        f"next={backlog.get('recommended_next')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
