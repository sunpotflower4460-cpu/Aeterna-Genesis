#!/usr/bin/env python3
"""e035 -- the Red Queen WITHOUT agents: endogenous sustained change from a Hopf bifurcation.

MODULE:   e035_field_red_queen
QUESTION: e029 Stage 1 got "a static parasite plateaus the host; coevolving parasites make the demand rise
          ENDOGENOUSLY (no external knob)" from an AGENT host-parasite model (Wright-Fisher) -- a floor
          (LAW.md: not a field). Does ENDOGENOUS sustained change emerge from a REAL POPULATION FIELD with
          no agents, no genomes, no selection sampling?
PUT IN:   the Rosenzweig-MacArthur predator-prey equations (Holling type II) for continuous host/parasite
          densities H,P (the mean-field / continuum limit of the birth-death process):
            dH/dt = r H (1 - H/K) - c H P/(H+H0);   dP/dt = e c H P/(H+H0) - m P.
          The only knob is the enrichment K (how far the host can grow = how far the arms race can escalate).
          NO "plateau", NO "sustained oscillation", NO threshold is put in -- all are measured.
EMERGED:  (measured) below a critical enrichment K_c the coexistence fixed point is stable, so a perturbation
          DECAYS and the system PLATEAUS (static, non-escalating -- the analog of the static-parasite plateau);
          above K_c a stable LIMIT CYCLE is born (a Hopf bifurcation) -> ENDOGENOUS sustained oscillation with
          NO external forcing (the field Red Queen: perpetual change from within). The onset K_c matches the
          analytic Hopf point (Jacobian trace = 0); host and parasite oscillate out of phase (the chase).
CLAIM TIER: measured(plateau below K_c; sustained oscillation above; onset matches the analytic Hopf) ;
          interpretive(endogenous perpetual change = a limit cycle born at a Hopf bifurcation; a static system
          relaxes to a plateau) ; analogy(the Red Queen, coevolution, an arms race).
KNOWN MATCH: Rosenzweig-MacArthur predator-prey; the paradox of enrichment (Hopf destabilization); predator-
          prey limit cycles and the quarter-period phase lag. All established population-dynamics physics.
STATUS:   GREEN (gates on physical population quantities: oscillation amplitude and its Hopf onset).
A_OR_B:   (A) faithful. Hand input = the Rosenzweig-MacArthur field law + K; the plateau, the limit cycle,
          the Hopf threshold and the phase lag are emergent and measured.

THE TRAP (designer hit it, we avoid it): do NOT put the threshold in. We set ONE enrichment K and a real
population law; the plateau, the sustained oscillation, the Hopf onset K_c and the phase lag are OUTPUTS that
match Rosenzweig-MacArthur / paradox-of-enrichment theory. "Static" is the SAME law below the Hopf point.

Floors: "Red Queen / coevolution / arms race" is analogy for a predator-prey limit cycle. 同じ数学≠同じもの:
this does NOT claim coevolution IS a Hopf bifurcation -- it shows the SAME fact (a static system plateaus; an
interacting one sustains ENDOGENOUS change with no external knob) emerges in a field with no agents. The field
gives endogenous OSCILLATION, NOT literal unbounded complexity growth (that stays frontier). (A) faithful: the
population law is put in by hand, not derived.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"r": 1.0, "c": 1.0, "H0": 0.3, "e": 1.0, "m": 0.4,
           "Ks": [0.45, 0.55, 0.65, 0.75, 0.85, 1.0, 1.15], "K_plateau": 0.55, "K_cycle": 1.15,
           "T": 8000, "dt": 0.005, "burn": 0.5, "amp_threshold": 0.1}
QUICK = {"Ks": [0.45, 0.55, 0.75, 1.15], "T": 6000}


def _fixed_point(K, p):
    Hs = p["m"] * p["H0"] / (p["e"] * p["c"] - p["m"])
    Ps = (p["r"] / p["c"]) * (1 - Hs / K) * (Hs + p["H0"])
    return Hs, Ps


def _jac_trace(K, p):
    """Trace of the Jacobian at coexistence; Hopf bifurcation when it crosses 0 (det>0)."""
    Hs, Ps = _fixed_point(K, p)
    return p["r"] * (1 - 2 * Hs / K) - p["c"] * Ps * p["H0"] / (Hs + p["H0"]) ** 2


def _analytic_hopf(p):
    Ks = np.linspace(p["Ks"][0], p["Ks"][-1] + 1.0, 800)
    tr = np.array([_jac_trace(K, p) for K in Ks])
    return float(np.interp(0.0, tr, Ks))


def _run(K, p):
    """Integrate the Rosenzweig-MacArthur field; return late-time amplitude and H-P zero-lag correlation."""
    Hs, Ps = _fixed_point(K, p)
    H, P = Hs * 1.15, Ps * 0.9
    Hh, Pp = [], []
    for t in range(p["T"]):
        dH = p["r"] * H * (1 - H / K) - p["c"] * H * P / (H + p["H0"])
        dP = p["e"] * p["c"] * H * P / (H + p["H0"]) - p["m"] * P
        H = max(H + p["dt"] * dH, 1e-12)
        P = max(P + p["dt"] * dP, 1e-12)
        if t > p["burn"] * p["T"]:
            Hh.append(H); Pp.append(P)
    Hh, Pp = np.array(Hh), np.array(Pp)
    amp = float(Hh.max() - Hh.min())
    hc, pc = Hh - Hh.mean(), Pp - Pp.mean()
    corr = float((hc * pc).mean() / (hc.std() * pc.std() + 1e-12))
    return amp, corr


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = []
    for K in p["Ks"]:
        amp, corr = _run(K, p)
        rows.append({"K": K, "trace": round(_jac_trace(K, p), 3),
                     "amplitude": round(amp, 3), "hp_corr": round(corr, 2)})
    hopf = _analytic_hopf(p)
    KK = np.array([r["K"] for r in rows]); AA = np.array([r["amplitude"] for r in rows])
    onset = float(np.interp(p["amp_threshold"], AA, KK))     # emergent oscillation onset
    amp_plateau = next(r["amplitude"] for r in rows if r["K"] == p["K_plateau"])
    amp_cycle = next(r["amplitude"] for r in rows if r["K"] == p["K_cycle"])
    corr_cycle = next(r["hp_corr"] for r in rows if r["K"] == p["K_cycle"])
    return {
        "params": p, "rows": rows,
        "analytic_hopf": round(hopf, 3), "measured_onset": round(onset, 3),
        "onset_err": round(abs(onset - hopf), 3),
        "amp_plateau": amp_plateau, "amp_cycle": amp_cycle, "corr_cycle": corr_cycle,
    }


def evaluate(result, quick=False):
    checks = {
        "enrichment_below_hopf_plateaus (amplitude < 0.05 below the critical enrichment)":
            bool(result["amp_plateau"] < 0.05),
        "enrichment_above_hopf_sustains_oscillation (amplitude > 0.3 above it, no external forcing)":
            bool(result["amp_cycle"] > 0.3),
        "oscillation_onset_matches_analytic_hopf (measured onset within 0.1 of Jacobian trace=0)":
            bool(result["onset_err"] < 0.1),
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e035 field Red Queen (predator-prey Hopf bifurcation, no agents)", "tier": "measured",
        "put_in": "Rosenzweig-MacArthur predator-prey field (Holling type II) for continuous host/parasite "
                  "densities; one enrichment K. NO agents / genomes / selection sampling",
        "emerged": ["oscillation amplitude vs enrichment K (plateau below Hopf, limit cycle above): %s"
                    % [(r["K"], r["amplitude"], r["trace"]) for r in result["rows"]],
                    "measured onset K_c=%s vs analytic Hopf (Jacobian trace=0) K_c=%s"
                    % (result["measured_onset"], result["analytic_hopf"]),
                    "host-parasite zero-lag correlation ~0 at K=cycle (quarter-period chase): %s"
                    % result["corr_cycle"]],
        "surprises": ["a single enrichment number K turns a static plateau into a self-sustained oscillation at "
                      "exactly the Hopf point -- endogenous perpetual change with no external forcing, threshold "
                      "never put in"],
        "persistence": "above K_c the limit cycle is the attractor -- the oscillation persists forever with no drive",
        "measured_numbers": {"rows": result["rows"], "analytic_hopf": result["analytic_hopf"],
                             "measured_onset": result["measured_onset"], "onset_err": result["onset_err"]},
        "not_scripted_check": "only K and the population law are set; the plateau, the limit cycle, the Hopf "
                              "onset and the phase lag are measured",
        "claim_tier": "measured (plateau below K_c; sustained oscillation above; onset matches analytic Hopf) ; "
                      "interpretive (endogenous perpetual change = a limit cycle born at a Hopf bifurcation) ; "
                      "analogy (the Red Queen / coevolution / arms race)",
        "floors": ["'Red Queen / coevolution / arms race' is analogy for a predator-prey limit cycle",
                   "同じ数学≠同じもの: this does NOT claim coevolution IS a Hopf bifurcation; the SAME fact "
                   "(static plateaus / interacting sustains endogenous change) emerges in a field with no agents",
                   "the field gives endogenous OSCILLATION, NOT literal unbounded complexity growth (frontier)",
                   "(A) faithful: the population law is put in by hand, not derived"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e035 field Red Queen (predator-prey Hopf, no agents)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e035 -- the Red Queen from a FIELD (Rosenzweig-MacArthur predator-prey, no agents) ===")
    print("  enrichment K | Jacobian trace | oscillation amplitude | H-P corr")
    for row in r["rows"]:
        reg = "plateau" if row["trace"] < 0 else "cycle"
        print("     K=%.2f | trace=%+.3f | amp=%.3f | corr=%+.2f  (%s)"
              % (row["K"], row["trace"], row["amplitude"], row["hp_corr"], reg))
    print("  measured onset K_c=%s vs analytic Hopf K_c=%s (err %s)"
          % (r["measured_onset"], r["analytic_hopf"], r["onset_err"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (Red Queen as a Hopf bifurcation; endogenous oscillation, threshold emergent)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "red_queen.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/red_queen.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
