"""Production entrypoint for a topic-diverse, actionable Research Continuity handoff.

The authoritative evidence remains in the underlying ledgers/manifests/Git history.  This adapter only
changes the compact ``must_carry_forward`` navigation view so a large family (currently Deep-Time) cannot
crowd every other research question out of the next autonomous scientist's working context.  It also
carries the separated X-mechanism intervention ledger forward as exploratory mechanism questions.

No evidence is deleted.  No scientific status, Room, Level, truth gate, physics law or initial condition is
changed.  Free-Hypothesis, Science-Bridge and intervened X-mechanism material remains explicitly non-strict.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ai_lab.dream import research_continuity as base

_DEFAULT_LIMIT = 40
_X_MECHANISMS = Path(__file__).resolve().parents[2] / "ai_lab" / "discoveries" / "x_mechanisms.json"
_ORIGINAL_CURRENT_LESSONS = base._current_lessons

# Reserve a small number of seats for distinct scientific questions, then fill by priority while keeping
# hard caps.  The full ``lessons`` ledger is still unbounded by these handoff caps.
_BUCKET_MINIMUMS: dict[str, int] = {
    "strict-geometry": 1,
    "strict-local-energy": 1,
    "unknown-x": 4,
    "strict-deep-time": 4,
    "free-hypothesis": 2,
    "science-bridge": 4,
    "cross-world": 1,
    "research-operations": 4,
    "other": 0,
}

_BUCKET_CAPS: dict[str, int] = {
    "strict-geometry": 2,
    "strict-local-energy": 2,
    "unknown-x": 8,
    "strict-deep-time": 6,
    "free-hypothesis": 6,
    "science-bridge": 8,
    "cross-world": 2,
    "research-operations": 8,
    "other": 6,
}

_BUCKET_ORDER = tuple(_BUCKET_MINIMUMS)


def _count(node: Any) -> str:
    if not isinstance(node, dict):
        return "?"
    hit = node.get("hit")
    n = node.get("n")
    if hit is None or n is None:
        return "?"
    return f"{hit}/{n}"


def _x_mechanism_lessons() -> list[dict[str, Any]]:
    ledger = base._read(_X_MECHANISMS, {"patterns": {}})
    easy = base._read(base._EASY, {})
    burst = str(easy.get("burst_id") or "unknown")
    rows: list[dict[str, Any]] = []
    ranked = sorted(
        (
            (int(raw.get("latest_observations", 0) or 0), str(pid), raw)
            for pid, raw in (ledger.get("patterns") or {}).items()
            if isinstance(raw, dict)
        ),
        reverse=True,
    )
    for _, pattern_id, raw in ranked[:6]:
        status = str(raw.get("status") or "UNRESOLVED")
        rows.append({
            "key": f"x-mechanism:{pattern_id}",
            "kind": "x_mechanism_dissection",
            "lane": "x-mechanism-exploratory",
            "importance": "carry",
            "priority": 78 if status != "UNRESOLVED" else 68,
            "burst": burst,
            "snapshot": {
                "pattern_id": pattern_id,
                "status": status,
                "latest_observations": raw.get("latest_observations"),
                "target_events": raw.get("target_events"),
                "unique_fresh_seed_groups": raw.get("unique_fresh_seed_groups"),
                "event_classes": raw.get("event_classes"),
                "leading_explanation": raw.get("leading_explanation"),
                "leading_sensitivity_candidate": raw.get("leading_sensitivity_candidate"),
                "next_question": raw.get("next_question"),
                "counts_as_strict_zero_evidence": False,
                "causal_claim_about_nature": False,
            },
            "source": "ai_lab/discoveries/x_mechanisms.json",
        })
    return rows


def _current_lessons_with_x() -> list[dict[str, Any]]:
    # The original function remains authoritative for all existing lanes.  X mechanism is additive only.
    rows = list(_ORIGINAL_CURRENT_LESSONS())
    existing = {str(row.get("key")) for row in rows if isinstance(row, dict)}
    rows.extend(row for row in _x_mechanism_lessons() if str(row.get("key")) not in existing)
    return rows


def _bucket(row: dict[str, Any]) -> str:
    lane = str(row.get("lane") or "")
    kind = str(row.get("kind") or "")
    if kind == "competing_geometry_explanation" or lane == "strict-geometry":
        return "strict-geometry"
    if kind == "local_energy_competing_explanation" or lane == "strict-local-energy":
        return "strict-local-energy"
    if kind in {"unknown_transition", "x_mechanism_dissection"} or "open-ended" in lane or "x-mechanism" in lane:
        return "unknown-x"
    if kind == "deep_time" or lane == "strict-deep-time":
        return "strict-deep-time"
    if "free-hypothesis" in lane and "science-bridge" not in lane:
        return "free-hypothesis"
    if kind in {"external_scientific_context", "literature_inspired_experiment"} or "science-bridge" in lane:
        return "science-bridge"
    if kind == "cross_world_integrity" or "cross-world" in lane:
        return "cross-world"
    if kind == "operational_or_instrument_debt" or lane == "research-operations":
        return "research-operations"
    return "other"


def _lesson_text(row: dict[str, Any]) -> str:
    snapshot = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
    kind = str(row.get("kind") or "")

    direct = (
        snapshot.get("strict_transfer_question")
        or snapshot.get("next_question")
        or snapshot.get("question")
        or snapshot.get("purpose")
        or snapshot.get("message")
    )
    if direct:
        return str(direct)

    if kind == "unknown_transition":
        return (
            f"{snapshot.get('pattern_id')}: status={snapshot.get('status')}; "
            f"same={_count(snapshot.get('exact'))}, nearby={_count(snapshot.get('nearby'))}, "
            f"control={_count(snapshot.get('contrast'))}. 回数だけでなく、何を変えると消えるかを追う。"
        )

    if kind == "x_mechanism_dissection":
        return (
            f"{snapshot.get('pattern_id')} の機構分解: status={snapshot.get('status')}; "
            f"explanation={snapshot.get('leading_explanation')}; sensitivity={snapshot.get('leading_sensitivity_candidate')}. "
            "介入結果はstrict-zero証拠ではなく、支持された説明もholdoutで壊し続ける。"
        )

    if kind == "competing_geometry_explanation":
        return (
            "三角形を特別扱いせず対照と比較し続ける。"
            f" triangle={snapshot.get('triangle_split')}/{snapshot.get('triangle_seen')}, "
            f"control={snapshot.get('control_split')}/{snapshot.get('control_seen')}, "
            f"triangle_required={snapshot.get('triangle_required')}."
        )

    if kind == "local_energy_competing_explanation":
        return (
            "局所エネルギーは幾何で関係を選んだ後に測る。"
            f" pairs={snapshot.get('pair_relations')}, pair-only={snapshot.get('pair_only')}, "
            f"triads={snapshot.get('triad_energy_relations')}, "
            f"split-asym={snapshot.get('split_asymmetry')}, no-split-asym={snapshot.get('no_split_asymmetry')}, "
            f"energy-before-geometry={snapshot.get('energy_peak_preceded_geometry')}. 因果・力・結合エネルギーとはまだ呼ばない。"
        )

    if kind == "deep_time":
        return (
            f"Deep-Time {snapshot.get('candidate_id')}: status={snapshot.get('status')}, "
            f"effective F={snapshot.get('effective_F_depth')}, prefix={snapshot.get('prefix_identity')}, "
            f"long-lived={snapshot.get('long_lived')}, transition={snapshot.get('transition_seen')}. "
            "同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。"
        )

    if kind == "external_scientific_context":
        mechanism = snapshot.get("mechanism") or "mechanism not summarized"
        return (
            f"既存科学の文脈: {snapshot.get('title')} — {mechanism}. "
            "論文の主張はAeternaの証拠ではなく、反証可能な実験の材料としてのみ使う。"
        )

    if kind == "cross_world_integrity":
        return "Cross-Worldの共通fingerprintは同じ物理・保存則・普遍法則を意味しない。start purityと再現性を別に監査する。"

    if kind == "exploratory_mechanism_question":
        return "Free Hypothesisの差はstrict証拠ではない。抽象的な機構質問だけをstrict-zero側へ戻して再検証する。"

    return f"{row.get('key')}: 重要な過去文脈を保持し、元証拠を確認してから次の方針を変える。"


def _candidate_rows(lessons: list[dict[str, Any]], science_directions: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lesson in lessons:
        if lesson.get("importance") != "carry":
            continue
        row = {
            "key": lesson.get("key"),
            "priority": int(lesson.get("priority", 0) or 0),
            "lane": lesson.get("lane"),
            "kind": lesson.get("kind"),
            "question_or_lesson": _lesson_text(lesson),
            "source": lesson.get("source"),
            "last_seen_at": lesson.get("last_seen_at"),
        }
        row["handoff_bucket"] = _bucket(row)
        rows.append(row)

    for direction in science_directions.get("directions") or []:
        if not isinstance(direction, dict) or direction.get("enabled") is False:
            continue
        row = {
            "key": f"science-direction:{direction.get('id')}",
            "priority": 74,
            "lane": "science-bridge/free-hypothesis",
            "kind": "literature_inspired_experiment",
            "question_or_lesson": direction.get("question") or direction.get("strict_transfer_question"),
            "strict_transfer_question": direction.get("strict_transfer_question"),
            "source": direction.get("source_reference") or direction.get("author"),
            "counts_as_strict_zero_evidence": False,
        }
        row["handoff_bucket"] = _bucket(row)
        rows.append(row)

    rows.sort(key=lambda row: (int(row.get("priority", 0) or 0), str(row.get("key"))), reverse=True)
    return rows


def diverse_carry_forward(
    lessons: list[dict[str, Any]],
    science_directions: dict[str, Any],
    *,
    limit: int = _DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Choose a compact handoff without allowing one research family to monopolize working memory."""
    limit = max(1, int(limit))
    candidates = _candidate_rows(lessons, science_directions)
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_bucket[str(row.get("handoff_bucket") or "other")].append(row)

    selected: list[dict[str, Any]] = []
    selected_keys: set[str] = set()
    counts: Counter[str] = Counter()

    def take(row: dict[str, Any], reason: str) -> bool:
        key = str(row.get("key") or "")
        bucket = str(row.get("handoff_bucket") or "other")
        if not key or key in selected_keys or len(selected) >= limit:
            return False
        if counts[bucket] >= _BUCKET_CAPS.get(bucket, _BUCKET_CAPS["other"]):
            return False
        selected_keys.add(key)
        counts[bucket] += 1
        selected.append({**row, "selection_reason": reason})
        return True

    for bucket in _BUCKET_ORDER:
        minimum = min(_BUCKET_MINIMUMS[bucket], _BUCKET_CAPS[bucket])
        for row in by_bucket.get(bucket, [])[:minimum]:
            take(row, "topic-reserved")

    for row in candidates:
        take(row, "priority-fill")
        if len(selected) >= limit:
            break

    selected.sort(
        key=lambda row: (
            int(row.get("priority", 0) or 0),
            row.get("selection_reason") == "topic-reserved",
            str(row.get("key")),
        ),
        reverse=True,
    )
    return selected


def install_selector() -> None:
    # Planning/navigation-only adapters. Source evidence and the durable full lesson ledger are untouched.
    base._current_lessons = _current_lessons_with_x
    base._carry_forward = diverse_carry_forward


def build(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    install_selector()
    doc = base.build(existing=existing)
    counts = Counter(str(row.get("handoff_bucket") or "other") for row in (doc.get("must_carry_forward") or []))
    latest_burst = doc.get("latest_strict_burst")
    manifest_burst = (doc.get("latest_manifest_reference") or {}).get("burst_id")
    if manifest_burst == latest_burst and latest_burst:
        manifest_relation = "MATCH"
    elif manifest_burst:
        manifest_relation = "OLDER_FINALIZED_MANIFEST_REFERENCE"
    else:
        manifest_relation = "NO_MANIFEST_REFERENCE"

    doc["carry_forward_selection"] = {
        "strategy": "topic-reserved-then-priority-fill-with-family-caps",
        "limit": _DEFAULT_LIMIT,
        "selected_count": len(doc.get("must_carry_forward") or []),
        "bucket_counts": dict(sorted(counts.items())),
        "bucket_minimums": dict(_BUCKET_MINIMUMS),
        "bucket_caps": dict(_BUCKET_CAPS),
        "full_lessons_remain_available": True,
    }
    doc.setdefault("latest_manifest_reference", {})["relation_to_latest_strict_burst"] = manifest_relation
    doc.setdefault("policy", {})["must_carry_forward_is_topic_diverse"] = True
    doc["policy"]["family_cap_deletes_source_lessons"] = False
    doc["policy"]["older_manifest_reference_implies_bad_physics"] = False
    doc["policy"]["x_mechanism_interventions_remain_non_strict"] = True
    doc["continuity_digest"] = base._compact_hash({
        "latest_strict_burst": doc.get("latest_strict_burst"),
        "must_carry_forward": doc.get("must_carry_forward"),
        "lesson_keys": [row.get("key") for row in (doc.get("lessons") or [])],
        "carry_forward_selection": doc.get("carry_forward_selection"),
    })
    return doc


def render_markdown(doc: dict[str, Any]) -> str:
    text = base.render_markdown(doc).rstrip()
    counts = (doc.get("carry_forward_selection") or {}).get("bucket_counts") or {}
    suffix = [
        "",
        "## Handoff coverage",
        "",
        "1つの研究系統だけでworking handoffを埋めないための表示です。全履歴は `lessons` と元ledgerに残ります。",
        "",
    ]
    for bucket, count in sorted(counts.items()):
        suffix.append(f"- `{bucket}`: {count}")
    suffix.extend([
        "",
        f"manifest relation: `{(doc.get('latest_manifest_reference') or {}).get('relation_to_latest_strict_burst')}`",
        "",
    ])
    return text + "\n" + "\n".join(suffix)


def run(*, persist: bool = True) -> dict[str, Any]:
    doc = build()
    if persist:
        base._write(base._OUTPUT, doc)
        base._REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        base._REPORT_MD.write_text(render_markdown(doc), encoding="utf-8")
    return doc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build topic-diverse durable research handoff")
    parser.add_argument("--no-record", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc = run(persist=not args.no_record)
    selection = doc.get("carry_forward_selection") or {}
    print(
        f"Research Continuity: lessons={doc.get('lesson_count')} "
        f"visible={doc.get('currently_visible_count')} carry={selection.get('selected_count')} "
        f"buckets={selection.get('bucket_counts')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
