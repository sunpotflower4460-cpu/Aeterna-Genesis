#!/usr/bin/env python3
"""e024 robustness (LAW.md audit 6): the engine's gate SIGNS must survive seed / grid (Np) /
dt changes. Absolute currents and revolutions are floors; what must not move is:
ratchet rectification stays positive (asym=1) and null (asym=0); the rotor's three-phase
revolutions exceed the single-phase; the vessel dies on fuel cut. We sweep and confirm."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e024_vessel_engine import ratchet as R      # noqa: E402
from experiments.e024_vessel_engine import motor as M        # noqa: E402
from experiments.e024_vessel_engine import vessel_motor as V  # noqa: E402


def _ratchet_case(seed, Np, dt):
    p = dict(R.DEFAULT)
    p.update({"seed": seed, "Np": Np, "dt": dt, "T": 60.0})
    rng = np.random.default_rng(seed)
    rect_rat = R._rectification(4.5, 1.0, p, rng)
    rect_sym = R._rectification(4.5, 0.0, p, rng)
    return {"seed": seed, "Np": Np, "dt": dt,
            "rect_ratchet": round(rect_rat, 3), "rect_symmetric": round(rect_sym, 3),
            "ok": bool(rect_rat > 0.2 and abs(rect_sym) < 0.1)}


def _motor_case(seed, Np):
    p = dict(M.DEFAULT)
    p.update({"seed": seed, "Np": Np, "T": 60.0})
    rng = np.random.default_rng(seed)
    rot = M._spin("rot", p, rng)
    puls = M._spin("puls", p, rng, bias=0.0)
    return {"seed": seed, "Np": Np, "rev_rot": round(rot, 2), "rev_puls": round(puls, 2),
            "ok": bool(rot > 5.0 and abs(puls) < 0.5)}


def _vessel_case(seed, Np):
    p = dict(V.DEFAULT)
    p.update({"seed": seed, "Np": Np, "T": 110.0, "fuel_cut": 55.0})
    rng = np.random.default_rng(seed)
    _, _, psi_fueled, _ = V.run(5.0, p, rng, vessel=True)
    _, _, psi_cut, _ = V.run(5.0, p, rng, vessel=True, fuel_cut=p["fuel_cut"])
    rate_minus = V.run(-5.0, p, rng)[0]
    return {"seed": seed, "Np": Np, "psi_fueled": round(psi_fueled, 3),
            "psi_cut": round(psi_cut, 3), "rate_minus5": round(rate_minus, 3),
            "ok": bool(psi_fueled > 0.5 and psi_cut < 0.2 and rate_minus < -0.1)}


def simulate(quick=False):
    seeds = [0, 1, 2] if quick else [0, 1, 2, 3, 4]
    ratchet = [_ratchet_case(s, 700, 0.005) for s in seeds]
    if not quick:
        ratchet.append(_ratchet_case(0, 1200, 0.004))       # finer grid + dt
    motor = [_motor_case(s, 200) for s in seeds]
    vessel = [_vessel_case(s, 350) for s in seeds]
    return {
        "ratchet": ratchet, "motor": motor, "vessel": vessel,
        "ratchet_all_ok": all(c["ok"] for c in ratchet),
        "motor_all_ok": all(c["ok"] for c in motor),
        "vessel_all_ok": all(c["ok"] for c in vessel),
        "robust": bool(all(c["ok"] for c in ratchet + motor + vessel)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e024 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e024 robustness (gate signs vs seed / Np / dt) ===")
    print("  ratchet all ok: %s" % r["ratchet_all_ok"])
    print("  motor all ok:   %s" % r["motor_all_ok"])
    print("  vessel all ok:  %s" % r["vessel_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
