"""Compact durable index over immutable per-burst research manifests.

Git remains the authoritative history and each manifest remains the per-burst provenance record.  This
index exists so future autonomous agents do not need to scan a large commit/report history merely to answer
"which burst, manifest and evidence commit should I inspect?".

Entries are keyed by burst id and manifest hash.  A different manifest for an already indexed burst is an
error, not an update.  The index may include planning/health summaries for navigation, but those fields are
not scientific confidence and cannot promote any claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_MANIFEST = _REPO / "ai_lab" / "reports" / "easy" / "research_manifest_latest.json"
_HEALTH = _REPO / "ai_lab" / "reports" / "easy" / "research_health_latest.json"
_BACKLOG = _REPO / "ai_lab" / "discoveries" / "research_backlog.json"
_FRONTIER = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"
_ENVIRONMENT = _REPO / "ai_lab" / "reports" / "easy" / "environment_latest.json"
_OUTPUT = _REPO / "ai_lab" / "discoveries" / "research_index.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "research_history_latest.md"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _entry_from_current() -> dict[str, Any]:
    manifest = _read(_MANIFEST, {})
    if not manifest:
        raise RuntimeError("research_manifest_latest.json is required before indexing a burst")
    burst = str(manifest.get("burst_id") or "")
    manifest_sha = str(manifest.get("manifest_content_sha256") or "")
    if not burst or not manifest_sha:
        raise RuntimeError("manifest must contain burst_id and manifest_content_sha256")
    health = _read(_HEALTH, {})
    backlog = _read(_BACKLOG, {})
    frontier = _read(_FRONTIER, {})
    environment = _read(_ENVIRONMENT, {})
    # v3 manifests promise an execution-environment anchor. Do not silently index a stale/missing
    # environment file as though it described this burst. Older v1/v2 manifests remain readable.
    if int(manifest.get("version", 0) or 0) >= 3:
        if not environment:
            raise RuntimeError(f"manifest v3 burst {burst} has no execution environment fingerprint")
        if str(environment.get("burst_id") or "") != burst:
            raise RuntimeError(
                f"environment fingerprint burst mismatch: manifest={burst} environment={environment.get('burst_id')}"
            )
    progress = frontier.get("progress_ratchet") or {}
    source = manifest.get("source_code") or {}
    core = environment.get("core_versions") or {}
    return {
        "burst_id": burst,
        "burst_generated_at": manifest.get("burst_generated_at"),
        "manifest_content_sha256": manifest_sha,
        "manifest_archive": f"ai_lab/reports/easy/manifests/{burst}.json",
        "research_source_git_sha": source.get("research_source_git_sha") or source.get("git_sha"),
        "evidence_snapshot_git_sha": source.get("evidence_snapshot_git_sha"),
        "research_workflow_run_id": source.get("research_workflow_run_id"),
        "research_workflow_run_number": source.get("research_workflow_run_number"),
        "infrastructure_health": {
            "healthy": health.get("healthy"),
            "strict_failure_count": int(health.get("strict_failure_count", 0) or 0),
            "warning_count": int(health.get("warning_count", 0) or 0),
        },
        "operations": {
            "active_backlog_count": int(backlog.get("active_count", 0) or 0),
            "recommended_next": backlog.get("recommended_next"),
        },
        "planning_progress": {
            "status": progress.get("status"),
            "new_question_count": len(progress.get("new_question_keys") or []),
            "replicated_question_count": len(progress.get("replicated_question_keys") or []),
            "next_burst_escape_required": bool(progress.get("next_burst_escape_required")),
        },
        "environment_anchor": {
            "burst_id": environment.get("burst_id"),
            "python": (environment.get("python") or {}).get("version_info"),
            "numpy": core.get("numpy"),
            "scipy": core.get("scipy"),
            "requirements_txt_sha256": (environment.get("contracts") or {}).get("requirements_txt_sha256"),
        },
        "semantics": {
            "navigation_summary_is_scientific_evidence": False,
            "planning_progress_is_scientific_confidence": False,
            "operations_priority_routes_physical_compute": False,
            "manifest_hash_proves_scientific_claim": False,
        },
    }


def build_index(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = _read(_OUTPUT, {"entries": []}) if existing is None else existing
    current = _entry_from_current()
    rows = [dict(row) for row in (existing.get("entries") or []) if isinstance(row, dict)]
    by_burst = {str(row.get("burst_id")): row for row in rows if row.get("burst_id")}
    old = by_burst.get(current["burst_id"])
    if old is not None:
        if str(old.get("manifest_content_sha256") or "") != current["manifest_content_sha256"]:
            raise RuntimeError(
                f"research index collision for {current['burst_id']}: manifest identity changed"
            )
        # Idempotent refresh is allowed only when the immutable identity matches. Replace navigation
        # fields so an interrupted first write can be repaired without changing the burst's provenance.
        by_burst[current["burst_id"]] = current
    else:
        by_burst[current["burst_id"]] = current
    ordered = sorted(
        by_burst.values(),
        key=lambda row: (str(row.get("burst_generated_at") or ""), str(row.get("burst_id") or "")),
    )
    return {
        "version": 1,
        "mode": "manifest-backed-research-burst-index",
        "entries": ordered,
        "count": len(ordered),
        "latest_burst": current["burst_id"],
        "latest_manifest_content_sha256": current["manifest_content_sha256"],
        "policy": {
            "git_history_remains_authoritative": True,
            "manifest_remains_per_burst_provenance_authority": True,
            "same_burst_different_manifest_is_error": True,
            "index_changes_scientific_truth": False,
            "index_promotes_rooms_or_levels": False,
        },
    }


def render_markdown(index: dict[str, Any], *, limit: int = 24) -> str:
    rows = list(index.get("entries") or [])[-max(1, int(limit)):]
    lines = [
        "# Research Burst History",
        "",
        "Manifest-backed navigation view. This is not a scientific confidence ranking.",
        "",
    ]
    for row in reversed(rows):
        health = row.get("infrastructure_health") or {}
        progress = row.get("planning_progress") or {}
        env = row.get("environment_anchor") or {}
        lines.append(
            f"- `{row.get('burst_id')}` — health={health.get('healthy')} "
            f"progress={progress.get('status')} newQ={progress.get('new_question_count')} "
            f"numpy={env.get('numpy')} scipy={env.get('scipy')} "
            f"evidence=`{row.get('evidence_snapshot_git_sha')}`"
        )
    lines.extend([
        "",
        "Each row points to an immutable manifest and an exact evidence Git commit when available. "
        "Planning/health fields are navigation metadata only.",
        "",
    ])
    return "\n".join(lines)


def run(*, persist: bool = True) -> dict[str, Any]:
    index = build_index()
    if persist:
        _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        _OUTPUT.write_text(json.dumps(index, indent=2, ensure_ascii=False))
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(render_markdown(index))
    return index


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Update compact manifest-backed research burst index")
    p.add_argument("--no-record", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    index = run(persist=not args.no_record)
    print(
        f"Research Index: count={index.get('count')} latest={index.get('latest_burst')} "
        f"manifest={index.get('latest_manifest_content_sha256')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
