"""Non-destructive research maintenance and organization.

"Cleaning" a scientific repository must not mean deleting inconvenient, negative or old evidence.
This module therefore performs only safe housekeeping automatically:

* parse/identity checks for important ledgers and latest aliases,
* duplicate/stale-reference detection,
* compact catalog regeneration,
* Research Continuity refresh,
* archive inventory for existing immutable hot/cold ledger storage.

It never deletes raw evidence, immutable manifests, negative results, quarantined results, or historical
research memory.  Anything that would require destructive cleanup is reported for review instead.
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "MISSING"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__


def _sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _duplicate_values(rows: Any, key: str) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows or []:
        if not isinstance(row, dict) or row.get(key) in (None, ""):
            continue
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, n in counts.items() if n > 1)


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
    return [
        {"file": name, "identity": label, "duplicates": dup}
        for label, rows, key in checks
        if (dup := _duplicate_values(rows, key))
    ]


def _archive_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in sorted(_DISC.glob("*.archive")):
        if not directory.is_dir():
            continue
        parts = sorted(directory.glob("*.json"))
        rows.append({
            "directory": str(directory.relative_to(_REPO)),
            "part_count": len(parts),
            "bytes": sum(p.stat().st_size for p in parts),
            "parts": [p.name for p in parts[-8:]],
        })
    return rows


def _catalog_entry(name: str, path: Path, doc: Any | None, error: str | None) -> dict[str, Any]:
    rel = str(path.relative_to(_REPO))
    generated_at = doc.get("generated_at") if isinstance(doc, dict) else None
    burst = doc.get("burst_id") if isinstance(doc, dict) else None
    return {
        "name": name,
        "path": rel,
        "exists": path.exists(),
        "parse_error": error,
        "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        "sha256": _sha(path),
        "generated_at": generated_at,
        "burst_id": burst,
    }


def build(*, apply_safe: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    safe_actions: list[str] = []
    if apply_safe:
        research_continuity.run(persist=True)
        safe_actions.append("refreshed research_continuity from existing evidence without deleting source history")

    documents: dict[str, Any] = {}
    catalog_rows: list[dict[str, Any]] = []
    parse_failures: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    missing_optional: list[str] = []
    for name, path in _TRACKED_JSON.items():
        doc, error = _read_json(path)
        documents[name] = doc
        catalog_rows.append(_catalog_entry(name, path, doc, error))
        if error == "MISSING":
            # Science Bridge files may not exist before its first run; this is reported but not fatal.
            missing_optional.append(name)
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
        "duplicate_identity_findings": duplicates,
        "stale_reference_findings": stale_refs,
        "missing_optional_files": missing_optional,
        "archive_inventory": archives,
        "healthy_for_automatic_organization": not parse_failures and not duplicates and not stale_refs,
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
        },
    }
    return report, catalog


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Maintenance — latest",
        "",
        f"safe maintenance healthy: **{report.get('healthy_for_automatic_organization')}**",
        "",
        "この掃除は科学的証拠を消しません。索引・handoffの再生成、重複/壊れた参照の検出だけを自動で行います。",
        "",
        f"- parse failures: {len(report.get('parse_failures') or [])}",
        f"- duplicate identity findings: {len(report.get('duplicate_identity_findings') or [])}",
        f"- stale reference findings: {len(report.get('stale_reference_findings') or [])}",
        f"- archive directories: {len(report.get('archive_inventory') or [])}",
        "",
    ]
    for item in report.get("safe_actions_applied") or []:
        lines.append(f"- safe action: {item}")
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
    ap = argparse.ArgumentParser(description="Safely organize Aeterna research without deleting evidence")
    ap.add_argument("--apply-safe", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(apply_safe=args.apply_safe, persist=not args.no_record)
    print(
        "Research Maintenance: "
        f"healthy={report.get('healthy_for_automatic_organization')} "
        f"parse={len(report.get('parse_failures') or [])} "
        f"duplicates={len(report.get('duplicate_identity_findings') or [])} "
        f"stale={len(report.get('stale_reference_findings') or [])}"
    )
    return 0 if report.get("healthy_for_automatic_organization") else 2


if __name__ == "__main__":
    raise SystemExit(main())
