#!/usr/bin/env python3
"""e034 -- spatial cooperation WITHOUT agents: a bistable reaction-diffusion field reproduces e027.

MODULE:   e034_field_cooperation_front
QUESTION: e027 Stage 3 got "well-mixed cooperation collapses; spatial cooperation survives; but above a
          temptation threshold even structure fails" from an AGENT grid (Nowak-May: cells copy the best
          neighbor) -- a floor (LAW.md: not a field). Do the SAME three facts emerge from a REAL FIELD
          EQUATION with no agents, no imitation, no payoff bookkeeping?
PUT IN:   the bistable (Nagumo / Schlogl) reaction-diffusion equation for a local cooperator DENSITY field
          u(x) in [0,1]:  u_t = D*lap u + u*(1-u)*(u-a).  Two stable states u=0 (all-defect) and u=1
          (all-cooperate); u=a is the unstable threshold (the temptation). The only knob is a (the
          field-native analog of e027's temptation b). NO "well-mixed collapses", NO "spatial survives",
          NO threshold value is put in -- all are measured.
EMERGED:  (measured) mean-field (well-mixed, no diffusion): a sub-threshold cooperator seed decays to
          defect. Spatial: a cooperator domain INVADES the defect state via a traveling front when a<1/2
          (front velocity > 0), so cooperation spreads in a cluster. The invasion REVERSES at the Maxwell
          point a=1/2 (an emergent threshold, never put in); the front speed matches the Nagumo law
          c = sqrt(D/2)*(1-2a).
CLAIM TIER: measured(well-mixed decay; front velocity vs a; sign change at the Maxwell point; Nagumo-speed
          match) ; interpretive(spatial structure lets the favored state INVADE, and the survival is
          conditional on the temptation via a front-velocity sign change) ; analogy(cooperation, the major
          transition, multicellularity).
KNOWN MATCH: Nagumo / Schlogl bistable fronts; the Maxwell (equal-area) point a=1/2; front speed
          c = sqrt(D/2)(1-2a). All established reaction-diffusion physics.
STATUS:   GREEN (gates on physical field quantities: front velocity, its sign change, the mean-field state).
A_OR_B:   (A) faithful. Hand input = the bistable RD field law + a; the collapse, the invasion, the
          threshold a=1/2 and the front speed are emergent and measured.

THE TRAP (designer hit it, we avoid it): do NOT put the threshold in. We set ONE reaction parameter a and a
real diffusion law; the well-mixed collapse, the traveling-front invasion, the stall at a=1/2 and the front
speed are OUTPUTS matching Nagumo/Schlogl theory. Well-mixed is the SAME reaction with the Laplacian removed.

Floors: "cooperation / defection / major transition" is analogy for the two bistable states of a density
field. 同じ数学≠同じもの: this does NOT claim the evolution of cooperation IS a bistable front -- it shows the
SAME three facts (well-mixed collapse / spatial invasion / conditional threshold) emerge in a field with no
agents. This is cooperation STABILITY as a front, NOT a full major transition. (A) faithful: the RD law is
put in by hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"as": [0.30, 0.40, 0.45, 0.50, 0.55, 0.60], "D": 1.0, "N": 400, "dx": 1.0, "dt": 0.05,
           "steps": 3000, "a_below": 0.40, "a_above": 0.60, "wm_seed": 0.2, "wm_dt": 0.01,
           "wm_steps": 5000}
QUICK = {"as": [0.30, 0.40, 0.50, 0.60], "N": 300, "steps": 2000}


def _react(u, a):
    return u * (1 - u) * (u - a)


def _well_mixed(u0, a, p):
    """Mean-field (spatially uniform = reshuffled): the reaction ODE with NO Laplacian."""
    u = float(u0)
    for _ in range(p["wm_steps"]):
        u = min(max(u + p["wm_dt"] * _react(u, a), 0.0), 1.0)
    return u


def _front_velocity(a, p):
    """1D bistable front from a step IC (u=1 left, u=0 right); track the u=0.5 crossing -> velocity."""
    N, dx, dt, D = p["N"], p["dx"], p["dt"], p["D"]
    u = np.where(np.arange(N) < N // 2, 1.0, 0.0).astype(float)
    u[:5] = 1.0
    u[-5:] = 0.0

    def lap(v):
        return (np.roll(v, 1) + np.roll(v, -1) - 2 * v) / dx ** 2

    def front_pos(v):
        idx = np.where(v >= 0.5)[0]
        return idx[-1] if idx.size else 0

    p0 = front_pos(u)
    for _ in range(p["steps"]):
        v = u
        u = u + dt * (D * lap(v) + _react(v, a))
        u[:5] = 1.0
        u[-5:] = 0.0
        u = np.clip(u, 0.0, 1.0)
    p1 = front_pos(u)
    return (p1 - p0) * dx / (p["steps"] * dt)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for a in p["as"]:
        c = _front_velocity(a, p)
        c_th = np.sqrt(p["D"] / 2.0) * (1 - 2 * a)
        rows.append({"a": a, "front_velocity": round(float(c), 3), "nagumo_speed": round(float(c_th), 3)})
    # emergent Maxwell point: interpolate the a where the front velocity crosses zero
    aa = np.array([r["a"] for r in rows])
    cc = np.array([r["front_velocity"] for r in rows])
    maxwell = float(np.interp(0.0, cc[::-1], aa[::-1]))     # cc decreasing in a
    speed_err = float(np.max(np.abs(cc - np.array([r["nagumo_speed"] for r in rows]))))
    wm_below = _well_mixed(p["wm_seed"], p["a_below"], p)   # seed 0.2 < a=0.40 -> should decay
    # a cooperator domain below the Maxwell point invades (c>0); above it retreats (c<0)
    c_below = next(r["front_velocity"] for r in rows if r["a"] == p["a_below"])
    c_above = next(r["front_velocity"] for r in rows if r["a"] == p["a_above"])
    return {
        "params": p, "rows": rows,
        "maxwell_point": round(maxwell, 3), "nagumo_speed_err": round(speed_err, 3),
        "wellmixed_below_final": round(wm_below, 3),
        "front_below_maxwell": round(c_below, 3), "front_above_maxwell": round(c_above, 3),
    }


def evaluate(result, quick=False):
    checks = {
        "wellmixed_seed_decays_below_threshold (sub-threshold uniform seed -> defect state u<0.1)":
            bool(result["wellmixed_below_final"] < 0.1),
        "spatial_front_invades_below_maxwell_reverses_above (c>0 for a<0.5, c<0 for a>0.5)":
            bool(result["front_below_maxwell"] > 0.02 and result["front_above_maxwell"] < -0.02),
        "front_speed_matches_nagumo_and_maxwell_at_half (|c-theory|<0.03; zero-crossing a_c~0.5)":
            bool(result["nagumo_speed_err"] < 0.03 and abs(result["maxwell_point"] - 0.5) < 0.03),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e034 field cooperation front (bistable reaction-diffusion, no agents)", "tier": "measured",
        "put_in": "bistable Nagumo/Schlogl reaction-diffusion u_t = D lap u + u(1-u)(u-a) for a cooperator "
                  "density field; one reaction parameter a; well-mixed = same reaction with the Laplacian "
                  "removed. NO agents / imitation / payoff bookkeeping",
        "emerged": ["front velocity vs temptation a (with the Nagumo speed): %s"
                    % [(r["a"], r["front_velocity"], r["nagumo_speed"]) for r in result["rows"]],
                    "emergent Maxwell point (zero-velocity threshold, never put in): a_c=%s" % result["maxwell_point"],
                    "well-mixed sub-threshold seed -> %s (defect)" % result["wellmixed_below_final"]],
        "surprises": ["a single reaction parameter a gives a traveling front whose direction flips at exactly "
                      "a=1/2 (the Maxwell point) with a speed matching Nagumo theory -- the threshold is never put in"],
        "persistence": "the invading state fills the domain; the stall at a=1/2 is the equal-area (Maxwell) balance",
        "measured_numbers": {"rows": result["rows"], "maxwell_point": result["maxwell_point"],
                             "nagumo_speed_err": result["nagumo_speed_err"],
                             "wellmixed_below_final": result["wellmixed_below_final"]},
        "not_scripted_check": "only a and the RD law are set; the collapse, the invasion, the threshold a=1/2 "
                              "and the front speed are measured from the field",
        "claim_tier": "measured (well-mixed decay; front velocity; sign change at Maxwell; Nagumo-speed match) "
                      "; interpretive (spatial structure lets the favored state invade; survival is conditional "
                      "on the temptation) ; analogy (cooperation / major transition)",
        "floors": ["'cooperation / defection / major transition' is analogy for the two bistable field states",
                   "同じ数学≠同じもの: this does NOT claim the evolution of cooperation IS a bistable front; the "
                   "SAME three facts (collapse / invasion / threshold) emerge in a field with no agents",
                   "this is cooperation STABILITY as a front, NOT a full major transition (group reproduction / "
                   "division of labor are elsewhere)",
                   "(A) faithful: the reaction-diffusion law is put in by hand, not derived"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e034 field cooperation front (bistable RD, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e034 -- spatial cooperation from a FIELD (bistable reaction-diffusion, no agents) ===")
    print("  temptation a | front velocity | Nagumo speed sqrt(D/2)(1-2a)")
    for row in r["rows"]:
        print("     a=%.2f | c=%+.3f | theory=%+.3f" % (row["a"], row["front_velocity"], row["nagumo_speed"]))
    print("  emergent Maxwell point a_c=%s (theory 0.5); well-mixed sub-threshold seed -> %s (defect)"
          % (r["maxwell_point"], r["wellmixed_below_final"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (spatial cooperation as a bistable front; threshold a=1/2 emergent)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "cooperation_front.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/cooperation_front.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
