"""Export the Aquarium (水槽) templates: short t=0 replays of whites, recorded for display.

Every template re-runs its white FROM t=0 with a fixed seed and the unchanged model code (or, for the
official g002 room, copies that room's own recorded t=0 run), and records a handful of lens frames with
genesis/recording/recorder.FieldRecorder (downsampled, uint8, honesty flags). Nothing here changes
physics; recording is read-only w.r.t. the simulation.

    python tools/export_aquarium.py                 # all templates -> app/public/aquarium/
    python tools/export_aquarium.py sh-localized    # one template

Output: app/public/aquarium/templates.json + app/public/aquarium/<id>/field.json (committed; small).
The "put_in" / "emerged" / level / tier text of each template follows the cited experiment or doc.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from genesis.recording.recorder import FieldRecorder  # noqa: E402

_OUT = _REPO / "app" / "public" / "aquarium"
N_FRAMES = 36


def _schedule(total: int, n: int = N_FRAMES) -> set[int]:
    return {int(round(x)) for x in np.linspace(0, total, n)}


# --------------------------------------------------------------------------- recipes
def tdgl_quench_3d():
    from genesis.models import ginzburg_landau as gl
    edge, steps, seed = 48, 420, 0
    p = dict(gl.DEFAULTS)
    rng = np.random.default_rng(seed)
    psi = gl.make_initial((edge,) * 3, p["noise_amplitude"], rng)
    rec = (FieldRecorder(3, (edge,) * 3).declare("density", "abs(psi)^2", "n")
           .declare("phase", "arg(psi)", "rad", cyclic=True))
    marks = _schedule(steps)
    for s in range(steps + 1):
        if s in marks:
            rec.add(s * p["dt"], {"density": np.abs(psi) ** 2, "phase": np.angle(psi)})
        if s < steps:
            psi = gl.step(psi, s * p["dt"], p)
    return rec, {"model": "genesis.models.ginzburg_landau", "grid": [edge] * 3, "steps": steps, "dt": p["dt"],
                 "seed": seed, "noise_amplitude": p["noise_amplitude"], "quench_duration": p["quench_duration"]}


def gpe_vortex_ring_3d():
    from core import field
    from core.fft import k_squared_3d
    L, R, g, mu, dtau, n_imag, dt, n_real = 48, 7, 1.0, 1.0, 0.05, 120, 0.1, 800
    k2 = k_squared_3d(L)
    phase0 = field.vortex_ring_phase(L, R, charge=1)
    psi = np.sqrt(mu) * np.exp(1j * phase0)
    norm0 = np.sum(np.abs(psi) ** 2)
    for _ in range(n_imag):  # e003 preparation (before t=0): shape the core while pinning the ring
        psi = field.step_imag_3d(psi, 0.0, k2, g, mu, dtau)
        psi *= np.sqrt(norm0 / np.sum(np.abs(psi) ** 2))
        psi = np.abs(psi) * np.exp(1j * phase0)
    rec = (FieldRecorder(3, (L,) * 3).declare("density", "abs(psi)^2", "n")
           .declare("phase", "arg(psi)", "rad", cyclic=True))
    marks = _schedule(n_real)
    for s in range(n_real + 1):
        if s in marks:
            rec.add(s * dt, {"density": np.abs(psi) ** 2, "phase": np.angle(psi)})
        if s < n_real:
            psi = field.step_real_3d(psi, 0.0, k2, g, mu, dt)
    return rec, {"source": "experiments/e003_gpe_vortex_ring (QUICK)", "L": L, "R": R, "n_imag": n_imag, "dt": dt,
                 "steps": n_real}


def sh_localized():
    from genesis.models import swift_hohenberg as sh
    N, settle, regrow, seed = 64, 2500, 2500, 0
    p = dict(sh.DEFAULTS)
    k2 = sh._k2(N, p["dx"])
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    rec = FieldRecorder(2, (N, N)).declare("u", "u", "1")
    total = settle + regrow
    marks = _schedule(total)
    for s in range(total + 1):
        if s == settle:
            u = u.copy()
            u[: N // 2, :] = 0.0  # the perturbation of the L4 self-repair test (tests/test_lawclass.py)
        if s in marks:
            rec.add(s * p["dt"], {"u": u})
        if s < total:
            u = sh.step(u, p, k2)
    return rec, {"model": "genesis.models.swift_hohenberg", "N": N, "settle": settle, "cut_half_at_step": settle,
                 "regrow": regrow, "seed": seed}


def gray_scott_split():
    from genesis.models import gray_scott as gs
    N, steps, seed = 96, 12000, 0
    p = dict(gs.DEFAULTS)
    rng = np.random.default_rng(seed)
    U, V = gs.make_initial((N, N), p["n_seeds"], rng, seed_radius=p["seed_radius"])
    rec = FieldRecorder(2, (N, N)).declare("V", "V", "1")
    marks = _schedule(steps)
    for s in range(steps + 1):
        if s in marks:
            rec.add(s * p["dt"], {"V": V})
        if s < steps:
            U, V = gs.step(U, V, p)
    return rec, {"model": "genesis.models.gray_scott", "N": N, "steps": steps, "seed": seed,
                 "F": p["F"], "k": p["k"]}


def three_component_frontier():
    from genesis.models import three_component_rd as t3
    N, steps, seed = 96, 8000, 1
    p = dict(t3.DEFAULTS)
    k2 = t3._k2(N)
    rng = np.random.default_rng(seed)
    u, v, w = t3.make_initial((N, N), 1e-3, rng, p)
    rec = FieldRecorder(2, (N, N)).declare("u", "u", "1").declare("w", "w", "1")
    marks = _schedule(steps)
    for s in range(steps + 1):
        if s in marks:
            rec.add(s * p["dt"], {"u": u, "w": w})
        if s < steps:
            u, v, w = t3.step(u, v, w, p, k2)
    return rec, {"model": "genesis.models.three_component_rd", "N": N, "steps": steps, "seed": seed}


def cgl_spirals():
    from genesis.models import complex_ginzburg_landau as cgl
    N, steps, seed = 96, 5000, 0
    p = dict(cgl.DEFAULTS)
    k2 = cgl._k2((N, N))
    rng = np.random.default_rng(seed)
    A = cgl.make_initial((N, N), 1e-2, rng)
    rec = (FieldRecorder(2, (N, N)).declare("phase", "arg(A)", "rad", cyclic=True)
           .declare("amplitude", "abs(A)", "1"))
    marks = _schedule(steps)
    for s in range(steps + 1):
        if s in marks:
            rec.add(s * p["dt"], {"phase": np.angle(A), "amplitude": np.abs(A)})
        if s < steps:
            A = cgl.step(A, p, k2)
    return rec, {"model": "genesis.models.complex_ginzburg_landau", "N": N, "steps": steps, "seed": seed,
                 "b": p["b"], "c": p["c"]}


def gpe_dipole():
    from core import field
    from core.fft import k_squared
    from experiments.e052_dipole_self_propulsion.dipole_self_propulsion import FROZEN
    L, tauQ, hold, post, seed = 96, 200, 150, 1600, 1
    p = FROZEN
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    rec = (FieldRecorder(2, (L, L)).declare("amplitude", "abs(psi)", "1")
           .declare("phase", "arg(psi)", "rad", cyclic=True))
    total = tauQ + hold + post
    marks = _schedule(total)
    for s in range(total + 1):
        if s in marks:
            rec.add(s * p["dt"], {"amplitude": np.abs(psi), "phase": np.angle(psi)})
        if s < total:
            mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / tauQ)
            psi = field.step_damped_2d(psi, V, k2, p["g"], mu, p["dt"], p["gamma"])
    return rec, {"source": "experiments/e052_dipole_self_propulsion (run_one_seed recipe)", "L": L, "tauQ": tauQ,
                 "hold": hold, "post_steps": post, "seed": seed}


def convection_official():
    """Copy the official room's own recorded t=0 run (no re-run needed)."""
    src = _REPO / "rooms" / "official" / "room-g002-a" / "runs" / "seed-0000" / "field.json"
    return src, {"room": "rooms/official/room-g002-a", "run": "seed-0000", "Ra": 1000, "N": 48}


# --------------------------------------------------------------------------- template registry
TEMPLATES = [
    dict(id="tdgl-quench-3d", recipe=tdgl_quench_3d, dimension=3, white="g001 TDGL",
         title="渦の糸が生まれる（冷やした場・3D）",
         caption="一様な場にごく小さなノイズだけを入れて冷やすと、場所ごとに違う向きがそろい始め、そろい切れない所に「渦の糸」が残ります。明るい糸が渦の芯（|ψ| が小さい所）です。",
         put_in=["一様な場＋ごく小さなノイズ", "冷却（クエンチ）の強さと速さ"],
         emerged=["向きのそろった領域（対称性の破れ・L1）", "渦の糸（位相の巻き・L2）"],
         level="L2", tier="measured", source="rooms/official/room-g001-a · docs/WHITE_CEILINGS.md",
         lenses=[{"name": "density", "label": "渦の芯（|ψ|² が小さい所）", "transfer": "low"},
                 {"name": "phase", "label": "位相（向き）", "transfer": "cyclic"}], default_lens="density"),
    dict(id="gpe-vortex-ring-3d", recipe=gpe_vortex_ring_3d, dimension=3, white="GPE（超流体）",
         title="渦の輪が自分で進む（3D）",
         caption="超流体の中に置いた渦の輪は、誰にも押されずに自分の軸の方向へ進みます。輪そのものは置いたもの、進むことは方程式から出てきたものです。",
         put_in=["渦の輪（半径 7 の形を置いた）", "輪の芯の形を整える準備（t=0 より前）",
                 "円板状の影＝輪を置いたときの位相の継ぎ目（手法の作り物・e003 AUDIT）"],
         emerged=["輪がほぼ一定の半径で軸方向に進む（自己伝播）"],
         level="L3（運動・置いた輪）", tier="measured / analogy", source="experiments/e003_gpe_vortex_ring/AUDIT.md",
         lenses=[{"name": "density", "label": "渦の芯（|ψ|² が小さい所）", "transfer": "low"},
                 {"name": "phase", "label": "位相", "transfer": "cyclic"}], default_lens="density"),
    dict(id="gpe-dipole-2d", recipe=gpe_dipole, dimension=2, white="damped GPE",
         title="渦のペアが泳ぎだす（2D）",
         caption="ノイズだけの場を冷やすと渦がたくさん生まれ、打ち消し合って減っていき、最後に残った ＋と− の渦のペアが並んで泳ぎだします。ペアは置いていません。",
         put_in=["ノイズだけの場", "冷却のしかた（μ の変化）"],
         emerged=["たくさんの渦（L2）", "対消滅で数が減る", "± の渦ペアの自己推進（L3・seed 1）"],
         level="L3", tier="measured", source="experiments/e052_dipole_self_propulsion/AUDIT.md",
         lenses=[{"name": "amplitude", "label": "|ψ|（穴が渦）", "transfer": "high"},
                 {"name": "phase", "label": "位相", "transfer": "cyclic"}], default_lens="phase"),
    dict(id="convection-2d", recipe=convection_official, dimension=2, white="g002 Boussinesq",
         title="温度差から対流がはじまる（2D）",
         caption="静かな流体に下から温度差をかけると、ゆらぎが育って対流の渦（ロール）ができ、熱を運び始めます。",
         put_in=["静止した流体＋ノイズ", "上下の温度差（Ra=1000）"],
         emerged=["対流ロール（循環・L3）", "熱輸送の増加"],
         level="L3（大域）", tier="measured", source="rooms/official/room-g002-a",
         lenses=[{"name": "temperature", "label": "温度", "transfer": "diverging"},
                 {"name": "vorticity", "label": "渦度", "transfer": "diverging"}], default_lens="temperature"),
    dict(id="sh-localized", recipe=sh_localized, dimension=2, white="Swift-Hohenberg",
         title="半分に切られても治る個体（2D）",
         caption="一つのふくらみから、境界と模様をもった「個体」が育ちます。途中で上半分を消しても、同じ形に治ります。ただし自分では動きません。",
         put_in=["対称なふくらみ一つ（局在の種は置いた）", "途中で上半分を消す（修復テストの摂動）"],
         emerged=["内外の差・持続・サイズに依存しない形", "自己修復（L4-static）"],
         level="L4-static", tier="measured", source="docs/WHITE_CEILINGS.md · tests/test_lawclass.py",
         lenses=[{"name": "u", "label": "u", "transfer": "diverging"}], default_lens="u"),
    dict(id="gray-scott-split", recipe=gray_scott_split, dimension=2, white="Gray-Scott",
         title="点が分かれて増える（2D）",
         caption="いくつかの小さな点が、育っては二つに分かれて増えていきます。ただし分かれた点は中身（受け継ぐ違い）を持たないので、「遺伝」ではありません。",
         put_in=["8 つの小さな点（種）"],
         emerged=["点の成長と分裂（自己複製・L7-partial）"],
         level="L7-partial", tier="measured", source="docs/WHITE_CEILINGS.md",
         lenses=[{"name": "V", "label": "V の濃さ", "transfer": "high"}], default_lens="V"),
    dict(id="cgl-spirals", recipe=cgl_spirals, dimension=2, white="CGL",
         title="らせんが回り、乱れる（2D）",
         caption="振動する場にノイズを入れると、らせん状の波とその中心（穴）が生まれて動き回り、乱流になります。動くけれど、まとまった個体にはなりません。",
         put_in=["一様な振動＋ノイズ"],
         emerged=["らせんの芯（L2）", "芯が動き回る乱流（< L4）"],
         level="L2＋乱流運動", tier="measured", source="docs/WHITE_CEILINGS.md",
         lenses=[{"name": "phase", "label": "位相", "transfer": "cyclic"},
                 {"name": "amplitude", "label": "|A|（穴が芯）", "transfer": "high"}], default_lens="phase"),
    dict(id="three-component-frontier", recipe=three_component_frontier, dimension=2, white="三成分反応拡散",
         title="最前線：自分で動く個体は出るか（2D）",
         caption="「まとまり」と「自分で動く」を一つの白で同時に得られるかを試す場です。この条件では、点は分かれて増えてしまい、一つの個体が泳ぐところまでは届いていません（未達・frontier）。",
         put_in=["対称なふくらみ一つ＋ノイズ"],
         emerged=["点の形成と分裂（この条件）", "単一個体の自走は未確認"],
         level="frontier", tier="frontier", source="docs/WHITE_CEILINGS.md · docs/ANGULAR_MODES.md",
         lenses=[{"name": "u", "label": "u（活性）", "transfer": "high"},
                 {"name": "w", "label": "w（遅い抑制＝航跡）", "transfer": "high"}], default_lens="u"),
]


def export(ids: list[str] | None = None) -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for spec in TEMPLATES:
        entry = {k: v for k, v in spec.items() if k != "recipe"}
        if ids and spec["id"] not in ids:
            prev = _OUT / spec["id"] / "field.json"
            if not prev.exists():
                continue
            old = json.loads((_OUT / "templates.json").read_text())["templates"]
            entry["recipe"] = next(t["recipe"] for t in old if t["id"] == spec["id"])
            index.append(entry)
            continue
        t0 = time.time()
        out, recipe = spec["recipe"]()
        d = _OUT / spec["id"]
        d.mkdir(exist_ok=True)
        if isinstance(out, Path):
            shutil.copyfile(out, d / "field.json")
        else:
            out.write_field(str(d))
        entry["recipe"] = recipe
        index.append(entry)
        size = (d / "field.json").stat().st_size
        print(f"  {spec['id']:<26} {time.time() - t0:6.1f}s  {size / 2**20:5.2f} MB", flush=True)
    (_OUT / "templates.json").write_text(json.dumps({"version": 1, "templates": index}, ensure_ascii=False, indent=2),
                                         encoding="utf-8")


if __name__ == "__main__":
    export(sys.argv[1:] or None)
