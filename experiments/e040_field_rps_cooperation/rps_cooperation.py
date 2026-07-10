#!/usr/bin/env python3
"""e040 -- cooperation as SUSTAINED SPIRAL WAVES in a pure PDE: cyclic dominance C-D-L (no agents).

---
id: e040
role: E
claim_tier: measured
evidence: "with diffusion, the C-D-L cyclic-dominance (rock-paper-scissors) reaction-diffusion self-organizes into spiral waves in which ALL THREE (including cooperators) persist (C~0.31, D~0.29, L~0.26); the well-mixed control collapses heteroclinically to a single type"
target_encoded: false
known_match: "cyclic Lotka-Volterra / May-Leonard; Reichenbach-Mobilia-Frey spiral waves; the loner-PGG cyclic structure"
open_issues: ["the C-D-L cyclic structure is the PGG-with-loners mechanism as GENERIC cyclic competition, not the exact PGG payoffs (analogy)", "'cooperation' is analogy for the three density fields"]
---

MODULE:   e040_field_rps_cooperation
QUESTION: e037 sustained cooperation via ecological (density) feedback. A DIFFERENT route: cyclic dominance.
          With defect beats coop, coop beats loner, loner beats defect (rock-paper-scissors), does a spatial
          cyclic Lotka-Volterra self-organize into SPIRAL WAVES in which cooperators persist indefinitely --
          while the well-mixed system collapses to one type?
PUT IN:   three density fields a(C), b(D), c(L) on a periodic grid with logistic growth mu*x*(1-rho) and a
          cyclic suppression -s*(a*b, b*c, c*a) (D suppresses C, L suppresses D, C suppresses L) + diffusion D.
          A well-mixed control uses the SAME reaction with no diffusion. NO "spirals" and NO "cooperators
          persist" is put in -- both are measured.
EMERGED:  (measured) the spatial system self-organizes into rotating SPIRAL waves in which all three -- C, D
          and L -- persist (finite densities, large spatial std); the well-mixed control spirals inward
          heteroclinically and one type dominates (the others ~go extinct). Spatial self-organization sustains
          cooperation; the mean field does not.
CLAIM TIER: measured(spatial coexistence + spiral std vs well-mixed collapse) ; interpretive(cyclic dominance +
          space -> sustained cooperation) ; analogy(cooperation, rock-paper-scissors).
KNOWN MATCH: cyclic Lotka-Volterra / May-Leonard; Reichenbach-Mobilia-Frey spiral waves in cyclic games.
STATUS:   E (spiral coexistence emerges from the faithful cyclic RD; gates on physical density fields).
A_OR_B:   (A) faithful. Hand input = the cyclic RD field law + diffusion; the spirals and the coexistence
          are emergent and measured; the well-mixed collapse is the same law without space.

THE TRAP (designer hit it, we avoid it): we gate on the CONTRAST -- spatial coexistence (all three present,
large std = spirals) vs well-mixed collapse (one dominates) -- so the claim is that SPACE sustains
cooperation, not a tuned density. The cyclic structure is put in; the spiral pattern and coexistence are not.

Floors: "cooperation / rock-paper-scissors" is analogy for the three density fields. The C-D-L cyclic
structure is the loner-PGG mechanism as GENERIC cyclic competition (not the exact PGG payoffs). 同じ数学≠
同じもの. (A) faithful: the cyclic RD law is put in by hand, not derived. Spiral formation is REGIME-BOUNDED
and STOCHASTIC: it needs a large enough domain (N>~180) and moderate diffusion (D<~0.8, over-diffusion
homogenizes), and even then a MINORITY of initial conditions collapse to one type (finite-size bistability)
-- ~4/5 seeds form spirals; the robust facts are the spiral MAJORITY and that the well-mixed ALWAYS collapses.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 200, "dt": 0.1, "D": 0.6, "mu": 1.0, "s": 1.4, "steps": 6000, "seed": 0,
           "wm_dt": 0.02, "wm_steps": 8000}
QUICK = {"N": 150, "steps": 4000}    # N>=~140 is needed to host the spiral wavelength (smaller collapses)


def _lap(Z):
    return np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z


def _run_spatial(p):
    N = p["N"]
    rng = np.random.default_rng(p["seed"])
    a = 0.25 + 0.1 * rng.random((N, N))   # C (coop)
    b = 0.25 + 0.1 * rng.random((N, N))   # D (defect)
    c = 0.25 + 0.1 * rng.random((N, N))   # L (loner)
    mu, s, D, dt = p["mu"], p["s"], p["D"], p["dt"]
    traj = []
    for t in range(p["steps"]):
        rho = a + b + c
        a = np.clip(a + dt * (D * _lap(a) + mu * a * (1 - rho) - s * a * b), 0, None)   # C suppressed by D
        b = np.clip(b + dt * (D * _lap(b) + mu * b * (1 - rho) - s * b * c), 0, None)   # D suppressed by L
        c = np.clip(c + dt * (D * _lap(c) + mu * c * (1 - rho) - s * c * a), 0, None)   # L suppressed by C
        if t % 500 == 0:
            traj.append((round(float(a.mean()), 3), round(float(a.std()), 3)))
    return a, b, c, traj


def _run_wellmixed(p):
    a, b, c = 0.3, 0.3, 0.25
    mu, s, dt = p["mu"], p["s"], p["wm_dt"]
    for _ in range(p["wm_steps"]):
        rho = a + b + c
        a = max(a + dt * (mu * a * (1 - rho) - s * a * b), 0)
        b = max(b + dt * (mu * b * (1 - rho) - s * b * c), 0)
        c = max(c + dt * (mu * c * (1 - rho) - s * c * a), 0)
    return a, b, c


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    a, b, c, traj = _run_spatial(p)
    late = [x[1] for x in traj[len(traj) // 2:]]
    aw, bw, cw = _run_wellmixed(p)
    wm = [aw, bw, cw]
    return {
        "params": p,
        "spatial": {"C": round(float(a.mean()), 3), "D": round(float(b.mean()), 3),
                    "L": round(float(c.mean()), 3), "coop_std": round(float(a.std()), 3),
                    "late_min_std": round(float(min(late)) if late else 0.0, 3)},
        "spatial_all_present": bool(a.mean() > 0.02 and b.mean() > 0.02 and c.mean() > 0.02),
        "wellmixed": [round(float(x), 3) for x in wm],
        "wellmixed_dominant": round(float(max(wm)), 3), "wellmixed_min": round(float(min(wm)), 3),
        "traj": traj,
    }


def evaluate(result, quick=False):
    sp = result["spatial"]
    checks = {
        "cooperation_persists_as_spirals (spatial: all three present, coop density >0.02)":
            bool(result["spatial_all_present"] and sp["C"] > 0.02 and sp["late_min_std"] > 0.02),
        "spatial_spiral_pattern (coop spatial std >0.03 = rotating spiral waves)":
            bool(sp["coop_std"] > 0.03),
        "wellmixed_collapses_to_one (no space: one type dominates >0.8, another ~extinct <0.05)":
            bool(result["wellmixed_dominant"] > 0.8 and result["wellmixed_min"] < 0.05),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e040 field RPS cooperation (cyclic-dominance spiral waves, no agents)", "tier": "measured",
        "put_in": "three density fields (C,D,L) with logistic growth + cyclic suppression (D>C, L>D, C>L) + "
                  "diffusion; a well-mixed control with the same reaction, no diffusion. NO spirals put in",
        "emerged": ["spatial: C=%s D=%s L=%s (all persist), coop std=%s (spiral waves)"
                    % (result["spatial"]["C"], result["spatial"]["D"], result["spatial"]["L"],
                       result["spatial"]["coop_std"]),
                    "well-mixed control: %s -> one type dominates (%s), others ~extinct (min %s)"
                    % (result["wellmixed"], result["wellmixed_dominant"], result["wellmixed_min"])],
        "surprises": ["spatial self-organization into rotating spirals keeps cooperators alive indefinitely, "
                      "while the mean-field (well-mixed) system collapses heteroclinically to one type"],
        "persistence": "the spiral waves are a sustained spatiotemporal attractor; all three coexist dynamically",
        "measured_numbers": {"spatial": result["spatial"], "wellmixed": result["wellmixed"], "traj": result["traj"]},
        "not_scripted_check": "the spirals and coexistence are measured; the well-mixed collapse is the same law",
        "claim_tier": "measured (spatial coexistence + spiral std vs well-mixed collapse) ; interpretive (cyclic "
                      "dominance + space sustains cooperation) ; analogy (cooperation / rock-paper-scissors)",
        "floors": ["'cooperation / rock-paper-scissors' is analogy for the three density fields",
                   "the C-D-L cyclic structure is the loner-PGG mechanism as GENERIC cyclic competition (not "
                   "the exact PGG payoffs)",
                   "同じ数学≠同じもの; (A) faithful: the cyclic RD law is put in by hand"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e040 field RPS cooperation (cyclic spiral waves, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    sp = r["spatial"]
    print("=== e040 -- cooperation as SPIRAL WAVES in a pure PDE (C-D-L cyclic dominance, no agents) ===")
    print("  spatial: C=%s D=%s L=%s (all present=%s), coop std=%s (spirals)"
          % (sp["C"], sp["D"], sp["L"], r["spatial_all_present"], sp["coop_std"]))
    print("  well-mixed control: %s -> dominant %s, min %s (heteroclinic collapse)"
          % (r["wellmixed"], r["wellmixed_dominant"], r["wellmixed_min"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role E] (spatial spirals sustain cooperation; well-mixed collapses to one)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "rps_cooperation.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/rps_cooperation.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
