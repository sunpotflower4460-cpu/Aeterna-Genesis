"""Hypothesis portfolio allocation for Adaptive Dream v8-compatible planning.

The portfolio only subdivides research attention among hypothesis nodes. Global anti-bias floors
remain outside this module and must never be reduced by portfolio confidence.  v8 adds R0-root
relevance as a planning factor so observation-first questions are preferred over downstream reference
routes, without changing scientific truth gates.
"""
from __future__ import annotations

import math
from typing import Any

MAX_ACTIVE = 8


def _uncertainty(conf: float) -> float:
    return max(0.0, 1.0 - 2.0 * abs(float(conf) - 0.5))


def _status_factor(status: str) -> float:
    return {
        "PROPOSED": 0.75,
        "SCOUTING": 0.9,
        "TESTING": 1.0,
        "GROWING": 1.15,
        "CONDITIONAL": 1.05,
        "CHALLENGED": 1.2,
        "WEAKENED": 0.35,
        "DORMANT": 0.0,
        "FALSIFIED": 0.0,
    }.get(status, 0.8)


def priority(node: dict[str, Any]) -> float:
    """Information-value proxy, not truth probability.

    ``root_relevance`` is a north-star planning annotation only.  It never changes a measurement or
    success gate.  Nodes without v8 annotation retain a neutral 0.5 value for backward compatibility.
    """
    conf = float(node.get("confidence", 0.5))
    uncertainty = _uncertainty(conf)
    root = min(1.0, max(0.0, float(node.get("root_relevance", 0.5))))
    goal = min(1.0, max(0.0, float(node.get("goal_relevance", 0.5))))
    novelty = min(1.0, max(0.0, float(node.get("novelty", 0.5))))
    evidence = len(node.get("evidence_ids") or [])
    evidence_term = min(1.0, math.log1p(evidence) / math.log(6.0)) if evidence else 0.0
    raw = 0.32 * uncertainty + 0.28 * root + 0.10 * goal + 0.18 * novelty + 0.12 * evidence_term
    return max(0.0, raw * _status_factor(str(node.get("status") or "TESTING")))


def challenge_pressure(node: dict[str, Any]) -> float:
    """Stronger beliefs attract more attempts to break them."""
    conf = float(node.get("confidence", 0.5))
    support = float(node.get("support_weight", 0.0))
    return max(0.05, min(1.0, 0.2 + max(0.0, conf - 0.5) * 1.4 + min(0.3, support * 0.05)))


def build_portfolio(graph: dict[str, Any], *, hypothesis_budget: float = 0.35, max_active: int = MAX_ACTIVE) -> dict[str, Any]:
    nodes = [n for n in (graph.get("nodes") or {}).values() if str(n.get("status")) not in {"DORMANT", "FALSIFIED"}]
    ranked = sorted(nodes, key=lambda n: (priority(n), str(n.get("id"))), reverse=True)[:max(1, int(max_active))]
    scores = [priority(n) for n in ranked]
    denom = sum(scores) or 1.0
    items = []
    for n, score in zip(ranked, scores):
        share = float(hypothesis_budget) * score / denom
        focus = n.get("search_focus") if isinstance(n.get("search_focus"), dict) else None
        items.append({
            "hypothesis_id": n.get("id"),
            "status": n.get("status"),
            "confidence": float(n.get("confidence", 0.5)),
            "priority": round(score, 6),
            "hypothesis_budget_share": round(share, 6),
            "challenge_pressure": round(challenge_pressure(n), 6),
            "search_focus": focus,
            "runnable_focus": bool(focus and focus.get("family") and isinstance(focus.get("knobs"), dict)),
            "reason": {
                "uncertainty": round(_uncertainty(float(n.get("confidence", 0.5))), 4),
                "root_relevance": float(n.get("root_relevance", 0.5)),
                "root_alignment_class": n.get("root_alignment_class"),
                "goal_relevance": float(n.get("goal_relevance", 0.5)),
                "novelty": float(n.get("novelty", 0.5)),
                "evidence_cards": len(n.get("evidence_ids") or []),
            },
        })
    return {
        "version": 3,
        "research_north_star": "R0",
        "root_relevance_is_scientific_truth_probability": False,
        "hypothesis_budget_cap": float(hypothesis_budget),
        "active": items,
        "runnable_focuses": sum(bool(x.get("runnable_focus")) for x in items),
        "anti_bias": {
            "minimum_unexplored_fraction": 0.20,
            "minimum_assumption_breaker_fraction": 0.10,
            "minimum_random_fraction": 0.10,
            "hypothesis_exploitation_cap": 0.35,
            "stronger_belief_increases_challenge_pressure": True,
        },
        "changes_scientific_gate": False,
        "changes_official_level": False,
    }


def attach_to_decision(decision: dict[str, Any], portfolio: dict[str, Any]) -> dict[str, Any]:
    """Annotate the next plan without weakening any existing lane floor."""
    out = dict(decision)
    next_plan = dict(out.get("next_plan") or {})
    allocation = dict(next_plan.get("allocation") or {})
    available = min(0.35, max(0.0, float(allocation.get("hypothesis", 0.0))))
    active = portfolio.get("active") or []
    total = sum(float(x.get("hypothesis_budget_share", 0.0)) for x in active) or 1.0
    next_plan["hypothesis_portfolio"] = [
        {
            **x,
            "effective_lane_share": round(available * float(x.get("hypothesis_budget_share", 0.0)) / total, 6),
        }
        for x in active
    ]
    out["next_plan"] = next_plan
    out["portfolio_policy"] = {
        "subdivides_existing_hypothesis_lane_only": True,
        "can_reduce_unexplored_floor": False,
        "can_reduce_breaker_floor": False,
        "can_reduce_random_floor": False,
        "root_relevance_changes_scientific_gate": False,
    }
    return out
