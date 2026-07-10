#!/usr/bin/env python3
"""e040 robustness (LAW.md audit 6): spiral coexistence is a STOCHASTIC, regime-bounded phenomenon -- most
seeds lock into sustained spirals (all three persist) but some initial conditions collapse to one type
(finite-size bistability, a stated floor), and over-diffusion (D>~0.8) homogenizes. What is robust: at the
operating point (N=200, D=0.6) the MAJORITY of seeds form spirals, and the well-mixed control ALWAYS
collapses to one type. Not put in."""
import argparse, json, os, sys
_R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _R not in sys.path: sys.path.insert(0, _R)
from experiments.e040_field_rps_cooperation import rps_cooperation as R  # noqa: E402


def simulate(quick=False):
    p0 = dict(R.DEFAULT)
    seeds = [0, 1, 2] if quick else [0, 1, 2, 3, 4]
    rows, n_spiral, n_wm_collapse = [], 0, 0
    for s in seeds:
        p = dict(p0); p.update({"N": 200, "steps": 5000, "D": 0.6, "seed": s})
        a, b, c, _ = R._run_spatial(p)
        allp = bool(a.mean() > 0.02 and b.mean() > 0.02 and c.mean() > 0.02 and a.std() > 0.03)
        aw, bw, cw = R._run_wellmixed(p)
        wmc = bool(max(aw, bw, cw) > 0.8 and min(aw, bw, cw) < 0.05)
        n_spiral += allp; n_wm_collapse += wmc
        rows.append({"seed": s, "C": round(float(a.mean()), 3), "spiral": allp, "wm_collapse": wmc})
    frac = n_spiral / len(seeds)
    # robust = MAJORITY of seeds form spirals AND the well-mixed control ALWAYS collapses
    robust = bool(frac >= 0.6 and n_wm_collapse == len(seeds))
    return {"rows": rows, "spiral_fraction": round(frac, 2), "n_wm_collapse": n_wm_collapse,
            "n_seeds": len(seeds), "robust": robust}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv); r = simulate(quick=a.quick)
    print("=== e040 robustness (spiral fraction over seeds + well-mixed always collapses) ===")
    for c in r["rows"]:
        print("  seed=%s: C=%s spiral=%s wm_collapse=%s" % (c["seed"], c["C"], c["spiral"], c["wm_collapse"]))
    print("  spiral_fraction=%s (%s/%s), wm_collapse=%s/%s  ROBUST: %s"
          % (r["spiral_fraction"], int(r["spiral_fraction"] * r["n_seeds"]), r["n_seeds"],
             r["n_wm_collapse"], r["n_seeds"], r["robust"]))
    if not a.no_write and not a.quick:
        json.dump(r, open(os.path.join(os.path.dirname(__file__), "robustness.json"), "w"), indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
