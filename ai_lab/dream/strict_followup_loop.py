"""Production entry point: strict geometry controls + Adaptive Dream v4 follow-ups."""
from __future__ import annotations

from ai_lab.dream import adaptive_v4
from ai_lab.dream.strict_loop import _install_strict_geometry


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    return adaptive_v4.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
