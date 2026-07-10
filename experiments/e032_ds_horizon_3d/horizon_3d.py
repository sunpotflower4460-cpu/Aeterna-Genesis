#!/usr/bin/env python3
"""e032 -- the 3D Dou-Sorkin pathology: the 2+1 area law holds, but the coefficient loses universality.

MODULE:   e032_ds_horizon_3d  [FRONTIER]
QUESTION: e022 showed the 2D Dou-Sorkin horizon count is a density-INDEPENDENT pure number. In 3D (2+1)
          the DS coefficient has a known IR pathology (d>2). Can we MEASURE both: (a) the area law still
          holds (count proportional to the cut length), and (b) the coefficient is NO LONGER
          density-independent (it drifts), unlike the clean 2D number?
PUT IN:   Poisson sprinklings in a 2+1 Minkowski box; a null horizon v=t-x=0 (all y) with an anchor; the
          DS molecule rule; the cut Sigma-cap-H is a LINE along y. NO "area law" and NO "coefficient
          drifts" are put in -- both are measured.
EMERGED:  (measured) the molecule count is LINEAR in the y-window width w (an area law, R^2>0.85); the
          coefficient count/w GROWS with the sprinkling density (ratio >>1 over a density range), i.e. it
          is NOT the density-independent pure number the 2D case gives.
CLAIM TIER: measured(2+1 area law; density-dependent coefficient) ; interpretive(the DS entropy count keeps
          its AREA scaling in 3D but loses the coefficient's universality -- the d>2 IR pathology, so 3D is
          a FLOOR while 2D is SOLID) ; analogy(black-hole entropy area law) ; FRONTIER.
KNOWN MATCH: Dou-Sorkin causal-set entropy molecules; the area law; the d>2 IR pathology (Barton et al.
          proposed CURED molecules -- not reproduced here).
STATUS:   GREEN (gates on the molecule count and its coefficient -- physical/statistical quantities).
A_OR_B:   (A) faithful. Hand input = the sprinkling + the DS molecule rule; the linearity in w and the
          density-drift of the coefficient are emergent and measured.

THE TRAP (designer hit it, we avoid it): the AREA LAW (count proportional to cut length) is the robust,
frame-independent claim; the COEFFICIENT is the box/density-dependent quantity that is the pathology.
Gate on the linearity AND on the coefficient's density-drift -- never claim the 3D coefficient is a
universal number (it is not; Barton's cured molecules are frontier, not implemented here).

Floors: FRONTIER -- this QUANTIFIES the obstacle (density-dependent coefficient); it does NOT cure it. The
cured (Barton) molecules are not reproduced. "Entropy / horizon / black hole" is analogy for the count.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"H": 0.5, "ws": [0.2, 0.4, 0.6, 0.8], "densities": [2000, 6000, 18000],
           "seeds": [0, 1, 2, 3, 4], "seed0": 700}
QUICK = {"densities": [1500, 4500], "seeds": [0, 1, 2]}


def _molecule_midpoints(rho0, H, seed):
    """Midpoint-y of each Dou-Sorkin horizon molecule in a 2+1 Minkowski box."""
    rng = np.random.default_rng(seed)
    M = rng.poisson(rho0 * (2 * H) ** 3)
    t = rng.uniform(-H, H, M)
    x = rng.uniform(-H, H, M)
    yy = rng.uniform(-H, H, M)
    u = t + x
    v = t - x
    N = M
    R = np.zeros((N, N), bool)
    for i0 in range(0, N, 1500):
        i1 = min(i0 + 1500, N)
        dt = t[None, :] - t[i0:i1, None]
        dd = np.sqrt((x[None, :] - x[i0:i1, None]) ** 2 + (yy[None, :] - yy[i0:i1, None]) ** 2)
        R[i0:i1] = (dt > 0) & (dt > dd)
    vpos = np.where(v > 0)[0]
    sub = R[np.ix_(vpos, vpos)]
    miny = vpos[~sub.any(axis=0)]
    miny = miny[u[miny] > 0]
    R1set = np.zeros(N, bool)
    R1set[(u < 0) & (v < 0)] = True
    mids = []
    for q in miny:
        past = R[:, q]
        cand = np.where(past & R1set)[0]
        if cand.size == 0:
            continue
        pidx = np.where(past)[0]
        link = ~R[np.ix_(cand, pidx)].any(axis=1)
        for xi in cand[link]:
            mids.append(0.5 * (yy[xi] + yy[q]))
    return np.array(mids)


def _area_law(rho0, p):
    """Return (coefficient count/w slope, R^2 of linear fit) averaged over seeds."""
    ws = p["ws"]
    counts = np.zeros((len(p["seeds"]), len(ws)))
    for i, s in enumerate(p["seeds"]):
        m = _molecule_midpoints(rho0, p["H"], p["seed0"] + s)
        for j, w in enumerate(ws):
            counts[i, j] = ((m >= -w / 2) & (m <= w / 2)).sum()
    mean = counts.mean(0)
    slope, intercept = np.polyfit(ws, mean, 1)
    fit = np.polyval([slope, intercept], ws)
    ss_res = float(np.sum((mean - fit) ** 2))
    ss_tot = float(np.sum((mean - mean.mean()) ** 2)) + 1e-12
    r2 = 1 - ss_res / ss_tot
    return float(slope), float(r2), [round(float(c), 1) for c in mean]


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for rho in p["densities"]:
        slope, r2, counts = _area_law(rho, p)
        rows.append({"density": rho, "coefficient": round(slope, 1), "r2": round(r2, 3), "counts": counts})
    coef_lo = rows[0]["coefficient"]
    coef_hi = rows[-1]["coefficient"]
    return {
        "params": p, "rows": rows,
        "area_law_all_linear": bool(all(r["r2"] > 0.85 for r in rows)),
        "coefficient_ratio": round(coef_hi / max(coef_lo, 1e-9), 2),
        "density_ratio": round(p["densities"][-1] / p["densities"][0], 2),
    }


def evaluate(result, quick=False):
    checks = {
        "area_law_holds_2plus1 (count linear in cut width, R^2>0.85)":
            result["area_law_all_linear"],
        "coefficient_density_dependent (coef ratio >1.3 over density range = d>2 pathology)":
            bool(result["coefficient_ratio"] > 1.3),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e032 ds horizon 3d (2+1 area law; density-dependent coefficient)", "tier": "measured/frontier",
        "put_in": "2+1 Minkowski sprinklings + a null horizon + the DS molecule rule; cut is a line along y",
        "emerged": ["molecule count linear in y-window width (area law): %s"
                    % [(r["density"], r["counts"], r["r2"]) for r in result["rows"]],
                    "coefficient count/w vs density: %s -> ratio %s over a density ratio %s (NOT a pure number)"
                    % ([(r["density"], r["coefficient"]) for r in result["rows"]],
                       result["coefficient_ratio"], result["density_ratio"])],
        "surprises": ["the AREA LAW survives to 2+1, but the coefficient DRIFTS with density -- the "
                      "density-independence that made the 2D count a pure number is lost"],
        "persistence": "the linear-in-w area law holds at every density; the coefficient keeps drifting with density",
        "measured_numbers": {"rows": result["rows"], "coefficient_ratio": result["coefficient_ratio"],
                             "density_ratio": result["density_ratio"]},
        "not_scripted_check": "the linearity and the coefficient drift are measured from the sprinklings",
        "claim_tier": "measured (2+1 area law; density-dependent coefficient) ; interpretive (DS keeps area "
                      "scaling but loses coefficient universality in d>2 = why 3D is a floor) ; analogy (BH "
                      "entropy area law) ; FRONTIER",
        "floors": ["FRONTIER: this QUANTIFIES the d>2 IR pathology; it does NOT cure it (Barton cured "
                   "molecules not reproduced)",
                   "the 3D coefficient is NOT a universal number -- 3D stays a floor while 2D (e022) is SOLID",
                   "'entropy / horizon / black hole' is analogy for the molecule count"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e032 3D DS horizon pathology [frontier]")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e032 [FRONTIER] -- 3D Dou-Sorkin: area law holds, coefficient loses universality ===")
    for row in r["rows"]:
        print("  density=%6d: counts(vs w)=%s  coefficient=%.1f  R^2=%.3f"
              % (row["density"], row["counts"], row["coefficient"], row["r2"]))
    print("  coefficient ratio = %s over density ratio %s (2D would be ~1; 3D drifts = pathology)"
          % (r["coefficient_ratio"], r["density_ratio"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (2+1 area law measured; coefficient is a FLOOR, d>2 pathology)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "horizon_3d.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/horizon_3d.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
