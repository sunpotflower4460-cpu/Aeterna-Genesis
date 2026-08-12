"""Epistemic progress ratchet for Adaptive Research Yield.

The v9 information-yield router chooses promising *lanes*.  This v10 layer adds a second question:

    did the previous frontier budget actually close a new scientific question, or did we mostly
    repeat the same intervention cells again?

The ratchet is deliberately planning-only.  It does not change scientific truth gates, official
Emergence Levels, Rooms, target definitions, solver equations, or start-purity semantics.  It makes the
extra frontier budget harder to waste by remembering compact experiment signatures and preferring
unseen controls before routine repeats.  When a current target is saturated, the planner rotates away
instead of calling repetition "progress".

"Progress" here is epistemic, not a promise that nature must produce a new phenomenon.  A burst counts
as useful when it does at least one auditable thing such as:

* tests a previously untested start-side intervention cell,
* adds an independent fresh-seed replication of a decision-relevant cell,
* removes one still-untested Root operator,
* finds a deeper/changed reference-path response,
* records saturation and forces the next plan to rotate.

Negative evidence can therefore be real progress, while a repeated pretty pattern is not automatically
progress.  No target X-pattern, vortex, triangle, split, organism, brain, energy landscape, division
location/time, or desired morphology is seeded by this module.
"""
from __future__ import annotations

import math
from typing import Any

from ai_lab.dream import followups
from ai_lab.dream import frontier_expander
from ai_lab.dream import pure_genesis
from ai_lab.dream import research_optimizer
from ai_lab.dream import root_integrity
from ai_lab.dream import strict_geometry
from ai_lab.dream import why_gate


_HISTORY_WINDOW = 12
_STALL_COOLDOWN_AFTER = 2
_MAX_CANDIDATE_POOL = 12

# Keep references to v9 planning functions. install() replaces module attributes only at runtime.
_V9_RANK_X = research_optimizer.rank_x_focuses
_V9_LANE_PLAN = research_optimizer._lane_plan


def _history() -> list[dict[str, Any]]:
    ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
    return list(ledger.get("history") or [])[-_HISTORY_WINDOW:]


def _factor_token(value: Any) -> str:
    try:
        return f"{float(value):.8g}"
    except (TypeError, ValueError):
        return str(value)


def _question_key(lane: str, target: str, knob: str | None = None, factor: Any = None) -> str:
    parts = [str(lane), str(target)]
    if knob is not None:
        parts.append(str(knob))
    if factor is not None:
        parts.append(_factor_token(factor))
    return "|".join(parts)


def _history_question_counts(history: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in history:
        progress = row.get("progress") or {}
        for key in progress.get("question_keys") or row.get("progress_question_keys") or []:
            key = str(key)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _factor_levels(knob: str) -> list[float]:
    """Standard controls first, then deterministic closer/stronger boundary probes.

    These are still start-side parameter interventions inside the already allowed knob ranges.  They do
    not use an observed target morphology to choose a value.  Extra levels are only a generic way to
    avoid repeating the exact same low/high cells forever after the standard pair has been covered.
    """
    low, high = frontier_expander._KNOB_FACTORS[knob]
    candidates = [
        float(low),
        float(high),
        math.sqrt(float(low)),
        math.sqrt(float(high)),
        float(low) * float(low),
        float(high) * float(high),
    ]
    out: list[float] = []
    for value in candidates:
        if value <= 0 or not math.isfinite(value):
            continue
        if not any(abs(value - old) < 1e-10 for old in out):
            out.append(value)
    return out


def _candidate_question_keys(lane: str, target: str) -> list[str]:
    keys: list[str] = []
    for knob in frontier_expander._KNOB_RANGES:
        for factor in _factor_levels(knob):
            keys.append(_question_key(lane, target, knob, factor))
    return keys


def _coverage_for_target(lane: str, target: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _history_question_counts(history)
    possible = _candidate_question_keys(lane, target)
    seen = sum(1 for key in possible if counts.get(key, 0) > 0)
    return {
        "seen": seen,
        "possible": len(possible),
        "unseen": max(0, len(possible) - seen),
        "fraction": 0.0 if not possible else round(seen / len(possible), 6),
    }


def _consecutive_lane_low_gain(history: list[dict[str, Any]], lane: str) -> int:
    count = 0
    for row in reversed(history):
        progress = row.get("progress") or {}
        lane_units = progress.get("lane_knowledge_units") or {}
        if lane not in lane_units:
            break
        if float(lane_units.get(lane, 0.0)) > 0.0:
            break
        count += 1
    return count


def rank_x_focuses(
    *, limit: int = research_optimizer._MAX_X_FOCUSES,
    history: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """v9 specificity ranking plus intervention-coverage pressure.

    We inspect a wider candidate pool than the final number of simultaneous focuses.  A candidate with
    many already-covered mechanism cells is discounted so another specific candidate can take its turn.
    """
    history = _history() if history is None else history
    pool = _V9_RANK_X(limit=max(_MAX_CANDIDATE_POOL, int(limit) * 4), history=history)
    adjusted: list[dict[str, Any]] = []
    for row in pool:
        item = dict(row)
        coverage = _coverage_for_target("x", str(item["pattern_id"]), history)
        item["intervention_coverage"] = coverage
        novelty_multiplier = 0.35 + 0.65 * (1.0 - float(coverage["fraction"]))
        item["score_before_progress_ratchet"] = item.get("score")
        item["score"] = round(float(item.get("score", 0.0)) * novelty_multiplier, 6)
        adjusted.append(item)
    adjusted.sort(
        key=lambda x: (
            float(x.get("score", 0.0)),
            int((x.get("intervention_coverage") or {}).get("unseen", 0)),
            float(x.get("specificity", 0.0)),
            str(x.get("pattern_id")),
        ),
        reverse=True,
    )
    return adjusted[: max(0, int(limit))]


def _lane_plan(
    report: dict[str, Any], root_report: dict[str, Any], *, total: int,
    history: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    """Apply a cooldown to lanes that repeatedly spend budget without compact knowledge gain."""
    lanes, ranked_x, _ = _V9_LANE_PLAN(report, root_report, total=total, history=history)

    for name, lane in lanes.items():
        stalls = _consecutive_lane_low_gain(history, name)
        lane["recent_zero_gain_bursts"] = stalls
        if stalls >= _STALL_COOLDOWN_AFTER:
            lane["score"] = round(float(lane.get("score", 0.0)) * 0.35, 6)
            lane["floor"] = 0
            lane["progress_cooldown"] = True
            lane["reason"] = f"{lane.get('reason', '')}; repeated zero-gain frontier bursts trigger rotation"
        else:
            lane["progress_cooldown"] = False

    # Reward lanes that still have concrete untested cells.  This is planning coverage, not scientific
    # confidence.  It helps the allocator prefer a question it can actually close this burst.
    if ranked_x:
        x_unseen = sum(int((r.get("intervention_coverage") or {}).get("unseen", 0)) for r in ranked_x)
        lanes["x"]["novel_question_capacity"] = x_unseen
        if x_unseen > 0:
            lanes["x"]["score"] = round(float(lanes["x"].get("score", 0.0)) * 1.18, 6)

    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    if lanes["f"].get("eligible"):
        ftarget = f"{candidate.get('family')}:{candidate.get('trial_index')}"
        fcoverage = _coverage_for_target("f", ftarget, history)
        lanes["f"]["novel_question_capacity"] = fcoverage["unseen"]
        if fcoverage["unseen"] == 0:
            lanes["f"]["score"] = round(float(lanes["f"].get("score", 0.0)) * 0.50, 6)
            lanes["f"]["floor"] = 0

    top = (root_report.get("top_laws") or [])[:1]
    if lanes["root"].get("eligible") and top:
        law = top[0]
        law_id = str(law.get("id") or "root-law")
        active = [k for k, v in (law.get("coefficients") or {}).items() if abs(float(v)) > 1e-12]
        counts = _history_question_counts(history)
        unseen = sum(1 for op in active if counts.get(_question_key("root", law_id, op), 0) == 0)
        lanes["root"]["novel_question_capacity"] = unseen
        if unseen == 0:
            lanes["root"]["score"] = round(float(lanes["root"].get("score", 0.0)) * 0.55, 6)
            lanes["root"]["floor"] = 0

    alloc = research_optimizer._weighted_allocate(total, lanes)
    return lanes, ranked_x, alloc


def _ordered_intervention_specs(
    *, lane: str, target: str, family: str, knobs: dict[str, Any], burst_id: str,
    budget: int, history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = frontier_expander._clip_knobs(knobs)
    specs: list[dict[str, Any]] = []
    for i in range(min(2, max(0, int(budget)))):
        specs.append({
            "family": family,
            "knobs": dict(base),
            "seed": frontier_expander._seed(burst_id, target, lane, "progress-baseline", i),
            "intervention": "fresh-seed-baseline",
            "intervened_knob": None,
            "factor": 1.0,
            "quick": True,
            "progress_question_key": None,
        })
    if len(specs) >= int(budget):
        return specs

    counts = _history_question_counts(history)
    candidates: list[dict[str, Any]] = []
    for knob in frontier_expander._KNOB_RANGES:
        for factor in _factor_levels(knob):
            varied = dict(base)
            varied[knob] *= factor
            varied = frontier_expander._clip_knobs(varied)
            key = _question_key(lane, target, knob, factor)
            candidates.append({
                "family": family,
                "knobs": varied,
                "seed": frontier_expander._seed(burst_id, target, lane, knob, factor, "progress"),
                "intervention": "one-factor-start-side",
                "intervened_knob": knob,
                "factor": factor,
                "quick": True,
                "progress_question_key": key,
                "prior_question_count": counts.get(key, 0),
            })

    # Unseen cells first, then least-repeated cells.  Deterministic hash rotation avoids the same knob
    # winning ties forever while retaining reproducibility from burst_id.
    candidates.sort(
        key=lambda spec: (
            int(spec.get("prior_question_count", 0)),
            frontier_expander._seed(burst_id, target, spec["intervened_knob"], spec["factor"], "order"),
        )
    )
    specs.extend(candidates[: max(0, int(budget) - len(specs))])
    return specs[: max(0, int(budget))]


def _balanced_x_specs(entry: dict[str, Any], *, burst_id: str, budget: int) -> list[dict[str, Any]]:
    focus = entry["search_focus"]
    return _ordered_intervention_specs(
        lane="x",
        target=str(entry["pattern_id"]),
        family=str(focus["family"]),
        knobs=focus["knobs"],
        burst_id=burst_id,
        budget=budget,
        history=_history(),
    )


def _f_frontier_study(report: dict[str, Any], *, burst_id: str, budget: int) -> dict[str, Any]:
    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    depth = int(candidate.get("depth", -1))
    family = candidate.get("family")
    knobs = candidate.get("knobs") or {}
    if budget <= 0 or depth < 4 or not family or not knobs:
        return {"ran": False, "reason": "no-deep-frontier-or-budget", "experiments": 0}

    target = f"{family}:{candidate.get('trial_index')}"
    specs = _ordered_intervention_specs(
        lane="f", target=target, family=str(family), knobs=knobs,
        burst_id=burst_id, budget=budget, history=_history(),
    )
    rows: list[dict[str, Any]] = []
    for spec in specs:
        screened = followups._eval2d(spec)
        common = {
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "progress_question_key": spec.get("progress_question_key"),
        }
        if screened.get("score") is None:
            rows.append({**common, "finite_screen": False, "depth": -1})
            continue
        probe = strict_geometry._geometry_probe(screened)
        p = probe.get("zero_to_fission") or {}
        rows.append({
            **common,
            "finite_screen": True,
            "depth": int(p.get("depth", -1)),
            "depth_code": p.get("depth_code"),
            "balance_collapse": bool(probe.get("balance_collapse_seen")),
            "pre_split_instability": bool(probe.get("pre_split_instability_candidate")),
            "network_fission_candidate": bool(probe.get("network_fission_candidate")),
            "start_purity": p.get("start_purity"),
        })

    baseline = [float(r["depth"]) for r in rows if r.get("intervened_knob") is None and r.get("depth", -1) >= 0]
    baseline_mean = frontier_expander._mean(baseline)
    sensitivity = []
    for knob in frontier_expander._KNOB_RANGES:
        vals = [float(r["depth"]) for r in rows if r.get("intervened_knob") == knob and r.get("depth", -1) >= 0]
        if not vals:
            continue
        mean = frontier_expander._mean(vals)
        sensitivity.append({
            "knob": knob,
            "mean_depth": None if mean is None else round(mean, 4),
            "delta_from_fresh_baseline": None if mean is None or baseline_mean is None else round(mean - baseline_mean, 4),
            "samples": len(vals),
        })
    sensitivity.sort(key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True)
    fission = sum(bool(r.get("network_fission_candidate")) for r in rows)
    best = max((int(r.get("depth", -1)) for r in rows), default=-1)
    return {
        "ran": True,
        "source_depth": depth,
        "source_start_purity": candidate.get("start_purity"),
        "experiments": len(rows),
        "fresh_baseline_mean_depth": None if baseline_mean is None else round(baseline_mean, 4),
        "best_depth_seen": best,
        "relation_network_fission_candidates": fission,
        "sensitivity": sensitivity,
        "results": rows,
        "progress_target": target,
        "interpretation": (
            "Start-side controls are scheduled novelty-first. A changed F-depth narrows a simulator "
            "mechanism question only; F0-F7 remains one human-written reference path and is not a natural route."
        ),
        "target_geometry_seeded": False,
        "division_location_or_time_seeded": False,
        "F7_is_biological_cell_division": False,
    }


def _root_ablation_study(root_report: dict[str, Any], *, burst_id: str, budget: int) -> dict[str, Any]:
    top = (root_report.get("top_laws") or [])[:1]
    if budget <= 0 or not top:
        return {"ran": False, "reason": "no-root-law-or-budget", "experiments": 0}
    base = top[0]
    law_id = str(base.get("id") or "root-law")
    coefficients = dict(base.get("coefficients") or {})
    active = [k for k, v in coefficients.items() if abs(float(v)) > 1e-12]
    if not active:
        return {"ran": False, "reason": "root-law-has-no-active-operator", "experiments": 0}

    counts = _history_question_counts(_history())
    active.sort(key=lambda op: (counts.get(_question_key("root", law_id, op), 0), str(op)))
    sizes = tuple(max(3, int(n)) for n in (root_report.get("sizes") or [8, 12, 16]))
    steps = max(8, int(root_report.get("steps") or 48))
    baseline_priority = float(base.get("priority", 0.0))
    rows = []
    for i, operator in enumerate(active[: max(0, int(budget))]):
        coeffs = dict(coefficients)
        coeffs[operator] = 0.0
        proposal = pure_genesis.law_proposal(coeffs)
        gate = why_gate.validate_proposal(proposal)
        key = _question_key("root", law_id, operator)
        if not gate.accepted:
            rows.append({
                "operator_removed": operator,
                "why_gate_accepted": False,
                "progress_question_key": key,
            })
            continue
        proposal["why_gate"] = gate.as_dict()
        evaluated = pure_genesis.evaluate_law(
            proposal,
            sizes=sizes,
            steps=steps,
            seed=frontier_expander._seed(burst_id, "root-ablation", law_id, operator, i),
        )
        audited = root_integrity._audit_law(evaluated)
        priority = float(audited.get("priority", 0.0))
        rows.append({
            "operator_removed": operator,
            "why_gate_accepted": True,
            "audited_priority": round(priority, 6),
            "priority_change_vs_current_top": round(priority - baseline_priority, 6),
            "status": audited.get("status"),
            "integrity_flags": (audited.get("root_integrity") or {}).get("flags") or [],
            "progress_question_key": key,
        })
    rows.sort(key=lambda x: float(x.get("priority_change_vs_current_top", 0.0)))
    return {
        "ran": True,
        "source_law_id": law_id,
        "baseline_audited_priority": round(baseline_priority, 6),
        "experiments": len(rows),
        "ablations": rows,
        "most_needed_operator_candidate": rows[0].get("operator_removed") if rows else None,
        "interpretation": (
            "Untested operator removals are scheduled before routine repeats. An ablation only tests "
            "necessity inside the current computational candidate and never promotes an operator to a fundamental law."
        ),
        "new_physical_axiom_added": False,
    }


def _collect_question_keys(expansion: dict[str, Any]) -> dict[str, list[str]]:
    by_lane: dict[str, list[str]] = {"f": [], "x": [], "root": []}
    fstudy = expansion.get("f_frontier_mechanism") or {}
    for row in fstudy.get("results") or []:
        key = row.get("progress_question_key")
        if key:
            by_lane["f"].append(str(key))

    xstudy = expansion.get("x_pattern_mechanism") or {}
    for pattern in xstudy.get("patterns") or []:
        pid = str(pattern.get("pattern_id") or "unknown-x")
        for row in pattern.get("results") or []:
            knob = row.get("intervened_knob")
            if knob is None:
                continue
            by_lane["x"].append(_question_key("x", pid, str(knob), row.get("factor")))

    root = expansion.get("root_operator_ablation") or {}
    law_id = str(root.get("source_law_id") or "root-law")
    for row in root.get("ablations") or []:
        key = row.get("progress_question_key")
        if not key and row.get("operator_removed"):
            key = _question_key("root", law_id, str(row["operator_removed"]))
        if key:
            by_lane["root"].append(str(key))
    return by_lane


def _progress_audit(expansion: dict[str, Any], history_before: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _history_question_counts(history_before)
    by_lane = _collect_question_keys(expansion)
    flat = [key for keys in by_lane.values() for key in keys]
    unique_flat = list(dict.fromkeys(flat))
    novel = [key for key in unique_flat if counts.get(key, 0) == 0]
    repeated = [key for key in unique_flat if counts.get(key, 0) > 0]

    lane_units: dict[str, float] = {}
    lane_novel: dict[str, int] = {}
    lane_repeated: dict[str, int] = {}
    for lane, keys in by_lane.items():
        unique = list(dict.fromkeys(keys))
        n_novel = sum(counts.get(key, 0) == 0 for key in unique)
        n_repeat = sum(counts.get(key, 0) > 0 for key in unique)
        lane_novel[lane] = n_novel
        lane_repeated[lane] = n_repeat
        # Planning-only score: new cells are worth 1, fresh-seed replication cells 0.2.  It is never
        # used as physical evidence or confidence; it only detects repeated zero-yield routing.
        lane_units[lane] = round(float(n_novel) + 0.2 * float(n_repeat), 3)

    events: list[str] = []
    if novel:
        events.append("NEW_INTERVENTION_CELLS_TESTED")
    if repeated:
        events.append("FRESH_SEED_REPLICATION_CELLS_ADDED")

    fstudy = expansion.get("f_frontier_mechanism") or {}
    prior_depths = [int(x["f_best_depth"]) for x in history_before if x.get("f_best_depth") is not None]
    previous_max = max(prior_depths, default=-1)
    if int(fstudy.get("best_depth_seen", -1)) > previous_max:
        events.append("NEW_REFERENCE_DEPTH_OBSERVED")
    if int(fstudy.get("relation_network_fission_candidates", 0) or 0) > 0:
        events.append("RELATION_NETWORK_FISSION_CANDIDATE_OBSERVED")

    root = expansion.get("root_operator_ablation") or {}
    if root.get("ablations"):
        events.append("ROOT_OPERATOR_ABLATION_EVIDENCE_ADDED")

    xstudy = expansion.get("x_pattern_mechanism") or {}
    if any(
        abs(float(s.get("delta_from_fresh_baseline") or 0.0)) > 0.0
        for p in xstudy.get("patterns") or [] for s in p.get("sensitivity") or []
    ):
        events.append("X_RESPONSE_DIFFERENCE_OBSERVED")

    executed = int((expansion.get("budget") or {}).get("executed", 0) or 0)
    novel_fraction = 0.0 if not unique_flat else len(novel) / len(unique_flat)
    strong_advance = bool(novel) or any(
        event in events
        for event in (
            "NEW_REFERENCE_DEPTH_OBSERVED",
            "RELATION_NETWORK_FISSION_CANDIDATE_OBSERVED",
            "ROOT_OPERATOR_ABLATION_EVIDENCE_ADDED",
            "X_RESPONSE_DIFFERENCE_OBSERVED",
        )
    )
    if executed <= 0:
        status = "STALL_NO_FRONTIER_EXPERIMENT_EXECUTED"
    elif strong_advance:
        status = "ADVANCED"
    elif repeated:
        status = "ADVANCED_BY_REPLICATION_ONLY"
    else:
        status = "LOW_GAIN"

    escape_required = status in {"STALL_NO_FRONTIER_EXPERIMENT_EXECUTED", "LOW_GAIN"} or (
        status == "ADVANCED_BY_REPLICATION_ONLY" and novel_fraction < 0.20
    )
    if escape_required:
        events.append("NEXT_BURST_ROUTE_ROTATION_REQUIRED")

    return {
        "version": 1,
        "status": status,
        "definition": "epistemic planning progress only; not a physical success score",
        "question_keys": unique_flat,
        "new_question_keys": novel,
        "replicated_question_keys": repeated,
        "novel_question_fraction": round(novel_fraction, 6),
        "lane_novel_questions": lane_novel,
        "lane_replicated_questions": lane_repeated,
        "lane_knowledge_units": lane_units,
        "advance_events": events,
        "next_burst_escape_required": bool(escape_required),
        "guarantee_limit": (
            "The planner can force new controls, replications, or route changes; it cannot honestly "
            "guarantee that a new natural phenomenon will appear every burst."
        ),
        "negative_result_can_count_as_progress": True,
        "raw_recurrence_alone_counts_as_progress": False,
        "changes_scientific_truth_gate": False,
    }


def _persist_progress(expansion: dict[str, Any], progress: dict[str, Any]) -> None:
    ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
    ledger["latest"] = expansion
    rows = list(ledger.get("history") or [])
    if rows and str(rows[-1].get("burst_id")) == str(expansion.get("burst_id")):
        rows[-1]["progress"] = progress
        rows[-1]["progress_question_keys"] = progress.get("question_keys") or []
        rows[-1]["allocation_policy"] = "expected-information-yield-v2+epistemic-progress-ratchet-v1"
    ledger["history"] = rows[-96:]
    frontier_expander._write(frontier_expander._LEDGER, ledger)
    frontier_expander._write(frontier_expander._REPORT, expansion)


def run_progressive_frontier_expansion(
    *, report: dict[str, Any], root_report: dict[str, Any], burst_id: str,
    max_experiments: int = 24, persist: bool = True,
) -> dict[str, Any]:
    history_before = _history()
    expansion = research_optimizer.run_optimized_frontier_expansion(
        report=report,
        root_report=root_report,
        burst_id=burst_id,
        max_experiments=max_experiments,
        persist=persist,
    )
    progress = _progress_audit(expansion, history_before)
    expansion["version"] = max(3, int(expansion.get("version", 0) or 0))
    expansion["mode"] = "autonomous-information-yield-progress-ratchet"
    expansion["progress_ratchet"] = progress
    expansion.setdefault("policy", {}).update({
        "every_burst_has_epistemic_progress_contract": True,
        "unseen_intervention_cells_before_routine_repeats": True,
        "zero_gain_lanes_enter_cooldown": True,
        "saturated_targets_rotate_when_alternatives_exist": True,
        "negative_results_can_close_questions": True,
        "new_natural_phenomenon_each_burst_is_not_guaranteed": True,
    })
    expansion.setdefault("integrity", {}).update({
        "progress_score_changes_scientific_truth": False,
        "progress_score_promotes_rooms": False,
        "progress_score_changes_official_levels": False,
        "progress_metric_is_physical_observable": False,
    })
    if persist:
        _persist_progress(expansion, progress)
    return expansion


def install() -> None:
    """Install the v10 planning ratchet on top of v9 without touching physics or truth gates."""
    research_optimizer.rank_x_focuses = rank_x_focuses
    research_optimizer._lane_plan = _lane_plan
    research_optimizer._balanced_x_specs = _balanced_x_specs
    frontier_expander._f_frontier_study = _f_frontier_study
    frontier_expander._root_ablation_study = _root_ablation_study
    frontier_expander.run_frontier_expansion = run_progressive_frontier_expansion
