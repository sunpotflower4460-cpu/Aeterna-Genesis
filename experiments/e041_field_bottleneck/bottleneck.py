#!/usr/bin/env python3
"""e041 -- 'starting from one' as GEOMETRY: a physical pinch neck sets the founder number (no agents).

---
id: e041
role: S
claim_tier: measured
evidence: "a narrow pinch neck passes ~1 founder so the daughter is clonal (Simpson relatedness ->1); a wide neck passes many founders so the daughter is mixed (relatedness ->0.001) -- the single-cell bottleneck emerges from the neck WIDTH"
target_encoded: false
known_match: "the germline / single-cell bottleneck aligning within- vs between-unit fitness (Grosberg-Strathmann); Simpson diversity"
open_issues: ["S: a GEOMETRIC SAMPLING model (a neck strip over a tagged body), NOT a continuum field -- the pinch is abstracted; founder->clonal regrowth is imposed", "'clonal / relatedness / individual' is analogy"]
---

MODULE:   e041_field_bottleneck
QUESTION: the major transition (cooperation, division of labor) needs 'starting from one' -- a single-cell
          bottleneck that makes offspring clonal (relatedness 1) so within- and between-unit fitness align.
          Is that bottleneck an abstract rule, or does it EMERGE from the GEOMETRY of a dividing body -- the
          WIDTH of the pinch neck through which founders pass?
PUT IN:   a tagged body (each cell a distinct founder identity along a position 0..1) and a pinch NECK = a
          strip of width w around the midline; the daughter regrows from whoever passed the neck. NO
          "narrow neck -> clonal" is put in -- the founder count and the daughter's relatedness are measured.
EMERGED:  (measured) a NARROW neck passes ~1 founder, so the daughter is CLONAL (Simpson relatedness -> 1 =
          'started from one'); a WIDE neck passes many founders, so the daughter is MIXED (relatedness -> 0).
          The single-cell bottleneck is set by the neck WIDTH = the geometry of division.
CLAIM TIER: measured(founder count and relatedness vs neck width) ; interpretive(the bottleneck that enables
          a coherent higher individual emerges from the pinch geometry) ; analogy(clonality / relatedness).
KNOWN MATCH: the germline / single-cell bottleneck (Grosberg-Strathmann); Simpson diversity index.
STATUS:   S (a designed GEOMETRIC SAMPLING model: the neck-width -> relatedness relationship is measured,
          but the pinch is abstracted to a sampling strip -- NOT a continuum field emergence).

THE TRAP (designer hit it, we avoid it): the founder->clonal regrowth is imposed; the MEASURED, non-obvious
thing is the neck-width -> relatedness CURVE (narrow -> 1, wide -> 0). We gate on that relationship, not on a
named 'bottleneck'. Role S: this is a geometric/statistical abstraction, honestly not a field PDE.

Floors: S -- a GEOMETRIC SAMPLING model (a neck strip over a tagged body), NOT a continuum field; the pinch
is abstracted. "Clonal / relatedness / individual" is analogy. 同じ数学≠同じもの. This connects e026's
winding pinch and the single-cell bottleneck of the major transition, but as geometry, not a faithful field.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"Ncells": 3000, "ws": [0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0], "seeds": [0, 1, 2, 3, 4, 5]}
QUICK = {"Ncells": 2000, "seeds": [0, 1, 2]}


def _daughter(w, seed, Ncells):
    """Return (founder count, Simpson relatedness) for a neck of width w over a tagged body."""
    r = np.random.default_rng(seed)
    pos = r.random(Ncells)                              # cells along the body (position 0..1)
    fid = np.arange(Ncells)                             # each cell a distinct founder identity
    neck = np.abs(pos - 0.5) < w / 2                    # the pinch neck: a strip of width w
    founders = fid[neck]
    if len(founders) == 0:
        founders = fid[[int(np.argmin(np.abs(pos - 0.5)))]]   # at least the single closest cell
    daughter = r.choice(founders, size=Ncells)         # daughter regrows from whoever passed the neck
    _, cnt = np.unique(daughter, return_counts=True)
    p = cnt / cnt.sum()
    return len(founders), float((p ** 2).sum())        # founder count, relatedness = Simpson (1 = clonal)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for w in p["ws"]:
        vals = np.array([_daughter(w, s, p["Ncells"]) for s in p["seeds"]])
        nf, rel = float(vals[:, 0].mean()), float(vals[:, 1].mean())
        rows.append({"w": w, "founders": round(nf, 1), "relatedness": round(rel, 3)})
    narrow, wide = rows[0], rows[-1]
    # relatedness decreases monotonically as the neck widens (more founders -> more mixed)
    rels = [r["relatedness"] for r in rows]
    monotone = all(rels[i] >= rels[i + 1] - 0.02 for i in range(len(rels) - 1))
    return {"params": p, "rows": rows, "narrow": narrow, "wide": wide,
            "relatedness_monotone_in_width": bool(monotone)}


def evaluate(result, quick=False):
    checks = {
        "narrow_neck_single_founder (narrowest neck passes < 3 founders)":
            bool(result["narrow"]["founders"] < 3),
        "narrow_neck_clonal_daughter (relatedness > 0.5 at the narrowest neck = 'started from one')":
            bool(result["narrow"]["relatedness"] > 0.5),
        "wide_neck_mixed_daughter (relatedness < 0.1 and > 100 founders at the widest neck)":
            bool(result["wide"]["relatedness"] < 0.1 and result["wide"]["founders"] > 100),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e041 field bottleneck (neck geometry -> founder number -> clonality)", "tier": "measured",
        "put_in": "a tagged body (distinct founder identities) + a pinch neck of width w; the daughter "
                  "regrows from whoever passed the neck. NO narrow->clonal put in",
        "emerged": ["neck width -> (founders, relatedness): %s"
                    % [(r["w"], r["founders"], r["relatedness"]) for r in result["rows"]],
                    "narrow neck: %s founders, relatedness %s (clonal); wide neck: %s founders, relatedness %s (mixed)"
                    % (result["narrow"]["founders"], result["narrow"]["relatedness"],
                       result["wide"]["founders"], result["wide"]["relatedness"])],
        "surprises": ["the single-cell bottleneck of the major transition is not an abstract rule -- it is set "
                      "by the WIDTH of the dividing neck (geometry)"],
        "persistence": "relatedness decreases monotonically as the neck widens (few founders -> clonal, many -> mixed)",
        "measured_numbers": {"rows": result["rows"], "narrow": result["narrow"], "wide": result["wide"]},
        "not_scripted_check": "the neck-width -> relatedness relationship is measured, not imposed",
        "claim_tier": "measured (founder count + relatedness vs neck width) ; interpretive (the bottleneck "
                      "emerges from the pinch geometry) ; analogy (clonality / relatedness)",
        "floors": ["S: a GEOMETRIC SAMPLING model (a neck strip over a tagged body), NOT a continuum field",
                   "the founder->clonal regrowth is imposed; 'clonal / relatedness / individual' is analogy",
                   "同じ数学≠同じもの: this abstracts the pinch geometry; it is not a faithful field PDE"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e041 field bottleneck (neck geometry -> clonality)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e041 -- 'starting from one' as GEOMETRY (pinch neck width -> founder number, no agents) ===")
    print("   %13s %16s %22s" % ("neck width w", "founders passed", "relatedness (Simpson)"))
    for row in r["rows"]:
        print("   %13.4f %16.1f %22.3f" % (row["w"], row["founders"], row["relatedness"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role S] (the single-cell bottleneck emerges from the neck WIDTH = geometry)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "bottleneck.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/bottleneck.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
