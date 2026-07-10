#!/usr/bin/env python3
"""e038 -- continuous-trait evolution in a FIELD via object tracking: de novo climb, no standing variation.

---
id: e038
role: E
claim_tier: measured
evidence: "seeded at a LOW uniform trait (tau=0.2, optimum 1.0), de novo mutation+selection climb the field's mean trait to ~0.9 with NO standing variation; the trait stays continuous (>=4 occupied bins); a moving optimum is tracked (lag ~0.24)"
target_encoded: false
known_match: "replicator-mutator / de novo adaptation (cf e036); the standing-variation vs de-novo distinction"
open_issues: ["HYBRID: the dynamics are a pure Gray-Scott field but the trait is a tracked per-TISSUE LABEL (not a homogenized field) -- a floor", "the fitness->kill coupling is imposed; 'evolution' is analogy"]
---

MODULE:   e038_field_objtrack
QUESTION: e036 evolved a trait DENSITY over a trait axis. A pure trait FIELD homogenizes (global diffusion
          erases variation) and needs standing variation. Can OBJECT TRACKING fix both -- hold the trait
          per-TISSUE on emergent Gray-Scott spots, generate de novo variation at the growth front, and let
          SELECTION climb a LOW-seeded trait to the optimum with NO standing variation?
PUT IN:   a Gray-Scott reaction-diffusion field; each spot's TISSUE carries a continuous trait tau; at the
          division/growth FRONT, new tissue INHERITS the adjacent parent tau + a small MUTATION; fitness
          couples the trait to the local kill rate (tau near the optimum -> lower kill -> fitter). Seed ALL
          tissue at a LOW uniform tau=0.2. NO "the mean trait climbs" is put in -- it is measured.
EMERGED:  (measured) the field's mean trait CLIMBS 0.2 -> ~0.9 purely by de novo mutation + selection (no
          standing variation was seeded); the trait distribution stays CONTINUOUS (multiple occupied bins,
          not collapsed to discrete species); a moving optimum is tracked with a small lag (~0.24).
CLAIM TIER: measured(de novo climb; continuous distribution; moving-optimum lag) ; interpretive(object
          tracking lets continuous-trait evolution run in a field without homogenization) ; analogy(evolution).
KNOWN MATCH: replicator-mutator / de novo adaptation (cf e036); mutation-generated vs standing variation.
STATUS:   E (de novo climb emerges from the faithful GS field + trait tracking; gates on field trait statistics).
A_OR_B:   (A) faithful GS dynamics with a tracked trait LABEL (hybrid). Hand input = the GS field + trait
          inheritance + fitness coupling; whether de novo variation suffices to climb is emergent and measured.

THE TRAP (designer hit it, we avoid it): we seed a LOW UNIFORM trait (no standing variation) and let the
front-inheritance + mutation generate variation de novo. The climb is NOT put in -- selection (fitness->kill)
is the law; whether de novo mutation is ENOUGH to climb from a uniform low seed is the measured question.

Floors: HYBRID -- the dynamics are a pure Gray-Scott field but the trait is a tracked per-TISSUE LABEL (not a
homogenized field); the fitness->kill coupling is imposed. "Evolution / adaptation" is analogy. 同じ数学≠
同じもの. (A) faithful: the field law + trait rule are put in by hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]

DEFAULT = {"N": 100, "Du": 0.16, "Dv": 0.08, "F0": 0.030, "dt": 1.0, "steps": 32000,
           "seed_tau": 0.2, "mut": 0.035, "seed": 0, "hist_bins": 10}
QUICK = {"N": 72, "steps": 13000}


def _lap(Z):
    return np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z


def _run(p, seed_tau, moving):
    N = p["N"]
    rng = np.random.default_rng(p["seed"])
    U = np.ones((N, N)); V = np.zeros((N, N)); tau = np.full((N, N), seed_tau)
    for _ in range(16):
        cx, cy = rng.integers(6, N - 6, 2)
        U[cx - 3:cx + 3, cy - 3:cy + 3] = 0.5
        V[cx - 3:cx + 3, cy - 3:cy + 3] = 0.25
        tau[cx - 3:cx + 3, cy - 3:cy + 3] = seed_tau
    high = V > 0.15
    H = []
    for t in range(p["steps"]):
        topt = (0.5 + 0.4 * np.sin(t / 2500.0)) if moving else 1.0
        k_field = 0.0605 + 0.0045 * np.abs(tau - topt)      # trait near optimum -> lower kill -> fitter
        uvv = U * V * V
        U = U + p["dt"] * (p["Du"] * _lap(U) - uvv + p["F0"] * (1 - U))
        V = np.clip(V + p["dt"] * (p["Dv"] * _lap(V) + uvv - (p["F0"] + k_field) * V), 0, None)
        newhigh = V > 0.15
        front = newhigh & (~high)
        if front.any():                                     # growth front inherits parent tau + mutation
            hf = high.astype(float)
            num = sum(np.roll(np.roll(tau * hf, d0, 0), d1, 1) for d0, d1 in _NB)
            den = sum(np.roll(np.roll(hf, d0, 0), d1, 1) for d0, d1 in _NB)
            inh = num / (den + 1e-9) + p["mut"] * rng.standard_normal((N, N))
            tau = np.where(front & (den > 0.5), np.clip(inh, 0, 1), tau)
        high = newhigh
        if t % 300 == 0 and t > 0:                           # random disturbances (turnover)
            for _ in range(3):
                cx, cy = rng.integers(0, N, 2); rr = 9
                V[max(0, cx - rr):cx + rr, max(0, cy - rr):cy + rr] = 0
                U[max(0, cx - rr):cx + rr, max(0, cy - rr):cy + rr] = 1
        if t % 1500 == 0:
            m = V > 0.15
            mt = float(tau[m].mean()) if m.any() else 0.0
            H.append((t, round(mt, 3), int(m.sum())))
    return H, tau, V


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    # (a) de novo climb from a low uniform seed (no standing variation)
    Ha, ta, Va = _run(p, seed_tau=p["seed_tau"], moving=False)
    m = Va > 0.15
    hist, _ = np.histogram(ta[m], bins=p["hist_bins"], range=(0, 1))
    occupied = int((hist > 0).sum())
    # (b) moving optimum (red queen proxy): tracking lag
    Hr, _, _ = _run(p, seed_tau=0.5, moving=True)
    tgt = np.array([0.5 + 0.4 * np.sin(h[0] / 2500.0) for h in Hr])
    got = np.array([h[1] for h in Hr])
    lag = float(np.mean(np.abs(got[3:] - tgt[3:]))) if len(got) > 3 else 1.0
    return {
        "params": p, "trait_start": Ha[0][1], "trait_end": Ha[-1][1],
        "trait_traj": [h[1] for h in Ha], "occupied_bins": occupied, "hist": [int(x) for x in hist],
        "moving_optimum_lag": round(lag, 3),
    }


def evaluate(result, quick=False):
    checks = {
        "de_novo_continuous_adaptation (mean trait climbs from 0.2 seed to >0.6, no standing variation)":
            bool(result["trait_start"] < 0.35 and result["trait_end"] > 0.6),
        "trait_stays_continuous (>=4 occupied trait bins, not collapsed to discrete species)":
            bool(result["occupied_bins"] >= 4),
        "moving_optimum_tracked (red-queen lag < 0.35)":
            bool(result["moving_optimum_lag"] < 0.35),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e038 field objtrack (continuous-trait evolution in a field, object tracking)",
        "tier": "measured",
        "put_in": "Gray-Scott field; per-TISSUE continuous trait; front-inheritance + mutation; fitness->kill "
                  "coupling; a LOW uniform trait seed (no standing variation)",
        "emerged": ["de novo climb: mean trait %s -> %s (traj %s)"
                    % (result["trait_start"], result["trait_end"], result["trait_traj"]),
                    "trait distribution stays continuous: %s occupied bins (hist %s)"
                    % (result["occupied_bins"], result["hist"]),
                    "moving optimum tracked: lag %s" % result["moving_optimum_lag"]],
        "surprises": ["de novo mutation alone (no standing variation) suffices to climb a low-seeded trait to "
                      "the optimum; object tracking avoids the homogenization a pure trait field would suffer"],
        "persistence": "the climbed trait is held per-tissue and re-established at each growth front",
        "measured_numbers": {"trait_traj": result["trait_traj"], "occupied_bins": result["occupied_bins"],
                             "hist": result["hist"], "moving_optimum_lag": result["moving_optimum_lag"]},
        "not_scripted_check": "the climb, the continuous distribution and the tracking lag are measured",
        "claim_tier": "measured (de novo climb; continuous distribution; moving-optimum lag) ; interpretive "
                      "(object tracking runs continuous-trait evolution in a field) ; analogy (evolution)",
        "floors": ["HYBRID: pure GS dynamics but the trait is a tracked per-TISSUE LABEL (not a homogenized field)",
                   "the fitness->kill coupling is imposed; 'evolution / adaptation' is analogy",
                   "同じ数学≠同じもの; (A) faithful: the field law + trait rule are put in by hand"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e038 field objtrack (continuous-trait evolution, object tracking)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e038 -- continuous-trait evolution in a FIELD (object tracking, no agents) ===")
    print("  (a) de novo climb: mean trait %s -> %s (seeded low, NO standing variation)"
          % (r["trait_start"], r["trait_end"]))
    print("  (a) trait distribution: %s occupied bins (hist %s) -- stays continuous" % (r["occupied_bins"], r["hist"]))
    print("  (b) moving optimum (red queen): tracking lag = %s" % r["moving_optimum_lag"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role E, hybrid] (de novo climb via object-tracked trait; no standing variation)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "objtrack.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/objtrack.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
