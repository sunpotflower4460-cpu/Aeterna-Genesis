"""Parse and audit the production ``strict_goal_loop`` command from workflow YAML.

This is configuration-drift infrastructure.  It ensures a workflow edit cannot silently disable broad,
open-ended, Root, Deep-Time or frontier research simply because a CLI flag disappeared or stopped parsing.
The audit says nothing about whether a scientific result is interesting or correct.
"""
from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path
from typing import Any

import yaml

from ai_lab.dream import protocol_fingerprint

_REPO = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPO / ".github" / "workflows" / "dream-loop.yml"
_TARGET_STEP = "Run hourly Adaptive Dream v8 Pure Genesis R0 + NØ research"
_ENTRYPOINT = "ai_lab.dream.strict_goal_loop"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _step_script(workflow: dict[str, Any]) -> str:
    jobs = workflow.get("jobs") or {}
    job = jobs.get("research-burst") or {}
    for step in job.get("steps") or []:
        if isinstance(step, dict) and str(step.get("name") or "") == _TARGET_STEP:
            script = str(step.get("run") or "")
            if not script:
                raise RuntimeError(f"production step {_TARGET_STEP!r} has no run script")
            return script
    raise RuntimeError(f"production step {_TARGET_STEP!r} was not found")


def _logical_shell_lines(script: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for raw in script.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if current:
            current += " " + line
        else:
            current = line
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        lines.append(current)
        current = ""
    if current:
        lines.append(current)
    return lines


def production_argv(path: Path | None = None) -> list[str]:
    path = path or _WORKFLOW
    workflow = yaml.safe_load(path.read_text())
    script = _step_script(workflow)
    for logical in _logical_shell_lines(script):
        tokens = shlex.split(logical)
        needle = ["python", "-m", _ENTRYPOINT]
        for i in range(0, max(0, len(tokens) - len(needle) + 1)):
            if tokens[i:i + len(needle)] == needle:
                return tokens[i + len(needle):]
    raise RuntimeError(f"could not locate `python -m {_ENTRYPOINT}` in production workflow step")


def build_contract(path: Path | None = None) -> dict[str, Any]:
    path = path or _WORKFLOW
    argv = production_argv(path)
    parsed = protocol_fingerprint.parse_protocol(argv)
    config = parsed["parsed_config"]
    required_nonzero = {
        "trials": "broad 2D search",
        "native3d_trials": "native 3D anti-bias search",
        "followup_trials_2d": "promising-lead followup",
        "fission_path_trials_2d": "F reference-route control",
        "deep_time_max_leads": "Deep-Time extension",
        "open_ended_probes": "open-ended emergence discovery",
        "unknown_followup_max_patterns": "recurrent X verification",
        "root_law_trials": "Pure Genesis R0 candidate-law search",
        "frontier_experiments": "information-yield frontier experiments",
    }
    disabled = [
        {"option": key, "purpose": purpose, "value": config.get(key)}
        for key, purpose in required_nonzero.items()
        if int(config.get(key, 0) or 0) <= 0
    ]
    errors: list[str] = []
    if disabled:
        errors.append("one or more production research lanes are accidentally disabled")
    if config.get("no_record") is True:
        errors.append("production protocol unexpectedly enables --no-record")
    if config.get("no_refresh_app") is True:
        # Not a scientific failure, but the production workflow currently promises generated human views.
        errors.append("production protocol unexpectedly disables app/report refresh")
    return {
        "version": 1,
        "mode": "production-research-protocol-contract",
        "workflow_path": str(path.relative_to(_REPO)) if path.is_relative_to(_REPO) else str(path),
        "workflow_sha256": _sha256(path),
        "entrypoint": _ENTRYPOINT,
        "argv": argv,
        **parsed,
        "required_nonzero_lanes": required_nonzero,
        "disabled_required_lanes": disabled,
        "errors": errors,
        "valid": not errors,
        "semantics": {
            "required_lane_means_scientific_success_required": False,
            "protocol_contract_changes_scientific_truth": False,
            "protocol_hash_is_physical_observable": False,
            "workflow_arguments_are_target_outcomes": False,
        },
    }


def main() -> int:
    report = build_contract()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
