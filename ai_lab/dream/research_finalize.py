"""Finalize a research burst in a fixed, auditable order.

Order is intentionally one-way:

1. Research Compass derives a human-facing view and merges compact lessons.
2. Research Health audits the resulting infrastructure state without grading scientific success.
3. Research Manifest hashes the final evidence/planning/view state into an immutable burst record.

The manifest is written even when health finds an infrastructure error so uploaded CI/workflow artifacts
can preserve the failed state for diagnosis.  The process then exits non-zero.  No step changes physics,
initial conditions, scientific gates, Rooms, official Levels or hypothesis confidence.
"""
from __future__ import annotations

import argparse

from ai_lab.dream import research_compass
from ai_lab.dream import research_health
from ai_lab.dream import research_manifest


def run(*, persist: bool = True) -> dict:
    compass = research_compass.run(persist=persist)
    health = research_health.run(persist=persist)
    manifest = research_manifest.run(persist=persist)
    return {
        "compass": compass,
        "health": health,
        "manifest": manifest,
        "healthy": bool(health.get("healthy")),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Finalize Compass -> Health -> immutable provenance manifest")
    p.add_argument("--no-record", action="store_true", help="build/read only; do not write finalization files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = run(persist=not args.no_record)
    health = out["health"]
    manifest = out["manifest"]
    print(
        f"Research Finalize: burst={manifest.get('burst_id')} healthy={out['healthy']} "
        f"errors={health.get('strict_failure_count')} warnings={health.get('warning_count')} "
        f"manifest={manifest.get('manifest_content_sha256')}"
    )
    return 0 if out["healthy"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
