"""One universe = one white running from t=0, plus the exact list of everything a person put in.

A universe is fully described by its RECIPE:

    {"white": id, "seed": int, "knobs": {...initial knobs...},
     "events": [{"step": s, "kind": "set", "values": {...}}          # law change, applied before step s
                {"step": s, "kind": "perturb", "name": ..., "args": {...}}]}

`replay(recipe, steps)` rebuilds the state from t=0 and must reproduce the live state bit for bit
(tests/test_lab_determinism.py). A branch is simply the parent's recipe truncated at the branch step plus
the new event(s), so every universe in a lineage is independently reproducible from t=0.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any

import numpy as np

from genesis.recording.recorder import downsample
from tools.lab import whites

DISPLAY_MAX_3D = 48
DISPLAY_MAX_2D = 128


class Universe:
    def __init__(self, white_id: str, seed: int = 0, knobs: dict[str, Any] | None = None):
        self.white = whites.get(white_id)
        self.seed = int(seed)
        self.knobs = self.white.default_knobs()
        self.knobs.update(self.white.check_knobs(knobs or {}, allow_start=True))
        self.initial_knobs = dict(self.knobs)
        self.params = self.white.params(self.knobs)
        self._cache = self.white.cache(self.params)
        self.state = self.white.init(self.seed, self.knobs, self.params)
        self.step_index = 0
        self.events: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ time
    @property
    def dt(self) -> float:
        return float(self.params.get("dt", 1.0))

    @property
    def t(self) -> float:
        return self.step_index * self.dt

    def advance(self, n: int = 1) -> None:
        for _ in range(int(n)):
            self.state = self.white.step(self.state, self.step_index * self.dt, self.params, self._cache)
            self.step_index += 1

    # ------------------------------------------------------------------ interventions (all PUT IN)
    def set_law(self, values: dict[str, Any]) -> dict[str, Any]:
        checked = self.white.check_knobs(values, allow_start=False)
        if not checked:
            raise ValueError("変えるつまみがありません")
        self.knobs.update(checked)
        self.params = self.white.params(self.knobs)
        self._cache = self.white.cache(self.params)
        ev = {"step": self.step_index, "kind": "set", "values": checked}
        self.events.append(ev)
        return ev

    def perturb(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        spec = self.white.perturb_spec(name) if name in {p.name for p in self.white.perturbs} else None
        if spec is None:
            raise ValueError(f"{self.white.id}: 摂動 {name!r} はこの白では使えません")
        full = {a.name: a.default for a in spec.args}
        for k, v in (args or {}).items():
            a = next((x for x in spec.args if x.name == k), None)
            if a is None:
                raise ValueError(f"摂動 {name} に引数 {k!r} はありません")
            v = float(v)
            if not (a.lo <= v <= a.hi):
                raise ValueError(f"{k}={v} は範囲 [{a.lo}, {a.hi}] の外です")
            full[k] = v
        rng = np.random.default_rng([self.seed, self.step_index, len(self.events)])
        self.state = self.white.perturb(name, full, self.state, self.params, rng)
        ev = {"step": self.step_index, "kind": "perturb", "name": name, "args": full}
        self.events.append(ev)
        return ev

    def apply_event(self, ev: dict[str, Any]) -> None:
        if ev["kind"] == "set":
            self.set_law(ev["values"])
        elif ev["kind"] == "perturb":
            self.perturb(ev["name"], ev.get("args"))
        else:
            raise ValueError(f"unknown event kind {ev['kind']!r}")

    # ------------------------------------------------------------------ identity
    def recipe(self) -> dict[str, Any]:
        return {"white": self.white.id, "seed": self.seed, "knobs": dict(self.initial_knobs),
                "events": copy.deepcopy(self.events)}

    def sha256(self) -> str:
        h = hashlib.sha256()
        for k in sorted(self.state):
            a = np.ascontiguousarray(self.state[k])
            h.update(k.encode())
            h.update(str(a.dtype).encode())
            h.update(a.tobytes())
        return h.hexdigest()

    def clone(self) -> "Universe":
        return copy.deepcopy(self)

    # the White holds closures; ship only its id across processes and look it up again on arrival
    def __getstate__(self):
        d = dict(self.__dict__)
        d["white"] = self.white.id
        return d

    def __setstate__(self, d):
        d = dict(d)
        d["white"] = whites.get(d["white"])
        self.__dict__.update(d)

    # ------------------------------------------------------------------ observation (read-only)
    def metrics(self) -> dict[str, float]:
        return self.white.metrics(self.state)

    def display_grid(self) -> tuple[int, ...]:
        cap = DISPLAY_MAX_3D if self.white.dimension == 3 else DISPLAY_MAX_2D
        return tuple(min(n, cap) for n in self.white.grid)

    def frame(self, lens: str) -> dict[str, Any]:
        """uint8 frame of one lens with ITS OWN [lo, hi] (no clipping); the viewer may map it onto the lens'
        fixed display range. Display only: nothing here feeds back into the state."""
        spec = next((x for x in self.white.lenses if x.name == lens), None)
        if spec is None:
            raise ValueError(f"{self.white.id}: unknown lens {lens!r}")
        arr = downsample(self.white.lens(lens, self.state), self.display_grid())
        if spec.cyclic:
            lo, hi = -np.pi, np.pi
        else:
            lo, hi = float(np.min(arr)), float(np.max(arr))
        span = (hi - lo) or 1.0
        q = np.clip(np.round((arr - lo) / span * 255.0), 0, 255).astype(np.uint8)
        return {"grid": list(arr.shape), "lo": lo, "hi": hi, "data": np.ascontiguousarray(q).tobytes()}


def replay(recipe: dict[str, Any], steps: int) -> Universe:
    """Rebuild a universe from t=0: create with the initial knobs, then apply every event at its step."""
    u = Universe(recipe["white"], recipe["seed"], recipe.get("knobs"))
    for ev in sorted(recipe.get("events", []), key=lambda e: e["step"]):   # sort is stable: keeps order
        if ev["step"] > steps:
            break
        u.advance(ev["step"] - u.step_index)
        u.apply_event(ev)
    u.advance(steps - u.step_index)
    return u
