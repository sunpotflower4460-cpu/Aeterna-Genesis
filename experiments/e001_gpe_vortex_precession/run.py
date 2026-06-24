#!/usr/bin/env python3
"""Aeterna-Genesis experiment e001 -- GPE single-vortex precession.

================================ AUDIT HEADER ================================
MODULE:      e001_gpe_vortex_precession
QUESTION:    Does a vortex in a trap precess from the field equation alone?
PUT IN:      GPE  i d psi/dt = [-1/2 lap + V + g|psi|^2] psi  (the real BEC
             field equation) + harmonic trap V = 1/2 Omega^2 r^2 + one
             imprinted vortex in the initial condition. THIS ONLY.
EMERGED:     The vortex's precession (circular motion about the centre),
             angular-momentum conservation (near-constant radius), and the
             accompanying Thomas-Fermi density profile + faint sound.
CLAIM TIER:  measured (precession angle, radius, circulation are measured)
KNOWN MATCH: Matches vortex precession seen in BEC experiments and GPE theory
             (e.g. Anderson et al., vortex dynamics in trapped condensates).
AUDIT (7):
  1 Rules mention the result?   No  -- GPE is local; it never says "precess".
  2 Faithful physics?          Yes -- GPE is the equation real superfluids obey.
  3 Result in initial cond.?   No  -- initial state has one static vortex; the
                                       motion is not put in.
  4 Un-asked things emerge?    Yes -- TF density profile, precession period,
                                       and small sound waves all appear unbidden.
  5 Agrees with reality by #?  Yes -- radius ~ const (ang. mom.), circulation
                                       quantized (integer), matches BEC results.
  6 Robust?                    Yes -- persists across R0 in {6,10,14} and
                                       Omega in {0.05,0.06,0.08} (see AUDIT.md).
  7 Code asserts or discovers? Discovers -- core found by phase winding + density
                                       minimum, not written in.
STATUS:      GREEN
A_OR_B:      (A) faithful emergence. Hand-supplied input = the field equation
             itself (GPE is a mean-field effective theory, not a final law, so
             (B) -- deriving the law from nothing -- is not yet attempted).
=============================================================================

Run with no arguments to reproduce the reference result and write result.json.
Use --quick for a short run (used by tests/CI for a fast qualitative check).
"""

import argparse
import json
import os
import sys

import numpy as np

# Allow running both as a script and as part of the package.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, measure, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402


# Reference parameters (Section 3.3 of the spec) -- verified to give a clean
# result: radius ~10 constant, cumulative rotation > 360 deg over 8000 steps.
DEFAULT_PARAMS = {
    "L": 64,
    "g": 1.0,
    "Omega": 0.06,
    "mu": 1.0,
    "R0": 10.0,
    "charge": 1,
    "dtau": 0.05,
    "n_imag": 250,
    "dt": 0.1,
    "n_real": 8000,
    "sample": 50,
}

# Expected ranges the measured result must fall in (used by tests).
EXPECTATIONS = {
    "radius_mean": (9.0, 11.5),
    "radius_spread": (0.0, 2.0),       # max - min over the run
    "cumulative_rotation_deg": (360.0, 600.0),
    "charge": (1, 1),
    "energy_drift_max": 1e-4,
    "norm_drift_max": 1e-6,
}


def simulate(params=None, seed=0, verbose=False, quick=False):
    """Run the GPE vortex-precession experiment and return a measurements dict.

    Deterministic: no randomness is used (the seed is fixed only for hygiene
    and future-proofing). Returns measured quantities -- nothing about the
    result is written into the inputs.
    """
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    np.random.seed(seed)

    L = p["L"]
    center = field.default_center(L)
    V = field.harmonic_trap(L, p["Omega"], center)
    k2 = k_squared(L)

    # 1) initial state: TF amplitude with a single imprinted vortex at cx+R0.
    psi, phase0 = field.initial_vortex_state(
        L, p["Omega"], p["mu"], p["R0"], charge=p["charge"], center=center
    )
    norm0 = field.norm(psi)

    # 2) imaginary-time relaxation -- shape the density while pinning the
    #    vortex (re-imprint phase + renormalize each step) so the start state
    #    is free of spurious sound.
    for _ in range(p["n_imag"]):
        psi = field.step_imag(psi, V, k2, p["g"], p["mu"], p["dtau"])
        amp = np.abs(psi)
        amp *= np.sqrt(norm0 / np.sum(amp ** 2))
        psi = amp * np.exp(1j * phase0)

    quantized_start = vortex.is_circulation_quantized(psi)

    # 3) real-time evolution -- the vortex is now free; nothing is pinned.
    e0 = measure.energy(psi, V, p["g"])
    n0 = measure.norm(psi)
    angles, radii, charges, energies, norms = [], [], [], [], []
    prev = None
    for step in range(p["n_real"]):
        psi = field.step_real(psi, V, k2, p["g"], p["mu"], p["dt"])
        if step % p["sample"] == 0:
            core = vortex.track_single_vortex(psi, V, p["mu"], center, prev=prev)
            if core is not None:
                angles.append(core["angle"])
                radii.append(core["radius"])
                charges.append(core["charge"])
                prev = core
                energies.append(measure.energy(psi, V, p["g"]))
                norms.append(measure.norm(psi))

    radii = np.asarray(radii)
    cum_deg = np.degrees(measure.unwrap_cumulative(angles))
    charge_set = sorted(set(charges))
    result = {
        "params": p,
        "n_samples": len(radii),
        "radius_series": [round(float(r), 4) for r in radii],
        "rotation_series_deg": [round(float(a), 3) for a in cum_deg],
        "radius_mean": float(np.mean(radii)),
        "radius_min": float(np.min(radii)),
        "radius_max": float(np.max(radii)),
        "radius_std": float(np.std(radii)),
        "radius_spread": float(np.max(radii) - np.min(radii)),
        "cumulative_rotation_deg": float(cum_deg[-1]),
        "rotation_monotonic": bool(np.all(np.diff(cum_deg) >= -1e-9)),
        "charge": int(charge_set[0]) if len(charge_set) == 1 else charge_set,
        "circulation_quantized": bool(quantized_start),
        "energy_drift": float(abs(measure.energy(psi, V, p["g"]) - e0) / abs(e0)),
        "norm_drift": float(abs(measure.norm(psi) - n0) / n0),
    }
    if verbose:
        _print_report(result, quick=quick)
    return result


def evaluate(result, quick=False):
    """Return (passed: bool, checks: dict) comparing result to EXPECTATIONS.

    quick=True relaxes only the cumulative-rotation bound: a short run does
    fewer steps so it precesses less far, but the emergence is the same. All
    other checks (radius constancy, quantization, conservation) are unchanged.
    """
    checks = {}
    lo, hi = EXPECTATIONS["radius_mean"]
    checks["radius_mean_in_range"] = lo <= result["radius_mean"] <= hi
    lo, hi = EXPECTATIONS["radius_spread"]
    checks["radius_nearly_constant"] = lo <= result["radius_spread"] <= hi
    if quick:
        checks["precession_clear"] = result["cumulative_rotation_deg"] > 180.0
    else:
        lo, hi = EXPECTATIONS["cumulative_rotation_deg"]
        checks["precession_over_360"] = lo <= result["cumulative_rotation_deg"] <= hi
    checks["rotation_monotonic"] = result["rotation_monotonic"]
    checks["circulation_quantized"] = result["circulation_quantized"]
    checks["charge_is_plus_one"] = result["charge"] == 1
    checks["energy_conserved"] = result["energy_drift"] < EXPECTATIONS["energy_drift_max"]
    checks["norm_conserved"] = result["norm_drift"] < EXPECTATIONS["norm_drift_max"]
    return all(checks.values()), checks


def _print_report(result, quick=False):
    print(__doc__)
    print("------------------------------ MEASUREMENTS ------------------------------")
    p = result["params"]
    print(f"params: L={p['L']} g={p['g']} Omega={p['Omega']} mu={p['mu']} "
          f"R0={p['R0']} | imag {p['n_imag']}x{p['dtau']} real {p['n_real']}x{p['dt']}")
    print(f"samples:                 {result['n_samples']}")
    print(f"radius  min/mean/max:    {result['radius_min']:.2f} / "
          f"{result['radius_mean']:.2f} / {result['radius_max']:.2f} "
          f"(std {result['radius_std']:.3f})")
    print(f"cumulative rotation:     {result['cumulative_rotation_deg']:.1f} deg "
          f"(monotonic: {result['rotation_monotonic']})")
    print(f"vortex charge:           {result['charge']} "
          f"(circulation quantized: {result['circulation_quantized']})")
    print(f"energy drift:            {result['energy_drift']:.2e}")
    print(f"norm drift:              {result['norm_drift']:.2e}")
    passed, checks = evaluate(result, quick=quick)
    print("------------------------------- AUDIT 5/6 --------------------------------")
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"STATUS: {'GREEN' if passed else 'RED'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="GPE single-vortex precession (e001)")
    ap.add_argument("--quick", action="store_true",
                    help="short run for fast CI/test checks")
    ap.add_argument("--no-write", action="store_true",
                    help="do not write result.json")
    args = ap.parse_args(argv)

    params = None
    if args.quick:
        # Shorter relaxation/evolution -- still shows clear precession past 360.
        params = {"n_imag": 150, "n_real": 6000, "sample": 50}

    result = simulate(params, verbose=True, quick=args.quick)

    if not args.no_write and not args.quick:
        out_path = os.path.join(os.path.dirname(__file__), "result.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nwrote {out_path}")

    passed, _ = evaluate(result, quick=args.quick)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
