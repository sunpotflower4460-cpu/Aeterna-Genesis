"""Production-compatible entry point for Adaptive Dream v7.

Strict geometry and Prefix Identity instrumentation remain identical to the v6 strict entry point.
The only additional layer is v7 hypothesis evolution/mission planning after the measured burst.
"""
from __future__ import annotations

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v7
from ai_lab.dream import prefix_audit
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    return adaptive_v7.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
