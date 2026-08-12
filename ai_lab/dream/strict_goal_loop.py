"""Production-compatible entry point for Adaptive Dream v8 + strict Nothing Genesis.

Strict geometry and Prefix Identity instrumentation remain identical to the v6/v7 entry point.
The production command name is kept for workflow compatibility. Adaptive Dream v8 still performs the
R0/downstream research, then the NØ control is executed as a separate, stricter layer with zero physical
givens. NØ never changes scientific gates, Rooms or official Levels.
"""
from __future__ import annotations

import sys

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import adaptive_v8
from ai_lab.dream import nothing_genesis
from ai_lab.dream import prefix_audit
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    prefix_audit.install_geometry_digest_wrapper(base.hourly, strict)

    code = adaptive_v8.main(argv)
    if code != 0:
        return code

    # NØ is intentionally run *after* the ordinary/R0 burst. It does not borrow that burst's state,
    # seed, geometry, law or clock; it only uses the report burst_id as external bookkeeping metadata.
    raw_args = list(sys.argv[1:] if argv is None else argv)
    persist = "--no-record" not in raw_args
    nothing_genesis.run_nothing_research(persist=persist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
