"""Pure Genesis R0 automatic experimenter.

This module does *not* try to draw a universe, cell, neuron or brain.  It tests the smallest current
root hypothesis used by Aeterna:

    R0: something can become distinguishable from something else, and their relation can change.

A root run begins from a maximally permutation-symmetric relation state: every off-diagonal relation is
identical, so no position, distance, direction, geometry, frequency, phase, vortex, object or target is
encoded.  The first event is one anonymous relation changing slightly.  That event is the minimal
witness required to experimentally instantiate R0's "can change" clause; which pair changes and by how
much are numerical sampling/regulator choices and are varied in robustness checks.

Candidate dynamics are intentionally tiny expressions built only from the current relation, relation
composition through an intermediate distinction, relative relation contrast, and previous change.  No
candidate is declared fundamental: the search compares them and penalizes extra operators.  Geometry,
periodicity, closure and history dependence are measured only *after* evolution.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ai_lab.dream import why_gate

_REPO = Path(__file__).resolve().parents[2]
_HISTORY = _REPO / "ai_lab" / "discoveries" / "hypothesis_history.json"
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "root_latest.json"

TERM_ORDER = ("relation_self", "relation_composition_2", "relation_contrast", "relation_trend")
BASE_COEFFICIENTS = (-1.0, 0.0, 1.0)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _law_id(coefficients: dict[str, float]) -> str:
    raw = "|".join(f"{k}={float(coefficients.get(k, 0.0)):+.3f}" for k in TERM_ORDER)
    return "RLAW-" + hashlib.sha256(raw.encode()).hexdigest()[:10]


def law_proposal(coefficients: dict[str, float]) -> dict[str, Any]:
    operators = [k for k in TERM_ORDER if abs(float(coefficients.get(k, 0.0))) > 1e-12]
    return {
        "id": _law_id(coefficients),
        "why_chain": [why_gate.ROOT_ID, "relation", "candidate next-relation rule built only from R0-derived operators"],
        "operators": operators,
        "givens": [
            {"name": "distinguishability", "kind": "root_axiom"},
            {"name": "relation", "kind": "root_axiom"},
            {"name": "change", "kind": "root_axiom"},
            {"name": "finite_size", "kind": "numerical_regulator"},
            {"name": "step_count", "kind": "numerical_regulator"},
            {"name": "gauge_normalization", "kind": "numerical_regulator"},
            {"name": "root_event_pair", "kind": "numerical_regulator"},
            {"name": "root_event_sign", "kind": "numerical_regulator"},
            {"name": "operator_coefficient_grid", "kind": "numerical_regulator"},
        ],
        "target_encoded": False,
        "coefficients": {k: float(coefficients.get(k, 0.0)) for k in TERM_ORDER},
    }


def _canonical_candidates() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for vals in itertools.product(BASE_COEFFICIENTS, repeat=len(TERM_ORDER)):
        if not any(abs(v) > 1e-12 for v in vals):
            continue
        rows.append(dict(zip(TERM_ORDER, vals)))
    rows.sort(key=lambda c: (sum(abs(v) > 1e-12 for v in c.values()), _law_id(c)))
    return rows


def _mutations(previous: dict[str, Any]) -> Iterable[dict[str, float]]:
    for item in (previous.get("top_laws") or [])[:4]:
        base = {k: float((item.get("coefficients") or {}).get(k, 0.0)) for k in TERM_ORDER}
        for key in TERM_ORDER:
            for delta in (-0.5, 0.5):
                row = dict(base)
                row[key] = max(-1.5, min(1.5, row[key] + delta))
                if any(abs(v) > 1e-12 for v in row.values()):
                    yield row


def candidate_laws(*, max_laws: int, seed: int, previous: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Adaptive but deterministic law portfolio: simple laws + mutations of prior promising laws."""
    previous = previous or {}
    candidates = list(_mutations(previous)) + _canonical_candidates()
    dedup: dict[str, dict[str, float]] = {}
    for coeffs in candidates:
        dedup[_law_id(coeffs)] = coeffs
    rows = list(dedup.values())

    def key(c: dict[str, float]):
        complexity = sum(abs(v) > 1e-12 for v in c.values())
        h = hashlib.sha256(f"{seed}:{_law_id(c)}".encode()).hexdigest()
        return complexity, h

    rows.sort(key=key)
    out = []
    for coeffs in rows:
        p = law_proposal(coeffs)
        gate = why_gate.validate_proposal(p)
        if gate.accepted:
            p["why_gate"] = gate.as_dict()
            out.append(p)
        if len(out) >= max(0, int(max_laws)):
            break
    return out


def _normalize(r: np.ndarray, mode: str) -> np.ndarray:
    r = np.asarray(r, dtype=float).copy()
    np.fill_diagonal(r, 0.0)
    r = 0.5 * (r + r.T)
    if mode == "fro":
        scale = float(np.linalg.norm(r))
    elif mode == "max":
        scale = float(np.max(np.abs(r)))
    else:
        raise ValueError(f"unknown gauge normalization {mode!r}")
    if not np.isfinite(scale) or scale <= 1e-15:
        return np.zeros_like(r)
    return r / scale


def root_state(n: int, *, pair_index: int = 0, event_sign: int = 1, event_fraction: float = 0.05,
               normalization: str = "fro") -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Maximally symmetric relation state followed by one minimal anonymous relation-change event."""
    n = max(3, int(n))
    before = np.ones((n, n), dtype=float)
    np.fill_diagonal(before, 0.0)
    before = _normalize(before, normalization)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    pair = pairs[int(pair_index) % len(pairs)]
    after = before.copy()
    baseline = float(abs(before[pair])) or 1.0
    after[pair] += int(1 if event_sign >= 0 else -1) * max(1e-6, float(event_fraction)) * baseline
    after[pair[1], pair[0]] = after[pair]
    after = _normalize(after, normalization)
    return before, after, pair


def _compose2(r: np.ndarray) -> np.ndarray:
    out = (r @ r) / max(1, r.shape[0] - 1)
    np.fill_diagonal(out, 0.0)
    return 0.5 * (out + out.T)


def _contrast(r: np.ndarray) -> np.ndarray:
    mask = ~np.eye(r.shape[0], dtype=bool)
    mean = float(np.mean(r[mask]))
    out = r - mean
    np.fill_diagonal(out, 0.0)
    return out


def step_relation(previous: np.ndarray, current: np.ndarray, coefficients: dict[str, float], *, normalization: str) -> np.ndarray:
    terms = {
        "relation_self": current,
        "relation_composition_2": _compose2(current),
        "relation_contrast": _contrast(current),
        "relation_trend": current - previous,
    }
    raw = np.zeros_like(current, dtype=float)
    for name, arr in terms.items():
        raw += float(coefficients.get(name, 0.0)) * arr
    return _normalize(raw, normalization)


def _offdiag(r: np.ndarray) -> np.ndarray:
    return r[~np.eye(r.shape[0], dtype=bool)]


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    x, y = np.asarray(a, dtype=float).ravel(), np.asarray(b, dtype=float).ravel()
    if x.size != y.size or x.size == 0:
        return 0.0
    x, y = x - x.mean(), y - y.mean()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(np.dot(x, y) / denom) if denom > 1e-15 else 0.0


def _components(adj: np.ndarray) -> int:
    n = adj.shape[0]
    unseen = set(range(n))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            i = stack.pop()
            for j in np.flatnonzero(adj[i]):
                jj = int(j)
                if jj in unseen:
                    unseen.remove(jj)
                    stack.append(jj)
    return count


def _closure_metrics(r: np.ndarray) -> dict[str, Any]:
    vals = np.abs(_offdiag(r))
    if vals.size == 0 or float(np.max(vals)) <= 1e-15:
        return {"cycle_rank": 0, "cycle_density": 0.0, "threshold": None}
    threshold = float(np.quantile(vals, 0.80))
    adj = np.abs(r) >= threshold
    np.fill_diagonal(adj, False)
    adj = np.logical_or(adj, adj.T)
    edges = int(np.count_nonzero(np.triu(adj, 1)))
    components = _components(adj)
    cycle_rank = max(0, edges - r.shape[0] + components)
    possible = max(1, (r.shape[0] - 1) * (r.shape[0] - 2) // 2)
    return {"cycle_rank": cycle_rank, "cycle_density": min(1.0, cycle_rank / possible), "threshold": threshold}


def _recurrence(series: list[float]) -> dict[str, Any]:
    x = np.asarray(series, dtype=float)
    if x.size < 8 or float(np.std(x)) <= 1e-10:
        return {"peak_autocorrelation": 0.0, "period_steps_candidate": None, "physical_frequency_claim": False}
    x = x - x.mean()
    var = float(np.dot(x, x))
    best = (0.0, None)
    for lag in range(2, max(3, min(x.size // 2, 24))):
        denom = var or 1.0
        ac = float(np.dot(x[:-lag], x[lag:]) / denom)
        if ac > best[0]:
            best = (ac, lag)
    return {
        "peak_autocorrelation": round(max(0.0, best[0]), 6),
        "period_steps_candidate": int(best[1]) if best[1] is not None and best[0] >= 0.35 else None,
        "physical_frequency_claim": False,
        "note": "step周期は数値更新上の反復候補。物理的時間や周波数が創発したとはまだ言わない。",
    }


def _effective_rank(r: np.ndarray) -> float:
    s = np.linalg.svd(r, compute_uv=False)
    s = np.abs(s)
    tot = float(s.sum())
    if tot <= 1e-15:
        return 0.0
    p = s / tot
    entropy = -float(np.sum(p * np.log(p + 1e-30)))
    return float(np.exp(entropy))


def _history_dependence(prev: np.ndarray, curr: np.ndarray, coefficients: dict[str, float], *, normalization: str,
                        horizon: int = 8) -> float:
    """Counterfactual perturbation retention; intentionally not called memory."""
    n = curr.shape[0]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    base_prev, base = prev.copy(), curr.copy()
    test_prev, test = prev.copy(), curr.copy()
    pair = pairs[-1]
    before_delta = float(np.linalg.norm(test - base))
    scale = float(np.mean(np.abs(_offdiag(test)))) or 1.0
    test[pair] += 0.05 * scale
    test[pair[1], pair[0]] = test[pair]
    test = _normalize(test, normalization)
    injected = float(np.linalg.norm(test - base)) + before_delta
    for _ in range(max(1, int(horizon))):
        base_prev, base = base, step_relation(base_prev, base, coefficients, normalization=normalization)
        test_prev, test = test, step_relation(test_prev, test, coefficients, normalization=normalization)
    retained = float(np.linalg.norm(test - base))
    return min(2.0, retained / max(injected, 1e-12))


def run_one(coefficients: dict[str, float], *, n: int, steps: int, pair_index: int, event_sign: int,
            event_fraction: float, normalization: str) -> dict[str, Any]:
    prev, curr, pair = root_state(
        n, pair_index=pair_index, event_sign=event_sign, event_fraction=event_fraction, normalization=normalization,
    )
    initial_contrast = float(np.std(_offdiag(curr)))
    differentiation: list[float] = [initial_contrast]
    activity: list[float] = []
    snapshots: list[np.ndarray] = [curr.copy()]
    finite = True
    for _ in range(max(1, int(steps))):
        nxt = step_relation(prev, curr, coefficients, normalization=normalization)
        if not np.all(np.isfinite(nxt)):
            finite = False
            break
        activity.append(float(np.linalg.norm(nxt - curr)))
        differentiation.append(float(np.std(_offdiag(nxt))))
        prev, curr = curr, nxt
        snapshots.append(curr.copy())
    final_contrast = float(np.std(_offdiag(curr)))
    persistence = _corr(np.abs(snapshots[-1]), np.abs(snapshots[-2])) if len(snapshots) >= 2 else 0.0
    closure = _closure_metrics(curr)
    recurrence = _recurrence(differentiation)
    history = _history_dependence(prev, curr, coefficients, normalization=normalization) if finite else 0.0
    rank = _effective_rank(curr)
    differentiation_gain = final_contrast / max(initial_contrast, 1e-12)
    nontrivial_activity = float(np.mean(activity[-min(8, len(activity)):])) if activity else 0.0
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
        "geometry_was_seeded": False,
        "frequency_was_seeded": False,
        "torus_was_seeded": False,
        "vortex_was_seeded": False,
        "brain_was_seeded": False,
    }


def _run_score(run: dict[str, Any]) -> float:
    if not run.get("finite"):
        return 0.0
    diff = min(1.0, math.log1p(float(run.get("differentiation_gain", 0.0))) / math.log(6.0))
    act = min(1.0, float(run.get("late_activity", 0.0)) * 5.0)
    persist = max(0.0, float(run.get("relation_pattern_persistence", 0.0)))
    recur = min(1.0, float((run.get("recurrence") or {}).get("peak_autocorrelation", 0.0)))
    closure = min(1.0, float((run.get("closure") or {}).get("cycle_density", 0.0)) * 5.0)
    hist = min(1.0, float(run.get("counterfactual_history_dependence", 0.0)))
    return 0.28 * diff + 0.18 * act + 0.16 * persist + 0.12 * recur + 0.10 * closure + 0.16 * hist


def evaluate_law(proposal: dict[str, Any], *, sizes: tuple[int, ...], steps: int, seed: int) -> dict[str, Any]:
    coeffs = proposal["coefficients"]
    runs: list[dict[str, Any]] = []
    for idx, n in enumerate(sizes):
        for norm in ("fro", "max"):
            sign = 1 if (idx + seed) % 2 == 0 else -1
            pair_index = (seed * 17 + idx * 5 + (0 if norm == "fro" else 3))
            fraction = 0.03 if norm == "fro" else 0.07
            runs.append(run_one(
                coeffs, n=n, steps=steps, pair_index=pair_index, event_sign=sign,
                event_fraction=fraction, normalization=norm,
            ))
            runs.append(run_one(
                coeffs, n=n, steps=steps, pair_index=pair_index + 1, event_sign=-sign,
                event_fraction=fraction, normalization=norm,
            ))
    scores = np.asarray([_run_score(r) for r in runs], dtype=float)
    mean = float(scores.mean()) if scores.size else 0.0
    spread = float(scores.std()) if scores.size else 1.0
    robustness = max(0.0, 1.0 - min(1.0, spread / max(mean, 0.10)))
    complexity = sum(abs(float(coeffs.get(k, 0.0))) > 1e-12 for k in TERM_ORDER)
    priority = max(0.0, mean * (0.65 + 0.35 * robustness) - 0.025 * max(0, complexity - 1))
    periods = [int((r.get("recurrence") or {}).get("period_steps_candidate")) for r in runs
               if (r.get("recurrence") or {}).get("period_steps_candidate") is not None]
    cycle_hits = sum(int((r.get("closure") or {}).get("cycle_rank", 0)) > 0 for r in runs)
    history_hits = sum(float(r.get("counterfactual_history_dependence", 0.0)) >= 0.15 for r in runs)
    if priority >= 0.55 and robustness >= 0.55:
        status = "GROWING"
    elif priority >= 0.25:
        status = "TESTING"
    else:
        status = "WEAKENED"
    return {
        "id": proposal["id"],
        "origin": "pure-genesis-root-law",
        "statement": "R0-derived relation operators may generate persistent nontrivial relational organization without downstream structures being supplied.",
        "coefficients": coeffs,
        "operators": proposal["operators"],
        "why_chain": proposal["why_chain"],
        "why_gate": proposal["why_gate"],
        "axiom_cost": complexity,
        "status": status,
        "planning_confidence": round(min(0.82, max(0.18, 0.5 + (priority - 0.5) * 0.6)), 4),
        "priority": round(priority, 6),
        "mean_discovery_value": round(mean, 6),
        "regulator_robustness": round(robustness, 6),
        "runs": runs,
        "observations": {
            "recurrent_step_period_candidates": sorted(set(periods)),
            "closure_runs": cycle_hits,
            "history_dependence_runs": history_hits,
            "total_runs": len(runs),
            "physical_frequency_claim": False,
            "geometry_claim": False,
            "torus_claim": False,
            "vortex_claim": False,
            "brain_claim": False,
        },
    }


def _root_graph_nodes(results: list[dict[str, Any]], *, burst_id: str) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for item in results[:8]:
        hid = f"rootlaw:{item['id']}"
        nodes[hid] = {
            "id": hid,
            "origin": "pure-genesis-root-law",
            "statement": item["statement"],
            "counter_statement": "The apparent organization depends on a numerical regulator or added operator rather than surviving as an R0-derived result.",
            "falsification_condition": "The behavior disappears across finite-size, normalization, event-pair/sign, or holdout-law perturbation checks.",
            "parent_ids": [],
            "status": item["status"],
            "confidence": item["planning_confidence"],
            "support_weight": 0.0,
            "contradiction_weight": 0.0,
            "evidence_ids": [f"pure-genesis:{burst_id}:{item['id']}"],
            "independent_seeds": 0,
            "independent_conditions": len(item.get("runs") or []),
            "goal_relevance": 1.0,
            "root_relevance": 1.0,
            "novelty": 0.95,
            "created_burst": burst_id,
            "last_updated_burst": burst_id,
            "why_chain": item["why_chain"],
            "axiom_cost": item["axiom_cost"],
            "root_law_priority": item["priority"],
        }
    return nodes


def run_root_research(*, burst_id: str, law_trials: int = 24, sizes: tuple[int, ...] = (8, 12, 16),
                      steps: int = 48, seed: int = 0, persist: bool = True) -> dict[str, Any]:
    shared_history = _read(_HISTORY, {"version": 1, "bursts": []})
    previous = dict(shared_history.get("pure_genesis_r0") or {"version": 1, "top_laws": []})
    proposals = candidate_laws(max_laws=law_trials, seed=seed, previous=previous)
    results = [evaluate_law(p, sizes=tuple(max(3, int(n)) for n in sizes), steps=max(8, int(steps)), seed=seed + i)
               for i, p in enumerate(proposals)]
    results.sort(key=lambda x: (float(x.get("priority", 0.0)), -int(x.get("axiom_cost", 99)), str(x.get("id"))), reverse=True)
    top = results[: min(8, len(results))]
    gate_audit = {
        "version": 1,
        "burst_id": burst_id,
        "root_id": why_gate.ROOT_ID,
        "root_statement": why_gate.ROOT_STATEMENT,
        "root_reason": why_gate.ROOT_REASON,
        "proposals_checked": len(proposals),
        "accepted": sum(bool((p.get("why_gate") or {}).get("accepted")) for p in proposals),
        "rejected": 0,
        "downstream_concepts_seeded": False,
        "physical_givens_beyond_R0": [],
        "numerical_regulators_are_physical_claims": False,
    }
    report = {
        "version": 1,
        "mode": "pure-genesis-r0-shadow-research",
        "burst_id": burst_id,
        "root": {
            "id": why_gate.ROOT_ID,
            "statement": why_gate.ROOT_STATEMENT,
            "reason": why_gate.ROOT_REASON,
            "current_minimal_hypothesis_not_final_metaphysical_truth": True,
        },
        "research_question": "R0だけから、下流の答えを置かずに、持続・反復・閉路・履歴依存をもつ関係構造が自然に現れるか。",
        "law_trials": len(results),
        "sizes": list(sizes),
        "steps": int(steps),
        "top_laws": top,
        "all_laws": results,
        "root_graph_nodes": _root_graph_nodes(top, burst_id=burst_id),
        "why_gate": gate_audit,
        "observed_not_seeded": [
            "differentiation", "recurrence", "closure", "effective_relation_rank", "counterfactual_history_dependence"
        ],
        "not_claimed": ["physical_space", "physical_dimension", "physical_frequency", "torus", "vortex", "life", "brain", "consciousness"],
        "brain_from_zero": {
            "brain_is_target_encoded": False,
            "brain_claim": False,
            "principle": "宇宙と脳を別レシピにせず、R0から関係が階層化・再帰できるかを調べる。脳は先に定義しない。",
        },
        "honesty": {
            "node_count_is_physical_particle_count": False,
            "update_step_is_physical_time": False,
            "normalization_is_physical_law": False,
            "scalar_relation_representation_is_proven_fundamental": False,
            "root_event_pair_or_sign_is_targeted": False,
            "geometry_seeded": False,
            "frequency_seeded": False,
            "vortex_seeded": False,
            "torus_seeded": False,
            "brain_seeded": False,
        },
    }
    state = {
        "version": 1,
        "last_burst": burst_id,
        "top_laws": [
            {"id": x["id"], "coefficients": x["coefficients"], "priority": x["priority"], "status": x["status"]}
            for x in top
        ],
    }
    if persist:
        shared_history["pure_genesis_r0"] = {**state, "why_gate": gate_audit}
        _write(_HISTORY, shared_history)
        _write(_REPORT, report)
    return report


def merge_root_nodes(graph: dict[str, Any], root_report: dict[str, Any], *, burst_id: str) -> dict[str, Any]:
    """Mirror root-law planning hypotheses into the shared v7 graph without changing evidence gates."""
    nodes = graph.setdefault("nodes", {})
    for hid, fresh in (root_report.get("root_graph_nodes") or {}).items():
        old = nodes.get(hid)
        if old is None:
            nodes[hid] = dict(fresh)
            continue
        old.update({
            "statement": fresh.get("statement"),
            "counter_statement": fresh.get("counter_statement"),
            "falsification_condition": fresh.get("falsification_condition"),
            "status": fresh.get("status"),
            "confidence": fresh.get("confidence"),
            "goal_relevance": 1.0,
            "root_relevance": 1.0,
            "novelty": fresh.get("novelty", 0.95),
            "last_updated_burst": burst_id,
            "why_chain": fresh.get("why_chain"),
            "axiom_cost": fresh.get("axiom_cost"),
            "root_law_priority": fresh.get("root_law_priority"),
        })
        eids = list(dict.fromkeys(list(old.get("evidence_ids") or []) + list(fresh.get("evidence_ids") or [])))
        old["evidence_ids"] = eids[-64:]
    return why_gate.annotate_graph(graph)
