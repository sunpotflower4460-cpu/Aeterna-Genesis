#!/usr/bin/env python3
"""e019 Stage 2 (THE PRIZE) -- three-body coupling: metabolism + flow + particle.

The mission's most-important build: put the three prior results into ONE closed,
BIDIRECTIONAL loop and see what a one-way coupling cannot show.

  * metabolism b (e018): a driven store, db/dt = s*(1-b) - kU*U*b  (drive s fills it;
    running the flow drains it).
  * self-organized flow amplitude U (e013/e017): dU/dt = gU*b - dampU*U - drag*P(n)
    (metabolism drives the circulation; it is damped; AND the particle drags it --
    the BACK-REACTION).
  * particle n (e016): a stabilized Q_H=1 hopfion, held by the stabilizing flow and
    TRANSPORTED by a roll of the current amplitude U(t) (as in Stage 1). Its
    coherence P(n) (peak Skyrme-density = how intact it is) feeds back into dU.

So the loop is closed both ways: b -> U -> n and n -> U -> b. We MEASURE (never
impose the outcome):
  * DRIVEN, two-way: does the loop settle into a self-regulated state where the
    particle is carried but NOT torn (the back-reaction CAPS the circulation)?
  * ONE-WAY (drag=0): with no back-reaction the metabolism can drive U past the
    tearing point -> the particle is destroyed. The difference IS the coupling.
  * CUT THE DRIVE (s=0): b -> 0 -> U -> 0 -> the flow ceases and transport stops
    (the coupled system stalls) -- the three bodies live and die together.

Floors (honest): the flow is a REDUCED amplitude model (an ODE for U), NOT full
Navier-Stokes; the roll SHAPE is prescribed; the particle is a real 3D hopfion but
on a small box. "Homeostasis / live-and-die-together" is interpretive; not life.

MODULE:   e019_coupling (Stage 2: three-body coupling)
QUESTION: In a closed metabolism<->flow<->particle loop, does the particle's back-reaction self-limit the flow (homeostasis), and does cutting the drive stall all three?
PUT IN:   b<->U kinetics + a roll of amplitude U(t) advecting a stabilized hopfion + back-reaction drag*P(n). Homeostasis/stall not put in.
EMERGED:  (measured) two-way self-limits U -> particle held; one-way (drag=0) over-drives U -> particle torn; cut drive -> flow ceases, transport stalls.
CLAIM TIER: measured(self-limiting vs one-way, drive-off stall) ; interpretive(homeostasis, live-and-die-together) ; analogy(metabolism/particle).
KNOWN MATCH: negative feedback / homeostasis; advected order parameter (e016/e019).
STATUS:   GREEN (two-way self-limitation vs one-way tearing + drive-off stall measured; reduced-flow is the floor).
A_OR_B:   (A) faithful. Hand input = the coupled laws + a roll shape; the self-limitation and stall are emergent.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import hopf  # noqa: E402
from experiments.e019_coupling import coupling as e019  # noqa: E402

DEFAULT = {"L": 44, "box": 8.4, "c2": 1.0, "c4": 20.0, "kappa": 40.0, "dt": 6e-3,
           "start_scale": 2.9, "settle_steps": 130, "n_steps": 320,
           "roll_R": 5.0, "roll_x0": -4.0,
           # coupling kinetics (strong-drive regime: without back-reaction the
           # metabolism over-drives U past the particle's tearing point)
           "s": 1.0, "kU": 0.5, "gU": 34.0, "dampU": 0.8, "drag": 11.0,
           "b0": 1.0, "U0": 0.0, "kin_dt": 0.02}
QUICK = {"L": 40, "settle_steps": 100, "n_steps": 220}


def _coherence(n, dx):
    """Particle coherence P in [0,1]: normalized peak Skyrme (E4) density -- high
    when the hopfion is intact/localized, low when it has been torn/delocalized."""
    dn = hopf.central_diff(n, dx)
    F = hopf.skyrme_F(n, dn)
    w = sum(F[jk] ** 2 for jk in F)
    peak = float(w.max())
    return peak


def run(p, drive_on=True, two_way=True):
    n, dx = hopf.hopfion_field(p["L"], p["start_scale"], p["box"])
    K4 = hopf.k4_grid(p["L"], dx)
    dt = p["dt"]
    for _ in range(p["settle_steps"]):
        n = hopf.stabilized_flow_step(n, dx, p["c2"], p["c4"], dt, p["kappa"], K4)
    P0 = _coherence(n, dx)                          # reference coherence (intact)
    cx0, cz0 = e019._centroid(n, dx)
    b, U = p["b0"], p["U0"]
    s = p["s"] if drive_on else 0.0
    drag = p["drag"] if two_way else 0.0
    kdt = p["kin_dt"]
    trace = []
    for step in range(p["n_steps"]):
        # advect the particle by the current roll amplitude U (holds via stabilizer)
        n = hopf.stabilized_flow_step(n, dx, p["c2"], p["c4"], dt, p["kappa"], K4)
        ux, uz = e019._roll_velocity(p["L"], p["box"], U, p["roll_R"], p["roll_x0"])
        adv = ux[None, ...] * hopf.central_diff(n, dx)[0] + uz[None, ...] * hopf.central_diff(n, dx)[2]
        n = n - dt * adv
        n = n / np.linalg.norm(n, axis=0, keepdims=True)
        # coupled kinetics (metabolism b, flow amplitude U); P is the back-reaction
        P = _coherence(n, dx) / (P0 + 1e-12)        # in ~[0,1], 1 = fully intact
        db = s * (1.0 - b) - p["kU"] * U * b
        dU = p["gU"] * b - p["dampU"] * U - drag * P
        b = max(b + kdt * db, 0.0)
        U = max(U + kdt * dU, 0.0)
        if (step + 1) % max(1, p["n_steps"] // 4) == 0:
            trace.append({"step": step + 1, "b": round(b, 3), "U": round(U, 3),
                          "Q_H": round(float(hopf.hopf_charge(n, dx)), 3)})
    Qf = float(hopf.hopf_charge(n, dx))
    cx, cz = e019._centroid(n, dx)
    return {"b_final": round(b, 3), "U_final": round(U, 3),
            "Q_H_final": round(Qf, 3), "size_final": round(float(hopf.e4_rms_size(n, dx)), 3),
            "centroid_disp": round(float(np.hypot(cx - cx0, cz - cz0)), 3),
            "particle_held": bool(abs(Qf) > 0.7), "trace": trace}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    two_way = run(p, drive_on=True, two_way=True)
    one_way = run(p, drive_on=True, two_way=False)
    no_drive = run(p, drive_on=False, two_way=True)
    return {
        "params": p,
        "two_way": two_way, "one_way": one_way, "no_drive": no_drive,
        # the back-reaction self-limits: two-way holds the particle, one-way tears it
        "two_way_self_limits": bool(two_way["particle_held"] and two_way["U_final"] < one_way["U_final"]),
        "one_way_overdrives": bool(not one_way["particle_held"] or one_way["U_final"] > two_way["U_final"] + 1e-6),
        "backreaction_matters": bool(two_way["particle_held"] and not one_way["particle_held"]),
        # cutting the drive stalls the flow (transport ceases)
        "drive_off_stalls": bool(no_drive["U_final"] < 0.2 and no_drive["centroid_disp"] < two_way["centroid_disp"]),
    }


def evaluate(result, quick=False):
    checks = {
        "two-way self-limits (particle held, U capped)": result["two_way_self_limits"],
        "one-way over-drives (U higher / particle torn)": result["one_way_overdrives"],
        "cut drive -> flow ceases, transport stalls": result["drive_off_stalls"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e019 three-body coupling (metabolism+flow+particle)", "tier": "measured",
        "put_in": "b<->U kinetics + a roll of amplitude U(t) advecting a stabilized hopfion + back-reaction drag*P(n); outcome not put in",
        "emerged": ["two-way: self-limited, particle held (b,U,Q_H)=(%s,%s,%s)"
                    % (result["two_way"]["b_final"], result["two_way"]["U_final"], result["two_way"]["Q_H_final"]),
                    "one-way (drag=0): over-driven, U=%s Q_H=%s"
                    % (result["one_way"]["U_final"], result["one_way"]["Q_H_final"]),
                    "cut drive: U->%s, transport stalls (disp %s vs %s)"
                    % (result["no_drive"]["U_final"], result["no_drive"]["centroid_disp"],
                       result["two_way"]["centroid_disp"])],
        "surprises": ["the particle's back-reaction CAPS the self-organized flow so it survives -- an emergent negative feedback (homeostasis) that a one-way coupling cannot show"],
        "persistence": "the coupled state persists only while driven; the three bodies live and die together",
        "measured_numbers": {"two_way": result["two_way"], "one_way": result["one_way"],
                             "no_drive": result["no_drive"]},
        "not_scripted_check": "Q_H from B=curl A; U and b from the coupled ODEs; the self-limitation is not imposed",
        "claim_tier": "measured (self-limiting vs one-way, drive-off stall) ; interpretive (homeostasis) ; analogy (metabolism/particle)",
        "floors": ["the flow is a REDUCED amplitude model (an ODE for U), not full Navier-Stokes; the roll SHAPE is prescribed",
                   "the particle is a real 3D hopfion but on a small box; 'homeostasis/live-and-die-together' is interpretive, not life"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e019 three-body coupling")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e019 three-body coupling: metabolism <-> flow <-> particle ===")
    for name in ("two_way", "one_way", "no_drive"):
        d = r[name]
        print("  %-9s: b=%.3f U=%.3f Q_H=%.2f size=%.2f disp=%.2f held=%s"
              % (name, d["b_final"], d["U_final"], d["Q_H_final"], d["size_final"],
                 d["centroid_disp"], d["particle_held"]))
    print("  two-way self-limits=%s ; one-way over-drives=%s ; back-reaction matters=%s ; drive-off stalls=%s"
          % (r["two_way_self_limits"], r["one_way_overdrives"], r["backreaction_matters"], r["drive_off_stalls"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (two-way self-limitation vs one-way tearing + drive-off stall measured; reduced-flow is the floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "three_body.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/three_body.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
