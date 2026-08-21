"""Production adapter for topic-diverse continuity plus non-destructive X/relation cataloging.

The underlying maintenance policy remains non-destructive. This module installs the production Research
Continuity adapters, including relation-instrument measurement state, and asks maintenance to parse/catalog
the X-mechanism ledger when it exists. No source scientific evidence is deleted or rewritten.
"""
from __future__ import annotations

from pathlib import Path

from ai_lab.dream import relation_continuity_patch
from ai_lab.dream import research_continuity_entrypoint as continuity
from ai_lab.dream import research_maintenance as maintenance

_X_MECHANISMS = Path(__file__).resolve().parents[2] / "ai_lab" / "discoveries" / "x_mechanisms.json"


def install_production_adapters() -> None:
    relation_continuity_patch.install()
    maintenance.research_continuity = continuity
    maintenance._TRACKED_JSON = {
        **maintenance._TRACKED_JSON,
        "x_mechanisms": _X_MECHANISMS,
    }
    maintenance._OPTIONAL_NAMES = {*maintenance._OPTIONAL_NAMES, "x_mechanisms"}


def main(argv: list[str] | None = None) -> int:
    install_production_adapters()
    return maintenance.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
