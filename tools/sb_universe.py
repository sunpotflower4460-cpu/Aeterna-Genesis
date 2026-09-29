"""P19: a symmetric field breaks and differences are born -- what happens after that, in universes that differ only in
their CONDITIONS (3D first, 2D after). Nothing is aimed at; the census (genesis/diagnostics/emergence_census.py)
counts what formed without naming it.

    python tools/sb_universe.py run --preset yinyang --dim 3 --n 96 --seed 1 --T 400 --out /tmp/sb
    python tools/sb_universe.py run --preset continuous --expand --out /tmp/sb           # radiation-era expansion
    python tools/sb_universe.py run --preset continuous --set e=0 --term 0.lam=0.2 --out /tmp/sb
    python tools/sb_universe.py compare --presets yinyang,yinyang_middle,three_equal,continuous --seeds 1,2 --out …
    python tools/sb_universe.py table --out /tmp/sb

Every run writes run_<name>.json (the spec, the census every `every` time units, the lump tracks, the ω–k spectrum
of the last `window` time units, the energy drift and the lattice resolution) and PNG slices.

--expand: a(τ) = 1 + Hτ until the heaviest mode's length 1/(m·a) reaches `min_cells` cells (the lattice cannot
resolve further), with H chosen so that this happens at T; the run stops there.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from genesis.diagnostics import emergence_census as ec
from genesis.diagnostics import lump_tracker as lt
from genesis.models import sb_universe as sb
from tools.snapshot import colormap, render_field, write_png


def heaviest_mass(spec) -> float:
    """√(largest Hessian eigenvalue) of V at the valleys: the shortest length the vacuum has (in lattice units)."""
    rng = np.random.default_rng(0)
    R, N = spec["real"], spec["complex"]
    r = rng.standard_normal((R, 16))
    c = (rng.standard_normal((N, 16)) + 1j * rng.standard_normal((N, 16)))
    rr, cc = ec.roll_down(spec, r, c)
    best = 0.0
    h = 1e-4
    for k in range(16):
        x0 = ec._canon(spec, rr[:, k:k + 1], cc[:, k:k + 1])[:, 0]
        n = x0.size

        def V(x):
            a, b = ec._uncanon(spec, x[:, None])
            return float(sb.potential(spec, a, b)[0])
        H = np.array([[(V(x0 + (np.eye(n)[i] + np.eye(n)[j]) * h) - V(x0 + (np.eye(n)[i] - np.eye(n)[j]) * h)
                        - V(x0 - (np.eye(n)[i] - np.eye(n)[j]) * h) + V(x0 - (np.eye(n)[i] + np.eye(n)[j]) * h))
                       / (4 * h * h) for j in range(n)] for i in range(n)])
        best = max(best, float(np.linalg.eigvalsh(H).max()))
    return float(np.sqrt(max(best, 1e-12)))


def build_spec(preset: str | None, sets: list[str], terms: list[str]) -> dict:
    over = {}
    for s in sets:
        k, v = s.split("=")
        over[k] = json.loads(v) if v[:1] in "[{" or v in ("null", "true", "false") else float(v)
    for k in ("real", "complex"):
        if k in over:
            over[k] = int(over[k])
    spec = sb.spec_from(preset, **over)
    for s in terms:
        k, v = s.split("=")
        i, key = k.split(".")
        spec["terms"][int(i)][key] = float(v)
    return sb.validate(spec)


def _name(preset, sets, terms, dim, n, seed, T, expand) -> str:
    extra = "".join(f"_{s}" for s in sorted(sets)) + "".join(f"_t{s}" for s in sorted(terms))
    return f"{preset or 'custom'}{'_exp' if expand else ''}{extra}_{dim}d_n{n}_T{T:g}_s{seed}".replace("/", "-")


def _slice(a: np.ndarray) -> np.ndarray:
    return a[a.shape[0] // 2] if a.ndim == 3 else a


def _labels_png(labels: np.ndarray, path: Path, px: int = 360) -> None:
    lab = _slice(labels)
    k = max(int(labels.max()) + 1, 1)
    rgb = colormap(np.where(lab >= 0, (lab + 0.5) / k, 0.0))
    rgb[lab < 0] = 0                                              # between: black
    rep = max(1, px // lab.shape[0])
    write_png(np.repeat(np.repeat(rgb, rep, 0), rep, 1), path)


def run(spec: dict, dim: int, n: int, seed: int, T: float, every: float, window: float, out: Path, name: str,
        expand: bool = False, min_cells: float = 1.5, png: bool = True, lump_every: float = 2.0,
        long_life: float = 100.0, snaps: tuple = ()) -> dict:
    """long_life: a lump followed (every lump_every, within the light-cone reach) for at least this long counts as
    long-lived."""
    shape = (n,) * dim
    m = heaviest_mass(spec)
    res = {"core_cells_at_start": round(1.0 / m, 3)}
    if expand:
        a_max = 1.0 / (m * min_cells)
        if a_max <= 1.0:
            raise ValueError(f"the vacuum is already finer than {min_cells} cells: no room to expand")
        spec = dict(spec, H=(a_max - 1.0) / T, a_max=a_max)
    dt = sb.auto_dt(spec, dim)
    st = sb.make_initial(spec, shape, np.random.default_rng(seed))
    E0 = sb.energy(spec, st)
    frames, tracker, spectrum = [], lt.Tracker(shape, c=max(spec["c_real"] + spec["c_complex"] + [1.0])), \
        ec.Spectrum(spec)
    n_steps = int(round(T / dt))
    stride = max(1, int(round(every / dt)))
    sstride = max(1, int(round(0.5 / dt)))                          # spectrum samples: ω up to 2π
    w0 = max(0, n_steps - int(round(window / dt)))
    census_at = set(range(0, n_steps + 1, stride)) | {n_steps}
    spec_at = set(range(w0, n_steps + 1, sstride))
    lump_at = set(range(0, n_steps + 1, max(1, int(round(lump_every / dt)))))   # lumps are followed more often
    t0 = time.time()
    i, worst, last = 0, 0.0, None
    seen: dict[int, list] = {}
    for j in sorted(census_at | spec_at | lump_at):
        if j > i:
            st = sb.run(spec, st, dt, j - i)
            i = j
        if j in spec_at:
            spectrum.add(st)
        if j in lump_at and j not in census_at:
            tracker.add(float(st["tau"]), [{k: v for k, v in L.items() if k != "descr"}
                                           for L in ec.lumps(spec, st)["lumps"]])
        if j in census_at:
            c = ec.census(spec, st)
            tracker.add(c["t"], [{k: v for k, v in L.items() if k != "descr"} for L in c["_lumps"]])
            by_pos = {L["pos"]: L for L in c["_lumps"]}
            for tr in tracker.alive:                                  # what the followed lumps hold, at census times
                if tr.t[-1] == c["t"] and tr.pos[-1] in by_pos:
                    L = by_pos[tr.pos[-1]]
                    seen.setdefault(tr.id, []).append({"t": c["t"], "windings": L.get("windings"),
                                                       "valleys": L.get("valleys"), "size": L["size"]})
            last = c
            frames.append({k: v for k, v in c.items() if not k.startswith("_")})
            if png and any(abs(c["t"] - x) <= 0.5 * every for x in snaps):
                _labels_png(c["_labels"], out / f"{name}_labels_t{round(c['t']):04d}.png")
                render_field(_slice(sb.order_parameter(spec, st)), out / f"{name}_s_t{round(c['t']):04d}.png")
            if not spec["H"]:
                worst = max(worst, abs(sb.energy(spec, st) - E0))
            print(f"t={c['t']:.1f} a={c['a']:.3f} s={c['s_mean']:.3f} regions={c['domains']['regions']} "
                  f"between={c['domains']['between_fraction']:.3f} wind={c['windings'].get('per_field')} "
                  f"lumps={c['lumps']['n']} ({time.time() - t0:.0f}s)", flush=True)
    res.update({
        "name": name, "spec": spec, "dim": dim, "n": n, "seed": seed, "T": T, "dt": dt, "steps": n_steps,
        "frames": frames, "lumps": tracker.summary(), "spectrum": spectrum.result(),
        "long_lived_lumps": sum(1 for tr in tracker.tracks if tr.t[-1] - tr.t[0] >= long_life),
        "longest_lumps": [dict(x, seen=seen.get(x["id"], [])) for x in
                          sorted((tr.summary(shape) for tr in tracker.tracks), key=lambda x: -x["lifetime"])[:5]],
        "energy_drift": (worst / abs(E0)) if not spec["H"] else None,
        "energy_scale": E0,
        "core_cells_at_end": round(1.0 / (m * sb.scale_factor(spec, st["tau"])), 3),
        "state_sha256": hashlib.sha256(b"".join(np.ascontiguousarray(st[k]).tobytes()
                                                for k in ("r", "pr", "c", "pc", "th", "E"))).hexdigest(),
        "runtime_s": round(time.time() - t0, 1)})
    if dim == 3:
        from genesis.diagnostics.topology3d import three_d_authenticity
        res["three_d"] = three_d_authenticity(sb.order_parameter(spec, st))
    if png:
        _labels_png(last["_labels"], out / f"{name}_labels.png")
        render_field(_slice(sb.order_parameter(spec, st)), out / f"{name}_s.png")
        e = sb.energy_density(spec, st)
        render_field(e.max(0) if dim == 3 else e, out / f"{name}_energy.png")
    (out / f"run_{name}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def table(out: Path) -> str:
    rows = []
    for f in sorted(out.glob("run_*.json")):
        r = json.loads(f.read_text())
        c = r["frames"][-1]
        d = c.get("domains", {})
        sp = r.get("spectrum", {}).get("channels", {})
        rows.append("| " + " | ".join(str(x) for x in (
            r["name"], r["dim"], c["t"], c["a"], round(c["s_mean"], 3), f"{d.get('regions')}/{d.get('regions_big')}",
            d.get("between_fraction"), d.get("meetings"), d.get("boundary_pieces", {}).get("3+"),
            c["windings"].get("per_field"), c["windings"].get("shared_by_all"),
            f"{c['lumps']['n']}/{r.get('long_lived_lumps')}",
            r["lumps"]["events"], {k: v["branches_small_k"] for k, v in sp.items()},
            r["energy_drift"] and f"{r['energy_drift']:.1e}", r["core_cells_at_end"])) + " |")
    head = ("| run | dim | t | a | s | regions (all/≥27) | between | meetings | 3+ pieces | windings | shared "
            "| lumps (now/lived ≥100) | lump events "
            "| branches | dE/E | core cells |\n|" + "---|" * 16)
    return head + "\n" + "\n".join(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("run", "compare", "table"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--preset", default=None)
    ap.add_argument("--presets", default="yinyang,yinyang_middle,three_equal,continuous")
    ap.add_argument("--set", action="append", default=[], help="spec key, e.g. e=0.3, hbar=1e-3, complex=2")
    ap.add_argument("--term", action="append", default=[], help="term coefficient, e.g. 0.lam=0.2")
    ap.add_argument("--dim", type=int, default=3, choices=(2, 3))
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--T", type=float, default=400.0)
    ap.add_argument("--every", type=float, default=20.0)
    ap.add_argument("--window", type=float, default=200.0)
    ap.add_argument("--expand", action="store_true")
    ap.add_argument("--snaps", default="", help="times at which to also save the slice pictures, e.g. 60,80,120")
    ap.add_argument("--outside", default="closed,expand", help="compare: closed, expand or both")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n = a.n or (96 if a.dim == 3 else 384)
    if a.mode == "table":
        print(table(out))
        return 0
    jobs = []
    if a.mode == "run":
        jobs.append((a.preset, a.seed, a.expand))
    else:
        for p in a.presets.split(","):
            for s in (int(x) for x in a.seeds.split(",")):
                for o in a.outside.split(","):
                    jobs.append((p, s, o == "expand"))
    for preset, seed, expand in jobs:
        name = _name(preset, a.set, a.term, a.dim, n, seed, a.T, expand)
        if a.mode == "compare" and (out / f"run_{name}.json").exists():
            continue
        spec = build_spec(preset, a.set, a.term)
        try:
            r = run(spec, a.dim, n, seed, a.T, a.every, a.window, out, name, expand=expand,
                    snaps=tuple(float(x) for x in a.snaps.split(",") if x))
        except ValueError as err:
            print(name, "skipped:", err)
            continue
        print(name, "done", r["runtime_s"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
