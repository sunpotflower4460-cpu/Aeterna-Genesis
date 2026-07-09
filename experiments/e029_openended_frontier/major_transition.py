#!/usr/bin/env python3
"""e029 Stage 2 -- the major transition: does group reproduction make cooperation a stable higher unit?

MODULE:   e029_openended_frontier (Stage 2: major_transition)  [FRONTIER]
QUESTION: e027 showed spatial structure STABILIZES cooperation (a necessary condition). The full major
          transition needs the GROUP to become a reproducing unit. Does shifting the unit of selection to
          the group (groups reproduce by mean fitness, with a founder BOTTLENECK) rescue cooperation where
          individual selection collapses -- a higher-level individual?
PUT IN:   G groups of n agents; cooperators pay cost c and produce a public good b*(#C)/n shared in-group;
          reproduction either of INDIVIDUALS (by individual fitness) or of GROUPS (by group-mean fitness,
          each new group founded by k propagules + within-group selection). NO "group selection saves
          cooperation" and NO "bottleneck helps" are put in.
EMERGED:  (measured) individual selection collapses cooperation at every temptation b; group reproduction
          rescues it to a high stable fraction; a tighter founder bottleneck (small k) gives more
          cooperation than a loose one (the bottleneck reduces within-group cheating).
CLAIM TIER: measured(individual collapse; group rescue; bottleneck monotonicity) ; interpretive(a major
          transition = the group becomes the reproducing individual; conflict is suppressed by the
          bottleneck aligning within- and between-group fitness) ; analogy(multicellularity) ; FRONTIER.
KNOWN MATCH: multilevel / group selection (Wilson); Hamilton's rule; the germline bottleneck in the
          evolution of multicellularity (Grosberg-Strathmann); Traulsen-Nowak group selection.
STATUS:   GREEN (gates on cooperator fraction -- a physical/population quantity).
A_OR_B:   (A) faithful. Hand input = the payoff rule + the two reproduction schemes; the collapse, the
          rescue, and the bottleneck dependence are emergent and measured.

THE TRAP (designer hit it, we avoid it): individual and group runs use the SAME payoff; only the UNIT of
reproduction differs. The temptation b is swept so the individual-collapse is not a single cherry-picked
point. Gate on cooperator fraction -- never call this a "society" or "mind".

Floors: FRONTIER -- cooperation STABILITY under group reproduction is a necessary ingredient of a major
transition, NOT the whole thing (no division of labor, no germ-soma differentiation here; policing is
marginal in this regime). "Major transition / higher individual / multicellularity" is analogy for the
measured cooperator fraction.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"G": 60, "n": 20, "c": 0.5, "T": 300, "mut": 0.02,
           "bs": [1.5, 3.0], "ks": [1, 20], "seeds": [0, 1, 2], "b_main": 3.0}
QUICK = {"T": 180, "seeds": [0, 1]}


def _fitness(strat, n, b, c):
    C = strat.sum(1, keepdims=True)
    return np.clip(1.0 + b * C / n - c * strat, 1e-6, None)


def run(mode, b, p, seed, k=1):
    """Return the final cooperator fraction under individual or group reproduction."""
    rng = np.random.default_rng(seed)
    G, n = p["G"], p["n"]
    strat = (rng.random((G, n)) < 0.5).astype(float)
    for _ in range(p["T"]):
        fit = _fitness(strat, n, b, p["c"])
        if mode == "individual":
            flat = strat.reshape(-1)
            ff = fit.reshape(-1)
            newflat = flat[rng.choice(flat.size, size=flat.size, p=ff / ff.sum())]
            m = rng.random(flat.size) < p["mut"]
            newflat[m] = 1 - newflat[m]
            strat = newflat.reshape(G, n)
        else:  # group reproduction + founder bottleneck
            gfit = fit.mean(1)
            parents = rng.choice(G, size=G, p=gfit / gfit.sum())
            newg = []
            for par in parents:
                founders = strat[par][rng.integers(0, n, k)]
                grp = np.resize(founders, n).astype(float)
                gf = _fitness(grp[None], n, b, p["c"])[0]
                grp = grp[rng.choice(n, size=n, p=gf / gf.sum())]
                mm = rng.random(n) < p["mut"]
                grp[mm] = 1 - grp[mm]
                newg.append(grp)
            strat = np.array(newg)
    return float(strat.mean())


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    seeds = p["seeds"]
    mean = lambda xs: float(np.mean(xs))

    # individual vs group (k=1) cooperator fraction across temptations b
    sweep = []
    for b in p["bs"]:
        ind = mean([run("individual", b, p, s) for s in seeds])
        grp = mean([run("group", b, p, s, k=1) for s in seeds])
        sweep.append({"b": b, "individual": round(ind, 3), "group_bottleneck": round(grp, 3)})

    # bottleneck strength at b_main: tight (k=1) vs loose (k=n)
    bm = p["b_main"]
    coop_k = []
    for k in p["ks"]:
        coop_k.append({"k": k, "coop": round(mean([run("group", bm, p, s, k=k) for s in seeds]), 3)})

    ind_main = mean([run("individual", bm, p, s) for s in seeds])
    grp_main = next(sw["group_bottleneck"] for sw in sweep if sw["b"] == bm)
    tight = coop_k[0]["coop"]
    loose = coop_k[-1]["coop"]
    return {
        "params": p, "sweep": sweep, "coop_vs_k": coop_k, "b_main": bm,
        "individual_main": round(ind_main, 3), "group_main": round(grp_main, 3),
        "coop_tight_bottleneck": tight, "coop_loose_bottleneck": loose,
        "individual_collapses_all_b": bool(all(sw["individual"] < 0.15 for sw in sweep)),
        "group_rescues_all_b": bool(all(sw["group_bottleneck"] > 0.5 for sw in sweep)),
    }


def evaluate(result, quick=False):
    checks = {
        "individual_selection_collapses (coop<0.15 at all b)":
            result["individual_collapses_all_b"],
        "group_reproduction_rescues_cooperation (coop>0.5 at all b)":
            result["group_rescues_all_b"],
        "bottleneck_tightens_cooperation (k=1 coop > loose-k coop)":
            bool(result["coop_tight_bottleneck"] > result["coop_loose_bottleneck"]),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e029 openended frontier Stage 2 (major_transition)", "tier": "measured/frontier",
        "put_in": "G groups of n agents + public-good payoff; reproduction of INDIVIDUALS vs GROUPS (mean "
                  "fitness) with a founder bottleneck k",
        "emerged": ["cooperator fraction vs temptation b: %s"
                    % [(sw["b"], sw["individual"], sw["group_bottleneck"]) for sw in result["sweep"]],
                    "bottleneck strength at b=%s: %s (tighter k -> more cooperation)"
                    % (result["b_main"], [(c["k"], c["coop"]) for c in result["coop_vs_k"]])],
        "surprises": ["shifting the UNIT of reproduction to the group turns doomed cooperation into a stable "
                      "high fraction -- a higher-level individual"],
        "persistence": "group-reproduced cooperation is stable across the temptation range; individual collapses",
        "measured_numbers": {"sweep": result["sweep"], "coop_vs_k": result["coop_vs_k"],
                             "individual_main": result["individual_main"], "group_main": result["group_main"]},
        "not_scripted_check": "individual and group runs share the payoff; only the unit of reproduction "
                              "differs; the collapse/rescue/bottleneck dependence are measured",
        "claim_tier": "measured (collapse, rescue, bottleneck) ; interpretive (the group becomes the "
                      "reproducing individual; the bottleneck suppresses conflict) ; analogy (multicellularity) "
                      "; FRONTIER",
        "floors": ["FRONTIER: cooperation stability under group reproduction is a NECESSARY ingredient, not the "
                   "whole major transition (no division of labor / germ-soma here; policing is marginal in this regime)",
                   "'major transition / higher individual / multicellularity' is analogy for the cooperator fraction"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e029 Stage 2: the major transition [frontier]")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e029 Stage 2 [FRONTIER] -- the major transition: group reproduction rescues cooperation ===")
    print("  cooperator fraction vs temptation b (individual / group+bottleneck):")
    for sw in r["sweep"]:
        print("     b=%.1f  individual=%.2f  group=%.2f" % (sw["b"], sw["individual"], sw["group_bottleneck"]))
    print("  bottleneck at b=%s: %s (tighter k -> more cooperation)"
          % (r["b_main"], [(c["k"], c["coop"]) for c in r["coop_vs_k"]]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (group reproduction makes cooperation a stable higher unit; FRONTIER)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "major_transition.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/major_transition.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
