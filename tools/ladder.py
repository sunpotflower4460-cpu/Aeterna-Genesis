"""The ladder to the north star (docs/LADDER.md): print where we are, and check research/ladder.json.

    python tools/ladder.py            # where we are, in plain Japanese
    python tools/ladder.py --check    # validate (ids, statuses, evidence files, hypotheses); exit 1 on problems

A rung is `reached` only when its gate was passed by measurement; that needs evidence (a report or test file that
exists). The ladder is not integrated until one universe climbs every rung from t = 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LADDER = ROOT / "research" / "ladder.json"
HYPOTHESES = ROOT / "research" / "hypotheses.json"
STATUSES = ("reached", "partial", "open", "frontier")
MARK = {"reached": "●", "partial": "◐", "open": "○", "frontier": "·"}
WORD = {"reached": "到達", "partial": "一部", "open": "まだ", "frontier": "遠い"}
RUNG_KEYS = ("id", "name", "question", "gate", "placed_ok", "status", "note", "evidence", "hypotheses", "next")


def load(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or LADDER).read_text(encoding="utf-8"))


def check(d: dict[str, Any], root: Path = ROOT, hypotheses_path: Path | None = None) -> list[str]:
    """Problems found in a ladder document (empty = fine)."""
    probs: list[str] = []
    hp = hypotheses_path or root / "research" / "hypotheses.json"
    known = {h["id"] for h in json.loads(hp.read_text(encoding="utf-8"))["hypotheses"]} if hp.exists() else set()
    rungs = d.get("rungs")
    if not isinstance(rungs, list) or not rungs:
        return ["rungs がない"]
    seen: set[str] = set()
    for i, r in enumerate(rungs):
        rid = r.get("id", f"#{i}")
        for k in RUNG_KEYS:
            if k not in r:
                probs.append(f"{rid}: {k} がない")
        if rid in seen:
            probs.append(f"{rid}: id が重複")
        seen.add(rid)
        if rid != f"R{i}":
            probs.append(f"{rid}: 順番が R{i} と合わない")
        st = r.get("status")
        if st not in STATUSES:
            probs.append(f"{rid}: status {st!r} は {STATUSES} のどれでもない")
        ev = r.get("evidence") or []
        if st == "reached" and not ev:
            probs.append(f"{rid}: reached なのに証拠がない")
        if st == "partial" and not r.get("note"):
            probs.append(f"{rid}: partial なのに、何が足りないか（note）がない")
        for e in ev:
            if not e.get("claim"):
                probs.append(f"{rid}: 証拠に claim がない")
            f = e.get("file")
            if not f or not (root / f).exists():
                probs.append(f"{rid}: 証拠のファイル {f!r} がない")
        for h in r.get("hypotheses") or []:
            if h not in known:
                probs.append(f"{rid}: 仮説 {h} が research/hypotheses.json にない")
    for s in d.get("side") or []:
        for h in s.get("hypotheses") or []:
            if h not in known:
                probs.append(f"{s.get('id')}: 仮説 {h} が research/hypotheses.json にない")
    if d.get("integrated") and any(r.get("status") != "reached" for r in rungs):
        probs.append("integrated なのに、到達していない段がある")
    return probs


def summary(d: dict[str, Any]) -> list[str]:
    """Plain lines: the top reached rung, then each rung with its mark and next step."""
    rungs = d["rungs"]
    top = None
    for r in rungs:
        if r["status"] != "reached":
            break
        top = r
    lines = [f"北極星：{d.get('north_star', '')}"]
    lines.append(f"いま：{top['id']}「{top['name']}」まで到達" if top else "いま：まだ最初の段")
    if not d.get("integrated"):
        lines.append("（どの段も別々の白で確かめた段階。1 つの宇宙で t=0 から全部はまだ）")
    for r in rungs:
        line = f"{MARK[r['status']]} {r['id']} {r['name']}（{WORD[r['status']]}）"
        if r["status"] == "partial" and r.get("note"):
            line += f" — {r['note']}"
        elif r.get("next"):
            line += f" — 次：{r['next']}"
        lines.append(line)
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = load()
    if a.check:
        probs = check(d)
        for p in probs:
            print("✗", p)
        print("ok" if not probs else f"{len(probs)} 件の問題")
        return 1 if probs else 0
    print("\n".join(summary(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
