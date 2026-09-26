"""T1 / T2: a flux quantum threaded through the hole of the torus (P10, light-and-phase white).

    python tools/torus_flux.py --out /tmp/torus_flux

The periodic box IS a torus. Put in: ONE flux quantum through it, spread evenly -- every plaquette of the (0,1)
planes carries the same field B = 2π/(n₀n₁) (the links wrap with a seam that the compact links cannot see; the
other planes carry nothing). Gauss's law holds (E = 0, φ at rest), and uniform B exerts no force on itself.
Then φ starts on the hill (φ ≈ 0 + noise). Nothing else is put in.

T1 (3D, n×n×nz): does the evenly spread flux gather by itself into ONE quantized string (Meissner effect + flux
quantization), and does that string stay -- it has no partner of the opposite sign to meet? Measured every 10 t:
string length, the net piercing per (0,1) slice (conserved: the total wrapped flux of a slice cannot change unless
a plaquette crosses π), the axes the strings wrap, and at the end the flux per piercing (nearest-piercing split).

T2 (2D, the cross-section): relax (γ = 0.5, overdamped) to the lowest energy with one quantum and measure the
energy = the string TENSION (energy per unit length), for β = λ/(2e²) = 0.5, 1, 2. Known (Bogomolny): at β = 1
the tension is exactly 2π v² for one quantum; below β = 1 it is lower, above higher (type I / type II).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import abelian_higgs_nd as an
from tools.higgs3d_first_look import slice_flux
from tools.snapshot import render_field


def twisted_links(shape, k: int = 1) -> np.ndarray:
    """Link angles with k flux quanta through every (0,1) slice, spread evenly: wrap(P_01) = −2πk/(n₀n₁) on every
    plaquette (the sign is a convention), P = 0 in the other planes."""
    d, n0, n1 = len(shape), shape[0], shape[1]
    B = 2 * np.pi * k / (n0 * n1)
    th = np.zeros((d,) + tuple(shape))
    y = np.arange(n0).reshape((n0, 1) + (1,) * (d - 2))
    x = np.arange(n1).reshape((1, n1) + (1,) * (d - 2))
    th[0] = np.broadcast_to(B * x + 0.0 * y, shape)
    seam = np.zeros(shape)
    seam[:, n1 - 1] = 1.0
    th[1] = -(2 * np.pi * k / n0) * np.broadcast_to(y + 0.0 * x, shape) * seam
    return th


def start(shape, seed: int, p: dict, k: int = 1):
    phi, pi, _, E = an.make_initial(shape, np.random.default_rng(seed), p)
    return phi, pi, twisted_links(shape, k), E


def net_piercing(phi, th) -> list[int]:
    """Net winding of every (0,1) slice (one number per position along the other axes)."""
    w = an.winding(phi, th)[(0, 1)]
    return sorted(set(int(v) for v in w.reshape(w.shape[0] * w.shape[1], -1).sum(0)))


def t1(n: int, nz: int, gamma: float, seed: int, T: float, out: Path | None = None) -> dict:
    p = dict(an.DEFAULTS, gamma=gamma)
    s = start((n, n, nz), seed, p)
    rows = []
    for k in range(int(round(T / p["dt"])) + 1):
        if k % int(round(10 / p["dt"])) == 0:
            rows.append({"t": round(k * p["dt"], 1), "length": an.string_length(s[0], s[2]),
                         "mean_amp": round(float(np.abs(s[0]).mean()), 4), "net_per_slice": net_piercing(s[0], s[2]),
                         "wrapped": an.wrapped_axes(s[0], s[2]),
                         "gauss": float(np.abs(an.gauss_residual(s[0], s[1], s[3])).max())})
        s = an.step(*s, p)
    flux = {a: slice_flux(s[0], s[2], a) for a in an.wrapped_axes(s[0], s[2])}
    if out is not None:
        render_field((1.0 - np.abs(s[0])).max(axis=2), str(out / f"t1_n{n}_nz{nz}_g{gamma}_s{seed}.png"))
    fallen = [r for r in rows if r["mean_amp"] > 0.5]
    return {"n": n, "nz": nz, "gamma": gamma, "seed": seed, "T": T, "rows": rows,
            "net_per_slice_ever": sorted({v for r in rows for v in r["net_per_slice"]}),
            "min_length_after_fall": min([r["length"] for r in fallen] or [0]),
            "end_length": rows[-1]["length"], "end_wrapped": rows[-1]["wrapped"], "end_flux": flux,
            "max_gauss": max(r["gauss"] for r in rows)}


def t2(beta: float, n: int = 32, e: float = 0.3, seed: int = 1, T: float = 800.0) -> dict:
    p = dict(an.DEFAULTS, lam=2 * e * e * beta, e=e, gamma=0.5)
    s = start((n, n), seed, p)
    for _ in range(int(round(T / p["dt"]))):
        s = an.step(*s, p)
    w = an.winding(s[0], s[2])[(0, 1)]
    E = an.energy(*s, p)
    return {"beta": beta, "n": n, "e": e, "lam": p["lam"], "energy": round(E, 4), "bps": round(2 * np.pi * p["v"] ** 2, 4),
            "ratio_to_bps": round(E / (2 * np.pi * p["v"] ** 2), 4), "vortices": int(np.count_nonzero(w)),
            "net": int(w.sum())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--T", type=float, default=600.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"t1": [], "t2": []}
    for gamma in (0.01, 0.0):
        for seed in (1, 2, 3):
            r = t1(32, 16, gamma, seed, a.T, out)
            res["t1"].append(r)
            L = [x["length"] for x in r["rows"] if x["mean_amp"] > 0.5]
            print(f"T1 γ={gamma} seed={seed}: net piercing per slice ever {r['net_per_slice_ever']} | length after the"
                  f" fall (every 100 t) {L[::10]} → end {r['end_length']} (straight = 16) | wraps {r['end_wrapped']}"
                  f" | flux per piercing {r['end_flux']} | max gauss {r['max_gauss']:.1e}", flush=True)
    for beta in (0.5, 1.0, 2.0):
        r = t2(beta)
        res["t2"].append(r)
        print(f"T2 β={beta}: energy of one quantum {r['energy']} vs 2πv² = {r['bps']} (ratio {r['ratio_to_bps']})"
              f" | vortices {r['vortices']}, net {r['net']}", flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
