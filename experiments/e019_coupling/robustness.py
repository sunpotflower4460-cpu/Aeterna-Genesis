#!/usr/bin/env python3
"""e019 robustness (LAW.md audit 6): transport (centroid moves with U) and the
held-then-torn Q_H(U) crossover must survive changing the roll size R and the
particle stiffness c4. The crossover value U_c may shift; the qualitative
carry-then-tear must not."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e019_coupling import coupling as e019  # noqa: E402


def _case(c4, roll_R, L, n_steps):
    p = dict(e019.DEFAULT)
    p.update({"c4": c4, "roll_R": roll_R, "L": L, "n_steps": n_steps,
              "settle_steps": 110, "U_list": [0.0, 4.0, 8.0, 11.0]})
    rows = [e019.run_U(p, U) for U in p["U_list"]]
    disp = [r["centroid_disp"] for r in rows]
    moves = all(disp[i] <= disp[i + 1] + 1e-6 for i in range(len(disp) - 1)) and disp[-1] > disp[0] + 1e-2
    low_holds = rows[1]["held"]        # U=4
    high_torn = not rows[-1]["held"]   # U=11
    return {"c4": c4, "roll_R": roll_R, "L": L,
            "disp": [round(d, 2) for d in disp],
            "moves": bool(moves), "low_holds": bool(low_holds), "high_torn": bool(high_torn),
            "pass": bool(moves and low_holds and high_torn)}


def run_sweep(quick=False):
    if quick:
        cases = [(20.0, 5.0, 40, 180)]
    else:
        cases = [(20.0, 5.0, 44, 240), (25.0, 5.0, 44, 240), (20.0, 6.5, 44, 240)]
    return [_case(*c) for c in cases]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e019 robustness")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    rows = run_sweep(quick=args.quick)
    for r in rows:
        print("  c4=%.0f R=%.1f L=%d: disp=%s moves=%s low_holds=%s high_torn=%s  %s"
              % (r["c4"], r["roll_R"], r["L"], r["disp"], r["moves"], r["low_holds"],
                 r["high_torn"], "PASS" if r["pass"] else "FAIL"))
    npass = sum(r["pass"] for r in rows)
    ok = npass == len(rows)
    print("ROBUSTNESS: %s (%d/%d cases PASS)" % ("GREEN" if ok else "MIXED", npass, len(rows)))
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump({"cases": rows}, f, indent=2)
        print("wrote robustness.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
