"""やさしい説明: what a goal is doing, in words a complete beginner can read -- made MECHANICALLY from the
goal, its measured evaluation, its sweeps and who is doing what. No AI is needed (and nothing is guessed):
every sentence comes from a number the lab already has. An AI may be asked to rephrase it (server), but this
text is always there and always true to the measurements.
"""
from __future__ import annotations

from typing import Any

METRIC_WORDS = {
    "spots": "点（まとまり）の数", "area": "まとまりの広さ", "speed": "まとまりが動く速さ", "v_mass": "模様の量",
    "defects": "渦（うず）の数", "mean_amp": "場の平均の強さ", "peaks": "山の数", "amax": "いちばん高い山の高さ",
    "mean_density": "平均の濃さ", "core_voxels": "輪の芯の大きさ", "cy": "まとまりの縦の位置", "cx": "まとまりの横の位置",
    "energy": "エネルギーの合計", "mean_phi": "場の平均", "walls": "壁（谷と谷の境目）の多さ", "lumps": "エネルギーの塊の数",
    "lump_size": "塊の大きさ", "vortices": "渦の数", "net_winding": "渦の向きの合計", "gauss": "ガウスの法則のずれ",
    "flux_per_vortex": "渦 1 本あたりの磁束（2π を 1 とする）",
}
OP_WORDS = {"==": "ちょうど {v}", "!=": "{v} 以外", ">": "{v} より大きい", ">=": "{v} 以上", "<": "{v} より小さい",
            "<=": "{v} 以下"}
STATE_WORDS = {"running": "調べている", "finished": "調べ終えた", "stopped": "止められた", "over_budget": "予算を使い切って止まった",
               "error": "うまく動かなかった", "starting": "準備している"}


def criterion_words(c: dict[str, Any]) -> str:
    m = METRIC_WORDS.get(c["metric"], c["metric"])
    op = OP_WORDS.get(c["op"], c["op"] + " {v}").format(v=f"{c['value']:g}")
    hold = f"、それが {c['hold']:g} 時間つづく" if c.get("hold") else ""
    return f"{m}が {op}{hold}"


def goal_plain(goal: dict[str, Any], evaluation: dict[str, Any] | None, now: list[dict[str, Any]],
               researchers: list[dict[str, Any]], hypothesis: dict[str, Any] | None = None) -> list[str]:
    """A handful of short sentences, most important first."""
    out: list[str] = []
    what = hypothesis["idea"] if hypothesis else (goal.get("question") or goal["title"])
    out.append(f"🎯 さがしているもの：{what}")
    if goal["criteria"]:
        out.append("✅ 見つかったと言える目安：" + "、そして ".join(criterion_words(c) for c in goal["criteria"])
                   + "。（数字の目安で、「生きている」などの意味はありません）")
    else:
        out.append("✅ 決まった目安はありません。試したことと、そのとき数字がどう変わったかを記録していきます。")

    ev = evaluation or {"met": False, "universes": []}
    sweeps = goal.get("sweeps") or []
    tried = sum(len(s["variants"]) for s in sweeps)
    n_u = len(ev["universes"])
    counts = []
    if n_u:
        counts.append(f"水槽で {n_u} つの宇宙を見ています")
    if tried:
        counts.append(f"画面の外でまとめて {tried} 通り試しました")
    if counts:
        out.append("🔬 " + "。".join(counts) + "。")

    if goal["criteria"]:
        hits = [u["label"] for u in ev["universes"] if u["all_met"]]
        sweep_hits = [v for s in sweeps for v in s["variants"] if v.get("all_met")]
        if hits or sweep_hits:
            where = []
            if hits:
                where.append(f"水槽の宇宙 {', '.join(hits)}")
            if sweep_hits:
                where.append(f"まとめて試した {len(sweep_hits)} 通り")
            out.append(f"🎉 目安をぜんぶ満たしたもの：{'、'.join(where)}。本当にそう言えるかは、あとで人が確かめます。")
        else:
            best = max([sum(c["met"] for c in u["criteria"]) for u in ev["universes"]]
                       + [v.get("met", 0) for s in sweeps for v in s["variants"]] or [0])
            if n_u or tried:
                out.append(f"🔎 まだ見つかっていません。いちばん近いもので、目安 {len(goal['criteria'])} つのうち {best} つ。")

    for e in now[-3:]:
        who = "うえきさん" if e["actor"] == "you" else e["actor"]
        out.append(f"👀 {who}：{e['what']}")
    for r in researchers:
        if r["state"] != "running":
            out.append(f"🤖 {r['name']}は{STATE_WORDS.get(r['state'], r['state'])}。")

    b, s = goal["budget"], goal["spent"]
    used = max((s.get(k, 0) / b[lim]) if b.get(lim) else 0 for k, lim in
               (("universes", "max_universes"), ("steps", "max_steps"), ("usd", "max_usd"), ("minutes", "max_minutes")))
    out.append(f"💰 用意した予算の {min(100, round(used * 100))}% を使いました。")
    return out
