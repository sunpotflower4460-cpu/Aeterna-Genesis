"""Production-compatible entry point for Adaptive Dream v8 Pure Genesis R0 research.

Strict geometry and Prefix Identity instrumentation remain identical to the v6/v7 entry point.
The production command name is kept for workflow compatibility, but the top research north star is now
Pure Genesis R0.  Existing v7 hypothesis evolution and all scientific truth gates remain intact.
"""
from __future__ import annotations

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v8
from ai_lab.dream import prefix_audit
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    return adaptive_v8.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
