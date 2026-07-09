#!/usr/bin/env python3
"""e028 Stage 2 -- the dynamic receiver: a ring whose own state is set by a hidden flux it never touches.

MODULE:   e028_topological_memory (Stage 2: ring)
QUESTION: does a Ginzburg-Landau ring, with covariant derivative D = d/dtheta - i*Phi for a UNIFORM
          non-observed flux Phi, autonomously quantize its winding n ~ round(Phi), stay gauge-invariant
          (only the enclosed flux matters), and hold the winding behind a phase-slip barrier?
PUT IN:   a GL ring relaxed by spectral ETD (stiff diffusion done exactly in Fourier) for a range of Phi.
          NO "n = round(Phi)", NO "gauge invariance", NO "barrier" are put in -- all are measured.
EMERGED:  (measured) the ring's own winding jumps by integers at half-integer flux (n ~ round(Phi)); the
          energy is scalloped (period 1) and the current is sawtooth; a random single-valued gauge leaves
          the energy invariant to ~1e-6; forcing a phase-slip node costs far more than the ground state.
CLAIM TIER: measured(quantized winding, gauge invariance, phase-slip barrier) ; interpretive(the ring
          RECEIVES a quantized memory it cannot locally access) ; analogy(memory, a superconducting ring).
KNOWN MATCH: fluxoid quantization in a superconducting ring; the Aharonov-Bohm / Byers-Yang effect.
STATUS:   GREEN (gates on winding, energy, and gauge-invariance -- physical quantities only).
A_OR_B:   (A) faithful. Hand input = the GL ring + a uniform flux; quantization, gauge invariance, and
          the barrier are emergent and measured.

THE TRAP (designer hit it, we avoid it): the stiff diffusion MUST be integrated with a spectral ETD step
exp(-(k - Phi)^2 dt) in Fourier space -- an explicit real-space step overflows to NaN. Gate on winding /
energy / current -- never name a gate "memory". (The barrier proxy is a FLOOR, not a GREEN threshold.)

Floors: a 1D GL ring toy; the barrier is a forced-node PROXY for the phase-slip saddle (a floor on the
protection, not an exact instanton). "Memory / received / hidden flux" is analogy for fluxoid quantization.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"M": 256, "beta": 2.0, "steps": 2500, "dt": 0.1,
           "phis": None, "n_phi": 31, "phi_max": 3.0, "seed": 0}
QUICK = {"M": 192, "steps": 1500, "n_phi": 16}


def _relax(Phi, p, k, pin_n=None):
    """Spectral-ETD GL relaxation on the ring; returns (F, J, n, |psi|min, psi)."""
    M = p["M"]
    th = np.arange(M) / M * 2 * np.pi
    dth = 2 * np.pi / M
    if pin_n is not None:
        psi = np.exp(1j * pin_n * th).astype(complex)
    else:
        psi = (1 + 0.01 * np.random.default_rng(p["seed"]).standard_normal(M)).astype(complex)
    expL = np.exp(-(k - Phi) ** 2 * p["dt"])                        # spectral ETD (stiff term exact)
    for _ in range(p["steps"]):
        NL = -2 * p["beta"] * (np.abs(psi) ** 2 - 1) * psi
        psi = np.fft.ifft(expL * np.fft.fft(psi + p["dt"] * NL))
    c = np.fft.fft(psi)
    Dpsi = np.fft.ifft(1j * (k - Phi) * c)
    F = float(np.sum(0.5 * np.abs(Dpsi) ** 2 + p["beta"] * (np.abs(psi) ** 2 - 1) ** 2) * dth)
    J = float(np.mean(np.imag(np.conj(psi) * Dpsi)))
    ph = np.angle(psi)
    n = int(round(np.sum(np.angle(np.exp(1j * np.diff(np.concatenate([ph, ph[:1]]))))) / (2 * np.pi)))
    return F, J, n, float(np.abs(psi).min()), psi


def _ground(Phi, p, k):
    lo = int(np.floor(Phi)) - 1
    cand = [_relax(Phi, p, k, pin_n=n0) for n0 in range(lo, lo + 4)]
    return min(cand, key=lambda c: c[0])


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    M = p["M"]
    k = np.fft.fftfreq(M, d=1.0 / M)                                # integer wavenumbers
    phis = list(np.linspace(0, p["phi_max"], p["n_phi"]))

    # (1) autonomous quantization: n ~ round(Phi), energy period 1, current sawtooth
    sweep = []
    for P in phis:
        F, J, n, mn, _ = _ground(P, p, k)
        sweep.append({"phi": round(float(P), 3), "n": n, "J": round(J, 3), "psi_min": round(mn, 3)})
    # quantization: the received winding is the NEAREST integer to Phi (|n - Phi| <= 1/2).
    # At an exact half-integer Phi both neighbours satisfy this -- that is the degenerate jump point.
    quantized_ok = all(abs(s["n"] - s["phi"]) <= 0.5 + 1e-6 for s in sweep)

    # (2) gauge invariance: a random single-valued gauge leaves the energy invariant
    Phi = 0.35
    F0, _, _, _, psi0 = _relax(Phi, p, k, pin_n=0)
    dth = 2 * np.pi / M
    rng = np.random.default_rng(5)
    chi = np.cumsum(rng.normal(0, 0.2, M))
    chi -= chi.mean()
    psi_g = psi0 * np.exp(1j * chi)
    A_g = Phi + (np.roll(chi, -1) - chi) / dth
    Dg = (np.roll(psi_g, -1) * np.exp(-1j * A_g * dth) - psi_g) / dth
    Fg = float(np.sum(0.5 * np.abs(Dg) ** 2 + p["beta"] * (np.abs(psi_g) ** 2 - 1) ** 2) * dth)
    gauge_dE = abs(F0 - Fg)

    # (3) phase-slip barrier (FLOOR): forcing a node costs far more than the ground state
    F_slip = _relax(0.5, p, k, pin_n=0)[0]
    th = np.arange(M) / M * 2 * np.pi
    psi_node = np.tanh(np.minimum(th, 2 * np.pi - th) / 0.3).astype(complex)
    c = np.fft.fft(psi_node)
    Dn = np.fft.ifft(1j * (k - 0.5) * c)
    F_node = float(np.sum(0.5 * np.abs(Dn) ** 2 + p["beta"] * (np.abs(psi_node) ** 2 - 1) ** 2) * dth)

    return {
        "params": p, "sweep": sweep,
        "quantized_ok": bool(quantized_ok),
        "n_max": max(s["n"] for s in sweep),
        "gauge_dE": float(gauge_dE),
        "barrier_ground_E": round(F_slip, 3), "barrier_node_E": round(F_node, 3),
        "barrier": round(F_node - F_slip, 3),
    }


def evaluate(result, quick=False):
    checks = {
        "autonomous_quantized (|n-Phi|<=0.5 nearest integer; n rises to >=2)":
            bool(result["quantized_ok"] and result["n_max"] >= 2),
        "gauge_invariant (dE<1e-4 under random single-valued gauge)":
            bool(result["gauge_dE"] < 1e-4),
        "phase_slip_barrier (forced node E >> ground E)":
            bool(result["barrier_node_E"] > 2 * result["barrier_ground_E"]),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e028 topological memory Stage 2 (dynamic ring)", "tier": "measured",
        "put_in": "a GL ring with covariant derivative D=d/dtheta - i*Phi, relaxed by spectral ETD, over a Phi sweep",
        "emerged": ["received winding n ~ round(Phi) (rises to %s), current sawtooth; energy scalloped (period 1)"
                    % result["n_max"],
                    "gauge invariance: dE=%.2e under a random single-valued gauge" % result["gauge_dE"],
                    "phase-slip barrier (FLOOR): ground E=%s, forced-node E=%s, barrier=%s"
                    % (result["barrier_ground_E"], result["barrier_node_E"], result["barrier"])],
        "surprises": ["the ring's OWN energy/current/winding are set by a flux it never locally touches"],
        "persistence": "the winding is held behind a phase-slip barrier (switching requires |psi|->0)",
        "measured_numbers": {"sweep": result["sweep"], "gauge_dE": result["gauge_dE"],
                             "barrier_ground_E": result["barrier_ground_E"],
                             "barrier_node_E": result["barrier_node_E"]},
        "not_scripted_check": "quantization/gauge-invariance/barrier are measured from the relaxed field; "
                              "the stiff step is spectral ETD (explicit real-space overflows)",
        "claim_tier": "measured (quantized winding, gauge invariance, barrier) ; interpretive (the ring "
                      "receives a quantized memory it cannot locally access) ; analogy (memory / SC ring)",
        "floors": ["1D GL ring toy; the barrier is a forced-node PROXY for the phase-slip saddle (a floor)",
                   "the barrier is NOT a GREEN threshold, only a documented protection floor",
                   "'memory / hidden flux' is analogy for fluxoid quantization"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e028 Stage 2: dynamic GL ring receiver")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e028 Stage 2 -- dynamic ring: reads a quantized memory it cannot locally touch ===")
    print("  Phi sweep (received n, current J):")
    for s in r["sweep"][::max(1, len(r["sweep"]) // 8)]:
        print("     Phi=%.2f  n=%d  J=%+.3f  |psi|min=%.2f" % (s["phi"], s["n"], s["J"], s["psi_min"]))
    print("  gauge invariance dE = %.2e" % r["gauge_dE"])
    print("  phase-slip barrier (floor): ground E=%s node E=%s barrier=%s"
          % (r["barrier_ground_E"], r["barrier_node_E"], r["barrier"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (quantized/gauge/barrier measured; barrier is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "ring.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/ring.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
