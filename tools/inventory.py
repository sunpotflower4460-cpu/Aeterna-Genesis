"""Read-only repository inventory for the 2026-09 research restart (plan phase P0).

Counts what is tracked in git (sizes, file counts, largest files), what the automated Dream
candidates actually are (which white / genesis_model, which Emergence Level), how commits split
between bots and humans, and which workflows could write to main.

Every number is read from ONE commit object (``--commit``), never from the working tree, so the
report is reproducible from any later checkout, squash or merge:

    python tools/inventory.py --commit <sha> --out docs/INVENTORY_2026-09.md
    python tools/inventory.py --commit <sha> --confirmed-freeze   # only after bots are stopped
                                                                  # and in-flight runs drained

Without ``--confirmed-freeze`` the report calls the commit a snapshot, not the freeze point.
Standard library only (no numpy / PyYAML), so it runs in a bare container. It never modifies
research data; it only writes the Markdown report given by --out.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import re
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_TAG = "evidence-freeze-2026-09"
_WINDOW_START = "2026-07-27"
_BOT_WORKFLOWS = (
    "dream-loop", "free-hypothesis-lab", "science-bridge",
    "research-maintenance", "research-postflight", "research-continuity",
)


def _git(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=_REPO, check=True, capture_output=True, text=True,
                          input=stdin).stdout


def _human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return str(n)


def remote_tag_state(tag: str) -> tuple[str, str | None]:
    """('present', sha) / ('absent', None) / ('unknown', reason) — checked on origin, not locally."""
    try:
        proc = subprocess.run(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
                              cwd=_REPO, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return "unknown", type(exc).__name__
    if proc.returncode != 0:
        return "unknown", f"git ls-remote exit {proc.returncode}"
    refs = {ref: sha for sha, ref in (line.split("\t", 1) for line in proc.stdout.splitlines() if "\t" in line)}
    sha = refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")
    return ("present", sha) if sha else ("absent", None)


def tracked_files(commit: str) -> list[tuple[str, int]]:
    out = []
    for rec in _git("ls-tree", "-r", "-l", "-z", commit).split("\0"):
        if not rec:
            continue
        meta, path = rec.split("\t", 1)
        size = meta.split()[3]
        out.append((path, int(size) if size.isdigit() else 0))  # submodules report "-"
    return out


def _top(path: str) -> str:
    return path.split("/")[0] + "/" if "/" in path else "(root files)"


def candidate_rooms(commit: str) -> dict[str, collections.Counter]:
    """Tally genesis_model and levels from rooms/candidates/<dir>/room.yaml (flat keys, regex only)."""
    stats = {"model": collections.Counter(), "reached": collections.Counter(), "candidate": collections.Counter()}
    listing = _git("ls-tree", "-d", "-z", "--name-only", commit, "rooms/candidates/")
    dirs = sorted(p for p in listing.split("\0") if p)  # directories only: README.md etc. are skipped
    if not dirs:
        return stats
    batch = subprocess.run(["git", "cat-file", "--batch"], cwd=_REPO, check=True, capture_output=True,
                           input="".join(f"{commit}:{d}/room.yaml\n" for d in dirs).encode()).stdout
    pos = 0
    for _ in dirs:
        nl = batch.index(b"\n", pos)
        header = batch[pos:nl].decode()
        pos = nl + 1
        if header.endswith(" missing"):
            stats["model"]["(no room.yaml)"] += 1
            continue
        size = int(header.split()[2])
        body = batch[pos:pos + size].decode("utf-8", "replace")
        pos += size + 1  # object bytes + trailing LF
        m = re.search(r"^genesis_model:\s*(\S+)", body, re.M)
        stats["model"][m.group(1) if m else "(unknown)"] += 1
        m = re.search(r"^\s+reached_level:\s*(\S+)", body, re.M)
        stats["reached"][m.group(1) if m else "(none)"] += 1
        m = re.search(r"^\s+candidate_level:\s*(\S+)", body, re.M)
        stats["candidate"][m.group(1) if m else "(none)"] += 1
    return stats


def commit_stats(commit: str) -> dict:
    rows = [line.split("\t") for line in
            _git("log", commit, f"--since={_WINDOW_START}", "--format=%an\t%cI").splitlines() if line]
    authors = collections.Counter(a for a, _ in rows)
    humans = [(a, d) for a, d in rows if not a.endswith("-bot")]
    oldest = _git("log", "--reverse", "--format=%cI", commit).splitlines()[:1]
    shallow = _git("rev-parse", "--is-shallow-repository").strip() == "true"
    truncated = bool(shallow and oldest and oldest[0][:10] > _WINDOW_START)
    return {"authors": authors, "total": len(rows), "last_human": max((d for _, d in humans), default=None),
            "end": _git("log", "-1", "--format=%cI", commit).strip(), "truncated": truncated,
            "oldest": oldest[0] if oldest else None}


def workflow_triggers(commit: str) -> list[tuple[str, str]]:
    rows = []
    names = _git("ls-tree", "-z", "--name-only", commit, ".github/workflows/").split("\0")
    for path in sorted(p for p in names if p.endswith((".yml", ".yaml"))):
        text = _git("show", f"{commit}:{path}")
        block = re.search(r"^on:\n((?:[ #].*\n|\n)*)", text, re.M)
        keys = re.findall(r"^  ([a-z_]+):", block.group(1), re.M) if block else []
        writes_main = "git push origin HEAD:main" in text
        rows.append((Path(path).stem, ", ".join(keys) + (" · run 内で main へ push" if writes_main else "")))
    return rows


def render(commit: str, confirmed: bool, drain_note: str | None = None) -> str:
    files = tracked_files(commit)
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
    cand = candidate_rooms(commit)
    cs = commit_stats(commit)
    tree = _git("rev-parse", f"{commit}^{{tree}}").strip()
    when = _git("log", "-1", "--format=%cI %an", commit).strip()

    L = []
    L.append("# INVENTORY 2026-09 — 再始動前の棚卸し（P0）\n")
    L.append(f"生成: `python tools/inventory.py --commit {commit[:12]}{' --confirmed-freeze' if confirmed else ''}` · "
             f"{dt.date.today().isoformat()} · 読み取りのみ。**全ての数値は下の commit オブジェクトから数えた**"
             "（作業ツリーは見ない）。\n")
    L.append("## 測定した commit と凍結点\n")
    L.append(f"- 測定 commit: `{commit}`（tree `{tree}`、{when}）")
    if confirmed:
        L.append("- **凍結点として確定**：bot の自動 trigger 停止と、実行中・待機中 run の排出を確認した後の `main` 先頭。")
        if drain_note:
            L.append(f"- 排出の確認: {drain_note}")
        L.append(f"- 復元手順: `git restore --source={commit} -- <path>`（SHA は不変。タグ作成後はタグ名でも可）")
    else:
        L.append("- ⚠ **凍結点は未確定（スナップショット）**：この時点では bot がまだ動きうるため、この commit の後にも")
        L.append("  証拠が追加されうる。bot 停止と run の排出を確認してから `--confirmed-freeze` で再生成し、凍結点を確定する。")
    state, info = remote_tag_state(_TAG)
    if state == "present" and info == commit:
        L.append(f"- 凍結タグ `{_TAG}`: origin に存在し、この commit を指す（確認済み）")
    elif state == "present":
        L.append(f"- 凍結タグ `{_TAG}`: origin に存在するが別 commit `{info}` を指す。SHA を正本とする。")
    elif state == "absent":
        L.append(f"- 凍結タグ `{_TAG}`: origin に**未作成**（`git ls-remote` で確認）。作成されるまでは SHA を使う。")
    else:
        L.append(f"- 凍結タグ `{_TAG}`: **確認できず**（{info}）。有無は不明として扱い、SHA を正本とする。")
    L.append("")

    L.append("## 全体\n")
    L.append(f"- 追跡ファイル数: **{len(files):,}**")
    L.append(f"- 追跡ファイル合計サイズ: **{_human(total)}**（git blob サイズの合計）\n")
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
    L.append(f"- 部屋数（ディレクトリ数）: **{sum(cand['model'].values()):,}**\n")
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
    L.append(f"期間: {_WINDOW_START} 〜 {cs['end']}（測定 commit から到達できる履歴を `git log` で数えた）\n")
    L.append("| 作者 | コミット数 |\n|---|---:|")
    for a, n in cs["authors"].most_common():
        L.append(f"| `{a}` | {n:,} |")
    human = sum(n for a, n in cs["authors"].items() if not a.endswith("-bot"))
    L.append(f"\n- 合計 **{cs['total']:,}**、うち `*-bot` 以外 **{human:,}**"
             f"（約 {100 * human / max(cs['total'], 1):.0f}%）。最後の `*-bot` 以外のコミット: {cs['last_human']}")
    if cs["truncated"]:
        L.append(f"- ⚠ ローカル履歴が shallow で、最古の commit が {cs['oldest']}。期間の始まりまで届かないため、"
                 "上の数は下限。")
    L.append("")

    L.append("## GitHub Actions の trigger（測定 commit 時点）\n")
    L.append("| workflow | trigger |\n|---|---|")
    for name, trig in workflow_triggers(commit):
        mark = " ⏸" if name in _BOT_WORKFLOWS else ""
        L.append(f"| `{name}`{mark} | {trig} |")
    L.append("\n⏸ = P0（2026-09 再始動）で自動 trigger を外し、手動（`workflow_dispatch`）のみにする bot。")
    L.append("上の表は測定 commit 時点の trigger をそのまま示す。停止前の trigger は、P0 より前の commit の各 `.yml` に残っている。")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", required=True, help="commit to measure (every number comes from this object)")
    ap.add_argument("--confirmed-freeze", action="store_true",
                    help="mark the commit as the confirmed freeze point (bots stopped, in-flight runs drained)")
    ap.add_argument("--drain-note", help="how the drain was verified (time, method); printed with --confirmed-freeze")
    ap.add_argument("--out", default="docs/INVENTORY_2026-09.md")
    a = ap.parse_args()
    sha = _git("rev-parse", "--verify", a.commit + "^{commit}").strip()
    out = _REPO / a.out
    out.write_text(render(sha, a.confirmed_freeze, a.drain_note), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
