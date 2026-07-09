#!/usr/bin/env python3
"""e025 Stage 1 -- the complete vessel: three organs in ONE field, and two distinct collapses.

MODULE:   e025_vessel_life (Stage 1: complete)
QUESTION: can a topological core (a +1 vortex), a three-fold rotary motor, and a driven-dissipative
          droplet coexist in one 2D field, and are there TWO independent ways the vessel collapses?
PUT IN:   a 2D CGL-type field with a +1 core; a ratchet motor rectifying a fuel gradient into a
          product P that powers the field gain; a finite driven droplet. NO "the motor powers the
          winding" and NO "two distinct deaths" are put in -- both are measured.
EMERGED:  (measured) fueled: bulk |psi|^2 ~1.96 with winding +1; cut the fuel and the bulk collapses
          to ~0.01 (winding held until collapse); excise a body chunk and the winding + bulk regrow;
          inject an anti-vortex and the winding -> 0 while the bulk stays ~1.97.
CLAIM TIER: measured(bulk & winding levels under each intervention) ; interpretive(metabolism powers
          and is distinct from identity; two independent collapse modes) ; analogy(a "living vessel",
          "metabolic death" vs "identity death" -- KNOWN MATCH only, never a gate name).
KNOWN MATCH: complex Ginzburg-Landau driven droplets; topological charge conservation; ATP-synthase-like
          rotary metabolism (analogy).
STATUS:   GREEN (four gates; gate names are physical quantities only: bulk amplitude and winding).
A_OR_B:   (A) faithful. Hand input = field + motor + coupling + the interventions; the bulk/winding
          responses (and that the two collapse modes are independent) are emergent and measured.

THE TRAP (designer hit it, we avoid it): the motor product uses the SMOOTHED net rotation
max(om - 0.05, 0) (as in e024) so a fuel cut truly stops the drive and the bulk dies; the winding
is READ on a CCW loop that encloses only the single core (core.holonomy). Do NOT name a gate
"self / life / death / identity" -- those belong in the docstring / AUDIT as analogy. The GREEN
keys are bulk_and_winding_sustained, bulk_collapses_on_fuel_cut, winding_survives_body_excision,
winding_lost_while_bulk_high.

Floors: a coarse-grained 2D CGL toy on a fixed periodic lattice; the absolute bulk level (~1.9) and
the collapse thresholds depend on (gain, dissipation, dt, drop radius). The gated facts are the
SIGN/level contrasts (sustained > 0.5 vs collapsed < 0.2; winding ~ +/-1 vs ~ 0). "Living vessel /
two deaths" is analogy -- no biological cell, metabolism, or death is created.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import ring_winding  # noqa: E402

DEFAULT = {"N": 128, "T": 120.0, "dt": 0.02, "Nr": 500, "Rdrop": 44.0, "Rread": 11,
           "dmu": 5.0, "fuel_cut": 60.0, "event_t": 35.0, "seed": 0}
QUICK = {"T": 84.0, "Nr": 300, "fuel_cut": 42.0, "event_t": 26.0}


def _grid(N):
    x = np.arange(N) - N / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    r = np.hypot(X, Y)
    kx = 2 * np.pi * np.fft.fftfreq(N)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    return X, Y, r, KX ** 2 + KY ** 2


def _Vp(phi):
    return 3 * np.sin(3 * phi) + 3 * 0.6 * np.sin(6 * phi)


def _bulk(psi, r, Rdrop):
    return float(np.mean((np.abs(psi) ** 2)[r < Rdrop - 10]))


def _mk(cores, X, Y, r, Rdrop, N):
    ph = np.zeros((N, N))
    amp = np.ones((N, N))
    for (a, b, c) in cores:
        ph += c * np.arctan2(Y - b, X - a)
        amp *= np.tanh(np.hypot(X - a, Y - b) / 2.0)
    env = 0.5 * (1 - np.tanh((r - Rdrop) / 3.0))
    return (amp * env * np.exp(1j * ph)).astype(complex)


def _wind(psi, N):
    return ring_winding(psi, N / 2, N / 2, DEFAULT["Rread"], n=400)


def run(p, rng, fuel_cut=None, excise=None, anti=False):
    N, Rdrop = p["N"], p["Rdrop"]
    X, Y, r, K2 = _grid(N)
    psi = _mk([(0, 0, 1)], X, Y, r, Rdrop, N)
    phi = rng.random(p["Nr"]) * 2 * np.pi
    P, om = 0.0, 0.0
    expK = np.exp(-0.5 * K2 * p["dt"])
    conf = (r < Rdrop + 8)
    dt = p["dt"]
    nsteps = int(p["T"] / dt)
    et = p["event_t"]
    hist = []
    for i in range(nsteps):
        tt = i * dt
        mu = p["dmu"] if (fuel_cut is None or tt < fuel_cut) else 0.0
        for _ in range(5):
            dm = dt / 5
            dphi = dm * (-_Vp(phi) + mu) + np.sqrt(2 * 0.2 * dm) * rng.standard_normal(p["Nr"])
            phi += dphi
            om = 0.98 * om + 0.02 * (np.mean(dphi) / dm)
        P = P + dt * (0.6 * max(om - 0.05, 0.0) - 0.6 * P)
        gain = 2.2 * P / (P + 0.4)                                # gain POWERED by the motor product
        if excise is not None and abs(tt - et) < dt / 2:
            psi = psi * (~excise(X, Y))
        if anti and abs(tt - et) < dt / 2:
            psi = psi * np.exp(-1j * np.arctan2(Y, X - 6)) * np.tanh(np.hypot(X - 6, Y) / 2.0)
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        psi = psi * np.exp(dt * (gain * (r < Rdrop) - np.abs(psi) ** 2)) * conf
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        if i % max(1, nsteps // 30) == 0:
            hist.append((round(tt, 1), round(_bulk(psi, r, Rdrop), 3), round(_wind(psi, N), 2)))
    return _bulk(psi, r, Rdrop), _wind(psi, N), hist


def _chunk(X, Y):
    return (X > 14) & (X < 40) & (np.abs(Y) < 20)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])
    b_live, w_live, H_live = run(p, rng)
    b_fuel, w_fuel, H_fuel = run(p, rng, fuel_cut=p["fuel_cut"])
    b_body, w_body, H_body = run(p, rng, excise=_chunk)
    b_anti, w_anti, H_anti = run(p, rng, anti=True)
    return {
        "params": p,
        "living": {"bulk": round(b_live, 3), "winding": round(w_live, 2)},
        "fuel_cut": {"bulk": round(b_fuel, 3), "winding": round(w_fuel, 2)},
        "body_excise": {"bulk": round(b_body, 3), "winding": round(w_body, 2)},
        "anti": {"bulk": round(b_anti, 3), "winding": round(w_anti, 2)},
        "fuel_cut_traj": H_fuel, "anti_traj": H_anti,
    }


def evaluate(result, quick=False):
    L, F, B, A = (result["living"], result["fuel_cut"],
                  result["body_excise"], result["anti"])
    checks = {
        # living: metabolism sustains both bulk and the winding (identity core)
        "bulk_and_winding_sustained (bulk>0.5, |w|>0.5)":
            bool(L["bulk"] > 0.5 and abs(L["winding"]) > 0.5),
        # metabolic collapse: cut the fuel and the whole bulk collapses
        "bulk_collapses_on_fuel_cut (bulk<0.2)":
            bool(F["bulk"] < 0.2),
        # winding (identity) survives excision of a body chunk, bulk regrows
        "winding_survives_body_excision (|w|>0.5, bulk>0.5)":
            bool(abs(B["winding"]) > 0.5 and B["bulk"] > 0.5),
        # the OTHER collapse: an anti-vortex takes the winding to 0 while the bulk stays high
        "winding_lost_while_bulk_high (|w|<0.5, bulk>0.5)":
            bool(abs(A["winding"]) < 0.5 and A["bulk"] > 0.5),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e025 vessel life Stage 1 (complete)", "tier": "measured",
        "put_in": "2D CGL field + a +1 core + a ratchet motor powering the gain + a finite droplet + interventions",
        "emerged": ["fueled: bulk=%s winding=%s; fuel-cut: bulk=%s (collapse); body-excise: bulk=%s winding=%s "
                    "(regrows); anti-vortex: bulk=%s winding=%s (winding lost, bulk high)"
                    % (result["living"]["bulk"], result["living"]["winding"], result["fuel_cut"]["bulk"],
                       result["body_excise"]["bulk"], result["body_excise"]["winding"],
                       result["anti"]["bulk"], result["anti"]["winding"])],
        "surprises": ["TWO independent collapse modes: fuel cut collapses the bulk (winding held until the end); "
                      "an anti-vortex zeroes the winding while the bulk stays high -- metabolism != identity"],
        "persistence": "fueled bulk holds ~1.9 with winding +1; each intervention flips exactly one quantity",
        "measured_numbers": {"living": result["living"], "fuel_cut": result["fuel_cut"],
                             "body_excise": result["body_excise"], "anti": result["anti"]},
        "not_scripted_check": "winding read on a CCW loop around the single core; the motor product uses the "
                              "smoothed net rotation; no collapse mode is scripted",
        "claim_tier": "measured (bulk & winding levels) ; interpretive (two distinct collapses; metabolism != "
                      "identity) ; analogy (living vessel / metabolic death / identity death -- KNOWN MATCH only)",
        "floors": ["2D CGL toy on a fixed periodic lattice; absolute bulk (~1.9) and thresholds depend on "
                   "(gain, dissipation, dt, Rdrop)",
                   "the gated facts are the level contrasts (>0.5 vs <0.2; |w|~1 vs ~0), not absolute values",
                   "'living vessel / two deaths' is analogy -- no cell, metabolism, or death is created"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e025 Stage 1: the complete vessel")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e025 Stage 1 -- complete vessel: three organs, two collapse modes ===")
    print("  %-26s %10s %10s" % ("scenario", "bulk", "winding"))
    for name, key in [("fueled (living)", "living"), ("fuel cut (bulk collapse)", "fuel_cut"),
                      ("body excise", "body_excise"), ("anti-vortex (winding->0)", "anti")]:
        print("  %-26s %10.2f %+10.2f" % (name, r[key]["bulk"], r[key]["winding"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (bulk & winding measured; metabolism != identity)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "complete.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/complete.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
