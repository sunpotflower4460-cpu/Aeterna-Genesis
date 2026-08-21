"""Production policy adapter for Research Continuity.

The complete durable lesson ledger is intentionally allowed to grow. The compact handoff is different:
it must not let one prolific lane (for example hundreds of Deep-Time leads) hide every other important
class of evidence. This adapter guarantees representative per-lane caps while leaving the underlying
complete continuity ledger unchanged.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from typing import Any

from ai_lab.dream import research_continuity as base


_LANE_QUOTAS: dict[str, int] = {
    "research-operations": 6,
    "strict/open-ended-followup": 8,
    "strict-geometry": 2,
    "strict-local-energy": 2,
    "strict-deep-time": 6,
    "free-hypothesis": 5,
    "science-bridge": 4,
    "cross-world-shadow": 1,
}
_SCIENCE_DIRECTION_QUOTA = 6
_OTHER_LANES_QUOTA = 4
_MAX_HANDOFF = 40


def _fmt_rate(value: Any) -> str:
    if value is None:
        return "?"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _lesson_text(row: dict[str, Any]) -> str:
    snap = row.get("snapshot") or {}
    kind = str(row.get("kind") or "")
    if kind == "unknown_transition":
        return (
            f"{snap.get('pattern_id')} is {snap.get('status')}; exact/near/contrast rates="
            f"{_fmt_rate(snap.get('exact_rate'))}/{_fmt_rate(snap.get('nearby_rate'))}/"
            f"{_fmt_rate(snap.get('contrast_rate'))}. Keep specificity, weakening and non-replication."
        )
    if kind == "competing_geometry_explanation":
        return (
            f"Triangle split rate={_fmt_rate(snap.get('triangle_rate'))}, control split rate="
            f"{_fmt_rate(snap.get('control_rate'))}, excess={_fmt_rate(snap.get('triangle_excess_rate'))}; "
            f"triangle_required={snap.get('triangle_required')}. Do not make triangle a required natural route."
        )
    if kind == "local_energy_competing_explanation":
        return (
            f"Local energy: pairs={snap.get('pair_relations')} (pair-only={snap.get('pair_only')}), "
            f"triads={snap.get('triad_energy_relations')}, split/no-split vertex asymmetry="
            f"{snap.get('split_asymmetry')}/{snap.get('no_split_asymmetry')}, energy-before-geometry="
            f"{snap.get('energy_peak_preceded_geometry')}. Geometry was selected first; no causal/force/binding claim."
        )
    if kind == "deep_time":
        return (
            f"Deep-Time {snap.get('candidate_id')}: effective F-depth={snap.get('effective_F_depth')}, "
            f"prefix={snap.get('prefix_identity')}, long_lived={snap.get('long_lived')}, "
            f"transition_seen={snap.get('transition_seen')}, usable={snap.get('scientific_usable')}. "
            "Preserve same-t0/prefix semantics; lower raw depth alone is not physical regression."
        )
    if kind == "exploratory_mechanism_question":
        return str(snap.get("strict_transfer_question") or f"Retest abstract factor {snap.get('abstract_factor')} from strict zero.")
    if kind == "external_scientific_context":
        return (
            f"External science: {snap.get('title')} ({snap.get('doi')}); mechanism={snap.get('mechanism')}. "
            "Use as a map for falsifiable design, never as Aeterna evidence."
        )
    if kind == "operational_or_instrument_debt":
        return str(snap.get("question") or snap.get("purpose") or snap.get("message") or "Unresolved research instrumentation debt.")
    if kind == "cross_world_integrity":
        return "Cross-World fingerprint similarity is not identity of physics, conserved quantities, or a universality proof."
    return str(
        snap.get("strict_transfer_question")
        or snap.get("question")
        or snap.get("purpose")
        or snap.get("message")
        or "Retain this source-linked lesson before changing strategy."
    )


def _entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": row.get("key"),
        "priority": row.get("priority"),
        "lane": row.get("lane"),
        "kind": row.get("kind"),
        "question_or_lesson": _lesson_text(row),
        "source": row.get("source"),
        "last_seen_at": row.get("last_seen_at"),
    }


def balanced_carry_forward(lessons: list[dict[str, Any]], science_directions: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lessons:
        if not isinstance(row, dict) or row.get("importance") != "carry":
            continue
        buckets[str(row.get("lane") or "other")].append(row)
    for rows in buckets.values():
        rows.sort(
            key=lambda row: (
                int(row.get("priority", 0) or 0),
                str(row.get("last_seen_at") or ""),
                str(row.get("key")),
            ),
            reverse=True,
        )

    chosen: list[dict[str, Any]] = []
    chosen_keys: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        key = str(item.get("key") or "")
        if not key or key in chosen_keys or len(chosen) >= _MAX_HANDOFF:
            return
        chosen_keys.add(key)
        chosen.append(item)

    # Literature directions receive an explicit reservation before prolific simulation lanes.
    directions = [
        row for row in (science_directions.get("directions") or [])
        if isinstance(row, dict) and row.get("enabled") is not False
    ]
    for direction in directions[:_SCIENCE_DIRECTION_QUOTA]:
        add({
            "key": f"science-direction:{direction.get('id')}",
            "priority": 92,
            "lane": "science-bridge/free-hypothesis",
            "kind": "literature_inspired_experiment",
            "question_or_lesson": direction.get("question"),
            "strict_transfer_question": direction.get("strict_transfer_question"),
            "source": direction.get("source_reference") or direction.get("author"),
            "counts_as_strict_zero_evidence": False,
        })

    # Hard per-lane caps: a prolific lane may keep its best representatives but cannot consume another
    # lane's reserved attention budget. The complete lesson ledger still retains every item.
    for lane, quota in _LANE_QUOTAS.items():
        for row in buckets.get(lane, [])[:quota]:
            add(_entry(row))

    # Unknown future lanes receive a small shared reserve instead of being silently discarded.
    known = set(_LANE_QUOTAS)
    other_rows = [row for lane, rows in buckets.items() if lane not in known for row in rows]
    other_rows.sort(
        key=lambda row: (int(row.get("priority", 0) or 0), str(row.get("last_seen_at") or ""), str(row.get("key"))),
        reverse=True,
    )
    for row in other_rows[:_OTHER_LANES_QUOTA]:
        add(_entry(row))
    return chosen[:_MAX_HANDOFF]


def install_policy() -> None:
    base._carry_forward = balanced_carry_forward


def build(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    install_policy()
    return base.build(existing=existing)


def run(*, persist: bool = True) -> dict[str, Any]:
    install_policy()
    return base.run(persist=persist)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build diversity-aware durable Research Continuity handoff")
    parser.add_argument("--no-record", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc = run(persist=not args.no_record)
    lane_counts: dict[str, int] = defaultdict(int)
    for row in doc.get("must_carry_forward") or []:
        lane_counts[str(row.get("lane"))] += 1
    print(f"Balanced Research Continuity: carry={len(doc.get('must_carry_forward') or [])} lanes={dict(sorted(lane_counts.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
