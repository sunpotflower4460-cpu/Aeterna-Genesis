"""Bounded follow-up lane for the deepest 0->fission frontier candidates.

This lane is additive to mass discovery and the general Promising Lead engine.  It never seeds a
triangle or a split.  It merely re-runs start conditions that already advanced naturally and asks:
  - exact: does the same start region advance again with fresh randomness?
  - local: does the path survive small nearby start-condition changes?
  - contrast: does a deliberately different condition advance just as often?

The path result is observation metadata, not an official Emergence Level or scientific promotion.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ai_lab.dream import followups
from ai_lab.dream import strict_geometry

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "fission_path_leads.json"
_ACTIVE = {"OPEN", "VERIFYING", "REPEATED_PATH", "REPEATED_NONSPECIFIC"}


def _load() -> dict[str, Any]:
    if _LEDGER.exists():
        try:
            return json.loads(_LEDGER.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "version": 1,
        "note": "0->fission research guidance only; no official Level or promotion effect.",
        "leads": [],
    }


def _save(doc: dict[str, Any]) -> None:
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(doc, indent=2, ensure_ascii=False))


def _key(family: str, knobs: dict[str, Any]) -> str:
    n = max(float(knobs.get("noise_amplitude", 1e-3)), 1e-12)
    d = max(float(knobs.get("diffusion_ratio", 1.0)), 1e-12)
    raw = "|".join([
        family,
        f"n{round(math.log10(n), 1)}",
        f"c{round(float(knobs.get('correlation_length', 1.0)), 1)}",
        f"d{round(math.log10(d), 1)}",
        f"r{round(float(knobs.get('drive_strength', 1.0)), 1)}",
        f"q{round(float(knobs.get('quench_duration', 8.0)), 1)}",
    ])
    return raw


def _lead_id(key: str) -> str:
    return "fpath-" + hashlib.sha256(key.encode()).hexdigest()[:12]


def _bucket() -> dict[str, int]:
    return {"n": 0, "matched": 0}


def register_frontier(doc: dict[str, Any], *, burst_id: str, path_summary: dict[str, Any]) -> dict[str, int]:
    added = 0
    candidates = path_summary.get("frontier_candidates") or []
    for candidate in candidates:
        depth = int(candidate.get("depth", -1))
        # Stages 0-3 are already common enough to remain part of broad search. Intensive path follow-up
        # begins only when a persistent triangle (stage 4) or deeper transition appeared naturally.
        if depth < 4:
            continue
        family = candidate.get("family")
        knobs = candidate.get("knobs") or {}
        if not family or not isinstance(knobs, dict) or not knobs:
            continue
        key = _key(str(family), knobs)
        old = next((x for x in doc.setdefault("leads", []) if x.get("key") == key), None)
        if old is None:
            doc["leads"].append({
                "lead_id": _lead_id(key),
                "key": key,
                "family": family,
                "knobs": dict(knobs),
                "source_seed": candidate.get("seed"),
                "baseline_depth": depth,
                "first_burst": burst_id,
                "last_seen_burst": burst_id,
                "status": "OPEN",
                "priority": 1.0 + 0.15 * max(0, depth - 3),
                "times_selected": 0,
                "evidence": {
                    "exact": _bucket(), "local": _bucket(), "contrast": _bucket(),
                    "balance_collapse": 0,
                    "network_fission": 0,
                    "max_depth": depth,
                },
                "honesty": {
                    "triangle_seeded": False,
                    "division_seeded": False,
                    "official_level_changed": False,
                    "broad_exploration_reduced": False,
                },
            })
            added += 1
        else:
            old["last_seen_burst"] = burst_id
            old["baseline_depth"] = max(int(old.get("baseline_depth", -1)), depth)
            old["priority"] = min(2.5, float(old.get("priority", 1.0)) + 0.20)
            old["evidence"]["max_depth"] = max(int(old["evidence"].get("max_depth", -1)), depth)
            if old.get("status") == "WEAKENED":
                old["status"] = "VERIFYING"
    doc["last_registered_burst"] = burst_id
    _save(doc)
    return {"added": added, "total": len(doc.get("leads") or [])}


def _rate(b: dict[str, Any]) -> float | None:
    n = int(b.get("n", 0))
    return None if n <= 0 else round(int(b.get("matched", 0)) / n, 4)


def _status(lead: dict[str, Any]) -> str:
    ev = lead["evidence"]
    en, ln = int(ev["exact"]["n"]), int(ev["local"]["n"])
    er, lr = _rate(ev["exact"]) or 0.0, _rate(ev["local"]) or 0.0
    cr = _rate(ev["contrast"])
    if en >= 8 and int(ev["exact"]["matched"]) == 0:
        return "WEAKENED"
    if en >= 8 and ln >= 8 and er >= 0.35 and lr >= 0.20:
        # Reproduction with similarly high contrast success means the original region is probably not
        # specific; that is still useful evidence, but it should trigger widening rather than causal belief.
        if cr is not None and int(ev["contrast"]["n"]) >= 4 and cr >= max(0.25, 0.8 * lr):
            return "REPEATED_NONSPECIFIC"
        return "REPEATED_PATH"
    return "VERIFYING"


def run_followups(
    doc: dict[str, Any], *, burst_id: str, master_seed: int, workers: int,
    trials_2d: int = 24, max_leads: int = 2,
) -> dict[str, Any]:
    leads = [x for x in doc.get("leads", []) if x.get("status") in _ACTIVE]
    leads.sort(key=lambda x: (float(x.get("priority", 1.0)), -int(x.get("times_selected", 0))), reverse=True)
    chosen = leads[:max(0, int(max_leads))]
    if not chosen or trials_2d <= 0:
        return {
            "active_leads": len(leads), "selected_leads": 0, "trials_2d": 0,
            "geometry_replays": 0, "strengthened": 0, "weakened": 0, "leads": [],
        }

    per = max(1, int(trials_2d) // len(chosen))
    summaries: list[dict[str, Any]] = []
    total = strengthened = weakened = 0
    for lead in chosen:
        before = str(lead.get("status", "OPEN"))
        specs = followups._variant_specs(lead, per, master_seed=master_seed ^ 0xF15510)
        screened = followups._run_map(followups._eval2d, specs, workers)
        payload = [{**r, "quick": True} for r in screened if r.get("score") is not None]
        probes = followups._run_map(strict_geometry._geometry_probe, payload, workers)
        total += len(probes)
        baseline = int(lead.get("baseline_depth", 4))
        ev = lead["evidence"]
        by_signature = {
            (str(p.get("family")), int(p.get("seed"))): p for p in probes
        }
        for spec in screened:
            lane = str(spec.get("followup_lane"))
            bucket = ev[lane]
            bucket["n"] += 1
            probe = by_signature.get((str(spec.get("family")), int(spec.get("seed"))))
            if not probe:
                continue
            path = probe.get("zero_to_fission") or {}
            depth = int(path.get("depth", -1))
            ev["max_depth"] = max(int(ev.get("max_depth", -1)), depth)
            if depth >= baseline:
                bucket["matched"] += 1
            ev["balance_collapse"] += int(bool(probe.get("balance_collapse_seen")))
            ev["network_fission"] += int(bool(probe.get("network_fission_candidate")))

        lead["times_selected"] = int(lead.get("times_selected", 0)) + 1
        lead["last_followup_burst"] = burst_id
        lead["priority"] = max(0.25, float(lead.get("priority", 1.0)) * 0.90)
        lead["status"] = _status(lead)
        after = lead["status"]
        if after in {"REPEATED_PATH", "REPEATED_NONSPECIFIC"} and before not in {"REPEATED_PATH", "REPEATED_NONSPECIFIC"}:
            strengthened += 1
        if after == "WEAKENED" and before != "WEAKENED":
            weakened += 1
        summaries.append({
            "lead_id": lead["lead_id"],
            "family": lead["family"],
            "baseline_depth": baseline,
            "status": after,
            "exact_rate": _rate(ev["exact"]),
            "local_rate": _rate(ev["local"]),
            "contrast_rate": _rate(ev["contrast"]),
            "max_depth_seen": int(ev.get("max_depth", -1)),
            "balance_collapse_seen": int(ev.get("balance_collapse", 0)),
            "network_fission_seen": int(ev.get("network_fission", 0)),
        })

    doc["last_followup_burst"] = burst_id
    _save(doc)
    return {
        "active_leads": len(leads),
        "selected_leads": len(chosen),
        "trials_2d": sum(per for _ in chosen),
        "geometry_replays": total,
        "strengthened": strengthened,
        "weakened": weakened,
        "leads": summaries,
        "budget_is_additive": True,
        "broad_exploration_reduced": False,
        "official_emergence_levels_changed": False,
        "dedicated_3d_path_detector_available": False,
    }


def load_register_and_follow(
    *, burst_id: str, master_seed: int, workers: int, path_summary: dict[str, Any],
    trials_2d: int = 24, max_leads: int = 2,
) -> dict[str, Any]:
    doc = _load()
    registered = register_frontier(doc, burst_id=burst_id, path_summary=path_summary)
    run = run_followups(
        doc, burst_id=burst_id, master_seed=master_seed, workers=workers,
        trials_2d=trials_2d, max_leads=max_leads,
    )
    return {"registered": registered, **run}
