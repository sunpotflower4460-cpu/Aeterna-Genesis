"""Evidence-yield optimizer for Aeterna's *planning* frontier budget.

This module does not change physics, scientific gates, Rooms, official Emergence Levels, initial
conditions, or the broad anti-bias search.  It only replaces the extra ``frontier_experiments`` budget
router used by Adaptive Dream.

Why this exists
---------------
The v8 frontier expander correctly says F0-F7 is only one human-written reference route, but its old
allocator still gave an F4 candidate first refusal on roughly half of every extra budget.  At the same
time, recurrent X-patterns can become saturated (many repeats but little specificity), and a root
ablation can execute only as many trials as there are active operators.  Allocating by route depth alone
therefore wastes compute and can turn a reference path into an implicit objective.

The optimizer allocates by expected *information yield* instead:

* specific/contrast-separated X candidates outrank huge but nonspecific recurrence counts,
* recently studied X candidates are discounted so independent candidates rotate in,
* F-reference work receives a small falsification floor but only grows when it reaches genuinely new
  depth/instability/fission evidence; an ordinary repeated F4 cannot monopolize the budget,
* root work is driven by unresolved integrity gaps and capped by the number of executable ablations,
* allocation caps are based on experiments that can actually execute, so requested budget is not
  silently assigned to nonexistent one-factor trials.

All interventions remain start-side/fresh-seed.  No target X outcome, triangle, split, geometry, energy
landscape, organism, brain, or division location/time is encoded.  This is a research-planning policy,
not a new physical law.
"""
from __future__ import annotations

import math
from typing import Any

from ai_lab.dream import frontier_expander
from ai_lab.dream import open_ended


_RECENT_WINDOW = 8
_MAX_X_FOCUSES = 3


def _safe_rate(hit: int, n: int) -> float:
    return 0.0 if int(n) <= 0 else max(0.0, min(1.0, float(hit) / float(n)))


def _recent_history() -> list[dict[str, Any]]:
    ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
    return list(ledger.get("history") or [])[-_RECENT_WINDOW:]


def _recent_x_counts(history: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in history:
        ids = row.get("x_patterns") or []
        if not ids and row.get("x_pattern"):
            ids = [row.get("x_pattern")]
        for pid in ids:
            if pid:
                counts[str(pid)] = counts.get(str(pid), 0) + 1
    return counts


def rank_x_focuses(*, limit: int = _MAX_X_FOCUSES, history: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Rank reconstructable X leads by specificity + uncertainty, not raw recurrence count.

    A gigantic ``REPEATED_NONSPECIFIC`` pattern is useful as a background phenomenon but should not
    indefinitely beat a smaller candidate whose exact/nearby hits separate from contrast controls.
    """
    history = _recent_history() if history is None else history
    recent = _recent_x_counts(history)
    doc = frontier_expander._read(frontier_expander._UNKNOWN, {"patterns": {}})
    ranked: list[dict[str, Any]] = []

    for pid, row in (doc.get("patterns") or {}).items():
        focus = row.get("search_focus") or {}
        if not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        status = str(row.get("status") or "")
        if status not in {"REPEATED_SPECIFIC_CANDIDATE", "VERIFYING", "REPEATED_NONSPECIFIC"}:
            continue

        exact = row.get("exact") or {}
        local = row.get("local") or {}
        contrast = row.get("contrast") or {}
        en, eh = int(exact.get("n", 0)), int(exact.get("hit", 0))
        ln, lh = int(local.get("n", 0)), int(local.get("hit", 0))
        cn, ch = int(contrast.get("n", 0)), int(contrast.get("hit", 0))
        er, lr, cr = _safe_rate(eh, en), _safe_rate(lh, ln), _safe_rate(ch, cn)

        # Contrast separation is more informative than absolute recurrence.  Nearby recurrence gets
        # half weight because it can reveal a broad basin rather than a narrow condition-specific lead.
        specificity = max(0.0, er - cr) + 0.5 * max(0.0, lr - cr)
        evidence = min(1.0, math.log1p(eh + lh) / math.log(20.0))
        # Prefer candidates that are neither untouched nor completely saturated.  This term shrinks
        # gently with sample count rather than rewarding endless repeats.
        uncertainty = 1.0 / math.sqrt(1.0 + max(en, ln, cn) / 6.0)
        maturity = min(1.0, en / 8.0) if en > 0 else 0.0
        status_base = {
            "REPEATED_SPECIFIC_CANDIDATE": 1.20,
            "VERIFYING": 0.75,
            "REPEATED_NONSPECIFIC": 0.30,
        }[status]
        score = status_base + 1.45 * specificity + 0.45 * evidence + 0.35 * uncertainty
        score *= 0.60 + 0.40 * maturity
        if status == "REPEATED_NONSPECIFIC":
            score *= 0.45

        recent_count = recent.get(str(pid), 0)
        score *= 1.0 / (1.0 + 0.55 * recent_count)
        ranked.append({
            "pattern_id": str(pid),
            "row": row,
            "search_focus": focus,
            "score": round(score, 6),
            "specificity": round(specificity, 6),
            "exact_rate": round(er, 6),
            "nearby_rate": round(lr, 6),
            "contrast_rate": round(cr, 6),
            "recent_studies": recent_count,
            "status": status,
        })

    ranked.sort(key=lambda x: (float(x["score"]), float(x["specificity"]), x["pattern_id"]), reverse=True)
    return ranked[: max(0, int(limit))]


def _f_lane_score(report: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    depth = int(candidate.get("depth", -1))
    if depth < 4:
        return {"eligible": False, "score": 0.0, "depth": depth, "reason": "no-F4-plus-reference-candidate"}

    prior_depths = [int(x["f_best_depth"]) for x in history if x.get("f_best_depth") is not None]
    prior_max = max(prior_depths, default=-1)
    repeated_same = sum(int(x) == depth for x in prior_depths[-6:])
    new_depth = depth > prior_max

    geometry = report.get("geometry_summary") or {}
    balance = int(geometry.get("balance_collapse_seen", 0) or 0)
    presplit = int(geometry.get("pre_split_instability_candidate", 0) or 0)
    fission = int(geometry.get("network_fission_candidate", 0) or 0)

    score = 0.35
    if depth >= 5:
        score += 0.45
    if depth >= 6:
        score += 0.55
    if new_depth:
        score += 0.85
    if balance:
        score += 0.35
    if presplit:
        score += 0.45
    if fission:
        score += 1.0
    # A repeatedly rediscovered F4 is still useful as a control/falsification lane, but should not
    # receive first refusal merely because the human reference path exists.
    if depth == 4 and repeated_same >= 3 and not any((balance, presplit, fission)):
        score *= 0.45
    return {
        "eligible": True,
        "score": round(max(0.05, score), 6),
        "depth": depth,
        "new_depth_vs_recent": new_depth,
        "recent_same_depth_count": repeated_same,
        "balance_collapse_count": balance,
        "pre_split_count": presplit,
        "fission_count": fission,
        "reason": "reference-route falsification/mechanism value; not a natural-route objective",
    }


def _root_lane_score(root_report: dict[str, Any]) -> dict[str, Any]:
    top = (root_report.get("top_laws") or [])[:1]
    if not top:
        return {"eligible": False, "score": 0.0, "active_operators": 0, "reason": "no-root-candidate"}
    base = top[0]
    coeffs = base.get("coefficients") or {}
    active = [k for k, v in coeffs.items() if abs(float(v)) > 1e-12]
    if not active:
        return {"eligible": False, "score": 0.0, "active_operators": 0, "reason": "no-active-root-operator"}
    evidence = frontier_expander._root_evidence(root_report)
    score = 0.35
    unresolved = []
    if not evidence.get("new_distinctions"):
        score += 0.45
        unresolved.append("new_distinctions")
    if not evidence.get("new_quotient_closure"):
        score += 0.55
        unresolved.append("quotient_closure")
    if "relation_trend" in active:
        score += 0.30
        unresolved.append("hidden_history_assumption")
    # If current root observations rely on history dependence, ablation is more valuable than another
    # unqualified claim of 'memory'.
    if evidence.get("history_dependence"):
        score += 0.20
    return {
        "eligible": True,
        "score": round(score, 6),
        "active_operators": len(active),
        "unresolved": unresolved,
        "reason": "remove candidate operators and test integrity gaps; never promote an operator to fundamental law",
    }


def _weighted_allocate(total: int, lanes: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Allocate integer budget with explicit floors/caps and no silent over-allocation."""
    total = max(0, int(total))
    alloc = {name: 0 for name in lanes}
    if total <= 0:
        return alloc

    # Floors preserve falsification breadth. They are small enough that no human-written route can
    # dominate merely by being eligible.
    for name in ("x", "root", "f"):
        lane = lanes[name]
        if not lane.get("eligible"):
            continue
        floor = min(int(lane.get("floor", 0)), int(lane.get("cap", 0)), total - sum(alloc.values()))
        if floor > 0:
            alloc[name] += floor

    while sum(alloc.values()) < total:
        candidates = []
        for name, lane in lanes.items():
            if not lane.get("eligible") or alloc[name] >= int(lane.get("cap", 0)):
                continue
            # Diminishing return makes the next experiment in a lane less valuable than its first.
            marginal = float(lane.get("score", 0.0)) / (1.0 + 0.16 * alloc[name])
            candidates.append((marginal, name))
        if not candidates:
            break
        _, selected = max(candidates, key=lambda x: (x[0], x[1]))
        alloc[selected] += 1
    return alloc


def _balanced_x_specs(entry: dict[str, Any], *, burst_id: str, budget: int) -> list[dict[str, Any]]:
    """Create a balanced intervention set instead of always consuming knobs in fixed file order."""
    focus = entry["search_focus"]
    family = str(focus["family"])
    base = frontier_expander._clip_knobs(focus["knobs"])
    pid = entry["pattern_id"]
    specs: list[dict[str, Any]] = []
    for i in range(min(2, max(0, budget))):
        specs.append({
            "family": family,
            "knobs": dict(base),
            "seed": frontier_expander._seed(burst_id, pid, "yield-baseline", i),
            "intervention": "fresh-seed-baseline",
            "intervened_knob": None,
            "factor": 1.0,
            "quick": True,
        })
    if len(specs) >= budget:
        return specs

    knobs = list(frontier_expander._KNOB_RANGES)
    # Rotate the first knob between bursts/patterns, then alternate low/high factors. This avoids a
    # small sub-budget repeatedly measuring only noise_amplitude because of source-code ordering.
    offset = frontier_expander._seed(burst_id, pid, "knob-order") % len(knobs)
    knobs = knobs[offset:] + knobs[:offset]
    interventions = []
    for side in (0, 1):
        for name in knobs:
            factor = frontier_expander._KNOB_FACTORS[name][side]
            varied = dict(base)
            varied[name] *= factor
            interventions.append({
                "family": family,
                "knobs": frontier_expander._clip_knobs(varied),
                "seed": frontier_expander._seed(burst_id, pid, name, factor, "yield"),
                "intervention": "one-factor-start-side",
                "intervened_knob": name,
                "factor": factor,
                "quick": True,
            })
    specs.extend(interventions[: max(0, budget - len(specs))])
    return specs[:budget]


def _study_one_x(entry: dict[str, Any], *, burst_id: str, budget: int, max_episodes: int = 3) -> dict[str, Any]:
    pid = entry["pattern_id"]
    specs = _balanced_x_specs(entry, burst_id=burst_id, budget=budget)
    results = []
    for spec in specs:
        probe = open_ended._probe(spec)
        episodes = open_ended.detect_episodes(probe, max_episodes=max(1, int(max_episodes)))
        results.append({
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "same_pattern_seen": any(e.get("pattern_id") == pid for e in episodes),
            "other_pattern_ids": [e.get("pattern_id") for e in episodes if e.get("pattern_id") != pid],
            "zero_purity": probe.get("zero_purity"),
        })
    baseline = [float(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") is None]
    base_rate = frontier_expander._mean(baseline)
    sensitivity = []
    for name in frontier_expander._KNOB_RANGES:
        vals = [float(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") == name]
        if not vals:
            continue
        rate = frontier_expander._mean(vals)
        sensitivity.append({
            "knob": name,
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


def _x_portfolio_study(ranked: list[dict[str, Any]], *, burst_id: str, budget: int) -> dict[str, Any]:
    if budget <= 0 or not ranked:
        return {"ran": False, "reason": "no-ranked-x-or-budget", "experiments": 0, "patterns": []}
    # A useful mechanism study needs two fresh baselines plus interventions. Use at most three X leads
    # and avoid scattering tiny one-shot budgets across many IDs.
    eligible = ranked[: min(_MAX_X_FOCUSES, max(1, budget // 4))]
    sublanes = {
        x["pattern_id"]: {
            "eligible": True,
            "score": max(0.01, float(x["score"])),
            "floor": 2,
            "cap": 12,
        }
        for x in eligible
    }
    # Generic allocator expects f/x/root keys, so use a compact local weighted allocation here.
    alloc = {pid: 0 for pid in sublanes}
    for pid in alloc:
        if sum(alloc.values()) < budget:
            alloc[pid] = min(2, budget - sum(alloc.values()))
    while sum(alloc.values()) < budget:
        choices = []
        for pid, lane in sublanes.items():
            if alloc[pid] >= lane["cap"]:
                continue
            choices.append((lane["score"] / (1.0 + 0.18 * alloc[pid]), pid))
        if not choices:
            break
        _, pid = max(choices, key=lambda x: (x[0], x[1]))
        alloc[pid] += 1

    by_id = {x["pattern_id"]: x for x in eligible}
    studies = [
        _study_one_x(by_id[pid], burst_id=burst_id, budget=n)
        for pid, n in alloc.items() if n > 0
    ]
    primary = studies[0] if studies else {}
    return {
        "ran": bool(studies),
        "experiments": sum(int(x.get("experiments", 0)) for x in studies),
        "pattern_id": primary.get("pattern_id"),
        "patterns_studied": [x.get("pattern_id") for x in studies],
        "pattern_allocations": alloc,
        "sensitivity": primary.get("sensitivity") or [],
        "patterns": studies,
        "selection_policy": "specificity/contrast separation + uncertainty + recent-study rotation; raw recurrence alone is downweighted",
        "interpretation": (
            "X leads are challenged by fresh-seed start-side interventions. Sensitivity narrows a simulator mechanism question; "
            "it is not a new physical law and does not make matching fingerprints identical physics."
        ),
        "target_pattern_seeded": False,
        "target_shape_seeded": False,
    }


def _lane_plan(report: dict[str, Any], root_report: dict[str, Any], *, total: int, history: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    ranked_x = rank_x_focuses(limit=_MAX_X_FOCUSES, history=history)
    f = _f_lane_score(report, history)
    root = _root_lane_score(root_report)
    x_score = float(ranked_x[0]["score"]) if ranked_x else 0.0

    # Actual capacities: F's one-factor generator has 12 distinct specs; root has one ablation per
    # active operator; X can execute up to 12 interventions for each selected rotating focus.
    f_cap = 0
    if f["eligible"]:
        if f["depth"] >= 6 or f.get("fission_count"):
            f_cap = min(12, max(4, total // 2))
        elif f["depth"] >= 5 or f.get("new_depth_vs_recent"):
            f_cap = min(9, max(3, total // 3))
        else:
            f_cap = min(6, max(2, total // 4))
    root_cap = min(int(root.get("active_operators", 0)), 6) if root["eligible"] else 0
    x_focus_count = len(ranked_x)
    x_cap = min(total, 12 * x_focus_count) if x_focus_count else 0

    lanes = {
        "f": {**f, "floor": 2 if f["eligible"] else 0, "cap": f_cap},
        "x": {
            "eligible": bool(ranked_x), "score": round(x_score, 6),
            "floor": 4 if ranked_x else 0, "cap": x_cap,
            "top_pattern": ranked_x[0]["pattern_id"] if ranked_x else None,
            "ranked_patterns": [x["pattern_id"] for x in ranked_x],
            "reason": "condition-specific unknown transitions with controls; raw nonspecific recurrence is discounted",
        },
        "root": {**root, "floor": 1 if root["eligible"] else 0, "cap": root_cap},
    }
    alloc = _weighted_allocate(total, lanes)
    return lanes, ranked_x, alloc


def run_optimized_frontier_expansion(
    *, report: dict[str, Any], root_report: dict[str, Any], burst_id: str,
    max_experiments: int = 24, persist: bool = True,
) -> dict[str, Any]:
    """Drop-in replacement for v8 frontier routing, optimized for expected information yield."""
    total = max(0, int(max_experiments))
    history = _recent_history()
    lanes, ranked_x, budgets = _lane_plan(report, root_report, total=total, history=history)

    fstudy = frontier_expander._f_frontier_study(report, burst_id=burst_id, budget=budgets["f"])
    xstudy = _x_portfolio_study(ranked_x, burst_id=burst_id, budget=budgets["x"])
    rootstudy = frontier_expander._root_ablation_study(root_report, burst_id=burst_id, budget=budgets["root"])
    capabilities = frontier_expander._capability_map(report, root_report)
    instruments = frontier_expander._instrument_requests(capabilities)

    path = report.get("zero_to_fission_path") or {}
    f_candidate = path.get("best_frontier_candidate") or {}
    primary_x = ranked_x[0] if ranked_x else {}
    executed = int(fstudy.get("experiments", 0)) + int(xstudy.get("experiments", 0)) + int(rootstudy.get("experiments", 0))
    unallocated = max(0, total - sum(budgets.values()))
    execution_gap = max(0, sum(budgets.values()) - executed)

    expansion = {
        "version": 2,
        "mode": "autonomous-information-yield-frontier-expansion",
        "burst_id": burst_id,
        "north_star": "結果形状を与えず、NØ/R0境界から下流まで、最小前提で何が自発的に成立するかを最も情報量の高い反証可能実験から調べる。",
        "policy": {
            "destination_fixed_methods_adaptive": True,
            "expected_information_yield_routes_budget": True,
            "F_path_gets_first_refusal": False,
            "F_path_is_one_reference_only": True,
            "raw_recurrence_count_is_priority": False,
            "specificity_and_contrast_controls_are_priority": True,
            "recently_studied_leads_are_discounted": True,
            "actual_executable_capacity_caps_allocation": True,
            "hypotheses_may_be_replaced": True,
            "research_methods_may_expand": True,
            "missing_capabilities_trigger_instrument_requests": True,
            "given_form_experiments_allowed_as_parallel_scaffolded_lane": True,
            "scaffolded_results_count_as_pure_genesis_proof": False,
            "NØ_repetition_never_consumes_physical_trial_budget": True,
        },
        "budget": {
            "requested": total,
            "allocated": budgets,
            "executed": executed,
            "unallocated_due_to_capacity": unallocated,
            "allocated_but_not_executed": execution_gap,
            "lane_scores": {k: float(v.get("score", 0.0)) for k, v in lanes.items()},
            "lane_caps": {k: int(v.get("cap", 0)) for k, v in lanes.items()},
            "lane_floors": {k: int(v.get("floor", 0)) for k, v in lanes.items()},
            "lane_rationale": {k: v.get("reason") for k, v in lanes.items()},
        },
        "x_selection": [
            {k: row.get(k) for k in (
                "pattern_id", "score", "specificity", "exact_rate", "nearby_rate", "contrast_rate",
                "recent_studies", "status",
            )}
            for row in ranked_x
        ],
        "source_path_candidate": {
            "family": f_candidate.get("family"), "knobs": f_candidate.get("knobs") or {},
            "depth": f_candidate.get("depth"), "trial_index": f_candidate.get("trial_index"),
        },
        "source_x_focus": primary_x.get("search_focus") or {},
        "f_frontier_mechanism": fstudy,
        "x_pattern_mechanism": xstudy,
        "root_operator_ablation": rootstudy,
        "capability_map": capabilities,
        "instrument_requests": instruments,
        "human": frontier_expander._compact_human(capabilities, fstudy, xstudy, rootstudy),
        "integrity": {
            "new_unexplained_physical_axiom_added": False,
            "target_morphology_seeded": False,
            "x_pattern_seeded": False,
            "vortex_pair_or_triangle_seeded": False,
            "division_location_or_time_seeded": False,
            "brain_structure_seeded": False,
            "energy_landscape_seeded": False,
            "changes_official_level": False,
            "promotes_rooms": False,
            "recurrent_pattern_is_new_physical_law_claim": False,
            "F_path_is_assumed_natural_route": False,
            "allocation_policy_changes_scientific_truth_gate": False,
        },
    }

    if persist:
        ledger = frontier_expander._read(frontier_expander._LEDGER, {"version": 1, "history": []})
        ledger["latest"] = expansion
        rows = list(ledger.get("history") or [])
        rows.append({
            "burst_id": burst_id,
            "budget": expansion["budget"],
            "human": expansion["human"],
            "f_best_depth": fstudy.get("best_depth_seen"),
            "fission_candidates": fstudy.get("relation_network_fission_candidates"),
            "x_pattern": xstudy.get("pattern_id"),
            "x_patterns": xstudy.get("patterns_studied") or [],
            "root_ablation_operator": rootstudy.get("most_needed_operator_candidate"),
            "allocation_policy": "expected-information-yield-v2",
        })
        ledger["history"] = rows[-96:]
        frontier_expander._write(frontier_expander._LEDGER, ledger)
        frontier_expander._write(frontier_expander._REPORT, expansion)
    return expansion


def install() -> None:
    """Install the planning-only router before Adaptive v8 starts its frontier phase."""
    frontier_expander.run_frontier_expansion = run_optimized_frontier_expansion
