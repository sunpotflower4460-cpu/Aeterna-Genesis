#!/usr/bin/env python3
"""e036 robustness (LAW.md audit 6): the closed-form matches must survive a different peak curvature k and
mutation D. What must not move: the equilibrium variance stays at sqrt(2D/k) and the moving-optimum lag stays
at v/(k sigma^2) -- so the NUMBERS shift with k,D but always sit on their theoretical curves. Not put in."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e036_field_adaptation import adaptation as AD  # noqa: E402


def _case(k, D):
    p = dict(AD.DEFAULT)
    p.update({"k": k, "D_track": D, "Ds": [D], "vs": [0.1], "steps": 30000})
    x, dx, dt = AD._grid(p)
    pf, _ = AD._evolve(x, dx, dt, AD._gaussian(x, dx, 0.0, 1.0), D, k, p["steps"])
    mean = np.sum(x * pf) * dx
    var = float(np.sum((x - mean) ** 2 * pf) * dx)
    var_err = abs(var - np.sqrt(2 * D / k))
    sigma2 = np.sqrt(2 * D / k)
    _, means = AD._evolve(x, dx, dt, AD._gaussian(x, dx, 0.0, 1.0), D, k, p["steps"], v=0.1)
    lag = -float(means[-1])
    lag_err = abs(lag - 0.1 / (k * sigma2))
    ok = var_err < 0.02 and lag_err < 0.03
    return {"k": k, "D": D, "var": round(var, 4), "var_theory": round(float(np.sqrt(2 * D / k)), 4),
            "lag": round(lag, 4), "lag_theory": round(float(0.1 / (k * sigma2)), 4), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(1.0, 0.1)] if quick else [_case(1.0, 0.1), _case(2.0, 0.1), _case(1.0, 0.05)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e036 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e036 robustness (variance=sqrt(2D/k) and lag=v/(k sigma^2) under shifts of k, D) ===")
    for c in r["cases"]:
        print("  k=%s D=%s: var=%s (th %s) lag=%s (th %s) ok=%s"
              % (c["k"], c["D"], c["var"], c["var_theory"], c["lag"], c["lag_theory"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
