"""Promising Lead follow-up engine for Adaptive Dream v4.

A promising result is not just archived: it receives a bounded, automatic verification budget on
later hourly bursts.  The budget is ADDITIVE, so broad/unexplored/random exploration is never removed.
Follow-ups ask four different questions:
  - exact: does the same condition survive fresh seeds?
  - local: does the effect survive small nearby parameter changes?
  - contrast: does an intentionally different condition behave the same (possible confound)?
  - 3d: does the lead transfer when started directly in 3D?

Lead status is search metadata only.  It never changes emergence Levels, success thresholds,
promotion gates, or official Rooms.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from ai_lab import lab
from ai_lab.dream import adaptive
from ai_lab.dream import hourly_features as hourly

_REPO = Path(__file__).resolve().parents[2]
_LEADS = _REPO / "ai_lab" / "discoveries" / "promising_leads.json"
_ACTIVE = {"OPEN", "VERIFYING", "REPEATED", "ROBUST_REGION", "REPEATED_OBSERVATION"}


def _load() -> dict[str, Any]:
    if _LEADS.exists():
        try:
            return json.loads(_LEADS.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"version": 1, "note": "Bounded follow-up memory; status is not a scientific truth gate.", "leads": []}


def _save(doc: dict[str, Any]) -> None:
    _LEADS.parent.mkdir(parents=True, exist_ok=True)
    _LEADS.write_text(json.dumps(doc, indent=2, ensure_ascii=False))


def _seed(*parts: Any) -> int:
    raw = "|".join(str(x) for x in parts).encode()
    return int(hashlib.sha256(raw).hexdigest()[:12], 16) % 1_000_000_000


def _coarse_key(category: str, family: str, knobs: dict[str, Any]) -> str:
    n = max(float(knobs.get("noise_amplitude", 1e-3)), 1e-12)
    d = max(float(knobs.get("diffusion_ratio", 1.0)), 1e-12)
    bits = [
        category,
        family,
        f"n{round(math.log10(n), 1)}",
        f"c{round(float(knobs.get('correlation_length', 1.0)), 1)}",
        f"d{round(math.log10(d), 1)}",
        f"r{round(float(knobs.get('drive_strength', 1.0)), 1)}",
        f"q{round(float(knobs.get('quench_duration', 8.0)), 1)}",
    ]
    return "|".join(bits)


def _lead_id(key: str) -> str:
    return "lead-" + hashlib.sha256(key.encode()).hexdigest()[:12]


def _new_lead(*, category: str, family: str, knobs: dict[str, Any], seed: int | None,
              reached_level: int | None, burst_id: str, source: str, reason: str) -> dict[str, Any]:
    key = _coarse_key(category, family, knobs)
    return {
        "lead_id": _lead_id(key), "key": key, "category": category,
        "family": family, "knobs": dict(knobs), "source_seed": seed,
        "baseline_level": reached_level, "first_burst": burst_id, "last_seen_burst": burst_id,
        "source": source, "reason": reason, "status": "OPEN", "priority": 1.0,
        "times_selected": 0,
        "evidence": {
            "exact": {"n": 0, "success": 0},
            "local": {"n": 0, "success": 0},
            "contrast": {"n": 0, "success": 0},
            "native3d": {"n": 0, "success": 0},
            "geometry": {"n": 0, "triangle": 0, "fission_like": 0},
        },
        "honesty": {
            "status_changes_scientific_level": False,
            "status_changes_success_gate": False,
            "followup_replaces_broad_exploration": False,
        },
    }


def _upsert(doc: dict[str, Any], lead: dict[str, Any]) -> bool:
    items = doc.setdefault("leads", [])
    old = next((x for x in items if x.get("key") == lead["key"]), None)
    if old is None:
        items.append(lead)
        return True
    old["last_seen_burst"] = lead["last_seen_burst"]
    old["reason"] = lead["reason"]
    old["priority"] = min(2.0, float(old.get("priority", 1.0)) + 0.15)
    if old.get("status") == "WEAKENED":
        old["status"] = "VERIFYING"  # a genuinely new recurrence re-opens, but does not erase old evidence
    return False


def register_leads(
    doc: dict[str, Any], *, burst_id: str, events: list[dict[str, Any]],
    mass_results: list[dict[str, Any]], paired3d: list[dict[str, Any]], geometry_probes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Register only concrete, reconstructable leads.  Returns counts for reporting."""
    added = 0
    for e in events:
        if e.get("kind") not in {"REPRODUCED", "NEW_BEHAVIOR", "RARE_EVENT"}:
            continue
        f = e.get("facts") or {}
        family, knobs = f.get("family"), f.get("knobs")
        if not family or not isinstance(knobs, dict) or not knobs:
            continue
        category = "reproduced" if e.get("kind") == "REPRODUCED" else "behavior"
        lead = _new_lead(category=category, family=family, knobs=knobs, seed=f.get("seed"),
                         reached_level=f.get("reached_level"), burst_id=burst_id,
                         source=str(e.get("source") or "event"), reason=str(e.get("title") or e.get("kind")))
        added += int(_upsert(doc, lead))

    # Even if event classification is conservative, do not lose the strongest measured L2+ conditions.
    stable = [r for r in mass_results if r.get("score") is not None and int(r.get("reached_level") or 0) >= 2][:2]
    for r in stable:
        lead = _new_lead(category="high-level", family=r["family"], knobs=r["knobs"], seed=r.get("seed"),
                         reached_level=int(r.get("reached_level") or 0), burst_id=burst_id,
                         source="mass-2d", reason="L2以上に到達した上位条件")
        added += int(_upsert(doc, lead))

    for r in paired3d:
        if int(r.get("dimension_delta") or 0) <= 0:
            continue
        lead = _new_lead(category="dimension-emergence", family=r["family"], knobs=r["knobs"], seed=r.get("seed"),
                         reached_level=int(r.get("reached_level") or 0), burst_id=burst_id,
                         source="native-3d", reason="同条件の2Dより3Dの方が深く進んだ")
        added += int(_upsert(doc, lead))

    for p in geometry_probes:
        if not p.get("fission_like_after_triangle"):
            continue
        lead = _new_lead(category="triangle-fission", family=p["family"], knobs=p["knobs"], seed=p.get("seed"),
                         reached_level=2, burst_id=burst_id, source="geometry-probe",
                         reason="自然にできた3渦三角配置の後に分裂っぽい変化")
        added += int(_upsert(doc, lead))

    doc["last_burst"] = burst_id
    _save(doc)
    return {"added": added, "total": len(doc.get("leads") or [])}


def _variant_specs(lead: dict[str, Any], n: int, *, master_seed: int) -> list[dict[str, Any]]:
    n = max(0, int(n))
    counts = {"exact": int(n * 0.40), "local": int(n * 0.40)}
    counts["contrast"] = n - counts["exact"] - counts["local"]
    centre = adaptive._unit_from_knobs(lead["knobs"])
    family = lead["family"]
    out: list[dict[str, Any]] = []
    serial = 0
    for lane in ("exact", "local", "contrast"):
        for _ in range(counts[lane]):
            serial += 1
            rng = random.Random(_seed(lead["lead_id"], master_seed, lane, serial))
            unit = list(centre)
            fam = family
            if lane == "local":
                k = rng.randrange(len(unit))
                unit[k] = min(1.0, max(0.0, unit[k] + rng.uniform(-0.12, 0.12)))
            elif lane == "contrast":
                k = rng.randrange(len(unit))
                unit[k] = 1.0 - unit[k]
                if rng.random() < 0.5:
                    try:
                        pos = lab.IC_FAMILIES.index(fam)
                    except ValueError:
                        pos = 0
                    fam = lab.IC_FAMILIES[(pos + 1 + rng.randrange(max(1, len(lab.IC_FAMILIES) - 1))) % len(lab.IC_FAMILIES)]
            knobs = dict(lead["knobs"]) if lane == "exact" else adaptive._knobs(unit)
            out.append({
                "lead_id": lead["lead_id"], "followup_lane": lane, "family": fam, "knobs": knobs,
                "seed": _seed(lead["lead_id"], master_seed, lane, serial, "seed"), "quick": True,
            })
    return out


def _eval2d(spec: dict[str, Any]) -> dict[str, Any]:
    r = lab._screen_ic(spec["family"], spec["knobs"], int(spec["seed"]), quick=True)
    return {**spec, **r}


def _eval3d(spec: dict[str, Any]) -> dict[str, Any]:
    return hourly._screen3d(spec)


def _run_map(fn, payload: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    if not payload:
        return []
    if workers <= 1:
        return [fn(x) for x in payload]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, payload, chunksize=max(1, len(payload) // (workers * 8))))


def _rate(bucket: dict[str, Any]) -> float | None:
    n = int(bucket.get("n", 0))
    return None if n <= 0 else round(int(bucket.get("success", 0)) / n, 4)


def _update_status(lead: dict[str, Any]) -> None:
    ev = lead["evidence"]
    exact, local = ev["exact"], ev["local"]
    en, ln = int(exact["n"]), int(local["n"])
    er, lr = (_rate(exact) or 0.0), (_rate(local) or 0.0)
    if lead.get("category") == "triangle-fission":
        g = ev["geometry"]
        gn, fs = int(g["n"]), int(g["fission_like"])
        if gn >= 24 and fs == 0:
            lead["status"] = "WEAKENED"
        elif gn >= 24 and fs >= 4:
            lead["status"] = "REPEATED_OBSERVATION"  # observation repeated; causality is NOT claimed
        else:
            lead["status"] = "VERIFYING"
        return
    if en >= 16 and er < 0.20:
        lead["status"] = "WEAKENED"
    elif en >= 16 and er >= 0.60 and ln >= 16 and lr >= 0.40:
        lead["status"] = "ROBUST_REGION"
    elif en >= 12 and er >= 0.60:
        lead["status"] = "REPEATED"
    else:
        lead["status"] = "VERIFYING"


def run_followups(
    doc: dict[str, Any], *, burst_id: str, master_seed: int, workers: int,
    trials_2d: int = 256, trials_3d: int = 32, max_leads: int = 4, geometry_per_triangle_lead: int = 16,
) -> dict[str, Any]:
    """Spend a bounded additive budget on unresolved leads; broad exploration remains untouched."""
    leads = [x for x in doc.get("leads", []) if x.get("status") in _ACTIVE]
    leads.sort(key=lambda x: (float(x.get("priority", 1.0)), -int(x.get("times_selected", 0))), reverse=True)
    chosen = leads[:max(0, int(max_leads))]
    if not chosen:
        return {"active_leads": 0, "selected_leads": 0, "trials_2d": 0, "trials_3d": 0,
                "geometry_replays": 0, "strengthened": 0, "weakened": 0, "leads": []}

    per2 = max(1, int(trials_2d) // len(chosen)) if trials_2d > 0 else 0
    per3 = max(1, int(trials_3d) // len(chosen)) if trials_3d > 0 else 0
    summaries = []
    strengthened = weakened = geometry_total = 0
    for lead in chosen:
        before = lead.get("status", "OPEN")
        specs2 = _variant_specs(lead, per2, master_seed=master_seed)
        r2 = _run_map(_eval2d, specs2, workers)
        # 3D uses exact + local variants only; contrast remains a cheap 2D specificity check.
        specs3 = [x for x in _variant_specs(lead, per3, master_seed=master_seed ^ 0x3D44)
                  if x["followup_lane"] != "contrast"]
        specs3 = specs3[:per3]
        r3 = _run_map(_eval3d, specs3, workers)
        baseline = int(lead.get("baseline_level") or 2)
        for r in r2:
            lane = r["followup_lane"]
            b = lead["evidence"][lane]
            b["n"] += 1
            if r.get("reached_level") is not None and int(r.get("reached_level") or 0) >= baseline:
                b["success"] += 1
        for r in r3:
            b = lead["evidence"]["native3d"]
            b["n"] += 1
            if r.get("reached_level") is not None and int(r.get("reached_level") or 0) >= baseline:
                b["success"] += 1

        geometry = []
        if lead.get("category") == "triangle-fission" and geometry_per_triangle_lead > 0:
            selected = [r for r in r2 if r.get("score") is not None][:geometry_per_triangle_lead]
            payload = [{**r, "quick": True} for r in selected]
            geometry = _run_map(hourly._geometry_probe, payload, workers)
            gb = lead["evidence"]["geometry"]
            gb["n"] += len(geometry)
            gb["triangle"] += sum(bool(x.get("triangle_seen")) for x in geometry)
            gb["fission_like"] += sum(bool(x.get("fission_like_after_triangle")) for x in geometry)
            geometry_total += len(geometry)

        lead["times_selected"] = int(lead.get("times_selected", 0)) + 1
        lead["last_followup_burst"] = burst_id
        lead["priority"] = max(0.25, float(lead.get("priority", 1.0)) * 0.92)
        _update_status(lead)
        after = lead["status"]
        if after in {"REPEATED", "ROBUST_REGION", "REPEATED_OBSERVATION"} and before not in {"REPEATED", "ROBUST_REGION", "REPEATED_OBSERVATION"}:
            strengthened += 1
        if after == "WEAKENED" and before != "WEAKENED":
            weakened += 1
        ev = lead["evidence"]
        summaries.append({
            "lead_id": lead["lead_id"], "category": lead["category"], "status": after,
            "family": lead["family"], "reason": lead.get("reason"),
            "exact_rate": _rate(ev["exact"]), "local_rate": _rate(ev["local"]),
            "contrast_rate": _rate(ev["contrast"]), "native3d_rate": _rate(ev["native3d"]),
            "geometry": dict(ev["geometry"]),
        })

    doc["last_followup_burst"] = burst_id
    _save(doc)
    return {
        "active_leads": len(leads), "selected_leads": len(chosen),
        "trials_2d": sum(per2 for _ in chosen), "trials_3d": sum(per3 for _ in chosen),
        "geometry_replays": geometry_total, "strengthened": strengthened, "weakened": weakened,
        "leads": summaries,
        "budget_is_additive": True,
        "broad_exploration_reduced": False,
        "scientific_gates_changed": False,
    }


def load_register_and_follow(
    *, burst_id: str, master_seed: int, workers: int, events: list[dict[str, Any]],
    mass_results: list[dict[str, Any]], paired3d: list[dict[str, Any]], geometry_probes: list[dict[str, Any]],
    trials_2d: int = 256, trials_3d: int = 32, max_leads: int = 4,
) -> dict[str, Any]:
    doc = _load()
    reg = register_leads(doc, burst_id=burst_id, events=events, mass_results=mass_results,
                         paired3d=paired3d, geometry_probes=geometry_probes)
    run = run_followups(doc, burst_id=burst_id, master_seed=master_seed, workers=workers,
                        trials_2d=trials_2d, trials_3d=trials_3d, max_leads=max_leads)
    return {"registered": reg, **run}
