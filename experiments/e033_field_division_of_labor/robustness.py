#!/usr/bin/env python3
"""e033 robustness (LAW.md audit 6): the field division of labor must survive a fresh seed batch and a
different gradient penalty kappa (which sets the interface width). What must not move: the field stays
homogeneous below the Flory-Huggins critical point chi_c=2, demixes into two coexisting phases above it,
and the coexisting compositions match the theoretical binodal. NONE of these are put in."""

import argparse
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e033_field_division_of_labor import field_division as FD  # noqa: E402


def _case(seeds, kappa):
    p = dict(FD.DEFAULT)
    p.update({"seeds": seeds, "kappa": kappa, "chis": [1.5, 2.5], "steps": 5000})
    mixed = FD._measure(1.5, p)
    sep = FD._measure(2.5, p)
    binodal_err = max(abs(sep["phase_lo"] - sep["binodal_lo"]),
                      abs(sep["phase_hi"] - sep["binodal_hi"]))
    ok = (mixed["order_param"] < 0.05 and sep["both_phases_frac"] > 0.9 and binodal_err < 0.06)
    return {"seeds": seeds, "kappa": kappa, "op_mixed": mixed["order_param"],
            "both_sep": sep["both_phases_frac"], "binodal_err": round(binodal_err, 3), "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case([5, 6], 1.0)] if quick else [
        _case([5, 6], 1.0), _case([7, 8], 0.5), _case([9, 10], 2.0)]
    return {"cases": cases, "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="e033 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e033 robustness (homogeneous<chi_c / two phases>chi_c / binodal match vs seed & kappa) ===")
    for c in r["cases"]:
        print("  seeds=%s kappa=%s: op_mixed=%s both_sep=%s binodal_err=%s ok=%s"
              % (c["seeds"], c["kappa"], c["op_mixed"], c["both_sep"], c["binodal_err"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
