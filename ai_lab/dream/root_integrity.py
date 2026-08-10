"""Integrity audit for Pure Genesis R0 experiments.

The raw R0 search intentionally uses anonymous finite relation slots as a computational canvas.  This
module prevents properties of that canvas from being mistaken for physics.  In particular:

* anonymous slot labels are not physical entities; physical distinguishability is estimated from
  label-free relational profiles (a permutation quotient),
* the complete latent relation matrix is not evidence that a physical closed network emerged,
* because R0 supplies no polarity/charge axiom, a global sign inversion is treated as a representation
  gauge until a future Why Chain earns physical sign,
* a period measured in discrete update steps is never scored as physical frequency.

The audit changes *planning priority only*.  It does not change any official scientific gate, Room or
Emergence Level.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab.dream import pure_genesis

_REPO = Path(__file__).resolve().parents[2]
_HISTORY = _REPO / "ai_lab" / "discoveries" / "hypothesis_history.json"
_ROOT_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "root_latest.json"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _pair_index(n: int, pair: list[int] | tuple[int, int]) -> int:
    target = tuple(int(x) for x in pair)
    pairs = [(i, j) for i in range(int(n)) for j in range(i + 1, int(n))]
    try:
        return pairs.index(target)
    except ValueError:
        return 0


def _trajectory(run: dict[str, Any], coefficients: dict[str, float]) -> list[np.ndarray]:
    n = max(3, int(run.get("n", 3)))
    normalization = str(run.get("normalization") or "fro")
    pair_index = _pair_index(n, run.get("root_event_pair") or [0, 1])
    prev, curr, _ = pure_genesis.root_state(
        n,
        pair_index=pair_index,
        event_sign=int(run.get("root_event_sign", 1)),
        event_fraction=float(run.get("root_event_fraction", 0.05)),
        normalization=normalization,
    )
    states = [curr.copy()]
    for _ in range(max(1, int(run.get("steps", 1)))):
        nxt = pure_genesis.step_relation(prev, curr, coefficients, normalization=normalization)
        if not np.all(np.isfinite(nxt)):
            break
        prev, curr = curr, nxt
        states.append(curr.copy())
    return states


def _label_free_profile(r: np.ndarray, i: int) -> np.ndarray:
    """Sorted relations to all *other* latent slots; invariant to permutation of slot names."""
    row = np.delete(np.asarray(r[i], dtype=float), i)
    return np.sort(row)


def _profile_classes(r: np.ndarray) -> list[list[int]]:
    """Greedy equivalence classes of slots with the same label-free relational profile.

    The tolerance scales with the represented relation magnitude.  It is a numerical diagnostic, not a
    physical threshold, and is only used to reject claims based on arbitrary slot labels.
    """
    r = np.asarray(r, dtype=float)
    scale = max(float(np.max(np.abs(r))), 1.0e-12)
    tol = max(1.0e-9, scale * 1.0e-6)
    profiles = [_label_free_profile(r, i) for i in range(r.shape[0])]
    classes: list[list[int]] = []
    reps: list[np.ndarray] = []
    for idx, profile in enumerate(profiles):
        placed = False
        for j, rep in enumerate(reps):
            if profile.shape == rep.shape and float(np.max(np.abs(profile - rep))) <= tol:
                classes[j].append(idx)
                placed = True
                break
        if not placed:
            classes.append([idx])
            reps.append(profile)
    return classes


def _class_relation_matrix(r: np.ndarray, classes: list[list[int]]) -> np.ndarray:
    k = len(classes)
    out = np.zeros((k, k), dtype=float)
    for a, ca in enumerate(classes):
        for b, cb in enumerate(classes):
            vals: list[float] = []
            for i in ca:
                for j in cb:
                    if i != j:
                        vals.append(float(r[i, j]))
            out[a, b] = float(np.mean(vals)) if vals else 0.0
    return out


def _components(adj: np.ndarray) -> int:
    n = int(adj.shape[0])
    unseen = set(range(n))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            i = stack.pop()
            for raw in np.flatnonzero(adj[i]):
                j = int(raw)
                if j in unseen:
                    unseen.remove(j)
                    stack.append(j)
    return count


def _cycle_rank(adj: np.ndarray) -> int:
    n = int(adj.shape[0])
    if n < 3:
        return 0
    edges = int(np.count_nonzero(np.triu(adj, 1)))
    return max(0, edges - n + _components(adj))


def _quotient_closure(r: np.ndarray, classes: list[list[int]]) -> dict[str, Any]:
    """Closure among *emergent relational classes*, never among latent slot labels.

    We test three relative contrast cutoffs instead of blessing one arbitrary threshold.  A closure lead
    is called regulator-robust only when a cycle survives all three views.
    """
    k = len(classes)
    if k < 3:
        return {
            "distinction_classes": k,
            "cycle_ranks": {"0.25": 0, "0.50": 0, "0.75": 0},
            "robust_cycle": False,
            "physical_geometry_claim": False,
        }
    cr = _class_relation_matrix(r, classes)
    vals = np.asarray([cr[i, j] for i in range(k) for j in range(i + 1, k)], dtype=float)
    mean = float(np.mean(vals)) if vals.size else 0.0
    contrast = np.abs(cr - mean)
    np.fill_diagonal(contrast, 0.0)
    maxc = float(np.max(contrast)) if contrast.size else 0.0
    ranks: dict[str, int] = {}
    for frac in (0.25, 0.50, 0.75):
        if maxc <= 1.0e-12:
            adj = np.zeros_like(contrast, dtype=bool)
        else:
            adj = contrast >= (frac * maxc)
            np.fill_diagonal(adj, False)
            adj = np.logical_or(adj, adj.T)
        ranks[f"{frac:.2f}"] = _cycle_rank(adj)
    return {
        "distinction_classes": k,
        "cycle_ranks": ranks,
        "robust_cycle": bool(ranks and all(v > 0 for v in ranks.values())),
        "physical_geometry_claim": False,
        "note": "latent slotの完全グラフではなく、ラベル不変な関係profileから生じた区別class間だけを測る。",
    }


def _gauge_distance(a: np.ndarray, b: np.ndarray) -> tuple[float, bool]:
    """Distance modulo a global sign, because R0 has not earned a polarity axiom."""
    denom = max(float(np.linalg.norm(a)), float(np.linalg.norm(b)), 1.0e-12)
    same = float(np.linalg.norm(a - b)) / denom
    flipped = float(np.linalg.norm(a + b)) / denom
    return min(same, flipped), bool(flipped + 1.0e-12 < same)


def _audit_run(run: dict[str, Any], coefficients: dict[str, float]) -> dict[str, Any]:
    states = _trajectory(run, coefficients)
    if not states:
        return {
            "initial_distinction_classes": 0,
            "final_distinction_classes": 0,
            "new_classes_beyond_root_event": 0,
            "gauge_invariant_late_activity": 0.0,
            "global_sign_alias_fraction": 0.0,
            "quotient_closure": {"robust_cycle": False},
            "integrity_flags": ["NO_FINITE_TRAJECTORY"],
        }
    initial_classes = _profile_classes(states[0])
    final_classes = _profile_classes(states[-1])
    initial_closure = _quotient_closure(states[0], initial_classes)
    final_closure = _quotient_closure(states[-1], final_classes)
    distances: list[float] = []
    aliases = 0
    for a, b in zip(states[:-1], states[1:]):
        d, alias = _gauge_distance(a, b)
        distances.append(d)
        aliases += int(alias)
    late = distances[-min(8, len(distances)):] if distances else []
    gauge_activity = float(np.mean(late)) if late else 0.0
    alias_fraction = aliases / max(1, len(distances))
    flags: list[str] = []
    if alias_fraction >= 0.75 and gauge_activity <= 0.02:
        flags.append("GLOBAL_SIGN_FLIP_GAUGE_ALIAS")
    if int((run.get("closure") or {}).get("cycle_rank", 0)) > 0:
        flags.append("RAW_SLOT_GRAPH_CLOSURE_REJECTED")
    if (run.get("recurrence") or {}).get("period_steps_candidate") is not None:
        flags.append("STEP_RECURRENCE_NOT_PHYSICAL_FREQUENCY")
    if final_closure.get("robust_cycle") and initial_closure.get("robust_cycle"):
        flags.append("CLOSURE_ALREADY_PRESENT_AFTER_ROOT_EVENT")
    return {
        "initial_distinction_classes": len(initial_classes),
        "final_distinction_classes": len(final_classes),
        "new_classes_beyond_root_event": max(0, len(final_classes) - len(initial_classes)),
        "gauge_invariant_late_activity": gauge_activity,
        "global_sign_alias_fraction": alias_fraction,
        "initial_quotient_closure": initial_closure,
        "quotient_closure": final_closure,
        "new_robust_closure_after_root_event": bool(
            final_closure.get("robust_cycle") and not initial_closure.get("robust_cycle")
        ),
        "integrity_flags": flags,
        "latent_slot_labels_are_physical_entities": False,
        "global_relation_sign_is_physical_polarity": False,
        "update_step_period_is_physical_frequency": False,
    }


def _audited_run_value(run: dict[str, Any], audit: dict[str, Any]) -> float:
    if not run.get("finite"):
        return 0.0
    n = max(3, int(run.get("n", 3)))
    gain = max(0.0, float(run.get("differentiation_gain", 0.0)))
    contrast = min(1.0, math.log1p(gain) / math.log(6.0))
    final_classes = max(1, int(audit.get("final_distinction_classes", 1)))
    initial_classes = max(1, int(audit.get("initial_distinction_classes", 1)))
    class_diversity = min(1.0, max(0.0, (final_classes - 1) / max(1, n - 1)))
    new_classes = min(1.0, max(0.0, (final_classes - initial_classes) / max(1, n - initial_classes)))
    activity = min(1.0, max(0.0, float(audit.get("gauge_invariant_late_activity", 0.0))) * 5.0)
    history = min(1.0, max(0.0, float(run.get("counterfactual_history_dependence", 0.0))))
    persistence = max(0.0, min(1.0, float(run.get("relation_pattern_persistence", 0.0))))
    closure = 1.0 if audit.get("new_robust_closure_after_root_event") else 0.0
    value = (
        0.22 * contrast
        + 0.18 * class_diversity
        + 0.12 * new_classes
        + 0.15 * activity
        + 0.13 * history
        + 0.10 * closure
        + 0.10 * persistence
    )
    if "GLOBAL_SIGN_FLIP_GAUGE_ALIAS" in (audit.get("integrity_flags") or []):
        value *= 0.70
    return max(0.0, min(1.0, value))


def _audit_law(law: dict[str, Any]) -> dict[str, Any]:
    raw_priority = float(law.get("priority", 0.0))
    raw_value = float(law.get("mean_discovery_value", 0.0))
    audits: list[dict[str, Any]] = []
    values: list[float] = []
    for run in law.get("runs") or []:
        audit = _audit_run(run, law.get("coefficients") or {})
        audits.append(audit)
        values.append(_audited_run_value(run, audit))
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean()) if arr.size else 0.0
    spread = float(arr.std()) if arr.size else 1.0
    robustness = max(0.0, 1.0 - min(1.0, spread / max(mean, 0.10)))
    complexity = max(1, int(law.get("axiom_cost", 1)))
    adjusted = max(0.0, mean * (0.65 + 0.35 * robustness) - 0.025 * max(0, complexity - 1))
    flags = sorted({flag for a in audits for flag in (a.get("integrity_flags") or [])})
    if adjusted >= 0.55 and robustness >= 0.55:
        status = "GROWING"
    elif adjusted >= 0.25:
        status = "TESTING"
    else:
        status = "WEAKENED"
    law["raw_priority_before_root_integrity"] = raw_priority
    law["raw_mean_discovery_value_before_root_integrity"] = raw_value
    law["mean_discovery_value"] = round(mean, 6)
    law["regulator_robustness"] = round(robustness, 6)
    law["priority"] = round(adjusted, 6)
    law["status"] = status
    law["planning_confidence"] = round(min(0.82, max(0.18, 0.5 + (adjusted - 0.5) * 0.6)), 4)
    law["root_integrity"] = {
        "version": 1,
        "runs": audits,
        "flags": flags,
        "raw_slot_closure_used_for_priority": False,
        "step_period_used_as_physical_frequency_for_priority": False,
        "global_sign_is_physical_polarity": False,
        "permutation_quotient_used": True,
    }
    return law


def _critic_questions(laws: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    all_audits = [a for law in laws for a in ((law.get("root_integrity") or {}).get("runs") or [])]
    if any("GLOBAL_SIGN_FLIP_GAUGE_ALIAS" in (a.get("integrity_flags") or []) for a in all_audits):
        questions.append({
            "id": "RQC-global-sign",
            "question": "見えている2周期は、R0から得た現象ではなく全体符号反転という表現上の別名ではないか？",
            "next_test": "global signを同一視した距離でのみ持続的変化を評価する。",
        })
    if not any(int(a.get("new_classes_beyond_root_event", 0)) > 0 for a in all_audits):
        questions.append({
            "id": "RQC-new-distinction",
            "question": "現在の候補法則はR0の最初の差を増幅するだけで、新しい区別そのものを生んでいないのではないか？",
            "next_test": "下流部品を足さず、R0から説明できる候補演算の簡約・別表現を探索する。",
        })
    if not any(bool(a.get("new_robust_closure_after_root_event")) for a in all_audits):
        questions.append({
            "id": "RQC-closure",
            "question": "latent slotの完全なつながりを除いた後、本当に新しい閉じた関係は生まれているか？",
            "next_test": "permutation quotient後の区別class間だけで閉路を再検証する。",
        })
    top = laws[: min(8, len(laws))]
    trend_count = sum("relation_trend" in (x.get("operators") or []) for x in top)
    if top and trend_count > len(top) / 2:
        questions.append({
            "id": "RQC-trend",
            "question": "relation_trendを使うことが、まだ説明していない『記憶装置』を暗黙に置くことになっていないか？",
            "next_test": "trendなしのholdout法則と比較し、changeの履歴差分が本当にR0から必要かを反証する。",
        })
    return questions


def audit_report(report: dict[str, Any], *, persist: bool = False) -> dict[str, Any]:
    """Rerank a completed root report after removing representation shortcuts."""
    laws = [_audit_law(dict(x)) for x in (report.get("all_laws") or [])]
    laws.sort(
        key=lambda x: (float(x.get("priority", 0.0)), -int(x.get("axiom_cost", 99)), str(x.get("id"))),
        reverse=True,
    )
    report["all_laws"] = laws
    report["top_laws"] = laws[: min(8, len(laws))]
    report["root_integrity_audit"] = {
        "version": 1,
        "permutation_quotient_enabled": True,
        "latent_slot_labels_are_physical_entities": False,
        "raw_label_graph_closure_accepted_as_emergence": False,
        "global_sign_is_physical_polarity": False,
        "step_recurrence_is_physical_frequency": False,
        "first_change_explained_beyond_R0": False,
        "first_change_status": "R0 itself is the current root axiom; the experiment does not pretend to explain why R0 holds.",
        "critic_questions": _critic_questions(laws),
        "changes_scientific_gate": False,
        "changes_official_level": False,
    }
    report["observed_not_seeded"] = [
        "relation_contrast_amplification",
        "label_free_distinction_classes",
        "permutation_quotient_closure_after_root_event",
        "counterfactual_history_dependence",
    ]
    honesty = report.setdefault("honesty", {})
    honesty["latent_slot_count_is_physical_entity_count"] = False
    honesty["complete_latent_relation_canvas_is_emergent_closed_network"] = False
    honesty["global_sign_is_physical_charge_or_polarity"] = False
    honesty["step_period_is_physical_frequency"] = False
    honesty["first_relation_change_is_explained_beyond_R0"] = False

    if persist:
        _write(_ROOT_REPORT, report)
        history = _read(_HISTORY, {"version": 1, "bursts": []})
        root_state = dict(history.get("pure_genesis_r0") or {"version": 1})
        root_state["last_burst"] = report.get("burst_id")
        root_state["integrity_version"] = 1
        root_state["top_laws"] = [
            {
                "id": x.get("id"),
                "coefficients": x.get("coefficients") or {},
                "priority": x.get("priority"),
                "status": x.get("status"),
                "root_integrity_flags": (x.get("root_integrity") or {}).get("flags") or [],
            }
            for x in report.get("top_laws") or []
        ]
        history["pure_genesis_r0"] = root_state
        _write(_HISTORY, history)
    return report
