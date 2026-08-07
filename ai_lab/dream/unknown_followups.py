"""Bounded verification for recurrent open-ended X-patterns.

Only patterns that have already repeated across passive open-ended observations are eligible.  When
such a pattern reappears in the current mass-search population, this lane replays its start-side
condition with fresh seeds, a small local perturbation, and a deliberately different contrast.

This is additive verification.  It never replaces unexplored/random/breaker budgets and never turns a
pattern fingerprint into a scientific claim by itself.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ai_lab.dream import open_ended

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"


def _seed(pattern_id: str, burst_id: str, mode: str) -> int:
    raw = f"{pattern_id}|{burst_id}|{mode}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16) % 1_000_000 + 1


def _clip_knobs(knobs: dict[str, Any]) -> dict[str, float]:
    return {
        "noise_amplitude": max(1e-6, min(0.02, float(knobs.get("noise_amplitude", 1e-4)))),
        "correlation_length": max(1.0, min(12.0, float(knobs.get("correlation_length", 4.0)))),
        "diffusion_ratio": max(0.1, min(8.0, float(knobs.get("diffusion_ratio", 1.0)))),
        "drive_strength": max(0.1, min(5.0, float(knobs.get("drive_strength", 1.0)))),
        "quench_duration": max(4.0, min(20.0, float(knobs.get("quench_duration", 8.0)))),
    }


def variants(source: dict[str, Any], *, pattern_id: str, burst_id: str) -> list[dict[str, Any]]:
    base = _clip_knobs(source.get("knobs") or {})
    local = dict(base)
    local["noise_amplitude"] *= 1.15
    local["correlation_length"] *= 0.92
    local["diffusion_ratio"] *= 1.12
    local["drive_strength"] *= 0.95
    local["quench_duration"] *= 1.05
    local = _clip_knobs(local)
    contrast = dict(base)
    contrast["diffusion_ratio"] = 6.0 if base["diffusion_ratio"] < 1.0 else 0.15
    contrast["drive_strength"] = 0.25 if base["drive_strength"] > 2.5 else 4.75
    contrast["correlation_length"] = 11.0 if base["correlation_length"] < 6.0 else 1.25
    contrast = _clip_knobs(contrast)
    common = {"family": source.get("family"), "trial_index": source.get("trial_index"), "score": source.get("score")}
    return [
        {**common, "knobs": base, "seed": _seed(pattern_id, burst_id, "exact"), "followup_mode": "fresh-seed-exact"},
        {**common, "knobs": local, "seed": _seed(pattern_id, burst_id, "local"), "followup_mode": "fresh-seed-local"},
        {**common, "knobs": contrast, "seed": _seed(pattern_id, burst_id, "contrast"), "followup_mode": "fresh-seed-contrast"},
    ]


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _eligible_sources(mass_results: list[dict[str, Any]], *, max_patterns: int) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    graph = open_ended._load_ledger()
    current_by_trial = {x.get("trial_index"): x for x in mass_results}
    recurrent_ids = {
        p.get("pattern_id") for p in graph.get("patterns") or []
        if p.get("status") in {"CROSS_CONDITION_RECURRENT", "ROBUST_RECURRENT_CANDIDATE", "CROSS_WORLD_CANDIDATE"}
    }
    if not recurrent_ids:
        return []
    found: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen: set[str] = set()
    for episode in reversed(graph.get("recent_episodes") or []):
        pid = episode.get("pattern_id")
        source = current_by_trial.get(episode.get("trial_index"))
        if pid not in recurrent_ids or source is None or pid in seen:
            continue
        found.append((episode, source))
        seen.add(str(pid))
        if len(found) >= max(0, int(max_patterns)):
            break
    return found


def run_recurrent_followups(
    *, burst_id: str, mass_results: list[dict[str, Any]], quick: bool = True,
    max_patterns: int = 2, max_episodes_per_probe: int = 3,
) -> dict[str, Any]:
    selected = _eligible_sources(mass_results, max_patterns=max_patterns)
    doc = _read(_LEDGER, {"version": 1, "patterns": {}})
    out_rows: list[dict[str, Any]] = []
    graph = open_ended._load_ledger()

    for source_episode, source_rec in selected:
        pid = str(source_episode["pattern_id"])
        row = doc.setdefault("patterns", {}).setdefault(pid, {
            "pattern_id": pid,
            "exact": {"n": 0, "hit": 0},
            "local": {"n": 0, "hit": 0},
            "contrast": {"n": 0, "hit": 0},
            "status": "VERIFYING",
        })
        pattern_results = []
        for rec in variants(source_rec, pattern_id=pid, burst_id=burst_id):
            probe = open_ended._probe({**rec, "quick": bool(quick)})
            episodes = open_ended.detect_episodes(probe, max_episodes=max_episodes_per_probe)
            for e in episodes:
                e["followup_mode"] = rec["followup_mode"]
                e["source_pattern_id"] = pid
            graph = open_ended._update_ledger(graph, burst_id=burst_id, episodes=episodes)["ledger"]
            hit = any(e.get("pattern_id") == pid for e in episodes)
            bucket = "exact" if "exact" in rec["followup_mode"] else ("local" if "local" in rec["followup_mode"] else "contrast")
            row[bucket]["n"] = int(row[bucket].get("n", 0)) + 1
            row[bucket]["hit"] = int(row[bucket].get("hit", 0)) + int(hit)
            pattern_results.append({
                "mode": rec["followup_mode"],
                "seed": rec["seed"],
                "hit_same_pattern": hit,
                "episode_pattern_ids": [e.get("pattern_id") for e in episodes],
            })
        evidence_n = int(row["exact"]["n"]) + int(row["local"]["n"])
        evidence_hit = int(row["exact"]["hit"]) + int(row["local"]["hit"])
        contrast_hit = int(row["contrast"]["hit"])
        if evidence_n >= 4 and evidence_hit == 0:
            row["status"] = "WEAKENED"
        elif evidence_hit >= 2 and contrast_hit == 0:
            row["status"] = "REPEATED_SPECIFIC_CANDIDATE"
        elif evidence_hit >= 2 and contrast_hit > 0:
            row["status"] = "REPEATED_NONSPECIFIC"
        else:
            row["status"] = "VERIFYING"
        row["last_burst"] = burst_id
        out_rows.append({"pattern_id": pid, "status": row["status"], "results": pattern_results})

    open_ended._LEDGER.parent.mkdir(parents=True, exist_ok=True)
    open_ended._LEDGER.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    doc["last_burst"] = burst_id
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return {
        "version": 1,
        "selected_patterns": len(selected),
        "trials": len(selected) * 3,
        "patterns": out_rows,
        "fresh_seed_exact_local_contrast": True,
        "replaces_broad_exploration": False,
        "changes_scientific_gate": False,
        "target_shape_seeded": False,
    }
