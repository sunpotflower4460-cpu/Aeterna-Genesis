#!/usr/bin/env python3
"""e043 robustness (LAW.md audit 6): the differentiated adapted body self-organizes across seeds -- from a
uniform start, division fills the field, cells adapt to the local morphogen optimum (corr>0.55) and split into
ordered left->right trait domains (contrast>0.25). Not put in. (Reduced grid/steps for the sweep.)"""
import argparse, json, os, sys

import numpy as np

_R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _R not in sys.path:
    sys.path.insert(0, _R)
from experiments.e043_field_universe import universe as U  # noqa: E402


def simulate(quick=False):
    seeds = [0, 1, 2] if quick else [0, 1, 2, 3]
    rows, n_ok = [], 0
    for s in seeds:
        p = dict(U.DEFAULT); p.update({"N": 90, "steps": 12000, "seed": s})
        tau, V, topt, _ = U._run(p)
        m = V > 0.15
        corr = float(np.corrcoef(tau[m], topt[m])[0, 1]) if m.sum() > 4 and tau[m].std() > 1e-6 else 0.0
        left = float(tau[(topt < 0.33) & m].mean()); right = float(tau[(topt >= 0.66) & m].mean())
        ok = bool(m.mean() > 0.25 and corr > 0.55 and (right - left) > 0.25 and left < right)
        n_ok += ok
        rows.append({"seed": s, "occupied": round(float(m.mean()), 3), "corr": round(corr, 3),
                     "contrast": round(right - left, 3), "ok": ok})
    robust = bool(n_ok == len(seeds))
    return {"rows": rows, "n_ok": n_ok, "n_seeds": len(seeds), "robust": robust}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv); r = simulate(quick=a.quick)
    print("=== e043 robustness (differentiated body over seeds) ===")
    for c in r["rows"]:
        print("  seed=%s: occupied=%s corr=%s contrast=%s ok=%s" % (c["seed"], c["occupied"], c["corr"], c["contrast"], c["ok"]))
    print("  %s/%s seeds ok  ROBUST: %s" % (r["n_ok"], r["n_seeds"], r["robust"]))
    if not a.no_write and not a.quick:
        json.dump(r, open(os.path.join(os.path.dirname(__file__), "robustness.json"), "w"), indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
