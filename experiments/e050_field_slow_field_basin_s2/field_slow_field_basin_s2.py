#!/usr/bin/env python3
"""e050 slow-field basin memory -- ROBUSTNESS + 3D promotion (P07 / S2). role S, 2D screen -> 3D.

S2 stress-tests the S1 candidate (e049): the slow-field basin memory (hysteresis EXCESS over the matched g=0
OFF control) must survive (a) a coupling-strength sweep with a clear onset band, (b) resolution changes (not a
finite-size artifact), (c) multiple seeds, and (d) promotion from 2D to 3D. Same honest frame as S1: role S
(placed fields), local bidirectional coupling, matched OFF control, energy monitored, no target encoding.

  d_t psi = [alpha0 + g*s]*psi - |psi|^2*psi + lap(psi)     (dimension-agnostic local Laplacian)
  d_t s   = (1/tau)*(|psi|^2 - s) + Ds*lap(s)
memory(g,L,dim) := hysteresis_area(g) - hysteresis_area(0)   (EXCESS over the sweep-rate baseline)
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = dict(tau=10.0, Ds=0.5, dt=0.05, alpha_hi=0.6, alpha_lo=-0.6, n_alpha=13, settle=400, g_ref=0.6)
CONFIG_FULL = dict(L2=40, K=180, gs=(0.0, 0.15, 0.3, 0.45, 0.6, 0.75), Ls=(32, 48, 64),
                   seeds=(0, 1, 2, 3), L3=24, K3=120)
CONFIG_QUICK = dict(L2=28, K=90, gs=(0.0, 0.3, 0.6), Ls=(24, 32), seeds=(0, 1), L3=16, K3=70)
MARGIN = 0.06        # excess must exceed this to count as memory (preregistered, same scale as S1)


def _lap(f):
    out = -2.0 * f.ndim * f
    for ax in range(f.ndim):
        out = out + np.roll(f, 1, ax) + np.roll(f, -1, ax)
    return out


def hysteresis_area(shape, g, K, p, seed):
    rng = np.random.default_rng(seed)
    psi = 0.05 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    s = np.zeros(shape)
    dt, tau, Ds = p["dt"], p["tau"], p["Ds"]

    def step(a):
        nonlocal psi, s
        aeff = a + g * s
        psi = psi + dt * (aeff * psi - np.abs(psi) ** 2 * psi + _lap(psi))
        s = s + dt * ((np.abs(psi) ** 2 - s) / tau + Ds * _lap(s))
    for _ in range(p["settle"]):
        step(p["alpha_hi"])
    al = np.linspace(p["alpha_hi"], p["alpha_lo"], p["n_alpha"])
    au = np.linspace(p["alpha_lo"], p["alpha_hi"], p["n_alpha"])
    down, up, emax = [], [], 0.0
    for a in al:
        for _ in range(K):
            step(a)
        down.append(float(np.mean(np.abs(psi) ** 2)))
        emax = max(emax, float(np.mean(np.abs(psi) ** 4)))
    for a in au:
        for _ in range(K):
            step(a)
        up.append(float(np.mean(np.abs(psi) ** 2)))
    down = np.array(down)[::-1]; up = np.array(up)
    dalpha = (p["alpha_hi"] - p["alpha_lo"]) / (p["n_alpha"] - 1)
    return float(np.sum(np.abs(down - up)) * dalpha), emax


def excess(shape, g, K, p, seed):
    a_on, e_on = hysteresis_area(shape, g, K, p, seed)
    a_off, e_off = hysteresis_area(shape, 0.0, K, p, seed)
    return a_on - a_off, max(e_on, e_off)


def run(cfg, p=FROZEN):
    L2, K = cfg["L2"], cfg["K"]
    # (a) coupling-strength band: excess vs g (2D), onset g*
    gband = []
    a0, _ = hysteresis_area((L2, L2), 0.0, K, p, 0)
    for g in cfg["gs"]:
        ag, _e = hysteresis_area((L2, L2), g, K, p, 0)
        gband.append(dict(g=float(g), area=round(ag, 4), excess=round(ag - a0, 4)))
    onset = next((r["g"] for r in gband if r["excess"] > MARGIN), None)
    band_monotone = all(gband[i + 1]["excess"] >= gband[i]["excess"] - 0.03 for i in range(len(gband) - 1))

    # (b) resolution robustness: excess(L) at g_ref (2D)
    res = []
    for L in cfg["Ls"]:
        ex, _e = excess((L, L), p["g_ref"], K, p, 0)
        res.append(dict(L=int(L), excess=round(ex, 4)))
    res_ok = all(r["excess"] > MARGIN for r in res)

    # (c) seed robustness at reference (2D)
    seed_ex = [excess((L2, L2), p["g_ref"], K, p, s)[0] for s in cfg["seeds"]]
    seed_mean = float(np.mean(seed_ex)); seed_std = float(np.std(seed_ex))
    seeds_ok = (seed_mean - seed_std) > MARGIN

    # (d) 2D -> 3D promotion
    ex3, emax3 = excess((cfg["L3"],) * 3, p["g_ref"], cfg["K3"], p, 0)
    three_d_ok = ex3 > MARGIN and np.isfinite(emax3)

    robust = band_monotone and (onset is not None) and res_ok and seeds_ok and three_d_ok
    verdict = "robust_slow_field_basin_memory_candidate" if robust else (
        "2d_only_or_partial" if (seeds_ok and not three_d_ok) else "reliability_limited")
    checks = {
        "g-band has an onset and is ~monotone (excess grows with coupling)": band_monotone and onset is not None,
        "resolution robust: excess>margin at all L (not finite-size)": res_ok,
        "seed robust: mean-std excess > margin": seeds_ok,
        "3D promotion: excess>margin in 3D (survives dimension)": three_d_ok,
    }
    return dict(g_band=gband, onset_g=onset, resolution=res, seed_excess=[round(x, 4) for x in seed_ex],
                seed_mean=round(seed_mean, 4), seed_std=round(seed_std, 4),
                excess_3d=round(ex3, 4), energy_max_3d=emax3, verdict=verdict, checks=checks,
                all_ok=all(checks.values()), margin=MARGIN,
                matched_control="excess = area(g) - area(g=0), same grid/seed/steps/dt at every point")


def main(argv=None):
    ap = argparse.ArgumentParser(description="e050 P07/S2 slow-field basin memory robustness + 3D (role S)")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e050 slow-field basin memory ROBUSTNESS + 3D -- P07 / S2 (role S) ===")
    r = run(cfg)
    print("  (a) coupling band g -> excess:", [(x["g"], x["excess"]) for x in r["g_band"]], " onset g*=", r["onset_g"])
    print("  (b) resolution L -> excess:", [(x["L"], x["excess"]) for x in r["resolution"]])
    print("  (c) seeds excess=%s  mean=%.3f std=%.3f" % (r["seed_excess"], r["seed_mean"], r["seed_std"]))
    print("  (d) 3D excess=%.3f (energy_max=%.2e)" % (r["excess_3d"], r["energy_max_3d"]))
    for k, ok in r["checks"].items():
        print("   [%s] %s" % ("PASS" if ok else "FAIL", k))
    passed = r["all_ok"]
    print("STATUS:", "GREEN" if passed else "RED", "(role S: GREEN = robust across g/L/seed/3D; else honest partial)")
    print("  VERDICT:", r["verdict"])
    result = dict(experiment="e050_field_slow_field_basin_s2", frontier="P07", rung="S2", role="S",
                  status="GREEN" if passed else "RED", frozen=FROZEN,
                  config={k: v for k, v in cfg.items() if k != "seeds"}, **r)
    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        def _np(o):
            if isinstance(o, (np.bool_,)):
                return bool(o)
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            raise TypeError(repr(o))
        json.dump(result, open(os.path.join(args.out, "basin_memory_robustness.json"), "w"), indent=2, default=_np)
        print("wrote", os.path.join(args.out, "basin_memory_robustness.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
