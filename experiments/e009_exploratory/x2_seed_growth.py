#!/usr/bin/env python3
"""e009 X2 -- from a seed, something grows (morphogenesis, no branching ordered).

Tier A (anchor, KNOWN): Gray-Scott reaction-diffusion from a single seed. The
local rule never says "branch" or "replicate"; yet from one seed the pattern
self-replicates / branches. Measured: component count and active area grow.

Tier B/C (plausible -> unknown): add a one-directional gradient (a light/gravity-
like bias) to the feed rate F. Measured: does the growth become DIRECTIONAL (the
centre of mass drifts along the gradient, growth is asymmetric)? Also a
box-counting fractal dimension of the grown structure.

Floors: "plant-like" is analogy / a description of the observed form, NOT a
claim of life. The morphology TYPE is not predicted (frontier-observation); we
observe what the local rule produces.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy import ndimage

_RESULTS = os.path.join(os.path.dirname(__file__), "results")


def _lap(a):
    return (-4.0 * a + np.roll(a, 1, 0) + np.roll(a, -1, 0)
            + np.roll(a, 1, 1) + np.roll(a, -1, 1))


def gray_scott(L, Du, Dv, F, k, steps, grad=0.0, seed_r=4, seed=1):
    u = np.ones((L, L))
    v = np.zeros((L, L))
    c = L // 2
    u[c - seed_r:c + seed_r, c - seed_r:c + seed_r] = 0.5
    v[c - seed_r:c + seed_r, c - seed_r:c + seed_r] = 0.25
    rng = np.random.default_rng(seed)
    v += 0.01 * rng.random((L, L))
    Fmap = F + grad * (np.arange(L)[:, None] / L - 0.5)   # gradient along axis 0
    snaps = []
    for s in range(steps):
        uvv = u * v * v
        u += Du * _lap(u) - uvv + Fmap * (1.0 - u)
        v += Dv * _lap(v) + uvv - (Fmap + k) * v
        if s % (steps // 5) == 0:
            snaps.append(int((v > 0.2).sum()))
    return u, v, snaps


def _components(v):
    return int(ndimage.label(v > 0.2)[1])


def _fractal_dim(v):
    """Box-counting fractal dimension of the active (v>0.2) set."""
    mask = v > 0.2
    if mask.sum() < 10:
        return 0.0
    L = mask.shape[0]
    sizes = [2, 4, 8, 16, 32]
    counts = []
    for b in sizes:
        n = L // b
        sub = mask[:n * b, :n * b].reshape(n, b, n, b).any(axis=(1, 3))
        counts.append(max(int(sub.sum()), 1))
    d = -np.polyfit(np.log(sizes), np.log(counts), 1)[0]
    return float(d)


def _com_drift(v):
    """Centre-of-mass offset from grid centre along the gradient axis (axis 0)."""
    mask = v > 0.2
    if mask.sum() == 0:
        return 0.0
    com = ndimage.center_of_mass(mask)
    return float(com[0] - v.shape[0] / 2.0)


def simulate(quick=False):
    L = 96 if quick else 160
    steps = 2500 if quick else 5000
    # Tier A: self-replication (mitosis) and branching (coral)
    _, v_mit, snap_mit = gray_scott(L, 0.16, 0.08, 0.0367, 0.0649, steps)
    _, v_cor, snap_cor = gray_scott(L, 0.16, 0.08, 0.055, 0.062, steps)
    # Tier B: gradient -> directional growth (coral regime + F gradient)
    _, v_grad, _ = gray_scott(L, 0.16, 0.08, 0.055, 0.062, steps, grad=0.02)
    return {
        "params": {"L": L, "steps": steps},
        "tierA_mitosis": {"components": _components(v_mit),
                          "active_area_snaps": snap_mit,
                          "area_grows": bool(snap_mit[-1] > 3 * max(snap_mit[1], 1))},
        "tierA_coral": {"components": _components(v_cor),
                        "active_area_snaps": snap_cor,
                        "fractal_dim": round(_fractal_dim(v_cor), 3),
                        "area_grows": bool(snap_cor[-1] > snap_cor[1])},
        "tierB_gradient": {"com_drift_along_gradient": round(_com_drift(v_grad), 2),
                           "directional": bool(abs(_com_drift(v_grad)) > 3.0),
                           "fractal_dim": round(_fractal_dim(v_grad), 3)},
    }


def _atlas(r):
    return [
        {"experiment": "X2", "tier": "A",
         "put_in": "Gray-Scott reaction-diffusion + one seed patch",
         "emerged": ["self-replication (mitosis): 1 seed -> %d components"
                     % r["tierA_mitosis"]["components"],
                     "branching growth (coral), fractal_dim=%.2f"
                     % r["tierA_coral"]["fractal_dim"]],
         "surprises": [],
         "persistence": "area grows: mitosis=%s coral=%s"
         % (r["tierA_mitosis"]["area_grows"], r["tierA_coral"]["area_grows"]),
         "measured_numbers": {"mitosis_components": r["tierA_mitosis"]["components"],
                              "coral_fractal_dim": r["tierA_coral"]["fractal_dim"]},
         "not_scripted_check": "the local rule never says branch/replicate; form is measured",
         "claim_tier": "measured (components/area/fractal dim) ; analogy (plant-like)",
         "floors": ["plant-like is analogy / a description, NOT life"]},
        {"experiment": "X2", "tier": "B",
         "put_in": "Gray-Scott + a one-directional gradient in feed rate F",
         "emerged": ["directional growth" if r["tierB_gradient"]["directional"]
                     else "near-symmetric growth"],
         "surprises": ["CoM drift along gradient = %.2f cells"
                       % r["tierB_gradient"]["com_drift_along_gradient"]],
         "persistence": "directional=%s" % r["tierB_gradient"]["directional"],
         "measured_numbers": {"com_drift": r["tierB_gradient"]["com_drift_along_gradient"]},
         "not_scripted_check": "growth direction is measured (CoM), not imposed",
         "claim_tier": "measured (directionality) ; frontier-observation (morphology type)",
         "floors": ["fixed lattice; morphology type not predicted"]},
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e009 X2 seed growth")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== X2 Tier A: morphogenesis from one seed ===")
    print("  mitosis: 1 seed -> %d components (self-replication), area_snaps %s"
          % (r["tierA_mitosis"]["components"], r["tierA_mitosis"]["active_area_snaps"]))
    print("  coral:   %d components, fractal_dim=%.2f, area_snaps %s"
          % (r["tierA_coral"]["components"], r["tierA_coral"]["fractal_dim"],
             r["tierA_coral"]["active_area_snaps"]))
    print("=== X2 Tier B: gradient -> directional growth ===")
    print("  CoM drift along gradient = %.2f cells, directional=%s, fractal_dim=%.2f"
          % (r["tierB_gradient"]["com_drift_along_gradient"],
             r["tierB_gradient"]["directional"], r["tierB_gradient"]["fractal_dim"]))
    ok = (r["tierA_mitosis"]["components"] > 3 and r["tierA_coral"]["area_grows"]
          and r["tierB_gradient"]["directional"])
    print("STATUS: %s (Tier A measured replication/branching; Tier B directional)"
          % ("GREEN" if ok else "YELLOW (see numbers)"))
    if not args.no_write and not args.quick:
        os.makedirs(_RESULTS, exist_ok=True)
        with open(os.path.join(_RESULTS, "x2.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/x2.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
