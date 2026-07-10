#!/usr/bin/env python3
"""e041 robustness (LAW.md audit 6): narrow neck -> clonal, wide neck -> mixed must survive a different body
size and seed set. Not put in."""
import argparse, json, os, sys
import numpy as np
_R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _R not in sys.path: sys.path.insert(0, _R)
from experiments.e041_field_bottleneck import bottleneck as B  # noqa: E402


def _case(Ncells, seeds):
    nf_n, rel_n = np.mean([B._daughter(0.0003, s, Ncells) for s in seeds], axis=0)
    nf_w, rel_w = np.mean([B._daughter(1.0, s, Ncells) for s in seeds], axis=0)
    ok = nf_n < 3 and rel_n > 0.5 and rel_w < 0.1 and nf_w > 100
    return {"Ncells": Ncells, "narrow": [round(float(nf_n), 1), round(float(rel_n), 3)],
            "wide": [round(float(nf_w), 1), round(float(rel_w), 3)], "ok": bool(ok)}


def simulate(quick=False):
    cases = [_case(2000, [0, 1, 2])] if quick else [_case(3000, range(6)), _case(1500, range(4)), _case(5000, range(4))]
    return {"cases": [dict(c) for c in cases], "robust": bool(all(c["ok"] for c in cases))}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv); r = simulate(quick=a.quick)
    print("=== e041 robustness (narrow->clonal / wide->mixed vs body size / seeds) ===")
    for c in r["cases"]:
        print("  Ncells=%s: narrow(f,rel)=%s wide(f,rel)=%s ok=%s" % (c["Ncells"], c["narrow"], c["wide"], c["ok"]))
    print("  ROBUST: %s" % r["robust"])
    if not a.no_write and not a.quick:
        json.dump(r, open(os.path.join(os.path.dirname(__file__), "robustness.json"), "w"), indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
