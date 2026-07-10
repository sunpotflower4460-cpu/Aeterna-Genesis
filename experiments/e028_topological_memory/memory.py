#!/usr/bin/env python3
"""e028 Stage 1 -- topological memory: a number read on a loop around a non-observed hole.

MODULE:   e028_topological_memory (Stage 1: static)
QUESTION: is a winding around a masked hole a NON-LOCAL, LOCALLY-UNERASABLE bit, and can a FIXED small
          reader recover far more such bits than its own boundary degrees of freedom (capacity > dof)?
PUT IN:   phase fields with M point holes (vortices), each a random +/-1 sign; a reading loop (CCW)
          reads the enclosed winding. NO "the bit is non-local / protected / capacity > dof" is put in.
EMERGED:  (measured) every loop encircling a hole reads the same bit, a loop enclosing no hole reads 0;
          the winding is EXACTLY invariant under smooth local phase noise while a bump baseline erodes;
          a fixed h=6 reader (boundary dof ~48) recovers up to M=121 bits at 100%.
CLAIM TIER: measured(non-locality, protection, capacity>dof) ; interpretive(the bit is RECEIVED in the
          hole, not STORED in the reader) ; analogy(memory -- KNOWN MATCH only, never a gate name).
KNOWN MATCH: Aharonov-Bohm phase; topological charge; toric-code-like protected degrees of freedom.
STATUS:   GREEN (gates on winding and recovered-bit fraction -- physical quantities only).
A_OR_B:   (A) faithful. Hand input = placed holes + their bits; non-locality, protection, and the
          capacity-vs-dof scaling are emergent and measured.

THE TRAP (designer hit it, we avoid it): the loop is traversed COUNTER-CLOCKWISE (core.holonomy); a CW
loop flips every sign so a clean field would read "0%". The reader must encircle exactly ONE hole. Gate
on winding / recovered-bit fraction / capacity -- never name a gate "memory" or "self".

Floors: static coarse-grained field on a fixed lattice; the capacity number depends on the lattice/hole
spacing (finite-size). "Memory / received / source-window" is analogy for a winding invariant; no memory
is created.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import winding_around  # noqa: E402

DEFAULT = {"N": 240, "read_h": 6, "ks": [2, 3, 4, 5, 7, 9, 11], "noises": [0.0, 0.5, 1.0, 2.0, 4.0],
           "noise_k": 7, "seed": 0}
QUICK = {"ks": [2, 3, 5, 7, 11], "noises": [0.0, 1.0, 4.0]}


def _grid(N):
    ii = np.arange(N)
    X, Y = np.meshgrid(ii, ii, indexing="ij")
    return X, Y


def _make_phase(holes, bits, X, Y):
    ph = np.zeros(X.shape)
    for (hx, hy), b in zip(holes, bits):
        ph += b * np.arctan2(Y - hy, X - hx)
    return ph


def _grid_holes(k, N):
    s = N // (k + 1)
    return [((a + 1) * s, (b + 1) * s) for a in range(k) for b in range(k)], s


def _read_bit(phase, hx, hy, R):
    """+/-1 bit = sign of the CCW winding on a loop of radius R around (hx, hy).

    A winding that rounds to 0 is a genuine READ MISS -- return 0 (which never equals a stored +/-1),
    so a miss is counted as a read FAILURE. (Earlier this fell back to +1, which could spuriously match
    a stored +1 and inflate the capacity/fidelity -- a first-layer correctness bug, LAW.md audit 7/8.)
    """
    w = winding_around(phase, hx, hy, R, n=4 * (2 * int(R) + 1))
    return int(round(w))


def _box_winding(phase, cx, cy, h):
    """Winding on a CCW SQUARE loop (half-size h) about (cx, cy).

    A square encloses the grid corners a circle of the same reach cannot, so it is used for the
    'loop around ALL holes' check. Traversal is CCW (right edge up -> top left -> left down ->
    bottom right) to match core.holonomy's CCW sign convention.
    """
    N = phase.shape[0]
    top = list(range(cy - h, cy + h + 1))
    C = ([(cx + h, j) for j in top]                                  # right edge, going up
         + [(i, cy + h) for i in range(cx + h - 1, cx - h - 1, -1)]  # top edge, going left
         + [(cx - h, j) for j in range(cy + h - 1, cy - h - 1, -1)]  # left edge, going down
         + [(i, cy - h) for i in range(cx - h + 1, cx + h)])         # bottom edge, going right
    ph = np.array([phase[i % N, j % N] for (i, j) in C])
    d = (np.diff(np.concatenate([ph, ph[:1]])) + np.pi) % (2 * np.pi) - np.pi
    return float(np.sum(d) / (2 * np.pi))


def _smooth_noise(scale, N, rng, sigma=0.03):
    f = rng.normal(0, 1, (N, N))
    K2 = np.fft.fftfreq(N)[:, None] ** 2 + np.fft.fftfreq(N)[None, :] ** 2
    f = np.fft.ifft2(np.fft.fft2(f) * np.exp(-K2 / (2 * sigma ** 2))).real
    return scale * f / (np.abs(f).max() + 1e-9)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N, h = p["N"], p["read_h"]
    X, Y = _grid(N)
    rng = np.random.default_rng(p["seed"])
    dof = 8 * h                                              # boundary dof of the fixed reader

    # (A/B) capacity vs a FIXED small reader
    capacity = []
    for k in p["ks"]:
        holes, s = _grid_holes(k, N)
        bits = rng.choice([-1, 1], size=len(holes))
        ph = _make_phase(holes, bits, X, Y)
        R = min(h, s // 2 - 2)
        read = np.array([_read_bit(ph, hx, hy, R) for (hx, hy) in holes])
        acc = float(np.mean(read == bits))
        capacity.append({"M": int(k * k), "spacing": int(s), "acc": round(acc, 3),
                         "exceeds_dof": bool(k * k > dof)})

    # (C) protection at scale vs a dynamical bump baseline
    k = p["noise_k"]
    holes, s = _grid_holes(k, N)
    bits = rng.choice([-1, 1], size=len(holes))
    ph0 = _make_phase(holes, bits, X, Y)

    def _dyn_amp(noise):
        A = np.zeros((N, N))
        for (hx, hy), b in zip(holes, bits):
            A += b * 0.6 * np.exp(-((X - hx) ** 2 + (Y - hy) ** 2) / (2 * 5.0 ** 2))
        return A + _smooth_noise(noise, N, rng)

    protection = []
    for ns in p["noises"]:
        ph = ph0 + _smooth_noise(ns * np.pi, N, rng)
        topo_ok = float(np.mean([_read_bit(ph, hx, hy, h) == b for (hx, hy), b in zip(holes, bits)]))
        A = _dyn_amp(ns * 0.6)
        dyn_ok = float(np.mean([np.sign(A[hx, hy]) == b for (hx, hy), b in zip(holes, bits)]))
        protection.append({"noise": ns, "topo_ok": round(topo_ok, 3), "dyn_ok": round(dyn_ok, 3)})

    # (D) non-locality: a loop between holes reads 0; a big SQUARE loop reads the sum of all bits
    mid = ((holes[0][0] + holes[1][0]) // 2, (holes[0][1] + holes[1][1]) // 2)
    between = _box_winding(ph0, mid[0], mid[1], 5)
    big = _box_winding(ph0, N // 2, N // 2, N // 2 - 6)

    max_cap = max(c for c in [cc["M"] for cc in capacity if cc["acc"] >= 0.999] or [0])
    return {
        "params": p, "dof": dof,
        "capacity": capacity, "protection": protection,
        "between_holes_winding": round(float(between), 2),
        "big_loop_winding": int(round(big)), "sum_bits": int(sum(bits)),
        "max_perfect_capacity": max_cap,
        # topo bits are perfectly recovered at every noise level; dynamical bits erode at high noise
        "topo_all_perfect": bool(all(pp["topo_ok"] >= 0.999 for pp in protection)),
        "dyn_erodes": bool(protection[-1]["dyn_ok"] < 0.999),
    }


def evaluate(result, quick=False):
    checks = {
        "nonlocal_winding (between-holes~0, big=sum bits)":
            bool(abs(result["between_holes_winding"]) < 0.5
                 and result["big_loop_winding"] == result["sum_bits"]),
        "protected_under_local_perturbation (topo bits 100% at all noise)":
            result["topo_all_perfect"],
        "capacity_exceeds_dof (a fixed reader recovers M>dof bits at 100%)":
            bool(result["max_perfect_capacity"] > result["dof"]),
        "dynamical_baseline_erodes (bump bits < 100% at max noise)":
            result["dyn_erodes"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e028 topological memory Stage 1 (static)", "tier": "measured",
        "put_in": "phase fields with M point holes (each a +/-1 winding) + CCW reading loops",
        "emerged": ["capacity (fixed h=%d reader, dof=%d): %s"
                    % (result["params"]["read_h"], result["dof"],
                       [(c["M"], c["acc"]) for c in result["capacity"]]),
                    "protection vs noise (topo_ok, dyn_ok): %s"
                    % [(p["noise"], p["topo_ok"], p["dyn_ok"]) for p in result["protection"]],
                    "non-locality: between-holes winding=%s, big loop=%s = sum bits=%s"
                    % (result["between_holes_winding"], result["big_loop_winding"], result["sum_bits"])],
        "surprises": ["a fixed ~%d-dof reader recovers up to %d bits at 100%%: capacity >> reader dof"
                      % (result["dof"], result["max_perfect_capacity"])],
        "persistence": "the winding bits are exactly invariant under smooth local perturbation",
        "measured_numbers": {"capacity": result["capacity"], "protection": result["protection"],
                             "between_holes_winding": result["between_holes_winding"],
                             "big_loop_winding": result["big_loop_winding"], "sum_bits": result["sum_bits"]},
        "not_scripted_check": "bits are read as windings on CCW loops; non-locality/protection/capacity are measured",
        "claim_tier": "measured (non-locality, protection, capacity>dof) ; interpretive (the bit is RECEIVED "
                      "in the hole, not stored in the reader) ; analogy (memory, KNOWN MATCH only)",
        "floors": ["static coarse-grained field on a fixed lattice; the capacity number is finite-size",
                   "the gated facts are the winding invariance and the capacity>dof scaling, not absolute counts",
                   "'memory / received / source-window' is analogy for a winding invariant; no memory is created"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e028 Stage 1: topological memory (static)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e028 Stage 1 -- topological memory: received in the hole, not stored ===")
    print("  capacity (fixed h=%d reader, dof=%d):" % (r["params"]["read_h"], r["dof"]))
    for c in r["capacity"]:
        print("     M=%3d spacing=%3d acc=%.0f%%  M>dof=%s" % (c["M"], c["spacing"], 100 * c["acc"], c["exceeds_dof"]))
    print("  protection vs local noise (topo / dyn bits ok):")
    for pp in r["protection"]:
        print("     noise=%.1f  topo=%.0f%%  dyn=%.0f%%" % (pp["noise"], 100 * pp["topo_ok"], 100 * pp["dyn_ok"]))
    print("  non-locality: between-holes winding=%s  big loop=%s = sum bits=%s"
          % (r["between_holes_winding"], r["big_loop_winding"], r["sum_bits"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (non-locality/protection/capacity measured; capacity is finite-size)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "memory.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/memory.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
