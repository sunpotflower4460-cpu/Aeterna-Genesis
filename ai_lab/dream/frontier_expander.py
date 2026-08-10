"""Autonomous frontier expansion for the Pure Genesis north star.

This layer is intentionally mission-driven but evidence-conservative.  It does not define a fixed
A->B->C research loop.  Instead it inspects whatever the previous layers actually found and chooses
small, falsifiable next moves from a library of *research operations*: one-factor interventions,
operator ablations, robustness checks, boundary searches and requests for new measurement tools.

The destination is ambitious: start from R0 without target information and eventually obtain the
capabilities needed for universe-like organization, brain-like adaptive organization and seed-like
growth.  Those words are navigation goals, never seeded morphologies and never scientific claims.

Crucially, this module may steer planning but cannot:
* add unexplained physical axioms to Pure Genesis,
* seed an X-pattern, vortex, triangle, split, organism, brain or target shape,
* promote Rooms or assign official Emergence Levels,
* call a recurrent pattern a physical law,
* call relation-network fission biological cell division.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ai_lab.dream import followups
from ai_lab.dream import open_ended
from ai_lab.dream import pure_genesis
from ai_lab.dream import root_integrity
from ai_lab.dream import strict_geometry
from ai_lab.dream import why_gate

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "frontier_expansion.json"
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "frontier_latest.json"
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"

_KNOB_RANGES = {
    "noise_amplitude": (1e-6, 0.02),
    "correlation_length": (1.0, 12.0),
    "diffusion_ratio": (0.1, 8.0),
    "drive_strength": (0.1, 5.0),
    "quench_duration": (4.0, 20.0),
}
_KNOB_FACTORS = {
    "noise_amplitude": (0.60, 1.70),
    "correlation_length": (0.75, 1.30),
    "diffusion_ratio": (0.65, 1.55),
    "drive_strength": (0.75, 1.30),
    "quench_duration": (0.78, 1.28),
}


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _seed(*parts: Any) -> int:
    raw = "|".join(str(x) for x in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:12], 16) % 1_000_000_000 + 1


def _clip_knobs(knobs: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, (lo, hi) in _KNOB_RANGES.items():
        value = float(knobs.get(name, math.sqrt(lo * hi) if lo > 0 else (lo + hi) / 2.0))
        out[name] = max(lo, min(hi, value))
    return out


def _one_factor_specs(
    *, family: str, knobs: dict[str, Any], burst_id: str, source_id: str, limit: int,
) -> list[dict[str, Any]]:
    """Fresh-seed start-side interventions only; no outcome geometry is encoded."""
    base = _clip_knobs(knobs)
    specs: list[dict[str, Any]] = []
    for i in range(2):
        specs.append({
            "family": family,
            "knobs": dict(base),
            "seed": _seed(burst_id, source_id, "baseline", i),
            "intervention": "fresh-seed-baseline",
            "intervened_knob": None,
            "factor": 1.0,
            "quick": True,
        })
    for name in _KNOB_RANGES:
        for factor in _KNOB_FACTORS[name]:
            varied = dict(base)
            varied[name] = varied[name] * factor
            varied = _clip_knobs(varied)
            specs.append({
                "family": family,
                "knobs": varied,
                "seed": _seed(burst_id, source_id, name, factor),
                "intervention": "one-factor-start-side",
                "intervened_knob": name,
                "factor": factor,
                "quick": True,
            })
    return specs[: max(0, int(limit))]


def _mean(values: list[float]) -> float | None:
    vals = [float(x) for x in values if math.isfinite(float(x))]
    return None if not vals else sum(vals) / len(vals)


def _f_frontier_study(report: dict[str, Any], *, burst_id: str, budget: int) -> dict[str, Any]:
    path = report.get("zero_to_fission_path") or {}
    candidate = path.get("best_frontier_candidate") or {}
    depth = int(candidate.get("depth", -1))
    family = candidate.get("family")
    knobs = candidate.get("knobs") or {}
    if budget <= 0 or depth < 4 or not family or not knobs:
        return {"ran": False, "reason": "no-deep-frontier-or-budget", "experiments": 0}

    specs = _one_factor_specs(
        family=str(family), knobs=knobs, burst_id=burst_id,
        source_id=f"F-frontier-{candidate.get('trial_index')}", limit=budget,
    )
    rows: list[dict[str, Any]] = []
    for spec in specs:
        screened = followups._eval2d(spec)
        if screened.get("score") is None:
            rows.append({
                "intervention": spec["intervention"], "intervened_knob": spec["intervened_knob"],
                "factor": spec["factor"], "finite_screen": False, "depth": -1,
            })
            continue
        probe = strict_geometry._geometry_probe(screened)
        p = probe.get("zero_to_fission") or {}
        rows.append({
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "finite_screen": True,
            "depth": int(p.get("depth", -1)),
            "depth_code": p.get("depth_code"),
            "balance_collapse": bool(probe.get("balance_collapse_seen")),
            "pre_split_instability": bool(probe.get("pre_split_instability_candidate")),
            "network_fission_candidate": bool(probe.get("network_fission_candidate")),
            "start_purity": p.get("start_purity"),
        })

    baseline = [float(r["depth"]) for r in rows if r.get("intervened_knob") is None and r.get("depth", -1) >= 0]
    baseline_mean = _mean(baseline)
    sensitivity = []
    for name in _KNOB_RANGES:
        vals = [float(r["depth"]) for r in rows if r.get("intervened_knob") == name and r.get("depth", -1) >= 0]
        if not vals:
            continue
        m = _mean(vals)
        sensitivity.append({
            "knob": name,
            "mean_depth": None if m is None else round(m, 4),
            "delta_from_fresh_baseline": None if m is None or baseline_mean is None else round(m - baseline_mean, 4),
            "samples": len(vals),
        })
    sensitivity.sort(key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True)
    f7 = sum(bool(r.get("network_fission_candidate")) for r in rows)
    best = max((int(r.get("depth", -1)) for r in rows), default=-1)
    return {
        "ran": True,
        "source_depth": depth,
        "source_start_purity": (report.get("zero_to_fission_path") or {}).get("best_frontier_candidate", {}).get("start_purity"),
        "experiments": len(rows),
        "fresh_baseline_mean_depth": None if baseline_mean is None else round(baseline_mean, 4),
        "best_depth_seen": best,
        "relation_network_fission_candidates": f7,
        "sensitivity": sensitivity,
        "results": rows,
        "interpretation": (
            "This is a start-side sensitivity/intervention study. A knob changing F-depth supports a "
            "mechanism question inside this simulator, but does not by itself establish a fundamental "
            "physical cause or make the F-path the natural route."
        ),
        "target_geometry_seeded": False,
        "division_location_or_time_seeded": False,
        "F7_is_biological_cell_division": False,
    }


def _best_x_focus() -> tuple[str, dict[str, Any]] | None:
    doc = _read(_UNKNOWN, {"patterns": {}})
    candidates = []
    for pid, row in (doc.get("patterns") or {}).items():
        focus = row.get("search_focus") or {}
        if not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        exact = row.get("exact") or {}
        local = row.get("local") or {}
        hit = int(exact.get("hit", 0)) + int(local.get("hit", 0))
        n = int(exact.get("n", 0)) + int(local.get("n", 0))
        status_weight = {
            "REPEATED_SPECIFIC_CANDIDATE": 3,
            "VERIFYING": 2,
            "REPEATED_NONSPECIFIC": 1,
        }.get(str(row.get("status")), 0)
        candidates.append((status_weight, hit, n, str(pid), row))
    if not candidates:
        return None
    candidates.sort(reverse=True, key=lambda x: (x[0], x[1], x[2], x[3]))
    return candidates[0][3], candidates[0][4]


def _x_mechanism_study(*, burst_id: str, budget: int, max_episodes: int = 3) -> dict[str, Any]:
    selected = _best_x_focus()
    if budget <= 0 or selected is None:
        return {"ran": False, "reason": "no-recurrent-x-focus-or-budget", "experiments": 0}
    pid, row = selected
    focus = row.get("search_focus") or {}
    specs = _one_factor_specs(
        family=str(focus["family"]), knobs=focus["knobs"], burst_id=burst_id,
        source_id=pid, limit=budget,
    )
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
    baseline = [int(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") is None]
    base_rate = _mean([float(x) for x in baseline])
    sensitivity = []
    for name in _KNOB_RANGES:
        vals = [int(bool(r["same_pattern_seen"])) for r in results if r.get("intervened_knob") == name]
        if not vals:
            continue
        rate = _mean([float(x) for x in vals])
        sensitivity.append({
            "knob": name,
            "hit_rate": None if rate is None else round(rate, 4),
            "delta_from_fresh_baseline": None if rate is None or base_rate is None else round(rate - base_rate, 4),
            "samples": len(vals),
        })
    sensitivity.sort(key=lambda x: abs(float(x.get("delta_from_fresh_baseline") or 0.0)), reverse=True)
    return {
        "ran": True,
        "pattern_id": pid,
        "previous_status": row.get("status"),
        "experiments": len(results),
        "fresh_baseline_hit_rate": None if base_rate is None else round(base_rate, 4),
        "sensitivity": sensitivity,
        "results": results,
        "interpretation": (
            "Repeated X behavior is being challenged by controlled start-side parameter changes. "
            "Sensitivity can narrow a mechanism hypothesis, but recurrence or sensitivity alone is not a new physical law."
        ),
        "target_pattern_seeded": False,
        "target_shape_seeded": False,
    }


def _root_ablation_study(root_report: dict[str, Any], *, burst_id: str, budget: int) -> dict[str, Any]:
    top = (root_report.get("top_laws") or [])[:1]
    if budget <= 0 or not top:
        return {"ran": False, "reason": "no-root-law-or-budget", "experiments": 0}
    base = top[0]
    coefficients = dict(base.get("coefficients") or {})
    active = [k for k, v in coefficients.items() if abs(float(v)) > 1e-12]
    if not active:
        return {"ran": False, "reason": "root-law-has-no-active-operator", "experiments": 0}
    sizes = tuple(max(3, int(n)) for n in (root_report.get("sizes") or [8, 12, 16]))
    steps = max(8, int(root_report.get("steps") or 48))
    baseline_priority = float(base.get("priority", 0.0))
    rows = []
    for i, operator in enumerate(active[: max(0, int(budget))]):
        coeffs = dict(coefficients)
        coeffs[operator] = 0.0
        proposal = pure_genesis.law_proposal(coeffs)
        gate = why_gate.validate_proposal(proposal)
        if not gate.accepted:
            rows.append({"operator_removed": operator, "why_gate_accepted": False})
            continue
        proposal["why_gate"] = gate.as_dict()
        evaluated = pure_genesis.evaluate_law(
            proposal, sizes=sizes, steps=steps, seed=_seed(burst_id, "root-ablation", operator, i),
        )
        audited = root_integrity._audit_law(evaluated)
        p = float(audited.get("priority", 0.0))
        rows.append({
            "operator_removed": operator,
            "why_gate_accepted": True,
            "audited_priority": round(p, 6),
            "priority_change_vs_current_top": round(p - baseline_priority, 6),
            "status": audited.get("status"),
            "integrity_flags": (audited.get("root_integrity") or {}).get("flags") or [],
        })
    rows.sort(key=lambda x: float(x.get("priority_change_vs_current_top", 0.0)))
    return {
        "ran": True,
        "source_law_id": base.get("id"),
        "baseline_audited_priority": round(baseline_priority, 6),
        "experiments": len(rows),
        "ablations": rows,
        "most_needed_operator_candidate": rows[0].get("operator_removed") if rows else None,
        "interpretation": (
            "An ablation only says an operator matters for this current computational candidate after the root-integrity audit. "
            "It does not make that operator a fundamental law, and removing relation_trend is also a check against hidden memory assumptions."
        ),
        "new_physical_axiom_added": False,
    }


def _root_evidence(root_report: dict[str, Any]) -> dict[str, bool]:
    audits = [
        a for law in (root_report.get("top_laws") or [])
        for a in ((law.get("root_integrity") or {}).get("runs") or [])
    ]
    raw_runs = [r for law in (root_report.get("top_laws") or []) for r in (law.get("runs") or [])]
    return {
        "new_distinctions": any(int(a.get("new_classes_beyond_root_event", 0)) > 0 for a in audits),
        "new_quotient_closure": any(bool(a.get("new_robust_closure_after_root_event")) for a in audits),
        "history_dependence": any(float(r.get("counterfactual_history_dependence", 0.0)) >= 0.15 for r in raw_runs),
    }


def _capability_map(report: dict[str, Any], root_report: dict[str, Any]) -> list[dict[str, Any]]:
    root = _root_evidence(root_report)
    geometry = report.get("geometry_summary") or {}
    path = report.get("zero_to_fission_path") or {}
    open_summary = report.get("open_ended_emergence") or {}
    recurrent = int(open_summary.get("recurrent_unlabeled_patterns", 0)) > 0
    relation = int(geometry.get("persistent_pair_seen", 0)) > 0 or int(geometry.get("triad_local_energy_measured", 0)) > 0
    fdepth = int(path.get("deepest_contiguous_stage", -1))

    def row(cid: str, label: str, status: str, why: str, destination: str) -> dict[str, Any]:
        return {"id": cid, "label": label, "status": status, "evidence": why, "destination": destination}

    return [
        row("endogenous_distinction", "新しい区別が内側から増える", "LEAD" if root["new_distinctions"] else "OPEN",
            "permutation quotient後の新しい区別class" if root["new_distinctions"] else "まだroot監査を通った増殖証拠が弱い", "universe/brain/growth"),
        row("persistent_relation", "区別どうしが持続する関係を作る", "LEAD" if relation else "OPEN",
            "自然にできた持続関係を観測" if relation else "まだ持続関係の証拠不足", "universe/brain/growth"),
        row("unlabeled_recurrence", "名前を先に与えない反復変化", "LEAD" if recurrent else "OPEN",
            "複数seed/条件の未知遷移" if recurrent else "反復未知遷移を探索中", "universe/brain"),
        row("relational_closure", "ラベルを消しても残る閉じた関係", "LEAD" if root["new_quotient_closure"] else "OPEN",
            "root integrity後の新規closure" if root["new_quotient_closure"] else "latent canvas由来でないclosureを探索中", "universe/brain"),
        row("history_dependence", "過去の違いが後の変化に残る", "LEAD" if root["history_dependence"] else "OPEN",
            "counterfactual履歴依存の候補" if root["history_dependence"] else "記憶と呼ばず履歴依存を探索中", "brain/growth"),
        row("connected_instability", "一つの関係網のまま自発的に不安定化する", "LEAD" if fdepth >= 6 else "OPEN",
            "参照F-pathで連続F6候補" if fdepth >= 6 else "下流参照実験で未到達", "growth/reproduction-reference"),
        row("persistent_individual_identity", "まとまりが個体として自分を保つ", "UNMEASURED", "専用のidentity detectorが必要", "brain/growth"),
        row("self_repair", "壊されたあと自分で戻る", "UNMEASURED", "damage/recovery介入器が必要", "growth/brain"),
        row("growth_and_specialization", "増えながら役割分化する", "UNMEASURED", "成長・収支・分化の同時計測が必要", "growth/brain"),
        row("adaptive_prediction", "外界変化に適応し先を利用する", "UNMEASURED", "予測情報とholdout環境の検査が必要", "brain"),
        row("emergent_metric_geometry", "関係から距離や幾何が後から定義できる", "UNMEASURED", "座標を与えないmetric emergence監査が必要", "universe"),
        row("division_with_inheritance", "一個体が二つへ分かれ特徴を引き継ぐ", "UNMEASURED", "identity・収支・継承が揃うまで細胞分裂とは呼ばない", "growth/reproduction"),
    ]


def _instrument_requests(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status = {x["id"]: x["status"] for x in capabilities}
    requests = []

    def add(rid: str, question: str, purpose: str, *, scaffolded_only: bool = False) -> None:
        requests.append({
            "id": rid, "question": question, "purpose": purpose,
            "new_physical_axiom": False,
            "target_morphology_seeded": False,
            "may_use_scaffolded_analogy_lane": bool(scaffolded_only),
            "scaffolded_lane_cannot_count_as_pure_genesis_proof": bool(scaffolded_only),
        })

    if status.get("emergent_metric_geometry") != "LEAD":
        add("metric-from-relations", "座標なしの関係だけから、再現性のある距離・近傍・次元候補を後付けで定義できるか？",
            "宇宙らしい空間構造を最初から与えず検査する")
    if status.get("persistent_individual_identity") != "LEAD":
        add("identity-continuity", "構成要素が動いても同じまとまりと言える量を、結果形状を使わず定義できるか？",
            "成長・分裂・脳的まとまりの前提となる個体性を測る")
    if status.get("self_repair") != "LEAD":
        add("damage-recovery", "自然にできたまとまりを後から部分的に乱したとき、同じ統計的個性へ戻るか？",
            "自己維持を相関ではなく介入で確かめる")
    if status.get("growth_and_specialization") != "LEAD":
        add("growth-accounting", "外部から一様な供給だけを与えた補助実験で、形を指定せず成長・分化・収支が同時に起きるか？",
            "植物の種のような成長に必要な機構を切り分ける", scaffolded_only=True)
    if status.get("adaptive_prediction") != "LEAD":
        add("predictive-holdout", "繰り返し環境と未経験環境を分け、過去依存が単なる残響ではなく将来の応答改善に使われるか？",
            "脳らしい適応・予測への橋を検査する", scaffolded_only=True)
    if status.get("division_with_inheritance") != "LEAD":
        add("lineage-accounting", "持続する一個体が二つへ分かれた場合に、量の収支と特徴の継承を追えるか？",
            "関係網分離と生物的分裂を厳密に分ける")
    return requests


def _compact_human(capabilities: list[dict[str, Any]], fstudy: dict[str, Any], xstudy: dict[str, Any], rootstudy: dict[str, Any]) -> dict[str, Any]:
    leads = [x["label"] for x in capabilities if x.get("status") == "LEAD"]
    missing = [x["label"] for x in capabilities if x.get("status") in {"OPEN", "UNMEASURED"}]
    advances = []
    if fstudy.get("ran"):
        if int(fstudy.get("relation_network_fission_candidates", 0)) > 0:
            advances.append("不安定な関係網を少し揺さぶる追試の中で、持続的な関係網分離候補まで進む例が出ました。ただし生物の分裂ではありません。")
        elif fstudy.get("sensitivity"):
            advances.append("深い不安定化に届いた条件を一つずつ変え、どの条件に深さが敏感かを調べ始めました。")
    if xstudy.get("ran") and xstudy.get("sensitivity"):
        advances.append("何度も現れる名前のない変化について、単なる再現確認から一歩進み、どの条件を変えると消えやすいかを調べ始めました。")
    if rootstudy.get("ran") and rootstudy.get("ablations"):
        advances.append("最小ルートの候補法則から部品を一つずつ外し、どの部品が本当に必要そうかを監査つきで比べました。")
    if not advances:
        advances.append("今回は新しい仕組みの断定より、次の介入実験と不足している測定器を整理しました。")
    return {
        "destination": "形を先に与えず、最小の物理的出発点から宇宙・脳・種の成長に必要な働きが自力で生まれるところまで到達する。",
        "current_position": f"現在は『{ '、'.join(leads[:4]) if leads else '基礎的な区別と関係' }』に候補証拠があり、個体性・自己修復・成長・適応・継承などはまだ未到達です。",
        "advances": advances,
        "largest_gaps": missing[:5],
        "reporting_policy": "裏では多数の計算を行い、人向けには目的地に対する前進・現在地・最大の穴を中心に伝える。",
    }


def inject_planning_hypotheses(graph: dict[str, Any], expansion: dict[str, Any], *, burst_id: str) -> dict[str, Any]:
    """Turn mechanism observations into falsifiable planning nodes, never truth claims."""
    nodes = graph.setdefault("nodes", {})

    fstudy = expansion.get("f_frontier_mechanism") or {}
    if fstudy.get("ran") and fstudy.get("sensitivity"):
        top = fstudy["sensitivity"][0]
        path = expansion.get("source_path_candidate") or {}
        hid = "frontier:F-mechanism:" + str(top.get("knob"))
        nodes[hid] = {
            "id": hid,
            "origin": "autonomous-frontier-expansion",
            "statement": f"The current deep relation-instability region may be especially sensitive to {top.get('knob')}.",
            "counter_statement": "The apparent sensitivity is sampling noise or a regulator-specific effect.",
            "falsification_condition": "Fresh-seed matched interventions fail to preserve the sensitivity ranking.",
            "status": "TESTING",
            "confidence": 0.5,
            "support_weight": 0.0,
            "contradiction_weight": 0.0,
            "evidence_ids": [f"frontier:{burst_id}:F:{top.get('knob')}"],
            "goal_relevance": 0.9,
            "root_relevance": 0.45,
            "novelty": 0.75,
            "created_burst": burst_id,
            "last_updated_burst": burst_id,
            "search_focus": {
                "family": path.get("family"),
                "knobs": path.get("knobs") or {},
                "source": "F-frontier-mechanism-study",
                "target_shape_seeded": False,
            } if path.get("family") and path.get("knobs") else None,
            "causal_claim": False,
        }

    xstudy = expansion.get("x_pattern_mechanism") or {}
    if xstudy.get("ran") and xstudy.get("sensitivity"):
        top = xstudy["sensitivity"][0]
        focus = expansion.get("source_x_focus") or {}
        hid = "frontier:X-mechanism:" + str(xstudy.get("pattern_id")) + ":" + str(top.get("knob"))
        nodes[hid] = {
            "id": hid,
            "origin": "autonomous-frontier-expansion",
            "statement": f"Recurrent unlabeled transition {xstudy.get('pattern_id')} may depend on a bounded region of {top.get('knob')}.",
            "counter_statement": "The recurrence does not depend specifically on that parameter region.",
            "falsification_condition": "Fresh-seed interventions and nearby/contrast controls erase the apparent sensitivity.",
            "status": "TESTING",
            "confidence": 0.5,
            "support_weight": 0.0,
            "contradiction_weight": 0.0,
            "evidence_ids": [f"frontier:{burst_id}:X:{xstudy.get('pattern_id')}:{top.get('knob')}"],
            "goal_relevance": 0.85,
            "root_relevance": 0.35,
            "novelty": 0.85,
            "created_burst": burst_id,
            "last_updated_burst": burst_id,
            "search_focus": {
                "family": focus.get("family"),
                "knobs": focus.get("knobs") or {},
                "source_pattern_id": xstudy.get("pattern_id"),
                "source": "X-mechanism-study",
                "target_shape_seeded": False,
            } if focus.get("family") and focus.get("knobs") else None,
            "causal_claim": False,
        }

    rootstudy = expansion.get("root_operator_ablation") or {}
    if rootstudy.get("ran") and rootstudy.get("most_needed_operator_candidate"):
        op = str(rootstudy["most_needed_operator_candidate"])
        hid = "frontier:root-ablation:" + op
        nodes[hid] = {
            "id": hid,
            "origin": "autonomous-frontier-expansion",
            "statement": f"Operator {op} may be necessary for the current best R0-derived candidate under integrity audit.",
            "counter_statement": "Its apparent necessity is finite-size, normalization, or candidate-family specific.",
            "falsification_condition": "Holdout sizes, representations or simpler laws recover the same audited organization without it.",
            "status": "TESTING",
            "confidence": 0.5,
            "support_weight": 0.0,
            "contradiction_weight": 0.0,
            "evidence_ids": [f"frontier:{burst_id}:root-ablation:{op}"],
            "goal_relevance": 1.0,
            "root_relevance": 1.0,
            "novelty": 0.8,
            "created_burst": burst_id,
            "last_updated_burst": burst_id,
            "causal_claim": False,
            "fundamental_law_claim": False,
        }
    return graph


def run_frontier_expansion(
    *, report: dict[str, Any], root_report: dict[str, Any], burst_id: str,
    max_experiments: int = 24, persist: bool = True,
) -> dict[str, Any]:
    """Adapt the extra research budget to the strongest *current* uncertainties.

    Allocation is deliberately dynamic: deep F evidence gets a mechanism budget only when it exists;
    recurrent X evidence gets one only when a reconstructable focus exists; root ablations use the
    remainder.  No route is mandatory and empty lanes donate budget to the other questions.
    """
    total = max(0, int(max_experiments))
    path = report.get("zero_to_fission_path") or {}
    f_candidate = path.get("best_frontier_candidate") or {}
    x_selected = _best_x_focus()
    root_active = bool(root_report.get("top_laws"))

    eligible = []
    if int(f_candidate.get("depth", -1)) >= 4:
        eligible.append("f")
    if x_selected is not None:
        eligible.append("x")
    if root_active:
        eligible.append("root")

    budgets = {"f": 0, "x": 0, "root": 0}
    if eligible and total > 0:
        # Give the deepest current frontier first refusal, then recurrent unknowns, while always
        # reserving at least one root ablation when a root candidate exists.
        if "f" in eligible:
            budgets["f"] = min(12, max(4, total // 2))
        if "x" in eligible:
            budgets["x"] = min(10, max(4, (total - budgets["f"]) // 2 if total > budgets["f"] else 0))
        if "root" in eligible:
            active_ops = len([k for k, v in ((root_report.get("top_laws") or [{}])[0].get("coefficients") or {}).items() if abs(float(v)) > 1e-12])
            budgets["root"] = min(max(1, active_ops), max(0, total - budgets["f"] - budgets["x"]))
        used = sum(budgets.values())
        remainder = max(0, total - used)
        for lane in ("f", "x", "root"):
            if remainder <= 0 or lane not in eligible:
                continue
            cap = 14 if lane == "f" else (12 if lane == "x" else 6)
            add = min(remainder, max(0, cap - budgets[lane]))
            budgets[lane] += add
            remainder -= add

    fstudy = _f_frontier_study(report, burst_id=burst_id, budget=budgets["f"])
    xstudy = _x_mechanism_study(burst_id=burst_id, budget=budgets["x"])
    rootstudy = _root_ablation_study(root_report, burst_id=burst_id, budget=budgets["root"])
    capabilities = _capability_map(report, root_report)
    instruments = _instrument_requests(capabilities)
    x_focus = (x_selected or (None, {}))[1].get("search_focus") if x_selected else None

    expansion = {
        "version": 1,
        "mode": "autonomous-mission-driven-frontier-expansion",
        "burst_id": burst_id,
        "north_star": "R0から結果形状を与えず、宇宙・脳・種からの成長に必要な機能が自発的に成立するところまで進む。",
        "policy": {
            "destination_fixed_methods_adaptive": True,
            "hypotheses_may_be_replaced": True,
            "research_methods_may_expand": True,
            "strong_results_trigger_mechanism_interventions": True,
            "missing_capabilities_trigger_instrument_requests": True,
            "given_form_experiments_allowed_as_parallel_scaffolded_lane": True,
            "scaffolded_results_count_as_pure_genesis_proof": False,
        },
        "budget": {"requested": total, "allocated": budgets, "executed": int(fstudy.get("experiments", 0)) + int(xstudy.get("experiments", 0)) + int(rootstudy.get("experiments", 0))},
        "source_path_candidate": {
            "family": f_candidate.get("family"), "knobs": f_candidate.get("knobs") or {},
            "depth": f_candidate.get("depth"), "trial_index": f_candidate.get("trial_index"),
        },
        "source_x_focus": x_focus or {},
        "f_frontier_mechanism": fstudy,
        "x_pattern_mechanism": xstudy,
        "root_operator_ablation": rootstudy,
        "capability_map": capabilities,
        "instrument_requests": instruments,
        "human": _compact_human(capabilities, fstudy, xstudy, rootstudy),
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
        },
    }

    if persist:
        ledger = _read(_LEDGER, {"version": 1, "history": []})
        ledger["latest"] = expansion
        history = list(ledger.get("history") or [])
        history.append({
            "burst_id": burst_id,
            "budget": expansion["budget"],
            "human": expansion["human"],
            "f_best_depth": fstudy.get("best_depth_seen"),
            "fission_candidates": fstudy.get("relation_network_fission_candidates"),
            "x_pattern": xstudy.get("pattern_id"),
            "root_ablation_operator": rootstudy.get("most_needed_operator_candidate"),
        })
        ledger["history"] = history[-96:]
        _write(_LEDGER, ledger)
        _write(_REPORT, expansion)
    return expansion
