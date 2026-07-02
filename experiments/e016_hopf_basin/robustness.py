#!/usr/bin/env python3
"""e016 robustness (LAW.md audit 6): the size law size~sqrt(c4) with Q_H~1 must be
kappa-INDEPENDENT (the stabiliser strength is a numerical knob, not physics). We
sweep kappa over a wide range and confirm each c4 still holds Q_H~1 and the fit
stays tight (R^2, CV). Absolute k may shift with kappa; the LAW must not."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e016_hopf_basin import hopf_basin as e016  # noqa: E402


def _case(kappa, L, c4_list, n_steps):
    p = dict(e016.DEFAULT)
    p.update({"kappa": kappa, "L": L, "n_steps": n_steps, "c4_list": c4_list})
    sizes, held = [], []
    for c4 in c4_list:
        ss = p["start_frac"] * np.sqrt(c4)
        r = e016.flow_converge(p, c4, ss)
        held.append(r["Q_H_final"] > 0.85)
        sizes.append(r["size_final"])
    keep = [(c, s) for c, s, h in zip(c4_list, sizes, held) if h]
    if len(keep) >= 2:
        k, r2, cv, _ = e016._fit_sqrt([c for c, _ in keep], [s for _, s in keep])
    else:
        k, r2, cv = 0.0, 0.0, 1.0
    return {"kappa": kappa, "L": L, "n_held": sum(held), "fit_k": round(k, 3),
            "R2": round(r2, 3), "CV": round(cv, 3),
            "pass": bool(sum(held) >= 2 and r2 > 0.90 and cv < 0.12)}


def run_sweep(quick=False):
    if quick:
        cases = [(20.0, 40, [16.0, 20.0, 25.0], 350), (80.0, 40, [16.0, 20.0, 25.0], 350)]
    else:
        cases = [(20.0, 48, [16.0, 20.0, 25.0, 30.0], 500),
                 (40.0, 48, [16.0, 20.0, 25.0, 30.0], 500),
                 (80.0, 48, [16.0, 20.0, 25.0, 30.0], 500)]
    return [_case(*c) for c in cases]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e016 robustness (kappa-independence)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    rows = run_sweep(quick=args.quick)
    for r in rows:
        print("  kappa=%5.1f L=%d: %d held  k=%.3f R2=%.3f CV=%.3f  %s"
              % (r["kappa"], r["L"], r["n_held"], r["fit_k"], r["R2"], r["CV"],
                 "PASS" if r["pass"] else "FAIL"))
    npass = sum(r["pass"] for r in rows)
    ok = npass == len(rows)
    print("ROBUSTNESS: %s (%d/%d cases PASS; kappa-independent size law)"
          % ("GREEN" if ok else "MIXED", npass, len(rows)))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump({"cases": rows}, f, indent=2)
        print("wrote robustness.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
