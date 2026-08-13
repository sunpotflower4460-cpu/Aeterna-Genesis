"""Immutable provenance manifest for each autonomous Aeterna research burst.

The manifest hashes the evidence/planning/view files that exist at the end of a burst and records the
research-workflow identity that produced them.  It is provenance infrastructure, not a scientific result
and not a confidence score.

A per-burst archive is write-once in meaning: re-running the manifest builder with identical content is
allowed; producing different content for the same burst raises an error instead of silently rewriting
history.  ``latest.json`` remains a convenience alias.  Existing archives can also be verified against
the current files without rewriting them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_LATEST = _REPO / "ai_lab" / "reports" / "easy" / "research_manifest_latest.json"
_ARCHIVE_DIR = _REPO / "ai_lab" / "reports" / "easy" / "manifests"

_SCIENTIFIC_EVIDENCE = (
    "ai_lab/reports/easy/latest.json",
    "ai_lab/reports/easy/root_latest.json",
    "ai_lab/reports/emergence/latest.json",
    "ai_lab/reports/crossworld/latest.json",
    "ai_lab/reports/crossworld/replication_latest.json",
    "ai_lab/reports/multiworld/latest.json",
    "ai_lab/discoveries/unknown_followups.json",
    "ai_lab/discoveries/deep_time_fission.json",
    "ai_lab/discoveries/cross_world_emergence.json",
    "ai_lab/discoveries/question_critic.json",
)

_PLANNING_STATE = (
    "ai_lab/reports/easy/frontier_latest.json",
    "ai_lab/reports/easy/nothing_latest.json",
    "ai_lab/reports/easy/research_health_latest.json",
    "ai_lab/discoveries/research_memory.json",
    "ai_lab/discoveries/frontier_expansion.json",
    "ai_lab/discoveries/hypothesis_graph.json",
    "ai_lab/discoveries/hypothesis_history.json",
    "ai_lab/discoveries/hypothesis_portfolio.json",
    "ai_lab/discoveries/goal_progress.json",
)

_DERIVED_HUMAN_VIEWS = (
    "CURRENT_RESEARCH.md",
    "ai_lab/reports/easy/latest.md",
    "ai_lab/reports/easy/research_compass_latest.json",
    "ai_lab/reports/easy/research_compass_latest.md",
    "ai_lab/reports/easy/research_health_latest.md",
    "ai_lab/reports/easy/nothing_latest.md",
    "ai_lab/reports/easy/nothing_latest.png",
)


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _entry(relative: str) -> dict[str, Any] | None:
    path = _REPO / relative
    if not path.exists() or not path.is_file():
        return None
    return {
        "path": relative,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def _entries(paths: tuple[str, ...]) -> list[dict[str, Any]]:
    return [row for rel in paths if (row := _entry(rel)) is not None]


def _repo_git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_REPO, text=True, stderr=subprocess.DEVNULL
        ).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _research_git_sha() -> str | None:
    for name in ("AETERNA_RESEARCH_HEAD_SHA", "GITHUB_SHA"):
        value = str(os.environ.get(name) or "").strip()
        if value:
            return value
    return _repo_git_sha()


def _research_env(primary: str, fallback: str) -> str | None:
    value = str(os.environ.get(primary) or os.environ.get(fallback) or "").strip()
    return value or None


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content_identity(manifest: dict[str, Any]) -> str:
    """Hash the complete provenance record except for its own hash field."""
    payload = dict(manifest)
    payload.pop("manifest_content_sha256", None)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def build_manifest() -> dict[str, Any]:
    easy = _read(_EASY, {})
    burst = str(easy.get("burst_id") or "")
    if not burst:
        raise RuntimeError("cannot build research manifest without easy/latest burst_id")
    generated_at = easy.get("generated_at")

    scientific = _entries(_SCIENTIFIC_EVIDENCE)
    planning = _entries(_PLANNING_STATE)
    views = _entries(_DERIVED_HUMAN_VIEWS)
    manifest: dict[str, Any] = {
        "version": 2,
        "mode": "immutable-research-provenance-manifest",
        "burst_id": burst,
        "burst_generated_at": generated_at,
        "source_code": {
            "git_sha": _research_git_sha(),
            "research_workflow_run_id": _research_env("AETERNA_RESEARCH_RUN_ID", "GITHUB_RUN_ID"),
            "research_workflow_run_number": _research_env("AETERNA_RESEARCH_RUN_NUMBER", "GITHUB_RUN_NUMBER"),
            "research_workflow_run_attempt": _research_env("AETERNA_RESEARCH_RUN_ATTEMPT", "GITHUB_RUN_ATTEMPT"),
            "research_ref": _research_env("AETERNA_RESEARCH_REF", "GITHUB_REF"),
        },
        "scientific_evidence": scientific,
        "planning_and_integrity_state": planning,
        "derived_human_views": views,
        "counts": {
            "scientific_evidence_files": len(scientific),
            "planning_state_files": len(planning),
            "derived_view_files": len(views),
        },
        "semantics": {
            "file_hash_means_scientific_validity": False,
            "manifest_is_scientific_evidence": False,
            "derived_views_are_authoritative_over_raw_evidence": False,
            "negative_results_are_preserved": True,
            "same_burst_archive_may_be_silently_rewritten": False,
        },
        "integrity": {
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }
    manifest["manifest_content_sha256"] = _content_identity(manifest)
    return manifest


def _archive_payload(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def persist_manifest(manifest: dict[str, Any]) -> Path:
    burst = str(manifest["burst_id"])
    archive = _ARCHIVE_DIR / f"{burst}.json"
    payload = _archive_payload(manifest)
    if archive.exists():
        existing = _read(archive, {})
        if not existing or existing.get("manifest_content_sha256") != manifest.get("manifest_content_sha256"):
            raise RuntimeError(
                f"immutable manifest collision for {burst}: existing provenance differs from current burst state"
            )
    else:
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(payload)
    _LATEST.parent.mkdir(parents=True, exist_ok=True)
    _LATEST.write_text(payload)
    return archive


def verify_existing_manifest() -> dict[str, Any]:
    """Verify archived file hashes for the current burst without changing any file."""
    easy = _read(_EASY, {})
    burst = str(easy.get("burst_id") or "")
    archive_path = _ARCHIVE_DIR / f"{burst}.json"
    archived = _read(archive_path, {})
    if not burst or not archived:
        return {
            "burst_id": burst or None,
            "archive": str(archive_path.relative_to(_REPO)) if burst else None,
            "valid": False,
            "errors": ["manifest archive is missing or unreadable for current burst"],
            "checked_files": 0,
        }

    errors: list[str] = []
    checked = 0
    for group in ("scientific_evidence", "planning_and_integrity_state", "derived_human_views"):
        for row in archived.get(group) or []:
            relative = str(row.get("path") or "")
            if not relative:
                errors.append(f"{group}: archived row has no path")
                continue
            path = _REPO / relative
            checked += 1
            if not path.exists() or not path.is_file():
                errors.append(f"missing: {relative}")
                continue
            actual = _sha256(path)
            if actual != str(row.get("sha256") or ""):
                errors.append(f"hash mismatch: {relative}")
    return {
        "burst_id": burst,
        "archive": str(archive_path.relative_to(_REPO)),
        "valid": not errors,
        "errors": errors,
        "checked_files": checked,
        "verification_is_scientific_truth_gate": False,
    }


def run(*, persist: bool = True) -> dict[str, Any]:
    manifest = build_manifest()
    if persist:
        persist_manifest(manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build or verify an immutable per-burst provenance manifest")
    p.add_argument("--no-record", action="store_true", help="build only; do not write latest/archive files")
    p.add_argument("--verify-existing", action="store_true", help="verify current files against the archived current-burst manifest")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_existing:
        result = verify_existing_manifest()
        print(
            f"Research Manifest Verify: burst={result.get('burst_id')} valid={result.get('valid')} "
            f"checked={result.get('checked_files')} errors={len(result.get('errors') or [])}"
        )
        return 0 if result.get("valid") else 3
    manifest = run(persist=not args.no_record)
    print(
        f"Research Manifest: burst={manifest.get('burst_id')} "
        f"sha256={manifest.get('manifest_content_sha256')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
