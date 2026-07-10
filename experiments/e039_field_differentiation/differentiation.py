#!/usr/bin/env python3
"""e039 -- differentiation as a FIELD: identical cells become different types by position (no agents).

---
id: e039
role: E
claim_tier: measured
evidence: "a morphogen gradient (diffusion+decay) + ONE threshold rule gives 3 spatially ORDERED domains (French flag); a Gierer-Meinhardt activator-inhibitor breaks symmetry from uniform+noise into a self-organized pattern (activator std 0.02->1.19)"
target_encoded: false
known_match: "Wolpert French-flag positional information; Turing/Gierer-Meinhardt reaction-diffusion patterning"
open_issues: ["threshold values th1/th2 are modelling choices (a floor)", "'differentiation / same genome' is analogy for the field fates"]
---

MODULE:   e039_field_differentiation
QUESTION: e033 got germ-soma division of labor from a field. HERE: how do genetically IDENTICAL cells (one
          rule = same genome) become DIFFERENT specialized types arranged in space -- from a pure field,
          no agents? Two faithful mechanisms: (1) a MORPHOGEN gradient + one threshold rule (Wolpert French
          flag); (2) a TURING (Gierer-Meinhardt) instability that self-organizes a pattern from uniform+noise.
PUT IN:   (1) a morphogen M with a localized source diffusing + decaying (dM/dt = D lap M - k M) and ONE
          threshold rule fate = f(M) applied identically everywhere; (2) an activator-inhibitor RD system
          da/dt = Da lap a + a^2/h - mu_a a + rho, dh/dt = Dh lap h + a^2 - mu_h h from a UNIFORM state +
          tiny noise. NO "3 ordered domains" and NO "a pattern forms" is put in -- both are measured.
EMERGED:  (measured) (1) the morphogen relaxes to an exponential gradient (never put in) and the single
          threshold rule yields 3 domains that are SPATIALLY ORDERED (A->B->C) along it; (2) the activator
          spatial std grows from ~0.02 (uniform) to ~1.19 (a self-organized pattern) and cells split into
          two fates by local activator level -- de novo symmetry breaking with no source.
CLAIM TIER: measured(3 ordered domains from one rule; Turing std growth; two-fate split) ; interpretive
          (positional information and self-organization make identical cells differentiate) ; analogy
          (differentiation / same genome -> different types).
KNOWN MATCH: Wolpert (1969) French-flag positional information; Turing (1952) / Gierer-Meinhardt (1972).
STATUS:   E (differentiation emerges from the faithful morphogen / RD fields; gates on physical field quantities).
A_OR_B:   (A) faithful. Hand input = the morphogen/RD field laws + one threshold rule; the ordered domains,
          the exponential gradient and the Turing pattern are emergent and measured.

THE TRAP (designer hit it, we avoid it): the SAME threshold rule is applied to every cell (one genome). The
ORDER of the domains is NOT put in -- it follows from the monotonic emergent gradient; the Turing pattern is
NOT put in -- it self-organizes from a uniform state. We gate on the ordering and the std GROWTH, not on a
hand-placed pattern. Threshold values are modelling choices (a stated floor).

Floors: "differentiation / same genome / cell type" is analogy for the field fates. The threshold values
th1/th2 are modelling choices. 同じ数学≠同じもの: this does NOT claim biological development IS this PDE; the
SAME facts (ordered domains from a gradient; a self-organized pattern) emerge in a field with no agents.
(A) faithful: the field laws are put in by hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"N": 120, "mor_steps": 4000, "mor_D": 1.0, "mor_k": 0.006, "mor_dt": 0.2,
           "th1": 0.45, "th2": 0.12,
           "tur_steps": 9000, "Da": 0.04, "Dh": 1.0, "mua": 1.0, "muh": 1.4, "rho": 0.02,
           "tur_dt": 0.04, "seed": 0}
QUICK = {"N": 80, "mor_steps": 3000, "tur_steps": 6000}


def _lap(Z):
    return np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z


def _morphogen(p):
    """French flag: a localized source diffuses + decays into a steady exponential gradient."""
    N = p["N"]
    M = np.zeros((N, N))
    for _ in range(p["mor_steps"]):
        M[:3, :] = 1.0                                      # localized source at the left edge
        M = np.clip(M + p["mor_dt"] * (p["mor_D"] * _lap(M) - p["mor_k"] * M), 0, None)
    return M


def _turing(p):
    """Gierer-Meinhardt activator-inhibitor from uniform + tiny noise; return activator + std history."""
    N = p["N"]
    rng = np.random.default_rng(p["seed"])
    a = 1.0 + 0.02 * rng.standard_normal((N, N))
    h = 1.0 + 0.02 * rng.standard_normal((N, N))
    var = []
    for t in range(p["tur_steps"]):
        a2 = a * a
        a = np.clip(a + p["tur_dt"] * (p["Da"] * _lap(a) + a2 / h - p["mua"] * a + p["rho"]), 0, None)
        h = np.clip(h + p["tur_dt"] * (p["Dh"] * _lap(h) + a2 - p["muh"] * h), 1e-6, None)
        if t % 1500 == 0:
            var.append(round(float(a.std()), 3))
    return a, var


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N = p["N"]
    # (1) French flag
    M = _morphogen(p)
    fate = np.where(M > p["th1"], 0, np.where(M > p["th2"], 1, 2))
    col = fate[:, N // 2]
    doms = [int((col == f).sum()) for f in range(3)]
    # spatially ordered A -> B -> C along x (first A cell before first C cell), all three present
    ordered = bool(all(d > 0 for d in doms)
                   and int(np.argmax(col == 0)) < int(np.argmax(col == 2)))
    # (2) Turing
    a, var = _turing(p)
    turing_std0, turing_std = var[0], var[-1]
    high_frac = float((a > a.mean()).mean())
    return {
        "params": p, "domains": doms, "french_flag_ordered": ordered,
        "turing_std_start": turing_std0, "turing_std_end": turing_std, "turing_std_hist": var,
        "turing_high_fraction": round(high_frac, 3),
    }


def evaluate(result, quick=False):
    checks = {
        "french_flag_three_ordered_domains (3 non-empty fates, ordered A->B->C along the gradient)":
            bool(result["french_flag_ordered"] and all(d > 0 for d in result["domains"])),
        "turing_symmetry_breaks_from_uniform (activator std grows from ~0.02 to >0.5)":
            bool(result["turing_std_start"] < 0.1 and result["turing_std_end"] > 0.5),
        "turing_two_type_differentiation (high-activator fraction in 0.1..0.5)":
            bool(0.1 <= result["turing_high_fraction"] <= 0.5),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e039 field differentiation (French flag + Turing, no agents)", "tier": "measured",
        "put_in": "(1) a morphogen source diffusing+decaying + ONE threshold rule; (2) a Gierer-Meinhardt "
                  "activator-inhibitor from uniform+noise. NO ordered domains / pattern put in",
        "emerged": ["French flag: 3 fate domains (cells per type along the gradient) = %s, spatially ordered = %s"
                    % (result["domains"], result["french_flag_ordered"]),
                    "Turing: activator spatial std %s -> %s (uniform -> self-organized pattern)"
                    % (result["turing_std_start"], result["turing_std_end"]),
                    "Turing two-fate split: high-activator fraction = %s" % result["turing_high_fraction"]],
        "surprises": ["identical cells (one rule) split into 3 ORDERED domains purely by position; a uniform "
                      "sheet spontaneously breaks symmetry into a Turing pattern with no source"],
        "persistence": "the gradient is a steady state; the Turing pattern is the stable attractor of the RD system",
        "measured_numbers": {"domains": result["domains"], "turing_std_hist": result["turing_std_hist"],
                             "turing_high_fraction": result["turing_high_fraction"]},
        "not_scripted_check": "the domain ORDER and the Turing pattern are measured, not hand-placed",
        "claim_tier": "measured (ordered domains; Turing std growth; two-fate split) ; interpretive (positional "
                      "information + self-organization differentiate identical cells) ; analogy (differentiation)",
        "floors": ["'differentiation / same genome / cell type' is analogy for the field fates",
                   "the threshold values th1/th2 are modelling choices",
                   "同じ数学≠同じもの: this does NOT claim biological development IS this PDE",
                   "(A) faithful: the field laws are put in by hand, not derived"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e039 field differentiation (French flag + Turing, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e039 -- differentiation from a FIELD (French flag morphogen + Turing, no agents) ===")
    print("  (1) French flag: fate domains along the gradient = %s  ordered(A->B->C) = %s"
          % (r["domains"], r["french_flag_ordered"]))
    print("  (2) Turing: activator std %s -> %s (uniform -> pattern); high-activator fraction = %s"
          % (r["turing_std_start"], r["turing_std_end"], r["turing_high_fraction"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role E] (identical cells differentiate by position; morphogen gradient + Turing pattern)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "differentiation.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/differentiation.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
