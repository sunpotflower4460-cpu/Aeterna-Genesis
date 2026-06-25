#!/usr/bin/env python3
"""e010 robustness (LAW.md audit 6) + the z-exponent test (Layer 2).

Two sweeps:

(A) length_robustness -- the KZ mechanism (spacing/xi constant; 2 sigma = b)
    must survive changing the box L and the damping gamma. We report the
    spacing/xi CV and the internal consistency |2 sigma - b|/b for each.

(B) substrate_z_test -- KZ predicts a SMALLER dynamical exponent z gives a
    LARGER defect exponent b: b = (D-d) nu / (1 + nu z). We measure b on two
    substrates with a MATCHED, lightly-damped, full quench (mu/v2: -1 -> 1):
      * GPE                       (relaxational)        -> z = 2
      * relativistic scalar/NLKG  (second-order in time) -> z = 1
    and check the ORDERING b(z=1) > b(z=2).

HONESTY (floors, stated up front): the ABSOLUTE b is protocol dependent and
sits below the mean-field value (coarsening, finite L, count threshold). The
ordering is the measured KZ-consistent statement -- and it is delicate: HEAVY
damping drives the relativistic field into a relaxational (z=2-like) regime and
ERASES the contrast, while too-light damping lets it ring (sound -> extra
defects, non-monotonic). The clean ordering holds when each substrate is in its
natural-z, lightly-damped, monotonic regime. We report that, not a universal b.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, measure, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402


def _count(psi, frac=0.1):
    return vortex.count_defects(psi, frac=frac)[0]


def gpe_quench(L, tauQ, hold, seed, gamma, mu_i=-1.0, mu_f=1.0, dt=0.05):
    """Relaxational GPE quench (z=2)."""
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = 0.05 * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    for s in range(tauQ + hold):
        mu = mu_i + (mu_f - mu_i) * min(1.0, s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, 1.0, mu, dt, gamma)
    return psi


def nlkg_quench(L, tauQ, hold, seed, eta, v2_i=-1.0, v2_f=1.0, dt=0.05):
    """Relativistic complex scalar (nonlinear Klein-Gordon) quench (z=1).

    psi'' - lap psi + (|psi|^2 - v2) psi = -eta psi'  (light damping eta keeps
    the second-order/relativistic, z=1 character while removing enough energy to
    condense; too-large eta makes it relaxational like the GPE).
    """
    k2 = k_squared(L)
    rng = np.random.default_rng(seed)
    psi = 0.05 * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    pidot = np.zeros((L, L), complex)
    for s in range(tauQ + hold):
        v2 = v2_i + (v2_f - v2_i) * min(1.0, s / tauQ)
        lap = np.fft.ifft2(-k2 * np.fft.fft2(psi))
        acc = lap - (np.abs(psi) ** 2 - v2) * psi - eta * pidot
        pidot = pidot + dt * acc
        psi = psi + dt * pidot
    return psi


def _b_and_rho(fn, L, taus, hold, par, seeds=(1, 2, 3)):
    Ns, rhos = [], []
    for tq in taus:
        ns, rr = [], []
        for sd in seeds:
            p = fn(L, tq, hold, sd, par)
            ns.append(max(_count(p), 1))
            rr.append(float(np.median(np.abs(p) ** 2)))
        Ns.append(float(np.mean(ns)))
        rhos.append(float(np.mean(rr)))
    b = float(-np.polyfit(np.log(taus), np.log(Ns), 1)[0])
    mono = all(Ns[i] >= Ns[i + 1] for i in range(len(Ns) - 1))
    return b, Ns, mono, min(rhos)


def substrate_z_test(quick=False):
    L = 128 if quick else 192
    taus = [100, 200, 400] if quick else [100, 200, 400, 800]
    hold = 400
    bg, Ng, mg, rg = _b_and_rho(gpe_quench, L, taus, hold, 0.3)
    bn, Nn, mn, rn = _b_and_rho(nlkg_quench, L, taus, hold, 0.3)
    nu = 0.5  # mean-field
    mf = {"z=1": round(1.0 / (1 + nu * 1), 3), "z=2": round(1.0 / (1 + nu * 2), 3)}
    return {"GPE_z2": {"b": round(bg, 3), "N": [round(x) for x in Ng],
                       "monotonic": mg, "rho_min": round(rg, 2), "z": 2},
            "NLKG_z1": {"b": round(bn, 3), "N": [round(x) for x in Nn],
                        "monotonic": mn, "rho_min": round(rn, 2), "z": 1},
            "ordering_b_z1_gt_z2": bool(bn > bg),
            "kz_meanfield_b": mf,
            "meanfield_orders_same_way": bool(mf["z=1"] > mf["z=2"])}


def length_robustness(quick=False):
    taus = [100, 200, 400] if quick else [50, 100, 200, 400, 800]
    cases = ([(128, 1.0)] if quick
             else [(128, 1.0), (192, 1.0), (256, 1.0), (192, 0.7)])
    rows = []
    for L, gamma in cases:
        ratios, Ns, xis = [], [], []
        for tq in taus:
            ns, xs = [], []
            for sd in (1, 2, 3):
                psi = gpe_quench(L, tq, 150, sd, gamma, mu_i=-0.2)
                ns.append(max(_count(psi), 1))
                xs.append(measure.coherence_length(psi))
            N = float(np.mean(ns))
            xi = float(np.mean(xs))
            Ns.append(N)
            xis.append(xi)
            ratios.append((L / np.sqrt(N)) / xi)
        ratios = np.asarray(ratios)
        sigma = float(np.polyfit(np.log(taus), np.log(xis), 1)[0])
        b = float(-np.polyfit(np.log(taus), np.log(Ns), 1)[0])
        rows.append({"L": L, "gamma": gamma,
                     "spacing_over_xi": round(float(ratios.mean()), 3),
                     "cv": round(float(ratios.std() / ratios.mean()), 3),
                     "b": round(b, 3), "two_sigma": round(2 * sigma, 3),
                     "consistency_rel": round(abs(2 * sigma - b) / max(b, 1e-9), 3),
                     "pass": bool(ratios.std() / ratios.mean() < 0.15
                                  and abs(2 * sigma - b) / max(b, 1e-9) < 0.25)})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="e010 robustness + z-test")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    z = substrate_z_test(quick=args.quick)
    rows = length_robustness(quick=args.quick)
    print("=== (A) length/gamma robustness: spacing/xi const & 2sigma=b ===")
    for r in rows:
        print("  L=%3d gamma=%.1f: spacing/xi=%.3f (CV=%.3f)  b=%.3f 2sigma=%.3f cons=%.3f  %s"
              % (r["L"], r["gamma"], r["spacing_over_xi"], r["cv"], r["b"],
                 r["two_sigma"], r["consistency_rel"], "PASS" if r["pass"] else "FAIL"))
    print("=== (B) z-test: smaller z -> larger b ===")
    print("  GPE  (z=2): b=%.3f  N=%s mono=%s rho>=%.2f"
          % (z["GPE_z2"]["b"], z["GPE_z2"]["N"], z["GPE_z2"]["monotonic"], z["GPE_z2"]["rho_min"]))
    print("  NLKG (z=1): b=%.3f  N=%s mono=%s rho>=%.2f"
          % (z["NLKG_z1"]["b"], z["NLKG_z1"]["N"], z["NLKG_z1"]["monotonic"], z["NLKG_z1"]["rho_min"]))
    print("  ordering b(z=1) > b(z=2): %s   (KZ mean-field: z=1->%.3f > z=2->%.3f)"
          % (z["ordering_b_z1_gt_z2"], z["kz_meanfield_b"]["z=1"], z["kz_meanfield_b"]["z=2"]))
    n_pass = sum(r["pass"] for r in rows)
    # The z-ordering claim is only valid when BOTH substrates are in the clean
    # KZ regime: monotonic N(tau_Q) AND condensed (rho_min above threshold). A
    # bare bn>bg in a ringing/under-condensed run does not count (Codex P2).
    z_clean = bool(z["GPE_z2"]["monotonic"] and z["NLKG_z1"]["monotonic"]
                   and z["GPE_z2"]["rho_min"] >= 0.6 and z["NLKG_z1"]["rho_min"] >= 0.6)
    z_ok = bool(z["ordering_b_z1_gt_z2"] and z_clean)
    ok = (n_pass == len(rows)) and z_ok
    print("ROBUSTNESS: %s (%d/%d length cases PASS; z-ordering=%s, clean-regime=%s)"
          % ("GREEN" if ok else "MIXED", n_pass, len(rows),
             z["ordering_b_z1_gt_z2"], z_clean))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump({"length_robustness": rows, "z_test": z,
                       "z_ordering_clean": z_ok}, f, indent=2)
        print("wrote robustness.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
