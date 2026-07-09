#!/usr/bin/env python3
"""e028 robustness (LAW.md audit 6): the received-memory facts must survive the RNG seed (which sets the
random bits and the local noise) and grid size. Absolute capacity counts are finite-size floors; what
must not move is: topological bits are perfectly recovered under local noise (protected) while dynamical
bits erode, the capacity exceeds the reader dof, and the ring's winding is the nearest integer to Phi."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e028_topological_memory import memory as MEM   # noqa: E402
from experiments.e028_topological_memory import ring as RING     # noqa: E402


def _mem_case(seed):
    p = dict(MEM.DEFAULT)
    p.update({"seed": seed, "ks": [3, 7, 11], "noises": [0.0, 4.0], "noise_k": 7})
    # reuse the module's simulate by swapping DEFAULT via a shallow call
    saved = MEM.DEFAULT
    try:
        MEM.DEFAULT = p
        r = MEM.simulate(quick=False)
    finally:
        MEM.DEFAULT = saved
    ok = (r["topo_all_perfect"] and r["dyn_erodes"]
          and r["max_perfect_capacity"] > r["dof"]
          and r["big_loop_winding"] == r["sum_bits"])
    return {"seed": seed, "max_cap": r["max_perfect_capacity"], "dof": r["dof"],
            "big=sum": r["big_loop_winding"] == r["sum_bits"], "ok": bool(ok)}


def _ring_case(seed):
    p = dict(RING.DEFAULT)
    p.update({"seed": seed, "M": 192, "steps": 1500, "n_phi": 16})
    k = np.fft.fftfreq(p["M"], d=1.0 / p["M"])
    phis = list(np.linspace(0, p["phi_max"], p["n_phi"]))
    ok = all(abs(RING._ground(P, p, k)[2] - P) <= 0.5 + 1e-6 for P in phis)
    return {"seed": seed, "quantized_ok": bool(ok), "ok": bool(ok)}


def simulate(quick=False):
    seeds = [0, 1] if quick else [0, 1, 2, 3]
    mem = [_mem_case(s) for s in seeds]
    ring = [_ring_case(s) for s in ([0] if quick else [0, 1, 2])]
    return {
        "memory": mem, "ring": ring,
        "memory_all_ok": all(c["ok"] for c in mem),
        "ring_all_ok": all(c["ok"] for c in ring),
        "robust": bool(all(c["ok"] for c in mem + ring)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e028 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e028 robustness (received-memory facts vs seed / grid) ===")
    print("  memory all ok: %s" % r["memory_all_ok"])
    print("  ring all ok:   %s" % r["ring_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
