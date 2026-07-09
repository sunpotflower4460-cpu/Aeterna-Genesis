#!/usr/bin/env python3
"""e027 Stage 1 -- close the Darwinian loop with mutation (adapt, diversify, track).

MODULE:   e027_evolution_transition (Stage 1: evolution)
QUESTION: with heredity + mutation + selection, does a population adapt to a fitness peak, maintain
          diversity under rare-favoring selection, and track a moving optimum?
PUT IN:   a heritable scalar trait, Gaussian mutation at reproduction, and a fitness rule
          (Wright-Fisher fitness-proportional sampling). NO "the population adapts" and NO "diversity
          is maintained" are put in -- both are measured.
EMERGED:  (measured) mutation ON climbs to the peak (mean trait ~1.51) while OFF stays stuck (~0.00);
          negative frequency-dependence maintains diversity (std ~7.7, ~20 occupied bands); a moving
          optimum is tracked with small lag (~0.07).
CLAIM TIER: measured(the three population statistics) ; interpretive(the Darwinian loop closes with
          mutation: variation + heredity + selection = adaptation + novelty + endless change) ;
          analogy(evolution, niches, Red Queen).
KNOWN MATCH: Wright-Fisher variation-selection; negative frequency-dependent selection; the Red Queen.
STATUS:   GREEN (three gates on measured population statistics: mean trait, std, tracking lag).
A_OR_B:   (A) faithful. Hand input = trait + mutation + fitness rule; adaptation / diversity / tracking
          are emergent and measured.

THE TRAP (designer hit it, we avoid it): this is an AGENT model (a population of scalar traits), NOT a
field -- stated as a Floor. Fitness is clipped positive before sampling; mutation is applied at
reproduction so offspring differ from parents. The gates are measured statistics, not evocative labels.

Floors: a fixed 1D trait space -- adaptation and diversity happen, but no RISING COMPLEXITY / new
structural dimensions emerge (that is e027 Stage 2). True open-ended evolution (unbounded novelty) is
frontier. "Evolution / niches / Red Queen" is analogy.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 400, "T": 500, "seed": 0}
QUICK = {"N": 250, "T": 300}


def evolve(fitness_fn, p, rng, sigma_mut=0.05, x0=0.0):
    x = np.full(p["N"], float(x0))
    hist = []
    for gen in range(p["T"]):
        f = np.clip(fitness_fn(x, gen), 1e-9, None)
        prob = f / f.sum()
        parents = rng.choice(p["N"], size=p["N"], p=prob)
        x = x[parents] + rng.normal(0, sigma_mut, p["N"])       # inherit + MUTATE
        hist.append((gen, float(x.mean()), float(x.std())))
    return x, hist


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])

    # (1) adaptation to a fixed peak at x*=1.5, mutation ON vs OFF
    peak = lambda x, g: np.exp(-(x - 1.5) ** 2 / (2 * 0.3 ** 2))
    x_on, H_on = evolve(peak, p, rng, sigma_mut=0.05)
    x_off, H_off = evolve(peak, p, rng, sigma_mut=0.0)

    # (2) diversification under negative frequency-dependence (rare favored = niches)
    def freqdep(x, g):
        d = np.abs(x[:, None] - x[None, :])
        crowd = (d < 0.25).sum(1)
        return 1.0 / crowd
    x_div, H_div = evolve(freqdep, p, rng, sigma_mut=0.05, x0=0.0)
    hist_bands, _ = np.histogram(x_div, bins=20)
    n_bands = int((hist_bands > p["N"] / 40).sum())

    # (3) Red Queen: a moving optimum tracked with a lag
    moving = lambda x, g: np.exp(-(x - (1.5 * np.sin(g / 60.0))) ** 2 / (2 * 0.3 ** 2))
    x_rq, H_rq = evolve(moving, p, rng, sigma_mut=0.06)
    tracks = np.array([h[1] for h in H_rq])
    targets = np.array([1.5 * np.sin(g / 60.0) for g in range(len(H_rq))])
    lag = float(np.mean(np.abs(tracks[100:] - targets[100:]))) if len(H_rq) > 100 else float(
        np.mean(np.abs(tracks - targets)))

    return {
        "params": p,
        "mean_on": round(H_on[-1][1], 3), "mean_off": round(H_off[-1][1], 3),
        "std_diversify": round(H_div[-1][2], 2), "n_bands": n_bands,
        "trait_min": round(float(x_div.min()), 1), "trait_max": round(float(x_div.max()), 1),
        "red_queen_lag": round(lag, 3),
    }


def evaluate(result, quick=False):
    checks = {
        "mutation_enables_adaptation (ON~1.5, OFF~0)":
            bool(abs(result["mean_on"] - 1.5) < 0.3 and abs(result["mean_off"]) < 0.1),
        "negative_freq_dependence_maintains_diversity (std>0.5)":
            bool(result["std_diversify"] > 0.5),
        "moving_optimum_tracked (lag<0.6)":
            bool(result["red_queen_lag"] < 0.6),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e027 evolution transition Stage 1 (evolution)", "tier": "measured",
        "put_in": "heritable scalar trait + Gaussian mutation at reproduction + a fitness rule (Wright-Fisher)",
        "emerged": ["adaptation: mutation ON mean trait %s (climbs peak x*=1.5), OFF %s (stuck)"
                    % (result["mean_on"], result["mean_off"]),
                    "diversification: negative freq-dependence std=%s over [%s,%s], ~%s bands"
                    % (result["std_diversify"], result["trait_min"], result["trait_max"], result["n_bands"]),
                    "Red Queen: moving optimum tracked with lag=%s" % result["red_queen_lag"]],
        "surprises": ["rare-favoring selection MAINTAINS a wide diversity from a single starting trait"],
        "persistence": "adaptation and tracking persist for the whole run; diversity is maintained, not lost",
        "measured_numbers": {"mean_on": result["mean_on"], "mean_off": result["mean_off"],
                             "std_diversify": result["std_diversify"], "n_bands": result["n_bands"],
                             "red_queen_lag": result["red_queen_lag"]},
        "not_scripted_check": "adaptation/diversity/tracking are measured population statistics; only the "
                              "fitness rule and mutation are put in",
        "claim_tier": "measured (population statistics) ; interpretive (Darwinian loop closes with mutation) ; "
                      "analogy (evolution / niches / Red Queen)",
        "floors": ["AGENT model (scalar traits), not a field; fixed 1D trait space",
                   "adaptation & diversity emerge but NO rising complexity / new dimensions (that is Stage 2)",
                   "true open-ended evolution (unbounded novelty) is frontier; 'evolution' is analogy"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e027 Stage 1: evolution (adapt/diversify/track)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e027 Stage 1 -- evolution: the Darwinian loop closes with mutation ===")
    print("  adaptation: mutation ON -> mean %.2f (climbs), OFF -> mean %.2f (stuck)"
          % (r["mean_on"], r["mean_off"]))
    print("  diversification: std=%.2f over [%s,%s], ~%s bands"
          % (r["std_diversify"], r["trait_min"], r["trait_max"], r["n_bands"]))
    print("  Red Queen: moving optimum tracked, lag=%.2f" % r["red_queen_lag"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (adaptation/diversity/tracking measured; fixed trait space is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "evolution.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/evolution.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
