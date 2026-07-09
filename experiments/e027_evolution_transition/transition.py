#!/usr/bin/env python3
"""e027 Stage 3 -- the major transition: when do individuals combine into a higher-level unit?

MODULE:   e027_evolution_transition (Stage 3: transition)
QUESTION: does cooperation (a public good that costs the individual) survive only with spatial
          structure, and only while the temptation to cheat is bounded?
PUT IN:   a spatial prisoner's dilemma (Nowak-May): each C/D cell plays its 8 neighbors (C-C=1,
          D-from-C=b), then copies the best-scoring neighbor's strategy. NO "spatial structure saves
          cooperation" is put in -- it is measured.
EMERGED:  (measured) well-mixed cooperation collapses (~0.00); spatial cooperation survives in clusters
          (~0.73) with positive assortment (~+0.13); and the survival is conditional -- above b~1.7 even
          clustering fails.
CLAIM TIER: measured(cooperator fraction well-mixed vs spatial, assortment) ; interpretive(a higher-level
          unit forms when individual & group interest align via spatial assortment) ; analogy(major
          transition, multicellularity).
KNOWN MATCH: Nowak-May spatial games; multilevel selection; Hamilton's rule (assortment).
STATUS:   GREEN (three gates on measured cooperator fraction and assortment).
A_OR_B:   (A) faithful. Hand input = the payoff rule + update rule; cooperation survival and clustering
          are emergent and measured.

THE TRAP (designer hit it, we avoid it): the temptation b lives in a SURVIVAL BAND -- at b~1.4
cooperation survives spatially; at b>=1.7 it collapses even with structure. Using a b outside that band
would fake or hide the transition. Well-mixed is enforced by reshuffling the grid every step. Gates are
measured fractions, not evocative labels.

Floors: this is cooperation STABILITY (a necessary condition), NOT a full major transition -- group-level
reproduction, division of labor, and conflict suppression (bottlenecks / policing) are frontier.
"Major transition / multicellularity" is analogy.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 120, "b": 1.40, "steps": 120, "b_sweep": [1.4, 1.7, 1.85, 2.0, 2.3],
           "sweep_steps": 100, "seed": 0}
QUICK = {"N": 80, "steps": 70, "b_sweep": [1.4, 1.7, 2.0], "sweep_steps": 60}

_SHIFTS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
_NB = [s for s in _SHIFTS if s != (0, 0)]


def _coop_neighbors(S):
    return sum(np.roll(np.roll(S, dx, 0), dy, 1) for (dx, dy) in _NB)


def _step(S, b):
    Cn = _coop_neighbors(S)
    score = np.where(S == 1, Cn * 1.0, Cn * b)
    ss = np.stack([np.roll(np.roll(score, dx, 0), dy, 1) for (dx, dy) in _SHIFTS])
    st = np.stack([np.roll(np.roll(S, dx, 0), dy, 1) for (dx, dy) in _SHIFTS])
    return np.take_along_axis(st, np.argmax(ss, 0)[None], 0)[0]


def _assortment(S):
    Cn = _coop_neighbors(S)
    frac_around_C = (Cn[S == 1] / 8.0).mean() if (S == 1).any() else 0.0
    return float(frac_around_C - S.mean())


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])
    N, b = p["N"], p["b"]

    # spatial
    S = (rng.random((N, N)) < 0.5).astype(int)
    for _ in range(p["steps"]):
        S = _step(S, b)
    coop_spatial = float(S.mean())
    assort = _assortment(S)

    # well-mixed: reshuffle positions each step
    S = (rng.random((N, N)) < 0.5).astype(int)
    for _ in range(p["steps"]):
        flat = S.flatten()
        rng.shuffle(flat)
        S = flat.reshape(N, N)
        S = _step(S, b)
    coop_wellmixed = float(S.mean())

    # condition: sweep the temptation b (spatial)
    sweep = []
    for bb in p["b_sweep"]:
        S = (rng.random((N, N)) < 0.5).astype(int)
        for _ in range(p["sweep_steps"]):
            S = _step(S, bb)
        sweep.append((bb, round(float(S.mean()), 3)))

    return {
        "params": p,
        "coop_wellmixed": round(coop_wellmixed, 3),
        "coop_spatial": round(coop_spatial, 3),
        "assortment": round(assort, 3),
        "b_sweep": sweep,
    }


def evaluate(result, quick=False):
    checks = {
        "well_mixed_cooperation_collapses (<0.1)":
            bool(result["coop_wellmixed"] < 0.1),
        "spatial_cooperation_survives (>0.2)":
            bool(result["coop_spatial"] > 0.2),
        "cooperators_cluster (assortment>0.1)":
            bool(result["assortment"] > 0.1),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e027 evolution transition Stage 3 (transition)", "tier": "measured",
        "put_in": "spatial prisoner's dilemma (Nowak-May): payoff C-C=1, D-from-C=b; copy the best neighbor",
        "emerged": ["cooperator fraction: well-mixed=%s (collapses), spatial=%s (survives in clusters)"
                    % (result["coop_wellmixed"], result["coop_spatial"]),
                    "assortment=%s (>0: cooperators cluster); b-sweep (spatial)=%s (collapses beyond b~1.7)"
                    % (result["assortment"], result["b_sweep"])],
        "surprises": ["spatial structure alone lets cooperation resist cheaters; well-mixed always collapses"],
        "persistence": "spatial cooperation holds while the temptation b is bounded; beyond ~1.7 it collapses",
        "measured_numbers": {"coop_wellmixed": result["coop_wellmixed"], "coop_spatial": result["coop_spatial"],
                             "assortment": result["assortment"], "b_sweep": result["b_sweep"]},
        "not_scripted_check": "cooperator fraction and assortment are measured; only the payoff + update rules are set",
        "claim_tier": "measured (cooperator fraction, assortment) ; interpretive (a higher-level unit forms when "
                      "individual & group interest align via assortment) ; analogy (major transition / multicellularity)",
        "floors": ["cooperation STABILITY (necessary condition), NOT a full major transition",
                   "group-level reproduction, division of labor, conflict suppression (bottlenecks/policing) are frontier",
                   "the temptation b sits in a survival band (collapses beyond ~1.7); 'major transition' is analogy"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e027 Stage 3: the major transition (cooperation)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e027 Stage 3 -- major transition: cooperation into a higher-level unit ===")
    print("  cooperator fraction: well-mixed=%.2f (collapses)  spatial=%.2f (survives)"
          % (r["coop_wellmixed"], r["coop_spatial"]))
    print("  assortment=%.2f (cooperators cluster)   b-sweep (spatial)=%s"
          % (r["assortment"], r["b_sweep"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (cooperation stability measured; full transition is frontier)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "transition.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/transition.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
