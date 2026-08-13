"""Research Compass: make the live scientific frontier easy to see without deleting hard evidence.

The repository deliberately keeps detailed failures, quarantines and raw ledgers because they are part of
scientific integrity.  That is good for auditability but poor for orientation: the most important live
leads can be buried under hourly JSON and repeated negative details.

This module adds a *view*, not a new truth gate:

* ``research_compass_latest.{json,md}`` foregrounds the strongest current discoveries/progress.
* ``research_memory.json`` stores compact lessons that future agents can consult so an exact failed or
  saturated question is not proposed again merely because its details were visually de-emphasised.
* ``CURRENT_RESEARCH.md`` is a root-level live front page generated from the same evidence.

Nothing here changes physics, starts, scientific gates, Rooms, official Emergence Levels, hypothesis
confidence, Cross-World status, Prefix Identity Audit, or Local Vortex Energy selection.  The raw source
files remain authoritative and are never deleted or rewritten by this module.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_EMERGENCE = _REPO / "ai_lab" / "reports" / "emergence" / "latest.json"
_CROSSWORLD = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"
_MULTIWORLD = _REPO / "ai_lab" / "reports" / "multiworld" / "latest.json"
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_DEEP = _REPO / "ai_lab" / "discoveries" / "deep_time_fission.json"
_GOAL = _REPO / "ai_lab" / "discoveries" / "goal_progress.json"
_MEMORY = _REPO / "ai_lab" / "discoveries" / "research_memory.json"
_REPORT_JSON = _REPO / "ai_lab" / "reports" / "easy" / "research_compass_latest.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "research_compass_latest.md"
_ROOT_MD = _REPO / "CURRENT_RESEARCH.md"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _rate(hit: Any, n: Any) -> float:
    try:
        n_i = int(n or 0)
        return 0.0 if n_i <= 0 else max(0.0, min(1.0, float(hit or 0) / n_i))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def _pattern_rows(unknown: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pid, raw in (unknown.get("patterns") or {}).items():
        if not isinstance(raw, dict):
            continue
        exact = raw.get("exact") or {}
        local = raw.get("local") or {}
        contrast = raw.get("contrast") or {}
        er = _rate(exact.get("hit"), exact.get("n"))
        lr = _rate(local.get("hit"), local.get("n"))
        cr = _rate(contrast.get("hit"), contrast.get("n"))
        en = int(exact.get("n", 0) or 0)
        ln = int(local.get("n", 0) or 0)
        status = str(raw.get("status") or "")
        # This is an orientation score only. It never changes scientific status/confidence.
        separation = max(0.0, er - cr) + 0.5 * max(0.0, lr - cr)
        sample = min(1.0, math.log1p(en + ln) / math.log(32.0))
        status_bonus = {
            "REPEATED_SPECIFIC_CANDIDATE": 1.0,
            "VERIFYING": 0.25,
            "REPEATED_NONSPECIFIC": 0.05,
            "WEAKENED": -1.0,
        }.get(status, 0.0)
        rows.append({
            "pattern_id": str(pid),
            "status": status,
            "exact": {"hit": int(exact.get("hit", 0) or 0), "n": en, "rate": round(er, 6)},
            "nearby": {"hit": int(local.get("hit", 0) or 0), "n": ln, "rate": round(lr, 6)},
            "contrast": {
                "hit": int(contrast.get("hit", 0) or 0),
                "n": int(contrast.get("n", 0) or 0),
                "rate": round(cr, 6),
            },
            "family": (raw.get("search_focus") or {}).get("family"),
            "score_for_orientation_only": round(status_bonus + 1.5 * separation + 0.35 * sample, 6),
            "raw": raw,
        })
    return rows


def _specific_x_cards(unknown: dict[str, Any], *, limit: int = 4) -> list[dict[str, Any]]:
    rows = [r for r in _pattern_rows(unknown) if r["status"] == "REPEATED_SPECIFIC_CANDIDATE"]
    rows.sort(
        key=lambda r: (
            float(r["score_for_orientation_only"]),
            int(r["exact"]["hit"]),
            r["pattern_id"],
        ),
        reverse=True,
    )
    cards = []
    for row in rows[: max(0, int(limit))]:
        cards.append({
            "kind": "condition_specific_unknown_transition",
            "title": f"条件と結びつく名無し変化 {row['pattern_id']}",
            "importance": "HIGH",
            "evidence_status": "CANDIDATE",
            "plain": (
                f"同条件 {row['exact']['hit']}/{row['exact']['n']}、近い条件 "
                f"{row['nearby']['hit']}/{row['nearby']['n']}、対照 "
                f"{row['contrast']['hit']}/{row['contrast']['n']}。"
                "対照で消える傾向があるため、単なる反復回数より成立条件を絞る価値があります。"
            ),
            "start_family": row.get("family"),
            "not_claimed": ["new_physical_law", "from_nothing", "universality"],
            "source": "ai_lab/discoveries/unknown_followups.json",
        })
    return cards


def _broad_x_card(emergence: dict[str, Any], unknown: dict[str, Any]) -> dict[str, Any] | None:
    top = (emergence.get("top_recurrent") or [])[:1]
    if not top:
        return None
    row = top[0]
    pid = str(row.get("pattern_id") or "unknown")
    follow = (unknown.get("patterns") or {}).get(pid) or {}
    rep = row.get("representative") or {}
    return {
        "kind": "robust_background_transition",
        "title": f"広く繰り返す名無し変化 {pid}",
        "importance": "MEDIUM_HIGH",
        "evidence_status": "ROBUST_RECURRENT_CANDIDATE",
        "plain": (
            f"{int(row.get('observations', 0) or 0)}回、"
            f"{len(row.get('seeds') or [])}個の独立seed、{len(row.get('conditions') or [])}条件で観測。"
            "ただし広く出すぎるため、今後は回数を増やすより『何を変えると消えるか』を優先します。"
        ),
        "followup_status": follow.get("status"),
        "representative_start_purity": rep.get("zero_purity"),
        "not_claimed": ["new_physical_law", "strict_nothing_origin", "specific_mechanism"],
        "source": "ai_lab/reports/emergence/latest.json",
    }


def _crossworld_cards(cross: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in cross.get("g001_pattern_matches") or []:
        status = str(row.get("status") or "")
        if status not in {"CROSS_WORLD_ZERO_ALIGNED_LEAD", "SIGNATURE_OVERLAP_ONLY"}:
            continue
        strict = status == "CROSS_WORLD_ZERO_ALIGNED_LEAD"
        cards.append({
            "kind": "cross_world_zero_aligned" if strict else "cross_world_overlap_only",
            "title": f"別世界でも重なった変化 {row.get('g001_pattern_id')}",
            "importance": "HIGH" if strict else "MEDIUM",
            "evidence_status": status,
            "plain": (
                ("開始純度までそろえた比較で一致候補。" if strict else "共通の物差し上で変化方向が重なった候補。")
                + f" projection coverage={float(row.get('projection_coverage', 0.0)):.2f}。"
                + "別世界で似ても、同じ物理や普遍法則とはまだ言いません。"
            ),
            "matched_worlds": row.get("matched_worlds") or [],
            "matched_zero_pairs": row.get("matched_world_zero_pairs") or [],
            "g001_start_purities": row.get("g001_start_purities") or [],
            "not_claimed": ["universality", "identical_physics", "official_level"],
            "source": "ai_lab/reports/crossworld/latest.json",
        })
    return cards


def _local_energy_card(easy: dict[str, Any]) -> dict[str, Any] | None:
    geometry = easy.get("geometry_summary") or {}
    if not geometry:
        # Current easy report exposes these fields directly in some versions.
        geometry = easy
    pairs = int(geometry.get("persistent_pair_seen", 0) or 0)
    pair_only = int(geometry.get("persistent_pair_only_seen", 0) or 0)
    triads = int(geometry.get("triad_local_energy_measured", 0) or 0)
    if pairs <= 0 and triads <= 0:
        return None
    return {
        "kind": "local_vortex_energy_dataset",
        "title": "2渦・3渦の局所エネルギー地図が蓄積",
        "importance": "MEDIUM_HIGH",
        "evidence_status": "MEASURED_SHADOW",
        "plain": (
            f"持続2渦 {pairs}件（pair-only {pair_only}件）、3渦の局所エネルギー {triads}件。"
            "形だけで関係を選んだ後にエネルギーを測っています。"
        ),
        "pair_charge_patterns": geometry.get("pair_charge_patterns_measured") or {},
        "triad_charge_patterns": geometry.get("triad_charge_patterns_measured") or {},
        "triangle_vertex_asymmetry_split": geometry.get("mean_triangle_anchor_energy_asymmetry_split"),
        "triangle_vertex_asymmetry_no_split": geometry.get("mean_triangle_anchor_energy_asymmetry_no_split"),
        "energy_peak_before_geometry_collapse": int(
            geometry.get("energy_asymmetry_peak_preceded_geometry_collapse", 0) or 0
        ),
        "not_claimed": ["binding_energy", "effective_force", "causal_mechanism"],
        "source": "ai_lab/reports/easy/latest.json",
    }


def _usable_history_rows(lead: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        h for h in (lead.get("history") or [])
        if isinstance(h, dict) and h.get("scientific_usable") is not False and h.get("finite") is not False
    ]


def _deep_cards(deep: dict[str, Any], burst_id: str) -> list[dict[str, Any]]:
    leads = [x for x in (deep.get("leads") or []) if isinstance(x, dict)]
    cards: list[dict[str, Any]] = []
    stable = [x for x in leads if str(x.get("status") or "").startswith("STABLE_THROUGH_")]
    if stable:
        best = max(stable, key=lambda x: float(x.get("last_rung", 0.0) or 0.0))
        cards.append({
            "kind": "deep_time_long_lived",
            "title": "長時間でも残る関係状態",
            "importance": "MEDIUM_HIGH",
            "evidence_status": str(best.get("status")),
            "plain": (
                f"参照F-path上のF{int(best.get('baseline_F_depth', -1))}候補が "
                f"{float(best.get('last_rung', 0.0)):g}τまで残っています。"
                "先へ進まないことを失敗とせず、長寿命状態として別に保持します。"
            ),
            "not_claimed": ["natural_route", "official_level", "biological_division"],
            "source": "ai_lab/discoveries/deep_time_fission.json",
        })
    current_audited = []
    for lead in leads:
        if str(lead.get("last_burst") or "") != str(burst_id):
            continue
        if str(lead.get("prefix_identity_status") or "") != "MATCH":
            continue
        rows = _usable_history_rows(lead)
        if rows:
            current_audited.append((lead, rows[-1]))
    if current_audited:
        lead, row = max(current_audited, key=lambda pair: int(pair[1].get("F_depth", -1) or -1))
        cards.append({
            "kind": "deep_time_prefix_audited",
            "title": "同じ歴史を保った長時間追跡を確認",
            "importance": "MEDIUM",
            "evidence_status": "PREFIX_MATCH",
            "plain": (
                f"最新burstでPrefix Identity=MATCHの長時間追跡があり、raw F-depthは "
                f"F{int(row.get('F_depth', -1) or -1)}。履歴不一致を長時間結果として混ぜていません。"
            ),
            "lead_id": lead.get("lead_id"),
            "not_claimed": ["physical_regression_from_lower_raw_depth", "natural_route"],
            "source": "ai_lab/discoveries/deep_time_fission.json",
        })
    return cards


def _memory_candidates(unknown: dict[str, Any], deep: dict[str, Any], emergence: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for pid, row in (unknown.get("patterns") or {}).items():
        status = str((row or {}).get("status") or "")
        if status == "WEAKENED":
            entries.append({
                "key": f"x-weakened:{pid}",
                "kind": "weakened_x",
                "human_short": "同じ条件をそのまま再確認する優先度は低い",
                "avoid_exact_repeat": True,
                "reopen_when": "開始family・観測量・独立手法のどれかが実質的に変わった時",
                "source": "ai_lab/discoveries/unknown_followups.json",
            })
    top = (emergence.get("top_recurrent") or [])[:1]
    if top:
        pid = str(top[0].get("pattern_id") or "")
        if pid:
            entries.append({
                "key": f"x-saturated-background:{pid}",
                "kind": "saturated_background_x",
                "human_short": "反復回数だけを増やす実験は優先しない",
                "avoid_exact_repeat": True,
                "reopen_when": "新しいcontrast・境界・機構介入を試す時",
                "source": "ai_lab/reports/emergence/latest.json",
            })
    for lead in deep.get("leads") or []:
        for h in (lead or {}).get("history") or []:
            if h.get("scientific_usable") is False or h.get("legacy_semantics_unverified"):
                entries.append({
                    "key": f"deep-quarantine:{lead.get('lead_id')}",
                    "kind": "deep_time_quarantine",
                    "human_short": "古い生の深さ低下を物理的後退として再利用しない",
                    "avoid_exact_repeat": False,
                    "interpretation_block": "raw lower F-depth != physical regression without prefix/history semantics audit",
                    "reopen_when": "Prefix Identity と歴史的分類意味の再監査が通った時",
                    "source": "ai_lab/discoveries/deep_time_fission.json",
                })
                break
    return entries


_GLOBAL_LESSONS = [
    {
        "key": "integrity:recurrence-not-law",
        "kind": "integrity_rule",
        "human_short": "反復回数だけで新しい物理法則とは呼ばない",
        "avoid_exact_repeat": False,
        "reopen_when": "独立した機構・摂動・整合性証拠が増えた時",
    },
    {
        "key": "integrity:scaffolded-not-nothing",
        "kind": "integrity_rule",
        "human_short": "scaffolded/correlated startを『無から』と呼ばない",
        "avoid_exact_repeat": False,
        "reopen_when": "actual strict start purity が確認された時",
    },
    {
        "key": "integrity:local-energy-not-force",
        "kind": "integrity_rule",
        "human_short": "局所GLエネルギー差を力・結合エネルギー・原因と呼ばない",
        "avoid_exact_repeat": False,
        "reopen_when": "別の摂動・integrity studyで因果が確立した時",
    },
    {
        "key": "integrity:nonfinite-not-negative-physics",
        "kind": "integrity_rule",
        "human_short": "数値非有限を物理的な負の結果として閉じない",
        "avoid_exact_repeat": False,
        "reopen_when": "数値安定性を直して再試験できる時",
    },
    {
        "key": "integrity:deep-raw-regression-needs-audit",
        "kind": "integrity_rule",
        "human_short": "長時間の生F-depth低下を監査なしで物理的退化と読まない",
        "avoid_exact_repeat": False,
        "reopen_when": "Prefix Identity / historical semantics audit が通った時",
    },
]


def _merge_memory(existing: dict[str, Any], incoming: list[dict[str, Any]], *, burst_id: str, now: str) -> dict[str, Any]:
    """Merge Compass lessons without downgrading metadata written by other research layers.

    Progress Ratchet writes durable ``progress_question`` entries plus schema/policy metadata before
    Research Compass runs in production. Compass must preserve those fields instead of resetting the
    memory document to its original v1 view schema.
    """
    old_by_key = {
        str(row.get("key")): dict(row)
        for row in (existing.get("entries") or [])
        if isinstance(row, dict) and row.get("key")
    }
    for raw in [*_GLOBAL_LESSONS, *incoming]:
        row = dict(raw)
        key = str(row["key"])
        old = old_by_key.get(key, {})
        merged = {**old, **row}
        merged["first_seen_burst"] = old.get("first_seen_burst") or burst_id
        merged["last_seen_burst"] = burst_id
        merged["first_seen_at"] = old.get("first_seen_at") or now
        merged["last_seen_at"] = now
        merged["times_seen"] = int(old.get("times_seen", 0) or 0) + 1
        old_by_key[key] = merged
    entries = list(old_by_key.values())
    entries.sort(key=lambda r: (str(r.get("kind")), str(r.get("key"))))

    counts = dict(existing.get("counts") or {})
    counts.update({
        "total": len(entries),
        "avoid_exact_repeat": sum(bool(x.get("avoid_exact_repeat")) for x in entries),
        "weakened_x": sum(x.get("kind") == "weakened_x" for x in entries),
        "deep_time_quarantine": sum(x.get("kind") == "deep_time_quarantine" for x in entries),
        "integrity_rules": sum(x.get("kind") == "integrity_rule" for x in entries),
        "progress_questions": sum(x.get("kind") == "progress_question" for x in entries),
    })
    policy = dict(existing.get("policy") or {})
    policy.update({
        "raw_evidence_deleted": False,
        "failure_details_hidden_from_machine_memory": False,
        "human_front_page_keeps_failure_details_light": True,
        "memory_changes_scientific_truth": False,
        "memory_changes_official_levels": False,
    })
    if counts["progress_questions"] > 0:
        # Keep the ratchet's durable-memory contract explicit even if an older Compass write had
        # already stripped these metadata fields. The entries themselves are authoritative evidence.
        policy["progress_ratchet_reads_memory"] = True
        policy["progress_question_history_is_durable"] = True

    return {
        "version": max(2, int(existing.get("version", 1) or 1)),
        "purpose": existing.get("purpose") or "compact-do-not-repeat-and-interpretation-memory",
        "last_burst": burst_id,
        "updated_at": now,
        "entries": entries,
        "counts": counts,
        "policy": policy,
    }


def _failure_digest(memory: dict[str, Any]) -> dict[str, Any]:
    c = memory.get("counts") or {}
    return {
        "title": "同じことを繰り返さないための内部メモ",
        "plain": (
            f"再現が弱かったX候補 {int(c.get('weakened_x', 0) or 0)}件、"
            f"Deep-Time隔離メモ {int(c.get('deep_time_quarantine', 0) or 0)}件などを機械向けに保持。"
            "人向け画面では失敗詳細を広げませんが、証拠は削除しません。"
        ),
        "avoid_exact_repeat_entries": int(c.get("avoid_exact_repeat", 0) or 0),
        "details": "ai_lab/discoveries/research_memory.json",
    }


def build_compass(*, now: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    now = now or datetime.now(timezone.utc).isoformat()
    easy = _read(_EASY, {})
    emergence = _read(_EMERGENCE, {})
    cross = _read(_CROSSWORLD, {})
    multi = _read(_MULTIWORLD, {})
    unknown = _read(_UNKNOWN, {"patterns": {}})
    deep = _read(_DEEP, {"leads": []})
    goal = _read(_GOAL, {})
    burst_id = str(easy.get("burst_id") or emergence.get("burst_id") or deep.get("last_burst") or "unknown-burst")

    existing_memory = _read(_MEMORY, {"entries": []})
    memory = _merge_memory(
        existing_memory,
        _memory_candidates(unknown, deep, emergence),
        burst_id=burst_id,
        now=now,
    )

    important: list[dict[str, Any]] = []
    important.extend(_specific_x_cards(unknown, limit=3))
    broad = _broad_x_card(emergence, unknown)
    if broad:
        important.append(broad)
    important.extend(_crossworld_cards(cross)[:2])
    energy = _local_energy_card(easy)
    if energy:
        important.append(energy)
    important.extend(_deep_cards(deep, burst_id))

    # Fixed display ordering: condition-specific leads first, then cross-world, broad background,
    # measured energy, deep-time.  Importance is a reading aid, never a scientific confidence score.
    order = {
        "condition_specific_unknown_transition": 0,
        "cross_world_zero_aligned": 1,
        "cross_world_overlap_only": 2,
        "robust_background_transition": 3,
        "local_vortex_energy_dataset": 4,
        "deep_time_prefix_audited": 5,
        "deep_time_long_lived": 6,
    }
    important.sort(key=lambda x: order.get(str(x.get("kind")), 99))

    human = easy.get("human_summary") or {}
    advances = [str(x) for x in (human.get("achieved_this_time") or []) if x][:4]
    if not advances:
        advances = [
            "名無しの反復変化を、回数ではなく同条件・近傍・対照で切り分けています。",
            "長時間追跡ではPrefix Identityを使い、別の歴史を同じrunとして混ぜないようにしています。",
        ]

    specific = _specific_x_cards(unknown, limit=1)
    next_questions: list[str] = []
    if specific:
        next_questions.append(
            f"{specific[0]['title']}について、同じ再現確認より『どの条件を変えると消えるか』の境界を優先する。"
        )
    if int(cross.get("strict_zero_aligned_matches", 0) or 0) > 0:
        next_questions.append("現在のCross-World strict候補をfresh seedで独立追試し、出たり消えたりする成立条件を絞る。")
    recurrent_x_count = int(emergence.get("recurrent_unlabeled_patterns", 0) or 0)
    if recurrent_x_count <= 0:
        recurrent_x_count = len(unknown.get("patterns") or {})
    x_scope = f"{recurrent_x_count}種類規模の" if recurrent_x_count > 0 else "多数の"
    next_questions.extend([
        f"F-pathだけを追わず、{x_scope}名無し反復から条件特異的なものを優先して壊す。",
        "個体性・自己修復・成長・適応・継承は、形を置かずに測れる専用instrumentから整える。",
    ])

    compass = {
        "version": 1,
        "mode": "human-first-research-compass",
        "burst_id": burst_id,
        "generated_at": now,
        "headline": (
            important[0]["title"] if important else "大きな新規主張より、研究の成立条件を整理している段階"
        ),
        "current_position": str(human.get("current_position") or (
            "名無しの反復変化と履歴依存の候補を絞りつつ、個体性・自己修復・成長・適応・継承は未到達です。"
        )),
        "important_discoveries": important[:8],
        "progress_this_burst": advances,
        "highest_value_next_questions": next_questions[:4],
        "learned_avoidance": _failure_digest(memory),
        "strict_goal_snapshot": {
            "goal_reached": bool(goal.get("goal_reached")),
            "required_satisfied": int(goal.get("required_satisfied", 0) or 0),
            "required_total": int(goal.get("required_total", 0) or 0),
            "display_policy": "kept_compact_on_front_page; full checklist remains in goal_progress.json",
        },
        "multiworld_shadow": {
            "mode": multi.get("mode"),
            "official_level_effect": False,
            "promotion_effect": False,
        },
        "integrity": {
            "raw_failures_deleted": False,
            "negative_evidence_cherry_picked_away": False,
            "display_priority_changes_truth": False,
            "recurrent_x_is_physical_law_claim": False,
            "crossworld_is_universality_claim": False,
            "local_energy_is_force_or_binding_claim": False,
            "F_path_is_assumed_natural_route": False,
            "F_path_is_official_emergence_level": False,
            "network_separation_is_biological_division_claim": False,
            "q_tensor_is_spacetime_or_gravity_claim": False,
        },
        "authoritative_sources": [
            "ai_lab/reports/easy/latest.json",
            "ai_lab/reports/emergence/latest.json",
            "ai_lab/reports/crossworld/latest.json",
            "ai_lab/reports/multiworld/latest.json",
            "ai_lab/discoveries/unknown_followups.json",
            "ai_lab/discoveries/deep_time_fission.json",
            "ai_lab/discoveries/research_memory.json",
        ],
    }
    return compass, memory


def render_markdown(compass: dict[str, Any]) -> str:
    lines = [
        "# 🧭 Aeterna Research Compass",
        "",
        f"**いま一番見るべきもの：{compass.get('headline', '')}**",
        "",
        "このページは、証拠を削らずに **大事な発見と前進を先に見せる** ための入口です。",
        "失敗・隔離・弱い候補の詳細は機械向け記録に残し、ここでは同じことを繰り返さないための短い教訓だけ表示します。",
        "",
        "## 🌱 現在地",
        "",
        str(compass.get("current_position") or ""),
        "",
        "## ⭐ 大事な発見・進展",
        "",
    ]
    for i, card in enumerate(compass.get("important_discoveries") or [], 1):
        lines.extend([
            f"### {i}. {card.get('title', '')}",
            "",
            str(card.get("plain") or ""),
            "",
            f"- 証拠の位置づけ: **{card.get('evidence_status', 'CANDIDATE')}**",
            f"- 元データ: `{card.get('source', '')}`",
            "",
        ])
    lines.extend(["## ✅ 今回ちゃんと進んだこと", ""])
    for item in compass.get("progress_this_burst") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## 🎯 次にやる価値が高いこと", ""])
    for item in compass.get("highest_value_next_questions") or []:
        lines.append(f"- {item}")
    learned = compass.get("learned_avoidance") or {}
    lines.extend([
        "",
        "## 🧠 同じことを繰り返さないための記憶",
        "",
        str(learned.get("plain") or ""),
        "",
        f"詳細は `{learned.get('details', 'ai_lab/discoveries/research_memory.json')}` に残しています。",
        "",
        "## 🔒 読み方の約束",
        "",
        "- 繰り返したXは、それだけで新しい物理法則ではありません。",
        "- scaffolded / correlated start を『完全な無から』とは呼びません。",
        "- Cross-World一致は普遍性や同一物理の証明ではありません。",
        "- 局所GLエネルギー差を、力・結合エネルギー・原因とは呼びません。",
        "- F0–F7は人間が書いた参照ルートの一本で、公式Emergence Levelではありません。",
        "- 関係網の分離を、生物の細胞分裂とは呼びません。",
        "- Q-tensorはnematic orderの記述であり、時空や重力ではありません。",
        "",
        "---",
        "**生の証拠は削除していません。** このページは『何が重要か』を見やすくする表示レイヤーです。",
        "",
    ])
    return "\n".join(lines)


def run(*, persist: bool = True) -> dict[str, Any]:
    compass, memory = build_compass()
    if persist:
        markdown = render_markdown(compass)
        _write_json(_MEMORY, memory)
        _write_json(_REPORT_JSON, compass)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(markdown)
        _ROOT_MD.write_text(markdown)
    return compass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build the Aeterna Research Compass and compact no-repeat memory")
    p.add_argument("--no-record", action="store_true", help="build only; do not write files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    compass = run(persist=not args.no_record)
    print(f"Research Compass: {compass.get('burst_id')} — {compass.get('headline')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
