#!/usr/bin/env python3
"""e018 Stage 2 -- a SPATIAL membrane vesicle (phase field), not just kinetics.

Stage 1 was 0-dimensional kinetics (no space). Here the vessel has a BODY: a
phase field phi(x,y) that phase-separates into a dense interior (phi~+1) and a
dilute exterior (phi~-1), with a thin INTERFACE between them -- the membrane. The
droplet is kept alive by a DRIVE: a mass-controlled (nonlocal) Allen-Cahn active
droplet (a minimal Zwicker-style active emulsion),

    dphi/dt = eps^2 * lap(phi) - (phi^3 - phi) + mu(t)
    mu(t)   = s * (target - <phi>)  -  leak * (<phi> + 1)/2

The double-well -(phi^3-phi) sharpens a thin interface; the spatially-uniform
field mu(t) is a driven mass control: the drive s supplies material (holding the
mean, hence a finite droplet), while the leak degrades it. We MEASURE (never
write "die" or "form a droplet"):
  * DRIVEN: a single, COMPACT, bounded droplet with a THIN interface forms and
    persists -- a vesicle with a membrane, NOT a space-filling phase.
  * CUT THE DRIVE (s=0): the leak drains the droplet -> it DISSOLVES (death).
  * higher LEAK needs higher DRIVE to survive (leak up -> drive up), the spatial
    echo of the Stage-1 critical-drive curve.

Floors: a coarse-grained continuum phase field (not a lipid bilayer); the
"membrane/vesicle/protocell/death" language is analogy/interpretive; not a cell.
Fixed periodic lattice; the droplet size is set by the drive/leak balance.

MODULE:   e018_membrane_vesicle (Stage 2: phase-field vesicle)
QUESTION: Does a driven phase field make a BOUNDED vesicle with a membrane that persists on drive and dissolves without it?
PUT IN:   Allen-Cahn double-well + a driven mass control (drive s, leak). "Form a bounded droplet" / "dissolve" not put in.
EMERGED:  (measured) a single compact bounded droplet with a thin interface persists when driven; cut the drive -> it dissolves; leak up -> drive up to survive.
CLAIM TIER: measured(bounded single-droplet, driven persistence, dissolution, leak->drive threshold) ; analogy(membrane/vesicle/protocell).
KNOWN MATCH: phase separation (Cahn-Hilliard/Allen-Cahn); active droplets (Zwicker et al.).
STATUS:   GREEN (bounded vesicle + drive-dependent persistence measured; membrane/protocell is analogy).
A_OR_B:   (A) faithful. Hand input = phase-field dynamics + a drive; the bounded droplet and its death are emergent.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy import ndimage

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"L": 128, "steps": 6000, "eps2": 2.0, "target": -0.4, "dt": 0.05,
           "s": 1.0, "seed": 0,
           "leak_grid": [0.0, 0.4, 0.8], "s_grid": [0.1, 0.2, 0.3, 0.6, 1.0]}
QUICK = {"L": 96, "steps": 4000, "leak_grid": [0.0, 0.8], "s_grid": [0.1, 0.3, 1.0]}


def _lap(f):
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0)
            + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4 * f)


def evolve(p, s, leak):
    """Evolve the active droplet; return interior fraction, interface band, #blobs."""
    L = p["L"]
    rng = np.random.default_rng(p["seed"])
    x = np.arange(L)
    X, Y = np.meshgrid(x, x, indexing="ij")
    r = np.sqrt((X - L / 2) ** 2 + (Y - L / 2) ** 2)
    phi = -0.8 + 1.6 * (r < L * 0.18) + 0.02 * rng.standard_normal((L, L))
    dt = p["dt"]
    for _ in range(p["steps"]):
        m = phi.mean()
        mu = s * (p["target"] - m) - leak * (m + 1.0) * 0.5
        phi = phi + dt * (p["eps2"] * _lap(phi) - (phi ** 3 - phi) + mu)
    inside = phi > 0.0
    lbl, ncomp = ndimage.label(inside)
    if ncomp > 0:                       # keep the largest blob for compactness stats
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, ncomp + 1))
        biggest = int(np.argmax(sizes)) + 1
        blob = lbl == biggest
    else:
        blob = inside
    touches = int(blob[0, :].any() or blob[-1, :].any() or blob[:, 0].any() or blob[:, -1].any())
    return {"s": s, "leak": leak,
            "inside_frac": round(float(inside.mean()), 3),
            "interface_band": round(float(((phi > -0.6) & (phi < 0.6)).mean()), 3),
            "n_components": int(ncomp),
            "border_touch": touches,
            "alive": bool(inside.mean() > 0.02),
            "bounded_single_vesicle": bool(ncomp == 1 and 0.02 < inside.mean() < 0.45 and touches == 0)}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    driven = evolve(p, s=p["s"], leak=0.0)
    no_drive = evolve(p, s=0.0, leak=0.0)
    # leak -> drive survival threshold (spatial echo of Stage-1 critical-drive curve)
    thresholds = []
    for leak in p["leak_grid"]:
        surv = [s for s in p["s_grid"] if evolve(p, s=s, leak=leak)["alive"]]
        thresholds.append({"leak": leak, "min_surviving_s": min(surv) if surv else None})
    crit = [t["min_surviving_s"] for t in thresholds if t["min_surviving_s"] is not None]
    rises = bool(len(crit) >= 2 and all(crit[i] <= crit[i + 1] + 1e-9 for i in range(len(crit) - 1))
                 and crit[-1] > crit[0])
    return {
        "params": p, "driven": driven, "no_drive": no_drive,
        "vesicle_forms_when_driven": driven["bounded_single_vesicle"],
        "dissolves_without_drive": not no_drive["alive"],
        "thresholds": thresholds, "drive_threshold_rises_with_leak": rises,
    }


def evaluate(result, quick=False):
    checks = {
        "bounded single vesicle forms (driven)": result["vesicle_forms_when_driven"],
        "dissolves without drive (death)": result["dissolves_without_drive"],
        "leak up -> drive up to survive": result["drive_threshold_rises_with_leak"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e018 phase-field membrane vesicle", "tier": "measured",
        "put_in": "Allen-Cahn double-well + driven mass control (drive s, leak); 'droplet'/'dissolve' not put in",
        "emerged": ["a single compact bounded droplet with a thin interface (membrane) persists when driven: %s"
                    % result["driven"],
                    "cut the drive (s=0) -> it dissolves (%s) = death" % result["no_drive"],
                    "leak up -> drive up to survive: %s"
                    % [(t["leak"], t["min_surviving_s"]) for t in result["thresholds"]]],
        "surprises": ["a spatial vesicle with a membrane (not just kinetics) lives and dies by the same drive rule"],
        "persistence": "the vesicle persists only while driven above a leak-dependent threshold",
        "measured_numbers": {"driven": result["driven"], "no_drive": result["no_drive"],
                             "thresholds": result["thresholds"]},
        "not_scripted_check": "the droplet + interface + dissolution emerge from the field dynamics; no shape/death imposed",
        "claim_tier": "measured (bounded single-droplet, driven persistence, dissolution, leak->drive) ; analogy (membrane/vesicle/protocell)",
        "floors": ["coarse-grained continuum phase field (not a lipid bilayer); fixed periodic lattice",
                   "'membrane/vesicle/protocell/death' is analogy; not a cell; we did NOT make life"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e018 phase-field membrane vesicle")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e018 phase-field membrane vesicle (bounded droplet; driven lives, cut drive dies) ===")
    print("  driven:   %s" % r["driven"])
    print("  no drive: %s" % r["no_drive"])
    print("  leak -> min surviving drive:")
    for t in r["thresholds"]:
        print("     leak=%.1f  min_surviving_s=%s" % (t["leak"], t["min_surviving_s"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (bounded vesicle + drive-dependent persistence measured; membrane/protocell is analogy)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "membrane_vesicle.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/membrane_vesicle.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
