#!/usr/bin/env python3
"""e023 robustness (LAW.md audit 6): the order-only facts must survive the sprinkling seed. Absolute
numbers vary; what must not move is: rank recovers the hidden time (high Spearman), the directed interval
dimension is finite (~2), and symmetrizing the same pairs collapses to a small-world graph. We sweep
seeds and confirm."""

import argparse
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.causet import causal_relation, sprinkle, rank, interval_dimension  # noqa: E402
from experiments.e023_causal_action import order_time as OT                  # noqa: E402
from experiments.e023_causal_action import directed_vs_undirected as DU       # noqa: E402


def _case(seed):
    rng = np.random.default_rng(seed)
    # box Minkowski with the hidden clock kept, so rank can be checked against it
    t = rng.random(800) * 10.0
    x = rng.random(800) * 10.0
    dt = t[None, :] - t[:, None]
    dx = np.abs(x[None, :] - x[:, None])
    R = (dt > 0) & (dt > dx)
    np.fill_diagonal(R, False)
    rho_time = float(spearmanr(rank(R), t).correlation)
    d_dir = float(interval_dimension(causal_relation(sprinkle(1200, dim=2, region="diamond", seed=seed))))
    A = R | R.T
    neigh = [np.where(A[i])[0] for i in range(800)]
    growth = DU._ball_growth(neigh, int(rng.integers(0, 800)), 800, 6)
    reach2 = growth[2] / 800 if len(growth) > 2 else 1.0
    ok = rho_time > 0.8 and abs(d_dir - 2.0) < 0.3 and reach2 > 0.9
    return {"seed": seed, "rank_time_spearman": round(rho_time, 3),
            "directed_dimension": round(d_dir, 3), "reach_2hops_frac": round(reach2, 3),
            "ok": bool(ok)}


def simulate(quick=False):
    seeds = [1, 2] if quick else [1, 2, 3, 4, 5]
    cases = [_case(s) for s in seeds]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e023 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e023 robustness (order->time facts vs seed) ===")
    for c in r["cases"]:
        print("  seed=%s: Spearman=%s dim=%s reach2=%s ok=%s"
              % (c["seed"], c["rank_time_spearman"], c["directed_dimension"], c["reach_2hops_frac"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
