"""Do tori of waves grow in an excitable medium (like heart or nerve tissue), and do they last? (P13, 3D first, 2D after)

    python tools/torus_excitable.py --out /tmp/exc --corr 6 --seed 1              # 3D
    python tools/torus_excitable.py --out /tmp/exc --corr 6 --seed 1 --dim 2      # 2D

Law: Barkley (genesis/models/excitable_barkley.py), a = 0.75, b = 0.06, ε = 0.02, dx = 0.8. t = 0: patchy random
excitation (u and v independent smooth random fields, patch size `corr` cells) -- no wave, spiral or ring is put
in. Every cell is fed locally by the reaction (the medium can fire again after resting), nothing is pushed from
outside.

Measured every 5 t:
3D -- the filaments (vortex lines of the phase of (u − u*, v − v*), genesis/diagnostics/vortex_rings.py), the
      scroll rings among them (genus 1, flat, round), tracked frame to frame (centroid within 4 cells, radius within
      35%): lifetime, radius over time, drift along the ring's axis; the fraction of the box that is firing (u > 0.5).
2D -- spiral tips (phase singularities), their number over time.
Both -- the RHYTHM: over the last 100 t, the times at which each cell fires (u crosses 0.5 upward), the median
      period per cell, and how much the period differs across the box (one rhythm for all = the waves come from
      one kind of source).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics import vortex_rings as vr
from genesis.models import excitable_barkley as eb
from tools.snapshot import render_field
from tools.torus_birth import _mi, vortices_2d


def run(dim: int, corr: float, seed: int, T: float, n: int | None = None, every: float = 5.0, out: Path | None = None):
    n = n or (64 if dim == 3 else 160)
    shape = (n,) * dim
    p = dict(eb.DEFAULTS, corr=corr)
    u, v = eb.make_initial(shape, np.random.default_rng(seed), p)
    stride = int(round(every / p["dt"]))
    steps = int(round(T / p["dt"]))
    t_rhythm = T - 100.0
    last_fire = np.full(shape, np.nan)
    period_sum = np.zeros(shape)
    period_cnt = np.zeros(shape)
    frames, tracks, fi = [], [], -1
    for k in range(steps + 1):
        t = k * p["dt"]
        if k % stride == 0:
            fi += 1                                          # frame index: links frames exactly (dt·stride ≠ every)
            fr = {"t": round(t, 1), "firing": round(float((u > 0.5).mean()), 4)}
            z = eb.phase_field(u, v)
            if dim == 3:
                pieces = vr.rings(z)
                rings = [r for r in pieces if r["ring"]]
                fr.update(filaments=len(pieces), rings=len(rings), wrapping=sum(r["wraps"] for r in pieces),
                          filament_voxels=int(sum(r["voxels"] for r in pieces)))
                for r in rings:
                    c = np.array(r["centroid"])
                    cand = [tr for tr in tracks if tr["last_f"] == fi - 1
                            and np.linalg.norm(_mi(c, tr["pos"][-1], np.array(shape))) < 4.0
                            and abs(r["radius"] - tr["R"][-1]) < 0.35 * tr["R"][-1]]
                    if cand:
                        tr = min(cand, key=lambda tr: np.linalg.norm(_mi(c, tr["pos"][-1], np.array(shape))))
                        tr["last_t"], tr["last_f"] = round(t, 1), fi
                    else:
                        tr = {"born": round(t, 1), "last_t": round(t, 1), "last_f": fi, "pos": [], "R": [], "axis": []}
                        tracks.append(tr)
                    tr["pos"].append(c), tr["R"].append(r["radius"]), tr["axis"].append(np.asarray(r["axis"]))
            else:
                fr.update(tips=len(vortices_2d(z)))
            frames.append(fr)
        u_new, v_new = eb.step(u, v, p)
        if t >= t_rhythm:                                   # firing times: u crosses 0.5 upward
            fired = (u < 0.5) & (u_new >= 0.5)
            ok = fired & ~np.isnan(last_fire)
            period_sum[ok] += t - last_fire[ok]
            period_cnt[ok] += 1
            last_fire[fired] = t
        u, v = u_new, v_new
    per = np.where(period_cnt > 0, period_sum / np.maximum(period_cnt, 1), np.nan)
    fired_cells = np.isfinite(per)
    rhythm = {"cells_firing_periodically": round(float(fired_cells.mean()), 4)}
    if fired_cells.any():
        q = np.percentile(per[fired_cells], [5, 50, 95])
        rhythm.update(period_p5_50_95=[round(float(x), 3) for x in q])
    res = {"dim": dim, "n": n, "corr": corr, "seed": seed, "T": T, "frames": frames, "rhythm": rhythm}
    if dim == 3:
        rt = []
        for tr in tracks:
            if len(tr["pos"]) < 3:
                continue
            ax = np.mean([np.sign(np.dot(a, tr["axis"][0])) * a for a in tr["axis"]], axis=0)
            ax /= np.linalg.norm(ax)
            along = float(sum(np.dot(_mi(b, a, np.array(shape)), ax) for a, b in zip(tr["pos"][:-1], tr["pos"][1:])))
            dur = tr["last_t"] - tr["born"]
            R = np.array(tr["R"])
            step_t = stride * p["dt"]
            rt.append({"born": tr["born"], "last": tr["last_t"], "lifetime": round(dur, 1),
                       "R_first_mid_last": [round(float(R[0]), 2), round(float(R[len(R) // 2]), 2), round(float(R[-1]), 2)],
                       "dR_dt": round(float(np.polyfit(np.arange(len(R)) * step_t, R, 1)[0]), 4) if len(R) > 2 else 0.0,
                       "drift_along_axis": round(along, 2), "drift_speed": round(abs(along) / dur, 4) if dur else 0.0,
                       "alive_at_end": tr["last_f"] == fi})
        res["tracks"] = rt
    if out is not None:
        img = (u > 0.5).mean(axis=2) if dim == 3 else u
        render_field(img, str(out / f"exc{dim}d_c{corr}_s{seed}_u.png"), px=480)
        if dim == 3:
            render_field(vr.line_mask(eb.phase_field(u, v)).max(axis=2).astype(float),
                         str(out / f"exc3d_c{corr}_s{seed}_filaments.png"), px=480)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--corr", type=float, default=6.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=400.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = run(a.dim, a.corr, a.seed, a.T, out=out)
    fr = r["frames"]
    if a.dim == 3:
        print(f"3D corr={a.corr} seed={a.seed}: rings (every 50 t) {[f['rings'] for f in fr][::10]} | filaments"
              f" {[f['filaments'] for f in fr][::10]} | firing {[f['firing'] for f in fr][::20]} | rhythm {r['rhythm']}",
              flush=True)
        for x in sorted(r["tracks"], key=lambda x: -x["lifetime"])[:5]:
            print("   ", x, flush=True)
    else:
        print(f"2D corr={a.corr} seed={a.seed}: spiral tips (every 50 t) {[f['tips'] for f in fr][::10]} | firing"
              f" {[f['firing'] for f in fr][::20]} | rhythm {r['rhythm']}", flush=True)
    (out / f"exc{a.dim}d_c{a.corr}_s{a.seed}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
