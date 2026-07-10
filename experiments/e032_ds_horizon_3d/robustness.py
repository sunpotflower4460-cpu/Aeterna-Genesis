#!/usr/bin/env python3
"""e032 robustness (LAW.md audit 6): the 2+1 area law and the coefficient's density-drift must survive a
fresh seed batch and a different box height H. What must not move: the count stays linear in the cut width
(area law) and the coefficient grows with density (the d>2 pathology)."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e032_ds_horizon_3d import horizon_3d as H3  # noqa: E402


def _case(seeds, box_H):
    p = dict(H3.DEFAULT)
    p.update({"seeds": seeds, "densities": [1500, 4500], "H": box_H})
    lo_slope, lo_r2, _ = H3._area_law(p["densities"][0], p)
    hi_slope, hi_r2, _ = H3._area_law(p["densities"][1], p)
    ratio = hi_slope / max(lo_slope, 1e-9)
    ok = lo_r2 > 0.85 and hi_r2 > 0.85 and ratio > 1.3
    return {"seeds": seeds, "H": box_H, "r2_lo": round(lo_r2, 3), "r2_hi": round(hi_r2, 3),
            "coef_ratio": round(ratio, 2), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case([10, 11, 12], 0.5)] if quick else [
        _case([10, 11, 12], 0.5), _case([20, 21, 22], 0.4), _case([30, 31, 32], 0.6)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e032 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e032 robustness (2+1 area law + coefficient drift vs seed / box height) ===")
    for c in r["cases"]:
        print("  seeds=%s H=%s: R2 lo/hi=%s/%s coef_ratio=%s ok=%s"
              % (c["seeds"], c["H"], c["r2_lo"], c["r2_hi"], c["coef_ratio"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
