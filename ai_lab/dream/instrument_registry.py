"""Claim-safe registry for instruments requested by the autonomous frontier.

The frontier can correctly notice that a question is not yet measurable.  This registry makes the next
engineering step explicit without turning a measurement request into evidence that the requested phenomenon
exists.  Contracts specify what an implementation must measure, which controls it needs, and which tempting
interpretations remain blocked.

Registry entries are infrastructure/planning metadata only.  They never allocate physics compute or change
scientific truth, Rooms, official Emergence Levels, NØ, F0-F7, Cross-World status or Local Vortex Energy
semantics.
"""
from __future__ import annotations

from typing import Any

REGISTRY_VERSION = 1

INSTRUMENTS: dict[str, dict[str, Any]] = {
    "metric-from-relations": {
        "capability": "emergent_metric_geometry",
        "question": "Can a metric-like geometry be measured from relations without supplying geometry as the answer?",
        "implementation_contract": [
            "derive candidate distances/adjacency only from relation observables available before interpretation",
            "audit invariance to anonymous-slot relabeling/permutation when the upstream model requires it",
            "compare against null/permuted/relation-destroying controls",
            "report dimensional/metric fit as a measured candidate with uncertainty and coverage",
        ],
        "required_controls": ["permutation_or_label_control", "relation_destroying_control", "holdout_or_out_of_sample_check"],
        "claim_blocks": ["spacetime", "gravity", "fundamental_dimension", "geometry_from_strict_nothing"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
    "identity-continuity": {
        "capability": "persistent_individual_identity",
        "question": "Does a relation-defined candidate remain the same individual through time under an outcome-independent tracking rule?",
        "implementation_contract": [
            "define identity matching from predeclared relation/state observables, not a desired body shape",
            "track births/deaths/merges/splits with explicit ambiguity accounting",
            "compare continuity against shuffled-time or randomized-association controls",
            "report persistence duration and identity uncertainty rather than binary organism labels",
        ],
        "required_controls": ["association_shuffle_control", "ambiguity_accounting", "fresh_seed_replication"],
        "claim_blocks": ["organism", "self", "cell", "life"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
    "damage-recovery": {
        "capability": "self_repair",
        "question": "After a predeclared perturbation, does a persistent candidate recover more than matched passive controls?",
        "implementation_contract": [
            "require an independently established persistent candidate before applying damage",
            "choose perturbation location/magnitude without using the desired recovery outcome",
            "compare damaged recovery with undamaged, sham and matched-decay controls",
            "separate passive relaxation from restoration of candidate-specific relational organization",
        ],
        "required_controls": ["undamaged_control", "sham_control", "matched_passive_relaxation_control", "fresh_seed_replication"],
        "claim_blocks": ["healing", "homeostasis", "living_repair"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
    "growth-accounting": {
        "capability": "growth_and_specialization",
        "question": "Can persistent candidate extent/complexity increase with explicit accounting, and do subregions differentiate reproducibly?",
        "implementation_contract": [
            "measure candidate extent/complexity with an outcome-independent identity/segmentation rule",
            "account for externally supplied drive/material/order proxies separately from internally reorganized structure",
            "require specialization metrics to be defined before inspecting the target run",
            "compare against matched expansion without specialization and matched specialization noise controls",
        ],
        "required_controls": ["input_accounting", "expansion_only_control", "specialization_null_control", "fresh_seed_replication"],
        "claim_blocks": ["metabolism", "development", "organism_growth"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
    "predictive-holdout": {
        "capability": "adaptive_prediction",
        "question": "Does a candidate's state improve prediction or response on genuinely held-out future/changed conditions?",
        "implementation_contract": [
            "freeze feature extraction and prediction rule before evaluating held-out outcomes",
            "prevent future-state/condition labels from leaking into training or feature selection",
            "compare against persistence, shuffled-label and simple environmental baseline predictors",
            "test transfer to fresh seeds or changed conditions, not only interpolation on the source run",
        ],
        "required_controls": ["temporal_holdout", "label_shuffle_control", "simple_baseline_predictor", "fresh_condition_transfer"],
        "claim_blocks": ["learning", "intelligence", "agency", "brain"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
    "lineage-accounting": {
        "capability": "division_with_inheritance",
        "question": "Can persistent relation-defined individuals divide while preserving accountable inherited organization?",
        "implementation_contract": [
            "require persistent parent identity before any proposed division event",
            "require persistent daughter identities after separation, with no double-counting of one fluctuating body",
            "account parent-to-daughter relational/state information using a predeclared inheritance metric",
            "compare with transient network separation, fragmentation and unrelated-neighbor controls",
        ],
        "required_controls": ["persistent_body_division", "parent_daughter_accounting", "fragmentation_control", "unrelated_neighbor_control"],
        "claim_blocks": ["biological_cell_division", "reproduction", "heredity", "life"],
        "scaffolded_parallel_lane_allowed": True,
        "scaffolded_parallel_lane_is_pure_genesis_proof": False,
    },
}


def get(instrument_id: str) -> dict[str, Any] | None:
    row = INSTRUMENTS.get(str(instrument_id))
    if row is None:
        return None
    return {"id": str(instrument_id), "registry_version": REGISTRY_VERSION, **row}


def validate_request(request: dict[str, Any]) -> list[str]:
    """Return infrastructure contract violations for one frontier instrument request."""
    errors: list[str] = []
    rid = str(request.get("id") or "")
    registered = get(rid)
    if not rid:
        errors.append("instrument request has no id")
        return errors
    if registered is None:
        errors.append(f"unregistered instrument id: {rid}")
        return errors
    if request.get("new_physical_axiom") is True:
        errors.append(f"{rid}: instrument request declares a new physical axiom")
    if request.get("target_morphology_seeded") is True:
        errors.append(f"{rid}: instrument request seeds target morphology")
    if request.get("may_use_scaffolded_analogy_lane") is True and request.get(
        "scaffolded_lane_cannot_count_as_pure_genesis_proof"
    ) is not True:
        errors.append(f"{rid}: scaffolded analogy lane lacks explicit non-proof boundary")
    return errors


def validate_frontier_requests(frontier: dict[str, Any]) -> dict[str, Any]:
    requests = [row for row in (frontier.get("instrument_requests") or []) if isinstance(row, dict)]
    errors: list[str] = []
    ids: list[str] = []
    for row in requests:
        rid = str(row.get("id") or "")
        if rid:
            ids.append(rid)
        errors.extend(validate_request(row))
    duplicates = sorted({rid for rid in ids if ids.count(rid) > 1})
    errors.extend(f"duplicate instrument request id: {rid}" for rid in duplicates)
    return {
        "registry_version": REGISTRY_VERSION,
        "request_count": len(requests),
        "registered_request_count": sum(get(str(row.get("id") or "")) is not None for row in requests),
        "errors": errors,
        "valid": not errors,
        "request_is_evidence_of_phenomenon": False,
        "registry_changes_scientific_truth": False,
    }
