"""Goals: measurable criteria, the map, 'now doing', budgets; model catalog and role selection."""
import json

import pytest

from tools.lab import goals
from tools.lab.hub import LocalHub


def test_criterion_holds_for_a_duration():
    s = [{"t": t, "metrics": {"spots": 1 if 10 <= t <= 70 else 3}} for t in range(0, 100, 5)]
    assert goals.check_criterion(s, {"metric": "spots", "op": "==", "value": 1, "hold": 50})["met"]
    r = goals.check_criterion(s, {"metric": "spots", "op": "==", "value": 1, "hold": 80})
    assert not r["met"] and r["longest"] == 60
    assert not goals.check_criterion(s, {"metric": "spots", "op": ">", "value": 5, "hold": 0})["met"]


def test_speed_is_derived_from_the_centroid():
    s = [{"t": float(t), "metrics": {"cy": 10.0 + 0.5 * t, "cx": 20.0}} for t in range(5)]
    d = goals.derived_series(s)
    assert "speed" not in d[0]["metrics"] and d[3]["metrics"]["speed"] == pytest.approx(0.5)
    assert "speed" in goals.metrics_of("three-component") and "speed" not in goals.metrics_of("gray-scott")
    many = [{"t": float(t), "metrics": {"spots": 2, "cy": 10.0 + 5 * t, "cx": 20.0}} for t in range(3)]
    assert all("speed" not in x["metrics"] for x in goals.derived_series(many))   # several blobs: no speed


def test_validation_refuses_what_the_white_does_not_measure(tmp_path):
    book = goals.GoalBook(tmp_path)
    with pytest.raises(ValueError, match="測っていません"):
        book.create({"title": "x", "whites": ["gray-scott"], "criteria": [{"metric": "speed", "op": ">", "value": 0}]})
    with pytest.raises(ValueError):
        book.create({"title": "x", "researchers": [{"name": str(i)} for i in range(4)]})
    with pytest.raises(KeyError):
        book.create({"title": "x", "whites": ["no-such-white"]})


def test_evaluate_map_now_and_budget(tmp_path):
    book = goals.GoalBook(tmp_path)
    g = book.create({"title": "点が増える", "whites": ["gray-scott"],
                     "criteria": [{"metric": "spots", "op": ">=", "value": 8, "hold": 100}],
                     "budget": {"max_universes": 1}})
    hub = LocalHub()
    a = hub.create("gray-scott", 1)
    hub.run(a, 30)
    other = hub.create("sh", 0)                      # not a white of this goal -> ignored
    hub.run(other, 2)
    ev = goals.evaluate(g, hub)
    assert [u["universe"] for u in ev["universes"]] == [a] and ev["met"]
    book.update(g["id"], {"status": "running"})
    book.record_eval(g["id"], ev)
    assert book.get(g["id"])["status"] == "met"

    q = book.add_node(g["id"], "question", "F を下げると?", "you")
    t = book.add_node(g["id"], "attempt", "宇宙 A", "研究員1", parent=q["id"], universe=a, status="doing")
    book.set_node(g["id"], t["id"], status="met")
    with pytest.raises(ValueError):
        book.add_node(g["id"], "note", "x", "you", parent="n99")
    book.log(g["id"], "研究員1", "A を観測")
    book.log(g["id"], "研究員1", "B に分岐")
    book.log(g["id"], "you", "見ている")
    assert {e["actor"]: e["what"] for e in book.now_doing(g["id"])} == {"研究員1": "B に分岐", "you": "見ている"}
    assert book.over_budget(g["id"]) is None
    book.spend(g["id"], universes=1)
    assert "universes" in book.over_budget(g["id"])
    again = goals.GoalBook(tmp_path)                 # persisted
    assert again.get(g["id"])["nodes"][1]["status"] == "met"


def test_catalog_selection_and_goal_endpoints(tmp_path, monkeypatch):
    import threading
    import urllib.request
    from tools.lab import council as C
    from tools.lab.journal import Journal
    from tools.lab.server import make_server
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-in-env")
    srv = make_server(port=0, max_universes=2, journal=Journal(root=tmp_path / "j"), goals_root=tmp_path / "goals")
    srv.council.state_dir = tmp_path / "state"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(path, body=None):
        req = urllib.request.Request(base + path, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    try:
        models = call("/api/models")["models"]
        assert any(m["key"] == "anthropic/claude-opus-5-5" and m["tools"] for m in models)
        assert "sk-ant-secret-in-env" not in json.dumps(models)
        call("/api/council/select", {"role": "second_view", "key": "anthropic/claude-opus-5-5"})
        sel = json.loads((tmp_path / "state" / "selection.json").read_text())
        assert sel["roles"]["second_view"] == "anthropic/claude-opus-5-5"
        assert isinstance(srv.council.providers["second_view"], C.AnthropicProvider)

        g = call("/api/goals", {"title": "Q1", "whites": ["three-component"],
                                "criteria": [{"metric": "spots", "op": "==", "value": 1, "hold": 10}]})
        u = call("/api/universes", {"white": "three-component", "seed": 1, "play": False, "goal": g["id"]})
        view = call(f"/api/goals/{g['id']}")
        assert view["goal"]["nodes"][0]["kind"] == "attempt" and view["goal"]["nodes"][0]["universe"] == u["id"]
        assert view["now"][0]["actor"] == "you" and view["evaluation"]["universes"][0]["label"] == "A"
        assert "spots" in call("/api/goals/metrics?whites=three-component")["metrics"]["three-component"]
    finally:
        srv.shutdown()
        srv.hub.close()
        srv.server_close()
