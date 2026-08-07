"""Small fail-open watchdog for the hourly Dream schedule.

The primary schedule fires at :17.  A second schedule at :47 is only a safety net:
it runs a research burst when the latest completed easy report is older than the
configured freshness window.  A malformed/missing timestamp fails open so a broken
report can never silently suppress research.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("generated_at is missing")
    text = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("generated_at must include a timezone")
    return dt.astimezone(timezone.utc)


def should_run_backup(
    latest_path: str | Path,
    *,
    now: datetime | None = None,
    max_age_minutes: float = 70.0,
) -> tuple[bool, str]:
    """Return whether the :47 safety-net burst should run.

    Fail-open cases (missing file, bad JSON/timestamp, implausibly future report)
    intentionally return True.  A healthy recent report returns False.
    """
    path = Path(latest_path)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not path.exists():
        return True, "latest report is missing"
    try:
        doc = json.loads(path.read_text())
        generated = _parse_time(doc.get("generated_at"))
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        return True, f"latest report cannot be trusted: {exc}"

    age_minutes = (now - generated).total_seconds() / 60.0
    if age_minutes < -5.0:
        return True, f"latest report is implausibly in the future ({age_minutes:.1f} min)"
    if age_minutes > float(max_age_minutes):
        return True, f"latest completed report is stale ({age_minutes:.1f} min old)"
    return False, f"latest completed report is fresh ({max(0.0, age_minutes):.1f} min old)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Decide whether the Dream :47 backup burst is needed")
    ap.add_argument("--latest", default="ai_lab/reports/easy/latest.json")
    ap.add_argument("--max-age-minutes", type=float, default=70.0)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    run, reason = should_run_backup(a.latest, max_age_minutes=a.max_age_minutes)
    print("true" if run else "false")
    print(f"Dream watchdog: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
