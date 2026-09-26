"""Research record from a lab session: small, secret-free, and it replays from t=0 to the same state."""
import json

import pytest

from tools.lab import record
from tools.lab import replay as replay_cli
from tools.lab.hub import LocalHub


@pytest.fixture
def session():
    hub = LocalHub()
    a = hub.create("gray-scott", 1)
    hub.run(a, 10)
    b = hub.branch(a, {"F": 0.03})
    hub.run(b, 5)
    hub.perturb(b, "drop_seed", {"y": 0.3, "x": 0.6})
    hub.run(b, 4)
    s = hub.create("sh", 0)
    hub.run(s, 8)
    hub.perturb(s, "cut_half")
    hub.run(s, 6)
    return hub, [a, b, s]


def test_export_then_replay_matches(session, tmp_path, capsys):
    hub, ids = session
    res = record.export(hub, None, ids, "F を下げた枝を見る", out_root=tmp_path)
    d = tmp_path / res["name"]
    assert {"recipes.json", "summary.md", "thumbs/A.png", "thumbs/B.png", "thumbs/C.png"} <= set(res["files"])
    assert res["bytes"] <= record.MAX_BYTES
    summary = (d / "summary.md").read_text(encoding="utf-8")
    assert "主張ではない" in summary and "宇宙 A から step" in summary and "F を下げた枝を見る" in summary
    assert replay_cli.main([str(d)]) == 0
    assert "すべて t=0 から同じ状態に戻った" in capsys.readouterr().out
    assert all(r["ok"] for r in replay_cli.check(d))


def test_tampered_recipe_fails_replay(session, tmp_path):
    hub, ids = session
    d = tmp_path / record.export(hub, None, ids[:2], out_root=tmp_path)["name"]
    meta = json.loads((d / "recipes.json").read_text(encoding="utf-8"))
    meta["universes"][1]["recipe"]["events"][0]["values"]["F"] = 0.031      # someone edits the record
    (d / "recipes.json").write_text(json.dumps(meta), encoding="utf-8")
    assert replay_cli.main([str(d), "--universe", "B"]) == 1


def test_packet_can_be_rebuilt_from_the_record(session, tmp_path):
    hub, ids = session
    d = tmp_path / record.export(hub, None, [ids[2]], out_root=tmp_path)["name"]
    assert replay_cli.main([str(d), "--packet", str(tmp_path / "pk")]) == 0
    text = (tmp_path / "pk" / "packet.md").read_text(encoding="utf-8")
    assert "置いた（介入）" in text and "半分を消す" in text


def test_no_secrets_in_the_record(session, tmp_path, monkeypatch):
    from tools.lab import council as C
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-never-appear")
    hub, ids = session
    c = C.Council(hub, None, C.DEFAULT_CONFIG, {}, state_dir=tmp_path / "state")
    c.external("claude-code", "見ました。B は点が増えています（見た目）。")
    c.add_proposal("claude-code", "A", {"k": 0.06}, None, "境目を探す", "spots が減る", "k=0.06")
    res = record.export(hub, c, ids, out_root=tmp_path)
    blob = "".join((tmp_path / res["name"] / f).read_bytes().decode("utf-8", "ignore") for f in res["files"])
    assert "sk-ant-should-never-appear" not in blob and "ANTHROPIC_API_KEY" not in blob
    summary = (tmp_path / res["name"] / "summary.md").read_text(encoding="utf-8")
    assert "AI の会議" in summary and "#1" in summary and "未決" in summary


def test_export_endpoint(tmp_path):
    import threading
    import urllib.request
    from tools.lab.journal import Journal
    from tools.lab.server import make_server
    srv = make_server(port=0, max_universes=1, journal=Journal(root=tmp_path / "j"))
    srv.record_root = tmp_path / "records"
    srv.council.providers = {}
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def post(path, body):
        req = urllib.request.Request(base + path, method="POST", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    try:
        post("/api/universes", {"white": "cgl", "seed": 2, "play": False})
        post(f"/api/universes/{srv.hub.ids()[0]}/control", {"action": "step", "n": 3})
        res = post("/api/journal/export", {"note": "テスト"})
        assert replay_cli.main([res["dir"]]) == 0
        assert any(e["kind"] == "export" for e in srv.hub.journal.entries())
    finally:
        srv.shutdown()
        srv.hub.close()
        srv.server_close()
