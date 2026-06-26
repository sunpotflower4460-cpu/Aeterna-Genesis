#!/usr/bin/env python3
"""e015 Stage 2 -- the two arms of autopoiesis: cut EITHER and it dies.

A minimal mutual-production model of a closed living organization: a membrane M
and a metabolism A that PRODUCE EACH OTHER, fed by a throughflow S (the drive):

    dM/dt = alpha * A * (1 - M) - beta  * M      (metabolism builds the membrane)
    dA/dt = gamma * M * (1 - A) * S - delta * A  (membrane + substrate sustain metabolism)

The model has TWO production arms. We never write "die"; we MEASURE:
  * DRIVEN & intact: M and A settle at a nonzero coexistence (the vessel lives).
  * BREAK THE MEMBRANE (knock out gamma: the membrane can no longer support the
    metabolism): A decays, then M -- which A built -- decays too. Death.
  * STOP THE METABOLISM (knock out alpha: it can no longer build the membrane):
    M decays, then A -- which M sustained -- decays too. Death.
  * cut the DRIVE (S -> 0): both decay. A critical drive S_c separates life/death.

So the closure is autopoietic: each arm is necessary; cutting EITHER unbinds the
whole. This is the minimal kinematics of the open-closed duality of e015 Stage 1.

Floors: a minimal kinetic mutual-production model (not a spatial membrane);
"membrane/metabolism/autopoiesis/death" is analogy/interpretive; not a cell.

MODULE:   e015_vessel_closure (Stage 2: two-arm autopoiesis)
QUESTION: In a membrane<->metabolism mutual-production loop, does cutting EITHER arm kill the whole?
PUT IN:   two coupled production laws (A builds M; M+drive sustain A) + a drive S. "Die if an arm is cut" is NOT put in.
EMERGED:  (measured) intact+driven -> coexistence; knock out either arm -> both decay (death); a critical drive S_c.
CLAIM TIER: measured(coexistence, both-arm death, critical S) ; interpretive(autopoietic closure) ; analogy(membrane/metabolism/life).
KNOWN MATCH: autopoiesis (Maturana-Varela); mutual catalysis / dissipative closure.
STATUS:   GREEN (both-arm death + critical drive measured; "membrane/metabolism/life" is analogy).
A_OR_B:   (A) faithful kinetics. Hand input = the two mutual-production laws + a drive; death is emergent.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"alpha": 1.0, "beta": 0.2, "gamma": 1.0, "delta": 0.2, "S": 1.0,
           "steps": 6000, "dt": 0.01, "M0": 0.5, "A0": 0.5,
           "S_list": [0.02, 0.04, 0.06, 0.1, 0.3, 1.0], "cut_time": 15.0}
QUICK = {"steps": 4000, "S_list": [0.02, 0.06, 1.0]}


def integrate(p, S=None, break_membrane=None, stop_metabolism=None):
    """Evolve (M, A); knockouts set gamma->0 (break membrane) or alpha->0 (stop metabolism)."""
    if S is None:
        S = p["S"]
    M, A = p["M0"], p["A0"]
    dt = p["dt"]
    for s in range(p["steps"]):
        t = s * dt
        a = 0.0 if (stop_metabolism is not None and t >= stop_metabolism) else p["alpha"]
        g = 0.0 if (break_membrane is not None and t >= break_membrane) else p["gamma"]
        # both derivatives from the SAME old (M, A) -> order-independent (CodeRabbit P2)
        dM = a * A * (1 - M) - p["beta"] * M
        dA = g * M * (1 - A) * S - p["delta"] * A
        M = max(M + dt * dM, 0.0)
        A = max(A + dt * dA, 0.0)
    return round(M, 4), round(A, 4)


def _alive(MA):
    return bool(MA[0] > 0.05 and MA[1] > 0.05)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    normal = integrate(p)
    broke_M = integrate(p, break_membrane=p["cut_time"])
    stopped_A = integrate(p, stop_metabolism=p["cut_time"])
    sweep = []
    for S in p["S_list"]:
        MA = integrate(p, S=S)
        sweep.append({"S": S, "M": MA[0], "A": MA[1], "alive": _alive(MA)})
    alive_S = [s["S"] for s in sweep if s["alive"]]
    return {
        "params": p,
        "normal_MA": list(normal), "alive_when_intact": _alive(normal),
        "break_membrane_MA": list(broke_M), "dies_on_break_membrane": not _alive(broke_M),
        "stop_metabolism_MA": list(stopped_A), "dies_on_stop_metabolism": not _alive(stopped_A),
        "S_sweep": sweep,
        "critical_drive_S": min(alive_S) if alive_S else None,
        "has_critical_drive": bool(alive_S and not sweep[0]["alive"]),
    }


def evaluate(result, quick=False):
    checks = {
        "alive_when_intact_and_driven": result["alive_when_intact"],
        "dies_when_membrane_broken": result["dies_on_break_membrane"],
        "dies_when_metabolism_stopped": result["dies_on_stop_metabolism"],
        "critical_drive_exists": result["has_critical_drive"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e015 two-arm autopoiesis", "tier": "measured",
        "put_in": "membrane<->metabolism mutual-production laws + drive S; 'die if an arm is cut' not put in",
        "emerged": ["intact+driven -> coexistence M,A=%s (alive)" % result["normal_MA"],
                    "break membrane -> %s (death); stop metabolism -> %s (death) -- EITHER arm kills"
                    % (result["break_membrane_MA"], result["stop_metabolism_MA"]),
                    "a critical drive S_c=%s separates life from death" % result["critical_drive_S"]],
        "surprises": ["necessity of BOTH arms is emergent: the loop, not either part alone, is the living unit"],
        "persistence": "coexistence only while both arms run and the drive flows",
        "measured_numbers": {"normal_MA": result["normal_MA"],
                             "break_membrane_MA": result["break_membrane_MA"],
                             "stop_metabolism_MA": result["stop_metabolism_MA"],
                             "critical_drive_S": result["critical_drive_S"]},
        "not_scripted_check": "death follows from knocking out a production term; no death rule is written",
        "claim_tier": "measured (coexistence, both-arm death, critical S) ; interpretive (autopoietic closure) ; analogy (membrane/metabolism/life)",
        "floors": ["minimal kinetic model (not a spatial membrane); 'membrane/metabolism/life' is analogy; not a cell",
                   "fixed parameters; we did NOT make life"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e015 two-arm autopoiesis")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e015 two-arm autopoiesis (cut EITHER arm -> death) ===")
    print("  intact + driven:    M,A = %s  alive=%s" % (r["normal_MA"], r["alive_when_intact"]))
    print("  break the membrane: M,A = %s  death=%s" % (r["break_membrane_MA"], r["dies_on_break_membrane"]))
    print("  stop the metabolism:M,A = %s  death=%s" % (r["stop_metabolism_MA"], r["dies_on_stop_metabolism"]))
    print("  drive sweep (critical S_c=%s):" % r["critical_drive_S"])
    for s in r["S_sweep"]:
        print("    S=%.3f: M=%.3f A=%.3f %s" % (s["S"], s["M"], s["A"], "ALIVE" if s["alive"] else "dead"))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (both-arm death + critical drive measured; autopoiesis is analogy)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.dirname(__file__)
        with open(os.path.join(out, "autopoiesis.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote autopoiesis.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
