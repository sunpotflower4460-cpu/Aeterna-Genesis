"""「まとめて試す」 and やさしい説明: variants are plain t=0 recipes judged like the live lab; researchers can
sweep inside the goal's whites and budget; the beginner text comes only from measured numbers."""
import json
import threading
import urllib.request

import pytest

from tools.lab import goals, plain, sweep
from tools.lab.council import Usage
from tools.lab.hub import LocalHub
from tools.lab.researcher import GoalRunner
from tools.lab.universe import Universe

from tests.test_lab_researcher import Scripted


def test_plan_is_the_product_and_is_checked():
    v = sweep.plan("gray-scott", {"k": 0.06}, {"F": [0.03, 0.04]}, [1, 2])
    assert [(x["seed"], x["knobs"]["F"], x["knobs"]["k"]) for x in v] == [(1, 0.03, 0.06), (1, 0.04, 0.06),
                                                                         (2, 0.03, 0.06), (2, 0.04, 0.06)]
    with pytest.raises(ValueError, match="範囲"):
        sweep.plan("gray-scott", {}, {"F": [0.5]}, [])
    with pytest.raises(ValueError, match="通りまで"):
        sweep.plan("gray-scott", {}, {"F": [0.02, 0.03, 0.04, 0.05, 0.06], "k": [0.05, 0.055, 0.06, 0.065, 0.07]}, [])


def test_variants_match_the_live_lab_and_replay():
    crit = [{"metric": "spots", "op": ">=", "value": 1, "hold": 0}]
    v = sweep.plan("gray-scott", {}, {"F": [0.03, 0.04]}, [1])
    rs = sweep.run(v, 6, crit, workers=1)
    for r in rs:                                  # same recipe from t=0 -> same state (put it in a tank = same run)
        u = Universe("gray-scott", r["seed"], r["knobs"])
        u.advance(r["steps"])
        assert u.sha256() == r["sha256"]
    hub = LocalHub()                              # judged exactly like a live universe
    uid = hub.create("gray-scott", 1, v[0]["knobs"])
    hub.run(uid, 6)
    live = goals.check_criterion(goals.derived_series(hub.observation(uid)[0]), crit[0])
    mine = next(r for r in rs if r["knobs"] == v[0]["knobs"])
    assert live == mine["criteria"][0]
    assert rs == sweep.run(v, 6, crit, workers=2)  # separate processes give the same, ranked the same


def test_researcher_sweeps_inside_budget_and_records_it(tmp_path):
    book = goals.GoalBook(tmp_path)
    g = book.create({"title": "点", "whites": ["gray-scott"], "budget": {"max_steps": 120 * 5 * 3 + 10},
                     "criteria": [{"metric": "spots", "op": ">=", "value": 1, "hold": 0}]})
    book.update(g["id"], {"status": "running"})
    call = lambda white, vals, frames: ("sweep", {"white": white, "base": [], "vary": [{"knob": "F", "values": vals}],
                                                  "seeds": [], "frames": frames, "why": "F を振る",
                                                  "plain": "えさの量を 3 通り変えて試します"})
    p = Scripted([[call("sh", [0.1], 5), call("gray-scott", [0.03, 0.035, 0.04], 50),
                   call("gray-scott", [0.03, 0.035, 0.04], 5)], [("finish", {"summary": "s", "plain": "3 通り試しました", "outcome": "info"})]])
    hub = LocalHub()
    runner = GoalRunner(hub, book, None, provider_factory=lambda s: p)
    runner.sweep_workers = 1
    runner.start(g["id"])
    runner.join(g["id"], 60)
    assert "使えません" in p.results[0][1]
    assert "予算が足りません" in p.results[1][1] and "frames を 5 以下" in p.results[1][1]
    assert "まとめて試した s1: 3/3 通り" in p.results[2][1]
    g = book.get(g["id"])
    assert g["spent"]["steps"] == 3 * 5 * 120 and hub.ids() == []          # nothing was put in a tank
    s = g["sweeps"][0]
    assert s["criteria"] == g["criteria"] and len(s["planned"]) == 3
    assert [p["status"] for p in s["planned"]] == ["completed"] * 3
    assert all("joint_at" in v and v["criteria"] for v in s["variants"])
    assert s["by"] == "研究員1" and len(s["variants"]) == 3 and s["variants"][0]["label"].startswith("F=")
    node = next(n for n in g["nodes"] if "まとめて" in n["text"])
    assert node["plain"] == "えさの量を 3 通り変えて試します" and node["status"] == "met"
    assert any(n["plain"] == "3 通り試しました" for n in g["nodes"] if n["kind"] == "result")

    lines = plain.goal_plain(g, goals.evaluate(g, hub), book.now_doing(g["id"]), runner.status(g["id"]))
    text = "\n".join(lines)
    assert "点（まとまり）の数が 1 以上" in text and "まとめて 3 通り試しました" in text
    assert "目安をぜんぶ満たしたもの：まとめて試した 3 通り" in text and "生きている" in text   # the caveat is always there

    # Saved sweeps stay visible, but their verdict cannot be attached to a newly edited goal.
    book.update(g["id"], {"criteria": [{"metric": "spots", "op": ">", "value": 5000}]})
    assert "目安をぜんぶ満たしたもの" not in "\n".join(plain.goal_plain(g, None, [], []))


def test_all_planned_rows_survive_worker_errors_and_stops(monkeypatch):
    variants = sweep.plan("gray-scott", {}, {}, [11, 12, 13])
    run_variant = sweep.run_variant
    def run(v, *args):
        if v["seed"] == 11:
            raise RuntimeError("worker failed")
        return run_variant(v, *args)
    monkeypatch.setattr(sweep, "run_variant", run)
    trials = []
    results = sweep.run(variants, 1, [], workers=1, should_stop=lambda: len(trials) == 2,
                        on_trial=lambda *args: trials.append(args))
    assert [(index, status) for index, status, *_ in trials] == [(0, "failed"), (1, "completed"), (2, "not_run")]
    assert "worker failed" in trials[0][-1] and [r["seed"] for r in results] == [12]


def test_parallel_stop_keeps_every_completed_future():
    variants = sweep.plan("gray-scott", {}, {}, list(range(8)))
    trials = []
    results = sweep.run(variants, 1, [], workers=2, should_stop=lambda: bool(trials),
                        on_trial=lambda *args: trials.append(args))
    assert sorted(i for i, *_ in trials) == list(range(8))
    assert results and all(status in ("completed", "not_run") for _, status, _, _ in trials)
    assert {r["seed"] for r in results} == {variants[i]["seed"] for i, s, _, _ in trials if s == "completed"}


def test_disjoint_and_diverged_prefix_never_promote_in_live_or_sweep(monkeypatch):
    criteria = [{"metric": k, "op": ">", "value": 0, "hold": 0} for k in ("a", "b")]
    class Trial:
        white = type("Clock", (), {"steps_per_frame": 1})
        def __init__(self, white, seed, knobs):
            self.step_index, self.seed = 0, seed
        @property
        def t(self):
            return self.step_index
        def advance(self, n):
            self.step_index += n
        def finite(self):
            return self.seed == 0 or self.t < 2
        def metrics(self):
            return {"a": int(self.t == 0), "b": int(self.seed == 1 or self.t > 0)}
        def sha256(self):
            return "finished"
    monkeypatch.setattr(sweep, "Universe", Trial)
    for seed in (0, 1):
        trial = Trial("test", seed, {})
        samples = []
        for index in range(3):
            trial.step_index = index
            if trial.finite():
                samples.append({"t": index, "metrics": trial.metrics()})
        class Hub:
            def ids(self): return ["u"]
            def info(self, uid): return {"white": "test", "label": "A", "t": 2, "diverged": not trial.finite()}
            def observation(self, uid): return samples, []
        live = goals.evaluate({"id": "g", "whites": ["test"], "criteria": criteria}, Hub())
        replay = sweep.run_variant({"white": "test", "seed": seed, "knobs": {}}, 2, criteria)
        assert replay["met"] == 2 and not replay["all_met"] and not live["met"]
        assert replay["joint_at"] is None and live["universes"][0]["joint_at"] is None


def test_plain_text_without_criteria_or_activity(tmp_path):
    book = goals.GoalBook(tmp_path)
    g = book.create({"hypothesis": "H8"})
    lines = plain.goal_plain(g, goals.evaluate(g, LocalHub()), [], [], goals.hypothesis("H8"))
    assert lines[0].startswith("🎯") and "決まった目安はありません" in lines[1] and lines[-1].startswith("💰")


def test_explain_endpoint(tmp_path):
    from tools.lab.journal import Journal
    from tools.lab.server import make_server

    class Prov:
        model = "fake-explainer"

        def ask(self, system, parts, on_text):
            assert "中学生" in system and "生きている" in system
            on_text("点を探す実験です。")
            return Usage(100, 20)

        def cost(self, u):
            return 0.001

    class Council:
        config = {}
        prov = None
        charged = []

        def status(self):
            return {"roles": []}

        def usable(self, role):
            return self.prov

        def spent_today(self):
            return 0.0

        def _limit(self):
            return 3.0

        def _charge(self, usd):
            self.charged.append(usd)

    c = Council()
    srv = make_server(port=0, max_universes=1, journal=Journal(root=tmp_path / "j"), goals_root=tmp_path / "g", council=c)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(path, body=None):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                     method="POST" if body is not None else "GET", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        st, g = call("goals", {"hypothesis": "H8"})
        st, v = call(f"goals/{g['id']}")
        assert st == 200 and v["plain"][0].startswith("🎯")
        st, e = call(f"goals/{g['id']}/explain", {})
        assert st == 400 and "機械的" in e["error"]
        c.prov = Prov()
        st, e = call(f"goals/{g['id']}/explain", {})
        assert st == 200 and e["text"] == "点を探す実験です。" and c.charged == [0.001]
    finally:
        srv.shutdown()
        srv.hub.close()
