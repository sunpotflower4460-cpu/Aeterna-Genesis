"""H8: an observed interior and an unobserved outside (a border) -- one-way, or a circulation?

    python tools/bath_circulation.py --out /tmp/h8                 # T = 0 / 0.02 / 0.05, seeds 1-3, 2D φ⁴ 128²
    python tools/bath_circulation.py --out /tmp/h8 --quick

Wave white (φ⁴, t = 0 on the hill + noise). The border strip (width 8) absorbs (γ = 0.3) and, when T > 0, also
kicks back at temperature T (fluctuation–dissipation; genesis/models/wave_klein_gordon.step). Both are PUT IN.
Measured on the interior only (the "observed" part):
* what the outside (the bath) takes by damping and gives back by its kicks, booked exactly at the border
  (given = 0 when T = 0), in the whole run and in the second half -- the circulation measure;
* energy that came in from the border and energy that left (genesis/diagnostics/exchange.ExchangeMeter), over the
  whole run and over the second half (after the start-up energy has gone),
* lumps of the 10-t-averaged energy density standing out of the interior's own background (median + thr × hill),
  tracked with the light-speed limit (genesis/diagnostics/lump_tracker): births and deaths per 1000 t, in the
  first and the second half of the run (does a balance settle?), and how many are alive at the end.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics.exchange import ExchangeMeter
from genesis.diagnostics.lump_tracker import Tracker, detect
from genesis.models import wave_klein_gordon as kg
from tools.snapshot import render_field


def run(T_bath: float, seed: int, T: float, n: int, thr: float, out: Path, snap: bool) -> dict:
    p = dict(kg.DEFAULTS, absorb=0.3, bath_T=T_bath)
    dt, hill = p["dt"], 0.25 * p["lam"]
    phi, pi = kg.make_initial((n, n), np.random.default_rng(seed), p)
    mask = kg.damping_mask((n, n), int(p["absorb_width"]))
    inner = mask == 0
    meter, late, tracker = ExchangeMeter(), ExchangeMeter(), Tracker((n, n))
    closed = dict(p, absorb=0.0)                    # the conservative part of the step
    damp = np.exp(-p["absorb"] * dt * mask)         # the bath part, done here exactly as the model does it,
    kick = np.sqrt(T_bath * (1.0 - damp * damp))    # so what the outside takes and gives can be booked
    taken = given = taken2 = given2 = 0.0
    per_win, acc, k, frames = int(round(10 / dt)), np.zeros((n, n)), 0, []
    steps = int(round(T / dt))
    for s in range(1, steps + 1):
        phi, pi = kg.step(phi, pi, closed)
        before = 0.5 * float((pi * pi).sum())
        pi = pi * damp
        mid = 0.5 * float((pi * pi).sum())
        if T_bath > 0:
            pi = pi + kick * np.random.default_rng([seed, s]).standard_normal(pi.shape)
        after = 0.5 * float((pi * pi).sum())
        taken += before - mid                         # the outside takes (dissipation)
        given += after - mid                          # the outside gives back (fluctuation), 0 when T = 0
        if s * dt >= T / 2:
            taken2 += before - mid
            given2 += after - mid
        e = kg.energy_density(phi, pi, p)
        meter.add(s * dt, float(e[inner].sum()))
        if s * dt >= T / 2:                          # the second half: after the start-up energy has left
            late.add(s * dt, float(e[inner].sum()))
        acc += e
        k += 1
        if k == per_win:
            avg = acc / k
            base = float(np.median(avg[inner]))
            excess = np.where(inner, (avg - base) / hill, 0.0)
            lumps, _ = detect(excess, thr, max_extent=n // 4)
            tracker.add(s * dt, lumps)
            frames.append({"t": round(s * dt, 1), "lumps": len(lumps), "E_inner": round(float(e[inner].sum()), 3),
                           "background": round(base / hill, 4), **meter.summary()})
            acc, k = np.zeros((n, n)), 0
            last_avg = avg
    if snap:
        render_field(last_avg / hill, str(out / f"T{T_bath}_s{seed}_energy.png"))
    tracks = tracker.summary()["tracks"]
    half = T / 2

    def rate(key_time, lo, hi):
        return round(1000 * sum(1 for x in tracks if lo < x[key_time] <= hi) / (hi - lo), 2)

    deaths = [x for x in tracks if x["end"] != "alive"]
    bath = {"taken": round(taken, 3), "given": round(given, 3), "taken_2nd_half": round(taken2, 3),
            "given_2nd_half": round(given2, 3),
            "balance_2nd_half": round(given2 / taken2, 4) if taken2 > 0 else None}
    return {"bath_T": T_bath, "seed": seed, "T": T, "bath": bath, "exchange": meter.summary(),
            "exchange_second_half": late.summary(),
            "frames": frames,
            "births_per_1000t": {"first_half": rate("born", 10, half), "second_half": rate("born", half, T)},
            "deaths_per_1000t": {"first_half": round(1000 * sum(1 for x in deaths if x["last"] <= half) / half, 2),
                                 "second_half": round(1000 * sum(1 for x in deaths if x["last"] > half) / half, 2)},
            "alive_end": sum(1 for x in tracks if x["end"] == "alive"),
            "longest_lifetime": max([x["lifetime"] for x in tracks] or [0]),
            "mean_lumps_second_half": round(float(np.mean([f["lumps"] for f in frames if f["t"] > half])), 2)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--thr", type=float, default=0.2, help="lump threshold above the interior median (× hill)")
    ap.add_argument("--only", nargs="*", type=float, default=None, help="bath temperatures to run")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds, T, n = ([1], 600.0, 96) if a.quick else ([1, 2, 3], 3000.0, 128)
    res = []
    for Tb in (a.only if a.only is not None else [0.0, 0.02, 0.05]):
        for seed in seeds:
            r = run(Tb, seed, T, n, a.thr, out, snap=(seed == seeds[0]))
            res.append(r)
            b = r["bath"]
            print(f"T={Tb:<5} seed={seed}: bath 2nd half takes {b['taken_2nd_half']:.1f} gives {b['given_2nd_half']:.1f}"
                  f" (gives/takes {b['balance_2nd_half']})"
                  f" | births/1000t {r['births_per_1000t']} deaths/1000t {r['deaths_per_1000t']}"
                  f" | alive {r['alive_end']} mean lumps (2nd half) {r['mean_lumps_second_half']} longest {r['longest_lifetime']}",
                  flush=True)
    tag = "summary" if a.only is None else "summary_T" + "_".join(str(x) for x in a.only)
    (out / f"{tag}.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
