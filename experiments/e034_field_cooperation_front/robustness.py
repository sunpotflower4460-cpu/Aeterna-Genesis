#!/usr/bin/env python3
"""e034 robustness (LAW.md audit 6): the front picture must survive a different diffusion D and time step.
What must not move: the well-mixed sub-threshold seed decays; the front invades below a=1/2 and retreats
above it; the zero-velocity (Maxwell) threshold stays at a_c~0.5 and the speed tracks the Nagumo law
c=sqrt(D/2)(1-2a) (so it SCALES with sqrt(D) but the THRESHOLD does not move). None are put in."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e034_field_cooperation_front import cooperation_front as CF  # noqa: E402


def _case(D, dt):
    p = dict(CF.DEFAULT)
    p.update({"D": D, "dt": dt, "as": [0.40, 0.50, 0.60]})
    rows = [{"a": a, "c": CF._front_velocity(a, p), "th": np.sqrt(D / 2.0) * (1 - 2 * a)} for a in p["as"]]
    aa = np.array([r["a"] for r in rows]); cc = np.array([r["c"] for r in rows])
    maxwell = float(np.interp(0.0, cc[::-1], aa[::-1]))
    speed_err = float(np.max(np.abs(cc - np.array([r["th"] for r in rows]))))
    wm = CF._well_mixed(p["wm_seed"], 0.40, p)
    ok = (abs(maxwell - 0.5) < 0.03 and speed_err < 0.03 and wm < 0.1
          and rows[0]["c"] > 0.02 and rows[-1]["c"] < -0.02)
    return {"D": D, "dt": dt, "maxwell": round(maxwell, 3), "speed_err": round(speed_err, 3),
            "wm_below": round(wm, 3), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(1.0, 0.05)] if quick else [_case(1.0, 0.05), _case(0.5, 0.05), _case(2.0, 0.025)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e034 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e034 robustness (Maxwell threshold + Nagumo speed vs diffusion D / time step) ===")
    for c in r["cases"]:
        print("  D=%s dt=%s: maxwell=%s speed_err=%s wm_below=%s ok=%s"
              % (c["D"], c["dt"], c["maxwell"], c["speed_err"], c["wm_below"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
