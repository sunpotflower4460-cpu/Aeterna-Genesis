"""Follow the localized lumps of the wave white over time (2D or 3D): where they go, how long they live.

    python tools/wave_track.py --dim 3 --n 64 --absorb 0.3 --seed 1 --T 1500 --out /tmp/wt
    python tools/wave_track.py --dim 2 --n 128 --absorb 0.3 --seed 2 --T 3000 --out /tmp/wt

From t = 0 (on the hill + noise, DEFAULTS) with leapfrog dt = 0.2. Every `window` time units the energy density
averaged over that window (so a lump's oscillation does not make it blink) is searched for lumps
(genesis/diagnostics/lump_tracker: > 0.05 × hill height, extent ≤ n/4 along every axis; larger regions are
walls / membranes and are counted separately). Lumps are linked frame to frame with the speed limit c = 1.
At the end, φ is recorded at every surviving lump for `follow` time units: its main frequency vs the vacuum
mass gap (sqrt(2λ) for φ⁴, sqrt(λ) for sine-Gordon). Output: <out>/<tag>.json and a PNG of the last averaged
energy (3D: maximum projection). The absorbing border (absorb > 0) is PUT IN; so are the law and the t = 0 noise.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from genesis.diagnostics.lump_tracker import Tracker, detect
from genesis.models import wave_klein_gordon as kg
from tools.snapshot import render_field


def hill(p):
    return 2.0 * p["lam"] if p["potential"] == "sine_gordon" else 0.25 * p["lam"]


def gap(p):
    return float(np.sqrt(p["lam"]) if p["potential"] == "sine_gordon" else np.sqrt(2 * p["lam"]))


def run(dim: int, n: int, potential: str, absorb: float, seed: int, T: float, window: float, follow: float,
        out: Path) -> dict:
    p = dict(kg.DEFAULTS, potential=potential, absorb=absorb)
    dt, shape = p["dt"], (n,) * dim
    phi, pi = kg.make_initial(shape, np.random.default_rng(seed), p)
    mask = kg.damping_mask(shape, int(p["absorb_width"]))
    tracker = Tracker(shape, c=1.0, margin=2.0)
    per_win, acc, k = int(round(window / dt)), np.zeros(shape), 0
    frames, t0 = [], time.time()
    for step in range(1, int(round(T / dt)) + 1):
        phi, pi = kg.step(phi, pi, p, mask)
        acc += kg.energy_density(phi, pi, p)
        k += 1
        if k == per_win:
            avg = acc / k
            lumps, ext = detect(avg / hill(p), 0.05, max_extent=n // 4)
            t = step * dt
            tracker.add(t, lumps)
            frames.append({"t": round(t, 2), "E": round(kg.energy(phi, pi, p), 3), "lumps": len(lumps),
                           "extended": len(ext), "walls": round(kg.wall_density(phi, p), 5)})
            acc, k = np.zeros(shape), 0
    last_avg = avg
    s = tracker.summary()
    alive = [tr for tr in tracker.tracks if tr.end == "alive"]
    series = {tr.id: [] for tr in alive}
    for _ in range(int(round(follow / dt))):
        phi, pi = kg.step(phi, pi, p, mask)
        for tr in alive:
            idx = tuple(int(round(x)) % n for x in tr.pos[-1])
            series[tr.id].append(float(phi[idx]))
    for row in s["tracks"]:
        if row["id"] in series:
            x = np.array(series[row["id"]])
            x = x - (np.round(x / (2 * np.pi)) * 2 * np.pi if potential == "sine_gordon" else np.sign(x.mean()) * 1.0)
            f = np.abs(np.fft.rfft(x - x.mean()))
            w = float((np.fft.rfftfreq(len(x), dt) * 2 * np.pi)[np.argmax(f[1:]) + 1])
            row.update(omega=round(w, 3), mass_gap=round(gap(p), 3), below_gap=bool(0.5 * gap(p) < w < gap(p)),
                       amp=round(float(np.abs(x).max()), 3))
    tag = f"{potential}_{dim}d_n{n}_a{absorb}_s{seed}"
    img = last_avg / hill(p)
    render_field(img.max(axis=0) if dim == 3 else img, str(out / f"{tag}_energy.png"))
    res = {"tag": tag, "dim": dim, "n": n, "potential": potential, "absorb": absorb, "seed": seed, "T": T,
           "window": window, "seconds": round(time.time() - t0, 1), "frames": frames, **s}
    (out / f"{tag}.json").write_text(json.dumps(res, indent=1))
    return res


def brief(r: dict) -> str:
    long = [x for x in r["tracks"] if x["lifetime"] >= 0.5 * r["T"]]
    alive = [x for x in r["tracks"] if x["end"] == "alive"]
    osc = [x for x in alive if x.get("below_gap")]
    fast = max([x["mean_speed"] for x in long] or [0])
    return (f"{r['tag']}: tracks {len(r['tracks'])} events {r['events']} | lived ≥ T/2: {len(long)} | alive at end: {len(alive)}"
            f" (oscillating below gap: {len(osc)}) | max mean speed of long-lived {fast:.3f}"
            f" | end: E {r['frames'][-1]['E']} extended {r['frames'][-1]['extended']} ({r['seconds']} s)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dim", type=int, default=3)
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--potential", default="phi4", choices=["phi4", "sine_gordon"])
    ap.add_argument("--absorb", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=1500.0)
    ap.add_argument("--window", type=float, default=10.0)
    ap.add_argument("--follow", type=float, default=200.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(brief(run(a.dim, a.n, a.potential, a.absorb, a.seed, a.T, a.window, a.follow, out)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
