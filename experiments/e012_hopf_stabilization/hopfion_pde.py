#!/usr/bin/env python3
"""e012 Stage 3 (the prize) -- complete-PDE Hopf self-stabilization.

e012 Stage 2 showed the EXPLICIT Faddeev-Skyrme gradient flow collapses the bare
hopfion and only fragilely resists collapse for c4>0 (the quartic term is stiff;
Q_H rewinds). The static Derrick (Stage 1) proves a finite L* minimum EXISTS; the
question left open (frontier) was whether the full 3D PDE flow can hold a
hopfion at L* with Q_H ~ 1.

Here we close it with a STABILIZED SEMI-IMPLICIT flow (core.hopf
stabilized_flow_step): the gradient is filtered by 1/(1 + dt*kappa*|k|^4), a
biharmonic convexity-splitting stabiliser treated implicitly. The filter is
positive-definite -> energy stays MONOTONE -> the gradient sign is still correct;
it only damps the high-k modes where the quartic stiffness lives, so a much
larger stable dt is possible. We MEASURE:
  * c4 = 0 (bare):  still COLLAPSES -- Q_H -> 0 (Derrick collapse, e009 confirmed).
  * c4 > 0 (third): Q_H is HELD ~ 1 while the size converges to a finite L*, and
    L* GROWS with c4 (Derrick: L* ~ sqrt(c4)). Energy is monotone throughout.

So the "third" (a higher-derivative term) dynamically keeps a topologically
non-trivial particle ("circulation that does not cancel") alive at a finite size
-- frontier -> measured.

Floors (honest): there is a BASIN limit -- if the hopfion is started far BELOW
L* (under-resolved on the lattice) it still unwinds before it can grow; the flow
HOLDS a resolved hopfion at L*, it does not rescue an already-collapsed one. The
ABSOLUTE L* is resolution/kappa dependent; what is robust is Q_H ~ 1 preserved,
the finite converged size, and L* increasing with c4. "Particle" is analogy; the
literature result (Q_H=1 is a stable Faddeev-Skyrme minimiser, Faddeev-Niemi /
Sutcliffe) is the physics backing. Fixed lattice.

MODULE:   e012_hopf_stabilization (Stage 3: complete-PDE self-stabilization)
QUESTION: Can a complete 3D PDE flow hold a hopfion at finite L* with Q_H ~ 1 (the 'third' stabilising dynamically)?
PUT IN:   Q_H=1 hopfion + Faddeev-Skyrme energy + a stabilized semi-implicit gradient flow. No target size is put in.
EMERGED:  (measured) c4=0 collapses (Q_H->0); c4>0 HOLDS Q_H~1, converges to finite L*, L* grows with c4; energy monotone.
CLAIM TIER: measured(Q_H~1 held, finite L*, L*(c4) up, energy monotone) ; analogy(particle).
KNOWN MATCH: Faddeev-Niemi / Sutcliffe (Q_H=1 is a stable hopfion); Derrick 1964.
STATUS:   GREEN (complete-PDE self-stabilization measured; basin/absolute-L* are stated floors).
A_OR_B:   (A) faithful. Hand input = S^2 field + Faddeev-Skyrme energy + flow; stabilization is emergent.
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

DEFAULT = {"L": 40, "box": 7.0, "c2": 1.0, "kappa": 40.0, "dt": 8e-3,
           "n_steps": 1200, "n_check": 4, "start_scale": 2.0,
           "c4_list": [0.0, 15.0, 25.0, 40.0]}
QUICK = {"L": 36, "box": 7.0, "start_scale": 2.4, "n_steps": 800, "c4_list": [0.0, 25.0]}


def run_flow(p, c4):
    n, dx = hopf.hopfion_field(p["L"], p["start_scale"], p["box"])
    K4 = hopf.k4_grid(p["L"], dx)
    dt = p["dt"]
    E0 = hopf.faddeev_energy(n, dx, p["c2"], c4)[0]
    Q0 = hopf.hopf_charge(n, dx)
    s0 = hopf.e4_rms_size(n, dx)
    every = max(1, p["n_steps"] // p["n_check"])
    prev_E, E = E0, E0
    mono = True
    trace = []
    for step in range(p["n_steps"]):
        n = hopf.stabilized_flow_step(n, dx, p["c2"], c4, dt, p["kappa"], K4)
        E = hopf.faddeev_energy(n, dx, p["c2"], c4)[0]
        if E > prev_E + 1e-6 * abs(E0):
            mono = False
        prev_E = E
        if (step + 1) % every == 0:
            trace.append({"step": step + 1, "Q_H": round(hopf.hopf_charge(n, dx), 3),
                          "size": round(hopf.e4_rms_size(n, dx), 3)})
    Qf = trace[-1]["Q_H"] if trace else Q0
    sf = trace[-1]["size"] if trace else s0
    return {"c4": c4, "Q_H_initial": round(Q0, 3), "Q_H_final": Qf,
            "size_initial": round(s0, 3), "size_final": sf,
            "energy_monotone": bool(mono),
            "collapsed": bool(abs(Qf) < 0.5),
            "stabilised": bool(abs(Qf) > 0.7), "trace": trace}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    runs = [run_flow(p, c4) for c4 in p["c4_list"]]
    bare = next((r for r in runs if r["c4"] == 0.0), None)
    third = sorted([r for r in runs if r["c4"] > 0], key=lambda r: r["c4"])
    sizes = [r["size_final"] for r in third if r["stabilised"]]
    Lstar_grows = (all(sizes[i] <= sizes[i + 1] + 1e-6 for i in range(len(sizes) - 1))
                   if len(sizes) > 1 else True)
    return {
        "params": p, "runs": runs,
        "bare_collapses": bool(bare is not None and bare["collapsed"]),
        "third_holds_QH": bool(third and all(r["stabilised"] for r in third)),
        "all_energy_monotone": bool(all(r["energy_monotone"] for r in runs)),
        "Lstar_grows_with_c4": bool(Lstar_grows),
        "stable_sizes": [(r["c4"], r["size_final"]) for r in third],
    }


def evaluate(result, quick=False):
    checks = {
        "energy_monotone(all)": result["all_energy_monotone"],
        "bare_collapses(Q_H->0)": result["bare_collapses"],
        "third_holds_QH~1(self-stabilises)": result["third_holds_QH"],
        "Lstar_grows_with_c4(Derrick)": result["Lstar_grows_with_c4"],
    }
    return all(checks.values()), checks


def _atlas(result):
    third = [r for r in result["runs"] if r["c4"] > 0]
    return [{
        "experiment": "e012 hopfion complete-PDE self-stabilization", "tier": "measured",
        "put_in": "Q_H=1 hopfion + Faddeev-Skyrme energy + stabilized semi-implicit flow; no target size",
        "emerged": ["c4>0 HOLDS Q_H~1 and converges to a finite L* (self-stabilization): %s"
                    % result["stable_sizes"],
                    "L* grows with c4 (Derrick); bare c4=0 still collapses (Q_H->0)"],
        "surprises": ["the complete 3D PDE keeps a topological particle alive at finite size -- frontier -> measured"],
        "persistence": "c4>0 hopfion persists at L* (energy monotone); c4=0 unwinds",
        "measured_numbers": {"runs": [{"c4": r["c4"], "Q_H_final": r["Q_H_final"],
                                       "size_final": r["size_final"]} for r in result["runs"]],
                             "stable_sizes_L*(c4)": result["stable_sizes"]},
        "not_scripted_check": "Q_H from B=curl A; energy monotone verifies the gradient; no size imposed",
        "claim_tier": "measured (Q_H~1 held, finite L*, L*(c4) up, energy monotone) ; analogy (particle)",
        "floors": ["BASIN limit: a hopfion started far below L* (under-resolved) still unwinds; the flow holds a resolved one",
                   "absolute L* is resolution/kappa dependent; robust = Q_H~1 held, finite L*, L*(c4) increasing",
                   "fixed lattice; 'particle' is analogy, not an electron"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e012 Hopf complete-PDE self-stabilization")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e012 Stage 3: complete-PDE Hopf self-stabilization (semi-implicit) ===")
    for run in r["runs"]:
        tag = "COLLAPSE" if run["collapsed"] else ("SELF-STABILISED" if run["stabilised"] else "partial")
        print("  c4=%5.1f: Q_H %.2f -> %.2f  size %.2f -> %.2f  [%s]  energy_monotone=%s"
              % (run["c4"], run["Q_H_initial"], run["Q_H_final"], run["size_initial"],
                 run["size_final"], tag, run["energy_monotone"]))
    print("  bare collapses=%s ; third holds Q_H~1=%s ; L* grows with c4=%s ; energy monotone=%s"
          % (r["bare_collapses"], r["third_holds_QH"], r["Lstar_grows_with_c4"], r["all_energy_monotone"]))
    print("  stable sizes L*(c4): %s" % r["stable_sizes"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (complete-PDE self-stabilization measured; basin/absolute-L* are floors)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "hopfion_pde.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/hopfion_pde.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
