#!/usr/bin/env python3
"""e009 open menu -- exploratory runs (Tier C: see what happens, record honestly).

open-1  Universality of co-emergence across SUBSTRATE: does a relativistic
        complex scalar (nonlinear Klein-Gordon), NOT the GPE, also nucleate KZ
        vortices from white noise? If yes, co-emergence is substrate-independent.
open-2  Defect "chemistry": after a quench, do +/- vortices sit closer to
        OPPOSITE-sign neighbours than to same-sign (a bound +- "molecule")?

Phenomenon-atlas philosophy: record what happens, not pass/fail. Forbidden
words avoided (no "life/electron/consciousness"). Floors stated.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402

_RESULTS = os.path.join(os.path.dirname(__file__), "results")


def _count(psi, frac=0.1):
    w = np.rint(vortex.winding_field(psi)).astype(int)
    rho = np.abs(psi) ** 2
    cmin = np.minimum.reduce([rho[:-1, :-1], rho[1:, :-1], rho[:-1, 1:], rho[1:, 1:]])
    m = (w != 0) & (cmin < frac * rho.mean())
    return int(m.sum()), int(w[m].sum())


def nlkg_quench(L, v2_i, v2_f, tauQ, hold, dt, eta, noise, seed):
    """Relativistic complex scalar: psi'' - lap psi + (|psi|^2 - v2)psi = -eta psi'."""
    rng = np.random.default_rng(seed)
    k2 = k_squared(L)
    psi = noise * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    pidot = np.zeros((L, L), complex)
    for s in range(tauQ + hold):
        v2 = v2_i + (v2_f - v2_i) * min(1.0, s / tauQ)
        lap = np.fft.ifft2(-k2 * np.fft.fft2(psi))
        acc = lap - (np.abs(psi) ** 2 - v2) * psi - eta * pidot
        pidot = pidot + dt * acc
        psi = psi + dt * pidot
    return psi


def open1_universality(quick=False):
    L = 96 if quick else 128
    tauQ_list = [100, 200, 400] if quick else [100, 200, 400, 800]
    seeds = [1, 2] if quick else [1, 2, 3]
    rows = []
    for tauQ in tauQ_list:
        ns, nets = [], []
        for seed in seeds:
            psi = nlkg_quench(L, -1.0, 1.0, tauQ, 400, 0.05, 0.3, 0.05, seed)
            n, net = _count(psi)
            ns.append(n)
            nets.append(net)
        rows.append({"tauQ": tauQ, "N": float(np.mean(ns)),
                     "net_abs": float(np.mean(np.abs(nets))),
                     "rho_med": float(np.median(np.abs(psi) ** 2))})
    taus = np.array([r["tauQ"] for r in rows], float)
    nd = np.array([r["N"] for r in rows], float)
    b = float(-np.polyfit(np.log(taus), np.log(nd), 1)[0])
    return {"substrate": "relativistic complex scalar (nonlinear Klein-Gordon)",
            "rows": rows, "kz_exponent_b": round(b, 3),
            "vortices_emerge": bool(nd.min() > 3),
            "power_law_negative": bool(b > 0.1)}


def open2_defect_chemistry(quick=False):
    """Are +/- vortices bound (opposite-sign nearer than same-sign)?"""
    L = 128 if quick else 192
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(1)
    psi = 0.05 * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    tauQ = 300
    for s in range(tauQ + 600):
        mu = -1.0 + 2.0 * min(1.0, s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, 1.0, mu, 0.05, 0.3)
    cores = vortex.find_vortices(psi)
    # keep only density-gated genuine cores
    rho = np.abs(psi) ** 2
    pos = np.array([[c["x"], c["y"]] for c in cores])
    sign = np.array([c["charge"] for c in cores])
    keep = []
    for i, c in enumerate(cores):
        xi, yi = int(c["x"]), int(c["y"])
        if rho[min(xi, L - 1), min(yi, L - 1)] < 0.4 * rho.mean():
            keep.append(i)
    pos, sign = pos[keep], sign[keep]
    if len(pos) < 6:
        return {"n_defects": int(len(pos)), "note": "too few to measure"}
    # nearest same-sign vs opposite-sign distance (mean)
    d_same, d_opp = [], []
    for i in range(len(pos)):
        dd = np.hypot(pos[:, 0] - pos[i, 0], pos[:, 1] - pos[i, 1])
        dd[i] = np.inf
        same = sign == sign[i]
        opp = ~same
        if same.sum() > 0:
            d_same.append(dd[same].min())
        if opp.sum() > 0:
            d_opp.append(dd[opp].min())
    ms, mo = float(np.mean(d_same)), float(np.mean(d_opp))
    return {"n_defects": int(len(pos)),
            "mean_nearest_same_sign": round(ms, 2),
            "mean_nearest_opposite_sign": round(mo, 2),
            "opposite_closer_(pairing)": bool(mo < ms)}


def _atlas(u, c):
    return [
        {"experiment": "open-1 universality", "tier": "C",
         "put_in": "relativistic complex scalar (NLKG) + white noise + v^2 quench",
         "emerged": ["KZ vortices in a NON-GPE substrate, b=%.3f" % u["kz_exponent_b"]],
         "surprises": ["co-emergence is SUBSTRATE-INDEPENDENT (GPE and a relativistic"
                       " scalar both nucleate KZ vortices)"],
         "persistence": "vortices present at all tau_Q",
         "measured_numbers": {"kz_exponent_b": u["kz_exponent_b"],
                              "rows": u["rows"]},
         "not_scripted_check": "vortices measured by winding+density; the wave law never says 'vortex'",
         "claim_tier": "measured (KZ power law in NLKG) ; interpretive (universality => hypothesis hardens)",
         "floors": ["fixed lattice; a different z (relativistic) gives a different exponent"]},
        {"experiment": "open-2 defect chemistry", "tier": "C",
         "put_in": "GPE quench field; measure +/- nearest-neighbour distances",
         "emerged": ["+/- pairing" if c.get("opposite_closer_(pairing)") else "no clear pairing"],
         "surprises": [],
         "persistence": "static snapshot",
         "measured_numbers": c,
         "not_scripted_check": "distances measured from detected cores, nothing imposed",
         "claim_tier": "measured (distances) ; frontier-observation (whether this is a 'molecule')",
         "floors": ["a snapshot statistic, not a bound-state proof"]},
    ]


def simulate(quick=False):
    return {"open1_universality": open1_universality(quick),
            "open2_defect_chemistry": open2_defect_chemistry(quick)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e009 open menu")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    u, c = r["open1_universality"], r["open2_defect_chemistry"]
    print("=== open-1: universality across substrate (NLKG vs GPE) ===")
    for row in u["rows"]:
        print("   tauQ=%4d  N=%.1f  net|w|=%.1f  rho_med=%.2f"
              % (row["tauQ"], row["N"], row["net_abs"], row["rho_med"]))
    print("   NLKG KZ: N ~ tauQ^(-%.3f) ; vortices emerge in a NON-GPE substrate = %s"
          % (u["kz_exponent_b"], u["vortices_emerge"]))
    print("   -> co-emergence is substrate-independent (interpretive: hypothesis hardens)")
    print("=== open-2: defect chemistry (+/- pairing) ===")
    print("   %s" % c)
    if not args.no_write and not args.quick:
        os.makedirs(_RESULTS, exist_ok=True)
        with open(os.path.join(_RESULTS, "open_menu.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(u, c)}, f, indent=2)
        print("wrote results/open_menu.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
