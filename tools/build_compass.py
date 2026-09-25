"""Build RESEARCH_COMPASS.md (the human "where are we") from the single canonical index.

Inputs: research/index.json (hand-edited, reviewed in PRs), app/public/aquarium/templates.json,
research/inbox/*.md and research/decisions/*.md. Output: RESEARCH_COMPASS.md.

    python tools/build_compass.py           # write
    python tools/build_compass.py --check   # fail if RESEARCH_COMPASS.md is stale (used by tests)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_OUT = _REPO / "RESEARCH_COMPASS.md"


def _front(path: Path) -> dict[str, str]:
    m = re.match(r"---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)) if m else {}


def render() -> str:
    idx = json.loads((_REPO / "research" / "index.json").read_text(encoding="utf-8"))
    tpl_path = _REPO / "app" / "public" / "aquarium" / "templates.json"
    tpls = {t["id"]: t for t in json.loads(tpl_path.read_text(encoding="utf-8"))["templates"]} if tpl_path.exists() else {}
    L = ["# 🧭 Research Compass（研究の羅針盤）", "",
         "> 自動生成：`python tools/build_compass.py`（正本は [`research/index.json`](research/index.json)）。手で編集しない。",
         f"> 更新：{idx['updated']}", "", f"**北極星**：{idx['north_star']}", "",
         "## 白ごとの現在地（天井地図）", "",
         "| 白 | 到達 | tier | 天井の理由 | 水槽 |", "|---|---|---|---|---|"]
    for w in idx["whites"]:
        aq = f"[`{w['aquarium']}`](app/public/aquarium/{w['aquarium']}/)" if w.get("aquarium") in tpls else "—"
        L.append(f"| {w['name']} | **{w['reached']}** | {w['tier']} | {w['ceiling_reason']} | {aq} |")
    notes = [w for w in idx["whites"] if w.get("note")]
    if notes:
        L.append("")
        L += [f"- {w['name']}：{w['note']}" for w in notes]
    L += ["", "詳しくは [`docs/WHITE_CEILINGS.md`](docs/WHITE_CEILINGS.md)。", "", "## 開いている問い（優先順）", ""]
    for q in sorted(idx["open_questions"], key=lambda q: q["priority"]):
        L.append(f"{q['priority']}. **{q['question']}**（{q['where']}）")
    L += ["", "## 監査", ""]
    L += [f"- [{a['doc']}]({a['doc']})：{a['summary']}" for a in idx["audits"]]
    L += ["", "## 提案と決定（`research/`）", ""]
    inbox = sorted((_REPO / "research" / "inbox").glob("*.md"))
    decided = sorted((_REPO / "research" / "decisions").glob("*.md"))
    L.append(f"- 未決の提案：{len(inbox)} 件" + ("" if inbox else "（`/propose` で作る）"))
    L += [f"  - [{p.name}](research/inbox/{p.name})（{_front(p).get('white', '?')}）" for p in inbox]
    L.append(f"- 決定済み：{len(decided)} 件")
    L += [f"  - [{p.name}](research/decisions/{p.name})：{_front(p).get('status', '?')}" for p in decided]
    L += ["", "## 見る・動かす", "",
          "- 水槽：アプリ（`app/`）の最初の画面。テンプレート一覧は `app/public/aquarium/templates.json`。",
          "- AI と対話で進める：`CLAUDE.md` と `/status`・`/run-white`・`/audit`・`/report`・`/propose`。", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.check:
        if not _OUT.exists() or _OUT.read_text(encoding="utf-8") != text:
            sys.exit("RESEARCH_COMPASS.md is stale: run `python tools/build_compass.py`")
        print("RESEARCH_COMPASS.md is up to date")
        return
    _OUT.write_text(text, encoding="utf-8")
    print(f"wrote {_OUT.relative_to(_REPO)}")


if __name__ == "__main__":
    main()
