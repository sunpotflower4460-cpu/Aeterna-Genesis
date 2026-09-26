"""T3: the two arms as ONE line on a torus (P10, from the question "what if the torus is part of the picture?").

    python tools/torus_lines.py --out /tmp/torus

Two arms e^{it} and e^{ict} are two angles, (θ₁, θ₂) = (t, c·t) mod 2π: a point on a torus, moving along a straight
line of slope c. If c = p/q the line closes after q turns of θ₁ (t = 2πq) and never visits the rest of the
torus. If c is not a fraction (π, φ+1, √10) it never closes and comes arbitrarily close to every point (Kronecker).

Measured: the fraction of a G×G grid of cells on the flat torus that the line has visited by time t, for
c = 22/7, 355/113, π, φ+1, on a coarse grid (256², up to 5000 turns) and a fine one (2048², up to 2000 turns). Rational lines stop growing after closing; irrational ones keep
growing toward 1. Before t = 2πq, a line with a large denominator q cannot be told from an irrational one at
any resolution coarser than ~1/q -- the same fact as the near returns of H7.
PNGs: the flat torus (visit density) and a doughnut drawing, for each c at a few times.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.snapshot import render_field

CASES = {"22/7": 22 / 7, "355/113": 355 / 113, "π": np.pi, "φ+1": (1 + 5 ** 0.5) / 2 + 1}


def visits(c: float, t_max: float, G: int = 256, t_min: float = 0.0) -> np.ndarray:
    """Visit counts of the line (t, c t) mod 2π on a G×G grid, sampled finer than one cell."""
    dt = (2 * np.pi / G) / 3.0 / np.sqrt(1 + c * c)
    img = np.zeros((G, G))
    chunk = 2_000_000
    t0 = t_min
    while t0 < t_max:
        t = np.arange(t0, min(t_max, t0 + chunk * dt), dt)
        a = ((t % (2 * np.pi)) / (2 * np.pi) * G).astype(int) % G
        b = (((c * t) % (2 * np.pi)) / (2 * np.pi) * G).astype(int) % G
        img += np.bincount(b * G + a, minlength=G * G).reshape(G, G)
        t0 += chunk * dt
    return img


def coverage_curve(c: float, turns: list[int], G: int = 256) -> list[dict]:
    out, img, last = [], np.zeros((G, G)), 0.0
    for n in turns:
        img += visits(c, 2 * np.pi * n, G, t_min=last)
        last = 2 * np.pi * n
        out.append({"turns": n, "coverage": round(float((img > 0).mean()), 4)})
    return out


def _project(th1, th2, R, r, tilt, size):
    x = (R + r * np.cos(th2)) * np.cos(th1)
    y = (R + r * np.cos(th2)) * np.sin(th1)
    z = r * np.sin(th2)
    yv = y * np.cos(tilt) - z * np.sin(tilt)
    depth = y * np.sin(tilt) + z * np.cos(tilt)
    px = np.clip(((x / (2 * (R + r)) + 0.5) * (size - 1)).round().astype(int), 0, size - 1)
    py = np.clip(((0.5 - yv / (2 * (R + r))) * (size - 1)).round().astype(int), 0, size - 1)
    return py, px, depth


def doughnut(c: float, t_max: float, size: int = 360, R: float = 1.0, r: float = 0.42, tilt: float = 1.0) -> np.ndarray:
    """The line drawn on a doughnut (orthographic, tilted): a faint surface, and the path where it is in front."""
    g = np.linspace(0, 2 * np.pi, 1400, endpoint=False)
    T1, T2 = np.meshgrid(g, g, indexing="ij")
    py, px, d = _project(T1.ravel(), T2.ravel(), R, r, tilt, size)
    zbuf = np.full(size * size, -np.inf)
    np.maximum.at(zbuf, py * size + px, d)
    img = np.where(np.isfinite(zbuf), 0.15, 0.0)
    t = np.arange(0.0, t_max, 0.004)
    py, px, d = _project(t % (2 * np.pi), (c * t) % (2 * np.pi), R, r, tilt, size)
    front = d >= zbuf[py * size + px] - 0.03
    img[(py * size + px)[front]] = 1.0
    return img.reshape(size, size)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, c in CASES.items():
        res[name] = {"G256": coverage_curve(c, [1, 3, 7, 20, 113, 500, 2000, 5000], 256),
                     "G2048": coverage_curve(c, [7, 113, 500, 1000, 2000], 2048)}
        for g in ("G256", "G2048"):
            print(f"{name:8s} coverage of a {g[1:]}² torus after n turns: "
                  + ", ".join(f"{r['turns']}: {r['coverage']:.4f}" for r in res[name][g]), flush=True)
        safe = name.replace("/", "_").replace("+", "p").replace("π", "pi").replace("φ", "phi")
        for n in (7, 113):
            img = visits(c, 2 * np.pi * n, G=128)
            render_field(np.log1p(img), str(out / f"flat_{safe}_n{n}.png"), px=360)
            render_field(doughnut(c, 2 * np.pi * n), str(out / f"doughnut_{safe}_n{n}.png"), px=360)
    (out / "summary.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
