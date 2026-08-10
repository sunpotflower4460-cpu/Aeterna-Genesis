"""Evidence cards for Adaptive Dream v7 hypothesis evolution.

This module converts heterogeneous research outputs into a small common envelope.  It never
changes physics, success thresholds, official Levels, Rooms, or source evidence.  Quarantined
or scientifically unusable evidence receives zero voting weight by construction.
"""
from __future__ import annotations

import hashlib
from typing import Any


def _eid(*parts: Any) -> str:
    raw = "|".join(str(x) for x in parts)
    return "ev7-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _usable(card: dict[str, Any]) -> bool:
    return card.get("scientific_usable") is not False and card.get("integrity_status") not in {
        "PREFIX_MISMATCH_QUARANTINED",
        "FIELD_RECONSTRUCTION_MISMATCH_QUARANTINED",
        "OBSERVATION_PREFIX_MISMATCH_QUARANTINED",
    }


def finalize(card: dict[str, Any]) -> dict[str, Any]:
    """Normalize one evidence card and enforce integrity weighting."""
    out = dict(card)
    out.setdefault("version", 1)
    out.setdefault("direction", "NEUTRAL")
    out.setdefault("scientific_usable", True)
    out.setdefault("independence", {})
    out.setdefault("start_purity", "unknown")
    out.setdefault("source_kind", "unknown")
    out["weight"] = float(out.get("weight", 1.0)) if _usable(out) else 0.0
    return out


def from_legacy_hypothesis(h: dict[str, Any], *, burst_id: str) -> list[dict[str, Any]]:
    """Create bounded aggregate cards from the existing hypothesis ledger.

    Existing support/contradiction counts may summarize many correlated observations, so they are
    deliberately represented as aggregate cards rather than pretending every count is independent.
    """
    hid = str(h.get("id") or "unknown")
    cards: list[dict[str, Any]] = []
    support = int(h.get("support", 0))
    contradiction = int(h.get("contradiction", 0))
    if support:
        cards.append(finalize({
            "evidence_id": _eid(burst_id, hid, "legacy-support", support),
            "burst_id": burst_id,
            "hypothesis_id": hid,
            "direction": "SUPPORT",
            "source_kind": "legacy-hypothesis-aggregate",
            "aggregate_count": support,
            "weight": min(1.0, 0.25 + 0.05 * support),
            "scientific_usable": True,
        }))
    if contradiction:
        cards.append(finalize({
            "evidence_id": _eid(burst_id, hid, "legacy-contradiction", contradiction),
            "burst_id": burst_id,
            "hypothesis_id": hid,
            "direction": "CONTRADICT",
            "source_kind": "legacy-hypothesis-aggregate",
            "aggregate_count": contradiction,
            "weight": min(1.0, 0.25 + 0.05 * contradiction),
            "scientific_usable": True,
        }))
    return cards


def from_unknown_followups(doc: dict[str, Any], *, burst_id: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    patterns = doc.get("patterns") or {}
    rows = patterns.values() if isinstance(patterns, dict) else patterns
    for row in rows:
        pid = str(row.get("pattern_id") or "")
        if not pid:
            continue
        exact = row.get("exact") or {}
        local = row.get("local") or {}
        contrast = row.get("contrast") or {}
        en, eh = int(exact.get("n", 0)), int(exact.get("hit", 0))
        ln, lh = int(local.get("n", 0)), int(local.get("hit", 0))
        cn, ch = int(contrast.get("n", 0)), int(contrast.get("hit", 0))
        hypothesis_id = f"xpattern:{pid}"
        if eh + lh:
            cards.append(finalize({
                "evidence_id": _eid(burst_id, pid, "reproduce", en, eh, ln, lh),
                "burst_id": burst_id,
                "hypothesis_id": hypothesis_id,
                "direction": "SUPPORT",
                "source_kind": "unknown-followup",
                "exact": {"n": en, "hit": eh},
                "nearby": {"n": ln, "hit": lh},
                "contrast": {"n": cn, "hit": ch},
                "weight": min(1.0, 0.2 + 0.12 * (eh + lh)),
                "scientific_usable": True,
            }))
        if ch:
            cards.append(finalize({
                "evidence_id": _eid(burst_id, pid, "contrast-hit", cn, ch),
                "burst_id": burst_id,
                "hypothesis_id": hypothesis_id,
                "direction": "CONTRADICT",
                "source_kind": "unknown-followup-contrast",
                "contrast": {"n": cn, "hit": ch},
                "weight": min(1.0, 0.3 + 0.15 * ch),
                "scientific_usable": True,
            }))
        if en + ln >= 4 and eh + lh == 0:
            cards.append(finalize({
                "evidence_id": _eid(burst_id, pid, "failed-reproduction", en, ln),
                "burst_id": burst_id,
                "hypothesis_id": hypothesis_id,
                "direction": "CONTRADICT",
                "source_kind": "unknown-followup-failed-reproduction",
                "weight": 0.8,
                "scientific_usable": True,
            }))
    return cards


def from_deep_time(report: dict[str, Any], *, burst_id: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    deep = report.get("deep_time_followup") or {}
    for r in deep.get("results") or []:
        audit = r.get("prefix_identity_audit") or {}
        usable = audit.get("scientific_usable") is not False
        status = str(audit.get("status") or r.get("status") or "unknown")
        lead = str(r.get("lead_id") or r.get("candidate_key") or "unknown")
        cards.append(finalize({
            "evidence_id": _eid(burst_id, lead, "deep-time", status),
            "burst_id": burst_id,
            "hypothesis_id": f"deep-time:{lead}",
            "direction": "SUPPORT" if usable else "NEUTRAL",
            "source_kind": "deep-time-integrity",
            "integrity_status": status,
            "scientific_usable": usable,
            "weight": 0.6,
        }))
    return cards


def build_cards(*, report: dict[str, Any], legacy_hypotheses: dict[str, Any], unknown_followups: dict[str, Any]) -> list[dict[str, Any]]:
    burst_id = str(report.get("burst_id") or "unknown")
    cards: list[dict[str, Any]] = []
    for h in legacy_hypotheses.get("hypotheses") or []:
        cards.extend(from_legacy_hypothesis(h, burst_id=burst_id))
    cards.extend(from_unknown_followups(unknown_followups, burst_id=burst_id))
    cards.extend(from_deep_time(report, burst_id=burst_id))
    return cards
