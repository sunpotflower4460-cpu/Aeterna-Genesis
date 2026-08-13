"""Record the exact parsed research protocol used by ``strict_goal_loop``.

The production workflow command is currently visible in YAML, but a durable per-burst record is safer:
workflow defaults can change, parser defaults can change, and manual/dispatch runs may use different
arguments.  This module records only *recognized parsed research options* from Adaptive v8's parser; it
never copies arbitrary shell arguments, environment variables, tokens or secrets.

Protocol identity is reproducibility/planning metadata only.  It cannot change physics, scientific gates,
Rooms, official Levels or claim confidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from ai_lab.dream import adaptive_v8

_REPO = Path(__file__).resolve().parents[2]
_OUTPUT = _REPO / "ai_lab" / "reports" / "easy" / "protocol_latest.json"


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    return str(value)


def parse_protocol(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Parse exactly the options accepted by the production Adaptive v8 entry parser."""
    args = adaptive_v8.build_parser().parse_args(None if argv is None else list(argv))
    config = {
        str(key): _jsonable(value)
        for key, value in sorted(vars(args).items())
    }
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "parsed_config": config,
        "protocol_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "recognized_option_count": len(config),
    }


def build_protocol(*, burst_id: str, argv: Sequence[str] | None = None) -> dict[str, Any]:
    burst = str(burst_id or "").strip()
    if not burst:
        raise ValueError("burst_id is required")
    parsed = parse_protocol(argv)
    return {
        "version": 1,
        "mode": "research-protocol-fingerprint",
        "burst_id": burst,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entrypoint": "ai_lab.dream.strict_goal_loop",
        **parsed,
        "capture_policy": {
            "raw_shell_argv_recorded": False,
            "arbitrary_environment_recorded": False,
            "recognized_parser_options_only": True,
            "secrets_expected": False,
        },
        "semantics": {
            "protocol_hash_proves_scientific_claim": False,
            "protocol_is_physical_observable": False,
            "same_protocol_guarantees_bitwise_result": False,
            "same_protocol_improves_reproducibility": True,
        },
        "integrity": {
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }


def run(*, burst_id: str, argv: Sequence[str] | None = None, persist: bool = True) -> dict[str, Any]:
    report = build_protocol(burst_id=burst_id, argv=argv)
    if persist:
        _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        _OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Record parsed Adaptive research protocol")
    p.add_argument("--burst-id", required=True)
    p.add_argument("--no-record", action="store_true")
    p.add_argument("protocol_args", nargs=argparse.REMAINDER)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    protocol_args = list(args.protocol_args)
    if protocol_args[:1] == ["--"]:
        protocol_args = protocol_args[1:]
    report = run(
        burst_id=args.burst_id,
        argv=protocol_args,
        persist=not args.no_record,
    )
    print(
        f"Research Protocol: burst={report.get('burst_id')} "
        f"options={report.get('recognized_option_count')} sha256={report.get('protocol_sha256')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
