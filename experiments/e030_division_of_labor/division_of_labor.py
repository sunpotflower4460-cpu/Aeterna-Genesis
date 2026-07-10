#!/usr/bin/env python3
"""e030 -- division of labor: does a CONVEX fitness return drive germ-soma differentiation?

MODULE:   e030_division_of_labor  [FRONTIER]
QUESTION: the e029 major transition rescued cooperation but had NO division of labor. When does a group of
          cells SPECIALIZE into reproductive (germ) and viability (soma) roles rather than stay generalist?
          Michod/Rueffler: specialization is favored when the return curve is CONVEX (accelerating).
PUT IN:   G groups of n cells; each cell allocates x in [0,1] to reproduction, 1-x to viability; the
          per-cell return is a power law (x**a, (1-x)**a); a group needs BOTH functions, so group fitness =
          mean(reproduction) * mean(viability); groups reproduce by fitness + mutation. NO "specialize" is
          put in; we only set the return-curve shape a and measure the allocation distribution.
EMERGED:  (measured) with a CONVEX return (a>1) cells split into a bimodal germ/soma distribution -- most
          groups hold BOTH a pure-germ (x~1) and a pure-soma (x~0) cell -- and the specialist fraction
          rises monotonically with the convexity a; a concave return (a<1) gives far less specialization.
CLAIM TIER: measured(specialist fraction vs convexity; universal germ-soma coexistence at strong convexity)
          ; interpretive(division of labor emerges from a convex fitness return -- the missing piece of the
          major transition) ; analogy(germ-soma differentiation, multicellularity) ; FRONTIER.
KNOWN MATCH: Michod's fitness-convexity theory of germ-soma; Rueffler et al. on the evolution of division
          of labor; Volvox germ-soma differentiation.
STATUS:   GREEN (gates on the allocation distribution -- a physical/population quantity).
A_OR_B:   (A) faithful. Hand input = the return-curve shape + group fitness; the bimodal specialization and
          its dependence on convexity are emergent and measured.

THE TRAP (designer hit it, we avoid it): the group fitness is the PRODUCT of the two mean functions, so a
group with only reproducers OR only survivors dies -- both roles are needed; specialization is then favored
purely by the CONVEXITY of the return, not by hand. Gate on the allocation distribution (specialist
fraction / bimodality) -- never call the cells "alive" or a "mind".

Floors: FRONTIER -- a bounded toy; "germ-soma / division of labor / multicellularity" is analogy for the
measured allocation bimodality. A concave return still leaves some drift-spread (not perfectly generalist);
the robust facts are the CONTRAST convex-vs-concave and the monotone rise with convexity.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"G": 100, "n": 16, "T": 500, "mut": 0.03, "as": [0.5, 1.0, 2.0, 3.0, 4.0],
           "a_convex": 4.0, "a_concave": 0.5, "seeds": [0, 1, 2, 3]}
QUICK = {"T": 300, "seeds": [0, 1, 2]}


def _run(a, p, seed):
    """Evolve cell allocations under a power-law return of exponent a; return distribution summaries."""
    rng = np.random.default_rng(seed)
    G, n = p["G"], p["n"]
    x = np.clip(rng.normal(0.5, 0.03, (G, n)), 0, 1)
    for _ in range(p["T"]):
        gfit = np.clip((x ** a).mean(1) * ((1 - x) ** a).mean(1), 1e-12, None)
        parents = rng.choice(G, size=G, p=gfit / gfit.sum())
        x = np.clip(x[parents] + rng.normal(0, p["mut"], (G, n)), 0, 1)
    specialist_frac = float(np.mean((x < 0.2) | (x > 0.8)))
    both_roles = float(np.mean((x > 0.8).any(1) & (x < 0.2).any(1)))   # groups with pure germ AND pure soma
    return {"a": a, "specialist_frac": round(specialist_frac, 3), "both_roles": round(both_roles, 3),
            "mean_x": round(float(x.mean()), 3)}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    mean = lambda key, a: float(np.mean([_run(a, p, s)[key] for s in p["seeds"]]))

    sweep = []
    for a in p["as"]:
        sweep.append({"a": a,
                      "specialist_frac": round(mean("specialist_frac", a), 3),
                      "both_roles": round(mean("both_roles", a), 3)})
    spec_convex = next(s["specialist_frac"] for s in sweep if s["a"] == p["a_convex"])
    spec_concave = next(s["specialist_frac"] for s in sweep if s["a"] == p["a_concave"])
    both_convex = next(s["both_roles"] for s in sweep if s["a"] == p["a_convex"])
    # monotone rise of specialist fraction with convexity a
    fracs = [s["specialist_frac"] for s in sweep]
    monotone = all(fracs[i] <= fracs[i + 1] + 0.03 for i in range(len(fracs) - 1))
    return {
        "params": p, "sweep": sweep,
        "spec_convex": spec_convex, "spec_concave": spec_concave, "both_roles_convex": both_convex,
        "monotone_in_convexity": bool(monotone),
    }


def evaluate(result, quick=False):
    checks = {
        "convex_returns_drive_specialization (specialist frac at convex a >0.6)":
            bool(result["spec_convex"] > 0.6),
        "specialization_rises_with_convexity (convex >1.5x concave; monotone)":
            bool(result["spec_convex"] > 1.5 * result["spec_concave"] and result["monotone_in_convexity"]),
        "germ_soma_differentiation (groups with pure germ AND soma >0.9 at convex a)":
            bool(result["both_roles_convex"] > 0.9),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e030 division of labor (germ-soma from convex returns)", "tier": "measured/frontier",
        "put_in": "G groups of n cells allocating x to reproduction vs viability; power-law return exponent a; "
                  "group fitness = mean(repro)*mean(viab); group reproduction + mutation",
        "emerged": ["specialist fraction vs convexity a: %s"
                    % [(s["a"], s["specialist_frac"]) for s in result["sweep"]],
                    "groups holding BOTH a pure germ and a pure soma cell at convex a=%s: %s"
                    % (result["params"]["a_convex"], result["both_roles_convex"])],
        "surprises": ["a convex return alone splits a generalist group into a bimodal germ/soma pair -- "
                      "differentiation with nothing differentiated by hand"],
        "persistence": "specialization is stable under convex returns and scales monotonically with convexity",
        "measured_numbers": {"sweep": result["sweep"], "spec_convex": result["spec_convex"],
                             "spec_concave": result["spec_concave"], "both_roles_convex": result["both_roles_convex"]},
        "not_scripted_check": "only the return-curve shape is set; the bimodal specialization is measured",
        "claim_tier": "measured (specialist fraction vs convexity; germ-soma coexistence) ; interpretive "
                      "(division of labor from a convex return -- the missing piece of the major transition) "
                      "; analogy (germ-soma / multicellularity) ; FRONTIER",
        "floors": ["FRONTIER: a bounded toy; 'germ-soma / division of labor' is analogy for allocation bimodality",
                   "a concave return still leaves drift-spread; the robust facts are the convex-vs-concave "
                   "contrast and the monotone rise with convexity",
                   "no real cell / organism is differentiated"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e030 division of labor [frontier]")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e030 [FRONTIER] -- division of labor: convex returns drive germ-soma differentiation ===")
    print("  specialist fraction vs return-curve convexity a:")
    for s in r["sweep"]:
        print("     a=%.1f  specialist_frac=%.2f  groups_with_both_roles=%.2f"
              % (s["a"], s["specialist_frac"], s["both_roles"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (convex returns drive germ-soma differentiation; FRONTIER)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "division_of_labor.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/division_of_labor.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
