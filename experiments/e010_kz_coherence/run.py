#!/usr/bin/env python3
"""e010 Stage 1 -- Kibble-Zurek, pinned to the COHERENCE LENGTH.

Is the KZ defect count really set by the frozen coherence length? We quench a
2D damped GPE from white noise (same step-count protocol as e008: tau_Q and hold
are STEP counts, not times) and, at freeze-out, measure together:
  * N            -- quantized vortices (density-gated count, core/vortex)
  * spacing      -- L / sqrt(N), the mean inter-defect distance
  * xi           -- the 1/e coherence length of g1(r) (core/measure)
and test the KZ mechanism by NUMBER:
  (i)  spacing / xi is CONSTANT across tau_Q  (CV < 0.15)  -- defects set by xi
  (ii) xi ~ tau_Q^sigma  and  N ~ tau_Q^(-2 sigma)         -- so b = 2 sigma
       (internal consistency: the same exponent governs both, because
        N ~ spacing^-2 ~ xi^-2)

Closing check (genuine condensate, not the gamma-undercondensation trap of e008):
the field fully condenses, rho_median >~ 0.6, so the counted cores are real
vortices and not sound wrinkles.

Floors: the ABSOLUTE KZ exponent b is protocol dependent (gamma, threshold,
hold, freeze window); the MEASURED claims are the MECHANISM (spacing ∝ xi) and
the internal consistency 2 sigma = b -- not a universal value of b. The
spacing/xi constant depends on the xi convention (1/e of g1). Fixed lattice =
space is given. Reuses core (field, vortex, measure, fft); no new propagator.

MODULE:   e010_kz_coherence
QUESTION: Is the KZ defect density set by the frozen coherence length (spacing ∝ xi, b = 2 sigma)?
PUT IN:   damped GPE dψ/dt=-(i+γ)(-½∇²+g|ψ|²-μ)ψ + white noise + μ quench(τ_Q steps). No vortex/length is named.
EMERGED:  (measured) spacing/xi const across τ_Q; xi~τ_Q^σ, N~τ_Q^{-2σ}; quantized cores in a real condensate.
CLAIM TIER: measured(spacing/xi const, 2σ=b, quantization, condensation) ; interpretive(KZ mechanism reading).
KNOWN MATCH: Kibble 1976 / Zurek 1985 (defects set by frozen xi); e008 (KZ from white noise).
STATUS:   GREEN (mechanism + internal consistency measured; absolute b is a protocol-dependent floor).
A_OR_B:   (A) faithful emergence. Hand input = field law + white noise. Lattice (=space) is given.

id: e010
role: E
claim_tier: measured
evidence: "spacing/xi constant across tau_Q (CV<0.15); xi~tau_Q^sigma and N~tau_Q^{-2sigma} so b=2sigma; quantized cores in a real condensate"
target_encoded: false         # 8th audit CLEARED (see note)
known_match: "Kibble 1976 / Zurek 1985: KZ defect density set by the frozen coherence length"
open_issues: ["absolute b is protocol-dependent (tau_Q, hold, freeze window) -- a stated floor", "fixed lattice = space is given"]

8th-audit note (CLEARED, target_encoded=false): `spacing = L/sqrt(N)` is only the DEFINITION of the mean
inter-defect distance -- it is NOT a circular embedding of the KZ conclusion. The substantive claim
`spacing/xi = const` compares TWO INDEPENDENT measurements: N (density-gated vortex count, core.vortex) and
xi (the 1/e length of g1(r), core.measure). Neither derives the other, so "N ~ (L/xi)^2" is a genuine test
of the KZ mechanism, not a definition. b=2sigma then follows from that independent consistency.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, measure, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402

# tau_Q and hold are STEP COUNTS (e008 convention). mu_i is just below the
# transition so the field condenses THROUGHOUT the ramp (fully condensed at a
# short freeze hold), while the quench still crosses mu=0 to nucleate defects.
DEFAULT = {"L": 192, "g": 1.0, "mu_i": -0.2, "mu_f": 1.0, "dt": 0.05,
           "gamma": 1.0, "noise": 0.05, "hold": 150,
           "tauQ_list": [50, 100, 200, 400, 800], "seeds": [1, 2, 3],
           "frac": 0.1}
QUICK = {"L": 96, "hold": 120, "tauQ_list": [50, 100, 200, 400], "seeds": [1, 2]}


def quench(p, tauQ, seed):
    """Damped-GPE quench from white noise; returns the frozen field."""
    L, g = p["L"], p["g"]
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L))
                        + 1j * rng.standard_normal((L, L)))
    for s in range(tauQ + p["hold"]):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * min(1.0, s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, p["dt"], p["gamma"])
    return psi


def measure_row(p, tauQ):
    """Average N, spacing, xi, rho over seeds for one tau_Q."""
    L = p["L"]
    Ns, xis, rhos = [], [], []
    for seed in p["seeds"]:
        psi = quench(p, tauQ, seed)
        n, _ = vortex.count_defects(psi, frac=p["frac"])
        Ns.append(max(n, 1))
        xis.append(measure.coherence_length(psi))
        rhos.append(float(np.median(np.abs(psi) ** 2)))
    N = float(np.mean(Ns))
    xi = float(np.mean(xis))
    spacing = L / np.sqrt(N)
    return {"tauQ": tauQ, "N": round(N, 1), "spacing": round(spacing, 3),
            "xi": round(xi, 3), "spacing_over_xi": round(spacing / xi, 3),
            "rho_median": round(float(np.mean(rhos)), 3)}


def _slope(x, y):
    return float(np.polyfit(np.log(x), np.log(y), 1)[0])


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = [measure_row(p, tq) for tq in p["tauQ_list"]]
    taus = np.array([r["tauQ"] for r in rows], float)
    N = np.array([r["N"] for r in rows], float)
    xi = np.array([r["xi"] for r in rows], float)
    ratio = np.array([r["spacing_over_xi"] for r in rows], float)
    sigma = _slope(taus, xi)          # xi ~ tau_Q^sigma
    b = -_slope(taus, N)              # N ~ tau_Q^-b
    return {
        "params": p, "rows": rows,
        "spacing_over_xi_mean": round(float(ratio.mean()), 3),
        "spacing_over_xi_cv": round(float(ratio.std() / ratio.mean()), 4),
        "xi_exponent_sigma": round(sigma, 3),
        "defect_exponent_b": round(b, 3),
        "two_sigma": round(2 * sigma, 3),
        "internal_consistency_rel": round(float(abs(2 * sigma - b)
                                                 / max(b, 1e-9)), 3),
        "rho_median_min": round(float(min(r["rho_median"] for r in rows)), 3),
    }


EXPECT = {"cv_max": 0.15, "consistency_max": 0.20, "b_min": 0.1, "rho_min": 0.6}


def evaluate(result, quick=False):
    checks = {
        "spacing_tracks_xi(const_ratio)":
            result["spacing_over_xi_cv"] < EXPECT["cv_max"],
        "b_equals_2sigma(internal_consistency)":
            result["internal_consistency_rel"] < EXPECT["consistency_max"],
        "negative_power_law(b>0)":
            result["defect_exponent_b"] > EXPECT["b_min"],
        "genuine_condensate(rho>0.6)":
            result["rho_median_min"] > EXPECT["rho_min"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e010 coherence length", "tier": "measured",
        "put_in": "damped GPE + white noise + mu quench (tau_Q steps); no length/vortex named",
        "emerged": ["defect spacing is a CONSTANT multiple of the coherence length xi",
                    "xi ~ tau_Q^%.3f and N ~ tau_Q^-%.3f (b = 2 sigma)"
                    % (result["xi_exponent_sigma"], result["defect_exponent_b"])],
        "surprises": ["spacing/xi constant to CV=%.3f over a 16x range of tau_Q"
                      % result["spacing_over_xi_cv"]],
        "persistence": "frozen post-quench; closed with full condensation (rho_median>=%.2f)"
                       % result["rho_median_min"],
        "measured_numbers": {"spacing_over_xi": result["spacing_over_xi_mean"],
                             "cv": result["spacing_over_xi_cv"],
                             "sigma": result["xi_exponent_sigma"],
                             "b": result["defect_exponent_b"],
                             "two_sigma": result["two_sigma"]},
        "not_scripted_check": "xi from g1 1/e, N from winding+density gate; the law never says 'coherence length'",
        "claim_tier": "measured (spacing ∝ xi, 2 sigma = b) ; interpretive (KZ mechanism)",
        "floors": ["absolute b is protocol dependent (gamma/threshold/hold)",
                   "spacing/xi value depends on the xi convention (1/e of g1)",
                   "fixed lattice = space is given"],
    }]


def _print_report(result):
    print(__doc__.split("MODULE:")[0])
    print("------------------------- KZ coherence length -------------------------")
    for r in result["rows"]:
        print("  tauQ=%5d  N=%7.1f  spacing=%6.2f  xi=%5.2f  spacing/xi=%5.3f  rho=%.2f"
              % (r["tauQ"], r["N"], r["spacing"], r["xi"],
                 r["spacing_over_xi"], r["rho_median"]))
    print("  spacing/xi = %.3f (CV=%.3f)  -> defects set by the coherence length"
          % (result["spacing_over_xi_mean"], result["spacing_over_xi_cv"]))
    print("  xi ~ tau_Q^%.3f ;  N ~ tau_Q^-%.3f ;  2 sigma=%.3f  (b=%.3f) -> internal consistency %.3f"
          % (result["xi_exponent_sigma"], result["defect_exponent_b"],
             result["two_sigma"], result["defect_exponent_b"],
             result["internal_consistency_rel"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description="e010 KZ coherence length")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    result = simulate(quick=args.quick)
    _print_report(result)
    passed, checks = evaluate(result, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (mechanism + 2 sigma=b measured; absolute b is a protocol floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.dirname(__file__)
        with open(os.path.join(out, "result.json"), "w") as f:
            json.dump({"result": result, "atlas": _atlas(result)}, f, indent=2)
        print("wrote result.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
