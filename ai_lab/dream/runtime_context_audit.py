"""Fail-closed coherence audit for the runtime context of one autonomous research burst.

The scientific evidence, software environment and parsed research protocol are produced by different
pieces of infrastructure. This audit ensures their ``burst_id`` values refer to the same run and can also
bind the aliases to the exact triggering Dream workflow run/source commit.

It is infrastructure only: matching hashes/configuration do not validate a physical claim and a mismatch
is not new physics; it means the run cannot be considered provenance-complete until investigated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive_v8

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_ENVIRONMENT = _REPO / "ai_lab" / "reports" / "easy" / "environment_latest.json"
_PROTOCOL = _REPO / "ai_lab" / "reports" / "easy" / "protocol_latest.json"

_PROTOCOL_TOP_LEVEL = {
    "version", "mode", "burst_id", "generated_at", "entrypoint", "parsed_config",
    "protocol_sha256", "recognized_option_count", "capture_policy", "semantics", "integrity",
}
_PROTOCOL_CAPTURE_KEYS = {
    "raw_shell_argv_recorded", "arbitrary_environment_recorded",
    "recognized_parser_options_only", "secrets_expected",
}


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


def _known_parser_keys() -> set[str]:
    return set(vars(adaptive_v8.build_parser().parse_args([])))


def _protocol_payload_errors(protocol: dict[str, Any]) -> list[str]:
    """Validate actual captured content, not only the producer's self-declared policy booleans."""
    errors: list[str] = []
    extra_top = sorted(set(protocol) - _PROTOCOL_TOP_LEVEL)
    if extra_top:
        errors.append(f"protocol fingerprint contains forbidden/unknown top-level fields: {extra_top}")
    config = protocol.get("parsed_config")
    if not isinstance(config, dict):
        errors.append("protocol parsed_config must be an object")
        config = {}
    else:
        unknown_options = sorted(set(str(k) for k in config) - _known_parser_keys())
        missing_options = sorted(_known_parser_keys() - set(str(k) for k in config))
        if unknown_options:
            errors.append(f"protocol parsed_config contains unrecognized options: {unknown_options}")
        if missing_options:
            errors.append(f"protocol parsed_config is missing recognized options: {missing_options}")
        canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        actual_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if str(protocol.get("protocol_sha256") or "") != actual_sha:
            errors.append("protocol_sha256 does not match parsed_config content")
        if int(protocol.get("recognized_option_count", -1) or 0) != len(config):
            errors.append("recognized_option_count does not match parsed_config size")
    capture = protocol.get("capture_policy")
    if not isinstance(capture, dict):
        errors.append("protocol capture_policy must be an object")
        capture = {}
    extra_capture = sorted(set(capture) - _PROTOCOL_CAPTURE_KEYS)
    if extra_capture:
        errors.append(f"protocol capture_policy contains unknown fields: {extra_capture}")
    if capture.get("recognized_parser_options_only") is not True:
        errors.append("protocol fingerprint must contain recognized parser options only")
    if capture.get("raw_shell_argv_recorded") is not False:
        errors.append("protocol fingerprint must not persist raw shell argv")
    if capture.get("arbitrary_environment_recorded") is not False:
        errors.append("protocol fingerprint must not persist arbitrary environment variables")
    if capture.get("secrets_expected") is not False:
        errors.append("protocol fingerprint must explicitly declare secrets_expected=false")
    return errors


def build_audit(
    *, easy_path: Path | None = None, environment_path: Path | None = None,
    protocol_path: Path | None = None, expected_run_id: str | None = None,
    expected_source_sha: str | None = None,
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
    execution = reports["environment"].get("github_execution") or {}
    expected_run = str(expected_run_id or "").strip()
    expected_sha = str(expected_source_sha or "").strip()
    observed_run = str(execution.get("run_id") or "").strip()
    observed_sha = str(execution.get("sha") or "").strip()
    if expected_run and observed_run != expected_run:
        errors.append(
            f"environment workflow run mismatch: expected={expected_run} observed={observed_run or None}"
        )
    if expected_sha and observed_sha != expected_sha:
        errors.append(
            f"environment source SHA mismatch: expected={expected_sha} observed={observed_sha or None}"
        )

    if reports["protocol"]:
        errors.extend(_protocol_payload_errors(reports["protocol"]))

    return {
        "version": 2,
        "mode": "research-runtime-context-coherence-audit",
        "burst_id": easy_burst or None,
        "valid": not errors,
        "errors": errors,
        "expected_trigger": {
            "workflow_run_id": expected_run or None,
            "source_sha": expected_sha or None,
        },
        "observed": {
            "easy_burst_id": easy_burst or None,
            "environment_burst_id": env_burst or None,
            "protocol_burst_id": protocol_burst or None,
            "environment_workflow_run_id": observed_run or None,
            "environment_source_sha": observed_sha or None,
            "protocol_sha256": reports["protocol"].get("protocol_sha256"),
            "environment_requirements_sha256": (reports["environment"].get("contracts") or {}).get("requirements_txt_sha256"),
            "environment_workflow_sha256": (reports["environment"].get("contracts") or {}).get("dream_loop_workflow_sha256"),
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
    parser.add_argument("--expected-run-id", default=None)
    parser.add_argument("--expected-source-sha", default=None)
    args = parser.parse_args(argv)
    report = build_audit(
        expected_run_id=args.expected_run_id, expected_source_sha=args.expected_source_sha
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
