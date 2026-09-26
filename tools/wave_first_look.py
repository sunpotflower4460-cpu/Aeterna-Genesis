"""First look at the wave white (P7-3): walls from the hilltop, and localized lumps below the mass gap.

    python tools/wave_first_look.py --out /tmp/wave            # both potentials, closed + absorbing, seeds 1-3
    python tools/wave_first_look.py --out /tmp/wave --quick    # 1 seed, shorter

For each run: 128², t = 0 on the hill + noise 0.01 (DEFAULTS), leapfrog dt = 0.2, up to t = 2000.
* series: energy, wall density, lumps (instantaneous, > 0.5 hill), fraction in the "up" valley (every 50 t)
* with the absorbing border (absorb = 0.3, width 8, a PUT-IN): at t = 2000 average the energy density over
  100 t, find localized regions (> 0.05 hill), then follow each for 500 t: dominant frequency of φ at its
  centre vs the vacuum mass gap (sqrt(2λ) for φ⁴, sqrt(λ) for sine-Gordon), its energy at start / end, and drift.
  Oscillating below the gap is the textbook mark of an oscillon (it cannot shed energy as linear waves).
Writes summary.json and PNG snapshots (tools/snapshot.render_field). Nothing here changes the physics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from genesis.models import wave_klein_gordon as kg
from tools.snapshot import render_field


def hill(p):
    return 2.0 * p["lam"] if p["potential"] == "sine_gordon" else 0.25 * p["lam"]


def mass_gap(p):
    return float(np.sqrt(p["lam"]) if p["potential"] == "sine_gordon" else np.sqrt(2 * p["lam"]))


def run(pot: str, absorb: float, seed: int, T: float, out: Path, snaps: bool) -> dict:
    p = dict(kg.DEFAULTS, potential=pot, absorb=absorb)
    dt = p["dt"]
    phi, pi = kg.make_initial((128, 128), np.random.default_rng(seed), p)
    mask = kg.damping_mask(phi.shape, int(p["absorb_width"]))
    up = kg.vacuum_index(np.array([1.0 if pot == "phi4" else 0.0]), p)[0]
    series, steps = [], int(T / dt)
    for n in range(steps + 1):
        if n % int(50 / dt) == 0:
            L, size = kg.lumps(phi, pi, p)
            series.append({"t": round(n * dt, 1), "E": round(kg.energy(phi, pi, p), 3), "walls": round(kg.wall_density(phi, p), 5),
                           "lumps": L, "lump_size": round(size, 1), "up": round(float((kg.vacuum_index(phi, p) == up).mean()), 3)})
        if snaps and n in (0, int(200 / dt), steps):
            tag = f"{pot}_a{absorb}_s{seed}_t{int(n * dt)}"
            render_field(kg.energy_density(phi, pi, p) / hill(p), str(out / f"{tag}_energy.png"))
            render_field(phi if pot == "phi4" else np.angle(np.exp(1j * phi)), str(out / f"{tag}_phi.png"))
        if n < steps:
            phi, pi = kg.step(phi, pi, p, mask)
    res = {"potential": pot, "absorb": absorb, "seed": seed, "series": series}
    if absorb > 0:
        res["lumps_below_gap"] = follow(phi, pi, p, mask, out if snaps else None, f"{pot}_s{seed}")
    return res


def follow(phi, pi, p, mask, out, tag) -> dict:
    dt = p["dt"]
    acc = np.zeros_like(phi)
    for _ in range(int(100 / dt)):
        phi, pi = kg.step(phi, pi, p, mask)
        acc += kg.energy_density(phi, pi, p)
    acc /= int(100 / dt)
    if out is not None:
        render_field(acc / hill(p), str(out / f"{tag}_energy_avg.png"))
    lab, n = ndimage.label(acc > 0.05 * hill(p))
    blobs = []
    for i in range(1, n + 1):
        sel = lab == i
        if sel.sum() >= 3:
            cy, cx = ndimage.center_of_mass(acc * sel)
            blobs.append({"y": float(cy), "x": float(cx), "area": int(sel.sum()), "E": float(acc[sel].sum())})
    e_total = kg.energy(phi, pi, p)
    rec = [[] for _ in blobs]
    ends = [[None, None] for _ in blobs]
    for k in range(int(500 / dt)):
        phi, pi = kg.step(phi, pi, p, mask)
        if k in (0, int(500 / dt) - 1):
            e = kg.energy_density(phi, pi, p)
        for i, b in enumerate(blobs):
            y, x = int(round(b["y"])) % phi.shape[0], int(round(b["x"])) % phi.shape[1]
            rec[i].append(float(phi[y, x]))
            if k in (0, int(500 / dt) - 1):
                win = e[max(0, y - 10):y + 11, max(0, x - 10):x + 11]
                ends[i][0 if k == 0 else 1] = float(win.sum())
    rows = []
    for i, b in enumerate(blobs):
        s = np.array(rec[i])
        s = s - (1.0 if p["potential"] == "phi4" else 0.0) if p["potential"] == "phi4" else s - np.round(s / (2 * np.pi)) * 2 * np.pi
        f = np.abs(np.fft.rfft(s - s.mean()))
        w = float((np.fft.rfftfreq(len(s), dt) * 2 * np.pi)[np.argmax(f[1:]) + 1])
        rows.append({"area": b["area"], "E_share": round(b["E"] / e_total, 3), "omega": round(w, 3),
                     "mass_gap": round(mass_gap(p), 3), "below_gap": bool(w < mass_gap(p)),
                     "amp": round(float(np.abs(s).max()), 3), "E_window_start": round(ends[i][0], 3),
                     "E_window_end": round(ends[i][1], 3)})
    return {"E_total": round(e_total, 2), "regions": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds, T = ([1], 400.0) if a.quick else ([1, 2, 3], 2000.0)
    results = []
    for pot in ("phi4", "sine_gordon"):
        for absorb in (0.0, 0.3):
            for seed in seeds:
                r = run(pot, absorb, seed, T, out, snaps=(seed == seeds[0]))
                results.append(r)
                last = r["series"][-1]
                below = [x for x in r.get("lumps_below_gap", {}).get("regions", []) if x["below_gap"]]
                print(f"{pot:12s} absorb={absorb} seed={seed}: t=50 walls {r['series'][1]['walls']}"
                      f" | t={last['t']:g} E {last['E']} walls {last['walls']} up {last['up']}"
                      + (f" | below-gap regions {len(below)}" if absorb else ""), flush=True)
    (out / "summary.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
