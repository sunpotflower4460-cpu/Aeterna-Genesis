#!/usr/bin/env python3
"""e008 Stage 2 (3D): quantized vortex LINES from a 3D quench.

Same white start + one law (damped 3D GPE) as Stage 1, now in 3D: the quench
nucleates a tangle of vortex LINES. We label the depleted-core voxels into
(periodic-aware) connected components and classify each as a CONTRACTIBLE loop
(bounded, lives in the bulk) or a TORUS-WRAPPING line (reaches both faces of an
axis -- a non-contractible cycle of the periodic box). NOTE: in a periodic box
BOTH are genuine closed quantized vortex lines (a wrapping line closes through
the boundary); there are no open ends. Measured: that lines emerge, the
contractible fraction, and how the line count falls as the quench slows (3D KZ).

HONESTY / correction (Codex review P2): an earlier version used non-periodic
ndimage.label, which SPLIT torus-wrapping lines at the faces into fragments that
each looked like a small contractible loop -- inflating the "closed fraction" to
~0.94. With correct periodic union-find the contractible fraction is ~0.30: most
lines actually WRAP the torus. The robust, defensible claim is therefore
"quantized vortex lines emerge from white noise and thin out with slower quench
(3D KZ)" -- NOT "mostly small closed loops" (that was an artifact).

Floors (honest): the field is only PARTIALLY condensed at the count time (thick
cores), so the contractible/wrapping split is still a voxel-topology PROXY, not
an exact vortex-line trace. Reuses core 3D (e003).
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
    """Closed-loop vs box-spanning classification of depleted-core components.

    The field lives in an FFT-PERIODIC box, but ndimage.label uses non-periodic
    adjacency, so a vortex line crossing an opposite face is SPLIT into pieces
    that would each look like a small closed loop -- inflating the closed
    fraction (Codex review P2). We union components across opposite faces with a
    union-find before classifying. A unioned component that touches both faces
    of an axis (extent ~L) wraps the torus -> spanning; a bulk component that
    never reaches a face -> closed. Still a voxel-topology PROXY, not an exact
    vortex-line trace (floor stated in AUDIT/harvest).
    """
    rho = np.abs(psi) ** 2
    mask = rho < frac * rho.mean()
    lab, n = ndimage.label(mask, structure=np.ones((3, 3, 3)))
    L = psi.shape[0]

    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    # Union masked voxels that are 26-adjacent across each periodic face pair.
    for axis in range(3):
        f0 = np.take(lab, 0, axis=axis)
        f1 = np.take(lab, L - 1, axis=axis)
        h, w = f0.shape
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                rolled = np.roll(f1, (da, db), axis=(0, 1))
                both = (f0 > 0) & (rolled > 0)
                for l0, l1 in zip(f0[both], rolled[both]):
                    union(int(l0), int(l1))

    groups = {}
    for i in range(1, n + 1):
        groups.setdefault(find(i), []).append(i)

    closed = spanning = 0
    for members in groups.values():
        pts = np.concatenate([np.argwhere(lab == i) for i in members])
        if len(pts) < 4:                     # ignore tiny specks
            continue
        ext = pts.max(0) - pts.min(0) + 1
        if any(e >= L - 1 for e in ext):     # reaches both faces of an axis = wraps
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
        rows.append({"tauQ": tauQ, "contractible_loops": c, "wrapping_lines": s,
                     "contractible_fraction": round(cf, 3),
                     "rho_median": round(rm, 3)})
    lines = [r["contractible_loops"] + r["wrapping_lines"] for r in rows]
    return {
        "params": p, "rows": rows,
        "vortex_lines_emerge": bool(all(li > 0 for li in lines)),
        # reported data, NOT a pass gate: a wrapping line is also a closed line.
        "mean_contractible_fraction": round(
            float(np.mean([r["contractible_fraction"] for r in rows])), 3),
        "lines_decrease_with_tauQ": bool(lines[-1] <= lines[0]),
    }


def evaluate(result):
    # GREEN gates ONLY on defensible facts: quantized vortex lines emerge from
    # white noise, and their count thins with slower quench (3D KZ). The
    # contractible-vs-wrapping split is reported as DATA, not a gate -- in a
    # periodic box a torus-wrapping line is an equally valid closed vortex line.
    checks = {
        "vortex_lines_emerge": result["vortex_lines_emerge"],
        "lines_decrease_with_tauQ(3D_KZ)": result["lines_decrease_with_tauQ"],
    }
    return all(checks.values()), checks


def main(argv=None):
    ap = argparse.ArgumentParser(description="e008 Stage 2 (3D torus)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    result = simulate(quick=args.quick)
    print(__doc__)
    print("------------------------- 3D vortex lines -------------------------")
    for r in result["rows"]:
        print("  tauQ=%4d  contractible=%3d  wrapping=%2d  contractible_frac=%.2f  rho_med=%.2f"
              % (r["tauQ"], r["contractible_loops"], r["wrapping_lines"],
                 r["contractible_fraction"], r["rho_median"]))
    print("  mean contractible fraction = %.2f (rest WRAP the torus = also closed lines;"
          " ~0.94 in the old non-periodic labeling was an artifact)"
          % result["mean_contractible_fraction"])
    passed, checks = evaluate(result)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (GREEN gate = lines emerge + 3D KZ; contractible split reported as data;"
          " floor: partial condensation)" % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "result3d.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        print("wrote %s" % out)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
