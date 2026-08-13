"""Durable epistemic progress ratchet for Adaptive Research Yield.

Adaptive Research Yield chooses useful *lanes*.  This layer asks a second question: did the bounded
frontier budget actually reduce uncertainty, or did it repeat a question we already know how to ask?

The ratchet is planning-only. It never changes physics, initial conditions, scientific truth gates,
start-purity semantics, Rooms, official Emergence Levels, target definitions or solver equations.

Two memories are used for two different timescales:

* the frontier ledger provides short-term recency/cooldown context;
* ``research_memory.json`` provides durable question coverage and explicit no-repeat lessons.  The
  Research Compass preserves these entries when it refreshes the human-facing memory later in the same
  burst, so a tested cell does not become falsely "new" after the short ledger window rolls over.

A negative result can be progress when it closes a pre-declared question. A numerical/non-finite run
cannot: it remains retryable instrumentation failure. Raw recurrence alone is never progress.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab.dream import followups
from ai_lab.dream import frontier_expander
from ai_lab.dream import pure_genesis
from ai_lab.dream import research_optimizer
from ai_lab.dream import root_integrity
from ai_lab.dream import strict_geometry
from ai_lab.dream import why_gate


_REPO = Path(__file__).resolve().parents[2]
_MEMORY = _REPO / "ai_lab" / "discoveries" / "research_memory.json"
_RECENT_WINDOW = 12
_STALL_COOLDOWN_AFTER = 2
_MAX_CANDIDATE_POOL = 12

# Capture v9 planning functions before install() replaces module attributes at runtime.
_V9_RANK_X = research_optimizer.rank_x_focuses
_V9_LANE_PLAN = research_optimizer._lane_plan


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _full_history() -> list[dict[str, Any]]:
    ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
    return list(ledger.get("history") or [])


def _recent_history() -> list[dict[str, Any]]:
    return _full_history()[-_RECENT_WINDOW:]


def _memory() -> dict[str, Any]:
    return _read_json(_MEMORY, {"version": 1, "entries": []})


def _factor_token(value: Any) -> str:
    try:
        return f"{float(value):.12g}"
    except (TypeError, ValueError):
        return str(value)


def _question_key(
    lane: str, target: str, knob: str | None = None, executed_value: Any = None,
) -> str:
    """Key a question by the condition that actually executes after clipping."""
    parts = [str(lane), str(target)]
    if knob is not None:
        parts.append(str(knob))
    if executed_value is not None:
        parts.append(_factor_token(executed_value))
    return "|".join(parts)


def _memory_question_counts(memory: dict[str, Any] | None = None) -> dict[str, int]:
    memory = _memory() if memory is None else memory
    counts: dict[str, int] = {}
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or row.get("kind") != "progress_question":
            continue
        key = str(row.get("question_key") or "")
        if key:
            counts[key] = max(1, int(row.get("times_seen", 1) or 1))
    return counts


def _ledger_question_counts(history: list[dict[str, Any]] | None = None) -> dict[str, int]:
    history = _full_history() if history is None else history
    counts: dict[str, int] = {}
    for row in history:
        progress = row.get("progress") or {}
        for key in progress.get("question_keys") or row.get("progress_question_keys") or []:
            key = str(key)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _durable_question_counts(
    *, history: list[dict[str, Any]] | None = None, memory: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Prefer durable memory counts and fill legacy gaps from the full retained ledger.

    The recent window is deliberately *not* used for novelty. It is only a recency/cooldown view.
    """
    durable = _memory_question_counts(memory)
    for key, value in _ledger_question_counts(history).items():
        if key not in durable:
            durable[key] = value
    return durable


def _memory_x_policy(memory: dict[str, Any] | None = None) -> dict[str, set[str]]:
    memory = _memory() if memory is None else memory
    weakened: set[str] = set()
    saturated: set[str] = set()
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or not row.get("avoid_exact_repeat"):
            continue
        key = str(row.get("key") or "")
        kind = str(row.get("kind") or "")
        if kind == "weakened_x" and key.startswith("x-weakened:"):
            weakened.add(key.split(":", 1)[1])
        elif kind == "saturated_background_x" and key.startswith("x-saturated-background:"):
            saturated.add(key.split(":", 1)[1])
    return {"weakened": weakened, "saturated": saturated}


def _factor_levels(knob: str) -> list[dict[str, Any]]:
    """Return coarse standard controls first, then generic refinement levels."""
    low, high = frontier_expander._KNOB_FACTORS[knob]
    candidates = [
        (0, "standard-low", float(low)),
        (0, "standard-high", float(high)),
        (1, "refine-low", math.sqrt(float(low))),
        (1, "refine-high", math.sqrt(float(high))),
        (2, "strong-low", float(low) * float(low)),
        (2, "strong-high", float(high) * float(high)),
    ]
    out: list[dict[str, Any]] = []
    for phase, label, factor in candidates:
        if factor <= 0 or not math.isfinite(factor):
            continue
        if any(abs(factor - float(old["factor"])) < 1e-10 for old in out):
            continue
        out.append({"phase": phase, "label": label, "factor": factor})
    return out


def _candidate_cells(
    *, lane: str, target: str, knobs: dict[str, Any], burst_id: str,
) -> list[dict[str, Any]]:
    """Build unique executable cells; clipped duplicates collapse to one question."""
    base = frontier_expander._clip_knobs(knobs)
    knob_names = list(frontier_expander._KNOB_RANGES)
    if not knob_names:
        return []
    offset = frontier_expander._seed(burst_id, lane, target, "progress-knob-order") % len(knob_names)
    knob_names = knob_names[offset:] + knob_names[:offset]
    knob_order = {name: i for i, name in enumerate(knob_names)}

    by_key: dict[str, dict[str, Any]] = {}
    for knob in knob_names:
        for level in _factor_levels(knob):
            varied = dict(base)
            varied[knob] *= float(level["factor"])
            varied = frontier_expander._clip_knobs(varied)
            executed = varied[knob]
            key = _question_key(lane, target, knob, executed)
            row = {
                "knob": knob,
                "factor": float(level["factor"]),
                "executed_value": executed,
                "phase": int(level["phase"]),
                "level": str(level["label"]),
                "knob_order": knob_order[knob],
                "knobs": varied,
                "progress_question_key": key,
            }
            old = by_key.get(key)
            if old is None or (row["phase"], row["knob_order"]) < (old["phase"], old["knob_order"]):
                by_key[key] = row
    return list(by_key.values())


def _coverage_for_target(
    lane: str, target: str, knobs: dict[str, Any], *, burst_id: str,
    counts: dict[str, int],
) -> dict[str, Any]:
    cells = _candidate_cells(lane=lane, target=target, knobs=knobs, burst_id=burst_id)
    keys = [str(c["progress_question_key"]) for c in cells]
    seen = sum(counts.get(key, 0) > 0 for key in keys)
    return {
        "seen": seen,
        "possible": len(keys),
        "unseen": max(0, len(keys) - seen),
        "fraction": 0.0 if not keys else round(seen / len(keys), 6),
    }


def _last_escape_targets(history: list[dict[str, Any]]) -> set[str]:
    for row in reversed(history):
        progress = row.get("progress") or {}
        if progress:
            if not progress.get("next_burst_escape_required"):
                return set()
            return {str(x) for x in progress.get("next_burst_escape_targets") or [] if x}
    return set()


def _consecutive_lane_low_gain(history: list[dict[str, Any]], lane: str) -> int:
    """Count only genuinely consecutive *active* zero-gain bursts for this lane."""
    count = 0
    for row in reversed(history):
        progress = row.get("progress") or {}
        lane_units = progress.get("lane_knowledge_units") or {}
        if lane not in lane_units:
            break  # inactive lane is not a failed attempt and breaks the chronological streak
        if float(lane_units.get(lane, 0.0)) > 0.0:
            break
        count += 1
    return count


def rank_x_focuses(
    *, limit: int = research_optimizer._MAX_X_FOCUSES,
    history: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """v9 specificity ranking plus durable coverage, memory vetoes and one-burst escape."""
    recent = _recent_history() if history is None else history[-_RECENT_WINDOW:]
    full = _full_history()
    memory = _memory()
    counts = _durable_question_counts(history=full, memory=memory)
    policy = _memory_x_policy(memory)
    escape = _last_escape_targets(full)
    pool = _V9_RANK_X(limit=max(_MAX_CANDIDATE_POOL, int(limit) * 4), history=recent)

    adjusted: list[dict[str, Any]] = []
    for row in pool:
        item = dict(row)
        pid = str(item["pattern_id"])
        focus = item.get("search_focus") or {}
        knobs = focus.get("knobs") or {}
        if pid in policy["weakened"]:
            # Current upstream classification must materially change before this ID can re-enter v9's
            # eligible pool. Keeping the explicit memory veto prevents another agent from re-adding it
            # as an exact-repeat target without a changed question.
            continue
        coverage = _coverage_for_target(
            "x", pid, knobs, burst_id="coverage", counts=counts
        )
        item["intervention_coverage"] = coverage
        item["research_memory_saturated_background"] = pid in policy["saturated"]
        item["research_memory_avoid_exact_repeat"] = pid in policy["weakened"]

        if f"x:{pid}" in escape:
            continue
        if pid in policy["saturated"] and int(coverage["unseen"]) <= 0:
            # Memory says recurrence-only confirmation is not a new question. A saturated background X
            # reopens automatically when a genuinely new intervention cell exists.
            continue

        novelty_multiplier = 0.30 + 0.70 * (1.0 - float(coverage["fraction"]))
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
    full = _full_history()
    recent = full[-_RECENT_WINDOW:]
    counts = _durable_question_counts(history=full, memory=_memory())
    escape = _last_escape_targets(full)
    lanes, ranked_x, _ = _V9_LANE_PLAN(report, root_report, total=total, history=recent)

    # Re-rank through the ratchet because the captured v9 planner calls the captured v9 ranker.
    ranked_x = rank_x_focuses(limit=research_optimizer._MAX_X_FOCUSES, history=recent)
    if ranked_x:
        lanes["x"].update({
            "eligible": True,
            "score": round(float(ranked_x[0]["score"]), 6),
            "top_pattern": ranked_x[0]["pattern_id"],
            "ranked_patterns": [x["pattern_id"] for x in ranked_x],
            "cap": min(max(0, int(total)), 12 * len(ranked_x)),
            "floor": 4,
        })
    else:
        lanes["x"].update({"eligible": False, "score": 0.0, "cap": 0, "floor": 0})

    for name, lane in lanes.items():
        stalls = _consecutive_lane_low_gain(recent, name)
        lane["recent_zero_gain_bursts"] = stalls
        if stalls >= _STALL_COOLDOWN_AFTER:
            lane["score"] = round(float(lane.get("score", 0.0)) * 0.35, 6)
            lane["floor"] = 0
            lane["progress_cooldown"] = True
            lane["reason"] = (
                f"{lane.get('reason', '')}; repeated active zero-gain frontier bursts trigger rotation"
            )
        else:
            lane["progress_cooldown"] = False

    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    ftarget = f"{candidate.get('family')}:{candidate.get('trial_index')}"
    if lanes["f"].get("eligible"):
        fcoverage = _coverage_for_target(
            "f", ftarget, candidate.get("knobs") or {}, burst_id="coverage", counts=counts
        )
        lanes["f"]["novel_question_capacity"] = fcoverage["unseen"]
        if f"f:{ftarget}" in escape:
            lanes["f"].update({"eligible": False, "score": 0.0, "floor": 0, "cap": 0})
            lanes["f"]["escape_enforced"] = True
        elif fcoverage["unseen"] == 0:
            lanes["f"]["score"] = round(float(lanes["f"].get("score", 0.0)) * 0.50, 6)
            lanes["f"]["floor"] = 0

    top = (root_report.get("top_laws") or [])[:1]
    if lanes["root"].get("eligible") and top:
        law = top[0]
        law_id = str(law.get("id") or "root-law")
        active = [k for k, v in (law.get("coefficients") or {}).items() if abs(float(v)) > 1e-12]
        unseen = sum(
            counts.get(_question_key("root", law_id, op), 0) == 0 for op in active
        )
        lanes["root"]["novel_question_capacity"] = unseen
        if f"root:{law_id}" in escape:
            lanes["root"].update({"eligible": False, "score": 0.0, "floor": 0, "cap": 0})
            lanes["root"]["escape_enforced"] = True
        elif unseen == 0:
            lanes["root"]["score"] = round(float(lanes["root"].get("score", 0.0)) * 0.55, 6)
            lanes["root"]["floor"] = 0

    alloc = research_optimizer._weighted_allocate(total, lanes)
    return lanes, ranked_x, alloc


def _ordered_intervention_specs(
    *, lane: str, target: str, family: str, knobs: dict[str, Any], burst_id: str,
    budget: int,
) -> list[dict[str, Any]]:
    """Schedule baselines + unseen coarse controls + unseen refinements + least-repeated cells."""
    budget = max(0, int(budget))
    base = frontier_expander._clip_knobs(knobs)
    specs: list[dict[str, Any]] = []
    for i in range(min(2, budget)):
        specs.append({
            "family": family,
            "knobs": dict(base),
            "seed": frontier_expander._seed(burst_id, target, lane, "progress-baseline", i),
            "intervention": "fresh-seed-baseline",
            "intervened_knob": None,
            "factor": 1.0,
            "executed_value": None,
            "progress_question_key": None,
            "quick": True,
        })
    if len(specs) >= budget:
        return specs

    counts = _durable_question_counts()
    cells = _candidate_cells(lane=lane, target=target, knobs=base, burst_id=burst_id)
    for cell in cells:
        cell["prior_question_count"] = counts.get(str(cell["progress_question_key"]), 0)

    unseen_standard = [c for c in cells if c["phase"] == 0 and c["prior_question_count"] == 0]
    unseen_refine = [c for c in cells if c["phase"] > 0 and c["prior_question_count"] == 0]
    repeated = [c for c in cells if c["prior_question_count"] > 0]

    # Coarse-to-fine: established low/high controls first. knob_order + level label preserves low/high
    # pairing before moving to the next knob when both directions are still unseen.
    def coarse_key(c: dict[str, Any]) -> tuple[Any, ...]:
        direction = 0 if str(c["level"]).endswith("low") else 1
        return (int(c["knob_order"]), direction)

    unseen_standard.sort(key=coarse_key)
    unseen_refine.sort(key=lambda c: (int(c["phase"]), *coarse_key(c)))
    repeated.sort(
        key=lambda c: (
            int(c["prior_question_count"]), int(c["phase"]), *coarse_key(c)
        )
    )
    ordered = [*unseen_standard, *unseen_refine, *repeated]

    for cell in ordered[: max(0, budget - len(specs))]:
        specs.append({
            "family": family,
            "knobs": dict(cell["knobs"]),
            "seed": frontier_expander._seed(
                burst_id, target, lane, cell["knob"], cell["executed_value"], "progress"
            ),
            "intervention": "one-factor-start-side",
            "intervened_knob": cell["knob"],
            "factor": cell["factor"],
            "executed_value": cell["executed_value"],
            "progress_question_key": cell["progress_question_key"],
            "progress_phase": cell["phase"],
            "progress_level": cell["level"],
            "prior_question_count": cell["prior_question_count"],
            "quick": True,
        })
    return specs[:budget]


def _balanced_x_specs(entry: dict[str, Any], *, burst_id: str, budget: int) -> list[dict[str, Any]]:
    focus = entry["search_focus"]
    return _ordered_intervention_specs(
        lane="x",
        target=str(entry["pattern_id"]),
        family=str(focus["family"]),
        knobs=focus["knobs"],
        burst_id=burst_id,
        budget=budget,
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
        burst_id=burst_id, budget=budget,
    )
    rows: list[dict[str, Any]] = []
    for spec in specs:
        screened = followups._eval2d(spec)
        common = {
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "executed_value": spec.get("executed_value"),
            "progress_question_key": spec.get("progress_question_key"),
        }
        if screened.get("score") is None:
            rows.append({
                **common, "finite_screen": False, "depth": -1,
                "counts_as_tested_question": False,
            })
            continue
        probe = strict_geometry._geometry_probe(screened)
        p = probe.get("zero_to_fission") or {}
        rows.append({
            **common,
            "finite_screen": True,
            "counts_as_tested_question": True,
            "depth": int(p.get("depth", -1)),
            "depth_code": p.get("depth_code"),
            "balance_collapse": bool(probe.get("balance_collapse_seen")),
            "pre_split_instability": bool(probe.get("pre_split_instability_candidate")),
            "network_fission_candidate": bool(probe.get("network_fission_candidate")),
            "start_purity": p.get("start_purity"),
        })

    baseline = [
        float(r["depth"]) for r in rows
        if r.get("intervened_knob") is None and r.get("finite_screen") and r.get("depth", -1) >= 0
    ]
    baseline_mean = frontier_expander._mean(baseline)
    sensitivity: list[dict[str, Any]] = []
    for knob in frontier_expander._KNOB_RANGES:
        vals = [
            float(r["depth"]) for r in rows
            if r.get("intervened_knob") == knob and r.get("finite_screen") and r.get("depth", -1) >= 0
        ]
        if not vals:
            continue
        mean = frontier_expander._mean(vals)
        sensitivity.append({
            "knob": knob,
            "mean_depth": None if mean is None else round(mean, 4),
            "delta_from_fresh_baseline": (
                None if mean is None or baseline_mean is None else round(mean - baseline_mean, 4)
            ),
            "samples": len(vals),
        })
    sensitivity.sort(
        key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True
    )
    return {
        "ran": True,
        "source_depth": depth,
        "source_start_purity": candidate.get("start_purity"),
        "experiments": len(rows),
        "fresh_baseline_mean_depth": None if baseline_mean is None else round(baseline_mean, 4),
        "best_depth_seen": max((int(r.get("depth", -1)) for r in rows), default=-1),
        "relation_network_fission_candidates": sum(
            bool(r.get("network_fission_candidate")) for r in rows
        ),
        "sensitivity": sensitivity,
        "results": rows,
        "progress_target": target,
        "interpretation": (
            "Start-side controls are scheduled novelty-first and coarse-to-fine. A changed F-depth "
            "narrows a simulator mechanism question only; F0-F7 remains one human-written reference path."
        ),
        "target_geometry_seeded": False,
        "division_location_or_time_seeded": False,
        "F7_is_biological_cell_division": False,
    }


def _root_ablation_study(
    root_report: dict[str, Any], *, burst_id: str, budget: int,
) -> dict[str, Any]:
    top = (root_report.get("top_laws") or [])[:1]
    if budget <= 0 or not top:
        return {"ran": False, "reason": "no-root-law-or-budget", "experiments": 0}
    base = top[0]
    law_id = str(base.get("id") or "root-law")
    coefficients = dict(base.get("coefficients") or {})
    active = [k for k, v in coefficients.items() if abs(float(v)) > 1e-12]
    if not active:
        return {"ran": False, "reason": "root-law-has-no-active-operator", "experiments": 0}

    counts = _durable_question_counts()
    active.sort(key=lambda op: (counts.get(_question_key("root", law_id, op), 0), str(op)))
    sizes = tuple(max(3, int(n)) for n in (root_report.get("sizes") or [8, 12, 16]))
    steps = max(8, int(root_report.get("steps") or 48))
    baseline_priority = float(base.get("priority", 0.0))
    rows: list[dict[str, Any]] = []
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
                "progress_question_key": None,
                "rejected_question_key": key,
                "counts_as_tested_question": False,
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
            "counts_as_tested_question": True,
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
            "Untested operator removals are scheduled before routine repeats. An ablation tests "
            "necessity inside the computational candidate and never promotes an operator to a fundamental law."
        ),
        "new_physical_axiom_added": False,
    }


def _collect_question_keys(expansion: dict[str, Any]) -> dict[str, list[str]]:
    by_lane: dict[str, list[str]] = {"f": [], "x": [], "root": []}
    fstudy = expansion.get("f_frontier_mechanism") or {}
    for row in fstudy.get("results") or []:
        if row.get("finite_screen") is not True:
            continue  # numerical failure remains retryable and does not close the question
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
            executed = row.get("executed_value")
            if executed is None:
                # v9-compatible fallback for any row produced before the ratchet patch; new rows carry
                # executed_value and therefore key by the actual clipped condition.
                executed = row.get("factor")
            by_lane["x"].append(_question_key("x", pid, str(knob), executed))

    root = expansion.get("root_operator_ablation") or {}
    law_id = str(root.get("source_law_id") or "root-law")
    for row in root.get("ablations") or []:
        if row.get("counts_as_tested_question") is False:
            continue
        key = row.get("progress_question_key")
        if not key and row.get("operator_removed"):
            key = _question_key("root", law_id, str(row["operator_removed"]))
        if key:
            by_lane["root"].append(str(key))
    return by_lane


def _lane_targets(expansion: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"f": [], "x": [], "root": []}
    f = expansion.get("f_frontier_mechanism") or {}
    if f.get("progress_target"):
        out["f"].append(f"f:{f['progress_target']}")
    x = expansion.get("x_pattern_mechanism") or {}
    out["x"].extend(
        f"x:{pid}" for pid in (x.get("patterns_studied") or []) if pid
    )
    root = expansion.get("root_operator_ablation") or {}
    if root.get("source_law_id"):
        out["root"].append(f"root:{root['source_law_id']}")
    return out


def _progress_audit(
    expansion: dict[str, Any], counts_before: dict[str, int],
    history_before: list[dict[str, Any]],
) -> dict[str, Any]:
    by_lane = _collect_question_keys(expansion)
    targets = _lane_targets(expansion)
    flat = [key for keys in by_lane.values() for key in keys]
    unique_flat = list(dict.fromkeys(flat))
    novel = [key for key in unique_flat if counts_before.get(key, 0) == 0]
    repeated = [key for key in unique_flat if counts_before.get(key, 0) > 0]

    lane_executed = {
        "f": int((expansion.get("f_frontier_mechanism") or {}).get("experiments", 0) or 0),
        "x": int((expansion.get("x_pattern_mechanism") or {}).get("experiments", 0) or 0),
        "root": int((expansion.get("root_operator_ablation") or {}).get("experiments", 0) or 0),
    }
    lane_units: dict[str, float] = {}
    lane_novel: dict[str, int] = {}
    lane_repeated: dict[str, int] = {}
    for lane, keys in by_lane.items():
        if lane_executed.get(lane, 0) <= 0:
            continue  # inactive lanes must never accumulate a zero-gain streak
        unique = list(dict.fromkeys(keys))
        n_novel = sum(counts_before.get(key, 0) == 0 for key in unique)
        n_repeat = sum(counts_before.get(key, 0) > 0 for key in unique)
        lane_novel[lane] = n_novel
        lane_repeated[lane] = n_repeat
        # Replication is recorded separately but does not reset a zero-gain streak by pretending to be
        # novelty. This makes a replication-only burst request a real route change next time.
        lane_units[lane] = float(n_novel)

    events: list[str] = []
    if novel:
        events.append("NEW_INTERVENTION_CELLS_TESTED")
    if repeated:
        events.append("FRESH_SEED_REPLICATION_CELLS_ADDED")

    fstudy = expansion.get("f_frontier_mechanism") or {}
    prior_depths = [
        int(x.get("f_source_depth", x.get("f_best_depth")))
        for x in history_before
        if x.get("f_source_depth", x.get("f_best_depth")) is not None
    ]
    if int(fstudy.get("best_depth_seen", -1)) > max(prior_depths, default=-1):
        events.append("NEW_REFERENCE_RESPONSE_DEPTH_OBSERVED")
    if int(fstudy.get("relation_network_fission_candidates", 0) or 0) > 0:
        events.append("RELATION_NETWORK_FISSION_CANDIDATE_OBSERVED")
    if (expansion.get("root_operator_ablation") or {}).get("ablations"):
        events.append("ROOT_OPERATOR_ABLATION_EVIDENCE_ADDED")
    if any(
        abs(float(s.get("delta_from_fresh_baseline") or 0.0)) > 0.0
        for p in (expansion.get("x_pattern_mechanism") or {}).get("patterns") or []
        for s in p.get("sensitivity") or []
    ):
        events.append("X_RESPONSE_DIFFERENCE_OBSERVED")

    executed = int((expansion.get("budget") or {}).get("executed", 0) or 0)
    novel_fraction = 0.0 if not unique_flat else len(novel) / len(unique_flat)
    strong_advance = bool(novel) or any(
        e in events for e in (
            "NEW_REFERENCE_RESPONSE_DEPTH_OBSERVED",
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

    escape_required = status in {
        "STALL_NO_FRONTIER_EXPERIMENT_EXECUTED", "LOW_GAIN", "ADVANCED_BY_REPLICATION_ONLY"
    }
    escape_targets: list[str] = []
    if escape_required:
        for lane, used in lane_executed.items():
            if used <= 0:
                continue
            if lane_novel.get(lane, 0) == 0:
                escape_targets.extend(targets.get(lane) or [])
        events.append("NEXT_BURST_ROUTE_ROTATION_REQUIRED")

    return {
        "version": 2,
        "status": status,
        "definition": "epistemic planning progress only; not a physical success score",
        "question_keys": unique_flat,
        "new_question_keys": novel,
        "replicated_question_keys": repeated,
        "novel_question_fraction": round(novel_fraction, 6),
        "lane_executed": lane_executed,
        "lane_novel_questions": lane_novel,
        "lane_replicated_questions": lane_repeated,
        "lane_knowledge_units": lane_units,
        "advance_events": events,
        "next_burst_escape_required": bool(escape_required),
        "next_burst_escape_targets": list(dict.fromkeys(escape_targets)),
        "guarantee_limit": (
            "The planner can force new controls, valid replications, or route changes; it cannot "
            "honestly guarantee that a new natural phenomenon will appear every burst."
        ),
        "negative_result_can_count_as_progress": True,
        "numerical_nonfinite_counts_as_negative_result": False,
        "raw_recurrence_alone_counts_as_progress": False,
        "changes_scientific_truth_gate": False,
    }


def _persist_question_memory(
    question_keys: list[str], *, burst_id: str,
) -> None:
    if not question_keys:
        return
    now = datetime.now(timezone.utc).isoformat()
    memory = _memory()
    by_key = {
        str(row.get("key")): dict(row)
        for row in memory.get("entries") or []
        if isinstance(row, dict) and row.get("key")
    }
    for question in dict.fromkeys(str(x) for x in question_keys if x):
        key = f"progress-question:{question}"
        old = by_key.get(key, {})
        row = dict(old)
        row.update({
            "key": key,
            "kind": "progress_question",
            "question_key": question,
            "human_short": "frontierで実際に評価済みの問い。未知として再表示しない",
            "avoid_exact_repeat": False,
            "reopen_when": "独立replicationが明示的に必要、または実行条件/問いが変わった時",
            "source": "ai_lab/discoveries/frontier_expansion.json",
            "first_seen_burst": old.get("first_seen_burst") or burst_id,
            "last_seen_burst": burst_id,
            "first_seen_at": old.get("first_seen_at") or now,
            "last_seen_at": now,
            "times_seen": int(old.get("times_seen", 0) or 0) + 1,
            "scientific_test_completed": True,
        })
        by_key[key] = row
    entries = list(by_key.values())
    entries.sort(key=lambda r: (str(r.get("kind")), str(r.get("key"))))
    memory = {
        **memory,
        "version": max(2, int(memory.get("version", 1) or 1)),
        "purpose": memory.get("purpose") or "compact-do-not-repeat-and-interpretation-memory",
        "last_burst": burst_id,
        "updated_at": now,
        "entries": entries,
    }
    counts = dict(memory.get("counts") or {})
    counts["total"] = len(entries)
    counts["progress_questions"] = sum(e.get("kind") == "progress_question" for e in entries)
    counts["avoid_exact_repeat"] = sum(bool(e.get("avoid_exact_repeat")) for e in entries)
    memory["counts"] = counts
    policy = dict(memory.get("policy") or {})
    policy.update({
        "progress_ratchet_reads_memory": True,
        "progress_question_history_is_durable": True,
        "memory_changes_scientific_truth": False,
        "memory_changes_official_levels": False,
    })
    memory["policy"] = policy
    _MEMORY.parent.mkdir(parents=True, exist_ok=True)
    _MEMORY.write_text(json.dumps(memory, indent=2, ensure_ascii=False))


def _persist_progress(expansion: dict[str, Any], progress: dict[str, Any]) -> None:
    ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
    ledger["latest"] = expansion
    rows = list(ledger.get("history") or [])
    if rows and str(rows[-1].get("burst_id")) == str(expansion.get("burst_id")):
        rows[-1]["progress"] = progress
        rows[-1]["progress_question_keys"] = progress.get("question_keys") or []
        rows[-1]["allocation_policy"] = (
            "expected-information-yield-v2-review-fixed+durable-progress-ratchet-v2"
        )
    ledger["history"] = rows[-96:]
    frontier_expander._write(frontier_expander._LEDGER, ledger)
    frontier_expander._write(frontier_expander._REPORT, expansion)
    _persist_question_memory(
        progress.get("question_keys") or [], burst_id=str(expansion.get("burst_id") or "unknown-burst")
    )


def run_progressive_frontier_expansion(
    *, report: dict[str, Any], root_report: dict[str, Any], burst_id: str,
    max_experiments: int = 24, persist: bool = True,
) -> dict[str, Any]:
    history_before = _full_history()
    counts_before = _durable_question_counts(history=history_before, memory=_memory())
    expansion = research_optimizer.run_optimized_frontier_expansion(
        report=report,
        root_report=root_report,
        burst_id=burst_id,
        max_experiments=max_experiments,
        persist=persist,
    )
    progress = _progress_audit(expansion, counts_before, history_before)
    expansion["version"] = max(3, int(expansion.get("version", 0) or 0))
    expansion["mode"] = "autonomous-information-yield-durable-progress-ratchet"
    expansion["progress_ratchet"] = progress
    expansion.setdefault("policy", {}).update({
        "every_burst_has_epistemic_progress_contract": True,
        "durable_question_history_uses_research_memory": True,
        "unseen_standard_controls_before_refinement": True,
        "clipped_duplicate_conditions_count_once": True,
        "nonfinite_questions_remain_retryable": True,
        "inactive_lanes_do_not_accumulate_zero_gain": True,
        "recorded_next_burst_escape_is_enforced": True,
        "research_memory_avoid_exact_repeat_is_consulted": True,
        "negative_results_can_close_questions": True,
        "new_natural_phenomenon_each_burst_is_not_guaranteed": True,
    })
    expansion.setdefault("integrity", {}).update({
        "progress_score_changes_scientific_truth": False,
        "progress_score_promotes_rooms": False,
        "progress_score_changes_official_levels": False,
        "progress_metric_is_physical_observable": False,
        "research_memory_changes_physics": False,
    })
    if persist:
        _persist_progress(expansion, progress)
    return expansion


def install() -> None:
    """Install the durable planning ratchet on top of review-fixed Adaptive Research Yield."""
    research_optimizer.rank_x_focuses = rank_x_focuses
    research_optimizer._lane_plan = _lane_plan
    research_optimizer._balanced_x_specs = _balanced_x_specs
    frontier_expander._f_frontier_study = _f_frontier_study
    frontier_expander._root_ablation_study = _root_ablation_study
    frontier_expander.run_frontier_expansion = run_progressive_frontier_expansion
