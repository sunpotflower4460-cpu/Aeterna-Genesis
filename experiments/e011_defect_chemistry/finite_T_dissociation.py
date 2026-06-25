#!/usr/bin/env python3
"""e011 Stage 2 (NEW build) -- thermal dissociation of a bound +/- pair.

Stage 1 (x_pair_binding) showed the +/- pair is a BOUND dipole under the
conservative GPE. Here we put it in a finite-temperature bath -- the STOCHASTIC
GPE (core.field.step_sgpe_2d, a Langevin equation with fluctuation-dissipation
noise sqrt(2 gamma T) dW) -- and ask: does temperature DISSOCIATE the pair, and
does the lifetime fall as T rises (thermally activated decay)?

We imprint a +/- pair, track it by continuity (track_two_vortices, a TIGHT
window so we follow THIS pair and not thermally nucleated background vortices --
designer's trap c), and record the lifetime = steps until the pair annihilates
(separation -> 0) or its cores are lost. At T=0 the pair survives the window
(the DAMPED reference -- damping-driven annihilation is slower than the cap; the
truly bound pair is the conservative Stage-1 one); raising T shortens the
lifetime monotonically = thermal dissociation.

MEASURED: lifetime decreases with T (T up -> lifetime down). The Arrhenius form
tau ~ exp(dE/T) is reported as a fit but kept interpretive -- low-T runs are
right-censored at the observation cap, and high T invites background-vortex
proliferation (BKT), so the clean window is intermediate T. These are stated
floors, not hidden.

Pitfalls avoided: (a) phase-only t=0 has no density notch -> settle first;
(b/c) thermal sound/vortices are rejected by continuity tracking in a tight
window; (d) the death test is "THIS pair annihilated/lost", not a global count.

MODULE:   e011_defect_chemistry (Stage 2: finite-T dissociation)
QUESTION: Does temperature dissociate a bound +/- pair, with lifetime falling as T rises?
PUT IN:   stochastic GPE (Langevin, sqrt(2 gamma T) dW) + one imprinted +/- pair. No decay rate is put in.
EMERGED:  (measured) lifetime decreases monotonically with T; bound at T=0, dissociates when heated.
CLAIM TIER: measured(lifetime vs T monotone down) ; interpretive(Arrhenius/thermal activation).
KNOWN MATCH: thermal/Arrhenius activation; BKT vortex unbinding at high T.
STATUS:   GREEN (lifetime falls with T = measured); Arrhenius fit interpretive (censoring/BKT floors).
A_OR_B:   (A) faithful. Hand input = stochastic GPE + bound pair; the bath is the only addition vs Stage 1.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402

DEFAULT = {"L": 96, "g": 1.0, "mu": 1.0, "dt": 0.02, "gamma": 0.5, "d": 12,
           "cap": 2500, "chunk": 20, "merge_sep": 4.0,
           "T_list": [0.0, 0.15, 0.3, 0.45, 0.6], "seeds": [1, 2, 3, 4, 5, 6, 7, 8]}
QUICK = {"L": 64, "d": 10, "cap": 1500, "T_list": [0.0, 0.3, 0.6],
         "seeds": [1, 2, 3, 4, 5, 6]}


def _make_pair(L, mu, d):
    c = L / 2.0
    ph = (field.vortex_phase(L, +1, (c, c - d / 2.0))
          + field.vortex_phase(L, -1, (c, c + d / 2.0)))
    return np.sqrt(mu) * np.exp(1j * ph)


def pair_lifetime(p, T, seed):
    """Steps until the tracked +/- pair annihilates or is lost (capped)."""
    L, g, mu, dt, gamma, d = (p["L"], p["g"], p["mu"], p["dt"], p["gamma"], p["d"])
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = _make_pair(L, mu, d)
    for _ in range(20):                          # settle (form density notches)
        psi = field.step_real(psi, V, k2, g, mu, dt)
    pos = [(L / 2.0, L / 2.0 - d / 2.0), (L / 2.0, L / 2.0 + d / 2.0)]
    win = int(d)
    cores = vortex.track_two_vortices(psi, pos, (+1, -1), window=win)
    if any(c is None for c in cores):
        return 0
    pos = [(c["x"], c["y"]) for c in cores]
    for step in range(0, p["cap"], p["chunk"]):
        for _ in range(p["chunk"]):
            psi = field.step_sgpe_2d(psi, V, k2, g, mu, dt, gamma, T, rng)
        cores = vortex.track_two_vortices(psi, pos, (+1, -1), window=win)
        if any(c is None for c in cores):
            return step + p["chunk"]
        q = [(c["x"], c["y"]) for c in cores]
        if np.hypot(q[0][0] - q[1][0], q[0][1] - q[1][1]) < p["merge_sep"]:
            return step + p["chunk"]
        pos = q
    return p["cap"]


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for T in p["T_list"]:
        lts = [pair_lifetime(p, T, sd) for sd in p["seeds"]]
        rows.append({"T": T, "mean_lifetime": round(float(np.mean(lts)), 1),
                     "median": float(np.median(lts)),
                     "min": int(min(lts)), "max": int(max(lts)),
                     "n_annihilated": int(sum(1 for x in lts if x < p["cap"]))})
    Ts = np.array([r["T"] for r in rows], float)
    life = np.array([r["mean_lifetime"] for r in rows], float)
    slope = float(np.polyfit(Ts, life, 1)[0])     # lifetime vs T (should be < 0)
    # Arrhenius (interpretive): ln(lifetime) vs 1/T over T>0 (censoring floor)
    pos = Ts > 0
    arr = None
    if pos.sum() >= 2:
        dE = float(np.polyfit(1.0 / Ts[pos], np.log(life[pos]), 1)[0])
        arr = round(dE, 4)
    return {"params": p, "rows": rows,
            "lifetime_vs_T_slope": round(slope, 2),
            "lifetime_drop_frac": round(float(1.0 - life[-1] / life[0]), 3),
            "monotone_decreasing": bool(all(life[i] >= life[i + 1] - 1e-9
                                            for i in range(len(life) - 1))),
            "arrhenius_dE": arr}


def evaluate(result, quick=False):
    checks = {
        "lifetime_falls_with_T(slope<0)": result["lifetime_vs_T_slope"] < 0,
        "clear_drop(>=12%)": result["lifetime_drop_frac"] >= 0.12,
        "monotone_decreasing": result["monotone_decreasing"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e011 finite-T dissociation", "tier": "measured",
        "put_in": "stochastic GPE (Langevin bath sqrt(2 gamma T) dW) + one bound +/- pair",
        "emerged": ["the bound pair DISSOCIATES when heated; lifetime falls with T",
                    "lifetime drop %.0f%% from T=0 to T=%.2f"
                    % (100 * result["lifetime_drop_frac"], result["params"]["T_list"][-1])],
        "surprises": ["a thermal bath alone converts a stable bound pair into a decaying one"],
        "persistence": "T=0 survives the window (damped reference); finite T -> finite lifetime",
        "measured_numbers": {"rows": result["rows"],
                             "lifetime_vs_T_slope": result["lifetime_vs_T_slope"],
                             "arrhenius_dE": result["arrhenius_dE"]},
        "not_scripted_check": "lifetime from continuity-tracked THIS pair; no decay rate is put in",
        "claim_tier": "measured (lifetime vs T monotone down) ; interpretive (Arrhenius/thermal activation)",
        "floors": ["low-T lifetimes right-censored at the observation cap",
                   "high T invites BKT background-vortex proliferation -> stay at intermediate T",
                   "gamma>0 means even T=0 eventually decays (conservative pair is the bound reference)"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e011 finite-T dissociation")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e011 finite-T dissociation of a bound +/- pair (stochastic GPE) ===")
    for row in r["rows"]:
        print("  T=%.2f: mean lifetime=%6.1f  (median=%.0f, %d/%d annihilated)"
              % (row["T"], row["mean_lifetime"], row["median"],
                 row["n_annihilated"], len(r["params"]["seeds"])))
    print("  lifetime vs T slope = %.2f (<0 = thermal dissociation); drop = %.0f%%; Arrhenius dE = %s"
          % (r["lifetime_vs_T_slope"], 100 * r["lifetime_drop_frac"], r["arrhenius_dE"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (lifetime falls with T = thermal dissociation, measured)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "finite_T.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/finite_T.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
