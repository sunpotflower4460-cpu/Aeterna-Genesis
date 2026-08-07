"""Production entry point that installs the stricter triangle/control geometry lane.

Keeping the geometry hypothesis as a replaceable observation layer makes it explicit that this
research question does not alter the field law, Level thresholds, or promotion gates.
"""
from __future__ import annotations

from ai_lab.dream import adaptive_loop as base
from ai_lab.dream import strict_geometry as strict


def _install_strict_geometry() -> None:
    # adaptive_loop calls these through its imported `hourly` module. Replacing only these four
    # observation/report functions leaves mass 2D, full start-side 3D, reproduction, and all truth
    # diagnostics untouched.
    base.hourly.run_geometry_probes = strict.run_geometry_probes
    base.hourly.geometry_summary = strict.geometry_summary
    base.hourly.update_triangle_hypothesis = strict.update_triangle_hypothesis
    base.hourly.write_easy_report = strict.write_easy_report


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
