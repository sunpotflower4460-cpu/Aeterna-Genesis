"""Deterministic Question Critic for Genesis Dream.

The Research Director already challenges parameter hypotheses.  This module challenges the framing of
the question itself: are we mistaking one human-written route for the route, treating stability as
failure to progress, or trusting a long-horizon replay whose prefix is not reproducible?

It is deliberately non-generative and non-authoritative.  It writes bounded research questions and
recommended checks; it cannot change success thresholds, official Levels, Rooms, or physics laws.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "question_critic.json"
_HYPOTHESES = _REPO / "ai_lab" / "discoveries" / "hypothesis_ledger.json"
_DEEP = _REPO / "ai_lab" / "discoveries" / "deep_time_fission.json"


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _triangle_hypothesis() -> dict[str, Any] | None:
    doc = _read(_HYPOTHESES, {"hypotheses": []})
    return next((x for x in doc.get("hypotheses") or [] if x.get("id") == "three-vortex-triangle-fission"), None)


def _dimension_hypothesis() -> dict[str, Any] | None:
    doc = _read(_HYPOTHESES, {"hypotheses": []})
    return next((x for x in doc.get("hypotheses") or [] if x.get("id") == "dimension-specific-emergence"), None)


def _stable_deep_time_exists() -> bool:
    doc = _read(_DEEP, {"leads": []})
    return any(x.get("status") == "STABLE_THROUGH_64TAU" for x in doc.get("leads") or [])


def _prefix_problems(report: dict[str, Any]) -> list[dict[str, Any]]:
    deep = report.get("deep_time_followup") or {}
    bad = []
    for result in deep.get("results") or []:
        audit = result.get("prefix_identity_audit") or {}
        if audit.get("scientific_usable") is False:
            bad.append({
                "lead_id": result.get("lead_id") or result.get("candidate_key"),
                "status": audit.get("status"),
            })
    return bad


def _build_questions(report: dict[str, Any], open_summary: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    tri = _triangle_hypothesis() or {}
    tri_conf = float(tri.get("confidence", 0.5))
    if tri.get("status") in {"UNCERTAIN", "WEAKENED"} or tri_conf < 0.5:
        questions.append({
            "id": "Q-route-is-not-the-route",
            "question": "F-pathを『自然な次段階』だと仮定していないか？",
            "why_now": (
                f"三角形→分離仮説は status={tri.get('status', 'unknown')} / confidence={tri_conf:.3f}。"
                "F-pathは参照ルートとして残し、未知遷移と同列に比較する方がよい。"
            ),
            "test": "F専用追試は小さな独立予算に限定し、Directorの主focusをF-frontierで上書きしない。",
        })
    if _stable_deep_time_exists():
        questions.append({
            "id": "Q-stability-is-a-branch",
            "question": "『次段階へ進まない』ことを失敗と呼んでいないか？",
            "why_now": "F4候補の中に64τまで崩れず残った例がある。長寿命・準安定状態そのものが別枝かもしれない。",
            "test": "崩壊率だけでなく寿命分布・長期アトラクタ候補として記録し、分裂ルートとは別に追跡する。",
        })
    recurrent = int(open_summary.get("recurrent_unlabeled_patterns", 0))
    if recurrent > 0:
        questions.append({
            "id": "Q-vocabulary-may-be-missing",
            "question": "現在の『渦・三角形・分裂』という語彙に無い変化を見落としていないか？",
            "why_now": f"既存ラベルなしで複数条件に反復する遷移fingerprintが {recurrent} 件ある。",
            "test": "反復X-patternを名前付け前のまま再試験し、どの観測量・前後状態が予測力を持つか調べる。",
        })
    bad_prefix = _prefix_problems(report)
    if bad_prefix:
        questions.append({
            "id": "Q-long-run-prefix-integrity",
            "question": "長時間runは本当に元の短時間runの続きと言えるか？",
            "why_now": f"Prefix Identity Auditで使用不可の候補が {len(bad_prefix)} 件ある。",
            "test": "一致しないDeep-Time証拠を隔離し、同じt=0入力・通常観測時刻のdigest/分類が一致してから先を解釈する。",
        })
    dim = _dimension_hypothesis() or {}
    if dim.get("status") == "WEAKENED":
        questions.append({
            "id": "Q-3d-advantage-premise",
            "question": "『3Dなら急に強く創発する』という前提に計算を寄せすぎていないか？",
            "why_now": "次元優位仮説は反復比較で弱まっている。",
            "test": "Native 3Dの最低保証は維持しつつ、3D優位を目的にしたfocusは増やさない。",
        })
    questions.append({
        "id": "Q-route-cycle-attractor",
        "question": "現象を一方向のrouteとして見るより、cycle・merge・長期安定・役割交換として見るべきケースはないか？",
        "why_now": "一本のLevel/routeだけでは、戻る・循環する・安定し続ける創発を『進まない』として潰しうる。",
        "test": "Emergence Graphで枝・ループ・自己遷移を保存し、F-pathへの適合度を成功指標にしない。",
    })
    return questions


def run_question_critic(
    *, burst_id: str, report: dict[str, Any], open_summary: dict[str, Any], director_refreshed: bool,
) -> dict[str, Any]:
    doc = _read(_LEDGER, {"version": 1, "critiques": []})
    previous = (doc.get("critiques") or [])[-1] if doc.get("critiques") else None
    if not director_refreshed and previous:
        return {
            **previous,
            "burst_id": burst_id,
            "reused_between_director_cycles": True,
            "changes_research_allocation": False,
            "changes_scientific_gate": False,
        }

    questions = _build_questions(report, open_summary)
    critique = {
        "version": 1,
        "burst_id": burst_id,
        "reused_between_director_cycles": False,
        "questions": questions,
        "posture": {
            "F_path_role": "one-known-reference-route",
            "unknown_transition_role": "first-class-research-lead-after-recurrence",
            "stability_role": "possible-branch-not-failure",
            "native3d_floor": "keep",
            "question_can_be_wrong": True,
        },
        "changes_research_allocation": False,
        "changes_scientific_gate": False,
        "changes_official_level": False,
        "can_write_new_physics_law": False,
        "note": "Question Critic produces falsifiable questions/checks only; it does not decide scientific truth.",
    }
    doc.setdefault("critiques", []).append(critique)
    doc["critiques"] = doc["critiques"][-64:]
    doc["last_burst"] = burst_id
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return critique
