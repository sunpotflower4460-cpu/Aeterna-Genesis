#!/usr/bin/env python3
"""e037 -- persistent cooperation in a PURE PDE via the ECOLOGICAL public goods game (no agents).

---
id: e037
role: E
claim_tier: measured
evidence: "with a density-dependent (ecological) payoff, cooperators persist in a pure continuum PDE (frac~0.46); the classical constant-cost payoff collapses (~0.00); the mass-matched well-mixed case ALSO persists, so the mechanism is the ecological feedback, not spatial discreteness"
target_encoded: false
known_match: "Hauert-Holmes-Doebeli / Wakano-Nowak-Hauert ecological public goods; the paradox that cooperation persists in a variable-population continuum"
open_issues: ["'cooperation' is analogy for the co-existing density fields; classical PGG (fixed population) still needs discreteness/network reciprocity", "(A) faithful: the population PDE is put in by hand"]
---

MODULE:   e037_ecological_pgg
QUESTION: e027/e034 handled cooperation as an agent grid / a bistable front. Can PERSISTENT cooperation
          instead emerge in a PURE continuum PDE from the ECOLOGICAL public goods game (a density-dependent
          payoff), with NO agents and NO spatial discreteness -- and is the MECHANISM the ecological feedback
          rather than space?
PUT IN:   two population-density fields u (cooperators), v (defectors) on a periodic grid, growing by
          birth-into-empty-space with the Hauert-Holmes-Doebeli ECOLOGICAL payoff
          P_C - P_D = c*(r*A(rho) - 1),  A(rho) = (1-(1-rho)^N)/(N*rho)  (cooperators favoured at LOW rho),
          diffusion, and a common death rate. A CLASSICAL constant-cost payoff (P_C-P_D=-c) is the control.
          NO "cooperation persists" is put in -- it is measured. Well-mixed = the SAME reaction, Laplacian off.
EMERGED:  (measured) ECOLOGICAL payoff -> cooperators PERSIST in the pure PDE (coop fraction ~0.46, both
          densities > 0); CLASSICAL constant-cost -> cooperation COLLAPSES (~0.00); the mass-matched
          WELL-MIXED ecological case ALSO persists -> the mechanism is the density feedback, not space.
CLAIM TIER: measured(ecological persistence vs classical collapse; well-mixed persistence) ; interpretive
          (the ecological feedback -- cooperators favoured at low density -- lets cooperation persist in a
          CONTINUUM, refining the (A) boundary: classical PGG needs discreteness, ecological PGG does not) ;
          analogy(cooperation, public goods).
KNOWN MATCH: Hauert-Holmes-Doebeli / Wakano-Nowak-Hauert ecological public goods (density-dependent payoff).
STATUS:   E (persistence emerges from the faithful ecological payoff; gates on physical density fields).
A_OR_B:   (A) faithful. Hand input = the two-species population PDE + the ecological payoff; whether
          cooperation persists (and that the classical model collapses) is emergent and measured.

THE TRAP (designer hit it, we avoid it): the earlier failure used a WRONG constant-cost payoff (P_C-P_D=-c
always, so defectors always win) and concluded "pure-PDE cooperation is impossible". The correct ecological
payoff (Hauert-Holmes-Doebeli) is put in; persistence is measured. We gate on the CONTRAST ecological-vs-
classical AND on mass-matched well-mixed persistence, so the claim is the MECHANISM, not a tuned number.

Floors: "cooperation / public goods" is analogy for the two co-existing density fields. 同じ数学≠同じもの:
this does NOT claim social cooperation IS this PDE. The classical (fixed-population) public goods game still
needs discreteness / network reciprocity; only the ECOLOGICAL (variable-population) game persists in the
continuum. (A) faithful: the population PDE is put in by hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 8, "r": 2.5, "c": 1.0, "b0": 1.0, "death": 1.2, "L": 120, "dt": 0.01,
           "Du": 0.1, "Dv": 0.1, "steps": 20000, "seed": 0}
QUICK = {"L": 90, "steps": 12000}


def _lap(Z):
    return np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z


def _A(rho, N):
    rho = np.maximum(rho, 1e-9)
    return (1 - (1 - rho) ** N) / (N * rho)


def _payoff(u, v, p, ecological):
    rho = u + v
    rs = np.maximum(rho, 1e-9)
    x = np.clip(u / rs, 0, 1)
    if ecological:
        a = _A(rho, p["N"])
        # P_C - P_D = c*(r*A - 1): cooperators favoured where r*A(rho) > 1 (low density)
        return p["r"] * p["c"] * (x * (1 - a) + a) - p["c"], p["r"] * p["c"] * x * (1 - a)
    ben = p["r"] * p["c"] * x            # classical: benefit ~ coop fraction, constant cost c
    return ben - p["c"], ben             # P_C - P_D = -c always (defectors always win)


def _run(p, ecological=True, spatial=True):
    L = p["L"]
    rng = np.random.default_rng(p["seed"])
    u = 0.15 + 0.05 * rng.random((L, L))
    v = 0.15 + 0.05 * rng.random((L, L))
    for _ in range(p["steps"]):
        rho = u + v
        PC, PD = _payoff(u, v, p, ecological)
        du = (p["Du"] * _lap(u) if spatial else 0.0) + u * ((1 - rho) * (p["b0"] + PC) - p["death"])
        dv = (p["Dv"] * _lap(v) if spatial else 0.0) + v * ((1 - rho) * (p["b0"] + PD) - p["death"])
        u = np.clip(u + p["dt"] * du, 0.0, None)
        v = np.clip(v + p["dt"] * dv, 0.0, None)
    um, vm = float(u.mean()), float(v.mean())
    frac = um / (um + vm + 1e-9)
    return {"coop_fraction": round(frac, 3), "coop_density": round(um, 3), "defector_density": round(vm, 3)}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    eco_spatial = _run(p, ecological=True, spatial=True)
    classical_spatial = _run(p, ecological=False, spatial=True)
    eco_wellmixed = _run(p, ecological=True, spatial=False)
    return {
        "params": p,
        "eco_spatial": eco_spatial, "classical_spatial": classical_spatial, "eco_wellmixed": eco_wellmixed,
    }


def evaluate(result, quick=False):
    checks = {
        "ecological_cooperation_persists_in_pure_PDE (coop frac >0.3, coop density >0.05)":
            bool(result["eco_spatial"]["coop_fraction"] > 0.3
                 and result["eco_spatial"]["coop_density"] > 0.05),
        "classical_constant_cost_collapses (coop frac <0.1)":
            bool(result["classical_spatial"]["coop_fraction"] < 0.1),
        "mechanism_is_feedback_not_space (mass-matched well-mixed also persists >0.3)":
            bool(result["eco_wellmixed"]["coop_fraction"] > 0.3),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e037 ecological public goods (persistent cooperation in a pure PDE, no agents)",
        "tier": "measured",
        "put_in": "two population-density fields (cooperators u, defectors v) + Hauert-Holmes-Doebeli "
                  "ecological payoff P_C-P_D=c(rA(rho)-1) + diffusion + death; classical constant-cost control. "
                  "NO agents / discreteness",
        "emerged": ["ecological (spatial): coop fraction %s (density %s)"
                    % (result["eco_spatial"]["coop_fraction"], result["eco_spatial"]["coop_density"]),
                    "classical constant-cost (spatial): coop fraction %s (collapses)"
                    % result["classical_spatial"]["coop_fraction"],
                    "ecological WELL-MIXED (mass-matched, no Laplacian): coop fraction %s -> mechanism is the "
                    "density feedback, not space" % result["eco_wellmixed"]["coop_fraction"]],
        "surprises": ["cooperation persists in a PURE continuum PDE once the payoff is ecological "
                      "(density-dependent); the classical constant-cost model collapses -- the mechanism, not "
                      "spatial discreteness, decides"],
        "persistence": "the ecological coexistence is a stable state of the population PDE (well-mixed and spatial)",
        "measured_numbers": {"eco_spatial": result["eco_spatial"],
                             "classical_spatial": result["classical_spatial"],
                             "eco_wellmixed": result["eco_wellmixed"]},
        "not_scripted_check": "only the payoff form (ecological vs classical) and the population law are set; "
                              "persistence vs collapse is measured",
        "claim_tier": "measured (ecological persistence vs classical collapse; well-mixed persistence) ; "
                      "interpretive (ecological feedback lets cooperation persist in a continuum -- classical "
                      "PGG needs discreteness, ecological does not) ; analogy (cooperation / public goods)",
        "floors": ["'cooperation / public goods' is analogy for the two co-existing density fields",
                   "同じ数学≠同じもの: this does NOT claim social cooperation IS this PDE",
                   "the classical (fixed-population) public goods game still needs discreteness / network "
                   "reciprocity; only the ECOLOGICAL (variable-population) game persists in the continuum",
                   "(A) faithful: the population PDE is put in by hand, not derived"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e037 ecological public goods (pure PDE, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e037 -- persistent cooperation in a PURE PDE (ecological public goods, no agents) ===")
    print("  ecological (spatial):   coop fraction=%.3f  density=%.3f"
          % (r["eco_spatial"]["coop_fraction"], r["eco_spatial"]["coop_density"]))
    print("  classical  (spatial):   coop fraction=%.3f  (constant cost -> collapse)"
          % r["classical_spatial"]["coop_fraction"])
    print("  ecological (well-mixed, mass-matched): coop fraction=%.3f  (persists w/o space)"
          % r["eco_wellmixed"]["coop_fraction"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role E] (ecological feedback -> persistent cooperation in a pure PDE; classical collapses)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "ecological_pgg.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/ecological_pgg.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
