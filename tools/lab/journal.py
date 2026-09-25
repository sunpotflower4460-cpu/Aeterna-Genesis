"""Session journal: an append-only log of everything that happened in the lab (lab/sessions/<id>/).

Every universe creation, law change, perturbation, branch and deletion is written with its full recipe, so a
session can be replayed and, if worth it, exported into research/sessions/ (small) by a person.
lab/ is git-ignored: nothing lands in the repository unless someone exports it.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
LAB_DIR = _REPO / "lab"


class Journal:
    def __init__(self, root: Path | None = None, session_id: str | None = None):
        self.session_id = session_id or time.strftime("%Y%m%d-%H%M%S")
        self.dir = (root or LAB_DIR / "sessions") / self.session_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._universes: dict[str, dict[str, Any]] = {}

    def log(self, kind: str, **data: Any) -> dict[str, Any]:
        rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, **data}
        with self._lock:
            with open(self.dir / "journal.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def remember(self, uid: str, info: dict[str, Any]) -> None:
        """Keep the latest recipe/lineage of each universe in universes.json (rewritten atomically)."""
        with self._lock:
            self._universes[uid] = info
            tmp = self.dir / "universes.json.tmp"
            tmp.write_text(json.dumps(self._universes, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.dir / "universes.json")

    def entries(self) -> list[dict[str, Any]]:
        p = self.dir / "journal.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
