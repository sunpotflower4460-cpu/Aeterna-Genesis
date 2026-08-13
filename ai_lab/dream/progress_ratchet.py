"""Durable epistemic progress ratchet for Adaptive Research Yield.

Adaptive Research Yield chooses useful frontier lanes. This layer makes the next bounded compute budget
harder to waste by remembering which *actual executed conditions* have already been tested, preferring
coarse controls before refinements, and forcing a route change after replication-only/low-gain bursts.

This is planning/reporting only. It does not change physics, starts, scientific truth gates, Rooms,
official Emergence Levels, Prefix Identity, start-purity semantics, or target definitions.

Research Memory is the durable layer. The short frontier ledger is used only for recency/cooldown; tested
question keys are also stored as ``progress_question`` entries in ``research_memory.json`` so an old cell
does not become falsely "new" when a short history window rolls over. Research Compass preserves these
entries when it refreshes the human-facing memory later in the burst.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab.dream import followups
from ai_lab.dream import frontier_expander
from ai_lab.dream import open_ended
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

# Stable references to review-fixed v9 functions. install() changes module globals only at runtime.
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


def _memory() -> dict[str, Any]:
    return _read_json(_MEMORY, {"version": 1, "entries": []})


def _token(value: Any) -> str:
    try:
        return f"{float(value):.12g}"
    except (TypeError, ValueError):
        return str(value)


def _question_key(lane: str, target: str, knob: str | None = None, executed_value: Any = None) -> str:
    """Identify a question by the *post-clipping condition that actually executed*."""
    parts = [str(lane), str(target)]
    if knob is not None:
        parts.append(str(knob))
    if executed_value is not None:
        parts.append(_token(executed_value))
    return "|".join(parts)


def _memory_question_counts(memory: dict[str, Any] | None = None) -> dict[str, int]:
    memory = _memory() if memory is None else memory
    out: dict[str, int] = {}
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or row.get("kind") != "progress_question":
            continue
        key = str(row.get("question_key") or "")
        if key:
            out[key] = max(1, int(row.get("times_seen", 1) or 1))
    return out


def _ledger_question_counts(history: list[dict[str, Any]] | None = None) -> dict[str, int]:
    history = _full_history() if history is None else history
    out: dict[str, int] = {}
    for row in history:
        progress = row.get("progress") or {}
        for key in progress.get("question_keys") or row.get("progress_question_keys") or []:
            key = str(key)
            out[key] = out.get(key, 0) + 1
    return out


def _durable_question_counts(
    *, history: list[dict[str, Any]] | None = None, memory: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Use durable memory first and the *full retained ledger* only to fill legacy gaps."""
    out = _memory_question_counts(memory)
    for key, n in _ledger_question_counts(history).items():
        if key not in out:
            out[key] = n
    return out


def _memory_x_policy(memory: dict[str, Any] | None = None) -> dict[str, set[str]]:
    memory = _memory() if memory is None else memory
    weakened: set[str] = set()
    saturated: set[str] = set()
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or not row.get("avoid_exact_repeat"):
            continue
        key = str(row.get("key") or "")
        if row.get("kind") == "weakened_x" and key.startswith("x-weakened:"):
            weakened.add(key.split(":", 1)[1])
        if row.get("kind") == "saturated_background_x" and key.startswith("x-saturated-background:"):
            saturated.add(key.split(":", 1)[1])
    return {"weakened": weakened, "saturated": saturated}


def _levels(knob: str) -> list[dict[str, Any]]:
    """Established coarse low/high first, then generic closer/stronger boundary probes."""
    low, high = frontier_expander._KNOB_FACTORS[knob]
    raw = [
        (0, "standard-low", float(low)),
        (0, "standard-high", float(high)),
        (1, "refine-low", math.sqrt(float(low))),
        (1, "refine-high", math.sqrt(float(high))),
        (2, "strong-low", float(low) * float(low)),
        (2, "strong-high", float(high) * float(high)),
    ]
    out: list[dict[str, Any]] = []
    for phase, name, factor in raw:
        if factor <= 0 or not math.isfinite(factor):
            continue
        if any(abs(factor - float(x["factor"])) < 1e-10 for x in out):
            continue
        out.append({"phase": phase, "level": name, "factor": factor})
    return out


def _candidate_cells(
    *, lane: str, target: str, knobs: dict[str, Any], burst_id: str,
) -> list[dict[str, Any]]:
    """Enumerate unique executable cells; different factors that clip identically collapse to one."""
    base = frontier_expander._clip_knobs(knobs)
    names = list(frontier_expander._KNOB_RANGES)
    if not names:
        return []
    offset = frontier_expander._seed(burst_id, lane, target, "ratchet-order") % len(names)
    names = names[offset:] + names[:offset]
    order = {name: i for i, name in enumerate(names)}
    by_key: dict[str, dict[str, Any]] = {}
    for knob in names:
        for level in _levels(knob):
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
                "level": str(level["level"]),
                "knob_order": order[knob],
                "knobs": varied,
                "progress_question_key": key,
            }
            old = by_key.get(key)
            if old is None or (row["phase"], row["knob_order"]) < (old["phase"], old["knob_order"]):
                by_key[key] = row
    return list(by_key.values())


def _coverage(
    lane: str, target: str, knobs: dict[str, Any], *, counts: dict[str, int],
) -> dict[str, Any]:
    cells = _candidate_cells(lane=lane, target=target, knobs=knobs, burst_id="coverage")
    keys = [str(x["progress_question_key"]) for x in cells]
    seen = sum(counts.get(k, 0) > 0 for k in keys)
    return {
        "seen": seen,
        "possible": len(keys),
        "unseen": max(0, len(keys) - seen),
        "fraction": 0.0 if not keys else round(seen / len(keys), 6),
    }


def _last_escape_targets(history: list[dict[str, Any]]) -> set[str]:
    """Read the most recent progress decision; a recorded escape is consumed by the next plan."""
    for row in reversed(history):
        progress = row.get("progress") or {}
        if not progress:
            continue
        if not progress.get("next_burst_escape_required"):
            return set()
        return {str(x) for x in progress.get("next_burst_escape_targets") or [] if x}
    return set()


def _consecutive_lane_zero_gain(history: list[dict[str, Any]], lane: str) -> int:
    count = 0
    for row in reversed(history):
        units = ((row.get("progress") or {}).get("lane_knowledge_units") or {})
        if lane not in units:
            break  # inactive is not a failed attempt
        if float(units[lane]) > 0.0:
            break
        count += 1
    return count


def rank_x_focuses(
    *, limit: int = research_optimizer._MAX_X_FOCUSES,
    history: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    full = _full_history()
    recent = full[-_RECENT_WINDOW:] if history is None else list(history)[-_RECENT_WINDOW:]
    memory = _memory()
    counts = _durable_question_counts(history=full, memory=memory)
    policy = _memory_x_policy(memory)
    escape = _last_escape_targets(full)
    pool = _V9_RANK_X(limit=max(_MAX_CANDIDATE_POOL, int(limit) * 4), history=recent)
    out: list[dict[str, Any]] = []
    for raw in pool:
        row = dict(raw)
        pid = str(row["pattern_id"])
        status = str(row.get("status") or "")
        # A weakened memory can reopen only after upstream evidence has materially reclassified the X.
        if pid in policy["weakened"] and status != "REPEATED_SPECIFIC_CANDIDATE":
            continue
        if f"x:{pid}" in escape:
            continue
        focus = row.get("search_focus") or {}
        coverage = _coverage("x", pid, focus.get("knobs") or {}, counts=counts)
        row["intervention_coverage"] = coverage
        row["research_memory_saturated_background"] = pid in policy["saturated"]
        row["research_memory_reopened"] = pid in policy["weakened"]
        if pid in policy["saturated"] and int(coverage["unseen"]) <= 0:
            continue  # recurrence-only confirmation is not a new question
        multiplier = 0.30 + 0.70 * (1.0 - float(coverage["fraction"]))
        row["score_before_progress_ratchet"] = row.get("score")
        row["score"] = round(float(row.get("score", 0.0)) * multiplier, 6)
        out.append(row)
    out.sort(
        key=lambda x: (
            float(x.get("score", 0.0)),
            int((x.get("intervention_coverage") or {}).get("unseen", 0)),
            float(x.get("specificity", 0.0)),
            str(x.get("pattern_id")),
        ),
        reverse=True,
    )
    return out[: max(0, int(limit))]


def _lane_plan(
    report: dict[str, Any], root_report: dict[str, Any], *, total: int,
    history: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    full = _full_history()
    recent = full[-_RECENT_WINDOW:]
    counts = _durable_question_counts(history=full, memory=_memory())
    escape = _last_escape_targets(full)
    lanes, _, _ = _V9_LANE_PLAN(report, root_report, total=total, history=recent)

    ranked_x = rank_x_focuses(limit=research_optimizer._MAX_X_FOCUSES, history=recent)
    if ranked_x:
        lanes["x"].update({
            "eligible": True,
            "score": round(float(ranked_x[0]["score"]), 6),
            "floor": 4,
            "cap": min(max(0, int(total)), 12 * len(ranked_x)),
            "top_pattern": ranked_x[0]["pattern_id"],
            "ranked_patterns": [x["pattern_id"] for x in ranked_x],
        })
    else:
        lanes["x"].update({"eligible": False, "score": 0.0, "floor": 0, "cap": 0})

    for name, lane in lanes.items():
        stalls = _consecutive_lane_zero_gain(recent, name)
        lane["recent_zero_gain_bursts"] = stalls
        lane["progress_cooldown"] = stalls >= _STALL_COOLDOWN_AFTER
        if lane["progress_cooldown"]:
            lane["score"] = round(float(lane.get("score", 0.0)) * 0.35, 6)
            lane["floor"] = 0

    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    ftarget = f"{candidate.get('family')}:{candidate.get('trial_index')}"
    if lanes["f"].get("eligible"):
        c = _coverage("f", ftarget, candidate.get("knobs") or {}, counts=counts)
        lanes["f"]["novel_question_capacity"] = c["unseen"]
        if f"f:{ftarget}" in escape:
            lanes["f"].update({"eligible": False, "score": 0.0, "floor": 0, "cap": 0})
            lanes["f"]["escape_enforced"] = True
        elif c["unseen"] == 0:
            lanes["f"]["score"] = round(float(lanes["f"].get("score", 0.0)) * 0.5, 6)
            lanes["f"]["floor"] = 0

    top = (root_report.get("top_laws") or [])[:1]
    if lanes["root"].get("eligible") and top:
        law = top[0]
        law_id = str(law.get("id") or "root-law")
        active = [k for k, v in (law.get("coefficients") or {}).items() if abs(float(v)) > 1e-12]
        unseen = sum(counts.get(_question_key("root", law_id, op), 0) == 0 for op in active)
        lanes["root"]["novel_question_capacity"] = unseen
        if f"root:{law_id}" in escape:
            lanes["root"].update({"eligible": False, "score": 0.0, "floor": 0, "cap": 0})
            lanes["root"]["escape_enforced"] = True
        elif unseen == 0:
            lanes["root"]["score"] = round(float(lanes["root"].get("score", 0.0)) * 0.55, 6)
            lanes["root"]["floor"] = 0

    return lanes, ranked_x, research_optimizer._weighted_allocate(total, lanes)


def _ordered_specs(
    *, lane: str, target: str, family: str, knobs: dict[str, Any], burst_id: str, budget: int,
) -> list[dict[str, Any]]:
    budget = max(0, int(budget))
    base = frontier_expander._clip_knobs(knobs)
    specs: list[dict[str, Any]] = []
    for i in range(min(2, budget)):
        specs.append({
            "family": family,
            "knobs": dict(base),
            "seed": frontier_expander._seed(burst_id, target, lane, "ratchet-baseline", i),
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
        cell["prior"] = counts.get(str(cell["progress_question_key"]), 0)

    # Unseen standard low/high endpoints always precede unseen refinement. Within a phase, the rotated
    # knob order and low/high suffix keep the pair together before truncation.
    direction = lambda c: 0 if str(c["level"]).endswith("low") else 1
    coarse_key = lambda c: (int(c["knob_order"]), direction(c))
    standards = sorted([c for c in cells if c["phase"] == 0 and c["prior"] == 0], key=coarse_key)
    refinements = sorted(
        [c for c in cells if c["phase"] > 0 and c["prior"] == 0],
        key=lambda c: (int(c["phase"]), *coarse_key(c)),
    )
    repeats = sorted(
        [c for c in cells if c["prior"] > 0],
        key=lambda c: (int(c["prior"]), int(c["phase"]), *coarse_key(c)),
    )
    for cell in [*standards, *refinements, *repeats][: max(0, budget - len(specs))]:
        specs.append({
            "family": family,
            "knobs": dict(cell["knobs"]),
            "seed": frontier_expander._seed(
                burst_id, target, lane, cell["knob"], cell["executed_value"], "ratchet"
            ),
            "intervention": "one-factor-start-side",
            "intervened_knob": cell["knob"],
            "factor": cell["factor"],
            "executed_value": cell["executed_value"],
            "progress_question_key": cell["progress_question_key"],
            "progress_phase": cell["phase"],
            "progress_level": cell["level"],
            "prior_question_count": cell["prior"],
            "quick": True,
        })
    return specs[:budget]


def _balanced_x_specs(entry: dict[str, Any], *, burst_id: str, budget: int) -> list[dict[str, Any]]:
    focus = entry["search_focus"]
    return _ordered_specs(
        lane="x", target=str(entry["pattern_id"]), family=str(focus["family"]),
        knobs=focus["knobs"], burst_id=burst_id, budget=budget,
    )


def _study_one_x(
    entry: dict[str, Any], *, burst_id: str, budget: int, max_episodes: int = 3,
) -> dict[str, Any]:
    """v9 X study with executed-value/question-key provenance preserved in every result row."""
    pid = str(entry["pattern_id"])
    specs = _balanced_x_specs(entry, burst_id=burst_id, budget=budget)
    results: list[dict[str, Any]] = []
    for spec in specs:
        probe = open_ended._probe(spec)
        episodes = open_ended.detect_episodes(probe, max_episodes=max(1, int(max_episodes)))
        results.append({
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "executed_value": spec.get("executed_value"),
            "progress_question_key": spec.get("progress_question_key"),
            "progress_phase": spec.get("progress_phase"),
            "same_pattern_seen": any(e.get("pattern_id") == pid for e in episodes),
            "other_pattern_ids": [e.get("pattern_id") for e in episodes if e.get("pattern_id") != pid],
            "zero_purity": probe.get("zero_purity"),
        })
    baseline = [float(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") is None]
    base_rate = frontier_expander._mean(baseline)
    sensitivity: list[dict[str, Any]] = []
    for knob in frontier_expander._KNOB_RANGES:
        vals = [float(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") == knob]
        if not vals:
            continue
        rate = frontier_expander._mean(vals)
        sensitivity.append({
            "knob": knob,
            "hit_rate": None if rate is None else round(rate, 4),
            "delta_from_fresh_baseline": None if rate is None or base_rate is None else round(rate - base_rate, 4),
            "samples": len(vals),
        })
    sensitivity.sort(key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True)
    return {
        "pattern_id": pid,
        "selection_score": entry["score"],
        "previous_status": entry["status"],
        "prior_exact_rate": entry["exact_rate"],
        "prior_nearby_rate": entry["nearby_rate"],
        "prior_contrast_rate": entry["contrast_rate"],
        "recent_studies": entry["recent_studies"],
        "experiments": len(results),
        "fresh_baseline_hit_rate": None if base_rate is None else round(base_rate, 4),
        "sensitivity": sensitivity,
        "results": results,
        "zero_purity_is_reported_not_assumed": True,
        "target_pattern_seeded": False,
        "target_shape_seeded": False,
    }


def _f_frontier_study(report: dict[str, Any], *, burst_id: str, budget: int) -> dict[str, Any]:
    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    depth = int(candidate.get("depth", -1))
    family, knobs = candidate.get("family"), candidate.get("knobs") or {}
    if budget <= 0 or depth < 4 or not family or not knobs:
        return {"ran": False, "reason": "no-deep-frontier-or-budget", "experiments": 0}
    target = f"{family}:{candidate.get('trial_index')}"
    rows: list[dict[str, Any]] = []
    for spec in _ordered_specs(
        lane="f", target=target, family=str(family), knobs=knobs, burst_id=burst_id, budget=budget
    ):
        screened = followups._eval2d(spec)
        common = {
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "executed_value": spec.get("executed_value"),
            "progress_question_key": spec.get("progress_question_key"),
        }
        if screened.get("score") is None:
            rows.append({**common, "finite_screen": False, "depth": -1, "counts_as_tested_question": False})
            continue
        probe = strict_geometry._geometry_probe(screened)
        p = probe.get("zero_to_fission") or {}
        rows.append({
            **common, "finite_screen": True, "counts_as_tested_question": True,
            "depth": int(p.get("depth", -1)), "depth_code": p.get("depth_code"),
            "balance_collapse": bool(probe.get("balance_collapse_seen")),
            "pre_split_instability": bool(probe.get("pre_split_instability_candidate")),
            "network_fission_candidate": bool(probe.get("network_fission_candidate")),
            "start_purity": p.get("start_purity"),
        })
    baseline = [float(r["depth"]) for r in rows if r.get("intervened_knob") is None and r.get("finite_screen")]
    baseline_mean = frontier_expander._mean(baseline)
    sensitivity: list[dict[str, Any]] = []
    for knob in frontier_expander._KNOB_RANGES:
        vals = [float(r["depth"]) for r in rows if r.get("intervened_knob") == knob and r.get("finite_screen")]
        if vals:
            mean = frontier_expander._mean(vals)
            sensitivity.append({
                "knob": knob, "mean_depth": None if mean is None else round(mean, 4),
                "delta_from_fresh_baseline": None if mean is None or baseline_mean is None else round(mean - baseline_mean, 4),
                "samples": len(vals),
            })
    sensitivity.sort(key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True)
    return {
        "ran": True, "source_depth": depth, "source_start_purity": candidate.get("start_purity"),
        "experiments": len(rows),
        "fresh_baseline_mean_depth": None if baseline_mean is None else round(baseline_mean, 4),
        "best_depth_seen": max((int(r.get("depth", -1)) for r in rows), default=-1),
        "relation_network_fission_candidates": sum(bool(r.get("network_fission_candidate")) for r in rows),
        "sensitivity": sensitivity, "results": rows, "progress_target": target,
        "interpretation": "Novelty-first coarse-to-fine start-side controls; F0-F7 remains one human-written reference path.",
        "target_geometry_seeded": False, "division_location_or_time_seeded": False,
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
    counts = _durable_question_counts()
    active.sort(key=lambda op: (counts.get(_question_key("root", law_id, op), 0), str(op)))
    sizes = tuple(max(3, int(n)) for n in (root_report.get("sizes") or [8, 12, 16]))
    steps = max(8, int(root_report.get("steps") or 48))
    baseline_priority = float(base.get("priority", 0.0))
    rows: list[dict[str, Any]] = []
    for i, operator in enumerate(active[: max(0, int(budget))]):
        coeffs = dict(coefficients); coeffs[operator] = 0.0
        proposal = pure_genesis.law_proposal(coeffs)
        gate = why_gate.validate_proposal(proposal)
        key = _question_key("root", law_id, operator)
        if not gate.accepted:
            rows.append({"operator_removed": operator, "why_gate_accepted": False, "progress_question_key": None, "counts_as_tested_question": False})
            continue
        proposal["why_gate"] = gate.as_dict()
        evaluated = pure_genesis.evaluate_law(
            proposal, sizes=sizes, steps=steps,
            seed=frontier_expander._seed(burst_id, "root-ablation", law_id, operator, i),
        )
        audited = root_integrity._audit_law(evaluated)
        priority = float(audited.get("priority", 0.0))
        rows.append({
            "operator_removed": operator, "why_gate_accepted": True, "counts_as_tested_question": True,
            "audited_priority": round(priority, 6),
            "priority_change_vs_current_top": round(priority - baseline_priority, 6),
            "status": audited.get("status"),
            "integrity_flags": (audited.get("root_integrity") or {}).get("flags") or [],
            "progress_question_key": key,
        })
    rows.sort(key=lambda x: float(x.get("priority_change_vs_current_top", 0.0)))
    return {
        "ran": True, "source_law_id": law_id, "baseline_audited_priority": round(baseline_priority, 6),
        "experiments": len(rows), "ablations": rows,
        "most_needed_operator_candidate": rows[0].get("operator_removed") if rows else None,
        "interpretation": "Operator ablation tests necessity only inside the current computational candidate.",
        "new_physical_axiom_added": False,
    }


def _question_keys(expansion: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"f": [], "x": [], "root": []}
    for row in (expansion.get("f_frontier_mechanism") or {}).get("results") or []:
        if row.get("finite_screen") is True and row.get("progress_question_key"):
            out["f"].append(str(row["progress_question_key"]))
    for pattern in (expansion.get("x_pattern_mechanism") or {}).get("patterns") or []:
        for row in pattern.get("results") or []:
            if row.get("intervened_knob") is not None and row.get("progress_question_key"):
                out["x"].append(str(row["progress_question_key"]))
    for row in (expansion.get("root_operator_ablation") or {}).get("ablations") or []:
        if row.get("counts_as_tested_question") is not False and row.get("progress_question_key"):
            out["root"].append(str(row["progress_question_key"]))
    return out


def _targets(expansion: dict[str, Any]) -> dict[str, list[str]]:
    f = expansion.get("f_frontier_mechanism") or {}
    x = expansion.get("x_pattern_mechanism") or {}
    root = expansion.get("root_operator_ablation") or {}
    return {
        "f": [f"f:{f['progress_target']}"] if f.get("progress_target") else [],
        "x": [f"x:{p}" for p in x.get("patterns_studied") or [] if p],
        "root": [f"root:{root['source_law_id']}"] if root.get("source_law_id") else [],
    }


def _progress_audit(
    expansion: dict[str, Any], counts_before: dict[str, int], history_before: list[dict[str, Any]],
) -> dict[str, Any]:
    by_lane = _question_keys(expansion)
    targets = _targets(expansion)
    unique = list(dict.fromkeys(k for keys in by_lane.values() for k in keys))
    novel = [k for k in unique if counts_before.get(k, 0) == 0]
    repeated = [k for k in unique if counts_before.get(k, 0) > 0]
    executed_by_lane = {
        "f": int((expansion.get("f_frontier_mechanism") or {}).get("experiments", 0) or 0),
        "x": int((expansion.get("x_pattern_mechanism") or {}).get("experiments", 0) or 0),
        "root": int((expansion.get("root_operator_ablation") or {}).get("experiments", 0) or 0),
    }
    lane_units: dict[str, float] = {}
    lane_novel: dict[str, int] = {}
    lane_repeated: dict[str, int] = {}
    for lane, keys in by_lane.items():
        if executed_by_lane[lane] <= 0:
            continue  # inactive lanes are omitted, never written as zero-gain
        distinct = list(dict.fromkeys(keys))
        lane_novel[lane] = sum(counts_before.get(k, 0) == 0 for k in distinct)
        lane_repeated[lane] = sum(counts_before.get(k, 0) > 0 for k in distinct)
        lane_units[lane] = float(lane_novel[lane])  # replication does not reset a zero-gain streak

    events: list[str] = []
    if novel: events.append("NEW_INTERVENTION_CELLS_TESTED")
    if repeated: events.append("FRESH_SEED_REPLICATION_CELLS_ADDED")
    if (expansion.get("root_operator_ablation") or {}).get("ablations"):
        events.append("ROOT_OPERATOR_ABLATION_EVIDENCE_ADDED")
    if any(
        abs(float(s.get("delta_from_fresh_baseline") or 0.0)) > 0.0
        for p in (expansion.get("x_pattern_mechanism") or {}).get("patterns") or []
        for s in p.get("sensitivity") or []
    ):
        events.append("X_RESPONSE_DIFFERENCE_OBSERVED")
    fstudy = expansion.get("f_frontier_mechanism") or {}
    if int(fstudy.get("relation_network_fission_candidates", 0) or 0) > 0:
        events.append("RELATION_NETWORK_FISSION_CANDIDATE_OBSERVED")

    executed = int((expansion.get("budget") or {}).get("executed", 0) or 0)
    strong = bool(novel) or any(e in events for e in (
        "ROOT_OPERATOR_ABLATION_EVIDENCE_ADDED", "X_RESPONSE_DIFFERENCE_OBSERVED",
        "RELATION_NETWORK_FISSION_CANDIDATE_OBSERVED",
    ))
    if executed <= 0:
        status = "STALL_NO_FRONTIER_EXPERIMENT_EXECUTED"
    elif strong:
        status = "ADVANCED"
    elif repeated:
        status = "ADVANCED_BY_REPLICATION_ONLY"
    else:
        status = "LOW_GAIN"
    escape = status in {"STALL_NO_FRONTIER_EXPERIMENT_EXECUTED", "ADVANCED_BY_REPLICATION_ONLY", "LOW_GAIN"}
    escape_targets: list[str] = []
    if escape:
        for lane, n in executed_by_lane.items():
            if n > 0 and lane_novel.get(lane, 0) == 0:
                escape_targets.extend(targets.get(lane) or [])
        events.append("NEXT_BURST_ROUTE_ROTATION_REQUIRED")
    return {
        "version": 2, "status": status,
        "definition": "epistemic planning progress only; not a physical success score",
        "question_keys": unique, "new_question_keys": novel, "replicated_question_keys": repeated,
        "novel_question_fraction": 0.0 if not unique else round(len(novel) / len(unique), 6),
        "lane_executed": executed_by_lane, "lane_novel_questions": lane_novel,
        "lane_replicated_questions": lane_repeated, "lane_knowledge_units": lane_units,
        "advance_events": events, "next_burst_escape_required": escape,
        "next_burst_escape_targets": list(dict.fromkeys(escape_targets)),
        "negative_result_can_count_as_progress": True,
        "numerical_nonfinite_counts_as_negative_result": False,
        "raw_recurrence_alone_counts_as_progress": False,
        "changes_scientific_truth_gate": False,
        "guarantee_limit": "New controls/valid replications/route changes can be enforced; a new natural phenomenon cannot be guaranteed.",
    }


def _persist_question_memory(keys: list[str], *, burst_id: str) -> None:
    if not keys:
        return
    now = datetime.now(timezone.utc).isoformat()
    memory = _memory()
    by_key = {str(r.get("key")): dict(r) for r in memory.get("entries") or [] if isinstance(r, dict) and r.get("key")}
    for question in dict.fromkeys(str(x) for x in keys if x):
        key = f"progress-question:{question}"
        old = by_key.get(key, {})
        by_key[key] = {
            **old, "key": key, "kind": "progress_question", "question_key": question,
            "human_short": "frontierで実際に評価済みの問い。未知として再表示しない",
            "avoid_exact_repeat": False,
            "reopen_when": "独立replicationが明示的に必要、または実行条件/問いが変わった時",
            "source": "ai_lab/discoveries/frontier_expansion.json",
            "first_seen_burst": old.get("first_seen_burst") or burst_id, "last_seen_burst": burst_id,
            "first_seen_at": old.get("first_seen_at") or now, "last_seen_at": now,
            "times_seen": int(old.get("times_seen", 0) or 0) + 1, "scientific_test_completed": True,
        }
    entries = sorted(by_key.values(), key=lambda r: (str(r.get("kind")), str(r.get("key"))))
    memory.update({"version": max(2, int(memory.get("version", 1) or 1)), "last_burst": burst_id, "updated_at": now, "entries": entries})
    counts = dict(memory.get("counts") or {})
    counts.update({
        "total": len(entries),
        "progress_questions": sum(r.get("kind") == "progress_question" for r in entries),
        "avoid_exact_repeat": sum(bool(r.get("avoid_exact_repeat")) for r in entries),
    })
    memory["counts"] = counts
    policy = dict(memory.get("policy") or {})
    policy.update({"progress_ratchet_reads_memory": True, "progress_question_history_is_durable": True, "memory_changes_scientific_truth": False})
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
        rows[-1]["allocation_policy"] = "information-yield-v2+durable-progress-ratchet-v2"
    ledger["history"] = rows[-96:]
    frontier_expander._write(frontier_expander._LEDGER, ledger)
    frontier_expander._write(frontier_expander._REPORT, expansion)
    _persist_question_memory(progress.get("question_keys") or [], burst_id=str(expansion.get("burst_id") or "unknown-burst"))


def run_progressive_frontier_expansion(
    *, report: dict[str, Any], root_report: dict[str, Any], burst_id: str,
    max_experiments: int = 24, persist: bool = True,
) -> dict[str, Any]:
    before = _full_history()
    counts = _durable_question_counts(history=before, memory=_memory())
    expansion = research_optimizer.run_optimized_frontier_expansion(
        report=report, root_report=root_report, burst_id=burst_id,
        max_experiments=max_experiments, persist=persist,
    )
    progress = _progress_audit(expansion, counts, before)
    expansion["version"] = max(3, int(expansion.get("version", 0) or 0))
    expansion["mode"] = "autonomous-information-yield-durable-progress-ratchet"
    expansion["progress_ratchet"] = progress
    expansion.setdefault("policy", {}).update({
        "durable_question_history_uses_research_memory": True,
        "unseen_standard_controls_before_refinement": True,
        "clipped_duplicate_conditions_count_once": True,
        "nonfinite_questions_remain_retryable": True,
        "inactive_lanes_do_not_accumulate_zero_gain": True,
        "recorded_next_burst_escape_is_enforced": True,
        "research_memory_avoid_exact_repeat_is_consulted": True,
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
    """Install the ratchet above review-fixed Adaptive Research Yield; planning layer only."""
    research_optimizer.rank_x_focuses = rank_x_focuses
    research_optimizer._lane_plan = _lane_plan
    research_optimizer._balanced_x_specs = _balanced_x_specs
    research_optimizer._study_one_x = _study_one_x
    frontier_expander._f_frontier_study = _f_frontier_study
    frontier_expander._root_ablation_study = _root_ablation_study
    frontier_expander.run_frontier_expansion = run_progressive_frontier_expansion
