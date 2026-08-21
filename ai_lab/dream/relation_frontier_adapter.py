"""Planning adapter connecting relation-only instruments to the autonomous frontier.

An implemented instrument must stop appearing as missing engineering debt even when it has not produced a
scientific lead.  This adapter adds a third state, ``MEASURED``: the question is now measurable, but the
observations have not met the predeclared multi-run/multi-size candidate criteria.

``LEAD`` remains a planning lead, never a truth gate or a claim of physical space/life/division.
"""
from __future__ import annotations

from typing import Any

from ai_lab.dream import frontier_expander

_ORIGINAL_CAPABILITY_MAP = frontier_expander._capability_map
_ORIGINAL_INSTRUMENT_REQUESTS = frontier_expander._instrument_requests
_INSTALLED = False

_REQUEST_TO_CAPABILITY = {
    "metric-from-relations": "emergent_metric_geometry",
    "identity-continuity": "persistent_individual_identity",
    "lineage-accounting": "division_with_inheritance",
}


def _capability_map(report: dict[str, Any], root_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _ORIGINAL_CAPABILITY_MAP(report, root_report)
    measured = ((root_report.get("relation_instrument_summary") or {}).get("capabilities") or {})
    by_id = {str(row.get("id")): row for row in rows}
    notes = {
        "emergent_metric_geometry": "relation-only metric instrument active with permutation, rewire and holdout controls",
        "persistent_individual_identity": "relation-only structural identity tracker active with shuffled-time/ambiguity control",
        "division_with_inheritance": "persistent-parent/daughter lineage accounting instrument active with unrelated-pair control",
    }
    for cid, evidence in measured.items():
        if cid not in by_id or not isinstance(evidence, dict):
            continue
        status = str(evidence.get("instrument_status") or "UNMEASURED")
        if status not in {"MEASURED", "LEAD"}:
            continue
        by_id[cid]["status"] = status
        by_id[cid]["evidence"] = notes.get(cid, "measurement instrument active") + (
            "; controlled multi-size candidate present" if status == "LEAD" else "; no controlled multi-size lead yet"
        )
        by_id[cid]["instrument_measured"] = True
        by_id[cid]["planner_lead_is_scientific_truth"] = False
    return rows


def _instrument_requests(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = _ORIGINAL_INSTRUMENT_REQUESTS(capabilities)
    status = {str(row.get("id")): str(row.get("status")) for row in capabilities}
    out = []
    for request in rows:
        rid = str(request.get("id") or "")
        cid = _REQUEST_TO_CAPABILITY.get(rid)
        # Once the instrument is active, lack of a positive result is science, not missing engineering.
        if cid and status.get(cid) in {"MEASURED", "LEAD"}:
            continue
        out.append(request)
    return out


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    frontier_expander._capability_map = _capability_map
    frontier_expander._instrument_requests = _instrument_requests
    _INSTALLED = True


def uninstall_for_tests() -> None:
    global _INSTALLED
    frontier_expander._capability_map = _ORIGINAL_CAPABILITY_MAP
    frontier_expander._instrument_requests = _ORIGINAL_INSTRUMENT_REQUESTS
    _INSTALLED = False
