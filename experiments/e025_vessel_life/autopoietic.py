#!/usr/bin/env python3
"""e025 Stage 2 -- close the loop: the core reads its own winding and gates the motor.

MODULE:   e025_vessel_life (Stage 2: autopoietic)
QUESTION: if the field gain is gated by the field's OWN winding (the core reads itself), does losing
          the winding (an anti-vortex) then DRAG the bulk down -- i.e. does closing the loop couple the
          two collapse modes that were independent in Stage 1?
PUT IN:   the Stage-1 field + motor, plus a gate = sigmoid(|winding| - 0.5) that multiplies the gain
          ONLY when closure=True. NO "losing the winding stops self-maintenance" is put in -- it is measured.
EMERGED:  (measured) the DECISIVE CONTRAST: after an anti-vortex, WITHOUT closure the bulk stays ~1.97
          (body lives on) but WITH closure the bulk collapses to ~0.03 (winding loss drags the bulk down).
          Fuel cut still collapses the bulk; body excision (core intact) still regrows.
CLAIM TIER: measured(the closed-vs-open bulk contrast) ; interpretive(operational closure makes the self
          and its self-maintenance inseparable -- Maturana-Varela autopoiesis) ; analogy(true self vs a
          powered mechanism -- KNOWN MATCH only, never a gate name).
KNOWN MATCH: Maturana-Varela autopoiesis (operational closure); topological charge; CGL driven droplet.
STATUS:   GREEN (four gates; keys are physical: bulk amplitude and winding, plus the closure contrast).
A_OR_B:   (A) faithful. Hand input = the field + motor + a self-reading gate; whether closure couples
          winding-loss to bulk-collapse is emergent and measured.

THE TRAP (designer hit it, we avoid it): the gate is a SMOOTHED read of the field's own winding
(gate <- 0.92 gate + 0.08 sigmoid(8(|w|-0.5))); the winding is read on a CCW loop (core.holonomy).
Gate the physical GAIN, not a variable named "life". The decisive key is a physical contrast:
winding_loss_collapses_bulk_iff_closed.

Floors: a coarse-grained 2D CGL toy; the gate shape and thresholds are modelling choices. The gated
fact is the CONTRAST (closed -> bulk collapses on winding loss; open -> bulk survives), not the
absolute levels. "True self / autopoiesis" is analogy -- no living self is created.
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
           "dmu": 5.0, "fuel_cut": 55.0, "event_t": 35.0, "seed": 0}
QUICK = {"T": 84.0, "Nr": 300, "fuel_cut": 40.0, "event_t": 26.0}


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


def _chunk(X, Y):
    return (X > 14) & (X < 40) & (np.abs(Y) < 20)


def run(p, rng, fuel_cut=None, anti=False, excise=None, closure=False):
    N, Rdrop = p["N"], p["Rdrop"]
    X, Y, r, K2 = _grid(N)
    psi = _mk([(0, 0, 1)], X, Y, r, Rdrop, N)
    phi = rng.random(p["Nr"]) * 2 * np.pi
    P, om, gate = 0.0, 0.0, 1.0
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
        w = abs(_wind(psi, N))                                    # the core READS ITS OWN winding
        gt = 1.0 / (1.0 + np.exp(-8 * (w - 0.5)))
        gate = 0.92 * gate + 0.08 * gt                           # smoothed self-presence gate
        g_eff = (2.2 * P / (P + 0.4)) * (gate if closure else 1.0)
        if excise is not None and abs(tt - et) < dt / 2:
            psi = psi * (~excise(X, Y))
        if anti and abs(tt - et) < dt / 2:
            psi = psi * np.exp(-1j * np.arctan2(Y, X - 6)) * np.tanh(np.hypot(X - 6, Y) / 2.0)
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        psi = psi * np.exp(dt * (g_eff * (r < Rdrop) - np.abs(psi) ** 2)) * conf
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        if i % max(1, nsteps // 30) == 0:
            hist.append((round(tt, 1), round(_bulk(psi, r, Rdrop), 3),
                         round(_wind(psi, N), 2), round(gate, 2)))
    return _bulk(psi, r, Rdrop), _wind(psi, N), hist


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])
    # the decisive contrast: anti-vortex with vs without closure
    b_open, w_open, _ = run(p, rng, anti=True, closure=False)
    b_closed, w_closed, H_closed = run(p, rng, anti=True, closure=True)
    # other closed-loop scenarios
    b_live, w_live, H_live = run(p, rng, closure=True)
    b_fuel, w_fuel, _ = run(p, rng, fuel_cut=p["fuel_cut"], closure=True)
    b_body, w_body, _ = run(p, rng, excise=_chunk, closure=True)
    return {
        "params": p,
        "anti_open": {"bulk": round(b_open, 3), "winding": round(w_open, 2)},
        "anti_closed": {"bulk": round(b_closed, 3), "winding": round(w_closed, 2)},
        "living_closed": {"bulk": round(b_live, 3), "winding": round(w_live, 2),
                          "gate": round(H_live[-1][3], 2)},
        "fuel_cut_closed": {"bulk": round(b_fuel, 3), "winding": round(w_fuel, 2)},
        "body_excise_closed": {"bulk": round(b_body, 3), "winding": round(w_body, 2)},
        "anti_closed_traj": H_closed,
    }


def evaluate(result, quick=False):
    L = result["living_closed"]
    F = result["fuel_cut_closed"]
    B = result["body_excise_closed"]
    O = result["anti_open"]
    C = result["anti_closed"]
    checks = {
        "bulk_and_winding_sustained_closed (bulk>0.5, |w|>0.5)":
            bool(L["bulk"] > 0.5 and abs(L["winding"]) > 0.5),
        "bulk_collapses_on_fuel_cut (bulk<0.2)":
            bool(F["bulk"] < 0.2),
        "winding_survives_excision_closed (|w|>0.5, bulk>0.5)":
            bool(abs(B["winding"]) > 0.5 and B["bulk"] > 0.5),
        # the loop: winding loss (anti) collapses the bulk ONLY under closure
        "winding_loss_collapses_bulk_iff_closed (open bulk>0.5, closed bulk<0.2)":
            bool(O["bulk"] > 0.5 and C["bulk"] < 0.2),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e025 vessel life Stage 2 (autopoietic)", "tier": "measured",
        "put_in": "Stage-1 field + motor + a gate = sigmoid(|winding|-0.5) multiplying the gain when closure=True",
        "emerged": ["decisive contrast after an anti-vortex: open bulk=%s (survives) vs closed bulk=%s (collapses)"
                    % (result["anti_open"]["bulk"], result["anti_closed"]["bulk"]),
                    "closed living: bulk=%s winding=%s gate=%s; fuel-cut bulk=%s; body-excise bulk=%s winding=%s"
                    % (result["living_closed"]["bulk"], result["living_closed"]["winding"],
                       result["living_closed"]["gate"], result["fuel_cut_closed"]["bulk"],
                       result["body_excise_closed"]["bulk"], result["body_excise_closed"]["winding"])],
        "surprises": ["closing the loop makes winding-loss DRAG the bulk down; without the loop the body lives "
                      "on without its winding -- the two collapse modes become coupled only under closure"],
        "persistence": "closed loop holds bulk ~1.9 / winding +1 / gate ~1 while fueled and self-present",
        "measured_numbers": {"anti_open": result["anti_open"], "anti_closed": result["anti_closed"],
                             "living_closed": result["living_closed"], "fuel_cut_closed": result["fuel_cut_closed"],
                             "body_excise_closed": result["body_excise_closed"]},
        "not_scripted_check": "the gate reads the field's OWN winding on a CCW loop; the coupling of winding "
                              "loss to bulk collapse is measured, not scripted",
        "claim_tier": "measured (closed-vs-open bulk contrast) ; interpretive (operational closure = self and "
                      "self-maintenance inseparable) ; analogy (true self vs powered mechanism, KNOWN MATCH only)",
        "floors": ["2D CGL toy; the gate shape and thresholds are modelling choices",
                   "the gated fact is the CONTRAST (closed collapses on winding loss; open survives), not levels",
                   "'true self / autopoiesis' is analogy -- no living self is created"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e025 Stage 2: autopoietic closure")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e025 Stage 2 -- autopoietic closure: the self-reading loop ===")
    print("  DECISIVE CONTRAST (anti-vortex): open bulk=%.2f (survives)  closed bulk=%.2f (collapses)"
          % (r["anti_open"]["bulk"], r["anti_closed"]["bulk"]))
    print("  closed living: bulk=%.2f winding=%+.2f gate=%.2f"
          % (r["living_closed"]["bulk"], r["living_closed"]["winding"], r["living_closed"]["gate"]))
    print("  closed fuel-cut: bulk=%.2f   closed body-excise: bulk=%.2f winding=%+.2f"
          % (r["fuel_cut_closed"]["bulk"], r["body_excise_closed"]["bulk"], r["body_excise_closed"]["winding"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (closure couples winding-loss to bulk-collapse)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "autopoietic.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/autopoietic.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
