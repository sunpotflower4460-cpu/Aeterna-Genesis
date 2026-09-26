"""Light-cone-first white (P7-5 prototype): how close does a field on a causal set come to the continuum?

    python tools/causet_first_look.py --out /tmp/causet

1) Hop-and-stop propagator from the bottom tip of the unit 2D diamond, m = 5: mean of K in 10 proper-time bins
   vs ½ J0(mτ), for N = 500, 2000, 8000 (3 sprinklings each). PNG: K drawn on the diamond (each pixel = mean of
   the elements in it; t upward).
2) Smeared d'Alembertian at the top tip: mean ± s.e.m. over 20 sprinklings for φ = 1, (t−1)², x², several (N, ε).
Everything put in: the sprinkling (2D Minkowski, then only the order is used), ρ = 2N, m, ε.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import causet_field as cf
from tools.snapshot import render_field


def propagator(N: int, seed: int, m: float = 5.0) -> dict:
    pts, R = cf.diamond_with_tips(N, seed)
    K = cf.retarded_from(R, 2.0 * N, m, 0)
    tau = cf.proper_time(pts, 0)
    idx = np.minimum((tau * 10).astype(int), 9)
    rows = []
    for b in range(10):
        sel = R[0] & (idx == b)
        rows.append({"tau": [b / 10, (b + 1) / 10], "n": int(sel.sum()), "K": round(float(K[sel].mean()), 4),
                     "continuum": round(float(cf.continuum_retarded(tau[sel], m).mean()), 4)})
    return {"N": N, "seed": seed, "m": m, "rows": rows, "max_err": max(abs(r["K"] - r["continuum"]) for r in rows),
            "pts": pts, "K": K}


def picture(pts, K, path: str, size: int = 96) -> None:
    img, cnt = np.zeros((size, size)), np.zeros((size, size))
    iy = np.clip(((1 - pts[:, 0]) * size).astype(int), 0, size - 1)             # t upward
    ix = np.clip(((pts[:, 1] + 0.5) * size).astype(int), 0, size - 1)
    np.add.at(img, (iy, ix), K)
    np.add.at(cnt, (iy, ix), 1)
    render_field(np.where(cnt > 0, img / np.maximum(cnt, 1), 0.0), path, diverging=True, symmetric=True)


def box(N: int, eps: float, seeds: int = 20) -> dict:
    vals = []
    for s in range(seeds):
        pts, R = cf.diamond_with_tips(N, seed=100 + s)
        x = len(pts) - 1
        vals.append([cf.smeared_box(R, 2.0 * N, eps, f, x)
                     for f in (np.ones(len(pts)), (pts[:, 0] - 1) ** 2, pts[:, 1] ** 2)])
    v = np.array(vals)
    return {"N": N, "eps": eps, "expected": [0, -2, 2], "mean": np.round(v.mean(0), 3).tolist(),
            "sem": np.round(v.std(0) / np.sqrt(seeds), 3).tolist(), "sd": np.round(v.std(0), 3).tolist()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"propagator": [], "box": []}
    for N in (500, 2000, 8000):
        runs = [propagator(N, s) for s in range(3)]
        if N == 8000:
            picture(runs[0]["pts"], runs[0]["K"], str(out / "causet_K_N8000.png"))
        for r in runs:
            r.pop("pts"), r.pop("K")
        res["propagator"] += runs
        print(f"N={N}: max |mean K − ½J0| over bins {[round(r['max_err'], 4) for r in runs]}", flush=True)
    r0 = res["propagator"][-3]
    print("  τ bin   K   ½J0 :", [(r["tau"][0], r["K"], r["continuum"]) for r in r0["rows"]])
    for N, eps in ((2000, 0.1), (2000, 0.03), (8000, 0.03), (8000, 0.01)):
        b = box(N, eps)
        res["box"].append(b)
        print(f"B_ε N={N} ε={eps}: mean {b['mean']} ± {b['sem']} (sd {b['sd']}) expected {b['expected']}", flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
