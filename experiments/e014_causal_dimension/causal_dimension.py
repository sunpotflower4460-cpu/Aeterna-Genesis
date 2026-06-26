#!/usr/bin/env python3
"""e014 Stage 1 -- the DIMENSION is read off the causal order alone.

We sprinkle a causal set: N points scattered uniformly (Poisson) in a d-dim
Minkowski causal interval (the diamond between two timelike-separated points).
Then we THROW AWAY the coordinates and keep only the causal order -- which pairs
are timelike (causally) related. The Myrheim-Meyer relation links the fraction of
related pairs r to the dimension:

    r(d) = Gamma(d+1) Gamma(d/2) / ( 2 Gamma(3d/2) )

Inverting the MEASURED r gives the Myrheim-Meyer dimension d_MM, with NO metric
used -- only "a is before b". We recover d=2,3,4 to ~1%.

Designer's trap (recorded): the correct denominator is 2, not 4. A related pair
is counted ONCE (both directions are the SAME relation); the denominator-4 form
is the one-direction probability and reads the fraction 2x too small (d=2 would
give r=0.25 instead of 0.5). The lesson: suspect your own code first -- but here
the check showed the *theory formula* (as first written) was the error. Suspect
both. We pin r(2)=0.5 exactly as the guard.

MODULE:   e014_causal_dimension
QUESTION: Can the spacetime dimension be recovered from the causal ORDER alone (no coordinates)?
PUT IN:   a Poisson sprinkling in a d-dim Minkowski interval; then ONLY the causal relation a<b. The dimension is NOT put in as a label.
EMERGED:  (measured) Myrheim-Meyer dimension from the relation fraction recovers d=2,3,4 to ~1%.
CLAIM TIER: measured(d_MM(d) ~ d, denominator-2 formula) ; interpretive(causal order encodes dimension).
KNOWN MATCH: Myrheim 1978 / Meyer 1988 (causal-set dimension); CDT/causal-set programme.
STATUS:   GREEN (d_MM recovers 2,3,4; kinematic -- dynamic geometry inherited from AJL, not re-run).
A_OR_B:   (A) faithful kinematics. Hand input = causal order from a sprinkling; the dimension is read out, not put in.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.optimize import brentq
from scipy.special import gammaln

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"dims": [2, 3, 4], "N": 2000, "seeds": [0, 1, 2, 3]}
QUICK = {"dims": [2, 3], "N": 800, "seeds": [0, 1]}


def relation_fraction_theory(d):
    """Myrheim-Meyer expected related-pair fraction in a d-dim interval (denom 2)."""
    return float(np.exp(gammaln(d + 1) + gammaln(d / 2.0)
                        - np.log(2.0) - gammaln(3.0 * d / 2.0)))


def sprinkle_interval(d, N, rng):
    """N points uniform in the unit causal interval of d-dim Minkowski (1 time)."""
    T, X = [], []
    while len(T) < N:
        m = (N - len(T)) * 4 + 16
        t = rng.uniform(0.0, 1.0, size=m)
        xs = (rng.uniform(-0.5, 0.5, size=(m, d - 1)) if d > 1
              else np.zeros((m, 0)))
        rx = np.sqrt((xs ** 2).sum(1)) if d > 1 else np.zeros(m)
        keep = (t > rx) & ((1 - t) > rx)            # inside future(0) AND past(apex)
        for ti, xi in zip(t[keep], xs[keep]):
            T.append(ti)
            X.append(xi)
            if len(T) >= N:
                break
    return np.array(T), np.array(X)


def relation_fraction_measured(T, X):
    """Fraction of unordered pairs that are timelike (causally) related."""
    N = len(T)
    R = 0
    for i in range(N):
        dt = T[i + 1:] - T[i]
        if X.shape[1] > 0:
            dx2 = ((X[i + 1:] - X[i]) ** 2).sum(1)
        else:
            dx2 = np.zeros(N - i - 1)
        R += int(np.count_nonzero(dt ** 2 > dx2))
    return R / (N * (N - 1) / 2.0)


def dim_from_fraction(r):
    """Invert r(d) numerically for the Myrheim-Meyer dimension."""
    f = lambda d: relation_fraction_theory(d) - r
    try:
        return float(brentq(f, 1.0, 9.0))
    except ValueError:
        return float("nan")


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for d in p["dims"]:
        rs = []
        for seed in p["seeds"]:
            rng = np.random.default_rng(seed)
            T, X = sprinkle_interval(d, p["N"], rng)
            rs.append(relation_fraction_measured(T, X))
        r_mean = float(np.mean(rs))
        d_mm = dim_from_fraction(r_mean)
        rows.append({"d_true": d, "r_theory": round(relation_fraction_theory(d), 4),
                     "r_measured": round(r_mean, 4), "r_std": round(float(np.std(rs)), 4),
                     "d_MM": round(d_mm, 3), "abs_err": round(abs(d_mm - d), 3)})
    return {"params": p, "rows": rows,
            "denominator2_check_r2": round(relation_fraction_theory(2), 4),
            "max_abs_err": round(max(r["abs_err"] for r in rows), 3)}


EXPECT = {"err_max": 0.1}


def evaluate(result, quick=False):
    checks = {
        "d_MM_recovers_d(<0.1)": result["max_abs_err"] < EXPECT["err_max"],
        "denominator2(r(2)=0.5)": abs(result["denominator2_check_r2"] - 0.5) < 1e-6,
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e014 causal dimension (Myrheim-Meyer)", "tier": "measured",
        "put_in": "Poisson sprinkling in a d-dim Minkowski interval; then ONLY the causal order a<b",
        "emerged": ["the dimension read from the relation fraction: " +
                    ", ".join("d=%d->%.2f" % (r["d_true"], r["d_MM"]) for r in result["rows"])],
        "surprises": ["dimension recovered with NO coordinates -- causal order alone carries it"],
        "persistence": "kinematic (a property of the order); dynamic geometry inherited from AJL",
        "measured_numbers": {"rows": result["rows"]},
        "not_scripted_check": "coordinates are discarded before measuring; the dimension is read out, not labelled",
        "claim_tier": "measured (d_MM(d)~d, denominator-2) ; interpretive (causal order encodes dimension)",
        "floors": ["kinematic: given causal order -> dimension; dynamic self-organization of geometry is AJL (inherited, not re-run)",
                   "Myrheim-Meyer is a Hausdorff-type dimension (cf. spectral dimension, e014 Stage 2)"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e014 causal dimension")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e014 causal -> dimension (Myrheim-Meyer, no coordinates) ===")
    for row in r["rows"]:
        print("  d=%d: r_theory=%.4f r_measured=%.4f -> d_MM=%.3f (err %.3f)"
              % (row["d_true"], row["r_theory"], row["r_measured"], row["d_MM"], row["abs_err"]))
    print("  denominator-2 guard r(2)=%.4f (must be 0.5) ; max abs err=%.3f"
          % (r["denominator2_check_r2"], r["max_abs_err"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (causal order recovers the dimension)" % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.dirname(__file__)
        with open(os.path.join(out, "result.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote result.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
