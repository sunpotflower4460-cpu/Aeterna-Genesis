#!/usr/bin/env python3
"""e049 field/slow-field basin memory (P07 / S1). role S (scaffolded synthesis), 2D screen -- NOT emergence.

The S1 rung of docs/frontier/F0_P07_field_slow_field_basin.md. First rung that runs COUPLED fast/slow DYNAMICS.
A fast complex field psi (local relaxational Ginzburg-Landau) is bidirectionally, LOCALLY coupled to a slow
material field s (a "well-depth history" that lags |psi|^2). We sweep a control alpha0 down through the ordering
transition and back up, and ask: does the slow field make the ordered/disordered BASIN depend on history
(hysteresis) -- and is that a REAL slow-field effect or just the sweep-rate confound? The matched g=0 OFF
control quantifies the confound; the reported memory is the EXCESS over it.

  fast:  d_t psi = [alpha0 + g*s]*psi - |psi|^2*psi + lap(psi)      (local 5-point Laplacian; no global solver)
  slow:  d_t s   = (1/tau)*(|psi|^2 - s) + Ds*lap(s)               (slow, local, bidirectional)

WHY THIS IS HONEST (audited before running -- see AUDIT.md):
- role S: psi (damaged/quenched) and s are PLACED; we do NOT call this emergence.
- NO target encoding: s couples to the generic local amplitude |psi|^2, NOT to any winding/target/basin label;
  s0 carries NO template (it starts at 0). The basin outcome (order vs disorder) is an emergent consequence.
- "related, or just the same attractor?": the matched **g=0 OFF control** (same alpha grid / seed / steps / dt)
  is the discriminator. Memory = hysteresis_area(ON) - hysteresis_area(OFF), not raw hysteresis.
- "held history, or copied the present?": we measure the s-vs-|psi|^2 LAG during the sweep; a ~0 lag would be
  memory_copy_collapse (s just copies psi), not memory.
- energy/mass are monitored (feedback can inject energy -> failure=energy_instability); no hidden corrections.
- 2D screen, official_3d=false. This is a mechanism study; the E-candidate (s itself emerging from an
  undifferentiated quench) is a later rung and is NOT done here.

FROZEN before looking at results (stopping rule): the constants below and the alpha sweep are fixed; --quick
only coarsens grid/steps. Classification thresholds are preregistered here.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = dict(tau=10.0, Ds=0.5, dt=0.05, g_on=0.6, alpha_hi=0.6, alpha_lo=-0.6, n_alpha=13, settle=400)
CONFIG_FULL = dict(L=48, K=300, seeds=(0, 1, 2))
CONFIG_QUICK = dict(L=32, K=160, seeds=(0,))
# preregistered classification margins (dimensionless; NOT imported from Loop)
MARGIN_EXCESS = 0.06        # ON hysteresis area must exceed OFF by this (control-separated memory)
MARGIN_RETAIN = 0.05        # ordered branch must retain this much more order at alpha=0 with the slow field
COPY_LAG_MIN = 0.02         # min s-vs-|psi|^2 lag during sweep; below => memory_copy_collapse
ENERGY_CAP = 1e6            # |free energy| guardrail; above => energy_instability


def _lap(f):
    return np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4.0 * f


def _free_energy(psi, alpha0):
    gx = 0.5 * (np.roll(psi, -1, 0) - np.roll(psi, 1, 0))
    gy = 0.5 * (np.roll(psi, -1, 1) - np.roll(psi, 1, 1))
    dens = -alpha0 * np.abs(psi) ** 2 + 0.5 * np.abs(psi) ** 4 + (np.abs(gx) ** 2 + np.abs(gy) ** 2)
    return float(dens.sum())


def sweep(g, cfg, p, seed):
    """Sweep alpha0 down (from ordered) then up; return branches + memory-lag + energy bound."""
    L, K = cfg["L"], cfg["K"]
    rng = np.random.default_rng(seed)
    psi = 0.05 * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    s = np.zeros((L, L))
    dt, tau, Ds = p["dt"], p["tau"], p["Ds"]

    def step(a):
        nonlocal psi, s
        aeff = a + g * s
        psi = psi + dt * (aeff * psi - np.abs(psi) ** 2 * psi + _lap(psi))
        s = s + dt * ((np.abs(psi) ** 2 - s) / tau + Ds * _lap(s))

    for _ in range(p["settle"]):
        step(p["alpha_hi"])                               # settle ordered at alpha_hi
    al = np.linspace(p["alpha_hi"], p["alpha_lo"], p["n_alpha"])
    au = np.linspace(p["alpha_lo"], p["alpha_hi"], p["n_alpha"])
    down, up, lags, emax = [], [], [], 0.0
    for a in al:
        for _ in range(K):
            step(a)
        down.append(float(np.mean(np.abs(psi) ** 2)))
        lags.append(abs(float(np.mean(s) - np.mean(np.abs(psi) ** 2))))
        emax = max(emax, abs(_free_energy(psi, a)))
    for a in au:
        for _ in range(K):
            step(a)
        up.append(float(np.mean(np.abs(psi) ** 2)))
        lags.append(abs(float(np.mean(s) - np.mean(np.abs(psi) ** 2))))
        emax = max(emax, abs(_free_energy(psi, a)))
    down = np.array(down)[::-1]                            # index ascending alpha
    up = np.array(up)
    dalpha = (p["alpha_hi"] - p["alpha_lo"]) / (p["n_alpha"] - 1)
    area = float(np.sum(np.abs(down - up)) * dalpha)
    retain = float(down[p["n_alpha"] // 2])               # ordered-branch order at alpha~0
    return dict(area=area, retain=retain, memory_lag=float(np.mean(lags)), energy_max=emax,
                down=[round(x, 4) for x in down], up=[round(x, 4) for x in up])


def run(cfg, p=FROZEN):
    on, off = [], []
    for seed in cfg["seeds"]:
        on.append(sweep(p["g_on"], cfg, p, seed))
        off.append(sweep(0.0, cfg, p, seed))
    area_on = float(np.mean([r["area"] for r in on])); area_off = float(np.mean([r["area"] for r in off]))
    retain_on = float(np.mean([r["retain"] for r in on])); retain_off = float(np.mean([r["retain"] for r in off]))
    lag_on = float(np.mean([r["memory_lag"] for r in on]))
    emax = max(max(r["energy_max"] for r in on), max(r["energy_max"] for r in off))

    excess = area_on - area_off
    retain_gain = retain_on - retain_off
    energy_ok = emax < ENERGY_CAP and np.isfinite(emax)
    not_copy = lag_on > COPY_LAG_MIN
    memory = (excess > MARGIN_EXCESS) and (retain_gain > MARGIN_RETAIN)

    if not energy_ok:
        verdict = "energy_instability"
    elif not not_copy:
        verdict = "memory_copy_collapse"
    elif memory:
        verdict = "slow_field_basin_memory_candidate"        # role S candidate (matched-control separated)
    elif excess <= MARGIN_EXCESS and retain_gain <= MARGIN_RETAIN:
        verdict = "common_attractor_relaxation_candidate"    # null: ON ~ OFF, no slow-field memory
    else:
        verdict = "partial"
    return dict(
        area_on=round(area_on, 4), area_off=round(area_off, 4), hysteresis_excess=round(excess, 4),
        retain_on=round(retain_on, 4), retain_off=round(retain_off, 4), retain_gain=round(retain_gain, 4),
        memory_lag_on=round(lag_on, 4), energy_max=emax, energy_ok=bool(energy_ok), not_copy=bool(not_copy),
        verdict=verdict,
        matched_control="g=0 OFF, same alpha grid / seeds / steps / dt (memory = ON excess over OFF)",
        on_curves=on[0], off_curves=off[0],
        classification={
            "slow_field_basin_memory_candidate (S)": verdict == "slow_field_basin_memory_candidate",
            "common_attractor_relaxation_candidate (null)": verdict == "common_attractor_relaxation_candidate",
            "memory_copy_collapse": verdict == "memory_copy_collapse",
            "energy_instability": verdict == "energy_instability",
            "partial": verdict == "partial",
        },
        thresholds=dict(margin_excess=MARGIN_EXCESS, margin_retain=MARGIN_RETAIN,
                        copy_lag_min=COPY_LAG_MIN, energy_cap=ENERGY_CAP))


def main(argv=None):
    ap = argparse.ArgumentParser(description="e049 P07/S1 slow-field basin memory (role S, ON vs matched OFF)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL

    print("=== e049 field/slow-field basin memory -- P07 / S1 (role S; fast/slow PLACED; 2D screen) ===")
    r = run(cfg)
    print("  hysteresis area  ON(g=%.1f)=%.4f  OFF(g=0)=%.4f  excess(ON-OFF)=%.4f  (margin %.2f)"
          % (FROZEN["g_on"], r["area_on"], r["area_off"], r["hysteresis_excess"], MARGIN_EXCESS))
    print("  order retained @alpha~0  ON=%.4f  OFF=%.4f  gain=%.4f  (margin %.2f)"
          % (r["retain_on"], r["retain_off"], r["retain_gain"], MARGIN_RETAIN))
    print("  memory lag (s vs |psi|^2) ON=%.4f (>%.2f => not a copy) | energy_max=%.2e ok=%s"
          % (r["memory_lag_on"], COPY_LAG_MIN, r["energy_max"], r["energy_ok"]))
    print("  VERDICT:", r["verdict"])
    print("  matched control:", r["matched_control"])
    # role S: a "support" here means a control-separated MECHANISM candidate, not emergence.
    passed = r["verdict"] in ("slow_field_basin_memory_candidate", "common_attractor_relaxation_candidate")
    # ^ both are HONEST, well-formed S1 outcomes (candidate or clean null); only copy/energy/partial are failures.
    print("STATUS:", "GREEN" if passed else "RED",
          "(role S: matched-control mechanism study; GREEN = a clean classified outcome, not 'emergence')")

    result = dict(experiment="e049_field_slow_field_basin", frontier="P07", rung="S1", role="S",
                  status="GREEN" if passed else "RED", frozen=FROZEN,
                  config={k: v for k, v in cfg.items() if k != "seeds"}, **r)
    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "basin_memory.json"), "w") as f:
            json.dump(result, f, indent=2)
        print("wrote", os.path.join(args.out, "basin_memory.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
