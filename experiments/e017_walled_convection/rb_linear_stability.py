#!/usr/bin/env python3
"""e017 Stage 1 -- walled Rayleigh-Benard: the TEXTBOOK critical Rayleigh number.

e013's self-organized convection used a PERIODIC box, whose linear onset Ra_c ~ 20
is the box's own eigenvalue -- an artifact of periodicity, not the physical wall
threshold. Here we solve the real linear-stability problem with WALLS and recover
the classical critical Rayleigh numbers to <0.4%.

Marginal (growth rate = 0) Boussinesq on z in [0,1], horizontal wavenumber a:
    (D^2 - a^2)^2 W = a^2 Ra Theta      (momentum)
    (D^2 - a^2) Theta = - W             (heat)
a generalized eigenvalue problem A x = Ra B x with x = (W, Theta). We build D1, D2
by finite differences and MINIMIZE Ra over a to get (Ra_c, a_c) for two wall types:
    * no-slip  (rigid): W = 0, DW = 0, Theta = 0  ->  Ra_c = 1707.76 @ a_c = 3.117
    * free-slip (stress-free): W = 0, D^2 W = 0, Theta = 0  ->  Ra_c = 657.5 @ 2.221

THE TRAP (designer hit it, we avoid it): the tangential wall condition must be
imposed with a ONE-SIDED derivative stencil. free-slip needs D^2 W = 0 as a real
one-sided second-derivative row; if that row is left undefined (all zeros) the
eigenproblem returns garbage (~2.6e11). no-slip needs DW = 0 (one-sided D1).
Theta = 0 on both walls. We verify the recovered numbers against the textbook.

Put in: the linearized Boussinesq operator + wall BCs. NOT put in: the value of
Ra_c or a_c -- they are eigenvalues we read out. This is a linear-onset ruler; the
nonlinear saturated flow + interior feeding is Stage 2 (rb_dns.py). Fixed grid.

MODULE:   e017_walled_convection (Stage 1: linear onset)
QUESTION: Does the walled linear-stability problem recover the textbook Ra_c (no-slip 1708, free-slip 657.5)?
PUT IN:   linearized marginal Boussinesq (D^2-a^2)^3-type operator + wall BCs (no-slip / free-slip). Ra_c not put in.
EMERGED:  (measured) Ra_c=1713.9@a_c=3.12 (no-slip), 657.3@2.22 (free-slip): textbook to <0.4%. Periodic Ra_c~20 is an artifact.
CLAIM TIER: measured(Ra_c, a_c for both BCs vs textbook) ; interpretive(periodic-box onset is an artifact).
KNOWN MATCH: Rayleigh 1916 / Jeffreys / Chandrasekhar (Ra_c=1707.76, 657.5).
STATUS:   GREEN (both critical numbers recovered to <0.4%).
A_OR_B:   (A) faithful. Hand input = linearized equations + BCs; the critical numbers are read out.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.linalg import eig
from scipy.optimize import minimize_scalar

TEXTBOOK = {"noslip": {"Ra": 1707.76, "a": 3.117}, "freeslip": {"Ra": 657.51, "a": 2.221}}


def _operators(N):
    """z in [0,1] with N points; D1, D2 finite-difference matrices with one-sided
    boundary rows (used to build the wall BC rows -- the trap the designer hit)."""
    z = np.linspace(0.0, 1.0, N)
    h = z[1] - z[0]
    D1 = np.zeros((N, N))
    D2 = np.zeros((N, N))
    for i in range(1, N - 1):
        D1[i, i - 1] = -1 / (2 * h)
        D1[i, i + 1] = 1 / (2 * h)
        D2[i, i - 1] = 1 / h ** 2
        D2[i, i] = -2 / h ** 2
        D2[i, i + 1] = 1 / h ** 2
    # one-sided (second-order) stencils at the two walls
    D1[0, 0:3] = [-3 / (2 * h), 4 / (2 * h), -1 / (2 * h)]
    D1[-1, -3:] = [1 / (2 * h), -4 / (2 * h), 3 / (2 * h)]
    D2[0, 0:4] = [2 / h ** 2, -5 / h ** 2, 4 / h ** 2, -1 / h ** 2]
    D2[-1, -4:] = [-1 / h ** 2, 4 / h ** 2, -5 / h ** 2, 2 / h ** 2]
    return z, h, D1, D2


def Ra_of_a(a, N, bc):
    """Smallest positive marginal Ra at horizontal wavenumber a for wall type bc."""
    z, h, D1, D2 = _operators(N)
    I = np.eye(N)
    Lap = D2 - a * a * I
    Lap2 = Lap @ Lap
    A = np.zeros((2 * N, 2 * N))
    B = np.zeros((2 * N, 2 * N))
    # momentum: Lap2 W = a^2 Ra Theta ;  heat: Lap Theta + W = 0
    A[:N, :N] = Lap2
    B[:N, N:] = a * a * I
    A[N:, N:] = Lap
    A[N:, :N] = I
    # --- wall BCs replace rows: W=0 (walls), tangential (rows 1,N-2), Theta=0 (walls) ---
    for idx in (0, N - 1):                       # W = 0
        A[idx, :] = 0.0; B[idx, :] = 0.0; A[idx, idx] = 1.0
    if bc == "noslip":                           # DW = 0 (one-sided D1)
        A[1, :] = 0.0; B[1, :] = 0.0; A[1, :N] = D1[0, :]
        A[N - 2, :] = 0.0; B[N - 2, :] = 0.0; A[N - 2, :N] = D1[-1, :]
    else:                                        # free-slip: D^2 W = 0 (one-sided D2)
        A[1, :] = 0.0; B[1, :] = 0.0; A[1, :N] = D2[0, :]
        A[N - 2, :] = 0.0; B[N - 2, :] = 0.0; A[N - 2, :N] = D2[-1, :]
    for idx in (N, 2 * N - 1):                   # Theta = 0
        A[idx, :] = 0.0; B[idx, :] = 0.0; A[idx, idx] = 1.0
    w = eig(A, B, right=False)
    w = w[np.isfinite(w)]
    w = w[np.abs(w.imag) < 1e-6 * np.abs(w.real) + 1e-9].real
    w = w[w > 1.0]
    return float(np.min(w)) if len(w) else np.inf


def critical(bc, N):
    res = minimize_scalar(lambda a: Ra_of_a(a, N, bc), bounds=(1.5, 4.5), method="bounded")
    Ra_c, a_c = float(res.fun), float(res.x)
    err = 100.0 * abs(Ra_c - TEXTBOOK[bc]["Ra"]) / TEXTBOOK[bc]["Ra"]
    return {"bc": bc, "Ra_c": round(Ra_c, 2), "a_c": round(a_c, 3),
            "textbook_Ra": TEXTBOOK[bc]["Ra"], "textbook_a": TEXTBOOK[bc]["a"],
            "err_pct": round(err, 3), "within_0p4pct": bool(err < 0.4)}


def simulate(quick=False):
    N = 60 if quick else 64
    rows = [critical(bc, N) for bc in ("noslip", "freeslip")]
    # dispersion curve for the atlas (no-slip), Ra(a) around the minimum
    a_grid = np.linspace(1.8, 4.4, 14)
    disp = [{"a": round(float(a), 3), "Ra": round(Ra_of_a(a, N, "noslip"), 1)} for a in a_grid]
    return {"N": N, "rows": rows, "dispersion_noslip": disp,
            "both_within_0p4pct": bool(all(r["within_0p4pct"] for r in rows))}


def evaluate(result, quick=False):
    by = {r["bc"]: r for r in result["rows"]}
    checks = {
        "no-slip Ra_c ~ 1708 (<0.4%)": by["noslip"]["within_0p4pct"],
        "free-slip Ra_c ~ 657.5 (<0.4%)": by["freeslip"]["within_0p4pct"],
        "no-slip Ra_c > free-slip Ra_c (rigid harder)": by["noslip"]["Ra_c"] > by["freeslip"]["Ra_c"],
    }
    return all(checks.values()), checks


def _atlas(result):
    by = {r["bc"]: r for r in result["rows"]}
    return [{
        "experiment": "e017 walled Rayleigh-Benard linear onset", "tier": "measured",
        "put_in": "linearized marginal Boussinesq operator + wall BCs (no-slip / free-slip); Ra_c not put in",
        "emerged": ["no-slip Ra_c=%.1f @ a_c=%.3f (textbook 1707.76, err %.2f%%)"
                    % (by["noslip"]["Ra_c"], by["noslip"]["a_c"], by["noslip"]["err_pct"]),
                    "free-slip Ra_c=%.1f @ a_c=%.3f (textbook 657.5, err %.2f%%)"
                    % (by["freeslip"]["Ra_c"], by["freeslip"]["a_c"], by["freeslip"]["err_pct"])],
        "surprises": ["the periodic-box Ra_c~20 (e013) is exposed as an artifact; walls give the textbook 1708/657.5"],
        "persistence": "linear onset -- a threshold, not a persistent state (nonlinear saturation is Stage 2)",
        "measured_numbers": {"rows": result["rows"], "dispersion_noslip": result["dispersion_noslip"]},
        "not_scripted_check": "Ra_c and a_c are eigenvalue readouts; only the operator and BCs are put in",
        "claim_tier": "measured (Ra_c, a_c both BCs vs textbook) ; interpretive (periodic-box onset is an artifact)",
        "floors": ["linear onset only (no amplitude); fixed 1D grid in z",
                   "the tangential BC MUST use a one-sided stencil (free-slip D^2W=0, no-slip DW=0) or the eigenproblem diverges"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e017 walled RB linear stability")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e017 walled Rayleigh-Benard: critical Rayleigh number ===")
    for row in r["rows"]:
        print("  %-9s Ra_c=%8.2f @ a_c=%.3f   (textbook %.2f @ %.3f, err %.3f%%)  [%s]"
              % (row["bc"], row["Ra_c"], row["a_c"], row["textbook_Ra"], row["textbook_a"],
                 row["err_pct"], "OK" if row["within_0p4pct"] else "OFF"))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (textbook Ra_c recovered to <0.4%%; periodic-box ~20 is an artifact)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "rb_linear_stability.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/rb_linear_stability.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
