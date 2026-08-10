"""Production entry point for Adaptive Dream v6 open-ended emergence research.

Strict triangle/F-path measurements remain available as one bounded reference lane, but they no
longer override the Research Director's main focus.  Open-ended transition discovery, Question
Critic, Prefix Identity Audit and the existing broad/3D/follow-up lanes run side by side.
"""
from __future__ import annotations

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v6
from ai_lab.dream import prefix_audit
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def _install_path_frontier_focus() -> None:
    """Legacy compatibility hook; intentionally a no-op in v6.

    v5 used to let an F4+ candidate replace the Director's generic focus.  That made one human-written
    route too central.  F-path candidates still receive their own small follow-up/Deep-Time budgets,
    but broad research direction is no longer rewritten around F-progress.
    """
    return None


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    # Add an independent t=0 endpoint digest only to the small set of naturally observed F4+ probes.
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)
    # Deliberately DO NOT call _install_path_frontier_focus().
    return adaptive_v6.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
