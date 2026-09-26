"""AI researchers: inside ONE goal's bounds, an AI tries things by itself -- and nothing else.

    person sets a goal (question, measured criteria, allowed whites, budget)  ->  presses 「研究を始める」
    -> 1..3 researchers, each its own thread and its own model, share the goal's budget and map

What a researcher can do (the only tools it is given):
    create_universe  new universe of an ALLOWED white (start knobs in range)            -> put in by <name>
    branch           copy a universe's current state, change law knobs / perturb once   -> put in by <name>
    run              advance ITS OWN universe by N frames (every frame measured)
    observe          the 事件簿 (measured series + rule-based events) of any universe, as text
    evaluate_goal    the goal's criteria, judged from measurements only
    note             a node on the goal's map (question / note / result)
    propose          a proposal card for the person (never executed by itself)
    close_universe   close ITS OWN universe
    finish           stop, with a summary

What it can NOT do: touch code, files, git, other goals, universes it did not make (other than reading
and branching from them), or anything outside the allowed whites / knob ranges / budget. Every universe it
makes is recorded as PUT IN by that researcher (journal, map, activity). Stopping is always possible: the
stop flag is checked before every tool call, and a stopped researcher's tools refuse. Nothing a researcher
writes is a claim; claims go through replay + /audit by a person.
"""
from __future__ import annotations

import datetime as _dt
import json
import threading
import time
from typing import Any, Callable

from tools.lab import goals as goalmod
from tools.lab import observe, sweep, whites
from tools.lab.council import (RULES, TOOL_CAPABLE, Usage, _entry_key, check_branch, model_catalog,
                               provider_for, uid_of)

MAX_FRAMES = 300          # per run call
MAX_TURNS = 24            # converse() calls per researcher (each is up to ROUNDS tool rounds)
ROUNDS = 8
TRANSCRIPT = 400          # entries kept per researcher

_CHANGES = {"type": "array", "description": "場の法則のつまみ（無ければ空）",
            "items": {"type": "object", "additionalProperties": False, "required": ["knob", "value"],
                      "properties": {"knob": {"type": "string"}, "value": {"type": "number"}}}}
_PARGS = {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "value"],
                                     "properties": {"name": {"type": "string"}, "value": {"type": "number"}}}}


def _tool(name: str, description: str, props: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "strict": True, "description": description,
            "input_schema": {"type": "object", "additionalProperties": False, "required": list(props),
                             "properties": props}}


RESEARCHER_TOOLS = [
    _tool("create_universe", "許された白で、新しい宇宙を t=0 から作る（一時停止の状態）。あなたが『置いた』ものとして記録される。",
          {"white": {"type": "string"}, "seed": {"type": "integer"},
           "knobs": {**_CHANGES, "description": "つまみ（場の法則・始め方。無ければ空＝既定値）"},
           "why": {"type": "string", "description": "なぜこの宇宙を作るか（1 文）"},
           "under": {"type": "string", "description": "マップの親ノード id（n3 など）。無ければ空文字"}}),
    _tool("branch", "宇宙のいまの状態を複製し、場の法則のつまみ変更か摂動だけを変えた新しい宇宙を作る（一時停止）。",
          {"parent": {"type": "string", "description": "宇宙のラベル（A, B, …）"}, "changes": _CHANGES,
           "perturb": {"type": "string", "description": "摂動の名前。無ければ空文字"}, "perturb_args": _PARGS,
           "why": {"type": "string"}, "under": {"type": "string", "description": "マップの親ノード id か空文字"}}),
    _tool("sweep", f"まとめて試す：画面に出さずに、つまみ（と seed）の組み合わせを最大 {sweep.MAX_VARIANTS} 通り t=0 から回し、"
          "ゴールの条件にどれだけ近いかの順に並べて返す。たくさんのパターンを安く試すときに使う。"
          "見込みのある組み合わせは create_universe で水槽に出して見る。",
          {"white": {"type": "string"},
           "base": {**_CHANGES, "description": "全部に共通のつまみ（無ければ空）"},
           "vary": {"type": "array", "description": "振るつまみと、その値の一覧",
                    "items": {"type": "object", "additionalProperties": False, "required": ["knob", "values"],
                              "properties": {"knob": {"type": "string"},
                                             "values": {"type": "array", "items": {"type": "number"}}}}},
           "seeds": {"type": "array", "items": {"type": "integer"}, "description": "seed の一覧（空なら 0 だけ）"},
           "frames": {"type": "integer", "description": f"1 通りあたりのコマ数（1〜{sweep.MAX_FRAMES}）"},
           "why": {"type": "string"},
           "plain": {"type": "string", "description": "超初心者向けに、何を試すのかを 1 文で"}}),
    _tool("run", f"自分が作った宇宙を frames コマ進める（1〜{MAX_FRAMES}）。コマごとに測定される。",
          {"universe": {"type": "string"}, "frames": {"type": "integer"}}),
    _tool("observe", "宇宙の事件簿（測定の時系列と、規則で検出した出来事）を文章で読む。",
          {"universe": {"type": "string"}}),
    _tool("evaluate_goal", "ゴールの条件を、測定だけで判定する（宇宙ごとに、どの条件を満たしたか）。", {}),
    _tool("note", "ゴールのマップに書く。kind は question（小さな問い）/ note（気づき）/ result（結果）。",
          {"kind": {"type": "string", "enum": ["question", "note", "result"]}, "text": {"type": "string"},
           "plain": {"type": "string", "description": "超初心者向けの言いかえ（専門用語なし・1〜2 文）"},
           "status": {"type": "string", "enum": ["todo", "doing", "met", "not_met", "ceiling", "info"]},
           "under": {"type": "string", "description": "親ノード id か空文字"},
           "universe": {"type": "string", "description": "関係する宇宙のラベルか空文字"}}),
    _tool("propose", "うえきさんへの提案カードを出す（実行はしない）。予算の外のことや、人に決めてほしいことに使う。",
          {"parent": {"type": "string"}, "changes": _CHANGES, "perturb": {"type": "string"}, "perturb_args": _PARGS,
           "why": {"type": "string"}, "predict": {"type": "string"}, "put_in": {"type": "string"}}),
    _tool("close_universe", "自分が作った宇宙を閉じる（CPU を空ける）。記録は残る。", {"universe": {"type": "string"}}),
    _tool("finish", "研究を終える。summary に、試したこと・測定で分かったこと・分からなかったことを書く。",
          {"summary": {"type": "string"},
           "plain": {"type": "string", "description": "超初心者向けのまとめ（専門用語なし・2〜3 文）"},
           "outcome": {"type": "string", "enum": ["met", "not_met", "ceiling", "info"]}}),
]

BRIEF = RULES + """

あなたはこのラボの「研究員」です。うえきさんが決めたゴールの範囲の中でだけ、自分で宇宙を作り・分岐し・進め・観測して試します。
- 使えるのは渡された道具だけ。許された白・つまみの範囲・予算の外には出られません（道具が断ります）。
- あなたが作った宇宙・分岐・摂動は、すべて「あなたが置いたもの」として記録されます。
- 条件を満たしたかどうかは evaluate_goal（測定）だけが決めます。見た目や期待で「できた」と言わないこと。
- たくさんのパターンは sweep（まとめて試す）で安く試し、見込みのあるものだけ create_universe で水槽に出して run → observe する。
- 分かったことはこまめに note でマップに書く。note と finish の plain には、専門用語を使わず、中学生にも分かる言葉で書く
  （例：「点が 1 つのまま動き続ける宇宙を探して、24 通り試しました。θ を小さくすると、点が割れにくくなりました」）。
- 他の研究員もいます。マップと「いまやっていること」を見て、同じことを重ねないようにしてください。
- 条件を満たした、予算が尽きそう、この白の天井だと判断した、のどれかで finish。天井や失敗も立派な結果です。
- 書くことはすべて観察の記録であって主張ではありません（主張は人が replay と /audit を通してから）。"""


def _now() -> str:
    return _dt.datetime.now().strftime("%H:%M:%S")


class Stopped(Exception):
    pass


def _kv(d: dict[str, Any]) -> str:
    return ", ".join(f"{k}={v:g}" if isinstance(v, (int, float)) else f"{k}={v}" for k, v in (d or {}).items())


def _push_user(history: list[dict[str, Any]], text: str) -> None:
    """Add a user turn. If the tool loop ran out of rounds, the last turn is already the user's tool results
    (Anthropic format): the text joins that turn instead of making two user turns in a row."""
    last = history[-1] if history else None
    if last and last.get("role") == "user" and isinstance(last.get("content"), list):
        last["content"].append({"type": "text", "text": text})
    else:
        history.append({"role": "user", "content": text})


def white_sheet(white_ids: list[str]) -> str:
    """What the researcher needs to know about each allowed white: knobs with ranges, perturbations,
    measured quantities, steps per frame, and what is put in."""
    lines = []
    for wid in white_ids:
        w = whites.get(wid)
        lines.append(f"■ {w.id}（{w.title}、{w.dimension}D、格子 {'×'.join(map(str, w.grid))}、1 コマ = {w.steps_per_frame} step）")
        for k in w.knobs:
            lines.append(f"  つまみ {k.name}（{k.label}、{'場の法則' if k.kind == 'law' else '始め方・作るときだけ'}）"
                         f" 既定 {k.default:g} 範囲 [{k.lo:g}, {k.hi:g}]")
        for p in w.perturbs:
            args = ", ".join(f"{a.name}∈[{a.lo:g},{a.hi:g}]" for a in p.args)
            lines.append(f"  摂動 {p.name}（{p.label}）{args}")
        lines.append(f"  測定値: {', '.join(goalmod.metrics_of(wid))}")
        lines.append(f"  置いてあるもの: {'; '.join(w.put_in)}")
    return "\n".join(lines)


def goal_sheet(g: dict[str, Any]) -> str:
    crit = "\n".join(f"  - {c['metric']} {c['op']} {c['value']:g} を {c['hold']:g} 時間単位つづけて"
                     + (f"（{c['label']}）" if c.get("label") else "") for c in g["criteria"]) or "  （条件なし）"
    b = g["budget"]
    hyp = ""
    if g.get("hypothesis"):
        try:
            h = goalmod.hypothesis(g["hypothesis"])
            hyp = (f"仮説 {h['id']}（{h['title']}）: {h['idea']}\n測り方: {h['measure']}\n反証になること: {h['falsify']}\n"
                   f"置いたもの: {h['put_in']}\n" + (f"まだ足りないもの: {h['needs']}\n" if h.get("needs") else ""))
        except KeyError:
            pass
    return (f"ゴール {g['id']}: {g['title']}\n{hyp}問い: {g['question'] or '（なし）'}\n条件（1 つの宇宙で全部を同時に）:\n{crit}\n"
            f"予算（研究員全員で共有）: 宇宙 {b['max_universes']:g} 個、計算 {b['max_steps']:g} step、"
            f"${b['max_usd']:g}、{b['max_minutes']:g} 分")


class Researcher:
    """One AI researcher on one goal. Runs in its own thread; `stop()` is honoured before every tool call."""

    def __init__(self, runner: "GoalRunner", gid: str, spec: dict[str, Any], provider):
        self.runner, self.gid, self.spec, self.provider = runner, gid, spec, provider
        self.name = spec["name"]
        self.state = "starting"          # starting / running / finished / stopped / over_budget / error
        self.reason = ""
        self.transcript: list[dict[str, Any]] = []
        self.owned: list[str] = []       # universe ids this researcher made
        self.usd = 0.0
        self.usage = Usage()
        self._stop = threading.Event()
        self._finished = False
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._main, daemon=True, name=f"researcher-{gid}-{self.name}")

    # ------------------------------------------------------------------ bookkeeping
    def _say(self, kind: str, text: str) -> None:
        with self._lock:
            if kind == "text" and self.transcript and self.transcript[-1]["kind"] == "text" and not self.transcript[-1].get("closed"):
                self.transcript[-1]["text"] += text
                return
            if self.transcript and self.transcript[-1]["kind"] == "text":
                self.transcript[-1]["closed"] = True
            self.transcript.append({"at": _now(), "kind": kind, "text": text})
            del self.transcript[:-TRANSCRIPT]

    def public(self) -> dict[str, Any]:
        with self._lock:
            tr = [dict(e) for e in self.transcript]
        return {"name": self.name, "model": self.provider.model if self.provider else "", "focus": self.spec.get("focus", ""),
                "state": self.state, "reason": self.reason, "owned": list(self.owned), "usd": round(self.usd, 4),
                "tokens": {"input": self.usage.input_tokens, "output": self.usage.output_tokens}, "transcript": tr}

    def start(self) -> None:
        self.state = "running"
        self.runner.book.log(self.gid, self.name, "研究を始めた")
        self.thread.start()

    def stop(self, why: str = "止めるボタン") -> None:
        self.reason = self.reason or why
        self._stop.set()

    # ------------------------------------------------------------------ the loop
    def _system(self) -> str:
        g = self.runner.book.get(self.gid)
        allowed = g["whites"] or list(whites.registry())
        focus = f"\nあなたの担当・観点: {self.spec['focus']}" if self.spec.get("focus") else ""
        return (BRIEF + f"\n\nあなたの名前: {self.name}{focus}\n\n" + goal_sheet(g)
                + "\n\n使ってよい白:\n" + white_sheet(allowed))

    def _situation(self) -> str:
        g = self.runner.book.get(self.gid)
        s, b = g["spent"], g["budget"]
        now = "; ".join(f"{e['actor']}: {e['what']}" for e in self.runner.book.now_doing(self.gid))
        nodes = "\n".join(f"  {n['id']} [{n['kind']}/{n['status']}] ({n['by']}) {n['text'][:120]}" for n in g["nodes"][-30:])
        labels = ", ".join(f"{self.runner.hub.info(u)['label']}（{self.runner.hub.info(u)['white']}、"
                           f"{'あなた' if u in self.owned else '他'}、t={self.runner.hub.info(u)['t']:.4g}）"
                           for u in self.runner.hub.ids())
        return (f"いまの状況（{_now()}）\n使った予算: 宇宙 {s['universes']:g}/{b['max_universes']:g}、"
                f"計算 {s['steps']:g}/{b['max_steps']:g} step、${s['usd']:.3f}/{b['max_usd']:g}、{s['minutes']:.1f}/{b['max_minutes']:g} 分\n"
                f"いる宇宙: {labels or 'なし'}\nいまやっていること: {now or 'なし'}\nマップ（新しい 30 件）:\n{nodes or '  （空）'}")

    def _main(self) -> None:
        history: list[dict[str, Any]] = [{"role": "user", "content": self._situation() + "\n\nはじめてください。"}]
        system = self._system()
        wrap_up = False
        try:
            for _ in range(MAX_TURNS):
                self._check()
                u = self.provider.converse(system, history, self._tool, lambda t: self._say("text", t),
                                           max_rounds=ROUNDS, tools=RESEARCHER_TOOLS)
                self._charge(u)
                if self._finished:
                    break
                if self.runner.book.get(self.gid)["status"] == "met":
                    if wrap_up:
                        break
                    wrap_up = True
                    _push_user(history, "ゴールの条件が測定で満たされました（evaluate_goal）。"
                               "新しい宇宙は作れません。finish で、試したことと分かったことをまとめてください。")
                    continue
                self._check()
                _push_user(history, self._situation() + "\n\n続けてください。終えるときは finish を呼んでください。")
            else:
                self.reason = self.reason or f"{MAX_TURNS} 回のやりとりの上限"
            if not self._finished and self.state == "running":
                self.state = "finished"
        except Stopped as e:
            self.state = "over_budget" if str(e).startswith("上限") else "stopped"
            self.reason = self.reason or str(e)
        except Exception as e:           # a provider / network failure must not break the lab
            self.state, self.reason = "error", f"{type(e).__name__}: {str(e)[:300]}"
        self._say("system", f"— 終了（{self.state}{'：' + self.reason if self.reason else ''}）")
        self.runner.book.log(self.gid, self.name, f"研究を終えた（{self.state}）")
        self.runner._done(self)

    def _charge(self, u: Usage) -> None:
        usd = self.provider.cost(u)
        self.usage.add(u)
        self.usd += usd
        self.runner.book.spend(self.gid, usd=usd)
        if self.runner.council is not None:
            self.runner.council._charge(usd)

    def _check(self) -> None:
        if self._stop.is_set():
            raise Stopped(self.reason or "止められました")
        g = self.runner.book.get(self.gid)
        if g["status"] in ("paused", "done", "draft"):      # "met": may still observe, note and finish
            raise Stopped(f"ゴールが「{g['status']}」になりました")
        self.runner.tick(self.gid)
        over = self.runner.book.over_budget(self.gid, include_universes=False)
        if over:
            raise Stopped(over)
        if self.runner.council is not None and self.runner.council.spent_today() >= self.runner.council._limit():
            raise Stopped("上限：今日の AI の費用")

    # ------------------------------------------------------------------ tools
    def _tool(self, name: str, args: dict[str, Any]) -> str:
        self._check()                                   # raises Stopped -> ends the thread
        self._say("tool", f"{name} {json.dumps(args, ensure_ascii=False)}")
        try:
            out = self._do(name, args)
        except (ValueError, KeyError) as e:
            out = f"エラー: {e}（直して、もう一度どうぞ）"
        self._say("result", out if len(out) < 1500 else out[:1500] + " …")
        return out

    def _own(self, label: str) -> str:
        uid = uid_of(self.runner.hub, label)
        if not uid:
            raise ValueError(f"宇宙 {label} はいません")
        if uid not in self.owned:
            raise ValueError(f"宇宙 {label} はあなたが作った宇宙ではありません（読む・分岐するのは自由です）")
        return uid

    def _allowed(self, white_id: str) -> None:
        g = self.runner.book.get(self.gid)
        if g["whites"] and white_id not in g["whites"]:
            raise ValueError(f"白 {white_id} はこのゴールでは使えません（使えるのは {', '.join(g['whites'])}）")

    def _new_universe(self) -> None:
        g = self.runner.book.get(self.gid)
        if g["status"] == "met":
            raise ValueError("ゴールはもう達成されています。新しい宇宙は作れません（finish でまとめてください）")
        if g["spent"]["universes"] + 1 > g["budget"]["max_universes"]:
            raise ValueError(f"宇宙の予算（{g['budget']['max_universes']:g} 個）を使い切りました")

    def _attempt(self, uid: str, what: str, under: str) -> str:
        info = self.runner.hub.info(uid)
        node = self.runner.book.add_node(self.gid, "attempt", f"宇宙 {info['label']}: {what}", self.name,
                                         parent=under or None, universe=uid, status="doing")
        self.runner.book.log(self.gid, self.name, f"宇宙 {info['label']} を作った（{what[:80]}）", uid)
        self.runner.book.spend(self.gid, universes=1)
        return node["id"]

    def _sweep(self, a: dict[str, Any]) -> str:
        book = self.runner.book
        self._allowed(a["white"])
        g = book.get(self.gid)
        if g["status"] == "met":
            raise ValueError("ゴールはもう達成されています（finish でまとめてください）")
        base = {k["knob"]: k["value"] for k in a.get("base", [])}
        vary = {v["knob"]: list(v["values"]) for v in a.get("vary", [])}
        variants = sweep.plan(a["white"], base, vary, [int(x) for x in a.get("seeds") or []])
        frames = int(a["frames"])
        if not 1 <= frames <= sweep.MAX_FRAMES:
            raise ValueError(f"frames は 1〜{sweep.MAX_FRAMES} です")
        spf = whites.get(a["white"]).steps_per_frame
        cost = len(variants) * frames * spf
        left = g["budget"]["max_steps"] - g["spent"]["steps"]
        if cost > left:
            fit = int(left // (len(variants) * spf))
            raise ValueError(f"計算の予算が足りません（{len(variants)} 通り × {frames} コマ = {cost:g} step、残り {left:g}）。"
                             + (f"frames を {fit} 以下にするか、組み合わせを減らしてください" if fit >= 1 else "組み合わせを減らしてください"))
        plain = a.get("plain") or ""
        book.log(self.gid, self.name, f"まとめて {len(variants)} 通り試している" + (f"：{plain}" if plain else ""))
        results = sweep.run(variants, frames, g["criteria"], workers=self.runner.sweep_workers,
                            should_stop=self._stop.is_set)
        book.spend(self.gid, steps=sum(r["steps"] for r in results))
        rec = book.add_sweep(self.gid, {"by": self.name, "white": a["white"], "why": a.get("why", ""), "plain": plain,
                                        "frames": frames, "base": base, "vary": vary,
                                        "variants": [{**{k: r[k] for k in ("seed", "knobs", "met", "all_met", "score",
                                                                             "diverged", "sha256", "steps", "t", "first", "last")},
                                                      "label": sweep.label(r)} for r in results]})
        n_c = len(g["criteria"])
        best = results[0] if results else None
        summary = (f"まとめて {len(results)} 通り試した（{rec['id']}）。" +
                   (f"いちばん近いのは {sweep.label(best)}：目安 {n_c} つのうち {best['met']} つ" if best and n_c else ""))
        book.add_node(self.gid, "result", summary + (f"。{a.get('why')}" if a.get("why") else ""), self.name,
                      status="met" if any(r["all_met"] for r in results) else "info",
                      plain=plain or summary)
        rows = []
        for r in results[:12]:
            cs = "; ".join(f"{c['metric']}{c['op']}{c['value']:g}: {'○' if c['met'] else '×'}（最長 {c['longest']:g}/{c['hold']:g}）"
                           for c in r["criteria"])
            rows.append(f"  {sweep.label(r)}: {'発散' if r['diverged'] else ''} 満たした {r['met']}/{n_c} {cs} 最後 {r['last']}")
        stopped = "（途中で止められました）" if len(results) < len(variants) else ""
        return (f"まとめて試した {rec['id']}: {len(results)}/{len(variants)} 通り{stopped}。近い順:\n" + "\n".join(rows)
                + ("\n★ 条件をぜんぶ満たした組み合わせがあります。create_universe で水槽に出して確かめてください。"
                   if any(r["all_met"] for r in results) else ""))

    def _do(self, name: str, a: dict[str, Any]) -> str:
        hub, book = self.runner.hub, self.runner.book
        if name == "create_universe":
            self._allowed(a["white"])
            self._new_universe()
            knobs = whites.get(a["white"]).check_knobs({k["knob"]: k["value"] for k in a.get("knobs", [])})
            with self.runner.create_lock:
                uid = hub.create(a["white"], int(a.get("seed", 0)), knobs)
            self.owned.append(uid)
            nid = self._attempt(uid, (a.get("why") or "新しい宇宙") + (f"（{_kv(knobs)}）" if knobs else ""), a.get("under", ""))
            return f"宇宙 {hub.info(uid)['label']} を作りました（t=0、一時停止）。マップ {nid}。次は run で進めてください。"
        if name == "branch":
            parent = uid_of(hub, a["parent"])
            if not parent:
                raise ValueError(f"宇宙 {a['parent']} はいません")
            self._allowed(hub.info(parent)["white"])
            self._new_universe()
            changes = {c["knob"]: c["value"] for c in a.get("changes", [])}
            pert = {"name": a.get("perturb", ""), "args": {x["name"]: x["value"] for x in a.get("perturb_args", [])}}
            puid, body = check_branch(hub, a["parent"], changes, pert if pert["name"] else None)
            with self.runner.create_lock:
                uid = hub.branch(puid, body["set"] or None, body["perturb"])
            self.owned.append(uid)
            change = ", ".join(x for x in (_kv(body["set"]), body["perturb"] and "摂動 " + body["perturb"]["name"]) if x)
            what = f"{hub.info(puid)['label']} から分岐（{change}）: {a.get('why', '')}"
            nid = self._attempt(uid, what, a.get("under", ""))
            return f"宇宙 {hub.info(uid)['label']} を作りました（{hub.info(puid)['label']} の t={hub.info(uid)['t']:.4g} から、一時停止）。マップ {nid}。"
        if name == "sweep":
            return self._sweep(a)
        if name == "run":
            uid = self._own(a["universe"])
            frames = int(a["frames"])
            if not 1 <= frames <= MAX_FRAMES:
                raise ValueError(f"frames は 1〜{MAX_FRAMES} です")
            spf = whites.get(hub.info(uid)["white"]).steps_per_frame
            g = book.get(self.gid)
            left = g["budget"]["max_steps"] - g["spent"]["steps"]
            frames = min(frames, int(left // spf))
            if frames < 1:
                raise ValueError("計算の予算を使い切りました")
            done = 0
            label = hub.info(uid)["label"]
            book.log(self.gid, self.name, f"宇宙 {label} を {frames} コマ進めている", uid)
            out: dict[str, Any] = {}
            while done < frames:                          # in chunks, so the stop button acts quickly
                self._check()
                n = min(25, frames - done)
                out = hub.run(uid, n)
                done += n
                book.spend(self.gid, steps=n * spf)
                if out.get("diverged"):
                    break
            info = hub.info(uid)
            tail = "（数値が発散しました。計算の限界で、物理ではありません）" if out.get("diverged") else ""
            return f"宇宙 {label} を {done} コマ進めました（t={info['t']:.4g}、step {info['step']}）{tail}。測定: {info['metrics']}"
        if name == "observe":
            uid = uid_of(hub, a["universe"])
            if not uid:
                raise ValueError(f"宇宙 {a['universe']} はいません")
            return observe.build(hub, [uid], motion_frames=0)["text"]
        if name == "evaluate_goal":
            g = book.get(self.gid)
            ev = goalmod.evaluate(g, hub)
            book.record_eval(self.gid, ev)
            for p in ev["universes"]:
                if p["all_met"]:
                    for n in g["nodes"]:
                        if n["universe"] == p["universe"] and n["kind"] == "attempt" and n["status"] == "doing":
                            book.set_node(self.gid, n["id"], "met")
            rows = []
            for p in ev["universes"]:
                cs = "; ".join(f"{c['metric']}{c['op']}{c['value']:g}: {'満たした' if c['met'] else 'まだ'}"
                               f"（最長 {c['longest']:g}/{c['hold']:g}、最新 {c['last']}）" for c in p["criteria"])
                rows.append(f"  {p['label']}（{p['white']}、t={p['t']:.4g}）{'★全部満たした' if p['all_met'] else ''} {cs}")
            return (f"判定（測定だけ）: {'達成' if ev['met'] else '未達成'}\n" + ("\n".join(rows) or "  （対象の宇宙なし）"))
        if name == "note":
            uid = uid_of(hub, a["universe"]) if a.get("universe") else None
            n = book.add_node(self.gid, a["kind"], a["text"], self.name, parent=a.get("under") or None,
                              universe=uid, status=a.get("status") or "info", plain=a.get("plain") or "")
            book.log(self.gid, self.name, f"マップに書いた: {(a.get('plain') or a['text'])[:80]}", uid)
            return f"マップに {n['id']} を書きました。"
        if name == "propose":
            if self.runner.council is None:
                return "提案カードの場所がありません（このラボでは使えません）"
            changes = {c["knob"]: c["value"] for c in a.get("changes", [])}
            pert = {"name": a.get("perturb", ""), "args": {x["name"]: x["value"] for x in a.get("perturb_args", [])}}
            p = self.runner.council.add_proposal(self.name, a["parent"], changes, pert if pert["name"] else None,
                                                 a.get("why", ""), a.get("predict", ""), a.get("put_in", ""))
            book.log(self.gid, self.name, f"提案カード #{p['id']} を出した")
            return f"提案カード #{p['id']} を出しました（うえきさんが押したときだけ実行されます）。"
        if name == "close_universe":
            uid = self._own(a["universe"])
            label = hub.info(uid)["label"]
            hub.delete(uid)
            self.owned.remove(uid)
            book.log(self.gid, self.name, f"宇宙 {label} を閉じた")
            return f"宇宙 {label} を閉じました（記録は残っています）。"
        if name == "finish":
            outcome = a.get("outcome") or "info"
            book.add_node(self.gid, "result", a.get("summary", ""), self.name, status=outcome, plain=a.get("plain") or "")
            self._finished = True
            self.state = "finished"
            return "終了を受け付けました。ありがとうございました。"
        return f"unknown tool {name}"


class GoalRunner:
    """Starts / stops the researchers of each goal and keeps the goal's wall-clock minutes."""

    def __init__(self, hub, book: goalmod.GoalBook, council=None,
                 provider_factory: Callable[[dict[str, Any]], Any] | None = None):
        self.hub, self.book, self.council = hub, book, council
        self.provider_factory = provider_factory or self._provider
        self.create_lock = threading.Lock()
        self.sweep_workers: int | None = None        # None: CPU count - 1 (tests use 1: in-process)
        self._lock = threading.RLock()
        self._teams: dict[str, list[Researcher]] = {}
        self._clock: dict[str, float] = {}           # goal -> monotonic time of the last minutes accounting

    def _provider(self, spec: dict[str, Any]):
        cfg = self.council.config if self.council is not None else {}
        cat = {e["key"]: e for e in model_catalog(cfg)}
        entry = cat.get(spec.get("model") or _entry_key(cfg.get("core") or {}))      # none chosen: the core's model
        if entry is None:
            raise ValueError(f"model {spec.get('model') or '（未選択）'} が一覧にありません")
        if entry["provider"] not in TOOL_CAPABLE:
            raise ValueError(f"{entry['key']} は道具（function calling）を使えないので研究員になれません")
        prov = provider_for("core", entry)
        ok, why = prov.available()
        if not ok:
            raise ValueError(f"{entry['key']}: {why}")
        return prov

    def tick(self, gid: str) -> None:
        with self._lock:
            now = time.monotonic()
            last = self._clock.get(gid)
            self._clock[gid] = now
        if last is not None and now > last:
            self.book.spend(gid, minutes=(now - last) / 60.0)

    def running(self, gid: str) -> list[Researcher]:
        with self._lock:
            return [r for r in self._teams.get(gid, []) if r.thread.is_alive()]

    def start(self, gid: str) -> list[dict[str, Any]]:
        """Start every researcher of the goal that is not already running. Errors (no key, model without
        tools) are reported per researcher; the others still start."""
        g = self.book.get(gid)
        over = self.book.over_budget(gid)
        if over:
            raise ValueError(over)
        specs = g["researchers"] or [{"name": "研究員1", "model": "", "focus": ""}]
        out = []
        with self._lock:
            alive = {r.name for r in self.running(gid)}
            team = [r for r in self._teams.get(gid, []) if r.name in alive]
            self._clock[gid] = time.monotonic()
            for spec in specs:
                if spec["name"] in alive:
                    continue
                try:
                    prov = self.provider_factory(spec)
                except ValueError as e:
                    out.append({"name": spec["name"], "state": "error", "reason": str(e)})
                    self.book.log(gid, spec["name"], f"始められません: {e}")
                    continue
                r = Researcher(self, gid, spec, prov)
                team.append(r)
                r.start()
                out.append({"name": r.name, "state": r.state, "reason": ""})
            self._teams[gid] = team
        return out

    def stop(self, gid: str, name: str | None = None, why: str = "止めるボタン") -> int:
        n = 0
        with self._lock:
            for r in self._teams.get(gid, []):
                if (name is None or r.name == name) and r.thread.is_alive():
                    r.stop(why)
                    n += 1
        return n

    def _done(self, r: Researcher) -> None:
        with self._lock:
            if not self.running(r.gid) or all(x is r or not x.thread.is_alive() for x in self._teams.get(r.gid, [])):
                self.tick(r.gid)
                self._clock.pop(r.gid, None)

    def status(self, gid: str) -> list[dict[str, Any]]:
        with self._lock:
            team = list(self._teams.get(gid, []))
        return [r.public() for r in team]

    def join(self, gid: str, timeout: float = 30.0) -> None:
        end = time.monotonic() + timeout
        for r in list(self._teams.get(gid, [])):
            r.thread.join(max(0.0, end - time.monotonic()))

    def close(self) -> None:
        with self._lock:
            for team in self._teams.values():
                for r in team:
                    r.stop("ラボを閉じた")
