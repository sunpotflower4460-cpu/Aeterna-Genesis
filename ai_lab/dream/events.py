"""Measured outcome -> research event classification for the Aeterna Dream Loop.

This module is intentionally model-free.  It does not decide whether physics is true and it
never changes an emergence threshold.  It only translates already-measured results into a
small event vocabulary that humans can scan quickly.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable

EVENT_KINDS = {
    "NEW_BEHAVIOR",
    "NEW_REGION",
    "REPRODUCED",
    "PROMOTION_READY",
    "STAGE_PROMOTED",
    "DIMENSION_FAILURE",
    "NEGATIVE_RESULT",
    "NUMERICAL_WARNING",
    "RARE_EVENT",
}

_MEASURE_KEYS = (
    "mean_amplitude_growth",
    "structure_factor_prominence",
    "defect_count",
)


def _clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _num(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def _knob_vector(knobs: dict[str, Any]) -> list[float]:
    """Map known search knobs to roughly comparable [0,1] coordinates.

    These coordinates are ONLY for novelty ranking.  They are not a scientific success gate.
    """
    noise = _num(knobs.get("noise_amplitude"), 1.0e-4)
    corr = _num(knobs.get("correlation_length"), 1.0)
    diff = _num(knobs.get("diffusion_ratio"), 1.0)
    drive = _num(knobs.get("drive_strength"), 0.0)
    quench = _num(knobs.get("quench_duration"), 8.0)
    return [
        _clip((math.log10(max(noise, 1.0e-8)) + 5.0) / 3.0),
        _clip((corr - 1.0) / 11.0),
        _clip((math.log10(max(diff, 1.0e-4)) + 1.0) / 2.0),
        _clip(drive / 5.0),
        _clip(quench / 40.0),
    ]


def feature_vector(record: dict[str, Any]) -> list[float]:
    """Compact behavior/search vector used only to rank how unlike history a run is."""
    mb = record.get("measured_by") or {}
    level = _num(record.get("reached_level"), 0.0)
    complexity = _num(record.get("complexity"), 0.0)
    growth = _num(mb.get("mean_amplitude_growth"), 1.0)
    prominence = _num(mb.get("structure_factor_prominence"), 0.0)
    defects = _num(mb.get("defect_count"), 0.0)
    return [
        _clip(level / 8.0),
        _clip(complexity),
        _clip(math.log10(max(growth, 1.0)) / 6.0),
        _clip(prominence / 10.0),
        _clip(defects / 20.0),
        *_knob_vector(record.get("knobs") or {}),
    ]


def _distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 1.0
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / max(1, len(a)))


def novelty_score(candidate: dict[str, Any], history: Iterable[dict[str, Any]]) -> float:
    """Nearest-neighbour novelty in [0,1], with a small IC-family distinction bonus.

    Novelty is presentation/ranking metadata only.  It never changes reached Level, audit state,
    or promotion gates.
    """
    hist = list(history)
    if not hist:
        return 1.0
    fv = feature_vector(candidate)
    family = candidate.get("family")
    nearest = 1.0
    for old in hist:
        d = _distance(fv, feature_vector(old))
        if family and old.get("family") and old.get("family") != family:
            d = min(1.0, d + 0.08)
        nearest = min(nearest, d)
    return round(_clip(nearest), 4)


def reproduction_summary(candidate: dict[str, Any], reruns: list[dict[str, Any]]) -> dict[str, Any]:
    target = int(candidate.get("reached_level") or 0)
    stable = [r for r in reruns if r.get("status") != "unstable" and r.get("reached_level") is not None]
    matched = [r for r in stable if int(r.get("reached_level") or 0) >= target]
    tested = len(reruns)
    ratio = len(matched) / tested if tested else 0.0
    return {
        "tested": tested,
        "stable": len(stable),
        "matched": len(matched),
        "ratio": round(ratio, 4),
        "target_level": target,
        "levels": [r.get("reached_level") for r in reruns],
        "seeds": [r.get("seed") for r in reruns],
    }


def _event_id(kind: str, source_key: str) -> str:
    raw = f"{kind}|{source_key}".encode("utf-8")
    return "evt-" + hashlib.sha256(raw).hexdigest()[:16]


def _event(
    kind: str,
    source_key: str,
    *,
    title: str,
    plain: str,
    why: str,
    facts: dict[str, Any],
    scientific_status: str,
    visual_interest: str = "medium",
    room_id: str | None = None,
    parent_room: str | None = None,
    source: str = "dream-search",
) -> dict[str, Any]:
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown Dream event kind: {kind}")
    return {
        "event_id": _event_id(kind, source_key),
        "kind": kind,
        "source": source,
        "source_key": source_key,
        "title": title,
        "plain": plain,
        "why": why,
        "facts": facts,
        "scientific_status": scientific_status,
        "visual_interest": visual_interest,
        "room_id": room_id,
        "parent_room": parent_room,
        "view_preset_id": None,
    }


def classify_search_candidate(
    candidate: dict[str, Any],
    *,
    parent_level: int,
    history: Iterable[dict[str, Any]],
    reruns: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Classify one expanded AI Lab search result into zero or more human-facing events."""
    key = candidate.get("key") or _search_key(candidate)
    status = candidate.get("status", "2d_screened")
    if status == "unstable" or candidate.get("score") is None:
        return [
            _event(
                "NUMERICAL_WARNING",
                key,
                title="数値的に不安定な条件を検出",
                plain="この条件では計算が安定して完走しませんでした。物理的な失敗とは数えません。",
                why="不安定計算を Level 0 と誤認しないため、探索結果から分離して記録します。",
                facts={"reason": candidate.get("reason"), "family": candidate.get("family"), "knobs": candidate.get("knobs", {})},
                scientific_status="numerical_warning",
                visual_interest="low",
            )
        ]

    level = int(candidate.get("reached_level") or 0)
    novelty = novelty_score(candidate, history)
    mb = candidate.get("measured_by") or {}
    facts = {
        "reached_level": level,
        "parent_level": int(parent_level),
        "delta_level": level - int(parent_level),
        "novelty": novelty,
        "family": candidate.get("family"),
        "knobs": candidate.get("knobs") or {},
        "seed": candidate.get("seed"),
        "measured_by": {k: mb.get(k) for k in _MEASURE_KEYS if k in mb},
    }
    events: list[dict[str, Any]] = []

    if novelty >= 0.28 and level >= parent_level:
        events.append(
            _event(
                "NEW_BEHAVIOR",
                key,
                title="過去の探索から離れた挙動を検出",
                plain=(
                    f"到達 Level L{level} のまま、過去の記録とは異なる測定パターンを示す候補が見つかりました。"
                ),
                why="新規性は過去の測定値・始原条件との距離で評価しています。成功判定そのものではありません。",
                facts=facts,
                scientific_status="2d_screened",
                visual_interest="high" if novelty >= 0.5 else "medium",
            )
        )

    if level < parent_level:
        events.append(
            _event(
                "NEGATIVE_RESULT",
                key,
                title="親Roomより浅い領域を確認",
                plain=f"この始原条件では親Roomの L{parent_level} に届かず、L{level} で止まりました。",
                why="成立しない領域も探索空間を狭める証拠として保存します。",
                facts=facts,
                scientific_status="negative_2d_result",
                visual_interest="low",
            )
        )

    if reruns:
        repro = reproduction_summary(candidate, reruns)
        repro_facts = {**facts, "reproduction": repro}
        if repro["ratio"] >= 2.0 / 3.0 and repro["tested"] >= 3:
            events.append(
                _event(
                    "REPRODUCED",
                    key,
                    title="別seedでも同じ到達Levelを再現",
                    plain=(
                        f"{repro['tested']} seed 中 {repro['matched']} seed で L{repro['target_level']} 以上を再現しました。"
                    ),
                    why="一つの初期乱数だけに依存した偶然ではない可能性が高まったため、再現候補として扱います。",
                    facts=repro_facts,
                    scientific_status="2d_reproducible",
                    visual_interest="high" if novelty >= 0.35 else "medium",
                )
            )
        elif repro["tested"] >= 3 and repro["matched"] == 0:
            events.append(
                _event(
                    "RARE_EVENT",
                    key,
                    title="単発では現れたが再現しにくい挙動",
                    plain="最初のseedでは見えた挙動が、追加seedでは同じ深さまで再現しませんでした。",
                    why="珍しい揺らぎか、狭い条件窓かを切り分ける価値があります。",
                    facts=repro_facts,
                    scientific_status="rare_2d_observation",
                    visual_interest="high",
                )
            )

    return events


def events_from_autopilot(
    discoveries: Iterable[dict[str, Any]],
    *,
    seen_job_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Translate newly completed genesis_orchestrator stages into Dream events."""
    seen = set(seen_job_ids or set())
    out: list[dict[str, Any]] = []
    for rec in discoveries:
        job_id = str(rec.get("job_id") or "")
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        stage = rec.get("stage")
        survived = bool(rec.get("survived_stage"))
        level = rec.get("reached_level")
        room_id = rec.get("result_room")
        parent_room = rec.get("parent_room")
        facts = {
            "campaign_id": rec.get("campaign_id"),
            "hypothesis_id": rec.get("hypothesis_id"),
            "trial_id": rec.get("trial_id"),
            "stage": stage,
            "seed": rec.get("seed"),
            "overrides": rec.get("overrides") or {},
            "reached_level": level,
            "min_reached_level": rec.get("min_reached_level"),
            "survived_stage": survived,
            "measured_by": rec.get("measured_by") or {},
        }
        if stage == "2d-screen" and survived:
            out.append(
                _event(
                    "NEW_REGION",
                    job_id,
                    title="2D探索を通過した始原条件",
                    plain=f"seed {rec.get('seed')} で L{level} に到達し、次元移行テストへ進みました。",
                    why="既存Autopilotの昇格規則を満たしたため、Local 3Dへ送られます。",
                    facts=facts,
                    scientific_status="2d_screened",
                    visual_interest="medium",
                    room_id=room_id,
                    parent_room=parent_room,
                    source="genesis-orchestrator",
                )
            )
        elif stage == "local-3d" and survived:
            out.append(
                _event(
                    "PROMOTION_READY",
                    job_id,
                    title="Local 3Dまで生き残った候補",
                    plain=f"2DだけでなくLocal 3Dでも L{level} に到達しました。次はcoarse 3Dの承認ゲートです。",
                    why="2D固有の見かけではない可能性が上がったため、人間が確認する価値の高い昇格候補です。",
                    facts=facts,
                    scientific_status="local_3d_passed",
                    visual_interest="high",
                    room_id=room_id,
                    parent_room=parent_room,
                    source="genesis-orchestrator",
                )
            )
        elif stage in {"local-3d", "coarse-global-3d", "full-3d"} and not survived:
            out.append(
                _event(
                    "DIMENSION_FAILURE",
                    job_id,
                    title="次元を上げると挙動が崩れた候補",
                    plain=f"{stage} では必要Levelに届かず、2D側の候補がそのまま移行しませんでした。",
                    why="2Dの見かけを3Dの物理と混同しないための重要な負の結果です。",
                    facts=facts,
                    scientific_status="rejected_in_dimension_transfer",
                    visual_interest="medium",
                    room_id=room_id,
                    parent_room=parent_room,
                    source="genesis-orchestrator",
                )
            )
        elif stage in {"coarse-global-3d", "full-3d"} and survived:
            out.append(
                _event(
                    "STAGE_PROMOTED",
                    job_id,
                    title=f"{stage} を通過",
                    plain=f"昇格パイプラインの {stage} を実測で通過しました。",
                    why="段階を飛ばさず、既存の昇格規則に従って到達した結果です。",
                    facts=facts,
                    scientific_status=f"{stage}_passed",
                    visual_interest="high",
                    room_id=room_id,
                    parent_room=parent_room,
                    source="genesis-orchestrator",
                )
            )
    return out, seen


def _search_key(rec: dict[str, Any]) -> str:
    knobs = rec.get("knobs") or {}
    packed = json.dumps(knobs, sort_keys=True, separators=(",", ":"))
    return f"{rec.get('family', 'unknown')}|{packed}|seed={rec.get('seed')}"
