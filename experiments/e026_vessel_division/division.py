#!/usr/bin/env python3
"""e026 -- topological division accounting: a wound core cannot be copied, only re-created.

---
id: e026
role: F
claim_tier: measured          # the WINDING-READ ARITHMETIC (loop sum = enclosed charge) is measured
evidence: "CCW loops read winding sums exactly; a +1 split gives (+1,0), and (+1,+1) requires a shed -1 so the total stays +1"
target_encoded: false         # loop arithmetic is real; but the 'division' is STATIC hand-placed cores, not a dynamic pinch
known_match: "topological charge conservation; no-cloning of a topological defect; pair nucleation"
open_issues: ["the DYNAMIC pinch that actually carries a vortex into a daughter FAILS (winding leaks to 0) = frontier", "static accounting only"]
---

**Role F (frontier)**: what is measured is the WINDING-READ ARITHMETIC on CCW loops (a real property of
core.holonomy): loop sum = enclosed charge, so a +1 cannot become (+1,+1) without a shed -1. But the
"division" itself is STATIC -- cores are hand-placed at the daughter positions; the DYNAMIC pinch that
carries a vortex into each daughter FAILS (winding leaks to 0). So the topological no-copy conclusion is a
consequence of conservation verified on placed charges, NOT an emergent division. Dynamic division is
frontier -> role F, not GREEN.

MODULE:   e026_vessel_division
QUESTION: if identity = an enclosed winding number (conserved), can a region of winding W split into
          two daughters that BOTH carry W -- or does conservation forbid duplicating it?
PUT IN:   phase fields built from placed +1/-1 cores; loops (CCW) of chosen radius read the enclosed
          winding. NO "cannot be copied" and NO "needs a shed anti" are put in -- both are winding reads.
EMERGED:  (measured) (A) one +1 split into two daughters gives windings (+1, 0): one wound, one empty
          (you cannot make (+1,+1)=+2 from +1). (B) to get two wound daughters you must nucleate a new
          +1/-1 pair and shed the -1 outside: daughters (+1,+1), a loop around both reads +2, a loop
          around everything (incl. the shed -1) reads +1 -- total winding CONSERVED.
CLAIM TIER: measured(the winding accounting) ; interpretive(reproduction CREATES a new individual, it
          does not copy; the anti-charge is a necessary by-product) ; analogy(reproduction / a "self" /
          "identity cannot be copied" -- KNOWN MATCH only, never a gate name).
KNOWN MATCH: topological charge conservation; the no-cloning of a topological defect; pair nucleation.
STATUS:   F (the winding-read arithmetic is measured, but the DIVISION is static hand-placed accounting;
          the dynamic pinch that carries a vortex into a daughter FAILS = frontier -> role F, not GREEN).
A_OR_B:   (A) faithful winding reads; but the "division" is STATIC (placed cores), not a dynamic emergent
          pinch. The topological no-copy is a consequence of conservation on placed charges. Role F.

THE TRAP (designer hit it, we avoid it): this is a STATIC accounting -- cores are placed at the daughter
positions and the enclosed winding is read on CCW loops (core.holonomy). A DYNAMIC pinch fails because
the vortex is not carried into each daughter (winding leaks to 0); that failure is a Floor, not the
result. Loops are counter-clockwise; each daughter loop encloses one core, the big loop encloses all.
Do NOT name a gate "identity" or "self" -- those are analogy in the docstring / AUDIT.

Floors: pure static topology (no time evolution, no metabolism cost paid) -- the dynamic pinch that
actually carries a vortex into a daughter is frontier. "Reproduction / self / identity cannot be
copied" is analogy for winding conservation; no organism is reproduced.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import winding_around  # noqa: E402

DEFAULT = {"N": 180, "sep": 18, "shed_y": 50, "R_daughter": 10,
           "R_both": 32, "R_all": 66, "n": 600}
QUICK = {"n": 400}


def _phase_of(cores, N):
    x = np.arange(N) - N / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    ph = np.zeros((N, N))
    for (a, b, c) in cores:
        ph += c * np.arctan2(Y - b, X - a)
    return ph


def _wind(ph, cx, cy, R, N, n):
    """Enclosed winding on a CCW loop of radius R about grid-offset (cx, cy)."""
    return winding_around(ph, N / 2 + cx, N / 2 + cy, R, n=n)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N, s, n = p["N"], p["sep"], p["n"]

    # (A) split one +1 -> can both daughters inherit it?
    phA = _phase_of([(-s, 0, 1)], N)
    A_left = _wind(phA, -s, 0, p["R_daughter"], N, n)
    A_right = _wind(phA, s, 0, p["R_daughter"], N, n)
    A_total = _wind(phA, 0, 0, 45, N, n)

    # (B) nucleate a new +1/-1 pair, shed the -1 outside both daughters
    phB = _phase_of([(-s, 0, 1), (s, 0, 1), (0, p["shed_y"], -1)], N)
    B_left = _wind(phB, -s, 0, p["R_daughter"], N, n)
    B_right = _wind(phB, s, 0, p["R_daughter"], N, n)
    B_both = _wind(phB, 0, 0, p["R_both"], N, n)        # loop around both daughters
    B_all = _wind(phB, 0, 0, p["R_all"], N, n)          # loop around EVERYTHING incl. shed anti

    return {
        "params": p,
        "A": {"left": round(A_left, 2), "right": round(A_right, 2), "total": round(A_total, 2)},
        "B": {"left": round(B_left, 2), "right": round(B_right, 2),
              "both_daughters": round(B_both, 2), "all_incl_anti": round(B_all, 2)},
    }


def evaluate(result, quick=False):
    A, B = result["A"], result["B"]
    checks = {
        # one +1 splits into one wound (+1) and one empty (0) daughter -- cannot duplicate
        "split_gives_one_wound_one_empty (|L|>0.5, |R|<0.5, total~+1)":
            bool(abs(A["left"]) > 0.5 and abs(A["right"]) < 0.5 and abs(A["total"] - 1) < 0.5),
        # two wound daughters require a nucleated pair + a shed anti; total winding conserved (~+1)
        "two_wound_daughters_need_shed_anti (|L|,|R|>0.5, both~+2, all~+1)":
            bool(abs(B["left"]) > 0.5 and abs(B["right"]) > 0.5
                 and abs(B["both_daughters"] - 2) < 0.5 and abs(B["all_incl_anti"] - 1) < 0.5),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e026 vessel division (topological accounting)", "tier": "measured",
        "put_in": "placed +1/-1 cores; CCW loops read the enclosed winding at daughter and enclosing radii",
        "emerged": ["(A) split one +1: daughters (%s, %s), enclosing %s -> one wound, one empty"
                    % (result["A"]["left"], result["A"]["right"], result["A"]["total"]),
                    "(B) nucleate +1/-1 + shed -1: daughters (%s, %s), loop both = %s (+2), loop all = %s (+1, conserved)"
                    % (result["B"]["left"], result["B"]["right"],
                       result["B"]["both_daughters"], result["B"]["all_incl_anti"])],
        "surprises": ["a +1 cannot become (+1,+1); making a second wound daughter forces a nucleated pair and "
                      "a shed anti-charge -- reproduction creates, it does not copy"],
        "persistence": "winding conservation is exact for any enclosing loop (a topological invariant)",
        "measured_numbers": {"A": result["A"], "B": result["B"]},
        "not_scripted_check": "windings are read on CCW loops around placed cores; 'cannot be copied' is a "
                              "measured consequence of conservation, not a rule written in",
        "claim_tier": "measured (winding accounting) ; interpretive (reproduction creates a new individual, "
                      "the anti is a necessary by-product) ; analogy (reproduction / self, KNOWN MATCH only)",
        "floors": ["pure STATIC topology; the dynamic pinch that carries a vortex into a daughter is frontier",
                   "no metabolic cost of pair nucleation is paid here (that is e024/e025's motor)",
                   "'reproduction / identity cannot be copied' is analogy for winding conservation; no organism reproduced"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e026 topological division accounting")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e026 -- topological division: a wound self cannot be copied, only re-created ===")
    print("  (A) split one +1: left=%.1f right=%.1f (total inside=%.1f)  -> one wound, one EMPTY"
          % (r["A"]["left"], r["A"]["right"], r["A"]["total"]))
    print("  (B) nucleate +1/-1 + shed -1: left=%.1f right=%.1f  loop-both=%.1f (+2)  loop-all=%.1f (+1, conserved)"
          % (r["B"]["left"], r["B"]["right"], r["B"]["both_daughters"], r["B"]["all_incl_anti"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role F] (winding arithmetic measured; the DIVISION is static accounting, dynamic pinch is frontier)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "division.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/division.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
