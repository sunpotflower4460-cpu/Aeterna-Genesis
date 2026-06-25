#!/usr/bin/env python3
"""Robustness sweep for e008 (LAW.md audit 6).

The Kibble-Zurek power law N ~ tau_Q^{-b} must survive changes of lattice size
L and damping gamma (its EXPONENT is protocol-dependent -- honestly noted -- but
the POWER LAW itself, the negative slope, and net-winding ~ 0 must persist). We
also confirm net winding stays ~0 across conditions.

Writes robustness.json and prints a table copied into AUDIT.md.
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from run import DEFAULT, kz_scaling  # noqa: E402


def main():
    base = dict(DEFAULT)
    base["tauQ_list"] = [50, 100, 200, 400, 800]
    base["seeds"] = [1, 2]
    cases = []
    print(f"{'variant':>16} | {'b':>6} {'R2':>6} {'net|w|':>7} | result")
    print("-" * 50)
    for label, over in [("L=128", {"L": 128}), ("L=192", {"L": 192}),
                        ("L=256", {"L": 256}), ("gamma=0.2", {"gamma": 0.2}),
                        ("gamma=0.5", {"gamma": 0.5})]:
        p = dict(base)
        p.update(over)
        rows, b, r2, _extra = kz_scaling(p, p["seeds"], p["tauQ_list"])
        netw = sum(r["net_winding_absmean"] for r in rows) / len(rows)
        ok = (0.1 < b < 1.0) and r2 > 0.85 and netw < 25
        cases.append({"variant": label, "b": b, "r2": r2,
                      "net_winding_absmean": netw, "pass": ok})
        print(f"{label:>16} | {b:>6.3f} {r2:>6.3f} {netw:>7.2f} | "
              f"{'PASS' if ok else 'FAIL'}")
    print("-" * 50)
    allp = all(c["pass"] for c in cases)
    bs = [c["b"] for c in cases]
    print("KZ power law holds for every variant: %s" % allp)
    print("exponent b range %.3f-%.3f (protocol-dependent, honestly noted)"
          % (min(bs), max(bs)))
    out = {"cases": cases, "all_pass": allp,
           "b_min": min(bs), "b_max": max(bs)}
    with open(os.path.join(_THIS_DIR, "robustness.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote robustness.json")
    return 0 if allp else 1


if __name__ == "__main__":
    sys.exit(main())
