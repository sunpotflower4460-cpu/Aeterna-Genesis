#!/usr/bin/env python3
"""e012 Stage 1 (static) -- a Q_H=1 hopfion, its energies, and the Derrick cliff.

We BUILD a charge-1 hopfion n: R^3 -> S^2 from the Hopf map (core/hopf), then
MEASURE, not assert:
  * Q_H  -- the Whitehead Hopf invariant (spectral B = curl A); it must come out
            an INTEGER (~1) although nothing in the construction rounds it.
  * E2   -- the gradient (sigma-model) energy.
  * E4   -- the Skyrme (quartic, "third") energy.
  * the Derrick landscape E(L) = L*c2*E2 + c4*E4/L under a rescaling x -> x/L:
      - c4 = 0 (bare gradient): E(L) = L*c2*E2 -> minimised at L -> 0 = COLLAPSE
        (this is WHY the bare-GPE hopfion of e009 shrinks).
      - c4 > 0 ("the third"):  a finite minimiser L* = sqrt(c4 E4 / (c2 E2)) =
        a STABLE size. The higher-derivative term stops Derrick collapse.

So: the "third" (a quartic, higher-derivative term) converts collapse into a
finite stable size. That is the STATIC half of the e012 claim; hopfion_flow.py
shows it DYNAMICALLY (gradient flow).

Floors: the ABSOLUTE E2, E4 are scheme/resolution (dx) dependent -- they grow as
the core is resolved finer; the ROBUST statements are Q_H (integer, topological)
and the Derrick SHAPE (collapse vs finite L*, and L* ~ sqrt(c4)). Fixed lattice.
"Particle" is analogy; we did not make an electron.

MODULE:   e012_hopf_stabilization (Stage 1: static Q_H + Derrick)
QUESTION: Does a higher-derivative 'third' turn Derrick collapse into a finite stable size?
PUT IN:   Q_H=1 hopfion field n:R^3->S^2; Faddeev-Skyrme E=c2*E2 + c4*E4. No target size is put in.
EMERGED:  (measured) Q_H~1 (integer); bare (c4=0) collapses, c4>0 has finite L*=sqrt(c4 E4/E2).
CLAIM TIER: measured(Q_H, E2, E4, Derrick L*) ; interpretive('third'=stabiliser) ; analogy(particle).
KNOWN MATCH: Derrick 1964; Faddeev-Niemi hopfion; e009 (bare-GPE hopfion shrinks).
STATUS:   GREEN (Q_H integer + Derrick landscape measured; absolute energies are a resolution floor).
A_OR_B:   (A) faithful. Hand input = field manifold S^2 + Faddeev-Skyrme energy. Lattice = space, given.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import hopf  # noqa: E402

DEFAULT = {"L": 96, "box": 12.0, "scale": 1.0, "c4_list": [0.0, 1.0, 4.0, 9.0]}
QUICK = {"L": 48, "box": 12.0, "scale": 1.0, "c4_list": [0.0, 4.0]}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    n, dx = hopf.hopfion_field(p["L"], p["scale"], p["box"])
    dn = hopf.central_diff(n, dx)
    E2 = hopf.energy2(dn, dx)
    F = hopf.skyrme_F(n, dn)
    E4 = hopf.energy4(F, dx)
    Q = hopf.hopf_charge(n, dx)
    # Derrick landscape for each c4
    derrick = []
    lams = np.linspace(0.2, 3.0, 29)
    for c4 in p["c4_list"]:
        _, E, Lstar = hopf.derrick_curve(E2, E4, c4, lams=lams)
        i = int(np.argmin(E))
        derrick.append({"c4": c4, "L_star_formula": round(Lstar, 3),
                        "L_argmin_grid": round(float(lams[i]), 3),
                        "collapses": bool(i == 0),
                        "E_min": round(float(E[i]), 2),
                        "E_at_smallest_L": round(float(E[0]), 2)})
    return {"params": p, "dx": round(dx, 4),
            "Q_H": round(Q, 4), "E2": round(E2, 2), "E4": round(E4, 2),
            "E4_over_E2": round(E4 / E2, 4), "derrick": derrick,
            "lams": [round(float(x), 3) for x in lams]}


def evaluate(result, quick=False):
    d = {x["c4"]: x for x in result["derrick"]}
    bare = d.get(0.0)
    third = next((x for x in result["derrick"] if x["c4"] > 0), None)
    checks = {
        "Q_H_is_integer_~1": abs(result["Q_H"] - 1.0) < 0.05,
        "bare_collapses(c4=0, min at L->0)": bool(bare is not None and bare["collapses"]),
        "third_stabilises(c4>0, finite L*)":
            bool(third is not None and not third["collapses"]
                 and third["L_star_formula"] > 0),
        "Lstar_grows_with_c4":
            _lstar_increases([x for x in result["derrick"] if x["c4"] > 0]),
    }
    return all(checks.values()), checks


def _lstar_increases(rows):
    ls = [r["L_star_formula"] for r in sorted(rows, key=lambda r: r["c4"])]
    return all(ls[i] < ls[i + 1] for i in range(len(ls) - 1)) if len(ls) > 1 else True


def _atlas(result):
    third = next((x for x in result["derrick"] if x["c4"] > 0), {})
    return [{
        "experiment": "e012 static hopfion", "tier": "measured",
        "put_in": "Q_H=1 hopfion (Hopf map) + Faddeev-Skyrme energy; no target size",
        "emerged": ["Q_H = %.3f (an integer, though nothing rounds it)" % result["Q_H"],
                    "bare gradient energy collapses (Derrick); the quartic 'third' gives a finite L*"],
        "surprises": ["the Hopf invariant comes out quantised from a smooth construction"],
        "persistence": "static; the dynamic confirmation is hopfion_flow.py",
        "measured_numbers": {"Q_H": result["Q_H"], "E2": result["E2"], "E4": result["E4"],
                             "L_star(c4=%.0f)" % third.get("c4", 0): third.get("L_star_formula")},
        "not_scripted_check": "Q_H from B=curl A (Whitehead); E2,E4 from the field; no size imposed",
        "claim_tier": "measured (Q_H, E2, E4, Derrick L*) ; interpretive ('third'=stabiliser) ; analogy (particle)",
        "floors": ["absolute E2,E4 are resolution(dx)-dependent; Q_H and Derrick shape are robust",
                   "fixed lattice; 'particle' is analogy, not an electron"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e012 static hopfion")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e012 static hopfion (Q_H, energies, Derrick) ===")
    print("  Q_H = %.4f (integer => topological)   E2 = %.1f   E4 = %.1f   E4/E2 = %.3f"
          % (r["Q_H"], r["E2"], r["E4"], r["E4_over_E2"]))
    print("  Derrick landscape E(L) = L*E2 + c4*E4/L:")
    for x in r["derrick"]:
        tag = "COLLAPSE (L->0)" if x["collapses"] else "stable L*=%.3f" % x["L_star_formula"]
        print("    c4=%.1f: %s  (E_min=%.1f)" % (x["c4"], tag, x["E_min"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (Q_H integer + Derrick: bare collapses, 'third' stabilises)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "hopfion_static.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/hopfion_static.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
