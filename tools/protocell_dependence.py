"""Do the replicators come to NEED their containers when no law says the material helps them (P18, ladder R4)?

Three ways to measure a dependence (3D first, 2D after):

    python tools/protocell_dependence.py point --dim 3 --n 32 --k 0.07 --aff 1 --seed 1 --T 200 --out /tmp/dep
        one point of the k × aff map: the run with material (y as the law) and the same t = 0 with no material at
        all (NO_MATERIAL: y = 0, no back-reaction, no noise in c, so c ≡ −1 exactly); D_y = 1 − V(none)/V(y).
    python tools/protocell_dependence.py knockout --dim 3 --k 0.08 --aff 0.5 --seed 1 --t0 200 --dt_after 200 --out …
        run to t0, then branch: one copy as it is, one with the material dissolved (c = −1 + fresh noise);
        D_ko = 1 − V(dissolved)/V(intact) at t0 + dt_after, and whether containers form again and the
        replicators recover. --no_remake: the dissolved copy can never make material again.
    python tools/protocell_dependence.py summary --out /tmp/dep
        the map: for each k and aff, dead / lives anywhere (the container is a shadow) / lives only with its
        material (dependent).

With aff = 0 the replicators' equations do not contain c (genesis/models/protocell_partition.py), so D is exactly 0:
that is the check of the tool, not a finding. The kill of the replicators (the other direction) is
tools/protocell_run.py --kill.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import protocell as pc
from genesis.models import protocell_partition as pp
from tools.protocell_run import run as pc_run

DEAD = 1e-4          # mean replicator density below this = gone
DEPENDENT = 0.5      # D above this = the replicators need the material
# "without material": never made (y = 0), and c ≡ −1 exactly (no back-reaction of the solutes on c, no noise in c;
# make_initial draws the same random numbers, so the seeds are the same). With y = 0 alone and aff > 0 the solutes
# still pull c by a few percent (back = 1), which is not "no material". With c ≡ −1 the partition term is exactly 0,
# so this control is the same run for every aff (tests/test_protocell_partition.py).
NO_MATERIAL = {"y": 0.0, "back": 0.0, "noise": 0.0}


def classify(v_with: float, v_without: float) -> str:
    if v_with < DEAD:
        return "dead"
    d = 1.0 - v_without / v_with
    return "dependent" if d > DEPENDENT else "anywhere"


def point(dim: int, n: int, k: float, aff: float, seed: int, T: float, extra: dict | None = None) -> dict:
    ov = dict(extra or {}, k=k, aff=aff)
    a = pc_run(dim, seed, T, ov, n=n, model=pp)
    b = pc_run(dim, seed, T, dict(ov, **NO_MATERIAL), n=n, model=pp)
    va, vb = a["frames"][-1]["replicators"], b["frames"][-1]["replicators"]
    last = a["frames"][-1]
    return {"mode": "point", "dim": dim, "n": n, "k": k, "aff": aff, "seed": seed, "T": T, "extra": extra or {},
            "params": a["params"], "v_with": va, "v_without": vb,
            "D_y": round(1.0 - vb / va, 4) if va > 0 else None, "class": classify(va, vb),
            "containers": last["containers"], "occupied_majority": last["occupied_majority"],
            "in_out": a["late_in_out_ratio"], "one_spot_each": a["late_one_spot_each_majority"],
            "divisions": a["n_divisions"], "inheritance_spot": a["inheritance_spot"],
            "n_inherit_spot": a["n_inherit_spot"], "spots_with": last["spots"], "spots_without": b["frames"][-1]["spots"],
            "three_d": a.get("three_d")}


def _obs(c, V1, V2):
    lab, cs = pc.containers(c, V1, V2)
    V = V1 + V2
    return {"replicators": round(float(V.mean()), 6), "containers": len(cs),
            "spots": int(pc.labels(V, pc.THRESH_V).max())}


def knockout(dim: int, n: int, k: float, aff: float, seed: int, t0: float, dt_after: float, every: float = 10.0,
             extra: dict | None = None, remake: bool = True) -> dict:
    """remake=False: after the knockout the dissolved copy can never make material again (NO_MATERIAL from t0 on,
    c ≡ −1) -- do replicators that grew up with containers die without them?"""
    p = dict(pp.DEFAULTS if dim == 3 else pp.DEFAULTS_2D, **(extra or {}), k=k, aff=aff)
    shape = (n,) * dim
    s = pp.make_initial(shape, np.random.default_rng(seed), p)
    for _ in range(int(round(t0 / p["dt"]))):
        s = pp.step(*s, p)
    if remake:
        c_ko = -1.0 + p["noise"] * np.random.default_rng(seed + 10_000).standard_normal(shape)
        pb = p
    else:
        c_ko, pb = np.full(shape, -1.0), dict(p, **NO_MATERIAL)
    a, b = s, (c_ko, *s[1:])
    stride = int(round(every / p["dt"]))
    series = []
    n_after = int(round(dt_after / p["dt"]))
    for i in range(n_after + 1):
        if i % stride == 0 or i == n_after:              # the last sample is always at t0 + dt_after
            series.append({"t": round(t0 + i * p["dt"], 2), "intact": _obs(a[0], a[2], a[3]),
                           "dissolved": _obs(b[0], b[2], b[3])})
        if i < n_after:
            a, b = pp.step(*a, p), pp.step(*b, pb)
    va, vb = series[-1]["intact"]["replicators"], series[-1]["dissolved"]["replicators"]
    low = min(x["dissolved"]["replicators"] for x in series)
    return {"mode": "knockout", "remake": remake, "dim": dim, "n": n, "k": k, "aff": aff, "seed": seed, "t0": t0,
            "dt_after": dt_after, "extra": extra or {}, "params": p, "series": series,
            "D_ko": round(1.0 - vb / va, 4) if va > 0 else None,
            "lowest_after_knockout": low, "v_intact_at_t0": series[0]["intact"]["replicators"],
            "recovered": bool(va > 0 and vb >= 0.5 * va),
            "containers_again": series[-1]["dissolved"]["containers"]}


def summary(out: Path) -> dict:
    rows = [json.loads(f.read_text()) for f in sorted(out.glob("point_*.json"))]
    table: dict = {}
    for r in rows:
        key = (r["dim"], r["n"], r["T"], json.dumps(r["extra"], sort_keys=True))
        table.setdefault(key, []).append(r)
    res = []
    for (dim, n, T, extra), rs in sorted(table.items()):
        affs = sorted({r["aff"] for r in rs})
        ks = sorted({r["k"] for r in rs})
        grid = {f"aff={a}": {f"{k:.4f}": sorted({r["class"] for r in rs if r["aff"] == a and r["k"] == k})
                             for k in ks} for a in affs}
        window = {}
        for a in affs:
            dep = [k for k in ks if all(r["class"] == "dependent" for r in rs if r["aff"] == a and r["k"] == k)
                   and any(r["aff"] == a and r["k"] == k for r in rs)]
            window[f"aff={a}"] = [min(dep), max(dep)] if dep else None
        res.append({"dim": dim, "n": n, "T": T, "extra": json.loads(extra), "grid": grid, "dependent_k": window})
    return {"maps": res}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("point", "knockout", "summary"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--k", type=float, default=None)
    ap.add_argument("--aff", type=float, default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T", type=float, default=200.0)
    ap.add_argument("--t0", type=float, default=200.0)
    ap.add_argument("--dt_after", type=float, default=100.0)
    ap.add_argument("--set", action="append", default=[], help="other law override, e.g. back=0")
    ap.add_argument("--no_remake", action="store_true", help="knockout: the material can never form again")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.mode == "summary":
        r = summary(out)
        (out / "summary.json").write_text(json.dumps(r, indent=1))
        print(json.dumps(r, indent=1))
        return 0
    extra = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    n = a.n or (48 if a.dim == 3 else 128)
    d = pp.DEFAULTS if a.dim == 3 else pp.DEFAULTS_2D
    k = d["k"] if a.k is None else a.k
    aff = d["aff"] if a.aff is None else a.aff
    tag = "".join(f"_{kk}{v}" for kk, v in extra.items())
    if a.mode == "point":
        r = point(a.dim, n, k, aff, a.seed, a.T, extra)
        name = f"point_{a.dim}d_n{n}_T{a.T:g}_k{k:.4f}_aff{aff:g}_s{a.seed}{tag}.json"
        print({x: r[x] for x in ("k", "aff", "v_with", "v_without", "D_y", "class", "containers", "in_out")})
    else:
        r = knockout(a.dim, n, k, aff, a.seed, a.t0, a.dt_after, extra=extra, remake=not a.no_remake)
        tag += "_noremake" if a.no_remake else ""
        name = f"ko_{a.dim}d_n{n}_k{k:.4f}_aff{aff:g}_s{a.seed}_t{a.t0:g}{tag}.json"
        print({x: r[x] for x in ("k", "aff", "D_ko", "recovered", "containers_again", "lowest_after_knockout")})
    (out / name).write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
