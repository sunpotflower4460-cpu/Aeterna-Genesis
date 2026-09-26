"""Do replicators grow their own closed containers, and do the containers divide with what they hold? (P15, ladder R4
-- 3D first, 2D after)

    python tools/protocell_run.py --out /tmp/pc --seed 1                       # 3D
    python tools/protocell_run.py --out /tmp/pc --seed 1 --set alpha=0         # control: replicators cannot build
    python tools/protocell_run.py --out /tmp/pc --seed 1 --kill 200            # control: remove the replicators at t=200
    python tools/protocell_run.py --out /tmp/pc --seed 1 --dim 2

Law: genesis/models/protocell.py. t = 0: no container anywhere (c = −1 + noise), food, seed blobs of V1/V2 in
random mixtures.

Measured every `every` t:
* containers (c > 0, periodic): number, how many hold a replicator spot, spots per container (and, late, the share of
  containers holding exactly one spot), the share of the box;
  replicator density inside vs outside the containers.
* container events, frame to frame by overlap: births (no container there before), clean divisions (one container
  then, two or more now, each only from it), merges, deaths. At divisions of containers whose content is one kind
  (purity > 0.9): do the daughters hold the parent's kind? (null: the kind drawn from all containers of the frame.)
* --kill T: all replicators are removed at t = T; how the container share falls afterwards.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import protocell as pc
from tools.cell_inherit import _overlaps
from tools.snapshot import render_field


def run(dim: int, seed: int, T: float, overrides: dict | None = None, kill: float | None = None, n: int | None = None,
        every: float = 25.0, out: Path | None = None, tag: str = ""):
    n = n or (48 if dim == 3 else 128)
    shape = (n,) * dim
    p = dict(pc.DEFAULTS if dim == 3 else pc.DEFAULTS_2D, **(overrides or {}))
    c, U, V1, V2 = pc.make_initial(shape, np.random.default_rng(seed), p)
    stride = int(round(every / p["dt"]))
    kill_i = None if kill is None else int(round(kill / p["dt"]))
    frames, divisions = [], []
    births = merges = deaths = 0
    prev = None
    for i in range(int(round(T / p["dt"])) + 1):
        if kill_i is not None and i == kill_i:
            V1, V2 = np.zeros_like(V1), np.zeros_like(V2)
        if i % stride == 0:
            lab, cs = pc.containers(c, V1, V2)
            box = lab > 0
            V = V1 + V2
            occ = [x for x in cs if x["spots"] > 0]
            kinds = {x["id"]: x["kind1"] for x in occ}
            frac1 = float(np.mean([k > 0.5 for k in kinds.values()])) if kinds else 0.5
            frames.append({"t": round(i * p["dt"], 2), "containers": len(cs), "occupied": len(occ),
                           "spots_per_container": sorted(x["spots"] for x in cs),
                           "box_share": round(float(box.mean()), 4),
                           "v_in": round(float(V[box].mean()), 4) if box.any() else None,
                           "v_out": round(float(V[~box].mean()), 5) if (~box).any() else None,
                           "replicators": round(float(V.mean()), 5)})
            if prev is not None:
                plab, pkinds, pfrac1 = prev
                ov = _overlaps(plab, lab)
                kids_of: dict[int, set] = {}
                pars_of: dict[int, set] = {}
                for a, b in ov:
                    kids_of.setdefault(a, set()).add(b)
                    pars_of.setdefault(b, set()).add(a)
                ids_now = [x["id"] for x in cs]
                births += sum(1 for b in ids_now if b not in pars_of)
                deaths += sum(1 for a in np.unique(plab) if a and a not in kids_of)
                merges += sum(1 for b in pars_of.values() if len(b) >= 2)
                for a, kids in kids_of.items():
                    if len(kids) >= 2 and all(pars_of[b] == {a} for b in kids):
                        ev = {"t": frames[-1]["t"], "kids": len(kids)}
                        if a in pkinds and pc.purity(pkinds[a]) > 0.9 and all(b in kinds for b in kids):
                            pk = pkinds[a]
                            ev.update(parent_kind1=round(pk, 4), kids_kind1=[round(kinds[b], 4) for b in kids],
                                      same=float(np.mean([(kinds[b] > 0.5) == (pk > 0.5) for b in kids])),
                                      null=round(pfrac1 if pk > 0.5 else 1.0 - pfrac1, 4))
                        divisions.append(ev)
            prev = (lab, kinds, frac1)
        c, U, V1, V2 = pc.step(c, U, V1, V2, p)
    fr = frames
    inh = [d for d in divisions if "same" in d]
    late = [f for f in fr if f["t"] >= T / 2]
    one_each = [float(np.mean([s == 1 for s in f["spots_per_container"]])) for f in late if f["containers"]]
    res = {"dim": dim, "n": n, "seed": seed, "T": T, "kill": kill, "params": {k: p[k] for k in
           ("kappa", "alpha", "beta", "g0", "s", "F", "k")}, "frames": fr, "divisions": divisions,
           "n_divisions": len(divisions), "births": births, "merges": merges, "deaths": deaths,
           "n_inherit": len(inh), "inheritance": round(float(np.mean([d["same"] for d in inh])), 4) if inh else None,
           "null": round(float(np.mean([d["null"] for d in inh])), 4) if inh else None,
           "containers_first_last": [next((f["containers"] for f in fr if f["containers"]), 0), fr[-1]["containers"]],
           "late_one_spot_each": round(float(np.mean(one_each)), 3) if one_each else None,
           "late_in_out_ratio": round(float(np.median([f["v_in"] / max(f["v_out"], 1e-9) for f in late
                                                        if f["v_in"] is not None and f["v_out"] is not None])), 1)
           if any(f["v_in"] is not None for f in late) else None}
    if out is not None:
        box_img = (c > 0).mean(axis=-1) if dim == 3 else c
        kind_img = (V1 - V2).sum(axis=-1) if dim == 3 else V1 - V2
        render_field(box_img, str(out / f"pc{dim}d_s{seed}{tag}_containers.png"), px=480)
        render_field(kind_img, str(out / f"pc{dim}d_s{seed}{tag}_kinds.png"), diverging=True, symmetric=True, px=480)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=400.0)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--kill", type=float, default=None)
    ap.add_argument("--set", action="append", default=[], help="law override, e.g. alpha=0")
    a = ap.parse_args(argv)
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    tag = "".join(f"_{k}{v}" for k, v in ov.items()) + (f"_kill{a.kill}" if a.kill is not None else "")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = run(a.dim, a.seed, a.T, ov, a.kill, a.n, out=out, tag=tag)
    fr = r["frames"]
    k = max(1, len(fr) // 8)
    print(f"{a.dim}D seed={a.seed}{tag}: containers {[f['containers'] for f in fr][::k]} | occupied"
          f" {[f['occupied'] for f in fr][::k]} | share {[f['box_share'] for f in fr][::k]} | replicators"
          f" {[f['replicators'] for f in fr][::k]} | births {r['births']} divisions {r['n_divisions']} merges"
          f" {r['merges']} deaths {r['deaths']} | one spot each (late) {r['late_one_spot_each']} | in/out"
          f" {r['late_in_out_ratio']} | inheritance {r['inheritance']} of {r['n_inherit']} (null {r['null']})",
          flush=True)
    (out / f"pc{a.dim}d_s{a.seed}{tag}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
