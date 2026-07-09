#!/usr/bin/env python3
"""e021 robustness (LAW.md audit 6): these GL relaxations are DETERMINISTIC (a tanh init, no noise), so
the RNG seed is irrelevant -- the meaningful robustness axes are the GRID SIZE, the reader radius, and
the droplet radius. The self-reading (ring winding = core winding, position invariance) and the
annihilation threshold (near anti kills, far anti survives) must survive those sweeps. We vary them and
confirm."""

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


def _sr_case(N, read_R):
    p = dict(SR.DEFAULT)
    p.update({"N": N, "read_R": read_R, "steps": 900})
    X, Y, r, K2 = SR._grid(N)
    c = N / 2
    reads_ok = True
    for w in (-1, 0, 1):
        psi = SR._relax_vortex(w, p, X, Y, r, K2)
        if abs(ring_winding(psi, c, c, read_R, n=400) - w) > 0.1:
            reads_ok = False
    psi = SR._relax_vortex(1, p, X, Y, r, K2, jitter=(N // 12, N // 16))
    pos_ok = abs(ring_winding(psi, c, c, read_R, n=400) - 1.0) < 0.1
    return {"N": N, "read_R": read_R, "reads_ok": bool(reads_ok), "pos_ok": bool(pos_ok),
            "ok": bool(reads_ok and pos_ok)}


def _va_case(N, Rdrop, read_R):
    p = dict(VA.DEFAULT)
    p.update({"N": N, "Rdrop": Rdrop, "read_R": read_R, "steps": 1500})
    X, Y, r, K2 = VA._grid(N)
    c = N / 2
    d_near, d_far = 7, int(Rdrop * 0.6)
    near = VA._evolve(VA._field([(0, 0, 1), (d_near, 0, -1)], X, Y, r, Rdrop, N), p, r, K2)
    far = VA._evolve(VA._field([(0, 0, 1), (d_far, 0, -1)], X, Y, r, Rdrop, N), p, r, K2)
    near_dead = abs(ring_winding(near, c, c, read_R, n=512)) < 0.5 and VA._core_amp(near, N) > 0.5
    far_alive = abs(ring_winding(far, c, c, read_R, n=512)) > 0.5
    return {"N": N, "Rdrop": Rdrop, "read_R": read_R,
            "near_dead": bool(near_dead), "far_alive": bool(far_alive),
            "ok": bool(near_dead and far_alive)}


def simulate(quick=False):
    # sweep grid size + reader radius (self_receiver) and grid + droplet + reader (vessel_alive)
    sr_axes = [(128, 40), (160, 50)] if quick else [(128, 32), (128, 45), (160, 50), (192, 60)]
    va_axes = [(160, 48, 18)] if quick else [(160, 48, 18), (176, 52, 20), (144, 44, 16)]
    sr = [_sr_case(N, R) for (N, R) in sr_axes]
    va = [_va_case(N, Rd, R) for (N, Rd, R) in va_axes]
    return {
        "self_receiver": sr, "vessel_alive": va,
        "sr_all_ok": all(c["ok"] for c in sr),
        "va_all_ok": all(c["ok"] for c in va),
        "robust": bool(all(c["ok"] for c in sr + va)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e021 robustness sweep (grid / radii, not seed)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e021 robustness (self-reading + annihilation threshold vs grid / radii) ===")
    for c in r["self_receiver"]:
        print("  self_receiver N=%s read_R=%s: ok=%s" % (c["N"], c["read_R"], c["ok"]))
    for c in r["vessel_alive"]:
        print("  vessel_alive N=%s Rdrop=%s read_R=%s: near_dead=%s far_alive=%s"
              % (c["N"], c["Rdrop"], c["read_R"], c["near_dead"], c["far_alive"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
