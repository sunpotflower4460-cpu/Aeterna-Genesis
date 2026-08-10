"""Observation presets for Dream events.

A preset changes only how an already-computed field is viewed.  It never changes the
simulation, success criteria, or official status of a Room.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ai_lab.dream import ledger_archive


def _measured(event: dict[str, Any]) -> dict[str, Any]:
    facts = event.get("facts") or {}
    return facts.get("measured_by") or {}


def recommended_lens(event: dict[str, Any]) -> str:
    mb = _measured(event)
    defects = float(mb.get("defect_count") or 0.0)
    if defects > 0:
        return "phase"
    return "density"


def make_view_preset(event: dict[str, Any]) -> dict[str, Any]:
    """Create a non-physical view recipe for one event.

    `ready` means the event points at a recorded candidate Room.  Screen-only discoveries still
    receive a recipe so that the same view can be applied if/when a recorded Room is produced.
    """
    room_id = event.get("room_id")
    parent = event.get("parent_room")
    lens = recommended_lens(event)
    preset_id = "view-" + event["event_id"].replace("evt-", "")
    return {
        "preset_version": 1,
        "preset_id": preset_id,
        "event_id": event["event_id"],
        "room_id": room_id,
        "parent_room": parent,
        "ready": bool(room_id),
        "lens": lens,
        "playback": {"speed": 0.5, "start_fraction": 0.0, "end_fraction": 1.0, "loop": True},
        "view": {"threshold": 0.2, "opacity": 0.72, "glow": 0.32, "quality": 1.0},
        "comparison": {
            "mode": "parent_vs_candidate" if room_id and parent else "single",
            "sync_time": True,
        },
        "reason": (
            "phase lens: winding/defect structure is measured"
            if lens == "phase"
            else "density lens: amplitude/density change is the clearest default"
        ),
        "honesty": {
            "changes_physics": False,
            "changes_success_gate": False,
            "scientific_promotion": False,
        },
    }


# Hot window for view presets; old recipes are immutable evidence, not discarded.
PRESET_KEEP = 400


def merge_presets(path: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    """Upsert deterministic presets, keeping old entries in immutable cold storage."""
    if os.path.exists(path):
        doc = json.load(open(path))
    else:
        doc = {"preset_version": 1, "note": "Observation presets only; they never alter physics or scientific status.", "presets": []}
    cold = ledger_archive.archived_ids(doc)
    by_id = {p["preset_id"]: p for p in doc.get("presets", [])}
    for event in events:
        preset = make_view_preset(event)
        event["view_preset_id"] = preset["preset_id"]
        if preset["preset_id"] not in cold:
            by_id[preset["preset_id"]] = preset
    doc["presets"] = sorted(by_id.values(), key=lambda p: p["preset_id"])
    ledger_archive.roll(doc, list_key="presets", id_key="preset_id", keep=PRESET_KEEP,
                        archive_dir=ledger_archive.archive_dir_for(path), name="presets")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    return doc
