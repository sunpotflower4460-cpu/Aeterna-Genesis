"""Production entrypoint for Research Continuity plus relation-instrument measurement state."""
from __future__ import annotations

from ai_lab.dream import relation_continuity_patch
from ai_lab.dream import research_continuity_entrypoint as continuity


def main(argv: list[str] | None = None) -> int:
    relation_continuity_patch.install()
    return continuity.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
