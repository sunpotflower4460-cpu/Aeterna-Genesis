"""Mission contract evaluation for Adaptive Dream v7.

A goal is a checklist of evidence requirements, never an instruction to seed a target morphology.
The default zero-to-division-like mission is intentionally stricter than F7: relation/network
separation alone cannot satisfy individual identity, accounting, or inheritance requirements.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT = _REPO / "ai_lab" / "missions" / "zero_to_division_like.json"


def load_contract(path: Path | None = None) -> dict[str, Any]:
    p = path or _DEFAULT
    return json.loads(p.read_text())


def evaluate(report: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only explicitly recorded goal evidence; do not infer biology from F-depth."""
    obs = report.get("goal_observations") or {}
    requirements = contract.get("requirements") or []
    rows = []
    for req in requirements:
        key = str(req.get("id"))
        evidence = obs.get(key)
        satisfied = bool(isinstance(evidence, dict) and evidence.get("satisfied") is True and evidence.get("scientific_usable") is not False)
        rows.append({
            "id": key,
            "label": req.get("label"),
            "required": bool(req.get("required", True)),
            "satisfied": satisfied,
            "evidence": evidence,
        })
    required = [x for x in rows if x["required"]]
    done = sum(1 for x in required if x["satisfied"])
    goal_reached = bool(required) and done == len(required)
    return {
        "version": 1,
        "mission_id": contract.get("mission_id"),
        "required_satisfied": done,
        "required_total": len(required),
        "progress_fraction": round(done / len(required), 4) if required else 0.0,
        "goal_reached": goal_reached,
        "requirements": rows,
        "important_interpretation": {
            "F7_alone_is_cell_division": False,
            "network_separation_alone_is_cell_division": False,
            "target_morphology_may_be_seeded": False,
            "division_location_or_time_may_be_seeded": False,
        },
    }
