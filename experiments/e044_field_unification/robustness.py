#!/usr/bin/env python3
"""e044 robustness (LAW.md audit 6): the ROBUST fact is the CONTRAST -- across seeds the local public good
sustains cooperation ABOVE the no-benefit control (coop_with_good > coop_control by a clear margin). The
absolute coop fraction is param/death-rate dependent (a stated floor); with-good > control is what is robust.
Not put in. (Reduced grid/steps for the sweep.)"""
import argparse, json, os, sys

import numpy as np

_R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _R not in sys.path:
    sys.path.insert(0, _R)
from experiments.e044_field_unification import unification as U  # noqa: E402


def simulate(quick=False):
    seeds = [0, 1, 2] if quick else [0, 1, 2, 3]
    rows, n_ok = [], 0
    for s in seeds:
        p = dict(U.DEFAULT); p.update({"N": 90, "steps": 12000, "seed": s})
        tau, coop, V, topt, m = U._run(p, Pboost=p["Pboost"])
        _, coopc, _, _, mc = U._run(p, Pboost=0.0)
        cf = float(coop[m].mean()) if m.any() else 0.0
        cfc = float(coopc[mc].mean()) if mc.any() else 0.0
        ok = bool(cf > 0.5 and cf - cfc > 0.15)
        n_ok += ok
        rows.append({"seed": s, "coop_good": round(cf, 3), "coop_ctrl": round(cfc, 3),
                     "advantage": round(cf - cfc, 3), "ok": ok})
    robust = bool(n_ok == len(seeds))
    return {"rows": rows, "n_ok": n_ok, "n_seeds": len(seeds), "robust": robust}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv); r = simulate(quick=a.quick)
    print("=== e044 robustness (public good sustains cooperation ABOVE the no-benefit control, over seeds) ===")
    for c in r["rows"]:
        print("  seed=%s: coop_good=%s coop_ctrl=%s advantage=%s ok=%s" % (c["seed"], c["coop_good"], c["coop_ctrl"], c["advantage"], c["ok"]))
    print("  %s/%s seeds ok  ROBUST: %s" % (r["n_ok"], r["n_seeds"], r["robust"]))
    if not a.no_write and not a.quick:
        json.dump(r, open(os.path.join(os.path.dirname(__file__), "robustness.json"), "w"), indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
