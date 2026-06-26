#!/usr/bin/env python3
"""e015 Stage 1 -- the vessel CLOSES only while it is DRIVEN (open-closed duality).

A Gray-Scott self-replicating spot is an open dissipative structure: it is fed by
a throughflow F (the drive) and maintains its own boundary and metabolism. The
local laws never say "stay alive" or "die if unfed". We MEASURE:
  * DRIVEN (F in the self-replication window): the pattern SELF-MAINTAINS and
    PROLIFERATES (total v and survival area grow), and SELF-HEALS -- excise half
    of it and it regrows.
  * UNDRIVEN (cut F -> 0): the closure cannot be sustained against decay; total v
    collapses to 0 (death).
  * a CRITICAL drive: sweeping F shows a survival WINDOW -- too little or too much
    throughflow and the structure dies.

So the vessel is OPEN (throughflow-driven) AND CLOSED (its boundary/metabolism
sustain each other) at once, and cutting the drive unbinds the closure. This is
Schrodinger's "order sustained against decay" / Prigogine dissipative structure /
the kinematics of autopoiesis -- as a measured drive-dependence.

Floors: Gray-Scott is a known reaction-diffusion system; "vessel/closure/death"
is interpretive/analogy; the maze/spot pattern is not a single cell; we did NOT
make life. Fixed lattice.

MODULE:   e015_vessel_closure
QUESTION: Is the vessel an open(driven)+closed(self-maintaining) dissipative structure that dies when the drive is cut?
PUT IN:   Gray-Scott RD + feed rate F (throughflow). "Die if F is cut" is NOT put in.
EMERGED:  (measured) driven -> self-maintain/heal/proliferate; F->0 -> total v->0 (death); a critical F window.
CLAIM TIER: measured(persist/collapse, heal, drive-dependence) ; interpretive(open-closed duality) ; analogy(autopoiesis).
KNOWN MATCH: Gray-Scott (Pearson); dissipative structures (Prigogine); autopoiesis (Maturana-Varela).
STATUS:   GREEN (drive-dependence + self-heal measured; "vessel/closure/death/life" is analogy).
A_OR_B:   (A) faithful. Hand input = Gray-Scott RD + a throughflow F; the open-closed behaviour emerges.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"L": 96, "Du": 0.16, "Dv": 0.08, "F": 0.0367, "k": 0.0649,
           "grow_steps": 12000, "death_steps": 8000, "heal_steps": 12000,
           "F_list": [0.01, 0.02, 0.0367, 0.05, 0.06, 0.08], "sweep_steps": 16000,
           "seed_r": 6, "seed": 1}
QUICK = {"L": 64, "grow_steps": 8000, "death_steps": 5000, "heal_steps": 8000,
         "F_list": [0.01, 0.0367, 0.08], "sweep_steps": 9000}


def _lap(a):
    return (-4.0 * a + np.roll(a, 1, 0) + np.roll(a, -1, 0)
            + np.roll(a, 1, 1) + np.roll(a, -1, 1))


def _seed(L, r, sd):
    u = np.ones((L, L))
    v = np.zeros((L, L))
    c = L // 2
    u[c - r:c + r, c - r:c + r] = 0.5
    v[c - r:c + r, c - r:c + r] = 0.25
    v += 0.01 * np.random.default_rng(sd).random((L, L))
    return u, v


def _step(u, v, F, k, Du, Dv, n):
    for _ in range(n):
        uvv = u * v * v
        u = u + Du * _lap(u) - uvv + F * (1.0 - u)
        v = v + Dv * _lap(v) + uvv - (F + k) * v
    return u, v


def _totv(v):
    return float(v.sum())


def _area(v):
    return float((v > 0.2).mean())


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    Du, Dv, F, k = p["Du"], p["Dv"], p["F"], p["k"]
    # grow under drive
    u, v = _seed(p["L"], p["seed_r"], p["seed"])
    u, v = _step(u, v, F, k, Du, Dv, p["grow_steps"])
    grown_totv = _totv(v)
    grown_area = _area(v)
    # cut the drive -> death
    ud, vd = u.copy(), v.copy()
    ud, vd = _step(ud, vd, 0.0, k, Du, Dv, p["death_steps"])
    dead_totv = _totv(vd)
    # self-heal: excise half, keep drive
    uh, vh = u.copy(), v.copy()
    uh[:p["L"] // 2, :] = 1.0
    vh[:p["L"] // 2, :] = 0.0
    excised_totv = _totv(vh)
    uh, vh = _step(uh, vh, F, k, Du, Dv, p["heal_steps"])
    healed_totv = _totv(vh)
    # critical-F sweep
    sweep = []
    for Fx in p["F_list"]:
        us, vs = _seed(p["L"], p["seed_r"], p["seed"])
        us, vs = _step(us, vs, Fx, k, Du, Dv, p["sweep_steps"])
        sweep.append({"F": Fx, "total_v": round(_totv(vs), 1),
                      "area": round(_area(vs), 3), "alive": bool(_totv(vs) > 1.0)})
    alive_F = [s["F"] for s in sweep if s["alive"]]
    return {
        "params": p,
        "grown_total_v": round(grown_totv, 1), "grown_area": round(grown_area, 3),
        "dead_total_v": round(dead_totv, 2),
        "death_on_cut": bool(dead_totv < 0.05 * grown_totv),
        "self_maintains": bool(grown_totv > 10.0 and grown_area > 0.05),
        "excised_total_v": round(excised_totv, 1), "healed_total_v": round(healed_totv, 1),
        "regen_fraction": round(healed_totv / grown_totv, 3) if grown_totv else 0.0,
        # the documented result is near-complete regrowth (~98%), so gate strictly
        "self_heals": bool(healed_totv >= 0.9 * grown_totv),
        "F_sweep": sweep,
        "survival_window": [min(alive_F), max(alive_F)] if alive_F else [],
        # a BOUNDED window: survival in the middle, death on BOTH the low-F and
        # high-F ends (AND, not OR -- CodeRabbit P1)
        "has_critical_F": bool(alive_F and not sweep[0]["alive"]
                               and not sweep[-1]["alive"]),
    }


def evaluate(result, quick=False):
    checks = {
        "self_maintains_when_driven": result["self_maintains"],
        "death_when_drive_cut(F->0)": result["death_on_cut"],
        "self_heals(excise->regrow)": result["self_heals"],
        "critical_drive_window": result["has_critical_F"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e015 vessel closure (drive-dependence)", "tier": "measured",
        "put_in": "Gray-Scott RD + throughflow F; 'die if unfed' not put in",
        "emerged": ["driven -> self-maintain/proliferate (total v %.0f) and SELF-HEAL (excise %.0f -> regrow %.0f)"
                    % (result["grown_total_v"], result["excised_total_v"], result["healed_total_v"]),
                    "cut the drive (F->0) -> total v -> %.2f (death)" % result["dead_total_v"],
                    "a survival WINDOW in F: %s (too little/much drive -> death)" % result["survival_window"]],
        "surprises": ["the closure unbinds the moment the throughflow stops -- open AND closed at once"],
        "persistence": "sustained only while driven; collapses without throughflow",
        "measured_numbers": {"grown_total_v": result["grown_total_v"],
                             "dead_total_v": result["dead_total_v"],
                             "healed_total_v": result["healed_total_v"],
                             "survival_window": result["survival_window"]},
        "not_scripted_check": "death emerges from cutting F; no death rule is written in",
        "claim_tier": "measured (persist/collapse, heal, drive-dependence) ; interpretive (open-closed) ; analogy (autopoiesis)",
        "floors": ["Gray-Scott is a known RD system; 'vessel/closure/death/life' is analogy; not a single cell",
                   "fixed lattice; we did NOT make life"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e015 vessel closure")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e015 vessel closure: open(driven) + closed(self-maintaining) ===")
    print("  driven: total_v=%.0f area=%.3f (self-maintain/proliferate)"
          % (r["grown_total_v"], r["grown_area"]))
    print("  drive cut (F->0): total_v=%.2f (death=%s)" % (r["dead_total_v"], r["death_on_cut"]))
    print("  self-heal: %.0f -> excise %.0f -> regrow %.0f (heals=%s)"
          % (r["grown_total_v"], r["excised_total_v"], r["healed_total_v"], r["self_heals"]))
    print("  F sweep (survival window %s):" % r["survival_window"])
    for s in r["F_sweep"]:
        print("    F=%.4f: total_v=%7.1f area=%.3f %s"
              % (s["F"], s["total_v"], s["area"], "ALIVE" if s["alive"] else "dead"))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (drive-dependence + self-heal measured; 'vessel/closure/death' is analogy)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.dirname(__file__)
        with open(os.path.join(out, "result.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote result.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
