#!/usr/bin/env python3
"""e008 Stage 2 (3D): closed vortex loops (the torus) from a 3D quench.

Same white start + one law (damped 3D GPE) as Stage 1, now in 3D: the quench
nucleates a tangle of vortex LINES. We label the depleted-core voxels into
connected components and classify each as a CLOSED LOOP (bounded extent -- a
torus topologically) or a line that SPANS the periodic box. Measured: the
closed-loop fraction and how the loop count falls as the quench slows (3D KZ).

Floors (honest): the field is only PARTIALLY condensed at the count time (thick
cores), so the closed/spanning split is a voxel-topology PROXY, not an exact
vortex-line trace. "Torus" = the topological fact that the core is a closed
loop, not a claim about spacetime. Reuses core 3D (e003).
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy import ndimage

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field  # noqa: E402
from core.fft import k_squared_3d  # noqa: E402

DEFAULT = {"L": 48, "g": 1.0, "mu_i": -1.0, "mu_f": 1.0, "dt": 0.05,
           "gamma": 0.4, "noise": 0.05, "hold": 300, "frac": 0.2,
           "tauQ_list": [100, 200, 400]}
QUICK = {"L": 40, "tauQ_list": [100, 200], "hold": 200}


def quench3d(p, tauQ, seed=1):
    L, g = p["L"], p["g"]
    k2 = k_squared_3d(L)
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L, L))
                        + 1j * rng.standard_normal((L, L, L)))
    cf = 1j + p["gamma"]
    for s in range(tauQ + p["hold"]):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / tauQ)
        rho = np.abs(psi) ** 2
        psi = psi * np.exp(-cf * (g * rho - mu) * p["dt"] * 0.5)
        ph = np.fft.fftn(psi)
        ph *= np.exp(-cf * 0.5 * k2 * p["dt"])
        psi = np.fft.ifftn(ph)
        rho = np.abs(psi) ** 2
        psi = psi * np.exp(-cf * (g * rho - mu) * p["dt"] * 0.5)
    return psi


def loop_fraction(psi, frac):
    """Closed-loop vs box-spanning classification of depleted-core components."""
    rho = np.abs(psi) ** 2
    mask = rho < frac * rho.mean()
    lab, n = ndimage.label(mask, structure=np.ones((3, 3, 3)))
    L = psi.shape[0]
    closed = spanning = 0
    for i in range(1, n + 1):
        pts = np.argwhere(lab == i)
        if len(pts) < 4:                     # ignore tiny specks
            continue
        ext = pts.max(0) - pts.min(0) + 1
        if any(e >= L - 1 for e in ext):
            spanning += 1
        else:
            closed += 1
    total = closed + spanning
    return closed, spanning, (closed / total if total else 0.0), float(np.median(rho))


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for tauQ in p["tauQ_list"]:
        psi = quench3d(p, tauQ)
        c, s, cf, rm = loop_fraction(psi, p["frac"])
        rows.append({"tauQ": tauQ, "closed_loops": c, "spanning_lines": s,
                     "closed_fraction": round(cf, 3), "rho_median": round(rm, 3)})
    loops = [r["closed_loops"] + r["spanning_lines"] for r in rows]
    return {
        "params": p, "rows": rows,
        "closed_loops_emerge": bool(all(r["closed_loops"] > 0 for r in rows)),
        "mean_closed_fraction": round(
            float(np.mean([r["closed_fraction"] for r in rows])), 3),
        "loops_decrease_with_tauQ": bool(loops[-1] <= loops[0]),
    }


def evaluate(result):
    checks = {
        "closed_loops_emerge": result["closed_loops_emerge"],
        "mostly_closed_loops": result["mean_closed_fraction"] > 0.5,
        "loops_decrease_with_tauQ(3D_KZ)": result["loops_decrease_with_tauQ"],
    }
    return all(checks.values()), checks


def main(argv=None):
    ap = argparse.ArgumentParser(description="e008 Stage 2 (3D torus)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    result = simulate(quick=args.quick)
    print(__doc__)
    print("------------------------- 3D vortex loops -------------------------")
    for r in result["rows"]:
        print("  tauQ=%4d  closed_loops=%3d  spanning=%2d  closed_frac=%.2f  rho_med=%.2f"
              % (r["tauQ"], r["closed_loops"], r["spanning_lines"],
                 r["closed_fraction"], r["rho_median"]))
    print("  mean closed-loop fraction = %.2f (torus = closed vortex line)"
          % result["mean_closed_fraction"])
    passed, checks = evaluate(result)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (measured: loops + fraction; 'torus'=topology; floor: partial condensation)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "result3d.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        print("wrote %s" % out)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
