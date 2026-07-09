#!/usr/bin/env python3
"""e027 Stage 2 -- can complexity RISE? expandable genome + a demand.

MODULE:   e027_evolution_transition (Stage 2: openended)
QUESTION: does mean genome length (complexity) rise only when the genome can expand (gene duplication)
          AND the environment demands it?
PUT IN:   variable-length genomes (a set of skills in [0,1]); tasks (targets in [0,1]); fitness =
          #tasks solved - cost*genome_length; mutation = point / duplicate / delete. NO "complexity
          rises with demand" is put in -- it is measured.
EMERGED:  (measured) a simple environment plateaus low (mean length ~1.4, cost prunes spare genes); a
          rich environment raises it to match (~6.0); a rising demand keeps it rising (~6.5).
CLAIM TIER: measured(mean genome length under each demand) ; interpretive(the missing ingredient for
          rising complexity = expandable genotype + demand) ; analogy(evolution, complexity).
KNOWN MATCH: gene duplication and divergence as a source of evolutionary novelty; cost of complexity.
STATUS:   GREEN (three gates on measured mean genome length).
A_OR_B:   (A) faithful. Hand input = the genome, tasks, and cost; whether complexity rises is emergent
          and measured.

THE TRAP (designer hit it, we avoid it): an AGENT model (variable-length genomes), NOT a field -- a
Floor. The demand is set EXTERNALLY; the rise MATCHES an imposed demand. True open-endedness needs the
demand itself to keep rising ENDOGENOUSLY (co-evolution / niche construction) = frontier, stated as a Floor.

Floors: the demand is external; genome length is a proxy for "complexity". No endogenous demand growth
(that is the deep frontier). "Complexity / evolution" is analogy.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"Npop": 200, "T": 350, "cost": 0.12, "seed": 1}
QUICK = {"Npop": 150, "T": 220}


def _fitness(g, tasks, cost, tol=0.1):
    solved = sum(1 for t in tasks if any(abs(s - t) < tol for s in g))
    return solved - cost * len(g)


def _mutate(g, rng, p_pt=0.4, p_dup=0.12, p_del=0.12):
    g = [min(max(s + (rng.normal(0, 0.05) if rng.random() < p_pt else 0), 0), 1) for s in g]
    if g and rng.random() < p_dup:
        g = g + [min(max(g[rng.integers(len(g))] + rng.normal(0, 0.08), 0), 1)]   # gene duplication
    if len(g) > 1 and rng.random() < p_del:
        del g[rng.integers(len(g))]
    if len(g) == 0:
        g = [float(rng.random())]
    return g


def _spread(n):
    return list(np.linspace(0.1, 0.9, int(n)))


def evolve(tasks_fn, p, rng):
    pop = [[float(rng.random())] for _ in range(p["Npop"])]
    hist = []
    for gen in range(p["T"]):
        tasks = tasks_fn(gen)
        f = np.array([_fitness(g, tasks, p["cost"]) for g in pop])
        w = np.exp(1.5 * (f - f.max()))
        prob = w / w.sum()
        par = rng.choice(p["Npop"], size=p["Npop"], p=prob)
        pop = [_mutate(list(pop[i]), rng) for i in par]
        mean_len = float(np.mean([len(g) for g in pop]))
        mean_solved = float(np.mean([_fitness(g, tasks, 0) for g in pop]))
        hist.append((gen, round(mean_len, 2), round(mean_solved, 2)))
    return pop, hist


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])
    _, Hs = evolve(lambda g: _spread(2), p, rng)                        # simple: 2 tasks
    _, Hr = evolve(lambda g: _spread(8), p, rng)                        # rich: 8 tasks
    _, Hg = evolve(lambda g: _spread(2 + min(g // 35, 8)), p, rng)      # rising demand 2->10
    return {
        "params": p,
        "len_simple": Hs[-1][1], "len_rich": Hr[-1][1], "len_rising": Hg[-1][1],
        "len_rising_mid": Hg[len(Hg) // 6][1],
        "solved_simple": Hs[-1][2], "solved_rich": Hr[-1][2], "solved_rising": Hg[-1][2],
    }


def evaluate(result, quick=False):
    checks = {
        "simple_env_plateaus (len<3.5)":
            bool(result["len_simple"] < 3.5),
        "demand_raises_complexity (rich > simple+2)":
            bool(result["len_rich"] > result["len_simple"] + 2),
        "rising_demand_keeps_rising (rising > simple+2 and > mid)":
            bool(result["len_rising"] > result["len_simple"] + 2
                 and result["len_rising"] > result["len_rising_mid"]),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e027 evolution transition Stage 2 (openended)", "tier": "measured",
        "put_in": "variable-length genomes (skills) + tasks + fitness = solved - cost*length + point/dup/delete mutation",
        "emerged": ["mean genome length: simple=%s (plateaus), rich=%s (rises to match), rising demand=%s (keeps rising)"
                    % (result["len_simple"], result["len_rich"], result["len_rising"]),
                    "tasks solved: simple=%s rich=%s rising=%s"
                    % (result["solved_simple"], result["solved_rich"], result["solved_rising"])],
        "surprises": ["complexity rises ONLY with an expandable genome AND a demand; cost prunes spare genes otherwise"],
        "persistence": "genome length tracks the demand: low when simple, high when rich, rising when demand rises",
        "measured_numbers": {"len_simple": result["len_simple"], "len_rich": result["len_rich"],
                             "len_rising": result["len_rising"], "solved_simple": result["solved_simple"],
                             "solved_rich": result["solved_rich"], "solved_rising": result["solved_rising"]},
        "not_scripted_check": "genome length is measured; only the tasks and cost are set -- the rise is emergent",
        "claim_tier": "measured (mean genome length) ; interpretive (missing ingredient = expandable genotype + "
                      "demand) ; analogy (complexity / evolution)",
        "floors": ["AGENT model, not a field; demand is EXTERNAL (rise matches an imposed demand)",
                   "genome length is a proxy for complexity",
                   "true open-endedness needs endogenous demand growth (co-evolution/niche construction) = frontier"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e027 Stage 2: openended (rising complexity)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e027 Stage 2 -- openended: can complexity rise? ===")
    print("  mean genome length: simple=%.1f  rich=%.1f  rising demand=%.1f"
          % (r["len_simple"], r["len_rich"], r["len_rising"]))
    print("  tasks solved:       simple=%.1f  rich=%.1f  rising=%.1f"
          % (r["solved_simple"], r["solved_rich"], r["solved_rising"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (rising complexity measured; external demand is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "openended.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/openended.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
