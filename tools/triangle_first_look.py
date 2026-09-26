"""Triangle white first look (P9-Q3): from noise, do waves settle into triangles, and what do three waves carry
that two cannot?

    python tools/triangle_first_look.py --out /tmp/tri

For g = 0, +0.5, −0.5 (the quadratic term, put in) and seeds 1–3, from u ≈ 0 + noise on a 64² periodic box
(dx = π/4, 8 cells per wavelength), run to t = 300 and measure:
* the pattern: closed triangles among the 6 strongest ring modes (angles, Φ = φ₁+φ₂+φ₃) and the triad skewness
  (weighted mean cos Φ over ALL closed triangles in the ring), every 20 t;
* the contrast: phase differences of mode PAIRS -- then the whole pattern is shifted by a random whole number of
  cells and everything is measured again: Φ must stay, pair differences move (they are not properties of the
  pattern);
* a PNG of the three final patterns side by side (stripes | g > 0 | g < 0).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics import triads as td
from genesis.models import swift_hohenberg_quadratic as sq
from tools.snapshot import render_field


def run(g: float, seed: int, n: int = 64, T: float = 300.0) -> dict:
    p = dict(sq.DEFAULTS, g=g)
    u = sq.make_initial((n, n), np.random.default_rng(seed), p)
    steps, every = int(round(T / p["dt"])), int(round(20 / p["dt"]))
    skew = []
    for k in range(steps + 1):
        if k % every == 0:
            skew.append((round(k * p["dt"], 1), round(td.triad_skewness(u, p["dx"]), 4)))
        if k < steps:
            u = sq.step(u, p)
    ps = td.peaks(u, p["dx"], 6)
    tri = td.triads(ps)
    shift = tuple(int(x) for x in np.random.default_rng(1000 + seed).integers(1, n, 2))
    us = np.roll(u, shift, (0, 1))
    ps2 = td.peaks(us, p["dx"], 6)
    tri2 = td.triads(ps2)
    return {"g": g, "seed": seed, "skewness": skew, "u": u,
            "triads": [{"Phi": round(t["Phi"], 4), "angles": [round(a, 1) for a in t["angles"]],
                        "weight": t["weight"]} for t in tri],
            "pairs": [round(x, 4) for x in td.pair_phases(ps)],
            "shift": shift, "triads_shifted": [round(t["Phi"], 4) for t in tri2],
            "pairs_shifted": [round(x, 4) for x in td.pair_phases(ps2)]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--T", type=float, default=300.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res, finals = [], {}
    for g in (0.0, 0.5, -0.5):
        for seed in (1, 2, 3):
            r = run(g, seed, T=a.T)
            finals.setdefault(g, r["u"])
            r.pop("u")
            res.append(r)
            main_tri = max(r["triads"], key=lambda t: t["weight"]) if r["triads"] else None
            print(f"g={g:+.1f} seed={seed}: skewness {r['skewness'][0][1]:+.3f} → {r['skewness'][-1][1]:+.3f}"
                  f" | strongest triangle {main_tri} | Φ of all triangles {[t['Phi'] for t in r['triads']]}"
                  f" → after shift {r['shift']}: {r['triads_shifted']}"
                  f" | pair Δφ {r['pairs'][:3]} → {r['pairs_shifted'][:3]}", flush=True)
    gap = np.full((64, 4), np.nan)
    strip = np.concatenate([finals[0.0], gap, finals[0.5], gap, finals[-0.5]], axis=1)
    render_field(np.nan_to_num(strip), str(out / "triangle_patterns.png"), diverging=True, symmetric=True, px=720)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
