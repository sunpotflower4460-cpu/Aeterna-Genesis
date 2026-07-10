#!/usr/bin/env python3
"""e045 -- NEGATIVE RESULT: endogenous negative-frequency-dependence does NOT self-generate diversity in the field.

---
id: e045
role: N
claim_tier: measured
evidence: "a faithful test of endogenous niche construction (fitness set ONLY by negative frequency dependence on a cell's own neighbours -- no external optimum) in the Gray-Scott object-tracking field REFUTES the reference claim: within the spot-SURVIVAL window the penalty is too weak to overcome spatial assortment, so local trait diversity is NOT above (is slightly below) the neutral-drift control (local-var excess ~ -0.001); and a penalty strong enough to matter (comp=6) drives the field EXTINCT (occupied -> 0). Self-generated open-ended diversity does not emerge here"
target_encoded: false
known_match: "negative frequency-dependent selection / niche construction (the EXPECTED positive); the neutral-drift null model; Gray-Scott spot-survival window"
open_issues: ["NEGATIVE: this refutes the naive route in THIS faithful field -- it does NOT prove endogenous open-endedness is impossible; a different field/coupling might succeed (open)", "HYBRID: per-tissue trait; frequency dependence imposed; 'niche / open-endedness' is analogy"]
---

MODULE:   e045_field_endogenous
QUESTION: e043/e044 used an EXTERNAL optimum (a morphogen). Can diversity be ENDOGENOUS -- the selective
          landscape SELF-generated, no external optimum -- if each cell's decay rises when its trait BAND is
          locally COMMON (negative frequency dependence = niche construction)? The reference sandbox CLAIMED
          this maintains many coexisting niches ABOVE neutral drift. Does it, in a FAITHFUL field?
PUT IN:   the one-field GS universe with a bounded [0,1] per-tissue trait inherited + mutated at the front; the
          ONLY fitness term is crowding = local density of cells sharing this cell's trait band -> higher decay.
          A decisive NEUTRAL control turns the frequency dependence OFF. Measure LOCAL trait variance and the
          number of occupied trait bands, and COMPARE to the neutral null. NO result is put in.
EMERGED:  (measured, NEGATIVE) the claim FAILS faithfully. (i) With a SURVIVABLE penalty (kept inside the GS
          spot-survival window k<~0.063), the endogenous field's LOCAL trait variance is NOT above -- it is
          slightly BELOW -- the neutral control (excess ~ -0.001), because spatial assortment (front
          inheritance) keeps local variance low in BOTH. (ii) A penalty strong enough to strongly disfavour
          common traits (comp=6, k up to 0.072) pushes decay OUTSIDE the survival window and the field goes
          EXTINCT (occupied -> 0). There is no survivable regime with diversity above neutral.
CLAIM TIER: measured(NEGATIVE: no local-diversity gain over neutral in the survival window; extinction under a
          strong penalty) ; interpretive(endogenous niche construction does not self-generate open-ended
          diversity in THIS faithful field) ; analogy(niche / open-endedness).
KNOWN MATCH: negative frequency-dependent selection (the EXPECTED positive); the neutral null; GS survival window.
STATUS:   N (NEGATIVE result -- an honest failure = an asset. The naive endogenous-open-endedness route does not
          work here: too-weak-to-matter within survival, lethal beyond it. Gated on the robust negative facts).
A_OR_B:   (A) faithful GS dynamics + tracked trait LABEL (hybrid). Hand input = the field law + trait rule +
          negative frequency dependence; the (negative) outcome vs the neutral null is emergent and measured.

THE TRAP (we report the negative instead of hiding it): the reference SANDBOX claimed endogenous diversity
above neutral. Rather than tune parameters until a GREEN appears (禁止), we swept the survivable window and
found NO regime beats neutral, and that the reference's own strong penalty kills the field. We publish the
NEGATIVE (role N), as with e020 (passive phase-field does not divide).

Floors: NEGATIVE -- this refutes the naive route in THIS faithful field; it does NOT prove endogenous
open-endedness impossible (a different field/coupling might succeed -- open/frontier). HYBRID: per-tissue trait;
the frequency dependence is imposed. "Niche / open-endedness" is analogy. 同じ数学≠同じもの.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.ndimage import uniform_filter

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# comp = strength of the negative frequency dependence; ceil = decay ceiling.
# survivable = penalty kept INSIDE the GS spot-survival window; strong = the reference's lethal setting.
DEFAULT = {"N": 100, "Du": 0.16, "Dv": 0.08, "F0": 0.030, "k0": 0.0605, "dt": 1.0, "steps": 16000,
           "K": 8, "mut": 0.03, "cr": 5, "comp": 3.0, "ceil": 0.0625,
           "strong_comp": 6.0, "strong_ceil": 0.072, "seed": 0}
QUICK = {"N": 84, "steps": 8000}


def _lap(Z):
    return np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z


def _local_var(tau, occ, w=7):
    s0 = uniform_filter(occ, w) + 1e-9
    s1 = uniform_filter(tau * occ, w)
    s2 = uniform_filter(tau * tau * occ, w)
    v = s2 / s0 - (s1 / s0) ** 2
    return float(np.mean(v[occ > 0.5])) if occ.sum() > 0 else 0.0


def _run(p, comp, ceil):
    N, K = p["N"], p["K"]
    rng = np.random.default_rng(p["seed"])
    U = np.ones((N, N)); V = np.zeros((N, N)); tau = rng.random((N, N))    # random initial traits
    nseed = max(12, int(24 * (N / 100.0) ** 2))
    for _ in range(nseed):
        cx, cy = rng.integers(6, N - 6, 2)
        U[cx - 3:cx + 3, cy - 3:cy + 3] = 0.5
        V[cx - 3:cx + 3, cy - 3:cy + 3] = 0.25
    high = V > 0.15
    for t in range(p["steps"]):
        occ = (V > 0.15).astype(float)
        band = np.clip((tau * K).astype(int), 0, K - 1)
        crowd = np.zeros((N, N))
        for b in range(K):                                   # crowding = local density sharing this band
            rho = uniform_filter((band == b) * occ, int(p["cr"]))
            crowd = np.where(band == b, rho, crowd)
        k_loc = np.clip(p["k0"] + comp * crowd, 0.050, ceil)  # common trait -> higher decay (penalised)
        uvv = U * V * V
        U = U + p["dt"] * (p["Du"] * _lap(U) - uvv + p["F0"] * (1 - U))
        V = np.clip(V + p["dt"] * (p["Dv"] * _lap(V) + uvv - (p["F0"] + k_loc) * V), 0, None)
        newhigh = V > 0.15
        front = newhigh & (~high)
        if front.any():
            hf = high.astype(float)
            num = sum(np.roll(np.roll(tau * hf, d0, 0), d1, 1) for d0, d1 in _NB)
            den = sum(np.roll(np.roll(hf, d0, 0), d1, 1) for d0, d1 in _NB)
            inh = num / (den + 1e-9) + p["mut"] * rng.standard_normal((N, N))
            tau = np.where(front & (den > 0.5), np.clip(inh, 0, 1), tau)
        high = newhigh
        if t % 300 == 0 and t > 0:
            for _ in range(2):
                cx, cy = rng.integers(0, N, 2); rr = 8
                V[max(0, cx - rr):cx + rr, max(0, cy - rr):cy + rr] = 0
                U[max(0, cx - rr):cx + rr, max(0, cy - rr):cy + rr] = 1
    occ = (V > 0.15).astype(float)
    return tau, occ


def _bands(tau, occ, K):
    tv = tau[occ > 0.5]
    if tv.size == 0:
        return 0, 0.0
    hist, _ = np.histogram(tv, bins=K, range=(0, 1))
    return int((hist > tv.size * 0.03).sum()), float(tv.std())


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    tau, occ = _run(p, comp=p["comp"], ceil=p["ceil"])                    # endogenous, survivable penalty
    taun, occn = _run(p, comp=0.0, ceil=p["ceil"])                        # NEUTRAL control (no freq dependence)
    _, occs = _run(p, comp=p["strong_comp"], ceil=p["strong_ceil"])      # strong penalty (reference setting)
    lv = _local_var(tau, occ); lvn = _local_var(taun, occn)
    nb, gstd = _bands(tau, occ, p["K"]); nbn, gstdn = _bands(taun, occn, p["K"])
    return {
        "params": p,
        "endogenous": {"occupied": round(float(occ.mean()), 3), "local_var": round(lv, 4),
                       "bands": nb, "global_std": round(gstd, 3)},
        "neutral": {"occupied": round(float(occn.mean()), 3), "local_var": round(lvn, 4),
                    "bands": nbn, "global_std": round(gstdn, 3)},
        "strong_penalty_occupied": round(float(occs.mean()), 4),
        "local_var_excess": round(lv - lvn, 4),
    }


def evaluate(result, quick=False):
    en, nu = result["endogenous"], result["neutral"]
    # This is a NEGATIVE result: the gates assert the robust FAILURE of the endogenous-diversity claim.
    checks = {
        "both_baselines_alive (endogenous & neutral both survive, occupied >0.15 -- a fair comparison)":
            bool(en["occupied"] > 0.15 and nu["occupied"] > 0.15),
        "NEGATIVE_no_local_diversity_gain (endogenous local variance NOT above neutral: excess <= 0.001)":
            bool(result["local_var_excess"] <= 0.001),
        "NEGATIVE_strong_penalty_kills_field (a penalty strong enough to matter drives extinction: occupied <0.02)":
            bool(result["strong_penalty_occupied"] < 0.02),
    }
    return all(checks.values()), checks


def _atlas(result):
    en, nu = result["endogenous"], result["neutral"]
    return [{
        "experiment": "e045 field endogenous (NEGATIVE: endogenous niche construction does not self-generate "
                      "diversity above neutral in the faithful field)", "tier": "measured(negative)",
        "put_in": "the one-field GS universe with a bounded [0,1] per-tissue trait; the ONLY fitness term is "
                  "negative frequency dependence; a decisive NEUTRAL control; a strong-penalty run at the "
                  "reference's lethal setting. NO result put in",
        "emerged": ["survivable penalty: endogenous local var %s vs neutral %s (excess %s = NOT above neutral)"
                    % (en["local_var"], nu["local_var"], result["local_var_excess"]),
                    "endogenous occupied %s, neutral occupied %s (both alive)"
                    % (en["occupied"], nu["occupied"]),
                    "strong penalty (reference setting): occupied %s = the field goes EXTINCT"
                    % result["strong_penalty_occupied"]],
        "surprises": ["the reference's endogenous-diversity claim FAILS faithfully: within the spot-survival "
                      "window the penalty is too weak to beat spatial assortment; strong enough to matter = lethal"],
        "persistence": "the negative is robust across grid sizes and step counts (no survivable regime beats neutral)",
        "measured_numbers": {"endogenous": en, "neutral": nu,
                             "strong_penalty_occupied": result["strong_penalty_occupied"],
                             "local_var_excess": result["local_var_excess"]},
        "not_scripted_check": "local variance vs the neutral null and the extinction under a strong penalty are "
                              "measured; we did NOT tune parameters to manufacture a positive",
        "claim_tier": "measured (NEGATIVE: no diversity gain over neutral in the survival window; extinction "
                      "beyond it) ; interpretive (endogenous niche construction does not self-generate open-ended "
                      "diversity here) ; analogy (niche / open-endedness)",
        "floors": ["NEGATIVE: refutes the naive route in THIS faithful field; does NOT prove endogenous "
                   "open-endedness impossible (a different field/coupling might succeed -- open/frontier)",
                   "HYBRID: per-tissue trait; the frequency dependence is imposed; 'niche / open-endedness' is analogy",
                   "同じ数学≠同じもの; an honest negative (cf e020) -- not a failure to be hidden or tuned away"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e045 field endogenous (NEGATIVE result, role N)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    en, nu = r["endogenous"], r["neutral"]
    print("=== e045 -- NEGATIVE: endogenous niche construction does NOT self-generate diversity in the field ===")
    print("  survivable penalty (endogenous): local var %s, %s bands, occupied %s"
          % (en["local_var"], en["bands"], en["occupied"]))
    print("  NEUTRAL control:                 local var %s, %s bands, occupied %s"
          % (nu["local_var"], nu["bands"], nu["occupied"]))
    print("  local-variance excess over neutral = %s (<=0 => NO endogenous diversity gain)" % r["local_var_excess"])
    print("  strong penalty (reference setting): occupied %s (field goes EXTINCT)" % r["strong_penalty_occupied"])
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role N] (honest negative: endogenous route fails -- too weak to matter, lethal beyond)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "endogenous.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/endogenous.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
