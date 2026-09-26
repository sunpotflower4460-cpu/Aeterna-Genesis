"""Does a torus grow by itself? (P11, 3D first, then 2D) -- vortex rings from a quench of the damped superfluid.

    python tools/torus_birth.py --out /tmp/torus_birth            # 3D (then run with --dim 2)

Law: damped GPE, local (genesis/models/gpe_local.py), g = μ = 1 (healing length ξ = 1). t = 0: ψ ≈ 0 + noise
0.01. Put in: the law and the bath coupling γ. No vortex, ring or shape is put in.

3D (n³ periodic box, seeds 1–3, γ = 0.03 and 0.01): every 5 t, every connected piece of vortex line
(genesis/diagnostics/vortex_rings.py) with its topology. A RING (a torus: closed, not around the box, genus 1,
flat and round) is tracked from frame to frame (nearest centroid within 3 cells, radius within 35%). For each
tracked ring: when it was born and last seen, its radius, how far it travelled along its own axis, its speed
compared with Kelvin's law for a superfluid vortex ring v = (ln(8R/ξ) − 0.615)/(2R), and whether it moves the
same way as the flow through its hole (v·n at the centroid) -- the doughnut circulation: through the hole
one way, around the outside back.
2D (n², same law): vortex–antivortex pairs are the cross-section of a ring. Counted: pairs of opposite
vortices closer than 6 cells to each other than to anything else, tracked, speed compared with 1/d (d = the
distance between the two), which is the 2D (straight, not curved) version of the same motion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics import vortex_rings as vr
from genesis.models import gpe_local as gl
from tools.snapshot import render_field


def kelvin(R: float, xi: float = 1.0) -> float:
    return (np.log(8 * R / xi) - 0.615) / (2 * R)


def _mi(a, b, L):
    d = np.asarray(a) - np.asarray(b)
    return d - L * np.round(d / L)


def flow_through_hole(v: np.ndarray, cen, axis, L: int) -> float:
    i = tuple(int(round(c)) % L for c in cen)
    vv = np.array([v[k][i] for k in range(3)])
    return float(vv @ np.asarray(axis))


def run3d(n: int, gamma: float, seed: int, T: float, every: float = 5.0, out: Path | None = None) -> dict:
    p = dict(gl.DEFAULTS, gamma=gamma)
    psi = gl.make_initial((n, n, n), np.random.default_rng(seed), p)
    frames, tracks, best_psi, best_count = [], [], None, -1
    stride = int(round(every / p["dt"]))
    for k in range(int(round(T / p["dt"])) + 1):
        if k % stride == 0 and np.abs(psi).mean() > 0.7:
            t = round(k * p["dt"], 1)
            pieces = vr.rings(psi)
            v = gl.velocity(psi)
            rings = [r for r in pieces if r["ring"]]
            for r in rings:
                r["flow"] = flow_through_hole(v, r["centroid"], r["axis"], n)
            frames.append({"t": t, "pieces": len(pieces), "rings": len(rings),
                           "wrapping": sum(r["wraps"] for r in pieces),
                           "line_voxels": int(sum(r["voxels"] for r in pieces))})
            for r in rings:                                         # link to an open track
                cand = [tr for tr in tracks if tr["last_t"] == round(t - every, 1)
                        and np.linalg.norm(_mi(r["centroid"], tr["pos"][-1], n)) < 3.0
                        and abs(r["radius"] - tr["R"][-1]) < 0.35 * tr["R"][-1]]
                if cand:
                    tr = min(cand, key=lambda tr: np.linalg.norm(_mi(r["centroid"], tr["pos"][-1], n)))
                    tr["last_t"] = t
                else:
                    tr = {"born": t, "last_t": t, "pos": [], "R": [], "axis": [], "flow": []}
                    tracks.append(tr)
                tr["pos"].append(r["centroid"]), tr["R"].append(r["radius"])
                tr["axis"].append(r["axis"]), tr["flow"].append(r["flow"])
            if len(rings) > best_count:
                best_count, best_psi = len(rings), psi.copy()
        psi = gl.step(psi, p)
    res_tracks = []
    for tr in tracks:
        if len(tr["pos"]) < 3:
            continue
        ax = np.mean([np.sign(np.dot(a, tr["axis"][0])) * np.asarray(a) for a in tr["axis"]], axis=0)
        ax /= np.linalg.norm(ax)
        steps = [_mi(b, a, n) for a, b in zip(tr["pos"][:-1], tr["pos"][1:])]
        along = float(sum(np.dot(s, ax) for s in steps))
        dur = tr["last_t"] - tr["born"]
        flow = float(np.mean([np.sign(np.dot(a, ax)) * f for a, f in zip(tr["axis"], tr["flow"])]))
        R = float(np.mean(tr["R"]))
        res_tracks.append({"born": tr["born"], "last": tr["last_t"], "frames": len(tr["pos"]), "R_mean": round(R, 2),
                           "R_first_last": [round(tr["R"][0], 2), round(tr["R"][-1], 2)],
                           "travel_along_axis": round(along, 2), "speed": round(abs(along) / dur, 4) if dur else 0.0,
                           "kelvin": round(kelvin(R), 4), "flow_through_hole": round(flow, 4),
                           "moves_with_the_flow": bool(np.sign(along) == np.sign(flow)) if along and flow else None})
    if out is not None and best_psi is not None:
        m = vr.line_mask(best_psi)
        render_field(m.max(axis=2).astype(float), str(out / f"lines3d_n{n}_g{gamma}_s{seed}.png"))
    return {"dim": 3, "n": n, "gamma": gamma, "seed": seed, "T": T, "frames": frames, "tracks": res_tracks}


def vortices_2d(psi: np.ndarray) -> list[tuple[float, float, int]]:
    """(y, x, sign) at the centre of every plaquette with a phase winding (periodic)."""
    ph = np.angle(psi)
    dy = (np.roll(ph, -1, 0) - ph + np.pi) % (2 * np.pi) - np.pi
    dx = (np.roll(ph, -1, 1) - ph + np.pi) % (2 * np.pi) - np.pi
    w = np.rint((dy + np.roll(dx, -1, 0) - np.roll(dy, -1, 1) - dx) / (2 * np.pi)).astype(int)
    return [(y + 0.5, x + 0.5, int(np.sign(w[y, x]))) for y, x in np.argwhere(w != 0)]


def pairs_2d(vs, n: int, dmax: float = 6.0) -> list[dict]:
    """Opposite vortices that are each other's nearest vortex, closer than dmax, with every other vortex at
    least 1.5 d away from both: an isolated ± pair (the cross-section of a ring)."""
    if len(vs) < 2:
        return []
    P = np.array([v[:2] for v in vs])
    D = np.linalg.norm(_mi(P[:, None, :], P[None, :, :], n), axis=2)
    np.fill_diagonal(D, np.inf)
    out = []
    for i in range(len(vs)):
        j = int(np.argmin(D[i]))
        if j <= i or int(np.argmin(D[j])) != i or vs[i][2] == vs[j][2] or D[i, j] > dmax:
            continue
        others = np.delete(np.minimum(D[i], D[j]), [i, j])
        if len(others) and others.min() < 1.5 * D[i, j]:
            continue
        mid = (P[i] + _mi(P[j], P[i], n) / 2) % n
        out.append({"mid": mid, "d": float(D[i, j]), "sep": _mi(P[j], P[i], n) * (1 if vs[i][2] > 0 else -1)})
    return out


def run2d(n: int, gamma: float, seed: int, T: float, every: float = 5.0) -> dict:
    p = dict(gl.DEFAULTS, gamma=gamma)
    psi = gl.make_initial((n, n), np.random.default_rng(seed), p)
    frames, tracks = [], []
    stride = int(round(every / p["dt"]))
    for k in range(int(round(T / p["dt"])) + 1):
        if k % stride == 0 and np.abs(psi).mean() > 0.7:
            t = round(k * p["dt"], 1)
            vs = vortices_2d(psi)
            prs = pairs_2d(vs, n)
            v = gl.velocity(psi)
            frames.append({"t": t, "vortices": len(vs), "pairs": len(prs)})
            for pr in prs:
                i = tuple(int(c) % n for c in pr["mid"])
                pr["flow"] = np.array([v[0][i], v[1][i]])
                cand = [tr for tr in tracks if tr["last_t"] == round(t - every, 1)
                        and np.linalg.norm(_mi(pr["mid"], tr["pos"][-1], n)) < 3.0
                        and abs(pr["d"] - tr["d"][-1]) < 0.35 * tr["d"][-1]]
                if cand:
                    tr = min(cand, key=lambda tr: np.linalg.norm(_mi(pr["mid"], tr["pos"][-1], n)))
                    tr["last_t"] = t
                else:
                    tr = {"born": t, "last_t": t, "pos": [], "d": [], "flow": []}
                    tracks.append(tr)
                tr["pos"].append(pr["mid"]), tr["d"].append(pr["d"]), tr["flow"].append(pr["flow"])
        psi = gl.step(psi, p)
    res = []
    for tr in tracks:
        if len(tr["pos"]) < 3:
            continue
        disp = sum(_mi(b, a, n) for a, b in zip(tr["pos"][:-1], tr["pos"][1:]))
        dur = tr["last_t"] - tr["born"]
        d = float(np.mean(tr["d"]))
        flow = np.mean(tr["flow"], axis=0)
        res.append({"born": tr["born"], "last": tr["last_t"], "frames": len(tr["pos"]), "d_mean": round(d, 2),
                    "travel": round(float(np.linalg.norm(disp)), 2),
                    "speed": round(float(np.linalg.norm(disp)) / dur, 4) if dur else 0.0,
                    "point_vortex": round(1.0 / d, 4),
                    "moves_with_the_flow": bool(np.dot(disp, flow) > 0)})
    return {"dim": 2, "n": n, "gamma": gamma, "seed": seed, "T": T, "frames": frames, "tracks": res}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--T", type=float, default=800.0)
    ap.add_argument("--gamma", type=float, default=0.03)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.dim == 2:
        r = run2d(a.n, a.gamma, a.seed, a.T)
        long = [tr for tr in r["tracks"] if tr["last"] - tr["born"] >= 20]
        print(f"2D n={a.n} γ={a.gamma} seed={a.seed}: vortices (every 100 t) {[f['vortices'] for f in r['frames']][::20]}"
              f" | isolated ± pairs per frame {[f['pairs'] for f in r['frames']][::20]} | tracked pairs {len(r['tracks'])},"
              f" living ≥ 20 t: {len(long)}", flush=True)
        for tr in sorted(r["tracks"], key=lambda x: x["born"] - x["last"])[:8]:
            print("   ", tr, flush=True)
        (out / f"torus2d_n{a.n}_g{a.gamma}_s{a.seed}.json").write_text(json.dumps(r, indent=1))
        return 0
    r = run3d(a.n, a.gamma, a.seed, a.T, out=out)
    long = [tr for tr in r["tracks"] if tr["last"] - tr["born"] >= 20]
    print(f"3D n={a.n} γ={a.gamma} seed={a.seed}: rings per frame (every 50 t) "
          f"{[f['rings'] for f in r['frames']][::10]} | line voxels {[f['line_voxels'] for f in r['frames']][::10]}"
          f" | tracked rings (≥3 frames) {len(r['tracks'])}, living ≥ 20 t: {len(long)}", flush=True)
    for tr in sorted(r["tracks"], key=lambda x: x["born"] - x["last"])[:8]:
        print("   ", tr, flush=True)
    (out / f"torus3d_n{a.n}_g{a.gamma}_s{a.seed}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
