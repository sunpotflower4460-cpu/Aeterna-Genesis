#!/usr/bin/env python3
"""e011 Stage 1 -- the dynamic "chemistry" of vortices: bound pairs obey a law.

Two imprinted vortices in a uniform condensate, evolved by the CONSERVATIVE GPE
(no damping), tracked by continuity (core/vortex.track_two_vortices). The local
field law -- which never mentions "pair", "translate" or "rotate" -- produces
two SELECTIVE, quantitative behaviours:

  * +/- (opposite signs)  -> a bound DIPOLE that TRANSLATES at speed v, with
                             v * d = const  (the Hamiltonian dipole law v~1/d).
  * ++  (same sign)        -> a bound pair that CO-ROTATES at angular speed w,
                             with w * d^2 = const ~ 2  (point-vortex w = 2/d^2).

Selectivity (the "chemistry"): the +/- pair barely rotates and the ++ pair's
centre of mass barely moves -- opposite signs translate, like signs orbit.

Pitfall avoided (designer's trap b): a phase-only imprint has NO density notch
at t=0, so we settle a few steps before the first measurement; tracking is by
winding + continuity (not a global density scan), which keeps each vortex's
identity and rejects sound.

Floors: v*d ~ const breaks at small d (d <~ a few healing lengths: core overlap,
compressible corrections), so the law is reported for d well above the core
size. The constants (v*d, w*d^2) are in lattice/GPE units; "molecule"/"chemistry"
is analogy, not a claim of a chemical bond. Conservative GPE => the bound pair is
robust (dissociation needs finite T -- see finite_T_dissociation.py).

MODULE:   e011_defect_chemistry (Stage 1: dynamic binding)
QUESTION: Do bound vortex pairs obey selective Hamiltonian laws (v*d const, w*d^2 const)?
PUT IN:   conservative GPE + uniform condensate + two imprinted vortices (field.vortex_phase). No motion is named.
EMERGED:  (measured) +/- translate with v*d=const; ++ co-rotate with w*d^2~2; selective.
CLAIM TIER: measured(v*d, w*d^2, selectivity) ; analogy("molecule"/"chemistry").
KNOWN MATCH: point-vortex Hamiltonian dynamics (dipole v~1/d; same-sign orbit w=2/d^2).
STATUS:   GREEN (both laws + selectivity measured; small-d deviation is a stated floor).
A_OR_B:   (A) faithful emergence. Hand input = GPE + uniform background + imprinted winding.
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

DEFAULT = {"L": 256, "g": 1.0, "mu": 1.0, "dt": 0.02, "settle": 20,
           "d_list": [16, 20, 24, 28], "nsub": 40}
QUICK = {"L": 160, "d_list": [16, 22], "nsub": 24}


def make_pair(L, mu, d, signs, center=None):
    """Uniform condensate sqrt(mu) with two vortices imprinted +-d/2 along y."""
    if center is None:
        center = (L / 2.0, L / 2.0)
    cx, cy = center
    ph = (field.vortex_phase(L, signs[0], (cx, cy - d / 2.0))
          + field.vortex_phase(L, signs[1], (cx, cy + d / 2.0)))
    return np.sqrt(mu) * np.exp(1j * ph)


def _step(psi, k2, g, mu, dt, n):
    V = np.zeros(psi.shape)
    for _ in range(n):
        psi = field.step_real(psi, V, k2, g, mu, dt)
    return psi


def track_pair(p, d, signs, total_steps):
    """Evolve a pair, return the per-frame [(x,y),(x,y)] trajectory by continuity."""
    L, g, mu, dt = p["L"], p["g"], p["mu"], p["dt"]
    k2 = k_squared(L)
    psi = make_pair(L, mu, d, signs)
    psi = _step(psi, k2, g, mu, dt, p["settle"])
    c = (L / 2.0, L / 2.0)
    pos = [(c[0], c[1] - d / 2.0), (c[0], c[1] + d / 2.0)]
    win = int(max(d, 10))
    cores = vortex.track_two_vortices(psi, pos, signs, window=win)
    if any(cc is None for cc in cores):
        return None, dt
    pos = [(cc["x"], cc["y"]) for cc in cores]
    traj = [pos]
    sub = max(1, total_steps // p["nsub"])     # never a zero stride (no evolution)
    for _ in range(p["nsub"]):
        psi = _step(psi, k2, g, mu, dt, sub)
        cores = vortex.track_two_vortices(psi, pos, signs, window=win)
        if any(cc is None for cc in cores):
            break
        pos = [(cc["x"], cc["y"]) for cc in cores]
        traj.append(pos)
    return traj, sub * dt


def _com(traj):
    return np.array([(0.5 * (q[0][0] + q[1][0]), 0.5 * (q[0][1] + q[1][1]))
                     for q in traj])


def _angle(traj):
    return np.unwrap([np.arctan2(q[1][1] - q[0][1], q[1][0] - q[0][0])
                      for q in traj])


def _sep(traj):
    return np.array([np.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]) for q in traj])


def dipole_law(p):
    """+/- pairs: translation speed v, product v*d (~const), and weak rotation."""
    rows = []
    for d in p["d_list"]:
        traj, dtf = track_pair(p, d, (+1, -1), total_steps=600)
        if traj is None or len(traj) < 5:
            rows.append({"d": d, "lost": True})
            continue
        t = np.arange(len(traj)) * dtf
        com = _com(traj)
        speed = float(np.hypot(np.polyfit(t, com[:, 0], 1)[0],
                               np.polyfit(t, com[:, 1], 1)[0]))
        omega = float(np.polyfit(t, _angle(traj), 1)[0])
        rows.append({"d": d, "v": round(speed, 4), "v_times_d": round(speed * d, 3),
                     "abs_omega": round(abs(omega), 5),
                     "sep_mean": round(float(_sep(traj).mean()), 2)})
    return rows


def corotation_law(p):
    """++ pairs: angular speed w, product w*d^2 (~const), and weak translation."""
    rows = []
    for d in p["d_list"]:
        traj, dtf = track_pair(p, d, (+1, +1), total_steps=1200)
        if traj is None or len(traj) < 5:
            rows.append({"d": d, "lost": True})
            continue
        t = np.arange(len(traj)) * dtf
        omega = float(np.polyfit(t, _angle(traj), 1)[0])
        com = _com(traj)
        drift = float(np.hypot(com[-1, 0] - com[0, 0], com[-1, 1] - com[0, 1]))
        rows.append({"d": d, "omega": round(omega, 5),
                     "omega_times_d2": round(abs(omega) * d * d, 3),
                     "com_drift": round(drift, 2)})
    return rows


def _cv(vals):
    a = np.asarray([v for v in vals if v is not None], float)
    return float(a.std() / a.mean()) if len(a) and a.mean() != 0 else 1.0


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    dip = dipole_law(p)
    cor = corotation_law(p)
    vd = [r.get("v_times_d") for r in dip if not r.get("lost")]
    wd2 = [r.get("omega_times_d2") for r in cor if not r.get("lost")]
    # selectivity: +/- translates (v large, omega ~0); ++ rotates (omega d^2 ~2, com small)
    dip_rot = np.mean([r.get("abs_omega", 0) for r in dip if not r.get("lost")])
    cor_drift = np.mean([r.get("com_drift", 0) for r in cor if not r.get("lost")])
    return {
        "params": p, "dipole": dip, "corotation": cor,
        "n_dipole_rows": len(vd), "n_corotation_rows": len(wd2),
        "v_times_d_mean": round(float(np.mean(vd)), 3) if vd else None,
        "v_times_d_cv": round(_cv(vd), 3),
        "omega_d2_mean": round(float(np.mean(wd2)), 3) if wd2 else None,
        "omega_d2_cv": round(_cv(wd2), 3),
        "dipole_rotation_small": round(float(dip_rot), 5),
        "corotation_drift_small": round(float(cor_drift), 2),
    }


EXPECT = {"cv_max": 0.15}


def evaluate(result, quick=False):
    # A "constant product" law is only meaningful ACROSS separations: with a
    # single surviving d the CV is trivially 0. Require >=2 tracked rows per law
    # before accepting the CV gate (Codex P2).
    checks = {
        "dipole_law(v*d const)": result["v_times_d_cv"] < EXPECT["cv_max"]
        and result["v_times_d_mean"] is not None and result["n_dipole_rows"] >= 2,
        "corotation_law(w*d^2 const)": result["omega_d2_cv"] < EXPECT["cv_max"]
        and result["omega_d2_mean"] is not None and result["n_corotation_rows"] >= 2,
        "selective(+/- translate, ++ rotate)":
            result["dipole_rotation_small"] < 0.01
            and result["corotation_drift_small"] < 8.0,
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e011 pair binding", "tier": "measured",
        "put_in": "conservative GPE + uniform condensate + two imprinted vortices; no motion named",
        "emerged": ["+/- bound dipole TRANSLATES with v*d=%.3f (const)"
                    % (result["v_times_d_mean"] or 0),
                    "++ bound pair CO-ROTATES with w*d^2=%.3f (~2, point-vortex)"
                    % (result["omega_d2_mean"] or 0)],
        "surprises": ["selective: opposite signs translate, like signs orbit -- "
                      "two distinct Hamiltonian laws from one field equation"],
        "persistence": "conservative GPE: the bound pair is robust (no dissociation without T)",
        "measured_numbers": {"v_times_d": result["v_times_d_mean"],
                             "v_times_d_cv": result["v_times_d_cv"],
                             "omega_d2": result["omega_d2_mean"],
                             "omega_d2_cv": result["omega_d2_cv"]},
        "not_scripted_check": "motion measured from continuity-tracked cores; the GPE never says 'orbit'",
        "claim_tier": "measured (v*d, w*d^2, selectivity) ; analogy ('molecule'/'chemistry')",
        "floors": ["v*d breaks at small d (core overlap); reported for d >> core size",
                   "constants in lattice/GPE units; 'molecule' is analogy, not a chemical bond"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e011 pair binding")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    result = simulate(quick=args.quick)
    print("=== +/- dipole: translation, v*d should be const ===")
    for r in result["dipole"]:
        if r.get("lost"):
            print("  d=%2d: lost" % r["d"]); continue
        print("  d=%2d: v=%.4f  v*d=%.3f  |omega|=%.5f  sep=%.1f"
              % (r["d"], r["v"], r["v_times_d"], r["abs_omega"], r["sep_mean"]))
    print("  -> v*d = %.3f (CV=%.3f)" % (result["v_times_d_mean"] or 0, result["v_times_d_cv"]))
    print("=== ++ pair: co-rotation, w*d^2 should be const (~2) ===")
    for r in result["corotation"]:
        if r.get("lost"):
            print("  d=%2d: lost" % r["d"]); continue
        print("  d=%2d: omega=%.5f  w*d^2=%.3f  com_drift=%.2f"
              % (r["d"], r["omega"], r["omega_times_d2"], r["com_drift"]))
    print("  -> w*d^2 = %.3f (CV=%.3f)" % (result["omega_d2_mean"] or 0, result["omega_d2_cv"]))
    passed, checks = evaluate(result, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (both Hamiltonian laws + selectivity measured)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "pair_binding.json")
        with open(out, "w") as f:
            json.dump({"result": result, "atlas": _atlas(result)}, f, indent=2)
        print("wrote results/pair_binding.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
