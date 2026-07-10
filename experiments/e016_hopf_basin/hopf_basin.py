#!/usr/bin/env python3
"""e016 Stage 1 -- Hopf basin: the sqrt(c4) SIZE LAW is target_encoded (RETRACTED); Q_H stability holds.

---
id: e016
role: F
claim_tier: observed          # Q_H~1/Q_H=2 topological stability, bounded basin -- observed
evidence: "Q_H=2 held (|Q_H|~2) and Q_H~1 held under the stabilized flow, energy monotone; the sqrt(c4) size law is RETRACTED"
target_encoded: true          # the sqrt(c4) size law: start seeded ~sqrt(c4) + under-converged flow -> scaling inherited from the IC
known_match: "Derrick 1964 predicts L*~sqrt(c4) as THEORY; Faddeev-Niemi/Sutcliffe: Q_H=1,2 stable hopfions"
open_issues: ["a START-INDEPENDENT L* (true convergence) is the open problem (H001 frontier)", "high-L CV degradation unexplained", "fixed lattice"]
---

**8th-audit finding (this revision)**: the headline "size = k*sqrt(c4)" is **target_encoded** and is
**RETRACTED** as an emergence claim. The size-law loop seeds each c4 at `start = start_frac*sqrt(c4)` and
the gradient flow is UNDER-CONVERGED (it does not reach a start-independent fixed point in n_steps), so the
converged size TRACKS the start (fixed c4, varied start -> size varies 3.77..5.82) and, with the start
DECOUPLED from sqrt(c4), size/sqrt(c4) drifts strongly (1.03 -> 0.80). Derrick's L*~sqrt(c4) is ESTABLISHED
THEORY, but this module does NOT cleanly measure it. What survives: Q_H~1 and Q_H=2 topological stability
(read from B=curl A, not size) and the bounded basin (observed). Role downgraded GREEN -> **F**.

e012 Stage 3 showed the stabilized semi-implicit flow HOLDS a Q_H=1 hopfion at a
finite size for a single resolved start. Here we probed a quantitative law:

  (a) size(c4) = k * sqrt(c4).  **REPORT-ONLY / RETRACTED** (target_encoded, see above). For a family of c4
      the flow was started at start_frac*sqrt(c4); the "tight" size=k*sqrt(c4) fit is inherited from that
      seeding, not measured from a start-independent fixed point. The decoupling test (d) demonstrates this.
  (b) basin.  For a fixed c4 we sweep the START size over a wide range and record
      the final Q_H. The hopfion is held (Q_H ~ 1) only for starts in a BOUNDED
      window around the reference size -- both far-below (under-resolved) and
      far-above (delocalising) starts unwind. We report the window edges as
      multiples of the reference start = the measured floor (NOT a global basin).
  (c) Q_H = 2.  A doubled-azimuthal-winding hopfion (an (m,n)=(1,2) map) starts at
      |Q_H| ~ 1.93 and the SAME flow holds it at |Q_H| ~ 2 with energy monotone --
      a second, higher-charge particle stabilised by the same "third".

Put in: an S^2 field (Q_H=1 or 2) + Faddeev-Skyrme energy + the stabilized flow.
No size, no size law, no basin edge is put in. All are MEASURED.

Floors (honest): absolute k and the basin edges are resolution/kappa dependent
(fixed lattice); the largest c4 is resolution-marginal (L*~sqrt(c4) grows toward
the lattice cutoff, so Q_H degrades there and that c4 is reported, not hidden).
The basin is BOUNDED, not global (arrested-Newton / higher resolution to widen it
is Stage 2 / working-ledger H001). "Particle" is analogy (Faddeev-Niemi backing).

MODULE:   e016_hopf_basin (Stage 1: Q_H stability; sqrt(c4) size law RETRACTED)
QUESTION: Does the stabilized flow hold Q_H=1 and Q_H=2 hopfions with energy monotone? (The sqrt(c4) size law is target_encoded -- see (d).)
PUT IN:   S^2 hopfion (Q_H=1 or 2) + Faddeev-Skyrme energy + stabilized semi-implicit flow.
EMERGED:  (observed) Q_H~1 held across c4; Q_H=2 held (|Q_H|~2), energy monotone; BOUNDED basin. The sqrt(c4) size law does NOT survive decoupling the start (target_encoded).
CLAIM TIER: observed(Q_H~1/Q_H=2 held, bounded basin) ; established/theory(Derrick L*~sqrt(c4)) ; analogy(particle). The sqrt(c4) MEASUREMENT is retracted (target_encoded).
KNOWN MATCH: Derrick 1964 (L*~sqrt(c4), theory); Faddeev-Niemi / Sutcliffe (Q_H=1,2 are stable hopfions).
STATUS:   F (Q_H stability observed; sqrt(c4) size law RETRACTED as target_encoded; true start-independent L* is frontier / H001).
A_OR_B:   (A) faithful law; but the size-law CLAIM had sqrt(c4) embedded in the initial condition (8th-audit fail) -> retracted.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import hopf  # noqa: E402

# start_frac is chosen ONCE (physical, not result-fitted): start = start_frac*sqrt(c4)
# keeps the initial soliton both RESOLVED (>~6 grid points across the core) and
# INSIDE the basin for every c4. c4 range avoids the under-resolved small-c4 end
# and the lattice-cutoff large-c4 end (which is reported as a floor).
# L=44 with kappa=40 is the default; the size law is tight here AND at L=52 (CV~3.5%).
# At L=56 the fit degrades (CV~6.6%, sub-sqrt(c4)); we HYPOTHESISED a kappa~dx^4
# over-damping and TESTED it (arrested_newton.py / H001) -- it did NOT help
# (calibrated CV ~= fixed CV at L=52), so the high-L degradation is an OPEN floor,
# not explained by simple kappa scaling. The measured law stands at L=44/52.
DEFAULT = {"L": 44, "box": 8.4, "c2": 1.0, "kappa": 40.0, "dt": 8e-3,
           "n_steps": 450, "n_check": 4, "start_frac": 0.62,
           "c4_list": [12.0, 16.0, 20.0, 25.0, 30.0],
           "basin_c4": 20.0,
           "basin_mults": [0.5, 0.7, 0.9, 1.2, 1.5, 2.0],
           "qh2_c4": 20.0, "qh2_scale": 2.6}
QUICK = {"L": 40, "n_steps": 400, "c4_list": [16.0, 20.0, 25.0],
         "basin_mults": [0.7, 1.0, 1.4, 2.0]}


def qh_field_mn(L, scale, box, m=1, n=1):
    """(m,n) hopfion: base Q_H=1 map with the azimuthal (toroidal) winding raised
    to n and the poloidal winding to m, so Q_H ~ m*n (measured, not imposed).
    (1,1) reproduces core.hopf.hopfion_field up to sign; (1,2)/(2,1) give |Q_H|~2.
    Magnitudes keep |Z1|^2+|Z2|^2=1 so the S^2 image is covered smoothly."""
    x = np.linspace(-box, box, L, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    Xs, Ys, Zs = X / scale, Y / scale, Z / scale
    r2 = Xs ** 2 + Ys ** 2 + Zs ** 2
    den = r2 + 1.0
    rho = np.sqrt(Xs ** 2 + Ys ** 2) + 1e-12
    phi = np.arctan2(Ys, Xs)
    pol = np.arctan2(2.0 * Zs, r2 - 1.0)
    mag1 = 2.0 * rho / den
    mag2 = np.sqrt(np.clip(1.0 - mag1 ** 2, 0.0, 1.0))
    Z1 = mag1 * np.exp(1j * n * phi)
    Z2 = mag2 * np.exp(1j * m * pol)
    nf = np.stack([2.0 * (Z1.conj() * Z2).real,
                   2.0 * (Z1.conj() * Z2).imag,
                   np.abs(Z1) ** 2 - np.abs(Z2) ** 2], axis=0)
    nf = nf / np.linalg.norm(nf, axis=0, keepdims=True)
    return nf, 2.0 * box / L


def flow_converge(p, c4, start_scale, field=None):
    """Run the stabilized flow to convergence; return final Q_H, size, monotone."""
    if field is None:
        n, dx = hopf.hopfion_field(p["L"], start_scale, p["box"])
    else:
        n, dx = field
    K4 = hopf.k4_grid(p["L"], dx)
    dt = p["dt"]
    E0 = hopf.faddeev_energy(n, dx, p["c2"], c4)[0]
    Q0 = hopf.hopf_charge(n, dx)
    prev_E, mono = E0, True
    for _ in range(p["n_steps"]):
        n = hopf.stabilized_flow_step(n, dx, p["c2"], c4, dt, p["kappa"], K4)
        E = hopf.faddeev_energy(n, dx, p["c2"], c4)[0]
        if E > prev_E + 1e-6 * abs(E0):
            mono = False
        prev_E = E
    return {"Q_H_initial": round(float(Q0), 3), "Q_H_final": round(float(hopf.hopf_charge(n, dx)), 3),
            "size_final": round(float(hopf.e4_rms_size(n, dx)), 3), "energy_monotone": bool(mono)}


def _fit_sqrt(c4s, sizes):
    """Least-squares size = k*sqrt(c4) through the origin; R^2 and CV of k."""
    x = np.sqrt(np.asarray(c4s, float))
    y = np.asarray(sizes, float)
    k = float((x * y).sum() / (x * x).sum())
    yhat = k * x
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    ks = y / x
    cv = float(ks.std() / ks.mean()) if ks.mean() else 1.0
    return k, r2, cv, ks.tolist()


def _decoupling(p, c4s):
    """8th-audit decisive test: start EVERY c4 at the SAME fixed size (decoupled from sqrt(c4)) and see
    whether the converged size still tracks sqrt(c4). If the flow truly found the Derrick optimum L*, then
    size/sqrt(c4) would be ~constant regardless of the start. It is NOT: with a fixed start the converged
    size barely moves with c4, so size/sqrt(c4) drifts strongly -- i.e. the sqrt(c4) scaling in part (a) is
    INHERITED from seeding start~start_frac*sqrt(c4), not measured from a start-independent fixed point.
    Returns the drift (spread of size/sqrt(c4)); a large drift CONFIRMS the size law is target_encoded."""
    fixed = p["start_frac"] * np.sqrt(p["basin_c4"])       # one in-basin size for all c4
    rows, ratios = [], []
    for c4 in c4s:
        r = flow_converge(p, c4, fixed)
        ratio = r["size_final"] / np.sqrt(c4)
        rows.append({"c4": c4, "fixed_start": round(fixed, 3), "size_final": r["size_final"],
                     "Q_H_final": r["Q_H_final"], "size_over_sqrt_c4": round(ratio, 4)})
        ratios.append(ratio)
    drift = (max(ratios) - min(ratios)) / (np.mean(ratios) + 1e-12)
    return rows, float(drift)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)

    # (a) size "law": each c4 started INSIDE its basin (start ~ start_frac*sqrt(c4)) -- REPORT ONLY.
    # WARNING (8th audit): because the START is seeded proportional to sqrt(c4) and the flow is
    # under-converged (it does NOT reach a start-independent fixed point in n_steps), the sqrt(c4)
    # scaling here is largely EMBEDDED in the initial condition. See _decoupling below.
    law = []
    for c4 in p["c4_list"]:
        ss = p["start_frac"] * np.sqrt(c4)
        r = flow_converge(p, c4, ss)
        r.update({"c4": c4, "start_scale": round(ss, 3)})
        law.append(r)
    held = [r for r in law if r["Q_H_final"] > 0.85]      # well-resolved subset
    marginal = [r for r in law if r["Q_H_final"] <= 0.85]  # resolution-marginal (floor)
    if len(held) >= 2:
        k, r2, cv, ks = _fit_sqrt([r["c4"] for r in held], [r["size_final"] for r in held])
    else:
        k, r2, cv, ks = 0.0, 0.0, 1.0, []

    # (b) basin: sweep start over multiples of the reference start at basin_c4
    bc4 = p["basin_c4"]
    ref = p["start_frac"] * np.sqrt(bc4)
    basin = []
    for m in p["basin_mults"]:
        r = flow_converge(p, bc4, m * ref)
        basin.append({"mult": m, "start_scale": round(m * ref, 3),
                      "Q_H_final": r["Q_H_final"], "held": bool(r["Q_H_final"] > 0.7)})
    held_mults = [b["mult"] for b in basin if b["held"]]
    basin_window = [min(held_mults), max(held_mults)] if held_mults else []
    # BOUNDED means a finite window: the sweep must FAIL to hold on BOTH sides
    # (smallest start AND largest start unwind), bracketing the held window. A sweep
    # that only fails on one side has not bracketed the other edge (CodeRabbit/Codex).
    bounded = bool(basin and not basin[0]["held"] and not basin[-1]["held"])

    # (c) Q_H = 2 : doubled azimuthal winding, same flow
    fld = qh_field_mn(p["L"], p["qh2_scale"], p["box"], m=1, n=2)
    q2 = flow_converge(p, p["qh2_c4"], p["qh2_scale"], field=fld)
    q2_held = bool(abs(q2["Q_H_final"]) > 1.7)

    # (d) 8th-audit decoupling test: does the sqrt(c4) scaling survive a start decoupled from sqrt(c4)?
    decoup_c4 = p["c4_list"] if not quick else p["c4_list"]
    decoup_rows, decoup_drift = _decoupling(p, decoup_c4)

    return {
        "params": p, "law": law, "held_c4": [r["c4"] for r in held],
        "marginal_c4": [r["c4"] for r in marginal],
        "fit_k": round(k, 4), "fit_R2": round(r2, 4), "size_cv": round(cv, 4),
        "k_per_c4": [round(v, 4) for v in ks],
        "basin": basin, "basin_window_mult": basin_window, "basin_bounded": bounded,
        "qh2": {"c4": p["qh2_c4"], **q2}, "qh2_held": q2_held,
        # REPORT-ONLY: the seeded-start CV of k=size/sqrt(c4). It is small ONLY because the start was
        # seeded proportional to sqrt(c4) and the flow barely moves it -- NOT a measured emergent law.
        "seeded_size_cv": round(cv, 4), "law_fit_report_only": bool(cv < 0.05 and len(held) >= 2),
        # 8th-audit verdict: with the start DECOUPLED from sqrt(c4), size/sqrt(c4) drifts strongly
        # (drift >> 0), so the sqrt(c4) "law" is TARGET_ENCODED (embedded in the initial condition).
        "decoupling": decoup_rows, "decoupling_drift": round(decoup_drift, 4),
        "size_law_target_encoded": bool(decoup_drift > 0.10),
        "all_held_monotone": bool(all(r["energy_monotone"] for r in law) and q2["energy_monotone"]),
    }


def evaluate(result, quick=False):
    # NOTE (8th audit / role F): the sqrt(c4) SIZE LAW is RETRACTED as an emergence claim -- it is
    # target_encoded (the start was seeded ~sqrt(c4) and the flow is under-converged, so the scaling is
    # inherited from the initial condition, not measured). We gate instead on (i) the HONEST finding that
    # decoupling the start collapses the scaling, and (ii) the topological claims that are NOT size-encoded
    # (Q_H~1 and Q_H=2 are read from B=curl A; energy is monotone under the gradient flow).
    checks = {
        "size_law_is_target_encoded (decoupled start -> size/sqrt(c4) drifts >10%, NOT emergent)":
            bool(result["size_law_target_encoded"]),
        "Q_H~1 held across resolved c4 (topological, not size-encoded)": len(result["held_c4"]) >= 2,
        "Q_H=2 held (|Q_H|>1.7, topological)": result["qh2_held"],
        "energy monotone under gradient flow": result["all_held_monotone"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e016 hopf basin (Q_H stability; sqrt(c4) size law RETRACTED)", "tier": "observed/F",
        "put_in": "S^2 hopfion (Q_H=1 or 2) + Faddeev-Skyrme energy + stabilized flow",
        "emerged": ["Q_H=2 held: |Q_H| %s->%s (energy monotone)"
                    % (result["qh2"]["Q_H_initial"], result["qh2"]["Q_H_final"]),
                    "Q_H~1 held across c4=%s; a BOUNDED basin, window (x ref start) = %s"
                    % (result["held_c4"], result["basin_window_mult"]),
                    "sqrt(c4) size law RETRACTED (target_encoded): with the start decoupled from sqrt(c4), "
                    "size/sqrt(c4) drifts %.1f%% (rows %s)"
                    % (100 * result["decoupling_drift"],
                       [(d["c4"], d["size_over_sqrt_c4"]) for d in result["decoupling"]])],
        "surprises": ["a single stabilizer holds BOTH Q_H=1 and Q_H=2 particles (topological, not size-encoded)"],
        "persistence": "Q_H held inside the basin; starts outside the bounded window unwind",
        "measured_numbers": {"qh2": result["qh2"], "basin": result["basin"],
                             "basin_window_mult": result["basin_window_mult"],
                             "decoupling": result["decoupling"], "decoupling_drift": result["decoupling_drift"],
                             "seeded_size_cv": result["seeded_size_cv"], "law_seeded": result["law"]},
        "not_scripted_check": "Q_H from B=curl A (topological); the size law failed the decoupling (8th audit)",
        "claim_tier": "observed (Q_H~1/Q_H=2 held, bounded basin) ; established/theory (Derrick L*~sqrt(c4)) ; "
                      "analogy (particle). The sqrt(c4) MEASUREMENT is target_encoded and retracted.",
        "floors": ["THE sqrt(c4) SIZE LAW IS RETRACTED (target_encoded: start seeded ~sqrt(c4), under-converged flow)",
                   "a START-INDEPENDENT L* (true convergence) is the open problem (H001 frontier)",
                   "Q_H stability / basin edges are resolution/kappa dependent (fixed lattice)",
                   "'particle' is analogy (Faddeev-Niemi backing), not an electron"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e016 Hopf basin: size law + Q_H=2")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e016 Hopf basin: Q_H=1/Q_H=2 stability (sqrt(c4) size law RETRACTED = target_encoded) ===")
    print("  (a) size 'law' [REPORT-ONLY, seeded start ~sqrt(c4)]:")
    for row in r["law"]:
        tag = "held" if row["Q_H_final"] > 0.85 else "MARGINAL"
        print("     c4=%5.1f start=%.2f: Q_H %.2f->%.2f  size=%.3f  [%s]"
              % (row["c4"], row["start_scale"], row["Q_H_initial"], row["Q_H_final"],
                 row["size_final"], tag))
    print("     seeded fit: size = %.3f*sqrt(c4)  CV=%.1f%% -- but this CV is INHERITED from seeding start~sqrt(c4)"
          % (r["fit_k"], 100 * r["seeded_size_cv"]))
    print("  (d) 8th-audit DECOUPLING (fixed start for all c4): size/sqrt(c4) = %s  drift=%.1f%% => target_encoded=%s"
          % ([d["size_over_sqrt_c4"] for d in r["decoupling"]], 100 * r["decoupling_drift"],
             r["size_law_target_encoded"]))
    print("  (b) basin (x ref start at c4=%.0f):" % r["params"]["basin_c4"])
    for b in r["basin"]:
        print("     mult=%.2f start=%.2f: Q_H=%.2f  [%s]"
              % (b["mult"], b["start_scale"], b["Q_H_final"], "hold" if b["held"] else "unwind"))
    print("     basin window (mult) = %s   bounded=%s" % (r["basin_window_mult"], r["basin_bounded"]))
    print("  (c) Q_H=2: |Q_H| %.2f->%.2f  size=%.3f  monotone=%s  held=%s"
          % (r["qh2"]["Q_H_initial"], r["qh2"]["Q_H_final"], r["qh2"]["size_final"],
             r["qh2"]["energy_monotone"], r["qh2_held"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s [role F] (Q_H stability observed; sqrt(c4) size law RETRACTED = target_encoded)"
          % ("PASS" if passed else "FAIL"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "hopf_basin.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/hopf_basin.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
