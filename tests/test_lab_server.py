"""Live lab server end to end: create -> stream frames -> change law -> branch -> delete; token on --lan."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from tools.lab.journal import Journal
from tools.lab.server import make_server


def _call(base, method, path, body=None, token=None):
    req = urllib.request.Request(base + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"X-Lab-Token": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _frames(base, spec, n):
    out = []
    with urllib.request.urlopen(f"{base}/api/stream?u={spec}", timeout=60) as r:
        event = None
        for raw in r:
            line = raw.decode().rstrip("\n")
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: ") and event == "frame":
                out.append(json.loads(line[6:]))
                if len(out) >= n:
                    return out
    return out


@pytest.fixture
def server(tmp_path):
    srv = make_server(port=0, max_universes=3, journal=Journal(root=tmp_path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.hub.close()
    srv.server_close()


def test_create_stream_set_branch_delete(server):
    srv, base = server
    st, whites = _call(base, "GET", "/api/whites")
    assert st == 200 and {w["id"] for w in whites["whites"]} >= {"gray-scott", "tdgl-3d", "three-component"}

    st, u = _call(base, "POST", "/api/universes", {"white": "gray-scott", "seed": 1})
    assert st == 201 and u["label"] == "A"
    frames = _frames(base, f"{u['id']}:V", 3)
    assert len(frames) == 3 and frames[-1]["step"] > frames[0]["step"]
    assert frames[0]["grid"] == [96, 96] and "spots" in frames[0]["metrics"]

    st, r = _call(base, "POST", f"/api/universes/{u['id']}/set", {"values": {"F": 0.04}})
    assert st == 200 and r["event"]["kind"] == "set"
    st, r = _call(base, "POST", f"/api/universes/{u['id']}/set", {"values": {"F": 0.5}})
    assert st == 400                                         # out of range is refused, not clamped
    st, r = _call(base, "POST", f"/api/universes/{u['id']}/set", {"values": {"n_seeds": 2}})
    assert st == 400                                         # start knobs only at t=0

    st, child = _call(base, "POST", f"/api/universes/{u['id']}/branch", {"perturb": {"name": "cut_half"}})
    assert st == 201 and child["parent"] == u["id"]
    fork = [e for e in child["recipe"]["events"] if e["step"] == child["branch_step"]]
    assert fork and fork[-1]["name"] == "cut_half"

    st, _ = _call(base, "DELETE", f"/api/universes/{child['id']}")
    assert st == 200
    kinds = [e["kind"] for e in srv.hub.journal.entries()]
    assert kinds[:1] == ["create"] and "set" in kinds and "branch" in kinds and kinds[-1] == "delete"


def test_lan_requires_token(tmp_path):
    srv = make_server(port=0, lan=True, max_universes=1, journal=Journal(root=tmp_path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        assert _call(base, "GET", "/api/health")[0] == 401
        st, h = _call(base, "GET", "/api/health", token=srv.token)
        assert st == 200 and h["ok"]
    finally:
        srv.shutdown()
        srv.hub.close()
        srv.server_close()


def test_labels_never_repeat():
    from tools.lab.hub import _label
    labels = [_label(i) for i in range(80)]
    assert labels[:3] == ["A", "B", "C"] and labels[25:28] == ["Z", "AA", "AB"]
    assert len(set(labels)) == len(labels)


def test_fork_index_journal_steps_and_concurrent_order(server):
    srv, base = server
    hub = srv.hub
    st, u = _call(base, "POST", "/api/universes", {"white": "sh", "seed": 3, "play": False})
    uid = u["id"]
    _call(base, "POST", f"/api/universes/{uid}/control", {"action": "step", "n": 2})
    _call(base, "POST", f"/api/universes/{uid}/set", {"values": {"r": -0.35}})        # parent event at step N
    st, child = _call(base, "POST", f"/api/universes/{uid}/branch", {"set": {"b": 1.8}})
    assert child["fork_index"] == 1                                                  # only b=1.8 is the fork
    assert [e.get("values") for e in child["recipe"]["events"][child["fork_index"]:]] == [{"b": 1.8}]

    # two interventions sent at the same time: the recipe must follow the worker's order
    results = []
    ts = [threading.Thread(target=lambda a=a: results.append(_call(base, "POST", f"/api/universes/{uid}/perturb",
                                                                   {"name": "kick", "args": {"amp": a}})))
          for a in (0.01, 0.02)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    info = hub.final_info(uid)
    assert hub.info(uid)["recipe"] == info["recipe"]
    from tools.lab.universe import replay
    assert replay(info["recipe"], info["step"]).sha256() == info["sha256"]

    _call(base, "POST", f"/api/universes/{uid}/control", {"action": "pause"})
    st, _ = _call(base, "DELETE", f"/api/universes/{uid}")
    uni = json.loads((hub.journal.dir / "universes.json").read_text())[uid]
    assert uni["closed"] and replay(uni["recipe"], uni["step"]).sha256() == uni["sha256"]
    assert any(e["kind"] == "delete" and e.get("sha256") for e in hub.journal.entries())


def test_observe_endpoint_saves_the_packet(server):
    srv, base = server
    st, u = _call(base, "POST", "/api/universes", {"white": "cgl", "seed": 0})
    _frames(base, f"{u['id']}:phase", 3)
    st, p = _call(base, "POST", "/api/observe", {"ids": [u["id"]]})
    assert st == 200 and p["universes"][0]["images"][0]["src"].startswith("data:image/png;base64,")
    assert "観測パケット" in p["text"] and p["saved"]
    assert any(e["kind"] == "observe" for e in srv.hub.journal.entries())
