"""Durable research continuity for autonomous handoff between Aeterna experiments.

Research Memory and immutable manifests preserve detailed evidence.  Continuity is a smaller *handoff*
layer: it keeps important lessons, contradictions, unresolved questions and literature/free-lab bridges
visible even when a later burst stops mentioning them.

This file never replaces source evidence.  It stores pointers/summaries only, never changes physics,
truth gates, Rooms or official Levels, and never turns exploratory evidence into strict evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_DEEP = _REPO / "ai_lab" / "discoveries" / "deep_time_fission.json"
_FREE_LEDGER = _REPO / "ai_lab" / "discoveries" / "free_hypothesis_lab.json"
_FREE_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "free_hypothesis_latest.json"
_SCIENCE_LEDGER = _REPO / "ai_lab" / "discoveries" / "science_bridge_ledger.json"
_SCIENCE_DIRECTIONS = _REPO / "ai_lab" / "discoveries" / "science_bridge_directions.json"
_BACKLOG = _REPO / "ai_lab" / "discoveries" / "research_backlog.json"
_INDEX = _REPO / "ai_lab" / "discoveries" / "research_index.json"
_HEALTH = _REPO / "ai_lab" / "reports" / "easy" / "research_health_latest.json"
_CROSSWORLD = _REPO / "ai_lab" / "discoveries" / "cross_world_emergence.json"
_OUTPUT = _REPO / "ai_lab" / "discoveries" / "research_continuity.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "research_continuity_latest.md"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rate(node: Any) -> float | None:
    if not isinstance(node, dict):
        return None
    n = int(node.get("n", 0) or 0)
    if n <= 0:
        return None
    return int(node.get("hit", 0) or 0) / n


def _compact_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _geometry(easy: dict[str, Any]) -> dict[str, Any]:
    g = easy.get("geometry_summary")
    return g if isinstance(g, dict) else easy


def _current_lessons() -> list[dict[str, Any]]:
    easy = _read(_EASY, {})
    unknown = _read(_UNKNOWN, {"patterns": {}})
    deep = _read(_DEEP, {"leads": []})
    free_ledger = _read(_FREE_LEDGER, {"runs": []})
    free_report = _read(_FREE_REPORT, {})
    science = _read(_SCIENCE_LEDGER, {"sources": []})
    backlog = _read(_BACKLOG, {"entries": []})
    health = _read(_HEALTH, {})
    crossworld = _read(_CROSSWORLD, {})
    burst = str(easy.get("burst_id") or health.get("burst_id") or "unknown")
    lessons: list[dict[str, Any]] = []

    # Unknown recurring transitions: retain both promising specificity and useful weakening/contradiction.
    ranked_x: list[tuple[float, dict[str, Any]]] = []
    for pid, raw in (unknown.get("patterns") or {}).items():
        if not isinstance(raw, dict):
            continue
        er = _rate(raw.get("exact")); nr = _rate(raw.get("nearby")); cr = _rate(raw.get("contrast"))
        en = int((raw.get("exact") or {}).get("n", 0) or 0)
        if en <= 0:
            continue
        specificity = float(er or 0.0) - float(cr or 0.0)
        status = str(raw.get("status") or "UNKNOWN")
        bonus = 2.0 if "SPECIFIC" in status and "NONSPECIFIC" not in status else 0.0
        if status == "WEAKENED":
            bonus += 0.5
        snapshot = {
            "pattern_id": pid,
            "status": status,
            "exact": raw.get("exact"),
            "nearby": raw.get("nearby"),
            "contrast": raw.get("contrast"),
            "exact_rate": er,
            "nearby_rate": nr,
            "contrast_rate": cr,
            "search_focus": raw.get("search_focus"),
        }
        ranked_x.append((bonus + specificity + min(1.0, en / 25.0), snapshot))
    for _, snapshot in sorted(ranked_x, key=lambda x: x[0], reverse=True)[:24]:
        lessons.append({
            "key": f"x:{snapshot['pattern_id']}",
            "kind": "unknown_transition",
            "lane": "strict/open-ended-followup",
            "importance": "carry" if "SPECIFIC" in str(snapshot.get("status")) else "context",
            "burst": burst,
            "snapshot": snapshot,
            "source": "ai_lab/discoveries/unknown_followups.json",
        })

    g = _geometry(easy)
    if g:
        lessons.append({
            "key": "geometry:triangle-vs-control-separation",
            "kind": "competing_geometry_explanation",
            "lane": "strict-geometry",
            "importance": "carry",
            "burst": burst,
            "snapshot": {
                "triangle_seen": g.get("triangle_seen"),
                "triangle_split": g.get("fission_like_after_triangle"),
                "control_seen": g.get("control_seen"),
                "control_split": g.get("fission_like_after_control"),
                "triangle_rate": g.get("rate_given_triangle"),
                "control_rate": g.get("rate_given_control"),
                "triangle_excess_rate": g.get("triangle_excess_rate"),
                "triangle_required": ((easy.get("zero_to_fission_path") or {}).get("triangle_is_required")),
            },
            "source": "ai_lab/reports/easy/latest.json#geometry_summary",
        })
        lessons.append({
            "key": "energy:vertex-asymmetry-vs-geometry",
            "kind": "local_energy_competing_explanation",
            "lane": "strict-local-energy",
            "importance": "carry",
            "burst": burst,
            "snapshot": {
                "pair_relations": g.get("persistent_pair_seen"),
                "pair_only": g.get("persistent_pair_only_seen"),
                "triad_energy_relations": g.get("triad_local_energy_measured"),
                "split_asymmetry": g.get("mean_triangle_anchor_energy_asymmetry_split"),
                "no_split_asymmetry": g.get("mean_triangle_anchor_energy_asymmetry_no_split"),
                "energy_peak_preceded_geometry": g.get("energy_asymmetry_peak_preceded_geometry_collapse"),
                "energy_used_to_select_relation": ((g.get("local_energy_observation") or {}).get("energy_used_to_select_relation")),
            },
            "source": "ai_lab/reports/easy/latest.json#geometry_summary",
        })

    # Deep-Time: keep prefix-qualified/usable leads and long-lived alternatives visible.
    deep_rows = [row for row in (deep.get("leads") or []) if isinstance(row, dict)]
    def deep_score(row: dict[str, Any]) -> tuple[int, int, str]:
        usable = int(bool(row.get("scientific_usable")))
        depth = int(row.get("F_depth", row.get("long_depth", row.get("depth", 0))) or 0)
        return usable, depth, str(row.get("candidate_id") or row.get("lead_id") or "")
    for row in sorted(deep_rows, key=deep_score, reverse=True)[:20]:
        cid = str(row.get("candidate_id") or row.get("lead_id") or row.get("id") or _compact_hash(row))
        lessons.append({
            "key": f"deep:{cid}",
            "kind": "deep_time",
            "lane": "strict-deep-time",
            "importance": "carry" if row.get("scientific_usable") else "context",
            "burst": burst,
            "snapshot": {
                "candidate_id": cid,
                "seed": row.get("seed"),
                "scientific_usable": row.get("scientific_usable"),
                "prefix_identity": row.get("prefix_identity") or row.get("prefix_identity_status") or row.get("prefix_audit"),
                "F_depth": row.get("F_depth", row.get("long_depth", row.get("depth"))),
                "F_code": row.get("F_code") or row.get("long_code"),
                "horizon_tau": row.get("horizon_tau") or row.get("tau"),
                "network_fission_candidate": row.get("network_fission_candidate"),
            },
            "source": "ai_lab/discoveries/deep_time_fission.json",
        })

    # Free-lab top outcomes are preserved as mechanism questions, never promoted to strict evidence.
    latest_free_by_type: dict[str, dict[str, Any]] = {}
    for run in free_ledger.get("runs") or []:
        if not isinstance(run, dict):
            continue
        top = run.get("top") or {}
        kind = str(top.get("experiment_type") or "")
        if kind:
            latest_free_by_type[kind] = {"run": run, "top": top}
    for kind, item in latest_free_by_type.items():
        top = item["top"]
        lessons.append({
            "key": f"free:{kind}",
            "kind": "exploratory_mechanism_question",
            "lane": "free-hypothesis",
            "importance": "carry",
            "burst": burst,
            "snapshot": {
                "experiment_type": kind,
                "orientation_priority_only": top.get("orientation_priority_only"),
                "abstract_factor": top.get("abstract_factor"),
                "strict_transfer_question": top.get("strict_transfer_question"),
                "latest_free_generated_at": item["run"].get("generated_at"),
                "counts_as_strict_zero_evidence": False,
            },
            "source": "ai_lab/discoveries/free_hypothesis_lab.json",
        })
    if free_report.get("top_hypothesis_for_next_question"):
        lessons.append({
            "key": "free:latest-top-full",
            "kind": "exploratory_latest_result",
            "lane": "free-hypothesis",
            "importance": "context",
            "burst": burst,
            "snapshot": free_report.get("top_hypothesis_for_next_question"),
            "source": "ai_lab/reports/easy/free_hypothesis_latest.json",
        })

    # Literature is carried as context/provenance, never as empirical Aeterna confirmation.
    for row in (science.get("sources") or []):
        if not isinstance(row, dict) or not row.get("key"):
            continue
        if not row.get("curated") and int(row.get("cited_by_count", 0) or 0) <= 0:
            continue
        lessons.append({
            "key": f"science:{row.get('key')}",
            "kind": "external_scientific_context",
            "lane": "science-bridge",
            "importance": "carry" if row.get("curated") else "context",
            "burst": burst,
            "snapshot": {
                "source_id": row.get("source_id"),
                "title": row.get("title"),
                "doi": row.get("doi"),
                "year": row.get("year"),
                "domain": row.get("domain"),
                "mechanism": row.get("mechanism"),
                "curated": row.get("curated"),
                "cited_by_count": row.get("cited_by_count"),
                "paper_claim_is_aeterna_evidence": False,
            },
            "source": "ai_lab/discoveries/science_bridge_ledger.json",
        })

    # Active operational debt must not disappear simply because the next report omits it.
    for row in (backlog.get("entries") or []):
        if not isinstance(row, dict) or not row.get("key"):
            continue
        if row.get("status") in {"RESOLVED", "CAPABILITY_LEAD_REPORTED"}:
            continue
        lessons.append({
            "key": f"ops:{row.get('key')}",
            "kind": "operational_or_instrument_debt",
            "lane": "research-operations",
            "importance": "carry",
            "burst": burst,
            "snapshot": {
                "status": row.get("status"),
                "question": row.get("question"),
                "purpose": row.get("purpose"),
                "message": row.get("message"),
                "operational_priority_score": row.get("operational_priority_score"),
            },
            "source": "ai_lab/discoveries/research_backlog.json",
        })

    # A compact reminder that Cross-World similarities are a shadow, not equivalence.
    if crossworld:
        lessons.append({
            "key": "crossworld:shadow-semantics",
            "kind": "cross_world_integrity",
            "lane": "cross-world-shadow",
            "importance": "carry",
            "burst": burst,
            "snapshot": {
                "same_fingerprint_means_same_physics": False,
                "universality_claim": False,
                "source_mode": crossworld.get("mode"),
                "observation_count": len(crossworld.get("observations") or crossworld.get("entries") or []),
            },
            "source": "ai_lab/discoveries/cross_world_emergence.json",
        })
    return lessons


def _merge(existing: dict[str, Any], current: list[dict[str, Any]], *, now: str) -> list[dict[str, Any]]:
    old = {
        str(row.get("key")): dict(row)
        for row in (existing.get("lessons") or [])
        if isinstance(row, dict) and row.get("key")
    }
    for item in current:
        key = str(item["key"])
        prior = old.get(key, {})
        snap = item.get("snapshot")
        snap_hash = _compact_hash(snap)
        history = list(prior.get("history_tail") or [])
        if not history or history[-1].get("snapshot_hash") != snap_hash:
            history.append({
                "seen_at": now,
                "burst": item.get("burst"),
                "snapshot_hash": snap_hash,
                "snapshot": snap,
            })
        old[key] = {
            **prior,
            **item,
            "first_seen_at": prior.get("first_seen_at") or now,
            "last_seen_at": now,
            "times_seen": int(prior.get("times_seen", 0) or 0) + 1,
            "history_tail": history[-20:],
            "currently_visible": True,
        }
    current_keys = {str(row["key"]) for row in current}
    for key, row in old.items():
        if key not in current_keys:
            row["currently_visible"] = False
    return sorted(
        old.values(),
        key=lambda row: (
            row.get("importance") == "carry",
            row.get("currently_visible") is True,
            str(row.get("last_seen_at") or ""),
            str(row.get("key")),
        ),
        reverse=True,
    )


def _carry_forward(lessons: list[dict[str, Any]], science_directions: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in lessons:
        if row.get("importance") != "carry":
            continue
        snap = row.get("snapshot") or {}
        question = (
            snap.get("strict_transfer_question")
            or snap.get("question")
            or snap.get("purpose")
            or snap.get("message")
        )
        rows.append({
            "key": row.get("key"),
            "lane": row.get("lane"),
            "kind": row.get("kind"),
            "question_or_lesson": question,
            "source": row.get("source"),
            "last_seen_at": row.get("last_seen_at"),
        })
    for direction in science_directions.get("directions") or []:
        if not isinstance(direction, dict) or direction.get("enabled") is False:
            continue
        rows.append({
            "key": f"science-direction:{direction.get('id')}",
            "lane": "science-bridge/free-hypothesis",
            "kind": "literature_inspired_experiment",
            "question_or_lesson": direction.get("question"),
            "strict_transfer_question": direction.get("strict_transfer_question"),
            "source": direction.get("source_reference") or direction.get("author"),
            "counts_as_strict_zero_evidence": False,
        })
    # Keep the handoff small enough to actually be read by future agents; the complete lesson ledger remains below.
    return rows[:40]


def build(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    now = _now()
    existing = _read(_OUTPUT, {"lessons": []}) if existing is None else existing
    easy = _read(_EASY, {})
    index = _read(_INDEX, {})
    health = _read(_HEALTH, {})
    science_directions = _read(_SCIENCE_DIRECTIONS, {"directions": []})
    current = _current_lessons()
    lessons = _merge(existing, current, now=now)
    latest_index = (index.get("entries") or [])[-1] if index.get("entries") else {}
    continuity = {
        "version": 1,
        "mode": "durable-research-continuity-handoff",
        "generated_at": now,
        "latest_strict_burst": easy.get("burst_id"),
        "latest_manifest_reference": {
            "burst_id": latest_index.get("burst_id"),
            "manifest_archive": latest_index.get("manifest_archive"),
            "manifest_content_sha256": latest_index.get("manifest_content_sha256"),
            "evidence_snapshot_git_sha": latest_index.get("evidence_snapshot_git_sha"),
        },
        "infrastructure_health": {
            "healthy": health.get("healthy"),
            "strict_failure_count": health.get("strict_failure_count"),
            "warning_count": health.get("warning_count"),
        },
        "must_carry_forward": _carry_forward(lessons, science_directions),
        "lessons": lessons,
        "lesson_count": len(lessons),
        "currently_visible_count": sum(row.get("currently_visible") is True for row in lessons),
        "policy": {
            "source_evidence_remains_authoritative": True,
            "important_old_lessons_are_deleted_when_not_visible": False,
            "negative_results_are_carried_forward": True,
            "free_lab_and_science_bridge_remain_separate_from_strict": True,
            "continuity_summary_changes_scientific_truth": False,
            "continuity_summary_routes_official_levels": False,
            "continuity_summary_promotes_rooms": False,
            "future_agents_should_read_must_carry_forward_before_new_strategy": True,
        },
    }
    continuity["continuity_digest"] = _compact_hash({
        "latest_strict_burst": continuity.get("latest_strict_burst"),
        "must_carry_forward": continuity.get("must_carry_forward"),
        "lesson_keys": [row.get("key") for row in lessons],
    })
    return continuity


def render_markdown(doc: dict[str, Any]) -> str:
    lines = [
        "# Research Continuity — read before changing direction",
        "",
        f"latest strict burst: `{doc.get('latest_strict_burst')}`",
        f"continuity digest: `{doc.get('continuity_digest')}`",
        "",
        "このファイルは過去の重要点を次の研究へ渡すための handoff です。元の証拠を置き換えません。",
        "",
        "## Must carry forward",
        "",
    ]
    for row in doc.get("must_carry_forward") or []:
        question = row.get("question_or_lesson") or row.get("strict_transfer_question") or "(context retained)"
        lines.append(f"- `{row.get('key')}` [{row.get('lane')}] — {question}")
    lines += [
        "",
        "## Integrity",
        "",
        "- Free Hypothesis / Science Bridge は strict-zero evidence に混ぜない。",
        "- 反証・0/3再現・WEAKENED・長寿命だが進まない状態も捨てない。",
        "- 詳細な根拠は Research Memory / immutable manifest / Git history を参照する。",
        "",
    ]
    return "\n".join(lines)


def run(*, persist: bool = True) -> dict[str, Any]:
    doc = build()
    if persist:
        _write(_OUTPUT, doc)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_MD.write_text(render_markdown(doc), encoding="utf-8")
    return doc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Build durable research handoff without changing evidence")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc = run(persist=not args.no_record)
    print(
        f"Research Continuity: lessons={doc.get('lesson_count')} "
        f"visible={doc.get('currently_visible_count')} carry={len(doc.get('must_carry_forward') or [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
