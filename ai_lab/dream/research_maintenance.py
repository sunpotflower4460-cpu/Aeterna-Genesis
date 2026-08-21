"""Non-destructive research maintenance and organization.

Scientific cleaning must never mean deleting inconvenient, negative or old evidence. Automatic work is
therefore limited to validation, index/catalog regeneration, continuity refresh and archive inventory.
Potentially destructive actions are only reported for review and are never performed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab.dream import research_continuity

_REPO = Path(__file__).resolve().parents[2]
_DISC = _REPO / "ai_lab" / "discoveries"
_EASY = _REPO / "ai_lab" / "reports" / "easy"
_OUTPUT = _EASY / "research_maintenance_latest.json"
_REPORT_MD = _EASY / "research_maintenance_latest.md"
_CATALOG = _DISC / "research_catalog.json"

_TRACKED_JSON = {
    "easy_latest": _EASY / "latest.json",
    "research_health": _EASY / "research_health_latest.json",
    "research_manifest": _EASY / "research_manifest_latest.json",
    "research_memory": _DISC / "research_memory.json",
    "research_index": _DISC / "research_index.json",
    "research_backlog": _DISC / "research_backlog.json",
    "research_continuity": _DISC / "research_continuity.json",
    "unknown_followups": _DISC / "unknown_followups.json",
    "deep_time": _DISC / "deep_time_fission.json",
    "cross_world": _DISC / "cross_world_emergence.json",
    "free_hypothesis_ledger": _DISC / "free_hypothesis_lab.json",
    "science_bridge_sources": _DISC / "science_bridge_sources.json",
    "science_bridge_directions": _DISC / "science_bridge_directions.json",
    "science_bridge_ledger": _DISC / "science_bridge_ledger.json",
    "ai_scientist_directions": _DISC / "ai_scientist_directions.json",
}

# These may legitimately be absent before their first derived/scheduled run. Core strict provenance,
# Research Memory and existing discovery ledgers are never silently classified as optional.
_OPTIONAL_NAMES = {
    "research_continuity",
    "science_bridge_directions",
    "science_bridge_ledger",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "MISSING"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _duplicate_values(rows: Any, key: str) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows or []:
        if not isinstance(row, dict) or row.get(key) in (None, ""):
            continue
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, count in counts.items() if count > 1)


def _structure_duplicates(name: str, doc: Any) -> list[dict[str, Any]]:
    if not isinstance(doc, dict):
        return []
    checks: list[tuple[str, Any, str]] = []
    if name == "science_bridge_sources":
        checks += [("source-id", doc.get("sources"), "id"), ("source-doi", doc.get("sources"), "doi")]
    elif name in {"science_bridge_directions", "ai_scientist_directions"}:
        checks += [("direction-id", doc.get("directions"), "id")]
    elif name == "research_index":
        checks += [("burst-id", doc.get("entries"), "burst_id"), ("manifest-hash", doc.get("entries"), "manifest_content_sha256")]
    elif name == "research_backlog":
        checks += [("backlog-key", doc.get("entries"), "key")]
    elif name == "research_continuity":
        checks += [("continuity-key", doc.get("lessons"), "key")]
    elif name == "science_bridge_ledger":
        checks += [("science-ledger-key", doc.get("sources"), "key")]
    findings = []
    for label, rows, identity_key in checks:
        duplicates = _duplicate_values(rows, identity_key)
        if duplicates:
            findings.append({"file": name, "identity": label, "duplicates": duplicates})
    return findings


def _archive_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in sorted(_DISC.glob("*.archive")):
        if not directory.is_dir():
            continue
        parts = sorted(directory.glob("*.json"))
        rows.append({
            "directory": str(directory.relative_to(_REPO)),
            "part_count": len(parts),
            "bytes": sum(part.stat().st_size for part in parts),
            "recent_parts": [part.name for part in parts[-8:]],
        })
    return rows


def _catalog_entry(name: str, path: Path, doc: Any | None, error: str | None) -> dict[str, Any]:
    return {
        "name": name,
        "path": str(path.relative_to(_REPO)),
        "required": name not in _OPTIONAL_NAMES,
        "exists": path.exists(),
        "parse_error": error,
        "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        "sha256": _sha(path),
        "generated_at": doc.get("generated_at") if isinstance(doc, dict) else None,
        "burst_id": doc.get("burst_id") if isinstance(doc, dict) else None,
    }


def build(*, apply_safe: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    safe_actions: list[str] = []
    if apply_safe:
        research_continuity.run(persist=True)
        safe_actions.append("refreshed Research Continuity from source evidence without deleting history")

    documents: dict[str, Any] = {}
    catalog_rows: list[dict[str, Any]] = []
    parse_failures: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    missing_optional: list[str] = []
    missing_required: list[str] = []
    for name, path in _TRACKED_JSON.items():
        doc, error = _read_json(path)
        documents[name] = doc
        catalog_rows.append(_catalog_entry(name, path, doc, error))
        if error == "MISSING":
            (missing_optional if name in _OPTIONAL_NAMES else missing_required).append(name)
        elif error:
            parse_failures.append({"name": name, "path": str(path.relative_to(_REPO)), "error": error})
        duplicates.extend(_structure_duplicates(name, doc))

    easy = documents.get("easy_latest") if isinstance(documents.get("easy_latest"), dict) else {}
    health = documents.get("research_health") if isinstance(documents.get("research_health"), dict) else {}
    continuity = documents.get("research_continuity") if isinstance(documents.get("research_continuity"), dict) else {}
    current_burst = easy.get("burst_id")
    stale_refs: list[dict[str, Any]] = []
    if health and current_burst and health.get("burst_id") not in (None, current_burst):
        stale_refs.append({"name": "research_health", "expected_burst": current_burst, "observed": health.get("burst_id")})
    if continuity and current_burst and continuity.get("latest_strict_burst") not in (None, current_burst):
        stale_refs.append({
            "name": "research_continuity",
            "expected_burst": current_burst,
            "observed": continuity.get("latest_strict_burst"),
        })

    archives = _archive_inventory()
    now = _now()
    healthy = not parse_failures and not duplicates and not stale_refs and not missing_required
    catalog = {
        "version": 1,
        "mode": "research-organization-catalog",
        "generated_at": now,
        "current_strict_burst": current_burst,
        "files": catalog_rows,
        "archive_inventory": archives,
        "policy": {
            "catalog_is_derived_navigation": True,
            "raw_evidence_is_deleted": False,
            "immutable_archive_parts_are_rewritten": False,
            "catalog_changes_scientific_truth": False,
        },
    }
    report = {
        "version": 1,
        "mode": "safe-research-maintenance",
        "generated_at": now,
        "apply_safe": bool(apply_safe),
        "safe_actions_applied": safe_actions,
        "parse_failures": parse_failures,
        "missing_required_files": missing_required,
        "missing_optional_files": missing_optional,
        "duplicate_identity_findings": duplicates,
        "stale_reference_findings": stale_refs,
        "archive_inventory": archives,
        "healthy_for_automatic_organization": healthy,
        "destructive_cleanup_required": False,
        "destructive_cleanup_performed": False,
        "policy": {
            "negative_results_are_deleted": False,
            "quarantined_results_are_deleted": False,
            "raw_scientific_ledgers_are_compacted_destructively": False,
            "immutable_manifests_are_deleted": False,
            "git_history_is_authoritative": True,
            "safe_automatic_cleanup_means_reindex_validate_and_organize": True,
            "potentially_destructive_actions_require_separate_review": True,
            "missing_core_research_state_is_healthy": False,
        },
    }
    return report, catalog


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Maintenance — latest",
        "",
        f"safe maintenance healthy: **{report.get('healthy_for_automatic_organization')}**",
        "",
        "この掃除は科学的証拠を消しません。索引/handoff再生成と、壊れた・重複した参照の検出だけを自動で行います。",
        "",
        f"- missing required: {len(report.get('missing_required_files') or [])}",
        f"- parse failures: {len(report.get('parse_failures') or [])}",
        f"- duplicate identity findings: {len(report.get('duplicate_identity_findings') or [])}",
        f"- stale reference findings: {len(report.get('stale_reference_findings') or [])}",
        f"- archive directories: {len(report.get('archive_inventory') or [])}",
        "",
    ]
    lines.extend(f"- safe action: {item}" for item in (report.get("safe_actions_applied") or []))
    lines += [
        "",
        "Raw evidence / negative results / quarantine / immutable manifests are never deleted by this job.",
        "",
    ]
    return "\n".join(lines)


def run(*, apply_safe: bool = False, persist: bool = True) -> dict[str, Any]:
    report, catalog = build(apply_safe=apply_safe)
    if persist:
        _write(_OUTPUT, report)
        _write(_CATALOG, catalog)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely organize Aeterna research without deleting evidence")
    parser.add_argument("--apply-safe", action="store_true")
    parser.add_argument("--no-record", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(apply_safe=args.apply_safe, persist=not args.no_record)
    print(
        "Research Maintenance: "
        f"healthy={report.get('healthy_for_automatic_organization')} "
        f"missing_required={len(report.get('missing_required_files') or [])} "
        f"parse={len(report.get('parse_failures') or [])} "
        f"duplicates={len(report.get('duplicate_identity_findings') or [])} "
        f"stale={len(report.get('stale_reference_findings') or [])}"
    )
    return 0 if report.get("healthy_for_automatic_organization") else 2


if __name__ == "__main__":
    raise SystemExit(main())
