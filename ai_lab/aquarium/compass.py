from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "aquaria" / "registry.json"
NOTEBOOK_PATH = ROOT / "aquaria" / "notebook.json"
BACKLOG_PATH = ROOT / "ai_lab" / "discoveries" / "research_backlog.json"
OUTPUT_JSON = ROOT / "ai_lab" / "reports" / "easy" / "aquarium_compass_latest.json"
OUTPUT_MD = ROOT / "ai_lab" / "reports" / "easy" / "aquarium_compass_latest.md"


def _load(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _requested_instruments(aquarium: dict[str, Any]) -> list[str]:
    recipe = aquarium.get("recipe_space") or {}
    out: list[str] = []
    next_instrument = recipe.get("next_instrument")
    if isinstance(next_instrument, str):
        out.append(next_instrument)
    required = recipe.get("required_instruments")
    if isinstance(required, list):
        out.extend(str(v) for v in required if isinstance(v, str))
    return list(dict.fromkeys(out))


def _note_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(e.get("author_role", "unknown")) for e in entries)
    latest_human = next((e.get("text") for e in reversed(entries) if e.get("author_role") == "human"), None)
    latest_ai = next((e.get("text") for e in reversed(entries) if e.get("author_role") == "ai"), None)
    return {
        "count": len(entries),
        "by_author": dict(counts),
        "latest_human_note": latest_human,
        "latest_ai_direction": latest_ai,
    }


def build_compass(
    registry: dict[str, Any] | None = None,
    notebook: dict[str, Any] | None = None,
    backlog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry if registry is not None else _load(REGISTRY_PATH, {"aquaria": []})
    notebook = notebook if notebook is not None else _load(NOTEBOOK_PATH, {"entries": []})
    backlog = backlog if backlog is not None else _load(BACKLOG_PATH, {"entries": []})

    note_entries = notebook.get("entries") or []
    backlog_entries = backlog.get("entries") or []
    backlog_by_request = {
        e.get("request_id"): e
        for e in backlog_entries
        if isinstance(e, dict) and isinstance(e.get("request_id"), str)
    }

    aquaria_out: list[dict[str, Any]] = []
    for aquarium in registry.get("aquaria") or []:
        aid = aquarium.get("aquarium_id")
        notes = [e for e in note_entries if e.get("aquarium_id") == aid]
        requested = _requested_instruments(aquarium)
        open_instruments = []
        for request_id in requested:
            entry = backlog_by_request.get(request_id)
            if entry:
                open_instruments.append(
                    {
                        "request_id": request_id,
                        "status": entry.get("status"),
                        "question": entry.get("question"),
                        "purpose": entry.get("purpose"),
                        "related_capability": entry.get("related_capability"),
                        "related_capability_status": entry.get("related_capability_status"),
                    }
                )

        aquaria_out.append(
            {
                "aquarium_id": aid,
                "title": aquarium.get("title"),
                "origin": aquarium.get("origin"),
                "status": aquarium.get("status"),
                "intent_mode": (aquarium.get("intent") or {}).get("mode"),
                "goal": (aquarium.get("intent") or {}).get("goal"),
                "classes": aquarium.get("classes") or [],
                "observation_focus": aquarium.get("observation_focus") or [],
                "evidence_refs": aquarium.get("evidence_refs") or [],
                "notes": _note_summary(notes),
                "requested_instruments": requested,
                "open_instruments": open_instruments,
            }
        )

    status_counts = Counter(str(a.get("status")) for a in aquaria_out)
    origin_counts = Counter(str(a.get("origin")) for a in aquaria_out)

    backlog_next = backlog.get("recommended_next")
    recommended_aquarium = None
    if isinstance(backlog_next, str) and backlog_next.startswith("instrument:"):
        target = backlog_next.split(":", 1)[1]
        recommended_aquarium = next(
            (a["aquarium_id"] for a in aquaria_out if target in a["requested_instruments"]),
            None,
        )
    if recommended_aquarium is None:
        recommended_aquarium = next(
            (a["aquarium_id"] for a in aquaria_out if a.get("status") == "active"),
            aquaria_out[0]["aquarium_id"] if aquaria_out else None,
        )

    return {
        "version": 1,
        "mode": "universe-aquarium-compass",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "aquaria": len(aquaria_out),
            "by_status": dict(status_counts),
            "by_origin": dict(origin_counts),
            "notes": len(note_entries),
        },
        "recommended_attention": {
            "aquarium_id": recommended_aquarium,
            "research_backlog_recommended_next": backlog_next,
            "reason": "Prefer a linked open instrument when Research Backlog names one; otherwise keep an active Aquarium visible.",
        },
        "aquaria": aquaria_out,
        "policy": {
            "planning_only": True,
            "intent_is_scientific_evidence": False,
            "notes_are_scientific_evidence": False,
            "changes_physics": False,
            "changes_initial_conditions": False,
            "routes_physical_compute": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }


def render_markdown(compass: dict[str, Any]) -> str:
    lines = [
        "# Universe Aquarium Compass",
        "",
        "人間とAIが共有する planning-only の研究地図。ここに書かれた Intent / Note / Direction は科学的証拠ではありません。",
        "",
    ]
    attention = compass.get("recommended_attention") or {}
    if attention.get("aquarium_id"):
        lines += [
            f"**いま確認する候補:** `{attention['aquarium_id']}`",
            "",
        ]

    for aquarium in compass.get("aquaria") or []:
        lines += [
            f"## {aquarium.get('title')} — `{aquarium.get('aquarium_id')}`",
            "",
            f"- origin: **{aquarium.get('origin')}** / status: **{aquarium.get('status')}** / intent: **{aquarium.get('intent_mode')}**",
            f"- goal: {aquarium.get('goal')}",
        ]
        latest_human = (aquarium.get("notes") or {}).get("latest_human_note")
        latest_ai = (aquarium.get("notes") or {}).get("latest_ai_direction")
        if latest_human:
            lines.append(f"- Human Note: {latest_human}")
        if latest_ai:
            lines.append(f"- AI Direction: {latest_ai}")
        instruments = aquarium.get("open_instruments") or []
        if instruments:
            lines.append("- open instruments: " + ", ".join(str(i.get("request_id")) for i in instruments))
        lines.append("")

    lines += [
        "---",
        "Intent は探索計画が読めますが、物理 solver は Intent 文を読みません。Aquarium Compass は compute allocation や scientific promotion を変更しません。",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    compass = build_compass()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(compass, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(compass), encoding="utf-8")
    return compass


def main() -> int:
    compass = write_outputs()
    print(
        "Aquarium Compass: aquaria=%d notes=%d attention=%s"
        % (
            compass["counts"]["aquaria"],
            compass["counts"]["notes"],
            compass["recommended_attention"]["aquarium_id"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
