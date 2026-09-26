"""Light-and-phase white in 3D: do flux strings grow from the hill, and do they stay?

    python tools/higgs3d_first_look.py --out /tmp/h3d --gamma 0.01 --seed 1
    python tools/higgs3d_first_look.py --out /tmp/h3d --quick

From t = 0 (φ ≈ 0 + noise 0.01, no gauge field, at rest; e = 0.3, λ = 0.36 → β = 2, dt = 0.2) in an n³ periodic
box. Every 10 t: total string length (plaquettes pierced by a gauge-invariant winding; meaningful once mean |φ| >
v/2), the axes along which strings run all the way around the box (every perpendicular slice pierced), Gauss
residual, energy, mean |φ|. At the end, for each such axis: the flux carried by each piercing in each slice (the
slice is split among the piercings by nearest distance -- tubes a few cells apart would overlap in fixed disks),
in units of 2π; and a PNG of the string cores seen through the box (max over z of 1 − |φ|). Cooling γ > 0 is PUT IN.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import abelian_higgs_nd as an
from tools.snapshot import render_field


def slice_flux(phi, th, axis: int) -> dict:
    """Flux (in 2π) carried by each piercing of the slices perpendicular to `axis`: every plaquette of a slice goes
    to its nearest piercing (periodic distance). Returns mean |flux| and the worst deviation from ±1."""
    i, j = [a for a in range(3) if a != axis]
    w = np.moveaxis(an.winding(phi, th)[(i, j)], axis, 0)
    F = np.moveaxis(an.wrap(an.plaquette(th, i, j)), axis, 0) / (2 * np.pi)
    ny, nx = w.shape[1:]
    yy, xx = np.mgrid[:ny, :nx]
    vals = []
    for sl in range(w.shape[0]):
        ys, xs = np.nonzero(w[sl])
        if len(ys) == 0:
            continue
        d = np.stack([np.minimum(abs(yy - y), ny - abs(yy - y)) ** 2 + np.minimum(abs(xx - x), nx - abs(xx - x)) ** 2
                      for y, x in zip(ys, xs)])
        near = d.argmin(0)
        vals += [float(F[sl][near == q].sum()) * int(np.sign(w[sl][ys[q], xs[q]])) for q in range(len(ys))]
    v = np.array(vals)
    return {"piercings": len(v), "mean": round(float(v.mean()), 4), "worst": round(float(np.abs(v - 1).max()), 4)}


def run(n: int, gamma: float, seed: int, T: float, out: Path) -> dict:
    p = dict(an.DEFAULTS, gamma=gamma)
    s = an.make_initial((n, n, n), np.random.default_rng(seed), p)
    rows, steps = [], int(round(T / p["dt"]))
    for k in range(steps + 1):
        if k % int(round(10 / p["dt"])) == 0:
            rows.append({"t": round(k * p["dt"], 1), "length": an.string_length(s[0], s[2]),
                         "mean_amp": round(float(np.abs(s[0]).mean()), 4), "wrapped": an.wrapped_axes(s[0], s[2]),
                         "gauss": float(np.abs(an.gauss_residual(s[0], s[1], s[3])).max()),
                         "E": round(an.energy(*s, p), 3)})
        if k < steps:
            s = an.step(*s, p)
    tag = f"n{n}_g{gamma}_s{seed}"
    flux = {a: slice_flux(s[0], s[2], a) for a in an.wrapped_axes(s[0], s[2])}
    render_field((1.0 - np.abs(s[0])).max(axis=2), str(out / f"{tag}_strings.png"))
    fallen = [r for r in rows if r["mean_amp"] > 0.5]
    res = {"n": n, "gamma": gamma, "seed": seed, "T": T, "rows": rows,
           "peak_length": max([r["length"] for r in fallen] or [0]), "end_length": rows[-1]["length"],
           "end_wrapped": rows[-1]["wrapped"], "end_flux_per_piercing": flux,
           "max_gauss": max(r["gauss"] for r in rows)}
    (out / f"{tag}.json").write_text(json.dumps(res, indent=1))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--gamma", type=float, default=0.01)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=800.0)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n, T = (24, 200.0) if a.quick else (a.n, a.T)
    r = run(n, a.gamma, a.seed, T, out)
    L = [x["length"] for x in r["rows"] if x["mean_amp"] > 0.5]
    print(f"n={n} γ={a.gamma} seed={a.seed}: length peak {r['peak_length']} → end {r['end_length']}"
          f" (every 100 t: {L[::10]}) | wraps around axes {r['end_wrapped']}, flux per piercing {r['end_flux_per_piercing']}"
          f" | max gauss {r['max_gauss']:.1e}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
