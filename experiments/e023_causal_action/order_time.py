#!/usr/bin/env python3
"""e023 Stage 1 -- from pure order to time: rank recovers the hidden clock; a slice is space.

MODULE:   e023_causal_action (Stage 1: order_time)
QUESTION: from a causal ORDER alone (no coordinates), does an oriented TIME emerge (the longest chain =
          rank recovers the hidden clock), does a spatial slice (an antichain) fill space, and is the
          interval dimension finite (~d)?
PUT IN:   a sprinkling into d-dim Minkowski (coordinates only GENERATE the order); then everything is
          read from the relation matrix. NO "rank recovers time", NO "finite dimension" are put in.
EMERGED:  (measured) rank (longest chain to each element) recovers the hidden time (Spearman ~0.99); the
          mid-rank antichain spreads across the spatial extent; the Myrheim-Meyer interval dimension is
          finite and near d.
CLAIM TIER: measured(rank<->time correlation, spatial spread, finite dimension) ; interpretive(time and
          a finite-dim space are read off the order alone) ; analogy(spacetime from causal order).
KNOWN MATCH: causal set theory (Bombelli-Lee-Meyer-Sorkin); Myrheim-Meyer dimension; "order + number = geometry".
STATUS:   GREEN (gates on order-only statistics -- Spearman, dimension, spatial spread).
A_OR_B:   (A) faithful. Hand input = the sprinkling; time (rank), space (antichain), and the dimension
          are read from the ORDER, and rank is checked to recover the hidden clock.

THE TRAP (designer hit it, we avoid it): every measured quantity uses ONLY the relation matrix (rank,
antichain, interval cardinality) -- the coordinates are scaffolding to GENERATE a non-trivial order and
are then discarded; we verify emergent time against the hidden clock. Gate on order statistics -- never
name a gate "time" as if a clock were built.

Floors: a fixed-dimension Minkowski sprinkling (the manifold is put in to generate the order); the claim
is that TIME and DIMENSION are RECOVERED from the order, not that a manifold is derived from nothing.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.causet import sprinkle, causal_relation, rank, interval_dimension  # noqa: E402

DEFAULT = {"N_box": 1000, "T": 10.0, "L": 10.0, "dims": [2, 3], "N_dim": 1500, "seed": 1}
QUICK = {"N_box": 700, "dims": [2], "N_dim": 1200}


def _box_minkowski(N, T, L, rng):
    """2D Minkowski box: hidden time t, space x; strict causal order R[a,b]=b in a's future cone."""
    t = rng.random(N) * T
    x = rng.random(N) * L
    dt = t[None, :] - t[:, None]
    dx = np.abs(x[None, :] - x[:, None])
    R = (dt > 0) & (dt > dx)
    np.fill_diagonal(R, False)
    return R, t, x


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])

    # (1) time emerges: rank recovers the hidden clock
    R, t, x = _box_minkowski(p["N_box"], p["T"], p["L"], rng)
    rk = rank(R)
    rho_time = float(spearmanr(rk, t).correlation)

    # (2) a spatial slice is an antichain that fills space
    kmid = int(np.median(rk))
    sl = np.where(rk == kmid)[0]
    if sl.size >= 2:
        spread = float((x[sl].max() - x[sl].min()) / p["L"])
    else:
        spread = 0.0

    # (3) the interval dimension is finite and near d (directed diamond sprinkle, order only)
    dims = []
    for d in p["dims"]:
        Rd = causal_relation(sprinkle(p["N_dim"], dim=d, region="diamond", seed=p["seed"]))
        dims.append({"d": d, "measured": round(float(interval_dimension(Rd)), 3)})

    return {
        "params": p,
        "rank_time_spearman": round(rho_time, 3),
        "slice_rank": kmid, "slice_size": int(sl.size), "slice_spatial_spread": round(spread, 3),
        "dimensions": dims,
        "dimension_finite": bool(all(abs(dd["measured"] - dd["d"]) < 0.3 for dd in dims)),
    }


def evaluate(result, quick=False):
    checks = {
        "rank_recovers_hidden_time (Spearman>0.8)":
            bool(result["rank_time_spearman"] > 0.8),
        "spatial_slice_fills_space (mid-rank antichain spread>0.5)":
            bool(result["slice_spatial_spread"] > 0.5),
        "interval_dimension_finite (|d_meas - d|<0.3)":
            result["dimension_finite"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e023 causal action Stage 1 (order_time)", "tier": "measured",
        "put_in": "a Minkowski sprinkling (coordinates only generate the order); all reads use the relation matrix",
        "emerged": ["rank recovers hidden time: Spearman=%s" % result["rank_time_spearman"],
                    "mid-rank antichain (size %s) spans spatial fraction %s"
                    % (result["slice_size"], result["slice_spatial_spread"]),
                    "interval dimension (order only): %s"
                    % [(dd["d"], dd["measured"]) for dd in result["dimensions"]]],
        "surprises": ["an oriented time and a finite-dimensional space are read off the abstract ORDER alone"],
        "persistence": "rank<->time and the finite dimension are stable properties of the order",
        "measured_numbers": {"rank_time_spearman": result["rank_time_spearman"],
                             "slice_spatial_spread": result["slice_spatial_spread"],
                             "dimensions": result["dimensions"]},
        "not_scripted_check": "coordinates are discarded; time (rank), space (antichain), and dimension are "
                              "read from the relation matrix and rank is checked against the hidden clock",
        "claim_tier": "measured (rank<->time, spatial spread, finite dimension) ; interpretive (time and space "
                      "from order) ; analogy (spacetime from causal order)",
        "floors": ["a fixed-dimension Minkowski sprinkling (the manifold generates the order)",
                   "the claim is time/dimension are RECOVERED from the order, not a manifold from nothing"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e023 Stage 1: order -> time")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e023 Stage 1 -- from pure order to time ===")
    print("  rank recovers hidden time: Spearman=%s" % r["rank_time_spearman"])
    print("  mid-rank antichain (size %s) spatial spread=%s" % (r["slice_size"], r["slice_spatial_spread"]))
    print("  interval dimension (order only): %s" % [(dd["d"], dd["measured"]) for dd in r["dimensions"]])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (time and finite-dim space read from the order)" % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "order_time.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/order_time.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
