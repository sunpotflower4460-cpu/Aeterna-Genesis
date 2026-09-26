"""Do dividing spots pass their kind on? (P14, ladder R3 -- 3D first, 2D after)

    python tools/cell_inherit.py --out /tmp/inh --seed 1                       # 3D, μ = 0
    python tools/cell_inherit.py --out /tmp/inh --seed 1 --mu 0.003            # mutation control
    python tools/cell_inherit.py --out /tmp/inh --seed 1 --k1 0.061            # V1 dies a little slower (selection)
    python tools/cell_inherit.py --out /tmp/inh --seed 1 --dim 2

Law: two replicators on one food (genesis/models/gray_scott_two.py). t = 0: U = 1 and 12 seed blobs, each a random
mixture of V1 and V2. Nothing assigns kinds.

Measured every `every` t (spots = connected V1 + V2 > 0.2, periodic):
* purification -- the kind of each spot, kind1 = V1 / (V1 + V2); purity = |kind1 − ½|·2; the seeds' mixtures at t = 0.
* divisions -- a spot of the previous frame that overlaps two or more spots now, each of which overlaps only it
  (clean division). For each: the parent's kind and the daughters' kinds. Divisions of PURE parents (purity > 0.9)
  are counted apart: early on, two seeds that touch form one mixed spot that later comes apart into two kinds.
* inheritance -- the fraction of daughters whose majority kind is the parent's. Null (no inheritance): a daughter
  of random kind drawn from the population, i.e. the frequency of the parent's kind among all spots of that frame.
* flips -- a spot that simply continues (one spot then, one spot now, only each other) but changed its majority kind.
* merges (a spot overlapping two or more previous spots), births (no previous spot), deaths (no spot now).
* the kind frequency over time (drift, or selection when k1 ≠ k2), and the volume of the box inside spots.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import gray_scott_two as g2
from tools.snapshot import render_field


def _overlaps(prev: np.ndarray, now: np.ndarray) -> dict[tuple[int, int], int]:
    m = (prev > 0) & (now > 0)
    pairs, cnt = np.unique(np.stack([prev[m], now[m]]), axis=1, return_counts=True)
    return {(int(a), int(b)): int(c) for (a, b), c in zip(pairs.T, cnt)}


def run(dim: int, seed: int, T: float, mu: float = 0.0, k1: float | None = None, n: int | None = None,
        every: float = 50.0, out: Path | None = None, k: float | None = None, F: float | None = None):
    n = n or (64 if dim == 3 else 160)
    shape = (n,) * dim
    p = dict(g2.DEFAULTS if dim == 3 else g2.DEFAULTS_2D, mu=mu)
    if k is not None:
        p["k1"] = p["k2"] = k
    if F is not None:
        p["F"] = F
    if k1 is not None:
        p["k1"] = k1
    U, V1, V2, mix = g2.make_initial(shape, np.random.default_rng(seed), p)
    stride = int(round(every / p["dt"]))
    frames, divisions = [], []
    merges = births = deaths = flips = continuations = 0
    prev = None
    for i in range(int(round(T / p["dt"])) + 1):
        if i % stride == 0:
            lab, sp = g2.spots(V1, V2)
            kinds = {s["id"]: s["kind1"] for s in sp}
            frac1 = float(np.mean([x > 0.5 for x in kinds.values()])) if kinds else None
            pur = [g2.purity(x) for x in kinds.values()]
            frames.append({"t": round(i * p["dt"], 1), "spots": len(sp),
                           "volume": round(float((V1 + V2 > g2.THRESH).mean()), 4),
                           "frac1": None if frac1 is None else round(frac1, 3),
                           "purity_median": round(float(np.median(pur)), 4) if pur else None,
                           "pure_fraction": round(float(np.mean([x > 0.9 for x in pur])), 3) if pur else None})
            if prev is not None:
                plab, pkinds, pfrac1 = prev
                ov = _overlaps(plab, lab)
                kids_of: dict[int, set] = {}
                pars_of: dict[int, set] = {}
                for a, b in ov:
                    kids_of.setdefault(a, set()).add(b)
                    pars_of.setdefault(b, set()).add(a)
                merges += sum(1 for b in pars_of.values() if len(b) >= 2)
                births += sum(1 for i in kinds if i not in pars_of)
                deaths += sum(1 for i in pkinds if i not in kids_of)
                for a, kids in kids_of.items():
                    if len(kids) == 1 and pars_of[next(iter(kids))] == {a}:
                        continuations += 1
                        flips += int((kinds[next(iter(kids))] > 0.5) != (pkinds[a] > 0.5))
                    if len(kids) >= 2 and all(pars_of[b] == {a} for b in kids):
                        pk = pkinds[a]
                        same = [(kinds[b] > 0.5) == (pk > 0.5) for b in kids]
                        freq = pfrac1 if pk > 0.5 else 1.0 - pfrac1
                        divisions.append({"t": frames[-1]["t"], "parent_kind1": round(pk, 4),
                                          "kids_kind1": [round(kinds[b], 4) for b in kids],
                                          "same": float(np.mean(same)), "null": round(float(freq), 4)})
            prev = (lab, kinds, frac1 if frac1 is not None else 0.5)
        U, V1, V2 = g2.step(U, V1, V2, p)
    last = frames[-1]
    pure_div = [d for d in divisions if g2.purity(d["parent_kind1"]) > 0.9]
    res = {"dim": dim, "n": n, "seed": seed, "T": T, "mu": mu, "k1": p["k1"], "k2": p["k2"], "F": p["F"],
           "seed_mixtures": [round(q, 3) for q in mix], "frames": frames, "divisions": divisions,
           "n_divisions": len(divisions), "merges": merges, "continuations": continuations, "flips": flips, "births": births, "deaths": deaths,
           "inheritance": round(float(np.mean([d["same"] for d in divisions])), 4) if divisions else None,
           "null": round(float(np.mean([d["null"] for d in divisions])), 4) if divisions else None,
           "n_divisions_pure": len(pure_div),
           "inheritance_pure": round(float(np.mean([d["same"] for d in pure_div])), 4) if pure_div else None,
           "null_pure": round(float(np.mean([d["null"] for d in pure_div])), 4) if pure_div else None,
           "spots_start_end": [frames[0]["spots"], last["spots"]], "alive_at_end": last["spots"] > 0,
           "frac1_start_end": [frames[1]["frac1"] if len(frames) > 1 else None, last["frac1"]]}
    if out is not None:
        img = (V1 - V2).sum(axis=-1) if dim == 3 else V1 - V2
        tag = _tag(dim, seed, mu, k1, k, F)
        render_field(img, str(out / f"{tag}.png"), diverging=True, symmetric=True, px=480)
    return res


def _tag(dim, seed, mu, k1, k, F) -> str:
    return (f"inh{dim}d_s{seed}_mu{mu}" + (f"_k{k}" if k is not None else "") + (f"_F{F}" if F is not None else "")
            + (f"_k1{k1}" if k1 is not None else ""))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=4000.0)
    ap.add_argument("--mu", type=float, default=0.0)
    ap.add_argument("--k1", type=float, default=None, help="V1's decay only (selection)")
    ap.add_argument("--k", type=float, default=None, help="both decays")
    ap.add_argument("--F", type=float, default=None)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = run(a.dim, a.seed, a.T, a.mu, a.k1, out=out, k=a.k, F=a.F)
    fr = r["frames"]
    print(f"{a.dim}D seed={a.seed} mu={a.mu} F={r['F']} k1={r['k1']} k2={r['k2']}: spots (every 500 t) {[f['spots'] for f in fr][::10]}"
          f" | frac1 {[f['frac1'] for f in fr][::10]} | pure {[f['pure_fraction'] for f in fr][::10]}"
          f" | divisions {r['n_divisions']} inheritance {r['inheritance']} (null {r['null']})"
          f" | from pure parents {r['n_divisions_pure']}: {r['inheritance_pure']} (null {r['null_pure']})"
          f" | flips {r['flips']}/{r['continuations']} | merges {r['merges']} births {r['births']} deaths {r['deaths']} | seeds {r['seed_mixtures']}", flush=True)
    tag = _tag(a.dim, a.seed, a.mu, a.k1, a.k, a.F)
    (out / f"{tag}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
