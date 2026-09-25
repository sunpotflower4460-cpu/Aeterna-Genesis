"""Claude Code bridge: send a proposal card or a message into the running lab (used by /guide).

    python -m tools.lab.propose --parent A --set F=0.040 --why "…" --predict "…" --put-in "…"
    python -m tools.lab.propose --parent B --perturb cut_half --why "…"
    python -m tools.lab.propose --say "（会議に出す文章）"

The lab validates every card against the white's registry (law knobs and ranges only) and never runs it:
a person presses 試す in the app.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _post(base: str, path: str, body: dict, token: str | None) -> dict:
    req = urllib.request.Request(base.rstrip("/") + path, method="POST", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **({"X-Lab-Token": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ラボが断りました ({e.code}): {json.loads(e.read()).get('error')}") from None
    except urllib.error.URLError as e:
        raise SystemExit(f"ラボに届きません（python -m tools.lab.server は動いていますか）: {e.reason}") from None


def _pairs(items: list[str]) -> dict[str, float]:
    out = {}
    for it in items:
        k, _, v = it.partition("=")
        out[k.strip()] = float(v)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lab", default=os.environ.get("LAB_URL", "http://127.0.0.1:8765"))
    ap.add_argument("--token", default=os.environ.get("LAB_TOKEN"))
    ap.add_argument("--say", help="会議に出す文章（Claude Code の発言として表示）")
    ap.add_argument("--parent", help="親の宇宙のラベル（A, B, …）")
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE")
    ap.add_argument("--perturb", help="cut_half / kick / drop_seed")
    ap.add_argument("--arg", action="append", default=[], metavar="NAME=VALUE", help="摂動の引数")
    ap.add_argument("--why", default="")
    ap.add_argument("--predict", default="")
    ap.add_argument("--put-in", default="")
    a = ap.parse_args(argv)
    if a.say:
        _post(a.lab, "/api/council/external", {"who": "claude-code", "text": a.say}, a.token)
        print("会議に出しました")
    if a.parent:
        body = {"source": "claude-code", "parent": a.parent, "set": _pairs(a.set), "why": a.why, "predict": a.predict,
                "put_in": a.put_in, "perturb": {"name": a.perturb, "args": _pairs(a.arg)} if a.perturb else None}
        p = _post(a.lab, "/api/proposals", body, a.token)
        print(f"提案カード #{p['id']} を出しました（{p['parent_label']} から: set={p['set']} perturb={p['perturb']}）。実行はアプリで人が押したときだけ。")
    if not a.say and not a.parent:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
