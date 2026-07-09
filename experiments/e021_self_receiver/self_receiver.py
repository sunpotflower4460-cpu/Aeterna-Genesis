#!/usr/bin/env python3
"""e021 Stage 1 -- self-reception: a ring reads its OWN core's winding, with no external field.

MODULE:   e021_self_receiver (Stage 1: self_receiver)
QUESTION: in ONE self-consistent GL field (a vortex core = the non-observed source-window), does a ring
          around it autonomously read the core's OWN winding -- no external flux -- and is that reading
          invariant to the core's position and to the reader radius (as long as it is outside the core)?
PUT IN:   a 2D GL field relaxed in imaginary time with the boundary winding clamped to exp(i w theta);
          a reading ring. NO "the ring reads its own core" and NO "position/radius invariance" are put in.
EMERGED:  (measured) the ring winding equals the core winding for w=-2..2 and the persistent-current sign
          follows it; the reading is invariant when the core is jittered off-centre; it is quantized
          across reader radii outside the core's healing halo.
CLAIM TIER: measured(ring winding = core winding, position/radius invariance) ; interpretive(self-identity
          = a loop reading its own source-window, with no external field) ; analogy(self, reception --
          KNOWN MATCH only, never a gate name).
KNOWN MATCH: fluxoid/winding quantization; a persistent current reading an enclosed topological charge.
STATUS:   GREEN (gates on ring winding and current sign -- physical quantities only).
A_OR_B:   (A) faithful. Hand input = the GL field + boundary winding; the ring's autonomous reading and
          its invariances are emergent and measured.

THE TRAP (designer hit it, we avoid it): the winding is read on a CCW ring (core.holonomy); a reader
INSIDE the core's healing halo (|psi| -> 0) loses the reading, so the reader must sit OUTSIDE the
source-window (a structural condition / floor). Gate on winding / current -- never name a gate "self".

Floors: a 2D GL toy; the boundary winding is clamped (the source's topology is a boundary condition).
The critical reader radius is finite-size. "Self / reception / source-window" is analogy for a loop
reading an enclosed winding; no self is created.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import ring_winding, circulation  # noqa: E402

DEFAULT = {"N": 128, "steps": 1500, "dt": 0.05, "beta": 1.0, "read_R": 40,
           "ws": [-2, -1, 0, 1, 2], "jitters": [[0, 0], [5, 0], [0, -8], [10, 6]],
           "radii": [8, 14, 22, 32, 45, 55], "seed": 0}
QUICK = {"steps": 900, "ws": [-2, -1, 0, 1, 2], "jitters": [[0, 0], [10, 6]],
         "radii": [14, 32, 55]}


def _grid(N):
    x = np.arange(N) - N / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    r = np.hypot(X, Y)
    kx = 2 * np.pi * np.fft.fftfreq(N)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    return X, Y, r, KX ** 2 + KY ** 2


def _relax_vortex(w, p, X, Y, r, K2, jitter=(0, 0)):
    """Imaginary-time GL relaxation with the boundary winding clamped to exp(i w theta)."""
    N = p["N"]
    x0, y0 = jitter
    amp = np.tanh(np.hypot(X - x0, Y - y0) / 2.0)
    psi = (amp * np.exp(1j * w * np.arctan2(Y - y0, X - x0))).astype(complex)
    th = np.arctan2(Y, X)
    bnd = (r > N / 2 - 3)
    bphase = np.exp(1j * w * th)
    expK = np.exp(-0.5 * K2 * p["dt"])
    for _ in range(p["steps"]):
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        psi = psi * np.exp(-p["dt"] * 2 * p["beta"] * (np.abs(psi) ** 2 - 1))
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        psi[bnd] = bphase[bnd]                                   # source-window winding = boundary condition
    return psi


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N = p["N"]
    X, Y, r, K2 = _grid(N)
    c = N / 2
    R = p["read_R"]

    # (1) the ring reads the core's OWN winding (no external field)
    reads = []
    for w in p["ws"]:
        psi = _relax_vortex(w, p, X, Y, r, K2)
        rw = ring_winding(psi, c, c, R, n=400)
        jc = circulation(psi, c, c, R, dR=6.0)
        reads.append({"w": w, "ring_winding": round(float(rw), 2), "current": round(float(jc), 4)})
    reads_core = all(abs(rd["ring_winding"] - rd["w"]) < 0.1 for rd in reads)
    current_follows = all((rd["current"] > 0) == (rd["w"] > 0) for rd in reads if rd["w"] != 0)

    # (2) position invariance: jitter the core; the reading is unchanged (uses w=1)
    jitters = []
    for jit in p["jitters"]:
        psi = _relax_vortex(1, p, X, Y, r, K2, jitter=jit)
        jitters.append({"jitter": jit, "ring_winding": round(float(ring_winding(psi, c, c, R, n=400)), 2)})
    position_invariant = all(abs(j["ring_winding"] - 1.0) < 0.1 for j in jitters)

    # (3) radius invariance outside the core: winding quantized across reader radii
    psi = _relax_vortex(1, p, X, Y, r, K2)
    radii = []
    for Rr in p["radii"]:
        amp_on_ring = float(np.mean(np.abs(psi)[np.abs(r - Rr) < 3]))
        radii.append({"R": Rr, "ring_winding": round(float(ring_winding(psi, c, c, Rr, n=400)), 2),
                      "amp_on_ring": round(amp_on_ring, 3)})
    radius_quantized = all(abs(rr["ring_winding"] - 1.0) < 0.1 for rr in radii if rr["amp_on_ring"] > 0.6)

    return {
        "params": p, "reads": reads, "jitters": jitters, "radii": radii,
        "reads_own_core": bool(reads_core), "current_follows_sign": bool(current_follows),
        "position_invariant": bool(position_invariant), "radius_quantized": bool(radius_quantized),
    }


def evaluate(result, quick=False):
    checks = {
        "ring_reads_core_winding (ring w == core w for w=-2..2)":
            bool(result["reads_own_core"] and result["current_follows_sign"]),
        "reading_invariant_to_core_position (jitter -> same winding)":
            result["position_invariant"],
        "reading_quantized_across_radii (winding=1 for readers outside the core)":
            result["radius_quantized"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e021 self receiver Stage 1 (self_receiver)", "tier": "measured",
        "put_in": "a self-consistent GL field with a clamped boundary winding + a reading ring (no external flux)",
        "emerged": ["ring reads core winding: %s"
                    % [(rd["w"], rd["ring_winding"], rd["current"]) for rd in result["reads"]],
                    "position invariance (jitter -> winding): %s"
                    % [(j["jitter"], j["ring_winding"]) for j in result["jitters"]],
                    "radius invariance: %s" % [(rr["R"], rr["ring_winding"]) for rr in result["radii"]]],
        "surprises": ["with NO external field the ring autonomously reads its own core's winding and current sign"],
        "persistence": "the reading is invariant to core position and reader radius (outside the core halo)",
        "measured_numbers": {"reads": result["reads"], "jitters": result["jitters"], "radii": result["radii"]},
        "not_scripted_check": "the ring winding/current are read on a CCW loop; the autonomous reading and "
                              "invariances are measured, not imposed",
        "claim_tier": "measured (ring winding = core winding, invariances) ; interpretive (self-identity = a "
                      "loop reading its own source-window) ; analogy (self / reception, KNOWN MATCH only)",
        "floors": ["2D GL toy; boundary winding is clamped (source topology is a boundary condition)",
                   "the reader must sit OUTSIDE the core halo; the critical radius is finite-size",
                   "'self / reception / source-window' is analogy for a loop reading a winding; no self is created"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e021 Stage 1: self-reception")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e021 Stage 1 -- self-reception: a ring reads its own core, no external field ===")
    print("  core w -> ring winding / current:")
    for rd in r["reads"]:
        print("     w=%+d  ring=%+.2f  current=%+.4f" % (rd["w"], rd["ring_winding"], rd["current"]))
    print("  position invariance (jitter -> winding): %s"
          % [(j["jitter"], j["ring_winding"]) for j in r["jitters"]])
    print("  radius invariance: %s" % [(rr["R"], rr["ring_winding"]) for rr in r["radii"]])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (autonomous self-reading measured; critical radius is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "self_receiver.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/self_receiver.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
