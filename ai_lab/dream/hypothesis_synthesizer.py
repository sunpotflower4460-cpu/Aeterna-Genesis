"""Bounded hypothesis synthesis for Adaptive Dream v7.

The first implementation is deterministic and provider-free so hourly research never depends on an
external model or secret.  It creates falsifiable research proposals from recurrent X-patterns.  A
future LLM adapter may propose richer nodes, but every proposal must pass the same validator and may
never directly alter confidence, physics, thresholds, Levels, Rooms, or initial target morphology.
"""
from __future__ import annotations

from typing import Any

_FORBIDDEN = (
    "seed target",
    "seed triangle",
    "seed vortex",
    "seed charge",
    "seed division",
    "lower threshold",
    "change threshold",
    "official room",
    "official level",
)


def validate_proposal(p: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for field in ("id", "statement", "counter_statement", "falsification_condition", "next_test"):
        if not str(p.get(field) or "").strip():
            problems.append(f"missing:{field}")
    text = " ".join(str(p.get(k) or "") for k in ("statement", "counter_statement", "falsification_condition", "next_test")).lower()
    for bad in _FORBIDDEN:
        if bad in text:
            problems.append(f"forbidden:{bad}")
    if p.get("changes_scientific_gate") is True:
        problems.append("forbidden:changes_scientific_gate")
    if p.get("confidence") not in (None, 0.5):
        problems.append("proposal_cannot_set_confidence")
    return not problems, problems


def propose_from_unknown(unknown: dict[str, Any], *, burst_id: str, max_proposals: int = 3) -> list[dict[str, Any]]:
    patterns = unknown.get("patterns") or {}
    rows = list(patterns.values()) if isinstance(patterns, dict) else list(patterns)
    rows.sort(key=lambda r: (
        int((r.get("exact") or {}).get("hit", 0)) + int((r.get("local") or {}).get("hit", 0)),
        -int((r.get("contrast") or {}).get("hit", 0)),
        str(r.get("pattern_id") or ""),
    ), reverse=True)
    out: list[dict[str, Any]] = []
    for row in rows:
        if len(out) >= max(0, int(max_proposals)):
            break
        pid = str(row.get("pattern_id") or "")
        if not pid or row.get("status") != "REPEATED_SPECIFIC_CANDIDATE":
            continue
        proposal = {
            "id": f"route-question:{pid}",
            "origin": "deterministic-hypothesis-synthesizer",
            "parent_ids": [f"xpattern:{pid}:condition-specific"],
            "statement": f"X-pattern {pid} may be a useful predictor of a later persistent relation, identity-like persistence, or self-separation marker, without assuming any F-path stage.",
            "counter_statement": "The X-pattern is reproducible but has no predictive value for later goal-relevant transitions beyond baseline rates.",
            "falsification_condition": "Fresh-seed matched trials show no excess of later goal-relevant markers after the X-pattern compared with controls that do not show it.",
            "next_test": "Run matched fresh-seed X-positive/X-negative temporal follow-up; measure later markers only after classifying the earlier X-pattern.",
            "status": "PROPOSED",
            "confidence": 0.5,
            "goal_relevance": 0.72,
            "novelty": 0.8,
            "created_burst": burst_id,
            "changes_scientific_gate": False,
            "causal_claim": False,
        }
        ok, problems = validate_proposal(proposal)
        if ok:
            out.append(proposal)
        else:
            proposal["validation_problems"] = problems
    return out


def insert_proposals(graph: dict[str, Any], proposals: list[dict[str, Any]], *, burst_id: str) -> dict[str, Any]:
    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", [])
    for p in proposals:
        ok, _ = validate_proposal(p)
        if not ok:
            continue
        pid = str(p["id"])
        if pid not in nodes:
            nodes[pid] = {
                **p,
                "support_weight": 0.0,
                "contradiction_weight": 0.0,
                "evidence_ids": [],
                "independent_seeds": 0,
                "independent_conditions": 0,
                "last_updated_burst": burst_id,
            }
        for parent in p.get("parent_ids") or []:
            if not any(e.get("source") == parent and e.get("target") == pid and e.get("relation") == "suggests-test" for e in edges):
                edges.append({"source": parent, "target": pid, "relation": "suggests-test", "created_burst": burst_id})
    return graph
