"""Deep-Time v2: historical-path semantics + Prefix Identity Audit.

The original Deep-Time worker correctly replays from t=0, but it used a whole-long-run Level
assessment when reconstructing F0..F4.  A structure that genuinely existed in the ordinary prefix
could therefore appear to 'fall back' from F4 to F1 simply because the much later endpoint changed.

v2 treats F-stages as historical observations: first verify that the ordinary prefix replays, then
append only genuinely later F5/F6/F7 transition evidence.  Prefix mismatches are quarantined instead
of being interpreted as physics.
"""
from __future__ import annotations

from typing import Any

from ai_lab.dream import deep_time as legacy
from ai_lab.dream import prefix_audit
from ai_lab.dream import strict_geometry as strict

_ORIGINAL_RUN = legacy.run_candidate
_ORIGINAL_REGISTER = legacy.register_and_run


def _baseline_depth(candidate: dict[str, Any]) -> int:
    return int(candidate.get("baseline_F_depth", candidate.get("depth", -1)))


def _historical_F_depth(prefix_depth: int, result: dict[str, Any]) -> int:
    """Extend a verified historical prefix; never erase an earlier stage because of a later endpoint."""
    depth = int(prefix_depth)
    if depth >= 4 and result.get("balance_collapse_seen"):
        depth = max(depth, 5)
    if depth >= 5 and result.get("pre_split_instability_candidate"):
        depth = max(depth, 6)
    if depth >= 6 and result.get("network_fission_candidate"):
        depth = max(depth, 7)
    return depth


def _prefix_classification(candidate: dict[str, Any], *, quick: bool) -> dict[str, Any]:
    """Replay exactly the ordinary window and reconstruct both F classification and detector history.

    Stored Deep-Time leads do not contain the mass-search reached_level field.  First let the legacy
    Deep-Time worker recompute Level from the ordinary-length trajectory, then feed that measured
    Level into the strict geometry detector so its compact series can be compared with the series
    recorded by the original ordinary geometry run.
    """
    prefix = _ORIGINAL_RUN(candidate, horizon_multiplier=0.0, quick=quick)
    measured_level = int(prefix.get("reached_level_for_path_measurement", 0))
    geometry = strict._geometry_probe({
        **candidate,
        "quick": bool(quick),
        "reached_level": measured_level,
    })
    path = geometry.get("zero_to_fission") or {}
    return {
        "F_depth": int(path.get("depth", -1)),
        "F_code": path.get("depth_code"),
        "triangle_seen": bool(geometry.get("triangle_seen")),
        "balance_collapse_seen": bool(geometry.get("balance_collapse_seen")),
        "observation_digest": prefix_audit.observation_digest(geometry.get("series")),
        "measured_level": measured_level,
    }


def run_candidate(candidate: dict[str, Any], *, horizon_multiplier: float, quick: bool = True) -> dict[str, Any]:
    result = _ORIGINAL_RUN(candidate, horizon_multiplier=horizon_multiplier, quick=quick)
    baseline = _baseline_depth(candidate)
    prefix = _prefix_classification(candidate, quick=quick)

    observation_check = prefix_audit.compare_digest(
        candidate.get("prefix_observation_digest"), prefix.get("observation_digest")
    )
    reconstructed_field = prefix_audit.replay_g001_endpoint(candidate, quick=quick)
    field_check = prefix_audit.compare_digest(candidate.get("prefix_state_digest"), reconstructed_field)
    classification_match = bool(prefix["F_depth"] == baseline) if baseline >= 0 else True

    if observation_check.get("match") is False:
        status = "OBSERVATION_PREFIX_MISMATCH_QUARANTINED"
        usable = False
    elif field_check.get("match") is False:
        status = "FIELD_RECONSTRUCTION_MISMATCH_QUARANTINED"
        usable = False
    elif not classification_match:
        status = "PREFIX_CLASSIFICATION_MISMATCH_QUARANTINED"
        usable = False
    elif observation_check.get("match") is True:
        status = "MATCH"
        usable = True
    else:
        status = "LEGACY_CLASSIFICATION_MATCH"
        usable = True

    corrected_depth = _historical_F_depth(prefix["F_depth"], result) if usable else prefix["F_depth"]
    result.update({
        "raw_full_horizon_F_depth": int(result.get("F_depth", -1)),
        "raw_full_horizon_F_code": result.get("F_code"),
        "prefix_replay_F_depth": prefix["F_depth"],
        "prefix_replay_F_code": prefix["F_code"],
        "prefix_replay_measured_level": prefix["measured_level"],
        "baseline_F_depth": baseline,
        "F_depth": corrected_depth,
        "F_code": f"F{corrected_depth}" if corrected_depth >= 0 else None,
        "prefix_identity_audit": {
            "version": 2,
            "status": status,
            "scientific_usable": usable,
            "baseline_F_depth": baseline,
            "prefix_replay_F_depth": prefix["F_depth"],
            "classification_match": classification_match,
            "actual_observation_history_check": observation_check,
            "independent_field_reconstruction_check": field_check,
            "prefix_is_same_t0_family_knobs_seed": True,
            "midrun_shape_seeded": False,
        },
        "historical_F_stages_are_monotone_observations": True,
        "evidence_quarantined": not usable,
    })
    return result


def _pre_register_with_digest(*, burst_id: str, path_summary: dict[str, Any]) -> None:
    doc = legacy._load()
    leads = doc.setdefault("leads", [])
    changed = False
    for candidate in path_summary.get("frontier_candidates") or []:
        if int(candidate.get("depth", -1)) < 4:
            continue
        key = legacy._candidate_key(candidate)
        lead = next((x for x in leads if x.get("lead_id") == key), None)
        if lead is None:
            lead = {
                "lead_id": key,
                "family": candidate.get("family"),
                "knobs": candidate.get("knobs") or {},
                "seed": candidate.get("seed"),
                "first_burst": burst_id,
                "last_seen_burst": burst_id,
                "baseline_F_depth": int(candidate.get("depth", 4)),
                "last_rung": 0.0,
                "status": "OPEN",
                "history": [],
            }
            leads.append(lead)
            changed = True
        for key_name in ("prefix_observation_digest", "prefix_state_digest"):
            digest = candidate.get(key_name)
            if digest and lead.get(key_name) != digest:
                lead[key_name] = digest
                changed = True
    if changed:
        legacy._save(doc)


def _quarantine_ledger_results(results: list[dict[str, Any]]) -> None:
    bad = {
        r.get("candidate_key"): (r.get("prefix_identity_audit") or {}).get("status")
        for r in results
        if (r.get("prefix_identity_audit") or {}).get("scientific_usable") is False
    }
    if not bad:
        return
    doc = legacy._load()
    changed = False
    for lead in doc.get("leads") or []:
        status = bad.get(lead.get("lead_id"))
        if not status:
            continue
        lead["status"] = "PREFIX_MISMATCH_QUARANTINED"
        lead["prefix_identity_status"] = status
        history = lead.get("history") or []
        if history:
            history[-1]["prefix_identity_status"] = status
            history[-1]["scientific_usable"] = False
        changed = True
    if changed:
        legacy._save(doc)


def register_and_run(
    *, burst_id: str, path_summary: dict[str, Any], max_leads: int = 1, quick: bool = True,
) -> dict[str, Any]:
    _pre_register_with_digest(burst_id=burst_id, path_summary=path_summary)
    previous = legacy.run_candidate
    legacy.run_candidate = run_candidate
    try:
        out = _ORIGINAL_REGISTER(
            burst_id=burst_id, path_summary=path_summary, max_leads=max_leads, quick=quick
        )
    finally:
        legacy.run_candidate = previous
    results = out.get("results") or []
    _quarantine_ledger_results(results)
    out["prefix_identity_audit_enabled"] = True
    out["actual_observation_history_audit_enabled"] = True
    out["historical_F_stage_semantics"] = True
    out["quarantined_prefix_mismatches"] = sum(
        (r.get("prefix_identity_audit") or {}).get("scientific_usable") is False for r in results
    )
    return out
