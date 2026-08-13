"""Fail-closed coherence audit for the runtime context of one autonomous research burst.

The scientific evidence, software environment and parsed research protocol are produced by different
pieces of infrastructure. This audit ensures their ``burst_id`` values still refer to the same run and
that the protocol/environment files retain their non-scientific provenance boundaries.

It is infrastructure only: matching hashes/configuration do not validate a physical claim and a mismatch
is not new physics; it means the run cannot be considered provenance-complete until investigated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_ENVIRONMENT = _REPO / "ai_lab" / "reports" / "easy" / "environment_latest.json"
_PROTOCOL = _REPO / "ai_lab" / "reports" / "easy" / "protocol_latest.json"


def _read_required(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"required {label} is missing: {path}")
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"required {label} is unreadable or malformed: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"required {label} must be a JSON object: {path}")
    return value


def build_audit(
    *, easy_path: Path | None = None, environment_path: Path | None = None,
    protocol_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    reports: dict[str, dict[str, Any]] = {}
    for key, path, label in (
        ("easy", easy_path or _EASY, "easy evidence"),
        ("environment", environment_path or _ENVIRONMENT, "execution environment"),
        ("protocol", protocol_path or _PROTOCOL, "parsed research protocol"),
    ):
        try:
            reports[key] = _read_required(path, label)
        except RuntimeError as exc:
            errors.append(str(exc))
            reports[key] = {}

    easy_burst = str(reports["easy"].get("burst_id") or "")
    env_burst = str(reports["environment"].get("burst_id") or "")
    protocol_burst = str(reports["protocol"].get("burst_id") or "")
    if not easy_burst:
        errors.append("easy evidence has no burst_id")
    if easy_burst and env_burst != easy_burst:
        errors.append(f"environment burst mismatch: easy={easy_burst} environment={env_burst or None}")
    if easy_burst and protocol_burst != easy_burst:
        errors.append(f"protocol burst mismatch: easy={easy_burst} protocol={protocol_burst or None}")

    env_semantics = reports["environment"].get("semantics") or {}
    if reports["environment"] and env_semantics.get("captures_secrets") is not False:
        errors.append("environment fingerprint must explicitly declare captures_secrets=false")

    capture = reports["protocol"].get("capture_policy") or {}
    if reports["protocol"]:
        if capture.get("recognized_parser_options_only") is not True:
            errors.append("protocol fingerprint must contain recognized parser options only")
        if capture.get("raw_shell_argv_recorded") is not False:
            errors.append("protocol fingerprint must not persist raw shell argv")
        if capture.get("arbitrary_environment_recorded") is not False:
            errors.append("protocol fingerprint must not persist arbitrary environment variables")
        if not str(reports["protocol"].get("protocol_sha256") or ""):
            errors.append("protocol fingerprint has no protocol_sha256")

    return {
        "version": 1,
        "mode": "research-runtime-context-coherence-audit",
        "burst_id": easy_burst or None,
        "valid": not errors,
        "errors": errors,
        "observed": {
            "easy_burst_id": easy_burst or None,
            "environment_burst_id": env_burst or None,
            "protocol_burst_id": protocol_burst or None,
            "protocol_sha256": reports["protocol"].get("protocol_sha256"),
            "environment_requirements_sha256": (
                reports["environment"].get("contracts") or {}
            ).get("requirements_txt_sha256"),
            "environment_workflow_sha256": (
                reports["environment"].get("contracts") or {}
            ).get("dream_loop_workflow_sha256"),
        },
        "integrity": {
            "runtime_context_is_scientific_evidence": False,
            "matching_context_proves_physical_claim": False,
            "context_mismatch_is_new_physics": False,
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit coherence of easy/environment/protocol burst context")
    parser.parse_args(argv)
    report = build_audit()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
