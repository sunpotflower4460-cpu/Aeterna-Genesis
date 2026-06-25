#!/usr/bin/env python3
"""e012 Stage 2 (NEW build) -- the DYNAMIC Faddeev-Skyrme gradient flow.

The static module showed Derrick's landscape: bare (c4=0) collapses, the quartic
"third" (c4>0) has a finite minimiser L*. Here we let the field MOVE: tangent-
projected gradient flow

    d_t n = -P_tangent(dE/dn),   |n|=1 enforced each step,

with E = c2*E2 + c4*E4 (core.hopf). The discrete dE/dn is assembled from the
same central differences as E, so the flow is guaranteed to DECREASE the energy
(monotone-energy sanity check -- a wrong gradient sign would raise it).

What we MEASURE (Q_H tracked, the topology that cannot be faked):
  * c4 = 0 (bare): the hopfion UNWINDS -- Q_H -> 0 and the Skyrme-density size
    shrinks. This is the DYNAMIC confirmation of e009's shrinking bare-GPE
    hopfion: pure gradient energy has no stable size on a lattice (Derrick).
  * c4 > 0 ("the third"): collapse is PARTIALLY RESISTED / DELAYED at fine
    resolution -- more of Q_H can survive for larger c4. BUT this effect is
    FRAGILE: at coarser resolution / with the explicit time step it forces, the
    c4>0 runs can collapse just as far, or go numerically unstable (Q_H even
    overshoots sign). So we report it as an OBSERVATION, not a robust GREEN.

Floors (honest, not hidden): FULL dynamic self-stabilisation to a persistent
Q_H~=1 hopfion is NOT reached here, and even the partial resistance is
resolution-sensitive -- the quartic term is stiff (an effective 4th-order
operator), forcing a tiny explicit time step, while the lattice cutoff competes
with L*. The ROBUST, resolution-independent results are: the gradient is correct
(energy decreases monotonically) and the bare hopfion COLLAPSES (Q_H -> 0). Full
stabilisation (and robust resistance) is a frontier-observation pending finer
grids / implicit (Fourier) treatment of the gradient term (a scale candidate).
The solid stabilisation evidence is the STATIC Derrick finite-L* minimum
(Stage 1, hopfion_static); this stage confirms the bare collapse dynamically.
"Particle" is analogy.

MODULE:   e012_hopf_stabilization (Stage 2: dynamic gradient flow)
QUESTION: Does the Faddeev-Skyrme flow collapse the bare hopfion and does the 'third' resist it?
PUT IN:   Q_H=1 hopfion + gradient flow of E=c2*E2+c4*E4, |n|=1 projection. No target size is put in.
EMERGED:  (measured) c4=0 unwinds (Q_H->0), energy monotone; (observed, fragile) c4>0 can partially delay collapse.
CLAIM TIER: measured(bare collapse, energy-monotone) ; frontier-observation(robust resistance & full self-stabilisation) ; analogy(particle).
KNOWN MATCH: Derrick 1964; Faddeev-Niemi hopfion; e009 (bare-GPE hopfion shrinks).
STATUS:   GREEN on energy-monotone + bare collapse (robust); resistance fragile, full stabilisation = frontier.
A_OR_B:   (A) faithful. Hand input = S^2 field + Faddeev-Skyrme energy + gradient flow. Lattice = space, given.
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

DEFAULT = {"L": 40, "box": 6.0, "scale": 1.4, "c2": 1.0,
           "c4_list": [0.0, 10.0, 25.0], "n_steps": 2000, "n_check": 5}
QUICK = {"L": 36, "box": 5.5, "scale": 1.3, "c4_list": [0.0, 8.0, 12.0],
         "n_steps": 1500, "n_check": 4}


def _dt_for(c4, dx):
    """Stable explicit step: the stiff quartic term needs dt ~ 1/(1+c4) smaller."""
    return 3.0e-4 / (1.0 + c4 / 5.0)


def run_flow(p, c4):
    n, dx = hopf.hopfion_field(p["L"], p["scale"], p["box"])
    dt = _dt_for(c4, dx)
    E0, E20, E40 = hopf.faddeev_energy(n, dx, p["c2"], c4)
    Q0 = hopf.hopf_charge(n, dx)
    s0 = hopf.e4_rms_size(n, dx)
    every = max(1, p["n_steps"] // p["n_check"])
    energies, checks = [E0], []
    for step in range(p["n_steps"]):
        n = hopf.flow_step(n, dx, p["c2"], c4, dt)
        if (step + 1) % every == 0:
            E = hopf.faddeev_energy(n, dx, p["c2"], c4)[0]
            energies.append(E)
            checks.append({"step": step + 1, "Q_H": round(hopf.hopf_charge(n, dx), 3),
                           "size": round(hopf.e4_rms_size(n, dx), 3), "E": round(E, 2)})
    Qf = checks[-1]["Q_H"] if checks else Q0
    sf = checks[-1]["size"] if checks else s0
    mono = all(energies[i] >= energies[i + 1] - 1e-6 * abs(energies[0])
               for i in range(len(energies) - 1))
    return {"c4": c4, "dt": dt, "Q_H_initial": round(Q0, 3), "Q_H_final": Qf,
            "size_initial": round(s0, 3), "size_final": sf,
            "size_ratio": round(sf / s0, 3) if s0 > 0 else 0.0,
            "E_initial": round(E0, 2), "E_final": round(energies[-1], 2),
            "energy_monotone_decrease": bool(mono),
            "collapsed": bool(Qf < 0.5), "trace": checks}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    runs = [run_flow(p, c4) for c4 in p["c4_list"]]
    bare = next((r for r in runs if r["c4"] == 0.0), None)
    nonzero = sorted([r for r in runs if r["c4"] > 0], key=lambda r: r["c4"])
    Qf_increases = all(nonzero[i]["Q_H_final"] <= nonzero[i + 1]["Q_H_final"] + 1e-9
                       for i in range(len(nonzero) - 1)) if len(nonzero) > 1 else True
    resists = bool(nonzero and bare is not None
                   and nonzero[-1]["Q_H_final"] > bare["Q_H_final"] + 0.05)
    stabilised = bool(nonzero and nonzero[-1]["Q_H_final"] > 0.7
                      and not nonzero[-1]["collapsed"])
    return {"params": p, "runs": runs,
            "bare_collapses": bool(bare is not None and bare["collapsed"]),
            "third_resists_collapse": resists,
            "final_QH_increases_with_c4": bool(Qf_increases),
            "all_energy_monotone": bool(all(r["energy_monotone_decrease"] for r in runs)),
            "full_self_stabilisation": stabilised}


def evaluate(result, quick=False):
    # GREEN gates ONLY on the resolution-ROBUST facts: the discrete gradient is
    # correct (energy decreases monotonically) and the bare (c4=0) hopfion
    # dynamically COLLAPSES (Q_H -> 0), the dynamic confirmation of e009. The
    # dynamic "third resists" effect is REAL at fine resolution but FRAGILE
    # (sign/size of the partial resistance depends on L/dt/steps, and c4>0 runs
    # can even go numerically unstable), so it is reported as an observation, NOT
    # a pass gate -- gating on it would be tuning-to-pass. The solid stabilisation
    # evidence is the STATIC Derrick finite-L* minimum (hopfion_static).
    checks = {
        "energy_monotone_decrease(sanity)": result["all_energy_monotone"],
        "bare_collapses(Q_H->0)": result["bare_collapses"],
    }
    return all(checks.values()), checks


def _atlas(result):
    bare = next((r for r in result["runs"] if r["c4"] == 0.0), {})
    top = max(result["runs"], key=lambda r: r["c4"])
    return [{
        "experiment": "e012 hopfion flow", "tier": "measured",
        "put_in": "Q_H=1 hopfion + Faddeev-Skyrme gradient flow (|n|=1 projection); no target size",
        "emerged": ["bare (c4=0) UNWINDS: Q_H %.2f -> %.2f (dynamic Derrick collapse, e009 confirmed)"
                    % (bare.get("Q_H_initial", 1), bare.get("Q_H_final", 0)),
                    "the discrete gradient is correct (energy decreases monotonically every run)"],
        "surprises": ["the bare soliton's collapse emerges from the flow, not put in"],
        "persistence": "c4=0 collapses (robust); c4>0 partial resistance is fragile; full Q_H~1 persistence = frontier",
        "measured_numbers": {"runs": [{"c4": r["c4"], "Q_H_final": r["Q_H_final"],
                                       "size_ratio": r["size_ratio"]} for r in result["runs"]],
                             "third_partial_resistance_observed": result["third_resists_collapse"],
                             "full_self_stabilisation": result["full_self_stabilisation"]},
        "not_scripted_check": "Q_H from B=curl A; energy monotone-decrease verifies the gradient; no size imposed",
        "claim_tier": "measured (bare collapse, energy-monotone) ; frontier-observation (robust resistance & full self-stabilisation) ; analogy (particle)",
        "floors": ["dynamic 'third resists' is real at fine resolution but FRAGILE (depends on L/dt/steps; c4>0 can go unstable)",
                   "quartic term is stiff -> tiny explicit dt; lattice cutoff competes with L*",
                   "full persistent Q_H~1 needs finer grid / implicit stepping (scale candidate); static Derrick is the solid finite-L* evidence",
                   "fixed lattice; 'particle' is analogy, not an electron"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e012 hopfion gradient flow")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e012 dynamic Faddeev-Skyrme flow (collapse vs the 'third') ===")
    for run in r["runs"]:
        tag = "COLLAPSE" if run["collapsed"] else "resists"
        print("  c4=%5.1f: Q_H %.2f -> %.2f  size x%.2f  E %.0f->%.0f  [%s]  mono=%s"
              % (run["c4"], run["Q_H_initial"], run["Q_H_final"], run["size_ratio"],
                 run["E_initial"], run["E_final"], tag, run["energy_monotone_decrease"]))
    print("  bare collapses=%s ; third partially resists/delays=%s ; resistance grows with c4=%s ; full stabilisation=%s"
          % (r["bare_collapses"], r["third_resists_collapse"],
             r["final_QH_increases_with_c4"], r["full_self_stabilisation"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (energy-monotone + bare collapse measured; resistance fragile, full self-stabilisation = frontier)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "hopfion_flow.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/hopfion_flow.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
