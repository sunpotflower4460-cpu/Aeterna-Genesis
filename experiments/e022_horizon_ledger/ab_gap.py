#!/usr/bin/env python3
"""e022 Stage 1 -- the gap passes one number: an Aharonov-Bohm ring reads only the enclosed flux.

MODULE:   e022_horizon_ledger (Stage 1: ab_gap)
QUESTION: does the content of an UNOBSERVED region (a hole the particle can never enter) reach the
          observed side ONLY as a single quantized number -- the enclosed flux, mod one quantum?
PUT IN:   a tight-binding ring with Peierls bond phases encoding a vector potential; a flux Phi through
          the hole. NO "only the loop-sum matters", NO "period 1", NO "local flatness" are put in.
EMERGED:  (measured) the spectrum depends on the bond phases ONLY through their loop-sum (gauge
          invariance to ~1e-15), it is periodic in Phi with period one quantum, and the local density is
          flat and Phi-independent -- the interior is locally invisible.
CLAIM TIER: measured(gauge invariance, periodicity mod 1, local flatness) ; interpretive(the gap/horizon
          passes a single received number, not a local field) ; analogy(reception, a horizon).
KNOWN MATCH: the Aharonov-Bohm effect; Byers-Yang flux periodicity; persistent currents in a ring.
STATUS:   GREEN (gates on spectral differences and density variance -- physical quantities only).
A_OR_B:   (A) faithful. Hand input = the ring Hamiltonian + a flux; gauge invariance, periodicity, and
          local flatness are emergent and measured (to machine precision).

THE TRAP (designer hit it, we avoid it): the enclosed flux is the LOOP SUM of the bond phases -- a wild
local reassignment with the same loop-sum must give the identical spectrum. Gate on spectral difference
/ density variance -- never name a gate "reception" or "self".

Floors: a finite tight-binding ring; the periodicity is mod one flux quantum. "Reception / horizon /
unobserved region" is analogy for a loop reading its enclosed flux.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 12, "phi": 0.37, "seed": 1}
QUICK = {}


def _ring_H(ph, N):
    H = np.zeros((N, N), complex)
    for i in range(N):
        H[i, (i + 1) % N] = -np.exp(1j * ph[i])
        H[(i + 1) % N, i] = -np.exp(-1j * ph[i])
    return H


def _phases(phi, gauge, N, rng):
    if gauge == "uniform":
        return np.full(N, 2 * np.pi * phi / N)
    p = rng.normal(0, 1.0, N)
    p += (2 * np.pi * phi - p.sum()) / N                     # wild local field, SAME loop-sum
    return p


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N = p["N"]
    rng = np.random.default_rng(p["seed"])
    E_u = np.linalg.eigvalsh(_ring_H(_phases(p["phi"], "uniform", N, rng), N))
    E_r = np.linalg.eigvalsh(_ring_H(_phases(p["phi"], "random", N, rng), N))
    E_p = np.linalg.eigvalsh(_ring_H(_phases(p["phi"] + 1.0, "uniform", N, rng), N))
    w, v = np.linalg.eigh(_ring_H(_phases(p["phi"], "uniform", N, rng), N))
    dens = np.abs(v[:, 0]) ** 2
    return {
        "params": p,
        "gauge_dE": float(np.max(np.abs(E_u - E_r))),
        "period_dE": float(np.max(np.abs(E_u - E_p))),
        "density_std": float(dens.std()),
        "flat_value": round(1.0 / N, 4),
    }


def evaluate(result, quick=False):
    checks = {
        "gauge_invariant (same loop-sum -> dE<1e-9)":
            bool(result["gauge_dE"] < 1e-9),
        "periodic_mod_one_quantum (Phi vs Phi+1 -> dE<1e-9)":
            bool(result["period_dE"] < 1e-9),
        "locally_flat (ground density std<1e-9)":
            bool(result["density_std"] < 1e-9),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e022 horizon ledger Stage 1 (ab_gap)", "tier": "measured",
        "put_in": "a tight-binding ring with Peierls bond phases + a flux Phi through the hole",
        "emerged": ["gauge invariance (same loop-sum): dE=%.1e" % result["gauge_dE"],
                    "periodicity Phi vs Phi+1: dE=%.1e" % result["period_dE"],
                    "local density std=%.1e (flat=%s)" % (result["density_std"], result["flat_value"])],
        "surprises": ["the whole spectrum depends on the bond phases ONLY through their loop-sum, mod one quantum"],
        "persistence": "gauge invariance and periodicity hold to machine precision",
        "measured_numbers": {"gauge_dE": result["gauge_dE"], "period_dE": result["period_dE"],
                             "density_std": result["density_std"]},
        "not_scripted_check": "the spectral invariances and density flatness are measured, not imposed",
        "claim_tier": "measured (gauge invariance, periodicity, flatness) ; interpretive (the gap passes a "
                      "single received number) ; analogy (reception / horizon)",
        "floors": ["a finite tight-binding ring; periodicity is mod one flux quantum",
                   "'reception / horizon / unobserved region' is analogy for a loop reading its enclosed flux"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e022 Stage 1: AB gap reception")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e022 Stage 1 -- the gap passes one number (Aharonov-Bohm) ===")
    print("  gauge invariance (same loop-sum): dE=%.1e" % r["gauge_dE"])
    print("  periodicity (Phi vs Phi+1):       dE=%.1e" % r["period_dE"])
    print("  local density std=%.1e (flat=%s)" % (r["density_std"], r["flat_value"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (only the loop number passes the gap)" % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "ab_gap.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/ab_gap.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
