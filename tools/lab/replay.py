"""Replay an exported lab record from t=0 and check it is the same universe (sha256 of the final state).

    python -m tools.lab.replay research/sessions/<id>                 # all universes
    python -m tools.lab.replay research/sessions/<id> --universe B    # one
    python -m tools.lab.replay research/sessions/<id> --packet /tmp/pk # also rebuild the observation packet

Exit code 1 if any universe does not reproduce. This is the first step from "seen in the lab" to a claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.lab.universe import replay


def check(record_dir: Path, only: list[str] | None = None) -> list[dict]:
    meta = json.loads((record_dir / "recipes.json").read_text(encoding="utf-8"))
    out = []
    for row in meta["universes"]:
        if only and row["label"] not in only:
            continue
        u = replay(row["recipe"], row["step"])
        out.append({"label": row["label"], "white": row["white"], "step": row["step"],
                    "expected": row["sha256"], "got": u.sha256(), "ok": u.sha256() == row["sha256"]})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", type=Path)
    ap.add_argument("--universe", action="append", help="label (repeatable)")
    ap.add_argument("--packet", type=Path, help="rebuild the observation packet from the replayed recipes here")
    a = ap.parse_args(argv)
    results = check(a.record, a.universe)
    for r in results:
        print(f"{'OK ' if r['ok'] else 'NG '} 宇宙 {r['label']}（{r['white']}）step {r['step']}  sha256 {r['got'][:16]}…"
              + ("" if r["ok"] else f"  （記録は {r['expected'][:16]}…）"))
    if a.packet:
        from tools.lab import observe
        from tools.lab.hub import LocalHub
        meta = json.loads((a.record / "recipes.json").read_text(encoding="utf-8"))
        hub = LocalHub()
        ids = [hub.replay_into(r["recipe"], r["step"], r["label"]) for r in meta["universes"]
               if not a.universe or r["label"] in a.universe]
        print(observe.save(observe.build(hub, ids), a.packet) / "packet.md")
    bad = [r for r in results if not r["ok"]]
    print("すべて t=0 から同じ状態に戻った" if not bad and results else f"{len(bad)} 個が一致しなかった")
    return 1 if bad or not results else 0


if __name__ == "__main__":
    sys.exit(main())
