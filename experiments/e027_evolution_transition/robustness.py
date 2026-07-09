#!/usr/bin/env python3
"""e027 robustness (LAW.md audit 6): the population-level gate SIGNS must survive the RNG seed.
Absolute statistics (std, exact genome length, cooperator fraction) are floors; what must not move is:
mutation ON adapts while OFF is stuck; a rich environment raises complexity above a simple one; spatial
cooperation survives while well-mixed collapses. We sweep seeds (short runs) and confirm."""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from experiments.e027_evolution_transition import evolution as E    # noqa: E402
from experiments.e027_evolution_transition import openended as O    # noqa: E402
from experiments.e027_evolution_transition import transition as T   # noqa: E402


def _evo_case(seed):
    p = dict(E.DEFAULT)
    p.update({"seed": seed, "N": 250, "T": 250})
    rng = np.random.default_rng(seed)
    peak = lambda x, g: np.exp(-(x - 1.5) ** 2 / (2 * 0.3 ** 2))
    _, Hon = E.evolve(peak, p, rng, sigma_mut=0.05)
    _, Hoff = E.evolve(peak, p, rng, sigma_mut=0.0)
    ok = abs(Hon[-1][1] - 1.5) < 0.3 and abs(Hoff[-1][1]) < 0.1
    return {"seed": seed, "mean_on": round(Hon[-1][1], 2), "mean_off": round(Hoff[-1][1], 2), "ok": bool(ok)}


def _open_case(seed):
    p = dict(O.DEFAULT)
    p.update({"seed": seed, "Npop": 150, "T": 180})
    rng = np.random.default_rng(seed)
    _, Hs = O.evolve(lambda g: O._spread(2), p, rng)
    _, Hr = O.evolve(lambda g: O._spread(8), p, rng)
    ok = Hs[-1][1] < 3.5 and Hr[-1][1] > Hs[-1][1] + 2
    return {"seed": seed, "len_simple": Hs[-1][1], "len_rich": Hr[-1][1], "ok": bool(ok)}


def _trans_case(seed):
    p = dict(T.DEFAULT)
    # a slightly larger grid than --quick so the assortment signal is clear of the 0.1 gate
    # boundary (a small-grid finite-size effect, not a physics change); full scale gives ~0.13
    p.update({"seed": seed, "N": 100, "steps": 90})
    rng = np.random.default_rng(seed)
    N, b = p["N"], p["b"]
    S = (rng.random((N, N)) < 0.5).astype(int)
    for _ in range(p["steps"]):
        S = T._step(S, b)
    coop_sp = float(S.mean())
    assort = T._assortment(S)
    S = (rng.random((N, N)) < 0.5).astype(int)
    for _ in range(p["steps"]):
        flat = S.flatten(); rng.shuffle(flat); S = flat.reshape(N, N)
        S = T._step(S, b)
    coop_wm = float(S.mean())
    ok = coop_wm < 0.1 and coop_sp > 0.2 and assort > 0.1
    return {"seed": seed, "coop_wm": round(coop_wm, 2), "coop_sp": round(coop_sp, 2),
            "assort": round(assort, 2), "ok": bool(ok)}


def simulate(quick=False):
    seeds = [0, 1] if quick else [0, 1, 2, 3, 4]
    evo = [_evo_case(s) for s in seeds]
    opn = [_open_case(s) for s in seeds]
    trn = [_trans_case(s) for s in seeds]
    return {
        "evolution": evo, "openended": opn, "transition": trn,
        "evolution_all_ok": all(c["ok"] for c in evo),
        "openended_all_ok": all(c["ok"] for c in opn),
        "transition_all_ok": all(c["ok"] for c in trn),
        "robust": bool(all(c["ok"] for c in evo + opn + trn)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="e027 robustness sweep")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e027 robustness (gate signs vs seed) ===")
    print("  evolution all ok:  %s" % r["evolution_all_ok"])
    print("  openended all ok:  %s" % r["openended_all_ok"])
    print("  transition all ok: %s" % r["transition_all_ok"])
    print("  ROBUST: %s" % r["robust"])
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "robustness.json")
        with open(out, "w") as f:
            json.dump(r, f, indent=2)
        print("wrote robustness.json")
    return 0 if r["robust"] else 1


if __name__ == "__main__":
    sys.exit(main())
