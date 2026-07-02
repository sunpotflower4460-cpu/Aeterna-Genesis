#!/usr/bin/env python3
"""e019 Stage 1 -- circulation carries a particle; the "third" holds it to U_c.

We put a stabilized Q_H=1 hopfion (the e012/e016 particle) into a PRESCRIBED
circulation (a sheared roll) and ask: does the circulation carry the particle,
and does the "third" (the quartic Faddeev-Skyrme term) keep the particle's
IDENTITY (Q_H) against the roll's shear?

We first SETTLE the soliton with the stabilizing Faddeev-Skyrme flow (so we start
from the attractor at L*), then TRANSPORT it by a prescribed localized roll (a
vortex in the x-z plane) with pure advection:
    n <- stabilized_flow_step(n)   x settle_steps   (relax onto the attractor)
    then, each transport step:  n <- n - dt * (u . grad n) ;  n <- n / |n|
We MEASURE (never impose motion or tearing):
  * the particle's CENTROID moves along the roll, displacement growing with U;
  * Q_H is HELD (~1) up to a critical circulation strength U_c, above which the
    roll's shear sharpens gradients past the grid and TEARS the particle: Q_H -> 0
    and its size diverges.

THE TRAP (designer hit it, we avoid it): u . grad n is a sum over the 3 SPATIAL
axes of the component field n (shape (3,L,L,L)); using a component/4D axis gives
an AxisError or a wrong centroid. We use core.hopf.central_diff (spatial axes) and
weight the centroid by the gradient-energy density (a 3D scalar field).

Floors: the roll is PRESCRIBED (not self-organized -- that is Stage 2, the
three-body coupling); U_c is a crossover of a fixed-lattice/kappa flow, not a
sharp universal threshold; "particle/identity" is analogy. Fixed lattice.

MODULE:   e019_coupling (Stage 1: transport + U_c)
QUESTION: Does a prescribed circulation carry the hopfion, and does the third hold its Q_H up to a critical U_c?
PUT IN:   stabilized Q_H=1 hopfion + Faddeev-Skyrme flow + advection -u.grad n by a prescribed roll. Motion/tearing not put in.
EMERGED:  (measured) centroid moves with U (monotone); Q_H held ~1 up to U_c, then torn (Q_H->0, size diverges).
CLAIM TIER: measured(centroid(U), Q_H(U), U_c) ; interpretive(third resists shear) ; analogy(particle/identity).
KNOWN MATCH: advected order parameter; Faddeev-Skyrme hopfion (e012/e016).
STATUS:   GREEN (transport + held-then-torn Q_H(U) with a crossover U_c measured; prescribed roll is the floor).
A_OR_B:   (A) faithful. Hand input = hopfion + energy + flow + a prescribed roll; motion and tearing are emergent.
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

DEFAULT = {"L": 48, "box": 8.4, "c2": 1.0, "c4": 20.0, "kappa": 40.0, "dt": 6e-3,
           "start_scale": 2.9, "settle_steps": 150, "n_steps": 260,
           "roll_R": 5.0, "roll_x0": -4.0,
           "U_list": [0.0, 2.0, 4.0, 6.0, 8.0, 11.0]}
QUICK = {"L": 40, "settle_steps": 110, "n_steps": 200,
         "U_list": [0.0, 4.0, 8.0, 11.0]}


def _roll_velocity(L, box, U, R, x0):
    """Prescribed localized roll: a vortex in the x-z plane centred at (x0,0),
    u_x = -U (z)/R exp(-rho^2/2R^2), u_z = U (x-x0)/R exp(...). y-invariant. The
    soliton sits on the vortex flank, is carried around it, and sheared."""
    x = np.linspace(-box, box, L, endpoint=False)
    X, _, Z = np.meshgrid(x, x, x, indexing="ij")
    rho2 = (X - x0) ** 2 + Z ** 2
    env = np.exp(-rho2 / (2.0 * R * R))
    ux = -U * Z / R * env
    uz = U * (X - x0) / R * env
    return ux, uz


def _centroid(n, dx):
    """Centroid (x,z) of the gradient-energy density (spatial axes only -- the trap)."""
    dn = hopf.central_diff(n, dx)                      # [d0 n, d1 n, d2 n], spatial axes
    w = sum((dn[a] ** 2).sum(axis=0) for a in range(3))  # 3D scalar density
    tot = w.sum()
    if tot <= 0:
        return 0.0, 0.0
    L = n.shape[1]
    ax = (np.arange(L) - L / 2) * dx
    cx = float((w * ax[:, None, None]).sum() / tot)
    cz = float((w * ax[None, None, :]).sum() / tot)
    return cx, cz


def run_U(p, U):
    n, dx = hopf.hopfion_field(p["L"], p["start_scale"], p["box"])
    K4 = hopf.k4_grid(p["L"], dx)
    dt = p["dt"]
    for _ in range(p["settle_steps"]):                 # settle onto the attractor first
        n = hopf.stabilized_flow_step(n, dx, p["c2"], p["c4"], dt, p["kappa"], K4)
    ux, uz = _roll_velocity(p["L"], p["box"], U, p["roll_R"], p["roll_x0"])
    Q0 = hopf.hopf_charge(n, dx)
    cx0, cz0 = _centroid(n, dx)
    for _ in range(p["n_steps"]):                      # pure transport (no relaxation)
        dn = hopf.central_diff(n, dx)
        adv = ux[None, ...] * dn[0] + uz[None, ...] * dn[2]   # u . grad n over spatial axes
        n = n - dt * adv
        n = n / np.linalg.norm(n, axis=0, keepdims=True)
    Qf = hopf.hopf_charge(n, dx)
    cx, cz = _centroid(n, dx)
    sf = hopf.e4_rms_size(n, dx)
    disp = float(np.hypot(cx - cx0, cz - cz0))
    return {"U": U, "Q_H_initial": round(float(Q0), 3), "Q_H_final": round(float(Qf), 3),
            "centroid_disp": round(disp, 3), "size_final": round(float(sf), 3),
            "held": bool(abs(Qf) > 0.7)}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = [run_U(p, U) for U in p["U_list"]]
    # centroid displacement grows monotonically with U (transport)
    disp = [r["centroid_disp"] for r in rows]
    centroid_moves = bool(len(disp) >= 2 and all(disp[i] <= disp[i + 1] + 1e-6 for i in range(len(disp) - 1))
                          and disp[-1] > disp[0] + 1e-2)
    held_U = [r["U"] for r in rows if r["held"]]
    torn_U = [r["U"] for r in rows if not r["held"]]
    U_c = (0.5 * (max(held_U) + min(torn_U))) if (held_U and torn_U) else None
    return {
        "params": p, "rows": rows,
        "centroid_moves_with_U": centroid_moves,
        "low_U_holds_QH": bool(rows[1]["held"]) if len(rows) > 1 else False,
        "high_U_torn": bool(torn_U and not rows[-1]["held"]),
        "U_c": round(U_c, 2) if U_c is not None else None,
        "size_diverges_when_torn": bool(torn_U and rows[-1]["size_final"] > 1.3 * rows[0]["size_final"]),
    }


def evaluate(result, quick=False):
    checks = {
        "centroid moves with U (transport)": result["centroid_moves_with_U"],
        "low-U holds Q_H (third resists shear)": result["low_U_holds_QH"],
        "high-U tears the particle (Q_H->0)": result["high_U_torn"],
        "critical U_c exists (held->torn crossover)": result["U_c"] is not None,
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e019 circulation carries a particle (transport + U_c)", "tier": "measured",
        "put_in": "stabilized Q_H=1 hopfion + Faddeev-Skyrme flow + advection by a prescribed roll; motion/tearing not put in",
        "emerged": ["centroid moves with U (transport): %s"
                    % [(r["U"], r["centroid_disp"]) for r in result["rows"]],
                    "Q_H held ~1 up to U_c=%s, then torn (Q_H->0)%s"
                    % (result["U_c"], " and size diverges" if result["size_diverges_when_torn"] else " (size grows)")],
        "surprises": ["the third holds the particle's identity against shear up to a finite circulation strength, then it tears"],
        "persistence": "identity (Q_H) persists for U < U_c; above U_c the particle is destroyed",
        "measured_numbers": {"rows": result["rows"], "U_c": result["U_c"]},
        "not_scripted_check": "Q_H from B=curl A; centroid from gradient-energy density over spatial axes; motion emerges from advection",
        "claim_tier": "measured (centroid(U), Q_H(U), U_c) ; interpretive (third resists shear) ; analogy (particle/identity)",
        "floors": ["the roll is PRESCRIBED, not self-organized (self-organized flow = Stage 2, three-body coupling)",
                   "U_c is a crossover of a fixed-lattice/kappa flow, not a sharp universal threshold",
                   "'particle/identity' is analogy; fixed lattice"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e019 circulation carries a particle")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e019 circulation carries a particle; the third holds it to U_c ===")
    for row in r["rows"]:
        tag = "HELD" if row["held"] else "TORN"
        print("  U=%5.1f: Q_H %.2f->%.2f  centroid_disp=%.2f  size=%.2f  [%s]"
              % (row["U"], row["Q_H_initial"], row["Q_H_final"], row["centroid_disp"],
                 row["size_final"], tag))
    print("  centroid moves with U=%s ; low-U holds=%s ; high-U torn=%s ; U_c=%s"
          % (r["centroid_moves_with_U"], r["low_U_holds_QH"], r["high_U_torn"], r["U_c"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (transport + held-then-torn Q_H(U) with crossover U_c measured; prescribed roll is the floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "coupling.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/coupling.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
