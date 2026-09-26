"""AI researchers: they act only through their tools, inside the goal's whites / knob ranges / budget, every
act is recorded as put in by them, and they stop when told. Providers here are scripted fakes."""
import json
import threading
import time
import urllib.parse
import urllib.request

import pytest

from tools.lab import goals
from tools.lab.council import Usage
from tools.lab.hub import LocalHub
from tools.lab.researcher import GoalRunner, _push_user


class Scripted:
    """A fake model: each converse() call plays the next list of tool calls, then ends its turn."""

    model = "fake-model"

    def __init__(self, turns, gate=None):
        self.turns, self.gate = list(turns), gate
        self.results: list[tuple[str, str]] = []
        self.systems: list[str] = []

    def cost(self, u):
        return (u.input_tokens + u.output_tokens) * 1e-6

    def converse(self, system, history, run_tool, on_text, max_rounds=6, tools=None):
        self.systems.append(system)
        assert {t["name"] for t in tools} >= {"create_universe", "run", "finish"}
        calls = self.turns.pop(0) if self.turns else [("finish", {"summary": "おわり", "outcome": "info"})]
        on_text("考えています。")
        for name, args in calls:
            if callable(args):                    # arguments that depend on what happened before
                args = args(self.results)
            self.results.append((name, run_tool(name, args)))
            if self.gate is not None:
                self.gate(name)
        history.append({"role": "assistant", "content": "ok"})
        return Usage(1000, 100)


def create(white="gray-scott", seed=1, knobs=(), why="試す", under=""):
    return ("create_universe", {"white": white, "seed": seed, "knobs": [{"knob": k, "value": v} for k, v in knobs],
                                "why": why, "under": under})


def run(u="A", frames=5):
    return ("run", {"universe": u, "frames": frames})


def finish(outcome="info"):
    return ("finish", {"summary": "まとめ", "outcome": outcome})


def setup(tmp_path, providers, **body):
    book = goals.GoalBook(tmp_path)
    g = book.create({"title": "点", "whites": ["gray-scott"], **body})
    book.update(g["id"], {"status": "running"})
    hub = LocalHub()
    it = iter(providers)
    runner = GoalRunner(hub, book, None, provider_factory=lambda spec: next(it))
    return book, g["id"], hub, runner


def test_a_researcher_tries_observes_notes_and_finishes(tmp_path):
    p = Scripted([[create(), run("A", 10), ("observe", {"universe": "A"}), ("evaluate_goal", {}),
                   ("note", {"kind": "note", "text": "点が増えた", "status": "info", "under": "", "universe": "A"})],
                  [finish("not_met")]])
    book, gid, hub, runner = setup(tmp_path, [p], criteria=[{"metric": "spots", "op": ">", "value": 999, "hold": 0}])
    runner.start(gid)
    runner.join(gid)
    r = runner.status(gid)[0]
    assert r["state"] == "finished" and r["owned"] == [hub.ids()[0]]
    g = book.get(gid)
    assert g["spent"]["universes"] == 1 and g["spent"]["steps"] == 10 * 120
    assert g["spent"]["usd"] == pytest.approx(2 * 1100e-6)
    kinds = [(n["kind"], n["by"]) for n in g["nodes"]]
    assert ("attempt", "研究員1") in kinds and ("note", "研究員1") in kinds and ("result", "研究員1") in kinds
    assert any(n["kind"] == "result" and n["status"] == "not_met" for n in g["nodes"])
    assert any("研究を終えた" in e["what"] for e in g["activity"])
    assert "事件簿" in p.results[2][1] or "t=" in p.results[2][1]
    assert p.results[3][1].startswith("判定（測定だけ）: 未達成")
    assert "gray-scott" in p.systems[0] and "[0.01, 0.08]" in p.systems[0]     # knobs and ranges are told
    assert hub.info(hub.ids()[0])["step"] == 10 * 120


def test_refusals_stay_inside_the_goal(tmp_path):
    p = Scripted([[create(white="sh"), create(knobs=[("F", 0.5)]), create(knobs=[("n_seeds", 3)]),
                   run("B", 1000), run("B", 1),
                   ("branch", {"parent": "A", "changes": [{"knob": "n_seeds", "value": 3}], "perturb": "",
                               "perturb_args": [], "why": "", "under": ""}),
                   ("close_universe", {"universe": "B"}), ("propose", {"parent": "A", "changes": [], "perturb": "",
                                                                     "perturb_args": [], "why": "", "predict": "", "put_in": ""}),
                   create(seed=2)]])
    book, gid, hub, runner = setup(tmp_path, [p], budget={"max_universes": 1})
    theirs = hub.create("gray-scott", 5)                     # a person's universe: label A
    runner.start(gid)
    runner.join(gid)
    out = dict(enumerate(r for _, r in p.results))
    assert "使えません" in out[0]                              # white not allowed
    assert "範囲" in out[1]                                    # knob out of range
    assert "作りました" in out[2]                              # start knob at creation: fine -> label B
    assert "frames は 1〜300" in out[3]
    assert "進めました" in out[4]
    assert "始め方" in out[5] or "予算" in out[5]              # start knob on a branch / no budget left
    assert "閉じました" in out[6] and "提案カードの場所がありません" in out[7]
    assert "予算" in out[8]                                    # max_universes = 1
    assert theirs in hub.ids() and hub.info(theirs)["step"] == 0     # the person's universe was not touched


def test_cannot_run_or_close_a_universe_it_did_not_make(tmp_path):
    p = Scripted([[run("A", 3), ("close_universe", {"universe": "A"}), ("observe", {"universe": "A"})]])
    book, gid, hub, runner = setup(tmp_path, [p])
    theirs = hub.create("gray-scott", 5)
    runner.start(gid)
    runner.join(gid)
    assert "あなたが作った宇宙ではありません" in p.results[0][1] and "あなたが作った宇宙ではありません" in p.results[1][1]
    assert "エラー" not in p.results[2][1]                     # reading is allowed
    assert hub.info(theirs)["step"] == 0 and theirs in hub.ids()


def test_step_budget_trims_then_stops(tmp_path):
    p = Scripted([[create(), run("A", 300)], [run("A", 5)]])
    book, gid, hub, runner = setup(tmp_path, [p], budget={"max_steps": 120 * 7})
    runner.start(gid)
    runner.join(gid)
    assert "7 コマ進めました" in p.results[1][1]
    r = runner.status(gid)[0]
    assert r["state"] == "over_budget" and "steps" in r["reason"]
    assert book.get(gid)["spent"]["steps"] == 120 * 7


def test_stop_button_and_pause_end_researchers(tmp_path):
    started = threading.Event()
    release = threading.Event()

    def gate(name):
        started.set()
        release.wait(5)

    endless = [[run("A", 2)] for _ in range(50)]
    p = Scripted([[create()]] + endless, gate=gate)
    q = Scripted([[create(seed=3)]] + [[run("B", 2)] for _ in range(50)], gate=lambda n: time.sleep(0.2))
    book, gid, hub, runner = setup(tmp_path, [p, q], researchers=[{"name": "あ"}, {"name": "い"}])
    runner.start(gid)
    assert started.wait(5)
    assert runner.stop(gid, "あ") == 1
    release.set()
    for r in runner._teams[gid]:
        if r.name == "あ":
            r.thread.join(5)
    st = {r["name"]: r for r in runner.status(gid)}
    assert st["あ"]["state"] == "stopped" and st["い"]["state"] == "running"
    book.update(gid, {"status": "paused"})                    # pausing the goal stops everyone at the next tool
    runner.join(gid, 10)
    st = {r["name"]: r for r in runner.status(gid)}
    assert st["い"]["state"] == "stopped" and "paused" in st["い"]["reason"]


def test_parallel_researchers_share_budget_and_map(tmp_path):
    ps = [Scripted([[create(seed=i), run_own(i)], [finish()]]) for i in range(3)]
    book, gid, hub, runner = setup(tmp_path, ps, researchers=[{"name": f"R{i}"} for i in range(3)],
                                   budget={"max_universes": 3})
    runner.start(gid)
    runner.join(gid, 60)
    st = runner.status(gid)
    assert [r["state"] for r in st] == ["finished"] * 3
    owned = [u for r in st for u in r["owned"]]
    assert len(set(owned)) == 3 and set(owned) == set(hub.ids())
    g = book.get(gid)
    assert g["spent"]["universes"] == 3
    assert {n["by"] for n in g["nodes"] if n["kind"] == "attempt"} == {"R0", "R1", "R2"}
    assert {e["actor"] for e in book.now_doing(gid)} == {"R0", "R1", "R2"}


def lambda_label(i):
    """Run whatever universe this researcher created (labels depend on the order the threads got there)."""
    def pick(results):
        made = [r for n, r in results if n == "create_universe"][-1]
        return {"universe": made.split("宇宙 ")[1].split(" ")[0], "frames": 3}
    return pick


def run_own(i):
    return ("run", lambda_label(i))


def test_goal_met_leads_to_wrap_up(tmp_path):
    p = Scripted([[create(), run("A", 2), ("evaluate_goal", {})], [create(seed=9)], [finish("met")]])
    book, gid, hub, runner = setup(tmp_path, [p], criteria=[{"metric": "spots", "op": ">=", "value": 0, "hold": 0}])
    runner.start(gid)
    runner.join(gid)
    assert book.get(gid)["status"] == "met" and "達成" in p.results[2][1]
    assert "達成されています" in p.results[3][1]                # no new universes after the goal is met
    att = [n for n in book.get(gid)["nodes"] if n["kind"] == "attempt"]
    assert att[0]["status"] == "met"
    assert runner.status(gid)[0]["state"] == "finished"


def test_push_user_never_makes_two_user_turns():
    h = [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "ok"}]}]
    _push_user(h, "続けて")
    assert len(h) == 1 and h[0]["content"][-1] == {"type": "text", "text": "続けて"}
    h = [{"role": "assistant", "content": "done"}]
    _push_user(h, "続けて")
    assert h[-1] == {"role": "user", "content": "続けて"}


def test_server_starts_and_stops_researchers(tmp_path):
    from tools.lab.journal import Journal
    from tools.lab.server import make_server

    class Council:            # the server's council is not needed here
        config = {}

        def status(self):
            return {"roles": []}

        def spent_today(self):
            return 0.0

        def _limit(self):
            return 3.0

        def _charge(self, usd):
            pass

    gate = threading.Event()
    p = Scripted([[create()]] + [[run("A", 1)] for _ in range(40)], gate=lambda n: gate.wait(0.05))
    srv = make_server(port=0, max_universes=2, journal=Journal(root=tmp_path / "j"), goals_root=tmp_path / "g",
                      council=Council(), researcher_factory=lambda spec: p)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(path, body=None):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                     method="POST" if body is not None else "GET",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    try:
        g = call("goals", {"title": "点", "whites": ["gray-scott"], "researchers": [{"name": "研究員1"}]})
        out = call(f"goals/{g['id']}", {"status": "running"})
        assert out["started"][0]["state"] == "running"
        for _ in range(100):
            v = call(f"goals/{g['id']}")
            if v["researchers"] and v["researchers"][0]["owned"]:
                break
            time.sleep(0.05)
        assert v["researchers"][0]["name"] == "研究員1" and len(call("universes")["universes"]) == 1
        assert call(f"goals/{g['id']}/researchers/{urllib.parse.quote('研究員1')}/stop", {})["stopped"] == 1
        srv.runner.join(g["id"], 30)
        assert call(f"goals/{g['id']}")["researchers"][0]["state"] == "stopped"
    finally:
        srv.runner.close()
        srv.shutdown()
        srv.hub.close()


def test_deepseek_researcher_loop_uses_function_calling(tmp_path, monkeypatch):
    """DeepSeek (direct, stdlib) drives a researcher through OpenAI-format tool calls; history is append-only."""
    from tools.lab.council import DeepSeekProvider

    monkeypatch.setenv("DEEPSEEK_TEST_KEY", "sk-test-secret")
    prov = DeepSeekProvider("core", {"provider": "deepseek", "model": "ds-test", "api_key_env": "DEEPSEEK_TEST_KEY"})
    replies = [
        {"choices": [{"message": {"content": "作ります", "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "create_universe", "arguments": json.dumps(
                {"white": "gray-scott", "seed": 1, "knobs": [], "why": "t", "under": ""})}}]}}],
         "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
        {"choices": [{"message": {"content": "", "tool_calls": [
            {"id": "c2", "type": "function", "function": {"name": "finish", "arguments": json.dumps(
                {"summary": "s", "outcome": "info"})}}]}}], "usage": {"prompt_tokens": 20, "completion_tokens": 5}},
        {"choices": [{"message": {"content": "おわり"}}], "usage": {"prompt_tokens": 30, "completion_tokens": 5}},
    ]
    sent = []

    def post(body):
        sent.append(json.loads(json.dumps(body)))
        return replies.pop(0)

    monkeypatch.setattr(prov, "post", post)
    book, gid, hub, runner = setup(tmp_path, [prov])
    runner.start(gid)
    runner.join(gid)
    r = runner.status(gid)[0]
    assert r["state"] == "finished" and r["tokens"] == {"input": 60, "output": 15}
    assert sent[0]["tool_choice"] == "auto" and sent[0]["messages"][0]["role"] == "system"
    assert {t["function"]["name"] for t in sent[0]["tools"]} >= {"create_universe", "finish"}
    roles = [m["role"] for m in sent[-1]["messages"]]
    assert roles == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert "sk-test-secret" not in json.dumps(sent) and "sk-test-secret" not in json.dumps(runner.status(gid))


def test_influence_tool_reads_without_changing_the_universe(tmp_path):
    book = goals.GoalBook(tmp_path)
    g = book.create({"title": "光円錐", "whites": ["wave-phi4", "gray-scott"]})
    book.update(g["id"], {"status": "running"})
    p = Scripted([[create(white="wave-phi4"), run("A", 2), ("influence", {"universe": "A", "frames": 6}),
                   ("influence", {"universe": "A", "frames": 100})]])
    hub = LocalHub()
    runner = GoalRunner(hub, book, None, provider_factory=lambda s: p)
    runner.start(g["id"])
    runner.join(g["id"], 60)
    out = p.results[2][1]
    assert "一定の速さ" in out and "置いたもの" in out
    assert "frames は 4〜60" in p.results[3][1]
    uid = hub.ids()[0]
    assert hub.info(uid)["step"] == 2 * 10                          # the measured universe itself did not move
    assert book.get(g["id"])["spent"]["steps"] == 2 * 10 + 2 * 6 * 4 * 2
