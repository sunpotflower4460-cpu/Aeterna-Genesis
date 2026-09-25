"""Run several universes side by side, one worker PROCESS each (numpy work is CPU-bound).

The hub owns the lineage and the journal; workers only step their universe, answer commands and push the
latest frame. Frames are "latest wins": a slow viewer skips frames, the simulation never waits for it.
"""
from __future__ import annotations

import itertools
import multiprocessing as mp
import os
import threading
import time
import traceback
from typing import Any

from tools.lab import whites
from tools.lab.journal import Journal
from tools.lab.universe import Universe

MAX_FPS = 12.0


# ---------------------------------------------------------------------------------------- worker side
def _frame_msg(u: Universe, playing: bool, speed: float) -> dict[str, Any]:
    return {"step": u.step_index, "t": u.t, "playing": playing, "speed": speed,
            "lenses": {L.name: u.frame(L.name) for L in u.white.lenses},
            "metrics": u.metrics(), "sha256": None}


def _worker(conn, universe: Universe, max_fps: float) -> None:
    u, playing, speed = universe, False, 1.0
    conn.send(("frame", _frame_msg(u, playing, speed)))
    while True:
        try:
            if conn.poll(0 if playing else 0.25):
                req, cmd, args = conn.recv()
                try:
                    out: Any = None
                    if cmd == "play":
                        playing = True
                    elif cmd == "pause":
                        playing = False
                    elif cmd == "step":
                        u.advance(max(1, int(args.get("n", 1))) * u.white.steps_per_frame)
                    elif cmd == "speed":
                        speed = float(min(max(args.get("value", 1.0), 0.1), 10.0))
                    elif cmd == "set":
                        out = u.set_law(args["values"])
                    elif cmd == "perturb":
                        out = u.perturb(args["name"], args.get("args"))
                    elif cmd == "snapshot":
                        out = u
                    elif cmd == "sha256":
                        out = u.sha256()
                    elif cmd == "stop":
                        conn.send(("reply", req, True, None))
                        return
                    else:
                        raise ValueError(f"unknown command {cmd!r}")
                    conn.send(("reply", req, True, out))
                except Exception as e:  # report to the caller, keep the universe alive
                    conn.send(("reply", req, False, str(e)))
                if cmd != "snapshot":
                    conn.send(("frame", _frame_msg(u, playing, speed)))
            if playing:
                t0 = time.monotonic()
                u.advance(max(1, int(round(u.white.steps_per_frame * speed))))
                conn.send(("frame", _frame_msg(u, playing, speed)))
                rest = 1.0 / max_fps - (time.monotonic() - t0)
                if rest > 0:
                    time.sleep(rest)
        except (EOFError, BrokenPipeError, KeyboardInterrupt):
            return


# ---------------------------------------------------------------------------------------- hub side
class _Handle:
    def __init__(self, uid: str, universe: Universe, parent: str | None, branch_step: int | None,
                 label: str, ctx, max_fps: float):
        self.uid, self.parent, self.branch_step, self.label = uid, parent, branch_step, label
        self.white = universe.white.id
        self.recipe = universe.recipe()
        self.frame: dict[str, Any] | None = None
        self.seq = 0
        self._replies: dict[int, tuple[bool, Any]] = {}
        self._cv = threading.Condition()
        self._req = itertools.count(1)
        self.conn, child = ctx.Pipe()
        self.proc = ctx.Process(target=_worker, args=(child, universe, max_fps), daemon=True,
                                name=f"lab-{uid}")
        self.proc.start()
        child.close()
        self.alive = True
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self) -> None:
        while True:
            try:
                msg = self.conn.recv()
            except (EOFError, OSError):
                break
            with self._cv:
                if msg[0] == "frame":
                    self.frame = msg[1]
                    self.seq += 1
                    Hub.bump()
                else:
                    self._replies[msg[1]] = (msg[2], msg[3])
                self._cv.notify_all()
        self.alive = False
        with self._cv:
            self._cv.notify_all()

    def call(self, cmd: str, timeout: float = 30.0, **args: Any) -> Any:
        req = next(self._req)
        with self._cv:
            self.conn.send((req, cmd, args))
            end = time.monotonic() + timeout
            while req not in self._replies:
                left = end - time.monotonic()
                if left <= 0 or not self.alive:
                    raise TimeoutError(f"{self.uid}: {cmd} did not answer")
                self._cv.wait(left)
            ok, out = self._replies.pop(req)
        if not ok:
            raise ValueError(out)
        return out

    def stop(self) -> None:
        try:
            self.call("stop", timeout=5)
        except Exception:
            pass
        self.proc.join(timeout=5)
        if self.proc.is_alive():
            self.proc.terminate()


class Hub:
    _changed = threading.Condition()
    _version = 0

    @classmethod
    def bump(cls) -> None:
        with cls._changed:
            cls._version += 1
            cls._changed.notify_all()

    @classmethod
    def wait_change(cls, seen: int, timeout: float) -> int:
        with cls._changed:
            if cls._version == seen:
                cls._changed.wait(timeout)
            return cls._version

    def __init__(self, max_universes: int | None = None, journal: Journal | None = None, max_fps: float = MAX_FPS):
        self.max_universes = max_universes or max(2, os.cpu_count() or 2)
        self.journal = journal
        self.max_fps = max_fps
        self._ctx = mp.get_context("spawn")      # same behaviour on Linux, macOS and Windows
        self._lock = threading.RLock()
        self._handles: dict[str, _Handle] = {}
        self._ids = itertools.count(1)
        self._labels = itertools.cycle("ABCDEFGHJKLMNPQRSTUVWXYZ")

    # ------------------------------------------------------------------ lifecycle
    def _spawn(self, universe: Universe, parent: str | None, branch_step: int | None) -> str:
        with self._lock:
            if len(self._handles) >= self.max_universes:
                raise ValueError(f"同時に動かせる宇宙は {self.max_universes} 個までです（CPU コア数）。どれかを閉じてください")
            uid = f"u{next(self._ids)}"
            h = _Handle(uid, universe, parent, branch_step, next(self._labels), self._ctx, self.max_fps)
            self._handles[uid] = h
        self._remember(h)
        Hub.bump()
        return uid

    def create(self, white_id: str, seed: int = 0, knobs: dict[str, Any] | None = None) -> str:
        u = Universe(white_id, seed, knobs)
        uid = self._spawn(u, None, None)
        self._log("create", uid, recipe=u.recipe())
        return uid

    def branch(self, parent_id: str, set_values: dict[str, Any] | None = None,
               perturb: dict[str, Any] | None = None) -> str:
        """Fork the parent's CURRENT state; the child differs only by the given law change / perturbation."""
        if not set_values and not perturb:
            raise ValueError("分岐では、つまみか摂動のどちらかを 1 つ変えてください")
        parent = self._get(parent_id)
        snap: Universe = parent.call("snapshot")
        if set_values:
            snap.set_law(set_values)
        if perturb:
            snap.perturb(perturb["name"], perturb.get("args"))
        uid = self._spawn(snap, parent_id, snap.step_index)
        self._log("branch", uid, parent=parent_id, at_step=snap.step_index, set=set_values, perturb=perturb,
                  recipe=snap.recipe())
        return uid

    def delete(self, uid: str) -> None:
        with self._lock:
            h = self._handles.pop(uid, None)
        if h is None:
            raise KeyError(uid)
        h.stop()
        self._log("delete", uid)
        Hub.bump()

    def close(self) -> None:
        with self._lock:
            hs, self._handles = list(self._handles.values()), {}
        for h in hs:
            h.stop()

    # ------------------------------------------------------------------ control
    def control(self, uid: str, action: str, **args: Any) -> Any:
        if action not in ("play", "pause", "step", "speed"):
            raise ValueError(f"unknown action {action!r}")
        return self._get(uid).call(action, **args)

    def set_law(self, uid: str, values: dict[str, Any]) -> dict[str, Any]:
        h = self._get(uid)
        ev = h.call("set", values=values)
        h.recipe["events"].append(ev)
        self._remember(h)
        self._log("set", uid, event=ev)
        return ev

    def perturb(self, uid: str, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        h = self._get(uid)
        ev = h.call("perturb", name=name, args=args or {})
        h.recipe["events"].append(ev)
        self._remember(h)
        self._log("perturb", uid, event=ev)
        return ev

    def sha256(self, uid: str) -> str:
        return self._get(uid).call("sha256")

    def snapshot(self, uid: str) -> Universe:
        return self._get(uid).call("snapshot")

    # ------------------------------------------------------------------ views
    def _get(self, uid: str) -> _Handle:
        with self._lock:
            h = self._handles.get(uid)
        if h is None:
            raise KeyError(f"no universe {uid!r}")
        return h

    def ids(self) -> list[str]:
        with self._lock:
            return list(self._handles)

    def info(self, uid: str) -> dict[str, Any]:
        h = self._get(uid)
        f = h.frame or {}
        w = whites.get(h.white)
        return {"id": uid, "label": h.label, "white": h.white, "title": w.title, "dimension": w.dimension,
                "parent": h.parent, "branch_step": h.branch_step, "recipe": h.recipe, "put_in": w.put_in,
                "step": f.get("step", 0), "t": f.get("t", 0.0), "playing": f.get("playing", False),
                "speed": f.get("speed", 1.0), "metrics": f.get("metrics", {}), "alive": h.alive}

    def list(self) -> list[dict[str, Any]]:
        return [self.info(uid) for uid in self.ids()]

    def latest(self, uid: str) -> tuple[int, dict[str, Any] | None]:
        h = self._get(uid)
        with h._cv:
            return h.seq, h.frame

    # ------------------------------------------------------------------ journal
    def _remember(self, h: _Handle) -> None:
        if self.journal:
            self.journal.remember(h.uid, {"label": h.label, "white": h.white, "parent": h.parent,
                                          "branch_step": h.branch_step, "recipe": h.recipe})

    def _log(self, kind: str, uid: str, **data: Any) -> None:
        if self.journal:
            try:
                self.journal.log(kind, universe=uid, **data)
            except OSError:
                traceback.print_exc()
