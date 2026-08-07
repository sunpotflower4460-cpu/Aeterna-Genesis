"""Production entry point: strict geometry controls + Adaptive Dream v4 follow-ups."""
from __future__ import annotations

from ai_lab.dream import adaptive_v4
from ai_lab.dream import followups
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_loop import _install_strict_geometry


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    # Follow-up triangle replays must use the same strict detector as the main geometry lane.
    # Otherwise a lead could appear to reproduce only because its verification used a looser detector.
    followups.hourly._geometry_probe = strict._geometry_probe
    return adaptive_v4.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
