"""Read-only repository inventory for the 2026-09 research restart (plan phase P0).

Counts what is tracked in git (sizes, file counts, largest files) and what the automated
Dream candidates actually are (which white / genesis_model, which Emergence Level).
It never modifies research data; it only writes the Markdown report given by --out.

    python tools/inventory.py --freeze-sha <commit> --out docs/INVENTORY_2026-09.md

Counts always come from the current checkout (HEAD); --freeze-sha only names the evidence
baseline, and the report prints both commits so they are never conflated.

Standard library only (no numpy / PyYAML), so it runs in a bare container.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
import re
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

# Commit counts measured with GitHub commit search on 2026-09-25 (local clone is shallow, so git log
# cannot reproduce them). Kept here as a sourced constant rather than recomputed.
_COMMIT_STATS = {
    "window": "2026-07-27 .. 2026-09-25",
    "total": 4125,
    "human_account": 198,
    "aeterna_dream_bot": 1146,
    "last_human_commit": "2026-09-01",
    "source": "GitHub commit search (repo:sunpotflower4460-cpu/Aeterna-Genesis), 2026-09-25",
}

_BOT_WORKFLOWS = (
    "dream-loop", "free-hypothesis-lab", "science-bridge",
    "research-maintenance", "research-postflight", "research-continuity",
)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_REPO, check=True, capture_output=True, text=True).stdout


def _remote_tag_commit(tag: str) -> str | None:
    """Commit an annotated/lightweight tag points to on origin (not the local tag), or None."""
    try:
        out = subprocess.run(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
                             cwd=_REPO, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    refs = dict(reversed(line.split("\t")) for line in out.splitlines() if "\t" in line)
    return refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")


def _human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return str(n)


def tracked_files() -> list[tuple[str, int]]:
    out = []
    for path in _git("ls-files", "-z").split("\0"):
        if not path:
            continue
        try:
            out.append((path, os.path.getsize(_REPO / path)))
        except OSError:
            out.append((path, 0))
    return out


def _top(path: str) -> str:
    return path.split("/")[0] + "/" if "/" in path else "(root files)"


def candidate_rooms() -> dict[str, collections.Counter]:
    """Tally genesis_model and levels from rooms/candidates/*/room.yaml (flat keys, regex only)."""
    stats = {"model": collections.Counter(), "reached": collections.Counter(),
             "candidate": collections.Counter(), "prefix": collections.Counter()}
    base = _REPO / "rooms" / "candidates"
    if not base.is_dir():
        return stats
    for room in sorted(x for x in base.iterdir() if x.is_dir()):  # skip README.md etc.
        stats["prefix"][re.sub(r"-\d{8}-.*", "", room.name) if "dream" in room.name else "other"] += 1
        f = room / "room.yaml"
        if not f.is_file():
            stats["model"]["(no room.yaml)"] += 1
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^genesis_model:\s*(\S+)", text, re.M)
        stats["model"][m.group(1) if m else "(unknown)"] += 1
        m = re.search(r"^\s+reached_level:\s*(\S+)", text, re.M)
        stats["reached"][m.group(1) if m else "(none)"] += 1
        m = re.search(r"^\s+candidate_level:\s*(\S+)", text, re.M)
        stats["candidate"][m.group(1) if m else "(none)"] += 1
    return stats


def workflow_triggers() -> list[tuple[str, str]]:
    rows = []
    for f in sorted((_REPO / ".github" / "workflows").glob("*.yml")):
        text = f.read_text(encoding="utf-8")
        block = re.search(r"^on:\n((?:[ #].*\n|\n)*)", text, re.M)
        keys = re.findall(r"^  ([a-z_]+):", block.group(1), re.M) if block else []
        writes_main = "git push origin HEAD:main" in text
        rows.append((f.stem, ", ".join(keys) + (" · run 内で main へ push する手順あり" if writes_main else "")))
    return rows


def render(freeze_sha: str, inventory_sha: str) -> str:
    files = tracked_files()
    total = sum(s for _, s in files)
    by_top: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    by_sub: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for p, s in files:
        t = _top(p)
        by_top[t][0] += 1
        by_top[t][1] += s
        parts = p.split("/")[:-1]  # directories only
        if parts and parts[0] in {"rooms", "app", "ai_lab"} and len(parts) >= 2:
            k = "/".join(parts[:3] if parts[0] == "app" else parts[:2]) + "/"
            by_sub[k][0] += 1
            by_sub[k][1] += s
    cand = candidate_rooms()
    today = dt.date.today().isoformat()

    L = []
    L.append("# INVENTORY 2026-09 — 再始動前の棚卸し（P0）\n")
    L.append(f"生成: `python tools/inventory.py` · {today} · 読み取りのみ（研究データは変更しない）。\n")
    L.append("## 凍結点\n")
    L.append(f"- 凍結 commit（**正本・不変**）: `{freeze_sha}`（bot を止める直前の `main`）")
    L.append(f"- 棚卸し対象 commit: `{inventory_sha}`（下の数値はこの checkout の git index から数えた。凍結 commit とは")
    L.append("  P0 自身の変更分だけ異なりうる）")
    tag = _remote_tag_commit("evidence-freeze-2026-09")
    if tag == freeze_sha:
        L.append("- 凍結タグ `evidence-freeze-2026-09`: origin に作成済み（上の凍結 commit を指すことを確認）")
    elif tag:
        L.append(f"- 凍結タグ `evidence-freeze-2026-09`: ⚠ origin では別 commit `{tag}` を指す。SHA を正本とする。")
    else:
        L.append("- 凍結タグ `evidence-freeze-2026-09`: **origin に未作成（pending）**。作成されるまでは SHA を使う。")
    L.append(f"- 復元手順: `git restore --source={freeze_sha} -- <path>`（SHA は常に有効。タグ作成後はタグ名でも可）\n")
    L.append("## 全体\n")
    L.append(f"- 追跡ファイル数: **{len(files):,}**")
    L.append(f"- 追跡ファイル合計サイズ: **{_human(total)}**\n")
    L.append("| 最上位 | ファイル数 | サイズ |\n|---|---:|---:|")
    for k, (n, s) in sorted(by_top.items(), key=lambda kv: -kv[1][1]):
        L.append(f"| `{k}` | {n:,} | {_human(s)} |")
    L.append("\n### 大きいサブディレクトリ（rooms / app / ai_lab）\n")
    L.append("| パス | ファイル数 | サイズ |\n|---|---:|---:|")
    for k, (n, s) in sorted(by_sub.items(), key=lambda kv: -kv[1][1])[:15]:
        L.append(f"| `{k}` | {n:,} | {_human(s)} |")
    L.append("\n### 大きいファイル上位 20\n")
    L.append("| ファイル | サイズ |\n|---|---:|")
    for p, s in sorted(files, key=lambda x: -x[1])[:20]:
        L.append(f"| `{p}` | {_human(s)} |")

    L.append("\n## 自動生成の候補部屋（`rooms/candidates/`）\n")
    L.append(f"- 部屋数: **{sum(cand['model'].values()):,}**\n")
    L.append("| genesis_model（白） | 部屋数 |\n|---|---:|")
    for k, v in cand["model"].most_common():
        L.append(f"| `{k}` | {v:,} |")
    for key, label in (("reached", "reached_level"), ("candidate", "candidate_level")):
        L.append(f"\n| {label} | 部屋数 |\n|---|---:|")
        for k, v in sorted(cand[key].items()):
            L.append(f"| {k} | {v:,} |")
    L.append("\n> 読み方（測定事実のみ）：候補部屋のほぼ全てが同じ白 `g001_ginzburg_landau_quench`（TDGL）。")
    L.append("> この白の天井は `docs/WHITE_CEILINGS.md` で **L2**（運動量/移流が無い）と既に測定されている。")
    L.append("> candidate_level 3 の由来と、名無し変化 X-… の正体は P2（宝の監査）で 0 から再実行して検証する。")
    L.append("> ここでは価値判断をしない。\n")

    L.append("## コミットの内訳\n")
    s = _COMMIT_STATS
    L.append(f"- 期間 {s['window']}: 合計 **{s['total']:,}** コミット、うち人間アカウント **{s['human_account']}**"
             f"（約 {100 * s['human_account'] / s['total']:.0f}%）、`aeterna-dream-bot` 単独で {s['aeterna_dream_bot']:,}。")
    L.append(f"- 最後の人間コミット: {s['last_human_commit']}")
    L.append(f"- 出典: {s['source']}（ローカル clone は shallow のため git log では再計算できない）\n")

    L.append("## GitHub Actions の trigger（この棚卸し時点）\n")
    L.append("| workflow | trigger |\n|---|---|")
    for name, trig in workflow_triggers():
        mark = " ⏸" if name in _BOT_WORKFLOWS else ""
        L.append(f"| `{name}`{mark} | {trig} |")
    L.append("\n⏸ = 2026-09 再始動のため自動 trigger を外し、手動（`workflow_dispatch`）のみにした bot。")
    L.append("元の trigger は凍結 commit の各 `.yml` に残っている。")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="docs/INVENTORY_2026-09.md")
    ap.add_argument("--freeze-sha", required=True,
                    help="immutable freeze-point commit (the evidence baseline); counts always come from HEAD")
    a = ap.parse_args()
    sha = _git("rev-parse", "--verify", a.freeze_sha + "^{commit}").strip()
    head = _git("rev-parse", "HEAD").strip()
    out = _REPO / a.out
    out.write_text(render(sha, head), encoding="utf-8")
    print(f"wrote {out.relative_to(_REPO)}")


if __name__ == "__main__":
    main()
