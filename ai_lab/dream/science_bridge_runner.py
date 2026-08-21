"""Run only Science Bridge directions through Free Hypothesis Lab.

This wrapper deliberately reuses the Free Lab simulator/provenance machinery instead of creating a
second scientific truth path.  It swaps the direction notebook for the Science Bridge notebook in
memory, installs the current strict-report compatibility adapter, and then runs exactly those curated
literature-inspired directions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_lab.dream import free_hypothesis_entrypoint
from ai_lab.dream import free_hypothesis_lab as lab

_REPO = Path(__file__).resolve().parents[2]
_SCIENCE_DIRECTIONS = _REPO / "ai_lab" / "discoveries" / "science_bridge_directions.json"


def direction_count() -> int:
    try:
        doc = json.loads(_SCIENCE_DIRECTIONS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return sum(
        1 for row in (doc.get("directions") or [])
        if isinstance(row, dict) and row.get("enabled") is not False and row.get("experiment_type")
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run curated Science Bridge directions in Free Hypothesis Lab")
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    count = direction_count()
    if count <= 0:
        print("Science Bridge Runner: no executable curated directions; nothing to run.")
        return 0

    free_hypothesis_entrypoint.install_context_adapter()
    original = lab._DIRECTIONS
    try:
        lab._DIRECTIONS = _SCIENCE_DIRECTIONS
        cli = [
            "--max-hypotheses", str(count),
            "--replicates", str(max(1, args.replicates)),
            "--seed", str(args.seed),
        ]
        if args.quick:
            cli.append("--quick")
        if args.no_record:
            cli.append("--no-record")
        code = lab.main(cli)
    finally:
        lab._DIRECTIONS = original
    print(f"Science Bridge Runner: executed curated_directions={count} in exploratory Free Lab only.")
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
