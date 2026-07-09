#!/usr/bin/env python3
"""e023 Stage 2 -- orientation makes spacetime: directed = finite-dim + time; undirected = small-world mush.

MODULE:   e023_causal_action (Stage 2: directed_vs_undirected)
QUESTION: does ORIENTATION (keeping the causal order) give a finite-dimensional space with an acyclic
          time, while symmetrizing the SAME pairs collapses to a small-world graph (dimension diverges,
          cycles destroy time)?
PUT IN:   one sprinkling; the SAME set of causal pairs, read with orientation (partial order) and without
          (symmetrized graph). NO "undirected is small-world", NO "orientation gives finite dimension".
EMERGED:  (measured) the directed order has a finite Myrheim-Meyer dimension (~2) and is acyclic (a
          time); symmetrizing the same pairs reaches almost all N within ~2 graph hops (small-world =
          dimension diverges) and creates 3-cycles (no acyclic order = no time).
CLAIM TIER: measured(directed finite dimension; undirected small-world reach; undirected cycles) ;
          interpretive(orientation is what makes spacetime -- a manifold-like space plus an arrow) ;
          analogy(the causal arrow builds spacetime).
KNOWN MATCH: causal set theory; the small-world / non-manifold collapse of undirected random graphs.
STATUS:   GREEN (gates on graph reach and cycle count -- physical/combinatorial quantities).
A_OR_B:   (A) faithful. Hand input = one sprinkling; the directed vs undirected contrast is emergent and
          measured from the same pairs.

THE TRAP (designer hit it, we avoid it): both readings use the SAME causal pairs -- only the orientation
differs; the small-world collapse and the cycles are measured, not imposed. Gate on graph reach / cycle
count -- never name a gate "time".

Floors: a fixed-dimension Minkowski sprinkling generates the order; the contrast is about ORIENTATION of
a given pair-set, not deriving a manifold from nothing.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.causet import interval_dimension  # noqa: E402

DEFAULT = {"N": 1000, "T": 10.0, "L": 10.0, "n_ball_seeds": 5, "rmax": 6, "seed": 1}
QUICK = {"N": 700}


def _box_minkowski(N, T, L, rng):
    t = rng.random(N) * T
    x = rng.random(N) * L
    dt = t[None, :] - t[:, None]
    dx = np.abs(x[None, :] - x[:, None])
    R = (dt > 0) & (dt > dx)
    np.fill_diagonal(R, False)
    return R


def _ball_growth(neigh, seed, N, rmax):
    dist = {seed: 0}
    frontier = [seed]
    counts = [1]
    for _ in range(1, rmax + 1):
        nxt = []
        for u in frontier:
            for v in neigh[u]:
                if v not in dist:
                    dist[v] = 1
                    nxt.append(v)
        frontier = nxt
        counts.append(len(dist))
        if len(dist) == N:
            break
    return counts


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])
    N = p["N"]
    R = _box_minkowski(N, p["T"], p["L"], rng)

    # directed: finite Myrheim-Meyer dimension
    d_directed = float(interval_dimension(R))

    # undirected: symmetrize the SAME pairs
    A = R | R.T
    neigh = [np.where(A[i])[0] for i in range(N)]
    ball_seeds = rng.integers(0, N, p["n_ball_seeds"])
    growths = [_ball_growth(neigh, int(s), N, p["rmax"]) for s in ball_seeds]
    maxlen = max(len(g) for g in growths)
    growths = [g + [N] * (maxlen - len(g)) for g in growths]
    mean_growth = np.array(growths).mean(0)
    # hops to reach 90% of N (small-world if very few)
    hops_to_90 = int(np.argmax(mean_growth >= 0.9 * N))
    reach_2hops = float(mean_growth[2] / N) if len(mean_growth) > 2 else 0.0

    # undirected cycles: 3-cycles (triangles) exist -> no acyclic order -> no time
    Ai = A.astype(np.int64)
    triangles = int(np.trace(Ai @ Ai @ Ai) // 6)

    return {
        "params": p,
        "directed_dimension": round(d_directed, 3),
        "undirected_mean_ball": [round(float(v), 0) for v in mean_growth[:6]],
        "undirected_hops_to_90pct": hops_to_90, "undirected_reach_2hops_frac": round(reach_2hops, 3),
        "undirected_triangles": triangles,
    }


def evaluate(result, quick=False):
    checks = {
        "directed_dimension_finite (|d-2|<0.3)":
            bool(abs(result["directed_dimension"] - 2.0) < 0.3),
        "undirected_collapses_smallworld (>=90% N within 2 hops)":
            bool(result["undirected_hops_to_90pct"] <= 2 and result["undirected_reach_2hops_frac"] > 0.9),
        "undirected_has_cycles (symmetrizing makes triangles -> no time)":
            bool(result["undirected_triangles"] > 0),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e023 causal action Stage 2 (directed vs undirected)", "tier": "measured",
        "put_in": "one Minkowski sprinkling; the SAME causal pairs read with vs without orientation",
        "emerged": ["directed Myrheim-Meyer dimension = %s (finite)" % result["directed_dimension"],
                    "undirected ball growth N(r) = %s (reaches ~all N in %s hops)"
                    % (result["undirected_mean_ball"], result["undirected_hops_to_90pct"]),
                    "undirected triangles = %s (cycles -> no acyclic order -> no time)"
                    % result["undirected_triangles"]],
        "surprises": ["removing only the ORIENTATION collapses a finite-dim space to a small-world mush with no time"],
        "persistence": "the directed order keeps a finite dimension + arrow; the undirected graph is small-world",
        "measured_numbers": {"directed_dimension": result["directed_dimension"],
                             "undirected_mean_ball": result["undirected_mean_ball"],
                             "undirected_hops_to_90pct": result["undirected_hops_to_90pct"],
                             "undirected_triangles": result["undirected_triangles"]},
        "not_scripted_check": "both readings use the SAME pairs; the small-world reach and cycles are measured",
        "claim_tier": "measured (directed finite dim; undirected small-world; cycles) ; interpretive (orientation "
                      "makes spacetime) ; analogy (the causal arrow builds spacetime)",
        "floors": ["a fixed-dimension Minkowski sprinkling generates the order; the contrast is about ORIENTATION",
                   "not a derivation of a manifold from nothing"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e023 Stage 2: directed vs undirected")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e023 Stage 2 -- orientation makes spacetime ===")
    print("  directed Myrheim-Meyer dimension = %s (finite)" % r["directed_dimension"])
    print("  undirected ball growth N(r) = %s (reaches ~all N in %s hops)"
          % (r["undirected_mean_ball"], r["undirected_hops_to_90pct"]))
    print("  undirected triangles = %s (cycles -> no time)" % r["undirected_triangles"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (directed=finite-dim+time; undirected=small-world mush)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "directed_vs_undirected.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/directed_vs_undirected.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
