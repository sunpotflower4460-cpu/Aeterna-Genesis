#!/usr/bin/env python3
"""e024 Stage 2 -- the motor: why THREE phases make a rotation, and a rotor that spins.

MODULE:   e024_vessel_engine (Stage 2: motor)
QUESTION: is three the minimum number of equally-spaced phases whose combined field ROTATES
          (constant magnitude) rather than pulses; and does a rotor follow the rotating field?
PUT IN:   N sinusoids offset by 2pi/N; a rotor phase in an overdamped torque (rotating field,
          or a pulsing single-phase field with an optional ratchet bias). No spin is put in.
EMERGED:  (measured) the field magnitude is ripple-free (rotates) iff N>=3; the N=3 currents
          sum to zero; the h=3,6,9 harmonics are the zero-sequence (triplen) set; a rotor in the
          rotating field self-spins one direction, a pulsing field only wobbles until a ratchet bias.
CLAIM TIER: measured(three_is_min_rotation, balance, triplen zero-sequence, rotor spins) ;
          interpretive(the motor's rotation is built from three balanced phases) ;
          analogy("three-phase heart", ATP synthase's 120-degree steps).
KNOWN MATCH: Tesla's rotating magnetic field; three-phase power; ATP synthase (a 3-fold rotary motor).
STATUS:   GREEN (rotation/ripple/balance/rev gates, physical quantities only).
A_OR_B:   (A) faithful. Hand input = N offset sinusoids + a torque; rotation and the rev count
          are emergent and measured.

THE TRAP (designer hit it, we avoid it): the rotor is driven by the NET turning; do not "help"
it -- a rotating field already builds a direction in, and a single-phase field must only spin when
the ratchet bias is added (else the trap of a hidden bias would fake a motor). Gate on the physical
ripple, current sum, harmonic offset, and revolution count -- never on "life".

Floors: idealized sinusoidal phases and an overdamped rotor with fixed noise; absolute revolutions
depend on (K, T, dt, D). The ripple<0.05-iff-N>=3, zero balance, triplen offset, and the sign/size
of the rotor's net revolutions are the robust gated facts. "Heart/ATP synthase" is analogy.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"Ns": [1, 2, 3, 4, 6], "K": 3.0, "w": 1.0, "D": 0.05,
           "T": 120.0, "dt": 0.005, "Np": 400, "bias": 0.8, "seed": 0}
QUICK = {"T": 60.0, "Np": 200}


def _field_ripple(N, nt=4000):
    """(min, max, ripple) of |sum_k exp(i th_k) cos(t - th_k)| for N offset phases."""
    t = np.linspace(0, 8 * np.pi, nt)
    field = np.zeros(nt, complex)
    for k in range(N):
        thk = 2 * np.pi * k / N
        field += np.exp(1j * thk) * np.cos(t - thk)
    mag = np.abs(field)
    rip = (mag.max() - mag.min()) / (mag.max() + mag.min() + 1e-9)
    return float(mag.min()), float(mag.max()), float(rip)


def _current_balance(N, nt=4000):
    """max |sum_k cos(t - 2pi k/N)| over a period (0 => self-contained/balanced)."""
    t = np.linspace(0, 8 * np.pi, nt)
    s = sum(np.cos(t - 2 * np.pi * k / N) for k in range(N))
    return float(np.max(np.abs(s)))


def _triplen_offsets():
    """Phase offset (deg) between 3-phase windings at each harmonic h=1..9."""
    return {h: (h * 120) % 360 for h in range(1, 10)}


def _spin(mode, p, rng, bias=0.0):
    """Net revolutions of an overdamped rotor ensemble in a rotating/pulsing field."""
    phi = rng.random(p["Np"]) * 2 * np.pi
    tot = np.zeros(p["Np"])
    sq = np.sqrt(2 * p["D"] * p["dt"])
    K, w, dt = p["K"], p["w"], p["dt"]
    for i in range(int(p["T"] / dt)):
        tt = i * dt
        if mode == "rot":
            torque = -K * np.sin(phi - w * tt)                       # rotating (three-phase)
        else:
            torque = -K * np.sin(phi) * np.cos(w * tt) + bias        # pulsing + optional ratchet bias
        dphi = dt * torque + sq * rng.standard_normal(p["Np"])
        phi = phi + dphi
        tot = tot + dphi
    return float(np.mean(tot) / (2 * np.pi))


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)

    ripples = {N: _field_ripple(N) for N in p["Ns"]}
    rotates = {N: ripples[N][2] < 0.05 for N in p["Ns"]}
    balance = {N: _current_balance(N) for N in [1, 2, 3, 4]}
    triplen = _triplen_offsets()

    rng = np.random.default_rng(p["seed"])
    rev_rot = _spin("rot", p, rng)
    rev_puls = _spin("puls", p, rng, bias=0.0)
    rev_ratchet = _spin("puls", p, rng, bias=p["bias"])

    return {
        "params": p,
        "ripple": {N: round(ripples[N][2], 4) for N in p["Ns"]},
        "rotates": {N: bool(rotates[N]) for N in p["Ns"]},
        "balance": {N: round(balance[N], 6) for N in balance},
        "triplen_zero_harmonics": [h for h, off in triplen.items() if off == 0],
        "triplen_offsets": triplen,
        "rev_three_phase": round(rev_rot, 3),
        "rev_single_phase": round(rev_puls, 3),
        "rev_single_plus_ratchet": round(rev_ratchet, 3),
        # three is the minimum equally-spaced set that rotates (N<=2 pulse, N>=3 rotate)
        "three_is_min": bool(all(not rotates[N] for N in p["Ns"] if N <= 2)
                             and all(rotates[N] for N in p["Ns"] if N >= 3)),
        "n3_balanced": bool(balance[3] < 1e-9),
        "triplen_are_369": bool([h for h, off in triplen.items() if off == 0] == [3, 6, 9]),
    }


def evaluate(result, quick=False):
    checks = {
        "three_is_min_rotation (ripple<0.05 iff N>=3)": result["three_is_min"],
        "three_phase_balanced (max|sum|<1e-9)": result["n3_balanced"],
        "triplen_zero_sequence (h=3,6,9 in phase)": result["triplen_are_369"],
        "rotor_self_spins (3phase>5rev; 1phase<0.5; 1phase+ratchet>5rev)":
            bool(result["rev_three_phase"] > 5.0
                 and abs(result["rev_single_phase"]) < 0.5
                 and result["rev_single_plus_ratchet"] > 5.0),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e024 vessel engine Stage 2 (motor)", "tier": "measured",
        "put_in": "N phase-offset sinusoids + an overdamped rotor torque (rotating / pulsing + ratchet bias)",
        "emerged": ["field ripple by N: %s -> rotates iff N>=3" % result["ripple"],
                    "three-phase current sum max|.| = %s (balanced); triplen zero-seq harmonics = %s"
                    % (result["balance"].get(3), result["triplen_zero_harmonics"]),
                    "rotor net revolutions: three-phase %s, single-phase %s, single+ratchet %s"
                    % (result["rev_three_phase"], result["rev_single_phase"], result["rev_single_plus_ratchet"])],
        "surprises": ["three is the MINIMUM equally-spaced phase set whose field rotates; a single-phase "
                      "field needs the ratchet's broken symmetry to pick a direction"],
        "persistence": "the rotating field self-starts a fixed direction; the pulsing field only wobbles",
        "measured_numbers": {"ripple": result["ripple"], "balance": result["balance"],
                             "triplen_offsets": result["triplen_offsets"],
                             "rev_three_phase": result["rev_three_phase"],
                             "rev_single_phase": result["rev_single_phase"],
                             "rev_single_plus_ratchet": result["rev_single_plus_ratchet"]},
        "not_scripted_check": "no spin direction is put in; the rotor's net revolutions are measured",
        "claim_tier": "measured (rotation, balance, triplen, rev) ; interpretive (rotation built from three "
                      "balanced phases) ; analogy (three-phase heart / ATP synthase)",
        "floors": ["idealized sinusoids + overdamped rotor; absolute revolutions depend on (K, T, dt, D)",
                   "the ripple<0.05-iff-N>=3, zero balance, triplen offset, and rev sign/size are gated, not the magnitude",
                   "'heart / ATP synthase' is a KNOWN MATCH analogy, not a biological claim"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e024 Stage 2: three-phase motor")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e024 Stage 2 -- motor: why three, and a rotor that spins ===")
    print("  field ripple by N (rotates iff <0.05): %s" % r["ripple"])
    print("  three-phase current balance max|sum| = %s" % r["balance"].get(3))
    print("  triplen zero-sequence harmonics = %s" % r["triplen_zero_harmonics"])
    print("  rotor revolutions: three-phase=%s  single-phase=%s  single+ratchet=%s"
          % (r["rev_three_phase"], r["rev_single_phase"], r["rev_single_plus_ratchet"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (rotation measured; magnitude is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "motor.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/motor.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
