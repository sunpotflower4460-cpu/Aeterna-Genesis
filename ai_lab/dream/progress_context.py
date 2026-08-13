"""Context-aware identity for mutable X search focuses.

A recurrent X fingerprint can be observed again from a different start-side search focus on a later
burst.  Durable progress memory must therefore distinguish "same fingerprint + same varied knob value"
from the scientifically different question "same fingerprint under a different family/base condition".

This module is a planning-only overlay installed after :mod:`progress_ratchet`.  It changes only the
identity used by the no-repeat router.  Physics, initial-condition generators, episode detection,
scientific statuses, truth gates, Rooms and official Emergence Levels are untouched.

Legacy X keys intentionally remain readable as history but are *not* treated as equivalent to a new
context-aware key.  Ambiguous old coverage is safer to re-cover once than to suppress an actually-new
start-side question.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from ai_lab.dream import frontier_expander
from ai_lab.dream import open_ended
from ai_lab.dream import progress_ratchet
from ai_lab.dream import research_optimizer

_CONTEXT_VERSION = 1

# Start from the review-fixed v9 scientific/navigation ranker, then re-apply the v10 durable-memory
# policies below with context-aware coverage. Calling v10's old rank_x_focuses here would let its
# contextless coverage suppress a genuinely new mutable search focus before this layer can inspect it.
_V10_RANK_X = progress_ratchet._V9_RANK_X
_V10_ORDERED_SPECS = progress_ratchet._ordered_specs


def _canonical_context(family: Any, knobs: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical *pre-intervention* start context used for X identity.

    Only family and clipped base knobs are included.  No episode outcome, hit/miss, morphology,
    fingerprint delta, geometry, energy, or post-run measurement can enter the identity.
    """
    clipped = frontier_expander._clip_knobs(knobs)
    ordered = {
        str(name): progress_ratchet._token(clipped[name])
        for name in sorted(clipped)
    }
    return {
        "version": _CONTEXT_VERSION,
        "family": str(family),
        "base_knobs": ordered,
    }


def context_signature(family: Any, knobs: dict[str, Any]) -> str:
    payload = json.dumps(
        _canonical_context(family, knobs),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _x_question_key(
    pattern_id: str, family: Any, base_knobs: dict[str, Any],
    knob: str, executed_value: Any,
) -> str:
    return "|".join([
        "x",
        str(pattern_id),
        f"ctx:{context_signature(family, base_knobs)}",
        str(knob),
        progress_ratchet._token(executed_value),
    ])


def _x_escape_target(pattern_id: str, family: Any, base_knobs: dict[str, Any]) -> str:
    return f"x:{pattern_id}@ctx:{context_signature(family, base_knobs)}"


def _x_candidate_cells(
    *, pattern_id: str, family: Any, knobs: dict[str, Any], burst_id: str,
) -> list[dict[str, Any]]:
    """Enumerate unique executable X cells inside one immutable start-side context."""
    base = frontier_expander._clip_knobs(knobs)
    names = list(frontier_expander._KNOB_RANGES)
    if not names:
        return []
    offset = frontier_expander._seed(burst_id, "x", pattern_id, "ratchet-order") % len(names)
    names = names[offset:] + names[:offset]
    order = {name: i for i, name in enumerate(names)}
    ctx = context_signature(family, base)
    by_key: dict[str, dict[str, Any]] = {}
    for knob in names:
        for level in progress_ratchet._levels(knob):
            varied = dict(base)
            varied[knob] *= float(level["factor"])
            varied = frontier_expander._clip_knobs(varied)
            executed = varied[knob]
            key = _x_question_key(pattern_id, family, base, knob, executed)
            row = {
                "knob": knob,
                "factor": float(level["factor"]),
                "executed_value": executed,
                "phase": int(level["phase"]),
                "level": str(level["level"]),
                "knob_order": order[knob],
                "knobs": varied,
                "progress_question_key": key,
                "context_signature": ctx,
                "context_target": _x_escape_target(pattern_id, family, base),
            }
            old = by_key.get(key)
            if old is None or (row["phase"], row["knob_order"]) < (old["phase"], old["knob_order"]):
                by_key[key] = row
    return list(by_key.values())


def _x_coverage(
    pattern_id: str, family: Any, knobs: dict[str, Any], *, counts: dict[str, int],
) -> dict[str, Any]:
    cells = _x_candidate_cells(
        pattern_id=pattern_id, family=family, knobs=knobs, burst_id="coverage"
    )
    keys = [str(x["progress_question_key"]) for x in cells]
    seen = sum(counts.get(key, 0) > 0 for key in keys)
    return {
        "seen": seen,
        "possible": len(keys),
        "unseen": max(0, len(keys) - seen),
        "fraction": 0.0 if not keys else round(seen / len(keys), 6),
        "context_signature": context_signature(family, knobs),
        "legacy_contextless_keys_count_as_seen": False,
    }


def rank_x_focuses(
    *, limit: int = research_optimizer._MAX_X_FOCUSES,
    history: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Apply v10 ranking policy while making coverage and escape decisions context-aware."""
    full = progress_ratchet._full_history()
    recent = full[-progress_ratchet._RECENT_WINDOW:] if history is None else list(history)[-progress_ratchet._RECENT_WINDOW:]
    memory = progress_ratchet._memory()
    counts = progress_ratchet._durable_question_counts(history=full, memory=memory)
    policy = progress_ratchet._memory_x_policy(memory)
    escape = progress_ratchet._last_escape_targets(full)
    pool = _V10_RANK_X(
        limit=max(progress_ratchet._MAX_CANDIDATE_POOL, int(limit) * 4),
        history=recent,
    )
    out: list[dict[str, Any]] = []
    for raw in pool:
        row = dict(raw)
        pid = str(row["pattern_id"])
        status = str(row.get("status") or "")
        if pid in policy["weakened"] and status != "REPEATED_SPECIFIC_CANDIDATE":
            continue
        focus = row.get("search_focus") or {}
        family = focus.get("family")
        knobs = focus.get("knobs") or {}
        if family is None or not knobs:
            continue
        contextual_escape = _x_escape_target(pid, family, knobs)
        # One-generation compatibility: a legacy pattern-wide escape still blocks the next plan.
        if f"x:{pid}" in escape or contextual_escape in escape:
            continue
        coverage = _x_coverage(pid, family, knobs, counts=counts)
        row["intervention_coverage"] = coverage
        row["search_context_signature"] = coverage["context_signature"]
        row["escape_target"] = contextual_escape
        row["research_memory_saturated_background"] = pid in policy["saturated"]
        row["research_memory_reopened"] = pid in policy["weakened"]
        if pid in policy["saturated"] and int(coverage["unseen"]) <= 0:
            continue
        multiplier = 0.30 + 0.70 * (1.0 - float(coverage["fraction"]))
        row["score_before_context_ratchet"] = row.get("score")
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


def _ordered_specs(
    *, lane: str, target: str, family: str, knobs: dict[str, Any], burst_id: str, budget: int,
) -> list[dict[str, Any]]:
    """Dispatch F to v10 unchanged; give X a context-scoped durable question identity."""
    if lane != "x":
        return _V10_ORDERED_SPECS(
            lane=lane, target=target, family=family, knobs=knobs,
            burst_id=burst_id, budget=budget,
        )
    budget = max(0, int(budget))
    base = frontier_expander._clip_knobs(knobs)
    ctx = context_signature(family, base)
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
            "progress_context_signature": ctx,
            "quick": True,
        })
    if len(specs) >= budget:
        return specs

    counts = progress_ratchet._durable_question_counts()
    cells = _x_candidate_cells(
        pattern_id=target, family=family, knobs=base, burst_id=burst_id
    )
    for cell in cells:
        cell["prior"] = counts.get(str(cell["progress_question_key"]), 0)

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
                burst_id, target, lane, ctx, cell["knob"], cell["executed_value"], "ratchet"
            ),
            "intervention": "one-factor-start-side",
            "intervened_knob": cell["knob"],
            "factor": cell["factor"],
            "executed_value": cell["executed_value"],
            "progress_question_key": cell["progress_question_key"],
            "progress_context_signature": ctx,
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
    pid = str(entry["pattern_id"])
    focus = entry["search_focus"]
    family = str(focus["family"])
    base_knobs = frontier_expander._clip_knobs(focus["knobs"])
    ctx = context_signature(family, base_knobs)
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
            "progress_context_signature": ctx,
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
        "search_context_signature": ctx,
        "escape_target": _x_escape_target(pid, family, base_knobs),
        "context_identity_uses_start_side_only": True,
        "legacy_contextless_keys_count_as_same_question": False,
        "zero_purity_is_reported_not_assumed": True,
        "target_pattern_seeded": False,
        "target_shape_seeded": False,
    }


def _targets(expansion: dict[str, Any]) -> dict[str, list[str]]:
    f = expansion.get("f_frontier_mechanism") or {}
    x = expansion.get("x_pattern_mechanism") or {}
    root = expansion.get("root_operator_ablation") or {}
    x_targets = [
        str(study.get("escape_target"))
        for study in x.get("patterns") or []
        if study.get("escape_target")
    ]
    if not x_targets:
        # Backward-compatible fallback for historical/foreign expansion shapes.
        x_targets = [f"x:{pid}" for pid in x.get("patterns_studied") or [] if pid]
    return {
        "f": [f"f:{f['progress_target']}"] if f.get("progress_target") else [],
        "x": x_targets,
        "root": [f"root:{root['source_law_id']}"] if root.get("source_law_id") else [],
    }


def install() -> None:
    """Install context identity after Progress Ratchet; planning layer only."""
    progress_ratchet.rank_x_focuses = rank_x_focuses
    progress_ratchet._ordered_specs = _ordered_specs
    progress_ratchet._balanced_x_specs = _balanced_x_specs
    progress_ratchet._study_one_x = _study_one_x
    progress_ratchet._targets = _targets
    research_optimizer.rank_x_focuses = rank_x_focuses
    research_optimizer._balanced_x_specs = _balanced_x_specs
    research_optimizer._study_one_x = _study_one_x
