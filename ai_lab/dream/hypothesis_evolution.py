"""Adaptive Dream v7 hypothesis graph and deterministic evolution.

The graph is a research-planning layer only.  It may strengthen, weaken, branch, or park research
hypotheses, but it cannot alter measurements, scientific gates, official Levels, official Rooms,
or model dynamics.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_GRAPH = _REPO / "ai_lab" / "discoveries" / "hypothesis_graph.json"
_HISTORY = _REPO / "ai_lab" / "discoveries" / "hypothesis_history.json"

ACTIVE = {"PROPOSED", "SCOUTING", "TESTING", "GROWING", "CONDITIONAL", "CHALLENGED", "WEAKENED"}


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    os.replace(tmp, path)


def empty_graph() -> dict[str, Any]:
    return {
        "version": 1,
        "nodes": {},
        "edges": [],
        "policy": {
            "changes_scientific_gate": False,
            "changes_official_level": False,
            "writes_official_rooms": False,
            "can_seed_target_morphology": False,
            "can_seed_vortex_position_or_charge": False,
            "can_seed_division_location_or_time": False,
            "can_use_quarantined_evidence": False,
        },
    }


def load_graph(path: Path | None = None) -> dict[str, Any]:
    return _read(path or _GRAPH, empty_graph())


def _edge(graph: dict[str, Any], source: str, target: str, relation: str, *, burst_id: str) -> None:
    key = (source, target, relation)
    if any((e.get("source"), e.get("target"), e.get("relation")) == key for e in graph.get("edges") or []):
        return
    graph.setdefault("edges", []).append({
        "source": source,
        "target": target,
        "relation": relation,
        "created_burst": burst_id,
    })


def _legacy_node(h: dict[str, Any], *, burst_id: str) -> dict[str, Any]:
    status_map = {
        "TESTING": "TESTING",
        "SUPPORTED": "GROWING",
        "UNCERTAIN": "TESTING",
        "WEAKENED": "WEAKENED",
    }
    return {
        "id": str(h.get("id")),
        "origin": "human-reference-hypothesis",
        "statement": str(h.get("statement") or ""),
        "counter_statement": str(h.get("counter_statement") or ""),
        "falsification_condition": str(h.get("falsification_condition") or ""),
        "parent_ids": [],
        "status": status_map.get(str(h.get("status")), "TESTING"),
        "confidence": float(h.get("confidence", 0.5)),
        "support_weight": 0.0,
        "contradiction_weight": 0.0,
        "evidence_ids": [],
        "independent_seeds": 0,
        "independent_conditions": 0,
        "goal_relevance": 0.5,
        "novelty": 0.25,
        "created_burst": burst_id,
        "last_updated_burst": burst_id,
        "legacy_snapshot": {
            "support": int(h.get("support", 0)),
            "contradiction": int(h.get("contradiction", 0)),
        },
    }


def migrate_legacy(graph: dict[str, Any], legacy: dict[str, Any], *, burst_id: str) -> dict[str, Any]:
    nodes = graph.setdefault("nodes", {})
    for h in legacy.get("hypotheses") or []:
        hid = str(h.get("id") or "")
        if not hid:
            continue
        if hid not in nodes:
            nodes[hid] = _legacy_node(h, burst_id=burst_id)
        else:
            nodes[hid]["legacy_snapshot"] = {
                "support": int(h.get("support", 0)),
                "contradiction": int(h.get("contradiction", 0)),
            }
            nodes[hid]["last_updated_burst"] = burst_id
    if "three-vortex-triangle-fission" in nodes and "triangle-balance-break-fission" in nodes:
        child = nodes["triangle-balance-break-fission"]
        if "three-vortex-triangle-fission" not in child.setdefault("parent_ids", []):
            child["parent_ids"].append("three-vortex-triangle-fission")
        _edge(graph, "three-vortex-triangle-fission", "triangle-balance-break-fission", "refines", burst_id=burst_id)
    return graph


def _clean_focus(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or not isinstance(raw.get("knobs"), dict) or not raw.get("family"):
        return None
    return {
        "family": raw.get("family"),
        "knobs": dict(raw.get("knobs") or {}),
        "source_pattern_id": raw.get("source_pattern_id"),
        "source_trial_index": raw.get("source_trial_index"),
        "captured_burst": raw.get("captured_burst"),
        "target_shape_seeded": False,
    }


def ingest_unknown_patterns(graph: dict[str, Any], unknown: dict[str, Any], *, burst_id: str) -> dict[str, Any]:
    nodes = graph.setdefault("nodes", {})
    patterns = unknown.get("patterns") or {}
    rows = patterns.values() if isinstance(patterns, dict) else patterns
    for row in rows:
        pid = str(row.get("pattern_id") or "")
        if not pid:
            continue
        hid = f"xpattern:{pid}"
        node = nodes.setdefault(hid, {
            "id": hid,
            "origin": "open-ended-x-pattern",
            "statement": f"X-pattern {pid} is a reproducible transition fingerprint under at least part of its observed start-condition neighborhood.",
            "counter_statement": "The apparent recurrence is seed/sampling noise or so broad that the stated condition relationship is not informative.",
            "falsification_condition": "Fresh-seed exact and nearby reproduction repeatedly fail, or the proposed specificity disappears under contrast tests.",
            "parent_ids": [],
            "status": "SCOUTING",
            "confidence": 0.5,
            "support_weight": 0.0,
            "contradiction_weight": 0.0,
            "evidence_ids": [],
            "independent_seeds": 0,
            "independent_conditions": 0,
            "goal_relevance": 0.45,
            "novelty": 0.85,
            "created_burst": burst_id,
        })
        node["last_updated_burst"] = burst_id
        node["followup_status"] = row.get("status")
        exact, local, contrast = row.get("exact") or {}, row.get("local") or {}, row.get("contrast") or {}
        node["followup_counts"] = {"exact": exact, "nearby": local, "contrast": contrast}
        focus = _clean_focus(row.get("search_focus"))
        if focus:
            node["search_focus"] = focus

        evidence_hit = int(exact.get("hit", 0)) + int(local.get("hit", 0))
        contrast_hit = int(contrast.get("hit", 0))
        if evidence_hit >= 2 and contrast_hit == 0:
            child_id = f"{hid}:condition-specific"
            child = nodes.setdefault(child_id, {
                "id": child_id,
                "origin": "automatic-branch",
                "statement": f"X-pattern {pid} is condition-specific enough that exact/nearby reproduction exceeds deliberately different contrast conditions.",
                "counter_statement": "The apparent specificity vanishes with more contrast or nearby trials.",
                "falsification_condition": "Contrast hits accumulate or exact/nearby reproduction falls to the contrast baseline.",
                "parent_ids": [hid],
                "status": "CONDITIONAL",
                "confidence": 0.5,
                "support_weight": 0.0,
                "contradiction_weight": 0.0,
                "evidence_ids": [],
                "independent_seeds": 0,
                "independent_conditions": 0,
                "goal_relevance": float(node.get("goal_relevance", 0.45)),
                "novelty": 0.75,
                "created_burst": burst_id,
            })
            child["last_updated_burst"] = burst_id
            child["branch_reason"] = "exact_or_nearby_recurrence_with_zero_contrast_hits"
            if focus:
                child["search_focus"] = focus
            _edge(graph, hid, child_id, "refines", burst_id=burst_id)
    return graph


def _status(node: dict[str, Any]) -> str:
    s = float(node.get("support_weight", 0.0))
    c = float(node.get("contradiction_weight", 0.0))
    conf = float(node.get("confidence", 0.5))
    if c >= 3.0 and s < 0.75:
        return "WEAKENED"
    if conf >= 0.72 and s >= 1.5:
        return "CHALLENGED"
    if conf >= 0.62 and s >= 1.0:
        return "GROWING"
    if s + c < 0.5:
        return node.get("status") if node.get("status") in {"PROPOSED", "SCOUTING", "CONDITIONAL"} else "TESTING"
    return "TESTING"


def apply_evidence(graph: dict[str, Any], cards: list[dict[str, Any]], *, burst_id: str) -> dict[str, Any]:
    nodes = graph.setdefault("nodes", {})
    for card in cards:
        hid = str(card.get("hypothesis_id") or "")
        node = nodes.get(hid)
        if node is None:
            continue
        eid = str(card.get("evidence_id") or "")
        if not eid or eid in set(node.get("evidence_ids") or []):
            continue
        node.setdefault("evidence_ids", []).append(eid)
        w = float(card.get("weight", 0.0))
        if card.get("direction") == "SUPPORT":
            node["support_weight"] = float(node.get("support_weight", 0.0)) + w
        elif card.get("direction") == "CONTRADICT":
            node["contradiction_weight"] = float(node.get("contradiction_weight", 0.0)) + w
        node["last_updated_burst"] = burst_id

    for node in nodes.values():
        s = float(node.get("support_weight", 0.0))
        c = float(node.get("contradiction_weight", 0.0))
        if s + c > 0:
            node["confidence"] = round(min(0.85, max(0.15, (s + 1.0) / (s + c + 2.0))), 4)
        node["status"] = _status(node)
    graph["last_updated_burst"] = burst_id
    return graph


def evolve(*, legacy: dict[str, Any], unknown: dict[str, Any], cards: list[dict[str, Any]], burst_id: str,
           graph_path: Path | None = None, history_path: Path | None = None, persist: bool = True) -> dict[str, Any]:
    graph = load_graph(graph_path)
    before = {k: (v.get("status"), v.get("confidence")) for k, v in (graph.get("nodes") or {}).items()}
    migrate_legacy(graph, legacy, burst_id=burst_id)
    ingest_unknown_patterns(graph, unknown, burst_id=burst_id)
    apply_evidence(graph, cards, burst_id=burst_id)
    changes = []
    for hid, node in (graph.get("nodes") or {}).items():
        prior = before.get(hid)
        now = (node.get("status"), node.get("confidence"))
        if prior != now:
            changes.append({"hypothesis_id": hid, "before": prior, "after": now})
    history = _read(history_path or _HISTORY, {"version": 1, "bursts": []})
    history.setdefault("bursts", []).append({"burst_id": burst_id, "changes": changes})
    history["bursts"] = history["bursts"][-128:]
    if persist:
        _save(graph_path or _GRAPH, graph)
        _save(history_path or _HISTORY, history)
    return {"graph": graph, "changes": changes, "history": history}
