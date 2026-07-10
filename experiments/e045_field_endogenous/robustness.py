#!/usr/bin/env python3
"""e045 robustness (LAW.md audit 6): the NEGATIVE result is robust across seeds -- with a survivable penalty the
endogenous field's local trait variance is NEVER meaningfully above the neutral control (excess <= 0.001 for
every seed). The endogenous route does not self-generate diversity, regardless of the initial condition. Not
put in. (Reduced grid/steps for the sweep.)"""
import argparse, json, os, sys

_R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _R not in sys.path:
    sys.path.insert(0, _R)
from experiments.e045_field_endogenous import endogenous as E  # noqa: E402


def simulate(quick=False):
    seeds = [0, 1, 2] if quick else [0, 1, 2, 3]
    rows, n_negative = [], 0
    for s in seeds:
        p = dict(E.DEFAULT); p.update({"N": 84, "steps": 8000, "seed": s})
        tau, occ = E._run(p, comp=p["comp"], ceil=p["ceil"])
        taun, occn = E._run(p, comp=0.0, ceil=p["ceil"])
        lv = E._local_var(tau, occ); lvn = E._local_var(taun, occn)
        excess = lv - lvn
        # NEGATIVE holds iff both alive AND endogenous does not beat neutral
        neg = bool(occ.mean() > 0.15 and occn.mean() > 0.15 and excess <= 0.001)
        n_negative += neg
        rows.append({"seed": s, "endo_local_var": round(lv, 4), "neutral_local_var": round(lvn, 4),
                     "excess": round(excess, 4), "negative_holds": neg})
    robust = bool(n_negative == len(seeds))
    return {"rows": rows, "n_negative": n_negative, "n_seeds": len(seeds), "robust": robust}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv); r = simulate(quick=a.quick)
    print("=== e045 robustness (the NEGATIVE holds over seeds: endogenous never beats neutral) ===")
    for c in r["rows"]:
        print("  seed=%s: endo_lv=%s neutral_lv=%s excess=%s negative_holds=%s"
              % (c["seed"], c["endo_local_var"], c["neutral_local_var"], c["excess"], c["negative_holds"]))
    print("  %s/%s seeds confirm the negative  ROBUST: %s" % (r["n_negative"], r["n_seeds"], r["robust"]))
    if not a.no_write and not a.quick:
        json.dump(r, open(os.path.join(os.path.dirname(__file__), "robustness.json"), "w"), indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
