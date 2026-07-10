#!/usr/bin/env python3
"""e036 -- adaptation WITHOUT agents: the replicator-mutator field climbs a fitness landscape.

MODULE:   e036_field_adaptation
QUESTION: e027 Stage 1 got "a population adapts to a fitness peak and tracks a moving optimum" from an AGENT
          model (Wright-Fisher: heritable trait + Gaussian mutation + fitness sampling) -- a floor (LAW.md:
          not a field). Do the SAME facts emerge from a REAL POPULATION-GENETICS FIELD EQUATION with no
          agents, no sampling?
PUT IN:   the replicator-mutator (Crow-Kimura) equation for a normalized population DENSITY field p(x,t)
          over a trait axis x:  dp/dt = D d2p/dx2 + (f(x) - <f>) p ,  <f> = int f p / int p.
          D is the mutation rate (diffusion in trait space); f(x) is the fitness landscape (a quadratic peak
          f = -k x^2/2, or a moving peak f = -k (x - v t)^2/2). NO "the population adapts", NO variance
          formula, NO tracking lag is put in -- all are measured.
EMERGED:  (measured) a mutation-selection balance whose equilibrium variance matches the closed form
          sigma^2 = sqrt(2D/k); adaptation -- an off-peak density climbs to the peak (mean -> 0); and for a
          moving optimum the density tracks it with a LAG L = v/(k sigma^2) that is LINEAR in the speed v
          (the lag load) -- none put in.
CLAIM TIER: measured(equilibrium variance vs sqrt(2D/k); adaptation to the peak; lag linear in speed and
          matching v/(k sigma^2)) ; interpretive(selection = advection up the fitness gradient, mutation =
          diffusion; adaptation and the lag load are field phenomena) ; analogy(evolution, adaptation, niches).
KNOWN MATCH: the replicator-mutator / Crow-Kimura continuous-of-alleles equation; mutation-selection balance
          sigma^2 = sqrt(2D/k); the lag load L = v/(k sigma^2) for a moving optimum. Established theory.
STATUS:   GREEN (gates on physical field quantities: the density's variance, mean, and tracking lag).
A_OR_B:   (A) faithful. Hand input = the replicator-mutator field law + D + the fitness landscape; the
          balance variance, the climb to the peak and the lag load are emergent and measured.

THE TRAP (designer hit it, we avoid it): do NOT put the variance or the lag in. We set the mutation D and the
fitness landscape f(x); the equilibrium variance sqrt(2D/k), the climb to the peak and the lag L=v/(k sigma^2)
are OUTPUTS that match Crow-Kimura theory. "Mutation off" is D=0 (a delta cannot move -> stuck), the field
analog of e027's mutation-off control.

Floors: "evolution / adaptation / niche" is analogy for a density field on a trait axis. 同じ数学≠同じもの:
this does NOT claim evolution IS the replicator-mutator PDE -- it shows the SAME facts (adaptation, mutation-
selection balance, lag load) emerge in a field with no agents. Above a critical speed the lag runs away (the
population is lost); only the small-speed linear regime is claimed. (A) faithful: the field law is put in by
hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"L": 12.0, "N": 481, "k": 1.0, "cfl": 0.3,
           "Ds": [0.05, 0.1, 0.2], "D_track": 0.1, "vs": [0.05, 0.10, 0.15],
           "x0": 3.0, "steps": 30000}
QUICK = {"N": 321, "Ds": [0.05, 0.2], "vs": [0.05, 0.15], "steps": 18000}


def _grid(p):
    x = np.linspace(-p["L"] / 2, p["L"] / 2, p["N"])
    dx = x[1] - x[0]
    Dmax = max(max(p["Ds"]), p["D_track"])
    dt = p["cfl"] * dx ** 2 / Dmax          # explicit-diffusion stability D*dt/dx^2 = cfl < 0.5
    return x, dx, dt


def _evolve(x, dx, dt, p0, D, k, steps, v=None):
    """Integrate the replicator-mutator field. A moving optimum is handled in its CO-MOVING frame: the peak
    stays at x=0 and a Galilean advection term v*dp/dx represents the peak's motion (so the steady lag is
    -mean, with no domain-boundary artifact). Returns the final density and the mean-trait history."""
    p = p0.copy()
    f = -0.5 * k * x ** 2
    means = np.empty(steps)
    for t in range(steps):
        lap = (np.roll(p, 1) + np.roll(p, -1) - 2 * p) / dx ** 2
        fbar = np.sum(f * p) / np.sum(p)
        adv = v * (np.roll(p, -1) - np.roll(p, 1)) / (2 * dx) if v is not None else 0.0
        p = p + dt * (D * lap + adv + (f - fbar) * p)
        p = np.clip(p, 0.0, None)
        p /= np.sum(p) * dx
        means[t] = np.sum(x * p) * dx
    return p, means


def _gaussian(x, dx, x0, sig):
    g = np.exp(-(x - x0) ** 2 / (2 * sig ** 2))
    return g / (np.sum(g) * dx)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    x, dx, dt = _grid(p)
    k = p["k"]
    # (M-1) mutation-selection balance variance vs theory sqrt(2D/k)
    var_rows = []
    for D in p["Ds"]:
        pf, _ = _evolve(x, dx, dt, _gaussian(x, dx, 0.0, 1.0), D, k, p["steps"])
        mean = np.sum(x * pf) * dx
        var = np.sum((x - mean) ** 2 * pf) * dx
        var_rows.append({"D": D, "variance": round(float(var), 4),
                         "theory": round(float(np.sqrt(2 * D / k)), 4)})
    var_err = max(abs(r["variance"] - r["theory"]) for r in var_rows)
    # (M-2) adaptation from an off-peak bump: mean climbs to the peak (0)
    _, means_ad = _evolve(x, dx, dt, _gaussian(x, dx, p["x0"], 0.5), p["D_track"], k, p["steps"])
    adapt_start, adapt_end = float(means_ad[0]), float(means_ad[-1])
    # (M-3) moving optimum: lag L = v/(k sigma^2), linear in v
    sigma2 = float(np.sqrt(2 * p["D_track"] / k))
    lag_rows = []
    for v in p["vs"]:
        _, means = _evolve(x, dx, dt, _gaussian(x, dx, 0.0, 1.0), p["D_track"], k, p["steps"], v=v)
        lag = -float(means[-1])          # co-moving frame: peak at 0, population lags at negative x
        lag_rows.append({"v": v, "lag": round(lag, 4), "theory": round(v / (k * sigma2), 4),
                         "lag_over_v": round(lag / v, 4)})
    lov = [r["lag_over_v"] for r in lag_rows]
    lag_linear_err = (max(lov) - min(lov)) / (np.mean(lov) + 1e-12)     # spread of lag/v (0 = perfectly linear)
    lag_theory_err = max(abs(r["lag"] - r["theory"]) for r in lag_rows)
    return {
        "params": p, "dt": round(dt, 6), "var_rows": var_rows, "lag_rows": lag_rows,
        "variance_err": round(var_err, 4),
        "adapt_start": round(adapt_start, 3), "adapt_end": round(adapt_end, 4),
        "lag_linear_spread": round(float(lag_linear_err), 3), "lag_theory_err": round(lag_theory_err, 4),
    }


def evaluate(result, quick=False):
    checks = {
        "mutation_selection_balance_matches_theory (equilibrium variance = sqrt(2D/k), err<0.02)":
            bool(result["variance_err"] < 0.02),
        "population_climbs_to_fitness_peak (off-peak mean %.2f -> |mean|<0.05)" % result["adapt_start"]:
            bool(abs(result["adapt_end"]) < 0.05 and result["adapt_start"] > 2.0),
        "moving_optimum_lag_linear_and_matches_load (lag/v const to <5%%; lag=v/(k sigma^2))":
            bool(result["lag_linear_spread"] < 0.05 and result["lag_theory_err"] < 0.03),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e036 field adaptation (replicator-mutator / Crow-Kimura, no agents)", "tier": "measured",
        "put_in": "replicator-mutator field dp/dt = D d2p/dx2 + (f-<f>)p for a population density over a trait "
                  "axis; mutation D; a quadratic (or moving) fitness peak. NO agents / sampling",
        "emerged": ["mutation-selection balance variance vs theory sqrt(2D/k): %s"
                    % [(r["D"], r["variance"], r["theory"]) for r in result["var_rows"]],
                    "adaptation: off-peak mean %s -> %s (climbs to the peak)"
                    % (result["adapt_start"], result["adapt_end"]),
                    "moving-optimum lag vs speed (theory v/(k sigma^2)): %s"
                    % [(r["v"], r["lag"], r["theory"]) for r in result["lag_rows"]]],
        "surprises": ["the equilibrium spread and the tracking lag come out at their Crow-Kimura closed forms "
                      "with no variance and no lag put in; the lag is linear in the speed (the lag load)"],
        "persistence": "the balance distribution is the stationary state; the moving-frame lag is steady",
        "measured_numbers": {"var_rows": result["var_rows"], "lag_rows": result["lag_rows"],
                             "variance_err": result["variance_err"], "lag_theory_err": result["lag_theory_err"]},
        "not_scripted_check": "only D and the fitness landscape are set; the variance, the climb and the lag "
                              "are measured from the density field",
        "claim_tier": "measured (balance variance = sqrt(2D/k); adaptation; lag linear in speed = v/(k sigma^2)) "
                      "; interpretive (selection = advection up the gradient, mutation = diffusion) ; analogy "
                      "(evolution / adaptation)",
        "floors": ["'evolution / adaptation / niche' is analogy for a density field on a trait axis",
                   "同じ数学≠同じもの: this does NOT claim evolution IS the replicator-mutator PDE; the SAME facts "
                   "(adaptation, mutation-selection balance, lag load) emerge in a field with no agents",
                   "only the small-speed LINEAR lag regime is claimed; above a critical speed the lag runs away "
                   "(the population is lost)",
                   "(A) faithful: the field law is put in by hand, not derived"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e036 field adaptation (replicator-mutator, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e036 -- adaptation from a FIELD (replicator-mutator / Crow-Kimura, no agents) ===")
    print("  (M-1) mutation-selection balance variance vs theory sqrt(2D/k):")
    for row in r["var_rows"]:
        print("     D=%.2f | var=%.4f | theory=%.4f" % (row["D"], row["variance"], row["theory"]))
    print("  (M-2) adaptation: off-peak mean %.3f -> %.4f (peak at 0)" % (r["adapt_start"], r["adapt_end"]))
    print("  (M-3) moving-optimum lag vs speed v (theory v/(k sigma^2)):")
    for row in r["lag_rows"]:
        print("     v=%.2f | lag=%.4f | theory=%.4f | lag/v=%.3f" % (row["v"], row["lag"], row["theory"], row["lag_over_v"]))
    passed, checks = evaluate(r, quick=args.quick)
    for kk, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", kk))
    print("STATUS: %s (adaptation as a replicator-mutator field; variance & lag at their closed forms)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "adaptation.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/adaptation.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
