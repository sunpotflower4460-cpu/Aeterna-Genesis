"""Production adapter that makes Safe Research Maintenance refresh the topic-diverse handoff.

The underlying maintenance policy remains non-destructive.  This module only installs the production
Research Continuity adapter before delegating to ``research_maintenance``.
"""
from __future__ import annotations

from ai_lab.dream import research_continuity_entrypoint as continuity
from ai_lab.dream import research_maintenance as maintenance


def install_continuity_adapter() -> None:
    maintenance.research_continuity = continuity


def main(argv: list[str] | None = None) -> int:
    install_continuity_adapter()
    return maintenance.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
