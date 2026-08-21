"""Production entrypoint for Free Hypothesis Lab with report-schema compatibility.

The strict/easy report intentionally evolves as new measurements are added.  Free Hypothesis planning
must read those measurements without copying or mutating strict evidence.  This adapter normalizes the
current ``geometry_summary`` layout (and the old top-level layout) into the small context consumed by
the exploratory planner, then delegates all simulation/provenance logic to ``free_hypothesis_lab``.
"""
from __future__ import annotations

from typing import Any

from ai_lab.dream import free_hypothesis_lab as lab


def extract_evidence_context(
    easy: dict[str, Any],
    deep: dict[str, Any],
    top_unknown: dict[str, Any],
) -> dict[str, Any]:
    geometry = easy.get("geometry_summary")
    if not isinstance(geometry, dict):
        geometry = easy
    return {
        "top_unknown": top_unknown,
        "pairs": int(geometry.get("persistent_pair_seen", 0) or 0),
        "triads": int(geometry.get("triad_local_energy_measured", 0) or 0),
        "energy_precedes_geometry": int(
            geometry.get("energy_asymmetry_peak_preceded_geometry_collapse", 0) or 0
        ),
        "triangle_split": int(geometry.get("fission_like_after_triangle", 0) or 0),
        "nontriangle_split": int(geometry.get("fission_like_after_control", 0) or 0),
        "triangle_seen": int(geometry.get("triangle_seen", 0) or 0),
        "nontriangle_seen": int(geometry.get("control_seen", 0) or 0),
        "deep_leads": len(deep.get("leads") or []),
        "easy_burst_id": easy.get("burst_id"),
        "geometry_detector_version": geometry.get("detector_version"),
    }


def current_evidence_context() -> dict[str, Any]:
    easy = lab._read(lab._EASY, {})
    deep = lab._read(lab._DEEP, {})
    return extract_evidence_context(easy, deep, lab._top_unknown_focus())


def install_context_adapter() -> None:
    # Planning-only monkeypatch.  No strict report/ledger is rewritten; simulation and provenance
    # remain exactly those of free_hypothesis_lab.py.
    lab._evidence_context = current_evidence_context


def main(argv: list[str] | None = None) -> int:
    install_context_adapter()
    return lab.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
