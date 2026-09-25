"""Registry of the whites the live lab can run.

Each entry is a THIN wrapper around the unchanged model code: `init` builds the t=0 state exactly as
tools/export_aquarium.py does (same functions, same argument order, same RNG use), and `step` calls the
model's own step function. Nothing here adds physics. What a person can touch is declared explicitly:

* knobs, kind "law"   -- coefficients of the field law (may change mid-run; recorded as a PUT-IN event)
* knobs, kind "start" -- how t=0 is prepared (only when a universe is created)
* perturbations       -- explicit interventions (cut half, drop a seed, kick with noise), always PUT IN

Level / ceiling statements are not repeated here; they live in research/index.json (`ceiling_ref`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True)
class Knob:
    name: str
    label: str
    kind: str            # "law" | "start"
    default: float
    lo: float
    hi: float
    step: float
    integer: bool = False


@dataclass(frozen=True)
class Lens:
    name: str
    label: str
    transfer: str        # high | low | cyclic | diverging (display only)
    vmin: float          # fixed display range (a view choice; frames carry their own min/max too)
    vmax: float
    cyclic: bool = False


@dataclass(frozen=True)
class Perturb:
    name: str
    label: str
    args: tuple[Knob, ...] = ()


PERTURB_CUT = Perturb("cut_half", "半分を消す（背景に戻す）")
PERTURB_KICK = Perturb("kick", "ノイズで揺らす", (Knob("amp", "強さ", "arg", 0.02, 0.0, 0.2, 0.005),))
PERTURB_SEED = Perturb("drop_seed", "種を置く", (Knob("y", "縦の位置", "arg", 0.5, 0.0, 1.0, 0.01),
                                                 Knob("x", "横の位置", "arg", 0.5, 0.0, 1.0, 0.01)))


@dataclass
class White:
    id: str
    title: str
    family: str
    model: str
    dimension: int
    grid: tuple[int, ...]
    steps_per_frame: int
    knobs: list[Knob]
    lenses: list[Lens]
    perturbs: list[Perturb]
    put_in: list[str]
    source: str
    ceiling_ref: str
    defaults: dict[str, Any]
    _init: Callable = field(repr=False, default=None)
    _step: Callable = field(repr=False, default=None)
    _lens: Callable = field(repr=False, default=None)
    _metrics: Callable = field(repr=False, default=None)
    _perturb: Callable = field(repr=False, default=None)
    _cache: Callable = field(repr=False, default=None)

    # ------------------------------------------------------------------ knobs -> model params
    def knob(self, name: str) -> Knob:
        for k in self.knobs:
            if k.name == name:
                return k
        raise KeyError(f"{self.id}: unknown knob {name!r}")

    def default_knobs(self) -> dict[str, float]:
        return {k.name: k.default for k in self.knobs}

    def check_knobs(self, values: dict[str, Any], allow_start: bool = True) -> dict[str, float]:
        out = {}
        for name, v in values.items():
            k = self.knob(name)
            if k.kind == "start" and not allow_start:
                raise ValueError(f"{name} は始め方のつまみなので、動いている宇宙では変えられません（新しい宇宙で）")
            v = float(v)
            if not (k.lo <= v <= k.hi) or not np.isfinite(v):
                raise ValueError(f"{name}={v} は範囲 [{k.lo}, {k.hi}] の外です")
            out[name] = int(round(v)) if k.integer else v
        return out

    def params(self, knobs: dict[str, float]) -> dict[str, Any]:
        """Model parameter dict = the model's own DEFAULTS, overridden only by declared knobs it reads."""
        p = dict(self.defaults)
        for name, v in knobs.items():
            if name in p:
                p[name] = v
        return p

    # ------------------------------------------------------------------ simulation hooks
    def cache(self, params):
        return self._cache(params) if self._cache else None

    def init(self, seed: int, knobs: dict[str, float], params: dict[str, Any]) -> dict[str, np.ndarray]:
        return self._init(int(seed), knobs, params)

    def step(self, state, t, params, cache):
        return self._step(state, t, params, cache)

    def lens(self, name: str, state) -> np.ndarray:
        return self._lens(name, state)

    def metrics(self, state) -> dict[str, float]:
        return self._metrics(state)

    def perturb(self, name: str, args: dict[str, float], state, params, rng):
        if name not in {p.name for p in self.perturbs}:
            raise ValueError(f"{self.id}: 摂動 {name!r} はこの白では使えません")
        return self._perturb(name, args, state, params, rng)

    def perturb_spec(self, name: str) -> Perturb:
        for p in self.perturbs:
            if p.name == name:
                return p
        raise KeyError(name)

    def public(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "family": self.family, "model": self.model,
                "dimension": self.dimension, "grid": list(self.grid), "steps_per_frame": self.steps_per_frame,
                "dt": self.defaults.get("dt"), "knobs": [asdict(k) for k in self.knobs],
                "lenses": [asdict(x) for x in self.lenses],
                "perturbs": [{"name": p.name, "label": p.label, "args": [asdict(a) for a in p.args]}
                             for p in self.perturbs],
                "put_in": self.put_in, "source": self.source, "ceiling_ref": self.ceiling_ref}


# ---------------------------------------------------------------------------------------- helpers
def _gauss(shape, cy, cx, width):
    ys, xs = np.arange(shape[0])[:, None], np.arange(shape[1])[None, :]
    dy = np.minimum(np.abs(ys - cy), shape[0] - np.abs(ys - cy))
    dx = np.minimum(np.abs(xs - cx), shape[1] - np.abs(xs - cx))
    return np.exp(-(dy ** 2 + dx ** 2) / (2.0 * width ** 2))


def _half(arr):
    return (slice(0, arr.shape[0] // 2),)


def _noise_like(arr, amp, rng):
    if np.iscomplexobj(arr):
        return amp * (rng.standard_normal(arr.shape) + 1j * rng.standard_normal(arr.shape))
    return amp * rng.standard_normal(arr.shape)


def _kick(state, keys, amp, rng):
    out = dict(state)
    for k in keys:
        out[k] = state[k] + _noise_like(state[k], amp, rng)
    return out


# ---------------------------------------------------------------------------------------- whites
def _tdgl():
    from genesis.diagnostics import measures
    from genesis.models import ginzburg_landau as gl

    def init(seed, knobs, p):
        rng = np.random.default_rng(seed)
        return {"psi": gl.make_initial((48,) * 3, p["noise_amplitude"], rng)}

    def step(s, t, p, cache):
        return {"psi": gl.step(s["psi"], t, p)}

    def lens(name, s):
        return np.abs(s["psi"]) ** 2 if name == "density" else np.angle(s["psi"])

    def metrics(s):
        return {"mean_amp": float(np.mean(np.abs(s["psi"]))), "defects": measures.winding_defect_count(s["psi"])}

    def perturb(name, a, s, p, rng):
        psi = s["psi"].copy()
        if name == "cut_half":
            psi[_half(psi)] = 0.0
            return {"psi": psi}
        return _kick(s, ["psi"], a["amp"], rng)

    return White(
        id="tdgl-3d", title="冷やした場に渦の糸が生まれる（TDGL・3D）", family="g001 TDGL",
        model="genesis.models.ginzburg_landau", dimension=3, grid=(48, 48, 48), steps_per_frame=6,
        # explicit Euler, dt=0.1, 7-point Laplacian: the fastest mode needs dt*(12*Du + eps_final) <= 2,
        # so Du <= 1.4 with eps_final <= 2 keeps every allowed setting numerically stable (not a physics limit).
        knobs=[Knob("Du", "拡散（なめらかさ）", "law", 1.0, 0.2, 1.4, 0.05),
               Knob("eps_final", "冷却後の強さ ε", "law", 1.0, 0.2, 2.0, 0.05),
               Knob("quench_duration", "冷やす時間", "law", 8.0, 0.0, 40.0, 1.0),
               Knob("noise_amplitude", "はじめのノイズ", "start", 0.01, 1e-4, 0.1, 1e-4)],
        lenses=[Lens("density", "渦の芯（|ψ|² が小さい所）", "low", 0.0, 1.0),
                Lens("phase", "位相（向き）", "cyclic", -np.pi, np.pi, True)],
        perturbs=[PERTURB_CUT, PERTURB_KICK],
        put_in=["一様な場＋ごく小さなノイズ", "冷却（クエンチ）の強さと速さ"],
        source="rooms/official/room-g001-a", ceiling_ref="g001", defaults=dict(gl.DEFAULTS),
        _init=init, _step=step, _lens=lens, _metrics=metrics, _perturb=perturb)


def _gpe_ring():
    from core import field
    from core.fft import k_squared_3d

    L, n_imag, dtau = 48, 120, 0.05
    defaults = {"g": 1.0, "mu": 1.0, "dt": 0.1, "R": 7.0}

    def cache(p):
        return {"k2": k_squared_3d(L)}

    def init(seed, knobs, p):
        # e003 preparation (before t=0): shape the core while pinning the imprinted ring's phase.
        k2 = k_squared_3d(L)
        phase0 = field.vortex_ring_phase(L, p["R"], charge=1)
        psi = np.sqrt(p["mu"]) * np.exp(1j * phase0)
        norm0 = np.sum(np.abs(psi) ** 2)
        for _ in range(n_imag):
            psi = field.step_imag_3d(psi, 0.0, k2, p["g"], p["mu"], dtau)
            psi *= np.sqrt(norm0 / np.sum(np.abs(psi) ** 2))
            psi = np.abs(psi) * np.exp(1j * phase0)
        return {"psi": psi}

    def step(s, t, p, cache):
        return {"psi": field.step_real_3d(s["psi"], 0.0, cache["k2"], p["g"], p["mu"], p["dt"])}

    def lens(name, s):
        return np.abs(s["psi"]) ** 2 if name == "density" else np.angle(s["psi"])

    def metrics(s):
        # measures.winding_defect_count only sees xy-plaquettes, and this ring lies in an xy plane, so it
        # would read 0. Report the plain core volume instead (|psi|^2 < 0.3 mu); ring tracking is left to
        # the observation layer, which must not mistake the imprint-seam debris near z=0 for the ring.
        rho = np.abs(s["psi"]) ** 2
        return {"mean_density": float(rho.mean()), "core_voxels": int((rho < 0.3).sum())}

    def perturb(name, a, s, p, rng):
        psi = s["psi"].copy()
        if name == "cut_half":
            psi[_half(psi)] = np.sqrt(p["mu"])
            return {"psi": psi}
        return _kick(s, ["psi"], a["amp"], rng)

    return White(
        id="gpe-ring-3d", title="渦の輪が自分で進む（GPE・3D）", family="GPE（超流体）",
        model="core.field (step_real_3d)", dimension=3, grid=(L,) * 3, steps_per_frame=6,
        knobs=[Knob("g", "相互作用 g", "law", 1.0, 0.3, 2.0, 0.05),
               Knob("R", "置く輪の半径", "start", 7.0, 4.0, 14.0, 0.5)],
        lenses=[Lens("density", "渦の芯（|ψ|² が小さい所）", "low", 0.0, 1.6),
                Lens("phase", "位相", "cyclic", -np.pi, np.pi, True)],
        perturbs=[PERTURB_CUT, PERTURB_KICK],
        put_in=["渦の輪（半径 R の形を置いた）", "輪の芯を整える準備（t=0 より前・虚時間 120 ステップ）",
                "円板状の影＝輪を置いたときの位相の継ぎ目（手法の作り物）"],
        source="experiments/e003_gpe_vortex_ring", ceiling_ref="gpe", defaults=defaults,
        _init=init, _step=step, _lens=lens, _metrics=metrics, _perturb=perturb, _cache=cache)


def _gray_scott():
    from genesis.models import gray_scott as gs
    N = 96

    def init(seed, knobs, p):
        rng = np.random.default_rng(seed)
        U, V = gs.make_initial((N, N), p["n_seeds"], rng, seed_radius=p["seed_radius"])
        return {"U": U, "V": V}

    def step(s, t, p, cache):
        U, V = gs.step(s["U"], s["V"], p)
        return {"U": U, "V": V}

    def lens(name, s):
        return s[name]

    def metrics(s):
        return {"spots": gs.spot_count(s["V"]), "v_mass": gs.v_mass(s["V"])}

    def perturb(name, a, s, p, rng):
        U, V = s["U"].copy(), s["V"].copy()
        if name == "cut_half":
            U[_half(U)], V[_half(V)] = 1.0, 0.0
        elif name == "drop_seed":
            blob = _gauss(U.shape, a["y"] * N, a["x"] * N, p["seed_radius"])
            U, V = U - 0.5 * blob, V + 0.5 * blob
        else:
            return _kick(s, ["U", "V"], a["amp"], rng)
        return {"U": U, "V": V}

    return White(
        id="gray-scott", title="点が分かれて増える（Gray-Scott・2D）", family="Gray-Scott",
        model="genesis.models.gray_scott", dimension=2, grid=(N, N), steps_per_frame=120,
        knobs=[Knob("F", "補給 F", "law", 0.035, 0.01, 0.08, 0.001),
               Knob("k", "消える速さ k", "law", 0.062, 0.04, 0.075, 0.0005),
               # explicit Euler, dt=1, 5-point Laplacian: stable while 8*D*dt < 2 -> keep D <= 0.2
               Knob("Du", "U の拡散", "law", 0.16, 0.05, 0.2, 0.005),
               Knob("Dv", "V の拡散", "law", 0.08, 0.02, 0.15, 0.005),
               Knob("n_seeds", "はじめの種の数", "start", 8, 1, 30, 1, True),
               Knob("seed_radius", "種の半径", "start", 3.0, 1.0, 8.0, 0.5)],
        lenses=[Lens("V", "V の濃さ", "high", 0.0, 0.5), Lens("U", "U の濃さ", "low", 0.0, 1.0)],
        perturbs=[PERTURB_SEED, PERTURB_CUT, PERTURB_KICK],
        put_in=["小さな点（種）をいくつか"], source="docs/WHITE_CEILINGS.md", ceiling_ref="gray_scott",
        defaults=dict(gs.DEFAULTS), _init=init, _step=step, _lens=lens, _metrics=metrics, _perturb=perturb)


def _three_component():
    from genesis.models import three_component_rd as t3
    N = 96

    def cache(p):
        return {"k2": t3._k2(N)}

    def init(seed, knobs, p):
        rng = np.random.default_rng(seed)
        u, v, w = t3.make_initial((N, N), knobs.get("noise", 1e-3), rng, p)
        return {"u": u, "v": v, "w": w}

    def step(s, t, p, cache):
        u, v, w = t3.step(s["u"], s["v"], s["w"], p, cache["k2"])
        return {"u": u, "v": v, "w": w}

    def lens(name, s):
        return s[name]

    def metrics(s):
        st = t3.spot_stats(s["u"])
        cy, cx = st["centroid"]
        return {"spots": st["count"], "area": float(st["area"]), "cy": float(cy), "cx": float(cx)}

    def perturb(name, a, s, p, rng):
        out = {k: v.copy() for k, v in s.items()}
        if name == "cut_half":
            for k in out:
                out[k][_half(out[k])] = 0.0
        elif name == "drop_seed":
            out["u"] = out["u"] + p["seed_amp"] * _gauss((N, N), a["y"] * N, a["x"] * N, p["seed_width"])
        else:
            return _kick(s, ["u"], a["amp"], rng)
        return out

    return White(
        id="three-component", title="最前線：自分で動く個体は出るか（三成分 RD・2D）", family="三成分反応拡散",
        model="genesis.models.three_component_rd", dimension=2, grid=(N, N), steps_per_frame=30,
        knobs=[Knob("Dw", "遅い抑制の拡散 Dw", "law", 40.0, 5.0, 80.0, 1.0),
               Knob("tau", "速い抑制の遅れ τ", "law", 1.0, 0.2, 5.0, 0.05),
               Knob("theta", "遅い抑制の遅れ θ", "law", 60.0, 5.0, 150.0, 1.0),
               Knob("k1", "かたより k1", "law", 0.0, -0.5, 0.5, 0.01),
               Knob("k3", "速い抑制の強さ k3", "law", 0.5, 0.0, 2.0, 0.05),
               Knob("k4", "遅い抑制の強さ k4", "law", 2.0, 0.0, 5.0, 0.05),
               Knob("noise", "はじめのノイズ", "start", 1e-3, 0.0, 0.05, 1e-4),
               Knob("seed_amp", "ふくらみの高さ", "start", 1.5, 0.2, 3.0, 0.1),
               Knob("seed_width", "ふくらみの幅", "start", 4.0, 1.0, 10.0, 0.5)],
        lenses=[Lens("u", "u（活性）", "high", -1.0, 1.5), Lens("w", "w（遅い抑制＝航跡）", "high", -0.1, 0.1),
                Lens("v", "v（速い抑制）", "high", -0.5, 0.5)],
        perturbs=[PERTURB_SEED, PERTURB_CUT, PERTURB_KICK],
        put_in=["対称なふくらみ一つ＋ノイズ"], source="docs/ANGULAR_MODES.md", ceiling_ref="three_component_rd",
        defaults=dict(t3.DEFAULTS), _init=init, _step=step, _lens=lens, _metrics=metrics, _perturb=perturb,
        _cache=cache)


def _cgl():
    from genesis.diagnostics import measures
    from genesis.models import complex_ginzburg_landau as cgl
    N = 96

    def cache(p):
        return {"k2": cgl._k2((N, N))}

    def init(seed, knobs, p):
        rng = np.random.default_rng(seed)
        return {"A": cgl.make_initial((N, N), knobs.get("noise", 1e-2), rng)}

    def step(s, t, p, cache):
        return {"A": cgl.step(s["A"], p, cache["k2"])}

    def lens(name, s):
        return np.angle(s["A"]) if name == "phase" else np.abs(s["A"])

    def metrics(s):
        return {"defects": measures.winding_defect_count(s["A"]), "mean_amp": float(np.mean(np.abs(s["A"])))}

    def perturb(name, a, s, p, rng):
        A = s["A"].copy()
        if name == "cut_half":
            A[_half(A)] = 1.0
        elif name == "drop_seed":
            A = A * (1.0 - 0.95 * _gauss((N, N), a["y"] * N, a["x"] * N, 3.0))
        else:
            return _kick(s, ["A"], a["amp"], rng)
        return {"A": A}

    return White(
        id="cgl", title="らせんが回り、乱れる（CGL・2D）", family="CGL",
        model="genesis.models.complex_ginzburg_landau", dimension=2, grid=(N, N), steps_per_frame=25,
        knobs=[Knob("b", "分散 b", "law", 2.0, -3.0, 3.0, 0.05),
               Knob("c", "非線形の回り c", "law", -1.0, -3.0, 3.0, 0.05),
               Knob("noise", "はじめのノイズ", "start", 1e-2, 1e-4, 0.2, 1e-4)],
        lenses=[Lens("phase", "位相", "cyclic", -np.pi, np.pi, True),
                Lens("amplitude", "|A|（穴が芯）", "high", 0.0, 1.4)],
        perturbs=[PERTURB_SEED, PERTURB_CUT, PERTURB_KICK],
        put_in=["一様な振動＋ノイズ"], source="docs/WHITE_CEILINGS.md", ceiling_ref="cgl",
        defaults=dict(cgl.DEFAULTS), _init=init, _step=step, _lens=lens, _metrics=metrics, _perturb=perturb,
        _cache=cache)


def _swift_hohenberg():
    from genesis.models import swift_hohenberg as sh
    N = 64

    def cache(p):
        return {"k2": sh._k2(N, p["dx"])}

    def init(seed, knobs, p):
        rng = np.random.default_rng(seed)
        return {"u": sh.make_initial((N, N), knobs.get("noise", 1e-3), rng, p)}

    def step(s, t, p, cache):
        return {"u": sh.step(s["u"], p, cache["k2"])}

    def lens(name, s):
        return s["u"]

    def metrics(s):
        st = sh.individual_stats(s["u"])
        cy, cx = st["centroid"]
        return {"area": float(st["area"]), "peaks": st["peaks"], "amax": st["amax"], "cy": float(cy), "cx": float(cx)}

    def perturb(name, a, s, p, rng):
        u = s["u"].copy()
        if name == "cut_half":
            u[_half(u)] = 0.0
        elif name == "drop_seed":
            u = u + p["seed_amp"] * _gauss((N, N), a["y"] * N, a["x"] * N, p["seed_width"] / p["dx"])
        else:
            return _kick(s, ["u"], a["amp"], rng)
        return {"u": u}

    return White(
        id="sh", title="半分に切られても治る個体（Swift-Hohenberg・2D）", family="Swift-Hohenberg",
        model="genesis.models.swift_hohenberg", dimension=2, grid=(N, N), steps_per_frame=40,
        knobs=[Knob("r", "背景の安定さ r", "law", -0.4, -1.0, 0.2, 0.01),
               Knob("b", "非線形 b", "law", 2.0, 0.5, 3.0, 0.05),
               Knob("noise", "はじめのノイズ", "start", 1e-3, 0.0, 0.05, 1e-4),
               Knob("seed_amp", "ふくらみの高さ", "start", 1.2, 0.2, 2.5, 0.1),
               Knob("seed_width", "ふくらみの幅", "start", 3.0, 1.0, 8.0, 0.25)],
        lenses=[Lens("u", "u", "diverging", -0.3, 1.45)],
        perturbs=[PERTURB_CUT, PERTURB_SEED, PERTURB_KICK],
        put_in=["対称なふくらみ一つ（局在の種は置いた）"], source="docs/WHITE_CEILINGS.md · tests/test_lawclass.py",
        ceiling_ref="swift_hohenberg", defaults=dict(sh.DEFAULTS), _init=init, _step=step, _lens=lens,
        _metrics=metrics, _perturb=perturb, _cache=cache)


_BUILDERS = [_tdgl, _gpe_ring, _gray_scott, _three_component, _cgl, _swift_hohenberg]
_REGISTRY: dict[str, White] | None = None


def registry() -> dict[str, White]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = {w.id: w for w in (b() for b in _BUILDERS)}
    return _REGISTRY


def get(white_id: str) -> White:
    try:
        return registry()[white_id]
    except KeyError:
        raise KeyError(f"unknown white {white_id!r}; known: {sorted(registry())}") from None
