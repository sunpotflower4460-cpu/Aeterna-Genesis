#!/usr/bin/env python3
"""e021 robustness (LAW.md audit 6): the self-reading and the annihilation threshold must survive the
seed and grid. Absolute currents / critical distances are floors; what must not move is: the ring reads
the core winding for w=-1..1 and is position-invariant; a near anti annihilates the core while a far
anti does not. We sweep seeds and confirm."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import ring_winding                         # noqa: E402
from experiments.e021_self_receiver import self_receiver as SR  # noqa: E402
from experiments.e021_self_receiver import vessel_alive as VA    # noqa: E402


def _sr_case(seed):
    p = dict(SR.DEFAULT)
    p.update({"seed": seed, "steps": 900})
    X, Y, r, K2 = SR._grid(p["N"])
    c = p["N"] / 2
    reads_ok = True
    for w in (-1, 0, 1):
        psi = SR._relax_vortex(w, p, X, Y, r, K2)
        if abs(ring_winding(psi, c, c, p["read_R"], n=400) - w) > 0.1:
            reads_ok = False
    psi = SR._relax_vortex(1, p, X, Y, r, K2, jitter=(10, 6))
    pos_ok = abs(ring_winding(psi, c, c, p["read_R"], n=400) - 1.0) < 0.1
    return {"seed": seed, "reads_ok": bool(reads_ok), "pos_ok": bool(pos_ok),
            "ok": bool(reads_ok and pos_ok)}


def _va_case(seed):
    p = dict(VA.DEFAULT)
    p.update({"seed": seed, "steps": 1500, "dists": [7, 30]})
    X, Y, r, K2 = VA._grid(p["N"])
    c = p["N"] / 2
    near = VA._evolve(VA._field([(0, 0, 1), (7, 0, -1)], X, Y, r, p["Rdrop"], p["N"]), p, r, K2)
    far = VA._evolve(VA._field([(0, 0, 1), (30, 0, -1)], X, Y, r, p["Rdrop"], p["N"]), p, r, K2)
    near_dead = abs(ring_winding(near, c, c, p["read_R"], n=512)) < 0.5 and VA._core_amp(near, p["N"]) > 0.5
    far_alive = abs(ring_winding(far, c, c, p["read_R"], n=512)) > 0.5
    return {"seed": seed, "near_dead": bool(near_dead), "far_alive": bool(far_alive),
            "ok": bool(near_dead and far_alive)}


def simulate(quick=False):
    seeds = [0, 1] if quick else [0, 1, 2]
    sr = [_sr_case(s) for s in seeds]
    va = [_va_case(s) for s in seeds]
    return {
        "self_receiver": sr, "vessel_alive": va,
        "sr_all_ok": all(c["ok"] for c in sr),
        "va_all_ok": all(c["ok"] for c in va),
        "robust": bool(all(c["ok"] for c in sr + va)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e021 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e021 robustness (self-reading + annihilation threshold vs seed) ===")
    print("  self_receiver all ok: %s" % r["sr_all_ok"])
    print("  vessel_alive all ok:  %s" % r["va_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
