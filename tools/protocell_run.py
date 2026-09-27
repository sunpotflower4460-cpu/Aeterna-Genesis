"""Do replicators grow their own closed containers, and do the containers divide with what they hold? (P15, ladder R4
-- 3D first, 2D after)

    python tools/protocell_run.py --out /tmp/pc --seed 1                       # 3D
    python tools/protocell_run.py --out /tmp/pc --seed 1 --set alpha=0         # control: replicators cannot build
    python tools/protocell_run.py --out /tmp/pc --seed 1 --kill 200            # control: remove the replicators at t=200
    python tools/protocell_run.py --out /tmp/pc --seed 1 --dim 2
    python tools/protocell_run.py --out /tmp/pc --seed 1 --model one --set y=2          # P17: one chemistry

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

from genesis.diagnostics.protocell_measures import assign_spots, inside_shares, spot_kinds  # noqa: F401 (re-export)
from genesis.models import protocell as pc
from tools.cell_inherit import _overlaps
from tools.snapshot import render_field


def _unwrap(mask):
    """Roll a periodic 3D component so that it does not cross the box edge where possible (an empty slab is moved
    to index 0 on every axis). Returns (mask, spans): spans = axes on which it has no empty slab."""
    spans = []
    for ax in range(mask.ndim):
        occ = mask.any(axis=tuple(a for a in range(mask.ndim) if a != ax))
        empty = np.flatnonzero(~occ)
        if empty.size:
            mask = np.roll(mask, -int(empty[0]), axis=ax)
        else:
            spans.append(ax)
    return mask, spans


def three_d_audit(c, V, dx: float = 1.0):
    """Is the 3D result a genuine 3D structure? three_d_authenticity of the material and the replicator fields, and
    a 3D-only invariant: the Betti numbers of every container (c > 0). A closed solid ball is (b0, b1, b2) =
    (1, 0, 0); a flat or extruded sheet that spans the box would show up as spanning components or b1 > 0."""
    from genesis.diagnostics.topology3d import three_d_authenticity
    from genesis.diagnostics.topology_betti import betti3d
    lab = pc.labels(c + 1.0, 1.0)
    shapes = []
    for i in range(1, int(lab.max()) + 1):
        m = lab == i
        if not m.any():
            continue
        m, spans = _unwrap(m)
        b = betti3d(m)
        ext = [int(m.any(axis=tuple(a for a in range(3) if a != ax)).sum()) for ax in range(3)]
        shapes.append({"b": [b["b0"], b["b1"], b["b2"]], "spans": spans, "extent": ext})
    balls = [x for x in shapes if x["b"] == [1, 0, 0] and not x["spans"]]
    return {"material": three_d_authenticity(c), "replicators": three_d_authenticity(V),
            "containers": len(shapes), "solid_balls": len(balls),
            "min_extent": min((min(x["extent"]) for x in shapes), default=None),
            "min_extent_length": min((min(x["extent"]) * dx for x in shapes), default=None),
            "not_balls": [x for x in shapes if x not in balls]}


def run(dim: int, seed: int, T: float, overrides: dict | None = None, kill: float | None = None, n: int | None = None,
        every: float = 25.0, out: Path | None = None, tag: str = "", model=pc, dx: float = 1.0):
    """dx < 1 (models with a "dx" parameter only): the same physical system on a finer grid -- pass n = L/dx; the
    time step shrinks as dx⁴ (explicit ∇⁴), the seed radius is kept in physical units and the initial white noise
    keeps its strength per physical volume."""
    n = n or (48 if dim == 3 else 128)
    shape = (n,) * dim
    if "dx" in (overrides or {}):
        raise ValueError("set the grid spacing with the dx argument (--dx), which also rescales dt, seeds and noise")
    p = dict(model.DEFAULTS if dim == 3 else model.DEFAULTS_2D, **(overrides or {}))
    if dx != 1.0:
        if "dx" not in p:
            raise ValueError("this model has no grid spacing parameter")
        # the same physical system: dt ∝ dx⁴ (explicit ∇⁴), the seed radius in physical units, and the white noise of
        # the material with the same strength per physical volume (per-cell std ∝ dx^(−dim/2))
        p.update(dx=dx, dt=p["dt"] * dx ** 4, seed_radius=p["seed_radius"] / dx,
                 noise=p["noise"] * dx ** (-dim / 2.0))
    c, U, V1, V2 = model.make_initial(shape, np.random.default_rng(seed), p)
    stride = int(round(every / p["dt"]))
    kill_i = None if kill is None else int(round(kill / p["dt"]))
    frames, divisions = [], []
    births = merges = deaths = 0
    prev = None
    n_steps = int(round(T / p["dt"]))
    for i in range(n_steps + 1):
        if kill_i is not None and i == kill_i:
            V1, V2 = np.zeros_like(V1), np.zeros_like(V2)
        if i % stride == 0 or i == n_steps:              # the last frame is always at T
            lab, cs = pc.containers(c, V1, V2)
            box = lab > 0
            V = V1 + V2
            slab = pc.labels(V, pc.THRESH_V)
            inside = inside_shares(slab, box)
            maj, unassigned = assign_spots(slab, lab)
            skinds = spot_kinds(slab, lab, V1, V)                   # kind of the spots each container holds
            sfrac1 = float(np.mean([k > 0.5 for k in skinds.values()])) if skinds else 0.5
            occ = [x for x in cs if x["spots"] > 0]
            kinds = {x["id"]: x["kind1"] for x in occ}
            frac1 = float(np.mean([k > 0.5 for k in kinds.values()])) if kinds else 0.5
            frames.append({"t": round(i * p["dt"], 2), "containers": len(cs), "occupied": len(occ),
                           "spots_per_container": sorted(x["spots"] for x in cs),
                           "box_share": round(float(box.mean()), 4),
                           "v_in": round(float(V[box].mean()), 4) if box.any() else None,
                           "v_out": round(float(V[~box].mean()), 5) if (~box).any() else None,
                           "replicators": round(float(V.mean()), 5), "spots": int(inside.size),
                           "spots_outside": int((inside <= 0.5).sum()),         # at least half outside
                           "spots_straddling": int(((inside > 0.5) & (inside < 1.0)).sum()),
                           "spot_min_inside": round(float(inside.min()), 3) if inside.size else None,
                           "occupied_majority": sum(1 for v in maj.values() if v > 0),
                           "spots_per_container_majority": sorted(maj.values()),
                           "spots_unassigned": unassigned})
            if prev is not None:
                plab, pkinds, pfrac1, pskinds, psfrac1 = prev
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
                        # the same division scored by the spots: every daughter must hold a spot of its own (a spot
                        # belongs to one container only, so one straddling spot cannot count for two daughters)
                        if a in pskinds and pc.purity(pskinds[a]) > 0.9 and all(b in skinds for b in kids):
                            pk = pskinds[a]
                            ev.update(spot_parent_kind1=round(pk, 4), spot_kids_kind1=[round(skinds[b], 4) for b in kids],
                                      spot_same=float(np.mean([(skinds[b] > 0.5) == (pk > 0.5) for b in kids])),
                                      spot_null=round(psfrac1 if pk > 0.5 else 1.0 - psfrac1, 4))
                        divisions.append(ev)
            prev = (lab, kinds, frac1, skinds, sfrac1)
        if i < n_steps:                                  # the audit and images below see the state of the last frame
            c, U, V1, V2 = model.step(c, U, V1, V2, p)
    fr = frames
    inh = [d for d in divisions if "same" in d]
    inh_s = [d for d in divisions if "spot_same" in d]
    late = [f for f in fr if f["t"] >= T / 2]
    one_each = [float(np.mean([s == 1 for s in f["spots_per_container"]])) for f in late if f["containers"]]
    one_each_maj = [float(np.mean([s == 1 for s in f["spots_per_container_majority"]])) for f in late
                    if f["containers"]]
    res = {"dim": dim, "n": n, "seed": seed, "T": T, "kill": kill, "model": model.__name__,
           "params": {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in p.items()},   # every entry
           "frames": fr, "divisions": divisions,
           "n_divisions": len(divisions), "births": births, "merges": merges, "deaths": deaths,
           "n_inherit": len(inh), "inheritance": round(float(np.mean([d["same"] for d in inh])), 4) if inh else None,
           "null": round(float(np.mean([d["null"] for d in inh])), 4) if inh else None,
           "n_inherit_spot": len(inh_s),
           "inheritance_spot": round(float(np.mean([d["spot_same"] for d in inh_s])), 4) if inh_s else None,
           "null_spot": round(float(np.mean([d["spot_null"] for d in inh_s])), 4) if inh_s else None,
           "containers_first_last": [next((f["containers"] for f in fr if f["containers"]), 0), fr[-1]["containers"]],
           "late_one_spot_each": round(float(np.mean(one_each)), 3) if one_each else None,
           "late_one_spot_each_majority": round(float(np.mean(one_each_maj)), 3) if one_each_maj else None,
           "late_occupied_majority": round(float(np.mean([f["occupied_majority"] / f["containers"] for f in late
                                                           if f["containers"]])), 3) if one_each_maj else None,
           "late_in_out_ratio": round(float(np.median([f["v_in"] / max(f["v_out"], 1e-9) for f in late
                                                        if f["v_in"] is not None and f["v_out"] is not None])), 1)
           if any(f["v_in"] is not None for f in late) else None}
    if dim == 3:
        res["three_d"] = three_d_audit(c, V1 + V2, dx)
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
    ap.add_argument("--dx", type=float, default=1.0, help="grid spacing (protocell_one only); pass --n = L/dx")
    ap.add_argument("--set", action="append", default=[], help="law override, e.g. alpha=0")
    ap.add_argument("--model", default="protocell", choices=("protocell", "one"),
                    help="one = genesis/models/protocell_one.py (P17: the material is the replicators' breakdown)")
    a = ap.parse_args(argv)
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    tag = "".join(f"_{k}{v}" for k, v in ov.items()) + (f"_kill{a.kill}" if a.kill is not None else "")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    model = pc
    if a.model == "one":
        from genesis.models import protocell_one as model
        tag = "_one" + tag
    r = run(a.dim, a.seed, a.T, ov, a.kill, a.n, out=out, tag=tag, model=model, dx=a.dx)
    fr = r["frames"]
    k = max(1, len(fr) // 8)
    print(f"{a.dim}D seed={a.seed}{tag}: containers {[f['containers'] for f in fr][::k]} | occupied"
          f" {[f['occupied'] for f in fr][::k]} | share {[f['box_share'] for f in fr][::k]} | replicators"
          f" {[f['replicators'] for f in fr][::k]} | spots outside {[f['spots_outside'] for f in fr][::k]} straddling"
          f" {[f['spots_straddling'] for f in fr][::k]} | births {r['births']} divisions {r['n_divisions']} merges"
          f" {r['merges']} deaths {r['deaths']} | one spot each (late) {r['late_one_spot_each']} (majority"
          f" {r['late_one_spot_each_majority']}, occupied {r['late_occupied_majority']}) | in/out"
          f" {r['late_in_out_ratio']} | inheritance {r['inheritance']} of {r['n_inherit']} (null {r['null']}) |"
          f" by spots {r['inheritance_spot']} of {r['n_inherit_spot']} (null {r['null_spot']})",
          flush=True)
    if "three_d" in r:
        t3 = r["three_d"]
        print(f"  3D audit: material genuinely_3d {t3['material']['genuinely_3d']} (z share"
              f" {t3['material']['z_variation_fraction']}), replicators {t3['replicators']['genuinely_3d']} |"
              f" containers {t3['containers']}, solid balls {t3['solid_balls']}, min extent {t3['min_extent']}",
              flush=True)
    (out / f"pc{a.dim}d_s{a.seed}{tag}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
