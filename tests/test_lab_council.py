"""AI council with fake providers: roles, labels, proposals-as-cards, the Claude Code bridge, budget, secrets."""
import json

import pytest

from tools.lab import council as C
from tools.lab.hub import LocalHub


class Fake(C.Provider):
    def __init__(self, role, text="…", price=0.0, available=True):
        super().__init__(role, {"provider": "fake", "model": f"fake-{role}", "price_in": price, "price_out": price,
                                "api_key_env": "LAB_TEST_SECRET"})
        self.text, self.ok, self.seen = text, available, []

    def available(self):
        return (True, "") if self.ok else (False, "no key")

    def ask(self, system, parts, on_text):
        self.seen.append((system, parts))
        on_text(self.text)
        return C.Usage(1000, 500)


class FakeCore(Fake):
    def __init__(self, calls):
        super().__init__("core", "まとめました。")
        self.calls, self.results, self.histories = calls, [], []

    def converse(self, system, history, run_tool, on_text):
        self.histories.append(list(history))
        on_text(self.text)
        for name, args in self.calls:
            self.results.append(run_tool(name, args))
        return C.Usage(2000, 800)


GOOD = ("propose_branch", {"parent": "A", "changes": [{"knob": "F", "value": 0.04}], "perturb": "", "perturb_args": [],
                           "why": "補給を増やす", "predict": "spots が増える", "put_in": "F=0.04"})
BAD_RANGE = ("propose_branch", {**GOOD[1], "changes": [{"knob": "F", "value": 0.5}]})
BAD_START = ("propose_branch", {**GOOD[1], "changes": [{"knob": "n_seeds", "value": 3}]})
PERTURB = ("propose_branch", {**GOOD[1], "changes": [], "perturb": "drop_seed",
                              "perturb_args": [{"name": "y", "value": 0.2}, {"name": "x", "value": 0.8}]})


@pytest.fixture
def lab(tmp_path):
    hub = LocalHub()
    uid = hub.create("gray-scott", 1)
    hub.run(uid, 12)
    return hub, uid, tmp_path


def _council(hub, tmp_path, providers, limit=3.0):
    cfg = {**C.DEFAULT_CONFIG, "limits": {"max_usd_per_day": limit}}
    return C.Council(hub, None, cfg, providers, state_dir=tmp_path / "state")


def test_look_runs_roles_in_order_and_cards_are_not_executed(lab):
    hub, uid, tmp = lab
    core = FakeCore([GOOD, BAD_RANGE, BAD_START, PERTURB])
    vis, sec = Fake("vision", "点が 2 つに分かれて見える"), Fake("second_view", "閾値の効果かもしれない")
    sec.cfg["images"] = False
    c = _council(hub, tmp, {"vision": vis, "second_view": sec, "core": core})
    c.look([uid], "Fを上げたらどうなる？", wait=True)

    whos = [m["who"] for m in c.messages]
    assert whos[0] == "you" and whos[-1] == "core" and set(whos[1:3]) == {"vision", "second_view"}
    vmsg = next(m for m in c.messages if m["who"] == "vision")
    assert vmsg["text"].startswith(C.UNMEASURED)                 # labelled even though the model did not say so
    c0 = core.histories[0][-1]["content"]              # a tool-using non-Anthropic core gets the text parts
    core_input = c0 if isinstance(c0, str) else json.dumps([p.get("text", "") for p in c0], ensure_ascii=False)
    assert C.UNMEASURED in core_input and "Fを上げたらどうなる" in core_input
    assert all(p["type"] == "text" for p in sec.seen[0][1])      # text-only second view gets no images
    assert any(p["type"] == "image" for p in vis.seen[0][1])

    assert "提案カード #1" in core.results[0]
    assert core.results[1].startswith("エラー") and "範囲" in core.results[1]
    assert core.results[2].startswith("エラー") and "始め方" in core.results[2]
    assert "提案カード #2" in core.results[3]
    assert len(hub.ids()) == 1                                   # nothing ran by itself
    assert [p["status"] for p in c.proposals] == ["open", "open"]

    p = c.try_proposal(1)
    assert p["status"] == "tried" and hub.info(p["child"])["parent"] == uid
    assert hub.info(p["child"])["recipe"]["events"][-1]["values"] == {"F": 0.04}
    with pytest.raises(ValueError):
        c.try_proposal(1)
    assert c.dismiss(2)["status"] == "dismissed"


def test_without_core_the_packet_goes_to_claude_code(lab):
    hub, uid, tmp = lab
    c = _council(hub, tmp, {"core": Fake("core", available=False)})
    c.look([uid], "どう見える？", wait=True)
    latest = tmp / "state" / "latest"
    assert (latest / "packet.md").exists() and "どう見える" in (latest / "request.md").read_text(encoding="utf-8")
    assert any("/guide" in m["text"] for m in c.messages if m["who"] == "system")
    assert c.status()["bridge"] is True
    c.external("claude-code", "見ました")
    assert c.messages[-1]["label"] == "Claude Code"


def test_budget_stops_calls_and_secrets_never_leave(lab, monkeypatch):
    hub, uid, tmp = lab
    monkeypatch.setenv("LAB_TEST_SECRET", "sk-very-secret-value")
    core = FakeCore([])
    c = _council(hub, tmp, {"vision": Fake("vision", price=1.0), "core": core}, limit=0.0)
    c.look([uid], wait=True)
    assert not core.histories and any("上限" in m["text"] for m in c.messages if m["who"] == "system")
    blob = json.dumps(c.snapshot(), ensure_ascii=False)
    assert "sk-very-secret-value" not in blob


def test_cost_is_counted_per_role(lab):
    hub, uid, tmp = lab
    vis = Fake("vision", price=2.0)
    c = _council(hub, tmp, {"vision": vis, "core": FakeCore([])})
    c.look([uid], wait=True)
    v = next(m for m in c.messages if m["who"] == "vision")
    assert v["usd"] == pytest.approx((1000 + 500) * 2.0 / 1e6)
    assert c.spent_today() == pytest.approx(v["usd"])


def test_config_example_parses_and_names_no_unverified_defaults():
    import tomllib
    from pathlib import Path
    cfg = tomllib.loads(Path("tools/lab/config.example.toml").read_text(encoding="utf-8"))
    assert cfg["core"]["model"] == "claude-opus-5-5"
    assert cfg["second_view"]["model"] == "" and cfg["vision"]["model"] == ""   # the person fills these in


def test_claude_code_bridge_cli_puts_cards_into_the_running_lab(tmp_path):
    import threading
    import urllib.request
    from tools.lab import propose
    from tools.lab.journal import Journal
    from tools.lab.server import make_server
    srv = make_server(port=0, max_universes=1, journal=Journal(root=tmp_path))
    srv.council.providers = {}                                   # no API keys: bridge mode
    srv.council.state_dir = tmp_path / "state"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        req = urllib.request.Request(base + "/api/universes", method="POST",
                                     data=json.dumps({"white": "gray-scott", "seed": 1, "play": False}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60).read()
        assert propose.main(["--lab", base, "--parent", "A", "--set", "F=0.04", "--why", "境目を探す"]) == 0
        assert propose.main(["--lab", base, "--say", "見ました"]) == 0
        with pytest.raises(SystemExit, match="範囲"):
            propose.main(["--lab", base, "--parent", "A", "--set", "F=0.9"])
        snap = json.loads(urllib.request.urlopen(base + "/api/council", timeout=30).read())
        assert snap["bridge"] and [p["set"] for p in snap["proposals"]] == [{"F": 0.04}]
        assert snap["messages"][-1]["who"] == "claude-code"
        assert len(srv.hub.ids()) == 1                           # the card did not run anything
    finally:
        srv.shutdown()
        srv.hub.close()
        srv.server_close()


def test_deepseek_is_called_directly_without_the_openai_package(lab, monkeypatch):
    """The DeepSeek role talks to DeepSeek's own endpoint with the standard library only."""
    import builtins
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    seen = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append((self.path, self.headers.get("Authorization"), body))
            chunks = [{"choices": [{"index": 0, "delta": {"reasoning_content": "（考え中）"}}]},
                      {"choices": [{"index": 0, "delta": {"content": "閾値の"}}]},
                      {"choices": [{"index": 0, "delta": {"content": "効果かも。"}}]},
                      {"choices": [], "usage": {"prompt_tokens": 700, "completion_tokens": 30}}]
            data = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks).encode() + b"data: [DONE]\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    real_import = builtins.__import__

    def no_openai(name, *a, **k):
        if name == "openai" or name.startswith("openai."):
            raise AssertionError("DeepSeek must not use the openai package")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_openai)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-test")
    hub, uid, tmp = lab
    try:
        ds = C.DeepSeekProvider("second_view", {**C.DEFAULT_CONFIG["second_view"], "model": "deepseek-test",
                                                "base_url": f"http://127.0.0.1:{srv.server_address[1]}"})
        assert ds.available() == (True, "")
        c = _council(hub, tmp, {"second_view": ds, "core": FakeCore([])})
        c.look([uid], wait=True)
    finally:
        srv.shutdown()
    msg = next(m for m in c.messages if m["who"] == "second_view")
    assert msg["text"] == "閾値の効果かも。" and msg["usage"] == {"input_tokens": 700, "output_tokens": 30}
    path, auth, body = seen[0]
    assert path == "/chat/completions" and auth == "Bearer sk-ds-test"
    assert body["model"] == "deepseek-test" and isinstance(body["messages"][1]["content"], str)   # text only
    assert C.make_providers(C.DEFAULT_CONFIG)["second_view"].__class__ is C.DeepSeekProvider


def test_core_history_restarts_when_the_core_model_changes(lab):
    """Each provider keeps its own history format; switching the core must not mix them (or send raw PNG bytes)."""
    hub, uid, tmp = lab
    a, b = FakeCore([]), FakeCore([])
    b.model = "fake-other"
    c = _council(hub, tmp, {"core": a})
    c.chat("一つ目", wait=True)
    c.chat("二つ目", wait=True)
    assert len(a.histories[1]) == 2 and all(isinstance(m["content"], str) for m in a.histories[1])
    c.providers["core"] = b
    c.chat("三つ目", wait=True)
    assert len(b.histories[0]) == 1 and "三つ目" in b.histories[0][0]["content"]
    assert any("履歴を新しく" in m["text"] for m in c.messages)
    json.dumps(b.histories[0])                                   # JSON-serialisable: no bytes inside
