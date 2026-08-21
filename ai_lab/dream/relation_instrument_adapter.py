"""Production adapter for relation-only measurement instruments in Pure Genesis R0.

The adapter replaces only the observation wrapper around ``pure_genesis.run_one``.  The relation update
law, root event, regulators, scoring and law ranking are unchanged.  During the already-existing run it
retains a bounded sample of relation matrices and passes them to the generic relation-structure
instruments.

This keeps a sharp boundary between *being measurable* and *being true*: planner-level LEAD below means
only that repeated controlled relation-only measurements produced a candidate worth further testing.  It
never means physical spacetime/dimension, an organism, life, biological division or heredity was shown.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from ai_lab.dream import pure_genesis
from genesis.diagnostics import relation_structure

_ORIGINAL_RUN_ONE = pure_genesis.run_one
_ORIGINAL_RUN_ROOT_RESEARCH = pure_genesis.run_root_research
_INSTALLED = False


def _instrumented_run_one(
    coefficients: dict[str, float], *, n: int, steps: int, pair_index: int, event_sign: int,
    event_fraction: float, normalization: str,
) -> dict[str, Any]:
    prev, curr, pair = pure_genesis.root_state(
        n, pair_index=pair_index, event_sign=event_sign, event_fraction=event_fraction,
        normalization=normalization,
    )
    initial_contrast = float(np.std(pure_genesis._offdiag(curr)))
    differentiation: list[float] = [initial_contrast]
    activity: list[float] = []
    snapshots: list[np.ndarray] = [curr.copy()]
    finite = True
    for _ in range(max(1, int(steps))):
        nxt = pure_genesis.step_relation(prev, curr, coefficients, normalization=normalization)
        if not np.all(np.isfinite(nxt)):
            finite = False
            break
        activity.append(float(np.linalg.norm(nxt - curr)))
        differentiation.append(float(np.std(pure_genesis._offdiag(nxt))))
        prev, curr = curr, nxt
        snapshots.append(curr.copy())

    final_contrast = float(np.std(pure_genesis._offdiag(curr)))
    persistence = (
        pure_genesis._corr(np.abs(snapshots[-1]), np.abs(snapshots[-2]))
        if len(snapshots) >= 2 else 0.0
    )
    closure = pure_genesis._closure_metrics(curr)
    recurrence = pure_genesis._recurrence(differentiation)
    history = (
        pure_genesis._history_dependence(prev, curr, coefficients, normalization=normalization)
        if finite else 0.0
    )
    rank = pure_genesis._effective_rank(curr)
    differentiation_gain = final_contrast / max(initial_contrast, 1e-12)
    nontrivial_activity = float(np.mean(activity[-min(8, len(activity)):])) if activity else 0.0
    relation_instruments = relation_structure.analyze_relation_matrix_series(
        snapshots,
        seed=(int(n) * 1009 + int(pair_index) * 17 + (1 if event_sign >= 0 else 2)),
        max_frames=8,
        edge_quantile=0.80,
    )
    return {
        "finite": finite,
        "n": int(n),
        "steps": int(steps),
        "normalization": normalization,
        "root_event_pair": list(pair),
        "root_event_sign": int(1 if event_sign >= 0 else -1),
        "root_event_fraction": float(event_fraction),
        "initial_differentiation": initial_contrast,
        "final_differentiation": final_contrast,
        "differentiation_gain": min(100.0, differentiation_gain),
        "late_activity": nontrivial_activity,
        "relation_pattern_persistence": max(-1.0, min(1.0, persistence)),
        "closure": closure,
        "recurrence": recurrence,
        "effective_relation_rank": rank,
        "counterfactual_history_dependence": history,
        "relation_structure_instruments": relation_instruments,
        "geometry_was_seeded": False,
        "frequency_was_seeded": False,
        "torus_was_seeded": False,
        "vortex_was_seeded": False,
        "brain_was_seeded": False,
        "identity_was_seeded": False,
        "division_was_seeded": False,
    }


def _law_instrument_counts(law: dict[str, Any]) -> dict[str, Any]:
    runs = [r for r in (law.get("runs") or []) if isinstance(r, dict)]
    metric_measured = 0
    metric_leads = 0
    identity_measured = 0
    identity_leads = 0
    lineage_measured = 0
    lineage_leads = 0
    metric_sizes: set[int] = set()
    identity_sizes: set[int] = set()
    lineage_sizes: set[int] = set()
    for run in runs:
        inst = run.get("relation_structure_instruments") or {}
        metric = inst.get("metric") or {}
        identity = inst.get("identity") or {}
        lineage = inst.get("lineage") or {}
        size = int(run.get("n", 0) or 0)
        if int(metric.get("measured_frames", 0) or 0) > 0:
            metric_measured += 1
        if metric.get("status") == "RELATIONAL_METRIC_SERIES_CANDIDATE":
            metric_leads += 1
            metric_sizes.add(size)
        if identity.get("status") not in {None, "NOT_MEASURED"}:
            identity_measured += 1
        if identity.get("status") == "IDENTITY_CONTINUITY_CANDIDATE":
            identity_leads += 1
            identity_sizes.add(size)
        if lineage.get("status") not in {None, "NOT_MEASURED"}:
            lineage_measured += 1
        if lineage.get("status") == "CONTROLLED_LINEAGE_ACCOUNTING_CANDIDATE":
            lineage_leads += 1
            lineage_sizes.add(size)
    return {
        "total_runs": len(runs),
        "metric_measured_runs": metric_measured,
        "metric_candidate_runs": metric_leads,
        "metric_candidate_sizes": sorted(metric_sizes),
        "identity_measured_runs": identity_measured,
        "identity_candidate_runs": identity_leads,
        "identity_candidate_sizes": sorted(identity_sizes),
        "lineage_measured_runs": lineage_measured,
        "controlled_lineage_candidate_runs": lineage_leads,
        "lineage_candidate_sizes": sorted(lineage_sizes),
    }


def _aggregate(report: dict[str, Any]) -> dict[str, Any]:
    top = [x for x in (report.get("top_laws") or []) if isinstance(x, dict)]
    rows = []
    for law in top:
        counts = _law_instrument_counts(law)
        law.setdefault("observations", {}).update({
            "relation_metric_measured_runs": counts["metric_measured_runs"],
            "relation_metric_candidate_runs": counts["metric_candidate_runs"],
            "identity_continuity_measured_runs": counts["identity_measured_runs"],
            "identity_continuity_candidate_runs": counts["identity_candidate_runs"],
            "lineage_accounting_measured_runs": counts["lineage_measured_runs"],
            "controlled_lineage_candidate_runs": counts["controlled_lineage_candidate_runs"],
            "physical_space_claim": False,
            "fundamental_dimension_claim": False,
            "organism_or_life_claim": False,
            "biological_cell_division_claim": False,
        })
        rows.append({"law_id": law.get("id"), **counts})

    metric_measured = sum(int(x["metric_measured_runs"]) for x in rows)
    metric_candidates = sum(int(x["metric_candidate_runs"]) for x in rows)
    identity_measured = sum(int(x["identity_measured_runs"]) for x in rows)
    identity_candidates = sum(int(x["identity_candidate_runs"]) for x in rows)
    lineage_measured = sum(int(x["lineage_measured_runs"]) for x in rows)
    lineage_candidates = sum(int(x["controlled_lineage_candidate_runs"]) for x in rows)
    metric_sizes = sorted({n for row in rows for n in row["metric_candidate_sizes"]})
    identity_sizes = sorted({n for row in rows for n in row["identity_candidate_sizes"]})
    lineage_sizes = sorted({n for row in rows for n in row["lineage_candidate_sizes"]})

    # These thresholds create a planning LEAD only.  They do not change Pure Genesis scoring or any
    # scientific truth gate.  Multi-size recurrence is required so a single finite regulator cannot do it.
    metric_status = (
        "LEAD" if metric_candidates >= 4 and len(metric_sizes) >= 2
        else ("MEASURED" if metric_measured > 0 else "UNMEASURED")
    )
    identity_status = (
        "LEAD" if identity_candidates >= 3 and len(identity_sizes) >= 2
        else ("MEASURED" if identity_measured > 0 else "UNMEASURED")
    )
    lineage_status = (
        "LEAD" if lineage_candidates >= 2 and len(lineage_sizes) >= 2
        else ("MEASURED" if lineage_measured > 0 else "UNMEASURED")
    )
    return {
        "version": 1,
        "mode": "pure-genesis-relation-instrument-summary",
        "top_law_runs": rows,
        "capabilities": {
            "emergent_metric_geometry": {
                "instrument_status": metric_status,
                "measured_runs": metric_measured,
                "candidate_runs": metric_candidates,
                "candidate_sizes": metric_sizes,
            },
            "persistent_individual_identity": {
                "instrument_status": identity_status,
                "measured_runs": identity_measured,
                "candidate_runs": identity_candidates,
                "candidate_sizes": identity_sizes,
            },
            "division_with_inheritance": {
                "instrument_status": lineage_status,
                "measured_runs": lineage_measured,
                "controlled_candidate_runs": lineage_candidates,
                "candidate_sizes": lineage_sizes,
            },
        },
        "integrity": {
            "coordinate_input_used": False,
            "anonymous_label_permutation_control": True,
            "relation_destroying_control": True,
            "holdout_control": True,
            "association_shuffle_control": True,
            "target_geometry_or_body_seeded": False,
            "changes_root_dynamics": False,
            "changes_law_score_or_ranking": False,
            "planner_lead_is_physical_truth": False,
            "physical_space_claim": False,
            "fundamental_dimension_claim": False,
            "organism_or_life_claim": False,
            "biological_cell_division_claim": False,
            "reproduction_or_heredity_claim": False,
        },
    }


def _instrumented_run_root_research(*args: Any, **kwargs: Any) -> dict[str, Any]:
    report = _ORIGINAL_RUN_ROOT_RESEARCH(*args, **kwargs)
    summary = _aggregate(report)
    report["relation_instrument_summary"] = summary
    observed = list(report.get("observed_not_seeded") or [])
    for item in ("relation_metric_candidate", "identity_continuity_candidate", "lineage_accounting_candidate"):
        if item not in observed:
            observed.append(item)
    report["observed_not_seeded"] = observed
    report.setdefault("honesty", {}).update({
        "relation_metric_instrument_changes_dynamics": False,
        "identity_detector_uses_target_body_shape": False,
        "lineage_detector_seeds_division": False,
        "instrument_planner_lead_is_physical_truth": False,
    })
    persist = bool(kwargs.get("persist", True))
    if persist:
        pure_genesis._write(pure_genesis._REPORT, report)
    return report


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    pure_genesis.run_one = _instrumented_run_one
    pure_genesis.run_root_research = _instrumented_run_root_research
    _INSTALLED = True


def uninstall_for_tests() -> None:
    global _INSTALLED
    pure_genesis.run_one = _ORIGINAL_RUN_ONE
    pure_genesis.run_root_research = _ORIGINAL_RUN_ROOT_RESEARCH
    _INSTALLED = False
