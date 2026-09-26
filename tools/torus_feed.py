"""A torus that does not disappear? (P12, 3D first, then 2D) -- an obstacle moving through the superfluid feeds it.

    python tools/torus_feed.py --out /tmp/feed --U 0.6 --seed 1                 # 3D
    python tools/torus_feed.py --out /tmp/feed --U 0.6 --seed 1 --dim 2         # 2D

Law: damped GPE, local (genesis/models/gpe_local.py), g = μ = 1 (sound speed c = 1, healing length ξ = 1),
γ = 0.01. Put in:
* t = 0: the uniform condensate at rest (ψ = 1) + noise 0.01. (P11 showed that the quench from ψ ≈ 0 settles
  here; starting from it saves time.)
* an obstacle: V = V0·exp(−r²/2w²), V0 = 5, w = 2.5 (a sphere in 3D, a disk in 2D), moving along the long axis at
  speed U (reached by a linear ramp over the first 50 t), around the periodic box again and again. Pushing it
  at constant speed is the external supply: energy flows in only one way, from whatever pushes the obstacle.
Nothing else is put in. Known physics: below a critical speed the flow goes round the obstacle; above it the
obstacle sheds vortex rings (3D) or vortex pairs / streets (2D) for as long as it keeps moving.

Measured every 5 t (the obstacle's inside, V > 0.5, is excluded from the vortex search):
3D -- vortex-line pieces and rings (genesis/diagnostics/vortex_rings.py); rings tracked as in P11; for each:
      where it was born relative to the obstacle, radius, lifetime, travel along its axis relative to the fluid
      at rest, whether it moves with the flow through its hole; rings that stay within 10 cells of the obstacle
      for ≥ 100 t ("attached"); births per 100 t in the first and second half; the fraction of frames with no ring.
2D -- vortex count, isolated ± pairs, births of vortices near the obstacle per 100 t, the sign pattern of shed
      vortices (pairs or an alternating street).
Both: the drag force on the obstacle F = −Σ|ψ|²∂V and the power put in, F·U.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics import vortex_rings as vr
from genesis.models import gpe_local as gl
from tools.snapshot import render_field
from tools.torus_birth import _mi, kelvin, pairs_2d, vortices_2d

V0, W, RAMP = 5.0, 2.5, 50.0


def obstacle(shape, pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """V on the grid and ∂V/∂(long axis) (the long axis is the last one), periodic minimum image."""
    grids = np.meshgrid(*[np.arange(n, dtype=float) for n in shape], indexing="ij")
    d = [(g - c + n / 2) % n - n / 2 for g, c, n in zip(grids, pos, shape)]
    V = V0 * np.exp(-sum(x * x for x in d) / (2 * W * W))
    return V, -d[-1] / (W * W) * V


def position(shape, t: float, U: float) -> np.ndarray:
    L = shape[-1]
    travelled = U * t * t / (2 * RAMP) if t < RAMP else U * (t - RAMP / 2)
    return np.array([n / 2 - 0.5 for n in shape[:-1]] + [(L / 4 + travelled) % L])


def run(dim: int, U: float, seed: int, T: float, gamma: float = 0.01, every: float = 5.0, out: Path | None = None,
        shape: tuple[int, ...] | None = None):
    shape = shape or ((48, 48, 128) if dim == 3 else (128, 256))
    p = dict(gl.DEFAULTS, gamma=gamma)
    rng = np.random.default_rng(seed)
    psi = 1.0 + 0j + p["noise"] * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    stride = int(round(every / p["dt"]))
    frames, tracks, last_img = [], [], None
    for k in range(int(round(T / p["dt"])) + 1):
        t = k * p["dt"]
        pos = position(shape, t, U)
        V, dV = obstacle(shape, pos)
        if k % stride == 0:
            inside = V > 0.5
            drag = float(-(np.abs(psi) ** 2 * dV).sum())
            speed = U * min(1.0, t / RAMP)
            fr = {"t": round(t, 1), "drag": round(drag, 4), "power": round(drag * speed, 4)}
            if dim == 3:
                pieces = vr.rings(psi, exclude=inside)
                rings = [r for r in pieces if r["ring"]]
                v = gl.velocity(psi)
                fr.update(pieces=len(pieces), rings=len(rings), line_voxels=int(sum(r["voxels"] for r in pieces)))
                for r in rings:
                    i = tuple(int(round(c)) % n for c, n in zip(r["centroid"], shape))
                    r["flow"] = float(np.array([v[a][i] for a in range(3)]) @ np.asarray(r["axis"]))
                    r["from_obstacle"] = float(np.linalg.norm(_mi(np.array(r["centroid"]), pos, np.array(shape))))
                    cand = [tr for tr in tracks if tr["last_t"] == round(t - every, 1)
                            and np.linalg.norm(_mi(np.array(r["centroid"]), tr["pos"][-1], np.array(shape))) < 4.0
                            and abs(r["radius"] - tr["R"][-1]) < 0.35 * tr["R"][-1]]
                    if cand:
                        tr = min(cand, key=lambda tr: np.linalg.norm(_mi(np.array(r["centroid"]), tr["pos"][-1],
                                                                         np.array(shape))))
                        tr["last_t"] = round(t, 1)
                    else:
                        tr = {"born": round(t, 1), "last_t": round(t, 1), "pos": [], "R": [], "axis": [], "flow": [],
                              "dist": []}
                        tracks.append(tr)
                    tr["pos"].append(np.array(r["centroid"])), tr["R"].append(r["radius"])
                    tr["axis"].append(r["axis"]), tr["flow"].append(r["flow"]), tr["dist"].append(r["from_obstacle"])
                if rings:
                    last_img = vr.line_mask(psi, 1, inside).max(axis=0).astype(float) + 0.3 * (V.max(axis=0) > 0.5)
            else:
                vs = [x for x in vortices_2d(psi) if not inside[int(x[0]) % shape[0], int(x[1]) % shape[1]]]
                near = [x for x in vs if np.linalg.norm(_mi(np.array(x[:2]), pos, np.array(shape))) < 3 * W + 4]
                fr.update(vortices=len(vs), pairs=len(pairs_2d(vs, min(shape))), near=len(near),
                          near_signs=sorted(int(x[2]) for x in near))
                last_img = np.angle(psi)
            frames.append(fr)
        psi = gl.step(psi, p, V)
    res = {"dim": dim, "U": U, "seed": seed, "T": T, "gamma": gamma, "shape": list(shape), "frames": frames}
    half = T / 2
    if dim == 3:
        rt = []
        for tr in tracks:
            if len(tr["pos"]) < 3:
                continue
            ax = np.mean([np.sign(np.dot(a, tr["axis"][0])) * np.asarray(a) for a in tr["axis"]], axis=0)
            ax /= np.linalg.norm(ax)
            steps = [_mi(b, a, np.array(shape)) for a, b in zip(tr["pos"][:-1], tr["pos"][1:])]
            along = float(sum(np.dot(s, ax) for s in steps))
            dur = tr["last_t"] - tr["born"]
            flow = float(np.mean([np.sign(np.dot(a, ax)) * f for a, f in zip(tr["axis"], tr["flow"])]))
            R = float(np.mean(tr["R"]))
            rt.append({"born": tr["born"], "last": tr["last_t"], "R_mean": round(R, 2),
                       "born_from_obstacle": round(tr["dist"][0], 1), "min_dist": round(min(tr["dist"]), 1),
                       "max_dist": round(max(tr["dist"]), 1), "last_dist": round(tr["dist"][-1], 1),
                       "frames": len(tr["pos"]),
                       "travel_along_axis": round(along, 2), "speed": round(abs(along) / dur, 4) if dur else 0.0,
                       "kelvin": round(kelvin(R), 4),
                       "moves_with_the_flow": bool(np.sign(along) == np.sign(flow)) if along and flow else None,
                       "attached": bool(dur >= 100 and max(tr["dist"]) < 10.0)})
        res["tracks"] = rt
        born_near = [tr for tr in rt if tr["born_from_obstacle"] < 12.0]
        res["births_first_half"] = sum(1 for tr in born_near if RAMP <= tr["born"] < half)
        res["births_second_half"] = sum(1 for tr in born_near if tr["born"] >= half)
        late = [f for f in frames if f["t"] >= half]
        res["frames_without_ring_late"] = round(sum(1 for f in late if f["rings"] == 0) / max(len(late), 1), 3)
        res["attached"] = sum(tr["attached"] for tr in rt)
    else:
        late = [f for f in frames if f["t"] >= half]
        res["mean_vortices_late"] = round(float(np.mean([f["vortices"] for f in late])), 2)
        res["mean_pairs_late"] = round(float(np.mean([f["pairs"] for f in late])), 2)
        res["frames_with_vortices_near_late"] = round(sum(1 for f in late if f["near"] > 0) / max(len(late), 1), 3)
    res["mean_power_late"] = round(float(np.mean([f["power"] for f in frames if f["t"] >= half])), 4)
    if out is not None and last_img is not None:
        render_field(last_img, str(out / f"feed{dim}d_U{U}_s{seed}.png"), px=720)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--U", type=float, default=0.6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=800.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = run(a.dim, a.U, a.seed, a.T, out=out)
    if a.dim == 3:
        tr = r["tracks"]
        print(f"3D U={a.U} seed={a.seed}: rings per frame (every 50 t) {[f['rings'] for f in r['frames']][::10]}"
              f" | tracked {len(tr)}, born near the obstacle: first half {r['births_first_half']}, second half"
              f" {r['births_second_half']} | frames without a ring (second half) {r['frames_without_ring_late']}"
              f" | attached {r['attached']} | with the hole flow {sum(1 for x in tr if x['moves_with_the_flow'])}/{len(tr)}"
              f" | power in (late) {r['mean_power_late']}", flush=True)
        for x in sorted(tr, key=lambda x: x["born"] - x["last"])[:6]:
            print("   ", x, flush=True)
    else:
        print(f"2D U={a.U} seed={a.seed}: vortices (every 50 t) {[f['vortices'] for f in r['frames']][::10]}"
              f" | isolated pairs {[f['pairs'] for f in r['frames']][::10]} | mean vortices late {r['mean_vortices_late']}"
              f" | frames with vortices near the obstacle (late) {r['frames_with_vortices_near_late']}"
              f" | power in (late) {r['mean_power_late']}", flush=True)
    (out / f"feed{a.dim}d_U{a.U}_s{a.seed}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
