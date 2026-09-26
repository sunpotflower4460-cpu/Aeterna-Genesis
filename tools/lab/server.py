"""Live aquarium lab server: JSON API + Server-Sent Events + the built app (app/dist), one origin.

    python -m tools.lab.server                 # http://127.0.0.1:8765   (this PC only)
    python -m tools.lab.server --lan           # also reachable from a phone on the same Wi-Fi; prints a token

Standard library only (http.server). Binding beyond localhost requires a random token on every API call, so
nobody else on the network can spend this computer's CPU (or, later, the AI guide's API budget).
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import secrets
import socket
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.lab import goals as goalmod  # noqa: E402
from tools.lab import observe, record, whites  # noqa: E402
from tools.lab.council import catalog_public  # noqa: E402
from tools.lab.council import Council  # noqa: E402
from tools.lab.researcher import GoalRunner  # noqa: E402
from tools.lab.hub import Hub  # noqa: E402
from tools.lab.journal import Journal  # noqa: E402

DIST = _REPO / "app" / "dist"
VERSION = 1


def _clean(obj: Any) -> Any:
    """JSON has no NaN/Infinity: send them as null (e.g. a centroid when nothing is there)."""
    if isinstance(obj, float):
        return obj if obj == obj and obj not in (float("inf"), float("-inf")) else None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def _dumps(obj: Any) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, allow_nan=False)


class LabServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, hub: Hub, token: str | None, dist: Path = DIST, council=None, goals_root=None,
                 researcher_factory=None):
        super().__init__(addr, Handler)
        self.hub, self.token, self.dist = hub, token, dist
        self.council = council if council is not None else Council(hub, hub.journal)
        self.record_root = None          # research/sessions (tests point this elsewhere)
        self.goals = goalmod.GoalBook(goals_root) if goals_root else goalmod.GoalBook()
        for g in self.goals.all():       # researchers do not survive a restart: a running goal comes back paused
            if g["status"] == "running":
                self.goals.update(g["id"], {"status": "paused"})
        self.runner = GoalRunner(hub, self.goals, self.council, researcher_factory)


class Handler(BaseHTTPRequestHandler):
    server: LabServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet: the terminal is for the token and errors
        pass

    # ------------------------------------------------------------------ plumbing
    def _json(self, obj: Any, status: int = 200) -> None:
        body = _dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, msg: str) -> None:
        self._json({"error": msg}, status)

    def _body(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode() or "{}")

    def _authorized(self, query: dict[str, list[str]]) -> bool:
        tok = self.server.token
        if not tok:
            return True
        got = self.headers.get("X-Lab-Token") or (query.get("token") or [""])[0]
        return secrets.compare_digest(got, tok)

    def _route(self, method: str) -> None:
        url = urlparse(self.path)
        q = parse_qs(url.query)
        parts = [unquote(p) for p in url.path.split("/") if p]
        if not parts or parts[0] != "api":
            if method == "GET":
                return self._static(url.path)
            return self._error(404, "not found")
        if not self._authorized(q):
            return self._error(401, "token required (see the terminal where the lab server runs)")
        try:
            return self._api(method, parts[1:], q)
        except KeyError as e:
            return self._error(404, str(e).strip("'\""))
        except (ValueError, TypeError) as e:
            return self._error(400, str(e))
        except TimeoutError as e:
            return self._error(504, str(e))

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_DELETE(self):
        self._route("DELETE")

    # ------------------------------------------------------------------ API
    def _api(self, method: str, parts: list[str], q: dict[str, list[str]]) -> None:
        hub = self.server.hub
        if parts == ["health"]:
            return self._json({"ok": True, "version": VERSION, "max_universes": hub.max_universes,
                               "session": hub.journal.session_id if hub.journal else None,
                               "council": self.server.council.status()})
        if parts == ["whites"]:
            return self._json({"whites": [w.public() for w in whites.registry().values()]})
        if parts == ["stream"]:
            return self._stream(q)
        if parts == ["journal", "export"] and method == "POST":
            b = self._body()
            res = record.export(hub, self.server.council, b.get("ids") or None, str(b.get("note") or "")[:4000],
                                out_root=self.server.record_root,
                                session=hub.journal.session_id if hub.journal else None)
            if hub.journal:
                hub.journal.log("export", **res)
            return self._json(res, 201)
        if parts == ["observe"] and method == "POST":
            return self._json(self._observe(self._body()))
        council = self.server.council
        book = self.server.goals
        runner = self.server.runner
        if parts == ["models"]:
            return self._json({"models": catalog_public(council.config)})
        if parts == ["council", "select"] and method == "POST":
            b = self._body()
            return self._json(council.select(str(b["role"]), b.get("key") or None))
        if parts == ["goals", "metrics"]:
            ws = [w for w in ",".join(q.get("whites", [])).split(",") if w] or list(whites.registry())
            return self._json({"metrics": {w: goalmod.metrics_of(w) for w in ws}, "ops": list(goalmod.OPS)})
        if parts == ["goals", "hypotheses"]:
            return self._json({"hypotheses": goalmod.load_hypotheses()})
        if parts == ["goals"] and method == "GET":
            return self._json({"goals": book.all()})
        if parts == ["goals"] and method == "POST":
            return self._json(book.create(self._body()), 201)
        if len(parts) >= 2 and parts[0] == "goals":
            gid = parts[1]
            if len(parts) == 2 and method == "GET":
                g = book.get(gid)
                ev = goalmod.evaluate(g, hub)
                book.record_eval(gid, ev)
                return self._json({"goal": book.get(gid), "evaluation": ev, "now": book.now_doing(gid),
                                   "over_budget": book.over_budget(gid), "researchers": runner.status(gid)})
            if len(parts) == 2 and method == "POST":
                b = self._body()
                prev = book.get(gid)["status"]
                if b.get("status") == "running" and prev != "running":
                    over = book.over_budget(gid)
                    if over:
                        raise ValueError(over + "（上限を上げてから始めてください）")
                g = book.update(gid, b)
                started = []
                if g["status"] == "running" and prev != "running":
                    started = runner.start(gid)
                elif g["status"] in ("paused", "done", "draft") and prev == "running":
                    runner.stop(gid, why=f"ゴールを「{g['status']}」にした")
                return self._json({**g, "started": started})
            if len(parts) == 5 and parts[2] == "researchers" and parts[4] == "stop" and method == "POST":
                n = runner.stop(gid, parts[3])
                book.log(gid, "you", f"{parts[3]} を止めた")
                return self._json({"stopped": n})
            if len(parts) == 3 and parts[2] == "nodes" and method == "POST":
                b = self._body()
                n = book.add_node(gid, b.get("kind", "note"), str(b.get("text", "")), b.get("by", "you"),
                                  b.get("parent"), b.get("universe"), b.get("status", "info"))
                book.log(gid, n["by"], f"マップに追加: {n['text'][:80]}", n["universe"])
                return self._json(n, 201)
            if len(parts) == 4 and parts[2] == "nodes" and method == "POST":
                b = self._body()
                return self._json(book.set_node(gid, parts[3], b.get("status"), b.get("text")))
        if parts == ["council"] and method == "GET":
            return self._json(council.snapshot(int((q.get("since") or ["0"])[0])))
        if parts == ["council", "look"] and method == "POST":
            b = self._body()
            ids = [i for i in (b.get("ids") or hub.ids()) if i in hub.ids()]
            if not ids:
                raise ValueError("宇宙がありません")
            council.look(ids, (b.get("text") or "").strip() or None)
            return self._json(council.status(), 202)
        if parts == ["council", "chat"] and method == "POST":
            text = (self._body().get("text") or "").strip()
            if not text:
                raise ValueError("言葉が空です")
            council.chat(text)
            return self._json(council.status(), 202)
        if parts == ["council", "external"] and method == "POST":
            b = self._body()
            return self._json(council.external(b.get("who", "claude-code"), str(b.get("text", ""))[:8000]), 201)
        if parts == ["proposals"] and method == "POST":
            b = self._body()
            return self._json(council.add_proposal(
                b.get("source", "claude-code"), str(b["parent"]), b.get("set") or {}, b.get("perturb"),
                b.get("why", ""), b.get("predict", ""), b.get("put_in", "")), 201)
        if len(parts) == 3 and parts[0] == "proposals" and method == "POST":
            pid = int(parts[1])
            if parts[2] == "try":
                return self._json(council.try_proposal(pid))
            if parts[2] == "dismiss":
                return self._json(council.dismiss(pid))
        if parts == ["universes"] and method == "GET":
            return self._json({"universes": hub.list()})
        if parts == ["universes"] and method == "POST":
            b = self._body()
            uid = hub.create(b["white"], int(b.get("seed", 0)), b.get("knobs") or {})
            if b.get("play", True):
                hub.control(uid, "play")
            self._attach(b.get("goal"), uid, "新しい宇宙")
            return self._json(hub.info(uid), 201)
        if len(parts) >= 2 and parts[0] == "universes":
            uid = parts[1]
            if len(parts) == 2 and method == "GET":
                return self._json(hub.info(uid))
            if len(parts) == 2 and method == "DELETE":
                hub.delete(uid)
                return self._json({"ok": True})
            if len(parts) == 3 and method == "POST":
                b = self._body()
                action = parts[2]
                if action == "control":
                    hub.control(uid, b["action"], **{k: v for k, v in b.items() if k != "action"})
                    return self._json(hub.info(uid))
                if action == "set":
                    return self._json({"event": hub.set_law(uid, b["values"]), "universe": hub.info(uid)})
                if action == "perturb":
                    return self._json({"event": hub.perturb(uid, b["name"], b.get("args")), "universe": hub.info(uid)})
                if action == "branch":
                    child = hub.branch(uid, b.get("set"), b.get("perturb"))
                    if b.get("play", True):
                        hub.control(child, "play")
                    self._attach(b.get("goal"), child, f"{hub.info(uid)['label']} から分岐")
                    return self._json(hub.info(child), 201)
        return self._error(404, "unknown endpoint")

    def _attach(self, gid: str | None, uid: str, what: str) -> None:
        """A universe made by a person while a goal is selected becomes an attempt on that goal's map."""
        if not gid:
            return
        info = self.server.hub.info(uid)
        self.server.goals.add_node(gid, "attempt", f"宇宙 {info['label']}（{info['white']}）: {what}", "you",
                                   universe=uid, status="doing")
        self.server.goals.log(gid, "you", f"宇宙 {info['label']} を試している（{what}）", uid)

    def _observe(self, body: dict[str, Any]) -> dict[str, Any]:
        """Build the observation packet for the given universes (all, if none given), save it with the
        session, and return it in the same form the AI council receives (images as data URLs)."""
        hub = self.server.hub
        ids = [i for i in (body.get("ids") or hub.ids()) if i in hub.ids()]
        if not ids:
            raise ValueError("宇宙がありません")
        packet = observe.build(hub, ids)
        saved = None
        if hub.journal:
            n = len(list((hub.journal.dir / "packets").glob("*"))) if (hub.journal.dir / "packets").exists() else 0
            saved = observe.save(packet, hub.journal.dir / "packets" / f"{n + 1:03d}")
            hub.journal.log("observe", universes=ids, packet=str(saved.relative_to(hub.journal.dir)))
        return {**observe.to_public(packet), "saved": str(saved) if saved else None}

    def _stream(self, q: dict[str, list[str]]) -> None:
        """SSE: `u=<id>:<lens>,<id>:<lens>` -> event "frame" per new frame, "universes" when the set changes."""
        hub = self.server.hub
        want: dict[str, str] = {}
        for item in ",".join(q.get("u", [])).split(","):
            if ":" in item:
                uid, lens = item.split(":", 1)
                want[uid] = lens
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        seen: dict[str, int] = {}
        roster: tuple[str, ...] = ()
        version, last_beat = -1, time.monotonic()
        try:
            while True:
                version = Hub.wait_change(version, 10.0)
                ids = tuple(hub.ids())
                if ids != roster:
                    roster = ids
                    self._send("universes", {"ids": list(ids)})
                for uid, lens in want.items():
                    try:
                        seq, frame = hub.latest(uid)
                    except KeyError:
                        continue
                    if frame is None or seen.get(uid) == seq:
                        continue
                    if frame.get("diverged"):
                        seen[uid] = seq
                        self._send("frame", {"id": uid, "seq": seq, "step": frame["step"], "t": frame["t"],
                                             "playing": False, "speed": frame["speed"], "metrics": {},
                                             "diverged": True, "lens": lens})
                        continue
                    if lens not in frame["lenses"]:
                        continue
                    seen[uid] = seq
                    L = frame["lenses"][lens]
                    self._send("frame", {"id": uid, "seq": seq, "step": frame["step"], "t": frame["t"],
                                         "playing": frame["playing"], "speed": frame["speed"],
                                         "metrics": frame["metrics"], "diverged": False, "lens": lens, "grid": L["grid"],
                                         "lo": L["lo"], "hi": L["hi"],
                                         "b64": base64.b64encode(L["data"]).decode("ascii")})
                if time.monotonic() - last_beat > 10:
                    self.wfile.write(b": beat\n\n")
                    self.wfile.flush()
                    last_beat = time.monotonic()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def _send(self, event: str, data: dict[str, Any]) -> None:
        self.wfile.write(f"event: {event}\ndata: {_dumps(data)}\n\n".encode())
        self.wfile.flush()

    # ------------------------------------------------------------------ static app
    def _static(self, path: str) -> None:
        root = self.server.dist.resolve()
        rel = path.lstrip("/") or "index.html"
        f = (root / rel).resolve()
        if not str(f).startswith(str(root)) or not f.is_file():
            f = root / "index.html"
        if not f.is_file():
            return self._error(404, "app not built: (cd app && npm install && npm run build)")
        data = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def make_server(host: str = "127.0.0.1", port: int = 8765, lan: bool = False, max_universes: int | None = None,
                journal: Journal | None = None, token: str | None = None, council=None, goals_root=None,
                researcher_factory=None) -> LabServer:
    if lan:
        host = "0.0.0.0"
        token = token or secrets.token_urlsafe(12)
    hub = Hub(max_universes=max_universes, journal=journal)
    return LabServer((host, port), hub, token, council=council, goals_root=goals_root,
                     researcher_factory=researcher_factory)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--lan", action="store_true", help="listen on all interfaces (token required)")
    ap.add_argument("--max-universes", type=int, default=None)
    a = ap.parse_args(argv)
    srv = make_server(port=a.port, lan=a.lan, max_universes=a.max_universes, journal=Journal())
    host = _lan_ip() if a.lan else "127.0.0.1"
    url = f"http://{host}:{a.port}/" + (f"?token={srv.token}#lab" if srv.token else "#lab")
    print(f"水槽ラボ: {url}")
    print(f"  記録: {srv.hub.journal.dir}")
    for r in srv.council.status()["roles"]:
        print(f"  AI {r['label']}: {r['model'] or '—'} {'（使える）' if r['available'] else '（' + r['reason'] + '）'}")
    if not DIST.joinpath("index.html").exists():
        print("  （画面が未ビルドです: cd app && npm install && npm run build）")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.runner.close()
        srv.hub.close()
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
