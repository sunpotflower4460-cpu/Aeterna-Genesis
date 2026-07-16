#!/usr/bin/env python3
"""e051 grown slow-field memory -- E-candidate bridge (P07). Does the memory field s GROW from an
undifferentiated quench (s(t=0)=0), not placed, and still tilt the return basin?

S1/S2 (e049/e050) PLACED both psi and s (role S) and showed hysteresis EXCESS over a matched g=0 OFF
control. This asks the north-star question for the memory field ITSELF: is the memory-carrying s a placed
template, or does it grow from |psi|^2 history out of s(t=0)=0? Same local law as e049/e050 (the LAW is
placed, exactly as GL is placed in G001); the question is whether the s STRUCTURE grows.

  d_t psi = [alpha + g*s]*psi - |psi|^2*psi + lap(psi)      (dimension-agnostic local Laplacian)
  d_t s   = (1/tau)*(|psi|^2 - s) + Ds*lap(s)

Three matched systems (identical grid/seed/schedule/dt/steps):
  OFF     g=0, s passive                              -> hysteresis baseline (sweep-rate/critical-slowing)
  grown   g>0, s(t=0)=0 (undifferentiated)            -> E-candidate: memory field NOT placed
  placed  g>0, s(t=0)=structured template (S ref)     -> "placed" reference, upper bound

memory excess := hysteresis_area(system) - hysteresis_area(OFF).  Pre-registered in
docs/frontier/F0_P07_addendum_grown_slow_field.md (E1..E4, verdict matrix). role decided from the result.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = dict(tau=10.0, Ds=0.5, dt=0.05, alpha_hi=0.6, alpha_lo=-0.6, n_alpha=13, settle=400, g_ref=0.6)
CONFIG_FULL = dict(L2=40, K=180, seeds=(0, 1, 2, 3), L3=24, K3=120)
CONFIG_QUICK = dict(L2=28, K=90, seeds=(0, 1), L3=16, K3=70)
MARGIN = 0.06        # excess must exceed this to count as memory (same prereg scale as S1/S2)


def _lap(f):
    out = -2.0 * f.ndim * f
    for ax in range(f.ndim):
        out = out + np.roll(f, 1, ax) + np.roll(f, -1, ax)
    return out


def _struct(s):
    """spatial structure of the slow field: std + mean gradient energy (0 for an undifferentiated s=const)."""
    g2 = 0.0
    for ax in range(s.ndim):
        g2 = g2 + np.mean((np.roll(s, -1, ax) - s) ** 2)
    return float(np.std(s)), float(g2)


def hysteresis_area(shape, g, K, p, seed, s_mode="grown"):
    """Return (area, energy_max, struct0, struct_settle, (mem_hold, field_end)).
    s_mode: off(g=0) | grown(g>0, s(t0)=0, slow tau) | placed(g>0, structured template) |
            copy(g>0, s=|psi|^2 instantaneously each step -> coupling but NO history/lag)."""
    rng = np.random.default_rng(seed)
    psi = 0.05 * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    if s_mode == "placed":
        # PLACED template: pre-load s to the ordered-well level with a smooth spatial pattern (structure at t=0).
        s = p["alpha_hi"] * (1.0 + 0.1 * rng.standard_normal(shape))
    elif s_mode == "copy":
        s = np.abs(psi) ** 2                   # instantaneous copy: s tracks |psi|^2 with no lag
    else:
        s = np.zeros(shape)                    # grown / off: undifferentiated, ZERO structure at t=0
    dt, tau, Ds = p["dt"], p["tau"], p["Ds"]
    struct0 = _struct(s)

    def step(a):
        nonlocal psi, s
        aeff = a + g * s
        psi = psi + dt * (aeff * psi - np.abs(psi) ** 2 * psi + _lap(psi))
        if s_mode == "copy":
            s = np.abs(psi) ** 2               # tau -> 0: memoryless instantaneous copy (no history)
        else:
            s = s + dt * ((np.abs(psi) ** 2 - s) / tau + Ds * _lap(s))
    for _ in range(p["settle"]):
        step(p["alpha_hi"])
    struct_settle = _struct(s)                 # for grown this grew from 0 -> memory pattern is GROWN

    al = np.linspace(p["alpha_hi"], p["alpha_lo"], p["n_alpha"])
    au = np.linspace(p["alpha_lo"], p["alpha_hi"], p["n_alpha"])
    down, up, emax = [], [], 0.0
    mem_hold, field_end = 0.0, 0.0
    for i, a in enumerate(al):
        for _ in range(K):
            step(a)
        down.append(float(np.mean(np.abs(psi) ** 2)))
        emax = max(emax, float(np.mean(np.abs(psi) ** 4)))
        if i == len(al) - 1:                   # most-disordered end of the down-sweep
            field_end = float(np.mean(np.abs(psi) ** 2))   # a copy would give s ~ this (~0)
            mem_hold = float(np.mean(s))                    # s still holding the ordered past = history
    for a in au:
        for _ in range(K):
            step(a)
        up.append(float(np.mean(np.abs(psi) ** 2)))
    down = np.array(down)[::-1]; up = np.array(up)
    dalpha = (p["alpha_hi"] - p["alpha_lo"]) / (p["n_alpha"] - 1)
    area = float(np.sum(np.abs(down - up)) * dalpha)
    return area, emax, struct0, struct_settle, (mem_hold, field_end)


def _area(shape, g, K, p, seed, s_mode):
    return hysteresis_area(shape, g, K, p, seed, s_mode)


def run(cfg, p=FROZEN):
    L2, K = cfg["L2"], cfg["K"]
    shape = (L2, L2)
    g = p["g_ref"]
    # matched trio (2D), identical seed/grid/schedule
    a_off, e_off, _s0o, _sso, _lo = _area(shape, 0.0, K, p, 0, "off")
    a_grn, e_grn, s0_g, ss_g, hold_g = _area(shape, g, K, p, 0, "grown")
    a_plc, e_plc, s0_p, ss_p, hold_p = _area(shape, g, K, p, 0, "placed")
    a_cpy, e_cpy, _s0c, _ssc, hold_c = _area(shape, g, K, p, 0, "copy")   # instantaneous, no-history control
    excess_grown = a_grn - a_off
    excess_placed = a_plc - a_off
    excess_copy = a_cpy - a_off                 # coupling with NO lag: the memoryless part of the excess

    # E3: memory structure GREW from an undifferentiated s(t=0)=0
    grown_struct_t0 = s0_g[0]                       # == 0 by construction
    grown_struct_settle = ss_g[0]
    structure_grew = (grown_struct_t0 < 1e-9) and (grown_struct_settle > 1e-3)
    # E2: grown is not a weak shadow of the placed template
    ratio_grown_to_placed = excess_grown / excess_placed if abs(excess_placed) > 1e-9 else float("inf")
    not_a_shadow = ratio_grown_to_placed > 0.5
    # E4: grown s holds HISTORY (lag), not an instantaneous |psi|^2 copy. The clean discriminator (prereg §6
    # memory_copy_collapse) is the instantaneous-copy control: it has the SAME coupling but tau->0 (no lag).
    # history_gain = excess(slow grown-s) - excess(instantaneous copy) isolates what the lag/memory adds.
    hold_grown, field_end_grown = hold_g
    history_gain = excess_grown - excess_copy
    holds_history = history_gain > MARGIN
    # E1: grown memory clears the bar; OFF is ~zero by construction
    grown_has_memory = excess_grown > MARGIN
    off_null = abs(a_off - a_off) < 1e-12  # trivially true; OFF is the subtrahend (excess=0 by construction)

    # 3D grown confirm (single point)
    a_off3, e_off3, _a, _b, _c = _area((cfg["L3"],) * 3, 0.0, cfg["K3"], p, 0, "off")
    a_grn3, e_grn3, _d, _e, _f = _area((cfg["L3"],) * 3, g, cfg["K3"], p, 0, "grown")
    excess_3d_grown = a_grn3 - a_off3
    grown_3d_ok = excess_3d_grown > MARGIN and np.isfinite(max(e_grn3, e_off3))

    # seed robustness of the grown excess (2D)
    seed_ex = []
    for sd in cfg["seeds"]:
        ao, _1, _2, _3, _4 = _area(shape, 0.0, K, p, sd, "off")
        ag, _5, _6, _7, _8 = _area(shape, g, K, p, sd, "grown")
        seed_ex.append(ag - ao)
    seed_mean = float(np.mean(seed_ex)); seed_std = float(np.std(seed_ex))
    seeds_ok = (seed_mean - seed_std) > MARGIN

    energy_ok = all(np.isfinite(x) for x in (e_off, e_grn, e_plc, e_off3, e_grn3))

    # verdict (pre-registered §4)
    if not energy_ok:
        verdict = "energy_instability"
    elif grown_has_memory and structure_grew and holds_history and seeds_ok:
        verdict = "grown_slow_field_memory_candidate"       # E-candidate
    elif (not grown_has_memory) and excess_placed > MARGIN:
        verdict = "placed_template_required"                # stays role S
    elif abs(excess_grown) <= MARGIN and abs(excess_placed) <= MARGIN:
        verdict = "common_attractor"                        # null
    elif grown_has_memory and not holds_history:
        verdict = "memory_copy_collapse"
    else:
        verdict = "partial"

    checks = {
        "E1 grown memory: excess(grown) > margin (memory from undifferentiated s=0)": grown_has_memory,
        "E2 not a shadow: excess(grown)/excess(placed) > 0.5": not_a_shadow,
        "E3 structure GREW: struct(s;t0)=0 -> struct(s;settle)>0": structure_grew,
        "E4 holds history: excess(grown) - excess(instantaneous copy) > margin (lag adds memory)": holds_history,
        "seed robust: mean-std excess(grown) > margin": seeds_ok,
        "3D grown: excess(grown,3D) > margin (survives dimension)": grown_3d_ok,
    }
    e_candidate = verdict == "grown_slow_field_memory_candidate"
    # exit/CI validity is separate from the scientific verdict: a valid matched-control run that reaches ANY
    # definitive pre-registered classification (incl. the honest nulls) is a successful negative-capable run.
    run_valid = energy_ok and verdict not in ("numerical_failure",)
    return dict(
        verdict=verdict, e_candidate=e_candidate, run_valid=run_valid, energy_ok=energy_ok,
        excess_grown=round(excess_grown, 4), excess_placed=round(excess_placed, 4),
        excess_off=0.0, excess_copy=round(excess_copy, 4), history_gain=round(history_gain, 4),
        ratio_grown_to_placed=round(ratio_grown_to_placed, 3),
        grown_struct_t0=round(grown_struct_t0, 6), grown_struct_settle=round(grown_struct_settle, 4),
        placed_struct_t0=round(s0_p[0], 4),
        mem_hold_grown=round(hold_grown, 4), field_end_grown=round(field_end_grown, 6),
        seed_excess=[round(x, 4) for x in seed_ex],
        seed_mean=round(seed_mean, 4), seed_std=round(seed_std, 4),
        excess_3d_grown=round(excess_3d_grown, 4), energy_max_2d=round(max(e_off, e_grn, e_plc), 4),
        energy_max_3d=round(max(e_off3, e_grn3), 4), checks=checks, all_ok=all(checks.values()),
        margin=MARGIN, matched_control="excess = area(system) - area(g=0 OFF), same grid/seed/schedule/dt")


def main(argv=None):
    ap = argparse.ArgumentParser(description="e051 grown slow-field memory -- E-candidate bridge (P07)")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL
    print("=== e051 grown slow-field memory -- E-candidate bridge (P07) ===")
    r = run(cfg)
    print("  excess: grown=%.3f  placed=%.3f  off=0.000   (ratio grown/placed=%.2f)"
          % (r["excess_grown"], r["excess_placed"], r["ratio_grown_to_placed"]))
    print("  struct(s) grown: t0=%.6f -> settle=%.4f   (placed t0=%.3f)  << 育ったのか置いたのか"
          % (r["grown_struct_t0"], r["grown_struct_settle"], r["placed_struct_t0"]))
    print("  history: excess(copy tau->0)=%.3f  history_gain=grown-copy=%.3f (>margin=%.2f?)  << 履歴か現在のコピーか"
          % (r["excess_copy"], r["history_gain"], r["margin"]))
    print("  seeds excess(grown)=%s  mean=%.3f std=%.3f" % (r["seed_excess"], r["seed_mean"], r["seed_std"]))
    print("  3D grown excess=%.3f" % r["excess_3d_grown"])
    for k, ok in r["checks"].items():
        print("   [E-gate %s] %s" % ("PASS" if ok else "FAIL", k))
    run_valid = r["run_valid"]
    print("STATUS:", "GREEN" if run_valid else "RED",
          "(GREEN = valid matched-control run reached a definitive pre-registered verdict; the science is below)")
    print("  SCIENTIFIC VERDICT:", r["verdict"], " -- E-candidate supported:", r["e_candidate"])
    if r["verdict"] == "memory_copy_collapse":
        print("  => the hysteresis EXCESS is coupling-renormalization, NOT slow-field lag-memory:")
        print("     an instantaneous copy (tau->0) reproduces it (history_gain=%.3f <= margin=%.2f)."
              % (r["history_gain"], r["margin"]))
    role = "E" if r["e_candidate"] else "N"
    result = dict(experiment="e051_grown_slow_field", frontier="P07", rung="E-candidate",
                  role=role, status="GREEN" if run_valid else "RED",
                  frozen=FROZEN, config={k: v for k, v in cfg.items() if k != "seeds"}, **r)
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
        json.dump(result, open(os.path.join(args.out, "grown_slow_field_memory.json"), "w"),
                  indent=2, default=_np)
        print("wrote", os.path.join(args.out, "grown_slow_field_memory.json"))
    return 0 if run_valid else 1


if __name__ == "__main__":
    sys.exit(main())
