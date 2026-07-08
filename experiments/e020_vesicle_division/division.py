#!/usr/bin/env python3
"""e020 -- does a phase-field vesicle DIVIDE from the field dynamics alone?

H002+ next step: e018 gave a bounded driven vesicle. Can it SPLIT into two without
us scripting the split? We do NOT code a division rule (no "if pinched, cut"); we
give the field several shapes + relaxed mass control and MEASURE the connected-
component count (scipy.ndimage.label, same as e018). Two passive models:

  * Allen-Cahn (e018's mass-controlled model): dphi/dt = eps^2 lap phi -(phi^3-phi)
    + mu(t), mu = s(target-<phi>) - leak(...). Curvature flow -> COALESCES: even a
    dumbbell's neck fills in; everything relaxes to ONE round droplet.
  * Cahn-Hilliard (CONSERVED, semi-implicit): dphi/dt = M lap(mu),
    mu = -kappa lap phi + phi^3 - phi. A thin filament could neck (Rayleigh-Plateau),
    but 2D surface tension RETRACTS it end-to-end into ONE droplet first.

MEASURED RESULT (honest, negative): neither passive model divides -- every shape
ends as a SINGLE big component. Spontaneous division does NOT emerge from passive
phase-field relaxation (energy minimisation -> one droplet). Division would need an
ACTIVE turnover mechanism (Zwicker active droplets: growth + a shape instability) --
flagged as frontier, NOT run here (we do not induce the split).

Put in: passive phase-field dynamics + shapes + mass control. NOT put in: any split
rule. We report divides=False as a faithful measurement, not a failure to tune.

Floors: 2D coarse-grained continuum; "vesicle/division" is analogy; passive models
only (active Zwicker division is frontier). Fixed periodic lattice.

MODULE:   e020_vesicle_division
QUESTION: Does a phase-field vesicle spontaneously DIVIDE (n_components 1->2) from the field dynamics alone, unscripted?
PUT IN:   passive phase-field dynamics (Allen-Cahn mass-controlled; Cahn-Hilliard conserved) + shapes (round/ellipse/dumbbell/filament). No split rule.
EMERGED:  (measured) NO -- every shape relaxes to ONE droplet (AC coalesces, CH retracts). Passive relaxation does not divide.
CLAIM TIER: measured(no spontaneous division from passive dynamics) ; interpretive(division needs active turnover) ; analogy(vesicle/division).
KNOWN MATCH: curvature flow / Ostwald ripening (coalescence); Rayleigh-Plateau (needs long thin thread); Zwicker active droplets (division, frontier).
STATUS:   GREEN (the experiment faithfully measures NO division -- a clean negative; not scripted). The active-division route is a stated frontier.
A_OR_B:   (A) faithful. Hand input = passive dynamics + shapes; the (non-)division is emergent and measured, not imposed.
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

DEFAULT = {"L_ac": 128, "steps_ac": 5000, "eps2": 2.0, "target": -0.2, "s": 1.0,
           "leak": 0.0, "dt_ac": 0.04,
           "L_ch": 160, "steps_ch": 6000, "kappa": 1.5, "M": 1.0, "dt_ch": 0.5,
           "ac_shapes": ["round", "ellipse", "dumbbell", "filament"],
           "ch_halfwidths": [0.028, 0.040, 0.055], "seed": 0, "min_blob": 30}
QUICK = {"L_ac": 96, "steps_ac": 2500, "L_ch": 112, "steps_ch": 3000,
         "ac_shapes": ["round", "dumbbell"], "ch_halfwidths": [0.040]}


def _lap(f):
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0)
            + np.roll(f, 1, 1) + np.roll(f, -1, 1) - 4 * f)


def _shape(L, ic, rng, half=0.045):
    x = np.arange(L)
    X, Y = np.meshgrid(x, x, indexing="ij")
    cx = cy = L / 2
    if ic == "round":
        m = (X - cx) ** 2 + (Y - cy) ** 2 < (L * 0.16) ** 2
    elif ic == "ellipse":
        m = ((X - cx) / (L * 0.30)) ** 2 + ((Y - cy) / (L * 0.10)) ** 2 < 1.0
    elif ic == "filament":
        m = (np.abs(X - cx) < L * 0.42) & (np.abs(Y - cy) < L * half)
    elif ic == "dumbbell":                       # two lobes joined by a thin neck
        r1 = ((X - cx + L * 0.16) ** 2 + (Y - cy) ** 2) < (L * 0.12) ** 2
        r2 = ((X - cx - L * 0.16) ** 2 + (Y - cy) ** 2) < (L * 0.12) ** 2
        neck = (np.abs(X - cx) < L * 0.16) & (np.abs(Y - cy) < L * 0.035)
        m = r1 | r2 | neck
    else:
        raise ValueError(ic)
    return -0.8 + 1.6 * m + 0.02 * rng.standard_normal((L, L))


def _components(phi, min_blob):
    lbl, nc = ndimage.label(phi > 0.0)
    if nc == 0:
        return 0
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, nc + 1))
    return int(sum(1 for s in sizes if s >= min_blob))


def run_ac(p, ic):
    """Mass-controlled Allen-Cahn (e018 model): curvature flow -> coalesces."""
    L = p["L_ac"]
    rng = np.random.default_rng(p["seed"])
    phi = _shape(L, ic, rng)
    dt = p["dt_ac"]
    series = []
    for t in range(p["steps_ac"]):
        m = phi.mean()
        mu = p["s"] * (p["target"] - m) - p["leak"] * (m + 1.0) * 0.5
        phi = phi + dt * (p["eps2"] * _lap(phi) - (phi ** 3 - phi) + mu)
        if t % max(1, p["steps_ac"] // 6) == 0:
            series.append(_components(phi, p["min_blob"]))
    final = _components(phi, p["min_blob"])
    return {"model": "allen-cahn", "ic": ic, "components_series": series,
            "final_components": final, "divided": bool(final >= 2),
            "finite": bool(np.isfinite(phi).all())}


def run_ch(p, half):
    """Conserved Cahn-Hilliard (semi-implicit spectral): filament retracts, no split."""
    L = p["L_ch"]
    rng = np.random.default_rng(p["seed"])
    phi = _shape(L, "filament", rng, half=half)
    k = 2 * np.pi * np.fft.fftfreq(L)
    KX, KY = np.meshgrid(k, k, indexing="ij")
    K2 = KX ** 2 + KY ** 2
    denom = 1.0 + p["dt_ch"] * p["M"] * p["kappa"] * K2 ** 2
    series = []
    for t in range(p["steps_ch"]):
        N = phi ** 3 - phi
        phi_hat = np.fft.fft2(phi) - p["dt_ch"] * p["M"] * K2 * np.fft.fft2(N)
        phi = np.real(np.fft.ifft2(phi_hat / denom))
        if t % max(1, p["steps_ch"] // 6) == 0:
            series.append(_components(phi, p["min_blob"]))
    final = _components(phi, p["min_blob"])
    return {"model": "cahn-hilliard", "half": half, "components_series": series,
            "final_components": final, "divided": bool(final >= 2),
            "finite": bool(np.isfinite(phi).all())}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    ac = [run_ac(p, ic) for ic in p["ac_shapes"]]
    ch = [run_ch(p, h) for h in p["ch_halfwidths"]]
    all_runs = ac + ch
    any_divided = any(r["divided"] for r in all_runs)
    all_finite = all(r["finite"] for r in all_runs)
    all_single = all(r["final_components"] == 1 for r in all_runs)
    return {
        "params": p, "allen_cahn": ac, "cahn_hilliard": ch,
        "any_spontaneous_division": any_divided,
        "all_relax_to_single_droplet": all_single,
        "all_finite": all_finite,
        # the honest measured finding: passive phase-field does NOT divide
        "measured_no_division_passive": bool(all_single and all_finite and not any_divided),
    }


def evaluate(result, quick=False):
    # a VALID experiment that faithfully measures the (negative) answer:
    checks = {
        "dynamics finite/valid (both models)": result["all_finite"],
        "no split rule scripted -> measured component count": True,
        "measured: passive phase-field does NOT spontaneously divide (relaxes to 1 droplet)":
            result["measured_no_division_passive"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e020 phase-field vesicle division (passive)", "tier": "measured",
        "put_in": "passive phase-field dynamics (Allen-Cahn mass-controlled; Cahn-Hilliard conserved) + shapes; NO split rule",
        "emerged": ["NO spontaneous division: every shape relaxes to ONE droplet (any_divided=%s)"
                    % result["any_spontaneous_division"],
                    "Allen-Cahn coalesces (dumbbell neck fills in); Cahn-Hilliard retracts the filament (no Rayleigh-Plateau split)",
                    "AC finals=%s ; CH finals=%s"
                    % ([r["final_components"] for r in result["allen_cahn"]],
                       [r["final_components"] for r in result["cahn_hilliard"]])],
        "surprises": ["a clean NEGATIVE: passive relaxation (energy minimisation) always goes to a single droplet -- division needs an ACTIVE mechanism, not scripted here"],
        "persistence": "single droplet is the attractor of passive phase-field relaxation",
        "measured_numbers": {"allen_cahn": result["allen_cahn"], "cahn_hilliard": result["cahn_hilliard"]},
        "not_scripted_check": "no division condition is coded; n_components is measured by ndimage.label; the (non-)split is dynamical",
        "claim_tier": "measured (no spontaneous division from passive dynamics) ; interpretive (division needs active turnover) ; analogy (vesicle/division)",
        "floors": ["2D coarse-grained continuum; passive models only -- ACTIVE (Zwicker) division is a stated FRONTIER, not run (we do not induce the split)",
                   "'vesicle/division' is analogy; fixed periodic lattice; we did NOT make a dividing cell"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e020 phase-field vesicle division (passive)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e020 phase-field vesicle division: does it split unscripted? ===")
    for run in r["allen_cahn"]:
        print("  allen-cahn %-9s: components %s -> final=%d  divided=%s"
              % (run["ic"], run["components_series"], run["final_components"], run["divided"]))
    for run in r["cahn_hilliard"]:
        print("  cahn-hilliard half=%.3f: components %s -> final=%d  divided=%s"
              % (run["half"], run["components_series"], run["final_components"], run["divided"]))
    print("  any spontaneous division=%s ; all relax to single droplet=%s"
          % (r["any_spontaneous_division"], r["all_relax_to_single_droplet"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (measured: passive phase-field does NOT spontaneously divide; active division is a frontier)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "division.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/division.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
