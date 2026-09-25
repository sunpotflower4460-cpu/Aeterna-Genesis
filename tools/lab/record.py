"""Turn a lab session into a small research record, and check that it replays.

    POST /api/journal/export  (button 「研究記録にする」)  ->  research/sessions/<id>/
        summary.md     what happened, for people: universes, what was put in, lineage, final sha256, the
                       事件簿 highlights, what the AI council said and which cards were tried or dismissed
        recipes.json   everything replay needs: recipe + step + sha256 per universe
        thumbs/*.png   one small last key frame per universe
    python -m tools.lab.replay research/sessions/<id>   ->  re-runs every recipe from t=0 and compares sha256

The record is at most ~1 MB. No keys, tokens or environment variables are written (only what the lab already
shows on screen). What the lab showed is a look, not a claim: a claim goes through replay + /audit.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

from tools.lab import observe, whites

_REPO = Path(__file__).resolve().parents[2]
SESSIONS = _REPO / "research" / "sessions"
MAX_BYTES = 1_000_000
ROLE = {"core": "中心", "vision": "見る係", "second_view": "別の視点", "claude-code": "Claude Code",
        "you": "うえきさん", "system": "ラボ"}


def _slug(text: str) -> str:
    s = re.sub(r"[^0-9A-Za-z぀-ヿ一-鿿]+", "-", text).strip("-")
    return s[:24] or "lab"


def export(hub, council=None, ids: list[str] | None = None, note: str = "", out_root: Path | None = None,
           session: str | None = None) -> dict[str, Any]:
    ids = [i for i in (ids or hub.ids()) if i in hub.ids()]
    if not ids:
        raise ValueError("書き出す宇宙がありません")
    now = _dt.datetime.now()
    name = f"{now.strftime('%Y-%m-%d-%H%M')}-{_slug(note.splitlines()[0] if note.strip() else hub.info(ids[0])['white'])}"
    out = (out_root or SESSIONS) / name
    out.mkdir(parents=True, exist_ok=False)
    labels = {uid: hub.info(uid)["label"] for uid in hub.ids()}

    rows = []
    for uid in ids:
        info, fin = hub.info(uid), hub.final_info(uid)      # final_info comes from the worker: authoritative
        rows.append({"id": uid, "label": info["label"], "white": info["white"], "parent": info["parent"],
                     "parent_label": labels.get(info["parent"]) if info["parent"] else None,
                     "branch_step": info["branch_step"], "fork_index": info.get("fork_index"),
                     "step": fin["step"], "t": fin["t"], "sha256": fin["sha256"], "recipe": fin["recipe"]})
    meta = {"version": 1, "exported_at": now.isoformat(timespec="seconds"), "session": session, "note": note,
            "replay": f"python -m tools.lab.replay research/sessions/{name}", "universes": rows}
    (out / "recipes.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    packet = observe.build(hub, ids, motion_frames=0)
    (out / "thumbs").mkdir()
    for u in packet["universes"]:
        kf = [im for im in u["images"] if im["kind"] == "keyframe"]
        if kf:
            (out / "thumbs" / f"{u['label']}.png").write_bytes(kf[-1]["png"])

    lines = [f"# 水槽ラボの記録（{now.strftime('%Y-%m-%d %H:%M')}）", ""]
    if note.strip():
        lines += ["うえきさんのメモ：", "", *[f"> {x}" for x in note.strip().splitlines()], ""]
    lines += ["これはラボで**見た**ことの記録で、主張ではない。主張にするときは下の replay で t=0 から作り直し、"
              "`/audit` を通すこと（AGENTS.md「育ったのか、置いたのか？」）。", "",
              f"再現：`{meta['replay']}`", ""]
    for row, u in zip(rows, packet["universes"]):
        w = whites.get(row["white"])
        lines += [f"## 宇宙 {row['label']}：{w.title}", ""]
        lines += [f"- {x}" for x in observe.describe_recipe(w, {**hub.info(row["id"]), "recipe": row["recipe"]})]
        if row["parent_label"]:
            lines.append(f"- 宇宙 {row['parent_label']} から step {row['branch_step']} で分岐")
        lines.append(f"- 最後：t={observe._fmt(row['t'])}・step {row['step']}・sha256 `{row['sha256'][:16]}…`")
        if (out / "thumbs" / f"{row['label']}.png").exists():
            lines.append(f"- 最後のキーフレーム：`thumbs/{row['label']}.png`")
        c = u["ceiling"]
        if c:
            lines.append(f"- この白の測定済みの天井：{c['reached']}（{c['tier']}）")
        ev = [e for e in u["events"] if not e["rule"].startswith("track:") or e["rule"] == "track:motion-summary"]
        if ev:
            lines += ["", "事件簿（規則で出した出来事の抜粋）：", ""]
            lines += [f"- [{e['rule']}] {e['text']}" for e in ev[-15:]]
        lines.append("")
    if council is not None and (council.messages or council.proposals):
        lines += ["## AI の会議", ""]
        for m in council.messages:
            if m["who"] == "system" and not m["text"].strip():
                continue
            text = m["text"].strip().replace("\n", " ")
            lines.append(f"- **{ROLE.get(m['who'], m['who'])}**{'（' + m['model'] + '）' if m['model'] else ''}："
                         f"{text[:400]}{'…' if len(text) > 400 else ''}")
        if council.proposals:
            lines += ["", "提案カード：", ""]
            for p in council.proposals:
                state = {"open": "未決", "tried": f"試した → 宇宙 {labels.get(p['child'], p['child'])}",
                         "dismissed": "見送った"}[p["status"]]
                change = ", ".join(f"{k}={v}" for k, v in (p["set"] or {}).items())
                if p["perturb"]:
                    change += f" 摂動 {p['perturb']['name']}"
                lines.append(f"- #{p['id']}（{ROLE.get(p['source'], p['source'])}）{p['parent_label']} から {change}："
                             f"{p['why']} → **{state}**")
        lines.append("")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    if total > MAX_BYTES:                         # thumbnails go first; the recipes and summary always stay
        for f in sorted((out / "thumbs").glob("*.png"), key=lambda f: -f.stat().st_size):
            total -= f.stat().st_size
            f.unlink()
            if total <= MAX_BYTES:
                break
    return {"dir": str(out), "name": name, "bytes": total, "universes": [r["label"] for r in rows],
            "files": sorted(str(f.relative_to(out)) for f in out.rglob("*") if f.is_file())}
