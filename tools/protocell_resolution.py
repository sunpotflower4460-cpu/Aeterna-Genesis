"""Does the one-chemistry result (P17) survive refining the grid? The SAME physical box L is run at several grid
spacings dx (n = L/dx; the time step shrinks as dx⁴, the seed radius is kept in physical units) and physical
observables are compared (3D first, 2D after).

    python tools/protocell_resolution.py run --dim 3 --L 32 --dx 0.8 --seed 1 --T 200 --out /tmp/res     # one run
    python tools/protocell_resolution.py summary --out /tmp/res                                           # compare

Seeds place the replicator seeds on cell indices, so the same seed is not the same t = 0 at another dx: compare
seed means and spreads, not single runs. Observables (physical units): containers per volume, the share of the box
inside containers, the inside/outside replicator ratio and the share of containers holding exactly one spot (late
half), divisions per volume, inheritance, and in 3D the share of containers that are closed balls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import protocell_one as po
from tools.protocell_run import run as pc_run

OBS = ("density", "box_share", "in_out", "one_spot_each", "occupied", "divisions", "inheritance", "balls")


def observe(r: dict, L: float) -> dict:
    vol = float(L) ** r["dim"]
    late = [f for f in r["frames"] if f["t"] >= r["T"] / 2]
    last = r["frames"][-1]
    t3 = r.get("three_d")
    return {"density": last["containers"] / vol, "box_share": last["box_share"],
            "in_out": r["late_in_out_ratio"], "one_spot_each": r["late_one_spot_each_majority"],
            "occupied": r["late_occupied_majority"],
            "divisions": r["n_divisions"] / vol, "inheritance": r["inheritance"],
            "balls": (t3["solid_balls"] / t3["containers"]) if t3 and t3["containers"] else None,
            "containers": last["containers"], "n_inherit": r["n_inherit"],
            "late_frames": len(late)}


def summary(out: Path, rel_tol: float = 0.15) -> dict:
    """{"<dim>D L=<L> T=<T>": {...}}: runs are compared only within the same dimension, box and duration."""
    rows = [json.loads(p.read_text()) for p in sorted(out.glob("res*.json"))]
    table: dict = {}
    for key in sorted({(r["dim"], r["L"], r["T"]) for r in rows}):       # only the same box and duration compare
        dim = f"{key[0]}D L={key[1]:g} T={key[2]:g}"
        by_dx: dict = {}
        for r in (r for r in rows if (r["dim"], r["L"], r["T"]) == key):
            by_dx.setdefault(r["dx"], []).append(r["obs"])
        stats = {dx: {k: [o[k] for o in obs if o[k] is not None] for k in OBS} for dx, obs in by_dx.items()}
        agg = {dx: {k: {"mean": float(np.mean(v)) if v else None, "min": min(v) if v else None,
                        "max": max(v) if v else None, "n": len(v)} for k, v in s.items()}
               for dx, s in stats.items()}
        if len(agg) < 2:                                   # nothing to compare a single spacing with
            table[dim] = {"dx": sorted(agg, reverse=True), "agg": agg, "verdict": {}, "insufficient": True,
                          "reason": "need at least two grid spacings"}
            continue
        verdict = {}
        for k in OBS:
            means = {dx: a[k]["mean"] for dx, a in agg.items() if a[k]["mean"] is not None}
            if len(means) < len(agg):                     # every spacing must contribute, or no verdict
                verdict[k] = {"insufficient": True, "missing_dx": sorted(set(agg) - set(means)),
                              "resolution_independent": None}
                continue
            hi, lo = max(means, key=means.get), min(means, key=means.get)
            diff = means[hi] - means[lo]                      # over every pair of spacings, not only the ends
            spread = max(agg[dx][k]["max"] - agg[dx][k]["min"] for dx in means)
            rel = diff / (float(np.mean([abs(m) for m in means.values()])) + 1e-12)
            verdict[k] = {"diff": round(diff, 6), "rel": round(rel, 4), "spread": round(spread, 6),
                          "widest_pair": [hi, lo],
                          "resolution_independent": bool(diff <= spread or rel <= rel_tol)}
        table[dim] = {"dx": sorted(agg, reverse=True), "agg": agg, "verdict": verdict, "insufficient": False}
    return table


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("run", "summary"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--L", type=float, default=None)
    ap.add_argument("--dx", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=200.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.mode == "summary":
        t = summary(out)
        for dim, d in t.items():
            print(f"{dim}  dx {d['dx']}" + ("  -- " + d["reason"] if d["insufficient"] else ""))
            for k in OBS:
                row = "  ".join(f"{dx}: {d['agg'][dx][k]['mean']:.4g} [{d['agg'][dx][k]['min']:.4g}–"
                                f"{d['agg'][dx][k]['max']:.4g}]" if d['agg'][dx][k]['mean'] is not None else f"{dx}: –"
                                for dx in d["dx"])
                print(f"  {k:14s} {row}  -> {d['verdict'].get(k)}")
        (out / "summary.json").write_text(json.dumps(t, indent=1, default=str))
        return 0
    L = a.L or (32.0 if a.dim == 3 else 128.0)
    n = int(round(L / a.dx))
    if abs(n * a.dx - L) > 1e-6 * L:                     # the grid must tile the same physical box exactly
        raise SystemExit(f"dx={a.dx} does not divide L={L} (n*dx = {n * a.dx}); choose dx = L/n")
    r = pc_run(a.dim, a.seed, a.T, n=n, model=po, dx=a.dx)
    rec = {"dim": a.dim, "L": L, "dx": a.dx, "n": n, "seed": a.seed, "T": a.T, "dt": r["params"]["dt"],
           "params": r["params"], "obs": observe(r, L), "three_d": r.get("three_d")}
    print(json.dumps(rec["obs"]), flush=True)
    (out / f"res{a.dim}d_dx{a.dx:.4f}_s{a.seed}.json").write_text(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
