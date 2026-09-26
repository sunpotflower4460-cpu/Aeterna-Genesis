"""Goals of the lab: a question, conditions that MEASUREMENTS decide, what is allowed, and the map of attempts.

    goal       "Q1: 一つの白で、まとまりと自分で動くことを同時に"  (question in words)
    criteria   [{"metric": "spots", "op": "==", "value": 1, "hold": 50},       # measured, per universe,
                {"metric": "speed", "op": ">", "value": 0.02, "hold": 50}]      #   all must hold at once
    whites     which whites may be used;  budget: universes / steps / USD / minutes
    map        goal -> questions -> attempts (universes) -> results, plus notes; each node says who put it

A criterion is judged only from the measured time series the lab already keeps (hub.observation): the value
must satisfy `op value` continuously for at least `hold` time units. Nothing here decides that anything is
"alive" or "an individual" -- it only says whether the numbers someone chose were met. Goals live in
lab/goals/ (git-ignored) and are included when a session is exported.
"""
from __future__ import annotations

import datetime as _dt
import itertools
import json
import math
import threading
from pathlib import Path
from typing import Any

from tools.lab import whites
from tools.lab.journal import LAB_DIR

OPS = {">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
       "==": lambda a, b: a == b, "!=": lambda a, b: a != b}
NODE_KINDS = ("question", "attempt", "note", "result")
NODE_STATUS = ("todo", "doing", "met", "not_met", "ceiling", "info")
DEFAULT_BUDGET = {"max_universes": 3, "max_steps": 2_000_000, "max_usd": 1.0, "max_minutes": 30}
HYPOTHESES = Path(__file__).resolve().parents[2] / "research" / "hypotheses.json"


# ------------------------------------------------------------------------------------------ hypotheses
def load_hypotheses(path: Path | None = None) -> list[dict[str, Any]]:
    """The hypotheses a person can pick as a goal (research/hypotheses.json). `ready` ones carry a goal
    template; `needs` ones say what is missing (a new white, a new measuring instrument)."""
    try:
        return json.loads((path or HYPOTHESES).read_text(encoding="utf-8"))["hypotheses"]
    except (OSError, ValueError, KeyError):
        return []


def hypothesis(hid: str, path: Path | None = None) -> dict[str, Any]:
    h = next((x for x in load_hypotheses(path) if x["id"] == hid), None)
    if h is None:
        raise KeyError(f"no hypothesis {hid!r}")
    return h


def goal_from_hypothesis(hid: str, path: Path | None = None) -> dict[str, Any]:
    """A goal body (for GoalBook.create) from a ready hypothesis."""
    h = hypothesis(hid, path)
    if h["status"] != "ready" or not h.get("goal"):
        raise ValueError(f"{hid} はまだ始められません（足りないもの: {h.get('needs') or '—'}）")
    return {"title": f"{h['id']}：{h['title']}", "question": h["question"], "hypothesis": h["id"], **h["goal"]}


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------------------------------ derived metrics
def derived_series(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add `speed` (centroid displacement per time unit) where cy/cx exist, so motion can be a criterion.
    Only while exactly ONE blob is measured (`spots` == 1 before and after, when the white counts spots):
    the centroid of several blobs jumps when one appears or vanishes, which is not the motion of anything.
    The periodic box is not unwrapped, so a crossing of the edge shows up as one large value."""
    out, prev = [], None
    for s in samples:
        m = dict(s["metrics"])
        single = all(x.get("spots", 1) == 1 for x in (m, prev["metrics"] if prev else {}))
        if prev and single and "cy" in m and "cx" in m and "cy" in prev["metrics"] and s["t"] > prev["t"]:
            a, b = prev["metrics"], m
            if all(isinstance(x, (int, float)) and x == x for x in (a["cy"], a["cx"], b["cy"], b["cx"])):
                m["speed"] = math.hypot(b["cy"] - a["cy"], b["cx"] - a["cx"]) / (s["t"] - prev["t"])
        out.append({**s, "metrics": m})
        prev = s
    return out


def metrics_of(white_id: str) -> list[str]:
    """Names a criterion may use for a white (measured by the white, plus derived `speed` if it has a centroid)."""
    from tools.lab.universe import Universe
    u = Universe(white_id, 0)
    names = list(u.metrics().keys())
    if "cy" in names and "cx" in names:
        names.append("speed")
    return names


# ------------------------------------------------------------------------------------------ evaluation
def check_criterion(samples: list[dict[str, Any]], c: dict[str, Any]) -> dict[str, Any]:
    """Longest stretch (in time units) during which `metric op value` held continuously; met once that
    stretch reaches `hold` (hold=0: held at least at one sample)."""
    op, metric, value, hold = OPS[c["op"]], c["metric"], float(c["value"]), float(c.get("hold", 0))
    best, start, last_v, ever = 0.0, None, None, False
    for s in samples:
        v = s["metrics"].get(metric)
        if not isinstance(v, (int, float)) or v != v:
            start = None
            continue
        last_v = float(v)
        if op(last_v, value):
            ever = True
            start = s["t"] if start is None else start
            best = max(best, s["t"] - start)
        else:
            start = None
    current = (samples[-1]["t"] - start) if (samples and start is not None) else 0.0
    end = samples[-1]["metrics"].get(metric) if samples else None      # "now" = the latest sample, not an old one
    last_v = float(end) if isinstance(end, (int, float)) and end == end else None
    met = ever and best >= hold
    return {"metric": metric, "op": c["op"], "value": value, "hold": hold, "met": bool(met),
            "longest": round(best, 4), "holding_now": round(current, 4) if start is not None else None,
            "last": last_v}


def evaluate(goal: dict[str, Any], hub) -> dict[str, Any]:
    """Per universe of the goal's whites: which criteria are met. The goal is met when ONE universe meets all
    criteria (each criterion judged on that universe's own measurements)."""
    per = []
    for uid in hub.ids():
        info = hub.info(uid)
        if goal["whites"] and info["white"] not in goal["whites"]:
            continue
        samples, _ = hub.observation(uid)
        samples = derived_series(samples)
        rows = [check_criterion(samples, c) for c in goal["criteria"]]
        per.append({"universe": uid, "label": info["label"], "white": info["white"], "t": info["t"],
                    "criteria": rows, "all_met": bool(rows) and all(r["met"] for r in rows)})
    return {"goal": goal["id"], "met": any(p["all_met"] for p in per), "universes": per, "at": _now()}


# ------------------------------------------------------------------------------------------ storage
class GoalBook:
    def __init__(self, root: Path | None = None):
        self.root = root or LAB_DIR / "goals"
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._goals: dict[str, dict[str, Any]] = {}
        for f in sorted(self.root.glob("*.json")):
            try:
                g = json.loads(f.read_text(encoding="utf-8"))
                self._goals[g["id"]] = g
            except (OSError, ValueError, KeyError):
                continue
        n = max([int(k[1:]) for k in self._goals if k[1:].isdigit()] or [0])
        self._ids = itertools.count(n + 1)

    def _save(self, g: dict[str, Any]) -> None:
        tmp = self.root / f"{g['id']}.json.tmp"
        tmp.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.root / f"{g['id']}.json")

    @staticmethod
    def validate(body: dict[str, Any]) -> dict[str, Any]:
        title = str(body.get("title") or "").strip()
        if not title:
            raise ValueError("ゴールの名前が空です")
        ws = [w for w in body.get("whites") or [] if w]
        for w in ws:
            whites.get(w)                                   # KeyError for unknown whites
        crit = []
        for c in body.get("criteria") or []:
            if c.get("op") not in OPS:
                raise ValueError(f"比べ方 {c.get('op')} は使えません（{' '.join(OPS)}）")
            metric = str(c.get("metric") or "")
            if ws and not any(metric in metrics_of(w) for w in ws):
                raise ValueError(f"測定値 {metric} は、選んだ白（{', '.join(ws)}）では測っていません")
            v, hold = float(c.get("value")), float(c.get("hold", 0))
            if not math.isfinite(v) or hold < 0:
                raise ValueError("条件の値が正しくありません")
            crit.append({"metric": metric, "op": c["op"], "value": v, "hold": hold, "label": str(c.get("label") or "")})
        budget = {**DEFAULT_BUDGET, **{k: float(v) for k, v in (body.get("budget") or {}).items() if k in DEFAULT_BUDGET}}
        if budget["max_universes"] < 1 or budget["max_universes"] > 8:
            raise ValueError("宇宙の上限は 1〜8 です")
        researchers = []
        for r in body.get("researchers") or []:
            name = str(r.get("name") or "").strip() or f"研究員{len(researchers) + 1}"
            researchers.append({"name": name, "model": str(r.get("model") or ""), "focus": str(r.get("focus") or "")})
        if len(researchers) > 3:
            raise ValueError("研究員は 3 人までです")
        return {"title": title, "question": str(body.get("question") or ""), "whites": ws, "criteria": crit,
                "budget": budget, "researchers": researchers, "hypothesis": str(body.get("hypothesis") or "") or None}

    def create(self, body: dict[str, Any], by: str = "you") -> dict[str, Any]:
        if body.get("hypothesis") and not body.get("title"):          # "仮説から選ぶ": the template, then overrides
            base = goal_from_hypothesis(body["hypothesis"])
            over = {k: v for k, v in body.items() if v not in (None, "")}
            body = {**base, **over, "budget": {**base.get("budget", {}), **(over.get("budget") or {})}}
        v = self.validate(body)
        with self._lock:
            gid = f"g{next(self._ids)}"
            g = {"id": gid, **v, "status": "draft", "created": _now(), "by": by, "nodes": [], "activity": [],
                 "spent": {"universes": 0, "steps": 0, "usd": 0.0, "minutes": 0.0}, "last_eval": None}
            self._goals[gid] = g
            self._save(g)
        return g

    def update(self, gid: str, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            g = self.get(gid)
            v = self.validate({**{k: g.get(k) for k in ("title", "question", "whites", "criteria", "budget", "researchers",
                                                         "hypothesis")}, **body})
            g.update(v)
            if body.get("status") in ("draft", "running", "paused", "done", "met"):
                g["status"] = body["status"]
            self._save(g)
            return g

    def get(self, gid: str) -> dict[str, Any]:
        if gid not in self._goals:
            raise KeyError(f"no goal {gid!r}")
        return self._goals[gid]

    def all(self) -> list[dict[str, Any]]:
        return list(self._goals.values())

    def add_node(self, gid: str, kind: str, text: str, by: str, parent: str | None = None,
                 universe: str | None = None, status: str = "info") -> dict[str, Any]:
        if kind not in NODE_KINDS:
            raise ValueError(f"kind {kind}")
        if status not in NODE_STATUS:
            raise ValueError(f"status {status}")
        with self._lock:
            g = self.get(gid)
            if parent and not any(n["id"] == parent for n in g["nodes"]):
                raise ValueError(f"親 {parent} が見つかりません")
            node = {"id": f"n{len(g['nodes']) + 1}", "parent": parent, "kind": kind, "text": text[:2000], "by": by,
                    "universe": universe, "status": status, "at": _now()}
            g["nodes"].append(node)
            self._save(g)
            return node

    def set_node(self, gid: str, nid: str, status: str | None = None, text: str | None = None) -> dict[str, Any]:
        with self._lock:
            g = self.get(gid)
            n = next((x for x in g["nodes"] if x["id"] == nid), None)
            if n is None:
                raise KeyError(f"no node {nid}")
            if status:
                if status not in NODE_STATUS:
                    raise ValueError(f"status {status}")
                n["status"] = status
            if text is not None:
                n["text"] = text[:2000]
            self._save(g)
            return n

    def log(self, gid: str, actor: str, what: str, universe: str | None = None) -> dict[str, Any]:
        """'いまやっていること': the newest entry per actor is what that actor is doing now."""
        with self._lock:
            g = self.get(gid)
            e = {"at": _now(), "actor": actor, "what": what[:500], "universe": universe}
            g["activity"] = (g["activity"] + [e])[-300:]
            self._save(g)
            return e

    def spend(self, gid: str, **amounts: float) -> dict[str, Any]:
        with self._lock:
            g = self.get(gid)
            for k, v in amounts.items():
                g["spent"][k] = g["spent"].get(k, 0) + v
            self._save(g)
            return g["spent"]

    def over_budget(self, gid: str, include_universes: bool = True) -> str | None:
        """The first exhausted budget, if any. Universes are a cap on MAKING universes: a researcher who has
        made the last one allowed may still run and observe it (include_universes=False)."""
        g = self.get(gid)
        b, s = g["budget"], g["spent"]
        for k, lim in (("universes", "max_universes"), ("steps", "max_steps"), ("usd", "max_usd"), ("minutes", "max_minutes")):
            if k == "universes" and not include_universes:
                continue
            if s.get(k, 0) >= b[lim]:
                return f"上限に達しました：{k} {s.get(k, 0):g} / {b[lim]:g}"
        return None

    def now_doing(self, gid: str) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for e in self.get(gid)["activity"]:
            latest[e["actor"]] = e
        return list(latest.values())

    def record_eval(self, gid: str, result: dict[str, Any]) -> None:
        with self._lock:
            g = self.get(gid)
            g["last_eval"] = result
            if result["met"] and g["status"] == "running":
                g["status"] = "met"
            self._save(g)
