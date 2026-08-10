"""Hot/cold split for the append-only Dream ledgers, without deleting evidence.

The event ledger and the view-preset ledger are rewritten in full every burst. At ~2,700 entries
each they are 3.9 MB and 2.2 MB, so every hourly commit rewrites ~6 MB of JSON even when only a few
entries changed. Aeterna's rule is that evidence is never deleted, so the fix is not truncation but
a hot/cold split:

* the most recent ``keep`` entries stay in the hot file that the loop reads and rewrites,
* older entries move into immutable numbered parts under ``<ledger>.archive/``, which are written
  once and never rewritten again -- so git stores each part exactly once instead of re-diffing it
  every hour,
* the hot file keeps the archived ids, so de-duplication still works and nothing is silently
  re-discovered, and it records which part holds each cold entry.

Recency is tracked by ``insertion_order`` rather than by mutating entries, so the entry schema that
CI and the Observatory read is unchanged. Entries that predate this module are ordered by id and
therefore archive first.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_PART = re.compile(r"-(\d{4})\.json$")


def archive_dir_for(path: Path | str) -> Path:
    path = Path(path)
    return path.parent / f"{path.stem}.archive"


def _next_part(archive_dir: Path, name: str) -> Path:
    highest = 0
    if archive_dir.exists():
        for existing in archive_dir.glob(f"{name}-*.json"):
            match = _PART.search(existing.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return archive_dir / f"{name}-{highest + 1:04d}.json"


def archived_ids(doc: dict[str, Any]) -> set[str]:
    return set((doc.get("archived") or {}).get("ids") or [])


def roll(
    doc: dict[str, Any],
    *,
    list_key: str,
    id_key: str,
    keep: int,
    archive_dir: Path | str,
    name: str,
    burst_id: str | None = None,
) -> dict[str, Any]:
    """Move everything older than the newest ``keep`` entries into an immutable archive part.

    Returns the same document, with the hot list trimmed. Writing nothing and returning early is
    the normal case for a small ledger.
    """
    entries = {
        str(entry.get(id_key)): entry
        for entry in (doc.get(list_key) or [])
        if entry.get(id_key)
    }
    known = set(entries)
    order = [i for i in (doc.get("insertion_order") or []) if i in known]
    seen = set(order)
    order.extend(sorted(i for i in known if i not in seen))

    overflow = len(order) - max(0, int(keep))
    if overflow <= 0:
        doc[list_key] = [entries[i] for i in sorted(entries)]
        doc["insertion_order"] = order
        return doc

    moved, kept = order[:overflow], order[overflow:]
    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    part = _next_part(archive_dir, name)
    part.write_text(json.dumps({
        "archive_version": 1,
        "note": "Immutable cold storage. Written once, never rewritten. Evidence is not deleted.",
        "sealed_at_burst": burst_id,
        "id_key": id_key,
        "count": len(moved),
        list_key: [entries[i] for i in moved],
    }, indent=2, ensure_ascii=False))

    archived = doc.setdefault("archived", {"parts": [], "ids": [], "count": 0})
    archived["parts"] = sorted({*(archived.get("parts") or []), part.name})
    archived["ids"] = sorted({*(archived.get("ids") or []), *moved})
    archived["count"] = len(archived["ids"])
    archived["directory"] = archive_dir.name
    archived["note"] = "Older entries live in the archive parts; nothing was deleted."

    doc[list_key] = [entries[i] for i in sorted(kept)]
    doc["insertion_order"] = kept
    return doc


def load_all(hot_path: Path | str, *, list_key: str) -> list[dict[str, Any]]:
    """Read the hot list plus every archive part, for analysis that needs the whole history."""
    hot_path = Path(hot_path)
    doc = json.loads(hot_path.read_text()) if hot_path.exists() else {}
    rows: list[dict[str, Any]] = []
    archive_dir = archive_dir_for(hot_path)
    if archive_dir.exists():
        for part in sorted(archive_dir.glob("*.json")):
            rows.extend(json.loads(part.read_text()).get(list_key) or [])
    rows.extend(doc.get(list_key) or [])
    return rows
