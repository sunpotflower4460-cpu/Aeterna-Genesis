"""Add relation-instrument results to the durable topic-diverse handoff.

The existing Research Continuity adapter already protects strict geometry, energy, X, X-mechanism,
Deep-Time, Science Bridge and operations.  This patch gives implemented relation instruments their own
small working-memory lane so a negative measurement is not forgotten or mislabelled as missing
engineering.

No source evidence or scientific status is changed. ``MEASURED`` means the instrument ran; ``LEAD`` is
only a planner candidate and never physical-space/life/division truth.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_lab.dream import research_continuity_entrypoint as continuity

_REPO = Path(__file__).resolve().parents[2]
_ROOT = _REPO / "ai_lab" / "reports" / "easy" / "root_latest.json"
_ORIGINAL_BASE_LESSONS = continuity._ORIGINAL_CURRENT_LESSONS
_ORIGINAL_BUCKET = continuity._bucket
_INSTALLED = False


def _relation_lessons() -> list[dict[str, Any]]:
    root = continuity.base._read(_ROOT, {})
    summary = root.get("relation_instrument_summary") or {}
    capabilities = summary.get("capabilities") or {}
    burst = str(root.get("burst_id") or "unknown")
    definitions = {
        "emergent_metric_geometry": (
            "metric-from-relations",
            "関係だけから得た距離・近傍・次元候補は、匿名label置換・relation rewire・holdoutを越えて残るか？",
            "物理空間・重力・基本次元とはまだ呼ばない。",
        ),
        "persistent_individual_identity": (
            "identity-continuity",
            "結果形状やnode IDを使わず追った関係構造は、time-shuffle対照より長く同一候補として持続するか？",
            "個体・自己・細胞・生命とはまだ呼ばない。",
        ),
        "division_with_inheritance": (
            "lineage-accounting",
            "持続した親候補の後に持続する2候補が現れ、親→娘の構造収支が無関係pair対照を上回るか？",
            "生物的細胞分裂・繁殖・遺伝とはまだ呼ばない。",
        ),
    }
    rows: list[dict[str, Any]] = []
    for capability_id, (instrument_id, question, boundary) in definitions.items():
        raw = capabilities.get(capability_id)
        if not isinstance(raw, dict):
            continue
        status = str(raw.get("instrument_status") or "UNMEASURED")
        if status not in {"MEASURED", "LEAD"}:
            continue
        if status == "LEAD":
            next_question = question + " fresh law/sizeと観測閾値holdoutでleadを壊しに行く。"
            priority = 77
        else:
            next_question = question + " 現在は測定可能だがleadなし。負の結果を保ち、別law/sizeで探索する。"
            priority = 66
        rows.append({
            "key": f"relation-instrument:{instrument_id}",
            "kind": "relation_instrument_measurement",
            "lane": "pure-genesis-relation-instruments",
            "importance": "carry",
            "priority": priority,
            "burst": burst,
            "snapshot": {
                "instrument_id": instrument_id,
                "capability_id": capability_id,
                "status": status,
                "question": next_question,
                "boundary": boundary,
                "measured_runs": raw.get("measured_runs"),
                "candidate_runs": raw.get("candidate_runs", raw.get("controlled_candidate_runs")),
                "candidate_sizes": raw.get("candidate_sizes"),
                "planner_lead_is_physical_truth": False,
                "counts_as_g001_strict_zero_evidence": False,
            },
            "source": "ai_lab/reports/easy/root_latest.json#relation_instrument_summary",
        })
    return rows


def _base_lessons_with_measurement_state() -> list[dict[str, Any]]:
    rows = list(_ORIGINAL_BASE_LESSONS())
    # Once an instrument is active, it is no longer engineering debt.  The actual measured result is
    # added below, including a negative/no-lead result when applicable.
    rows = [
        row for row in rows
        if not (
            row.get("kind") == "operational_or_instrument_debt"
            and str((row.get("snapshot") or {}).get("status") or "") == "MEASUREMENT_ACTIVE"
        )
    ]
    rows.extend(_relation_lessons())
    return rows


def _bucket(row: dict[str, Any]) -> str:
    if row.get("kind") == "relation_instrument_measurement" or "relation-instruments" in str(row.get("lane") or ""):
        return "relation-instruments"
    return _ORIGINAL_BUCKET(row)


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    continuity._ORIGINAL_CURRENT_LESSONS = _base_lessons_with_measurement_state
    continuity._bucket = _bucket
    continuity._BUCKET_MINIMUMS = {
        **continuity._BUCKET_MINIMUMS,
        "relation-instruments": 2,
    }
    continuity._BUCKET_CAPS = {
        **continuity._BUCKET_CAPS,
        "relation-instruments": 3,
    }
    order = list(continuity._BUCKET_ORDER)
    if "relation-instruments" not in order:
        insert_at = order.index("research-operations") if "research-operations" in order else len(order)
        order.insert(insert_at, "relation-instruments")
    continuity._BUCKET_ORDER = tuple(order)
    _INSTALLED = True
