"""Production entry point for strict geometry + promising leads + zero-to-fission frontier research."""
from __future__ import annotations

from ai_lab.dream import adaptive
from ai_lab.dream import adaptive_v5
from ai_lab.dream.strict_followup_loop import _install_strict_followup_geometry
from ai_lab.dream.strict_loop import _install_strict_geometry


def _install_path_frontier_focus() -> None:
    """Let only the bounded hypothesis/boundary lanes notice the deepest path frontier.

    Broad unexplored/random/breaker floors remain enforced by adaptive._normalize.  This does not
    create a triangle or a split; it simply reuses start conditions from a naturally deeper run.
    """
    original = adaptive.focus_from_report

    def focus_from_report(report):
        r = report or {}
        path = r.get("zero_to_fission_path") or {}
        if not path:
            ar = r.get("adaptive_research") or {}
            path = ar.get("zero_to_fission_path") or ((ar.get("triangle_hypothesis") or {}).get("zero_to_fission_path") or {})
        candidate = path.get("best_frontier_candidate") or {}
        depth = int(candidate.get("depth", -1))
        knobs = candidate.get("knobs") or {}
        family = candidate.get("family")
        if depth >= 4 and family and isinstance(knobs, dict) and knobs:
            return {
                "family": family,
                "knobs": knobs,
                "source_event_id": f"zero-to-fission-depth-{depth}",
                "source_path_depth": depth,
                "source": "zero-to-fission-frontier",
            }
        return original(report)

    adaptive.focus_from_report = focus_from_report


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    _install_path_frontier_focus()
    return adaptive_v5.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
