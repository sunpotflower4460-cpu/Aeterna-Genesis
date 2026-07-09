#!/usr/bin/env python3
"""e024 Stage 1 -- the ratchet: does an ASYMMETRIC potential rectify symmetric noise?

MODULE:   e024_vessel_engine (Stage 1: ratchet)
QUESTION: for an asymmetric ("counter-thread") periodic potential, is the drift v(F)
          NON-antisymmetric, so that a symmetric rocking vibration yields a NET current?
PUT IN:   overdamped Langevin in V(x) = -[sin(2pi x) + 0.25*asym*sin(4pi x)] + a symmetric
          drive +/-A and Gaussian noise. NO direction is put in; asym only breaks left/right.
EMERGED:  (measured) the rocking current (v(+A)+v(-A))/2 is 0 for the symmetric potential
          and a definite-sign, drive-growing current for the asymmetric one.
CLAIM TIER: measured(rectification, its growth with drive, any-asymmetry rectifies) ;
          interpretive(the arrow of a motor comes from a broken spatial symmetry) ;
          analogy(a "bolt tightening under vibration", a molecular ratchet).
KNOWN MATCH: the Brownian ratchet / Smoluchowski-Feynman ratchet; flashing/rocking ratchets.
STATUS:   GREEN (three rectification gates, physical quantities only).
A_OR_B:   (A) faithful. Hand input = the potential asymmetry + symmetric drive + noise;
          the NET current is emergent and measured, not scripted.

THE TRAP (designer hit it, we avoid it): measure the rectification from the STATIC tilted
drifts v(+A) and v(-A) separately and average -- integrating a slow rocking drive directly
fights the barrier and reads a spuriously weak current. Also: the current is a physical
drift velocity; do NOT name the gate "life" or "will".

Floors: overdamped point particle in 1D, fixed noise strength D and integration dt; absolute
current magnitudes depend on (D, T, dt). The rectification SIGN and its growth are the robust,
gated facts. "Bolt/tightening" is analogy.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"D": 0.3, "T": 120.0, "dt": 0.005, "Np": 2500,
           "amps": [1.5, 3.0, 4.5, 6.0], "asyms": [0.0, 0.1, 0.3, 0.6, 1.0], "seed": 0}
QUICK = {"T": 60.0, "Np": 900, "amps": [1.5, 4.5, 6.0], "asyms": [0.0, 0.1, 1.0]}


def _force(x, asym):
    """-dV/dx for V(x) = -[sin(2pi x) + 0.25*asym*sin(4pi x)]."""
    return 2 * np.pi * np.cos(2 * np.pi * x) + np.pi * asym * np.cos(4 * np.pi * x)


def drift(F, asym, p, rng):
    """Mean drift velocity of an overdamped ensemble under a static tilt F."""
    x = rng.random(p["Np"])
    x0 = x.copy()
    sq = np.sqrt(2 * p["D"] * p["dt"])
    for _ in range(int(p["T"] / p["dt"])):
        x = x + p["dt"] * (_force(x, asym) + F) + sq * rng.standard_normal(p["Np"])
    return float(np.mean(x - x0) / p["T"])


def _rectification(A, asym, p, rng):
    """Rocking current at amplitude A = (v(+A)+v(-A))/2 (static-tilt method)."""
    return (drift(A, asym, p, rng) + drift(-A, asym, p, rng)) / 2.0


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rng = np.random.default_rng(p["seed"])

    # (a) rocking current vs drive amplitude, symmetric vs asymmetric (ratchet)
    rect_sym, rect_rat = [], []
    for A in p["amps"]:
        rect_sym.append(round(_rectification(A, 0.0, p, rng), 4))
        rect_rat.append(round(_rectification(A, 1.0, p, rng), 4))

    # (b) rocking current vs asymmetry at fixed amplitude A=4.5
    Aref = 4.5
    asym_rect = [round(_rectification(Aref, a, p, rng), 4) for a in p["asyms"]]

    imax = p["amps"].index(max(p["amps"]))
    return {
        "params": p, "amps": p["amps"], "asyms": p["asyms"], "aref": Aref,
        "rect_symmetric": rect_sym, "rect_ratchet": rect_rat, "asym_rect": asym_rect,
        # asym=1 ratchet at the reference amplitude clearly rectifies; symmetric ~0
        "ratchet_rectifies_at_aref": rect_rat[p["amps"].index(Aref)] if Aref in p["amps"] else rect_rat[imax],
        "symmetric_is_null": max(abs(v) for v in rect_sym),
        # monotone growth of the ratchet current with drive amplitude
        "rect_grows_with_drive": bool(all(rect_rat[i] < rect_rat[i + 1] for i in range(len(rect_rat) - 1))
                                      and rect_rat[imax] > 0.5),
        # smallest nonzero asymmetry still rectifies (>0), symmetric (asym=0) does not
        "small_asym_rectifies": bool(asym_rect[p["asyms"].index(0.1)] > 0.0) if 0.1 in p["asyms"] else False,
        "asym0_null": bool(abs(asym_rect[p["asyms"].index(0.0)]) < 0.05) if 0.0 in p["asyms"] else False,
    }


def evaluate(result, quick=False):
    aref_rect = result["ratchet_rectifies_at_aref"]
    checks = {
        "rectifies_symmetric_drive (ratchet>0.3, symmetric~0)":
            bool(aref_rect > 0.3 and result["symmetric_is_null"] < 0.05),
        "rectification_grows_with_drive (monotone, max>0.5)":
            result["rect_grows_with_drive"],
        "any_asymmetry_rectifies (asym=0.1>0, asym=0~0)":
            bool(result["small_asym_rectifies"] and result["asym0_null"]),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e024 vessel engine Stage 1 (ratchet)", "tier": "measured",
        "put_in": "overdamped Langevin in an asymmetric periodic potential + symmetric drive +/-A + noise",
        "emerged": ["symmetric potential: rocking current ~0 (%s); asymmetric ratchet: %s (grows with A)"
                    % (result["rect_symmetric"], result["rect_ratchet"]),
                    "rocking current vs asymmetry at A=%.1f: %s (any asymmetry rectifies)"
                    % (result["aref"], result["asym_rect"])],
        "surprises": ["a SYMMETRIC vibration yields a definite-sign net current once the potential is asymmetric"],
        "persistence": "the rectification sign is fixed by the potential asymmetry; magnitude grows with drive",
        "measured_numbers": {"amps": result["amps"], "rect_symmetric": result["rect_symmetric"],
                             "rect_ratchet": result["rect_ratchet"], "asyms": result["asyms"],
                             "asym_rect": result["asym_rect"]},
        "not_scripted_check": "no direction is put in; only V's left/right asymmetry; the net current is measured",
        "claim_tier": "measured (rectification, growth, any-asymmetry) ; interpretive (the motor's arrow "
                      "= broken spatial symmetry) ; analogy (bolt/ratchet)",
        "floors": ["1D overdamped point particle; absolute currents depend on (D, T, dt)",
                   "the SIGN and growth of the rectification are the gated facts, not the magnitude",
                   "'bolt tightening' is analogy, not a claim about a real fastener"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e024 Stage 1: ratchet rectification")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e024 Stage 1 -- ratchet: symmetric noise -> net current ===")
    print("  rocking current (v(+A)+v(-A))/2 vs amplitude:")
    print("     %8s %14s %10s" % ("A", "symmetric", "ratchet"))
    for A, s, rr in zip(r["amps"], r["rect_symmetric"], r["rect_ratchet"]):
        print("     %8.1f %+14.3f %+10.3f" % (A, s, rr))
    print("  rocking current vs asymmetry (A=%.1f): %s" % (r["aref"], r["asym_rect"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (rectification measured; magnitude is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "ratchet.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/ratchet.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
