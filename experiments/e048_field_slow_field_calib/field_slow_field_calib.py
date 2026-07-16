#!/usr/bin/env python3
"""e048 field/slow-field basin-decision CALIBRATION (P07 / F1). role V (validation), NOT emergence.

This is the F1 (V) rung of docs/frontier/F0_P07_field_slow_field_basin.md. It does ONLY calibration on KNOWN,
PLACED basin states -- no coupled fast/slow DYNAMICS are run here (that is S1, and is not implemented). Its job
is to prove that the integration observers can decide "which basin is this field in?" cleanly, and to CALIBRATE
the dimensionless distance scale that the S1 experiment will use for its copy / detachment bands -- so those
bands come from this repo's own known states, never from Loop's imported numbers.

Calibrated / verified (all on placed, analytic states; measured tier):
  (1) basin separability: winding-reliability (LT-2) reads the W0/W1/W2 line-winding basins as dominant winding
      0/1/2 with dominant_fraction ~ 1 and zero invalid lines.
  (2) basin-decision rule: assign a test field to argmin_k invariant_distance(test, R_k) (LT-1, gauge-invariant);
      a clean state assigns to its basin with a large margin, a 50/50 morph is flagged ambiguous (small margin).
  (3) degradation: as noise grows, winding invalid_fraction rises and the basin margin shrinks (monotone).
  (4) distance-scale separation: d(identical)=0 < d(same-basin spread) < d(different basin), well separated, so
      the S1 copy/detachment bands (fractions of these scales) are meaningful. We REPORT the dimensionless bands.
  (5) local-vortex basin (LT-3): a 3D vortex-line-present vs absent basin is cleanly separated by the plaquette
      ledger (net winding), confirming the second basin family is also instrumentable.

DISCIPLINE (P07 / AGENTS.md): role V -- all basins are PLACED; this validates the DECISION INSTRUMENT, not
emergence. No physics/law/IC dynamics, no target encoding (we place known states and measure distances). No
Loop thresholds imported; the copy/detachment bands are derived here as fractions of measured same/diff scales.
no_touch: measures.py, rooms/official, existing experiments untouched; new module + observers only.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from genesis.diagnostics.gauge_aligned_distance import gauge_aligned_distance as gad      # noqa: E402
from genesis.diagnostics.winding_reliability import winding_reliability as wr             # noqa: E402
from genesis.diagnostics.plaquette_ledger import plaquette_ledger as pl                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FULL = dict(L=48, seeds=(0, 1, 2, 3), noise_ladder=(0.0, 0.2, 0.5, 0.9, 1.4), L3=24)
CONFIG_QUICK = dict(L=32, seeds=(0, 1), noise_ladder=(0.0, 0.5, 1.2), L3=18)


def basin_ref(L, w):
    """Reference basin W=w: a clean global line-winding (phase ramp along axis 0), unit amplitude."""
    x = np.arange(L)
    return np.exp(1j * 2 * np.pi * w * x / L)[:, None] * np.ones((1, L))


def assign_basin(test, refs):
    """Assign test to argmin_k invariant_distance(test, R_k); return (basin, margin, distances)."""
    d = [gad(test, r)["invariant_distance"] for r in refs]
    order = np.argsort(d)
    return int(order[0]), float(d[order[1]] - d[order[0]]), [float(x) for x in d]


def run(cfg):
    L = cfg["L"]
    refs = [basin_ref(L, k) for k in (0, 1, 2)]
    rng = np.random.default_rng(0)

    # (1) basin separability via winding reliability
    sep = []
    for k in (0, 1, 2):
        r = wr(refs[k], axis=0)
        sep.append(dict(basin=k, dominant=r["dominant_winding"], fraction=round(r["dominant_fraction"], 4),
                        invalid=r["invalid_fraction"]))
    sep_ok = all(s["dominant"] == s["basin"] and s["fraction"] > 0.99 and s["invalid"] == 0.0 for s in sep)

    # (2) basin-decision rule: clean assigns with large margin; a half/half morph is ambiguous
    clean = [assign_basin(refs[k], refs) for k in (0, 1, 2)]
    clean_ok = all(clean[k][0] == k and clean[k][1] > 1e-6 for k in (0, 1, 2))
    morph = refs[0].copy(); morph[L // 2:, :] = refs[1][L // 2:, :]        # spatial half W0 / half W1
    m_basin, m_margin, _ = assign_basin(morph, refs)
    clean_margin = min(clean[0][1], clean[1][1])
    ambiguity_ok = m_margin < 0.5 * clean_margin                          # morph margin clearly smaller

    # (3) degradation with noise (on basin W1)
    deg = []
    for a in cfg["noise_ladder"]:
        invs, mgs = [], []
        for s in cfg["seeds"]:
            rr = np.random.default_rng(100 + s)
            t = refs[1] + a * (rr.standard_normal((L, L)) + 1j * rr.standard_normal((L, L)))
            invs.append(wr(t, axis=0)["invalid_fraction"]); mgs.append(assign_basin(t, refs)[1])
        deg.append(dict(noise=a, invalid_fraction=round(float(np.mean(invs)), 4), margin=round(float(np.mean(mgs)), 4)))
    inv_series = [d["invalid_fraction"] for d in deg]
    mg_series = [d["margin"] for d in deg]
    monotone_ok = all(inv_series[i + 1] >= inv_series[i] - 1e-9 for i in range(len(inv_series) - 1)) and \
                  all(mg_series[i + 1] <= mg_series[i] + 1e-9 for i in range(len(mg_series) - 1))

    # (4) distance-scale separation -> copy/detachment bands (dimensionless, derived HERE).
    # within-basin spread uses a modest noise that STILL reads cleanly as the same basin (low invalid), so the
    # scale represents "same basin, minor variation" rather than a half-degraded field.
    same_noise = 0.15
    d_id = gad(refs[1], refs[1])["invariant_distance"]
    same = []
    for _ in range(6):
        n1 = same_noise * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
        n2 = same_noise * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
        same.append(gad(refs[1] + n1, refs[1] + n2)["invariant_distance"])
    d_same = float(np.mean(same))
    d_diff = float(np.mean([gad(refs[0], refs[1])["invariant_distance"], gad(refs[1], refs[2])["invariant_distance"]]))
    sep_ratio = d_diff / (d_same + 1e-12)
    bands_ok = (d_id < d_same < d_diff) and sep_ratio > 2.5      # same-basin scale clearly below between-basin
    copy_band = round(0.5 * d_same, 4)          # field<->slow distance below this => memory_copy_collapse (S1 rule)
    detach_band = round(0.5 * (d_same + d_diff), 4)   # above this => memory_detachment (S1 rule)

    # (5) local-vortex basin family via LT-3 (present vs absent), 3D
    n3 = cfg["L3"]
    xx = np.arange(n3) - (n3 - 1) / 2.0
    X, Y, Z = np.meshgrid(xx, xx, xx, indexing="ij")
    present = np.tanh(np.sqrt(X ** 2 + Y ** 2) / 2.0) * np.exp(1j * np.arctan2(Y, X))
    absent = np.ones((n3, n3, n3), complex)
    net_present = pl(present)["orientations"]["xy"]["net"]
    net_absent = pl(absent)["total"]["absolute"]
    lt3_ok = net_present >= n3 - 2 and net_absent == 0

    checks = {
        "LT-2 separates W0/W1/W2 basins (dominant winding, fraction>0.99, 0 invalid)": sep_ok,
        "LT-1 basin-decision: clean assigns to own basin with margin": clean_ok,
        "LT-1 ambiguity: 50/50 morph margin << clean margin": ambiguity_ok,
        "degradation monotone: noise raises invalid_fraction and shrinks margin": monotone_ok,
        "distance scale separated: d_id < d_same < d_diff, ratio>2.5": bands_ok,
        "LT-3 local-vortex basin present vs absent separated": lt3_ok,
    }
    return dict(separability=sep, clean_assign=clean, morph=dict(basin=m_basin, margin=round(m_margin, 4)),
                degradation=deg, scales=dict(d_identical=round(d_id, 6), d_same_basin=round(d_same, 4),
                d_different_basin=round(d_diff, 4), separation_ratio=round(sep_ratio, 2)),
                calibrated_bands=dict(copy_band=copy_band, detachment_band=detach_band,
                    note="dimensionless S1 bands derived from THIS repo's known states; Loop 0.05/0.35 NOT used"),
                lt3_basin=dict(net_present=int(net_present), abs_absent=int(net_absent)),
                checks=checks, all_ok=all(checks.values()))


def main(argv=None):
    ap = argparse.ArgumentParser(description="e048 P07/F1 basin-decision calibration (role V)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL

    print("=== e048 field/slow-field basin-decision CALIBRATION -- P07 / F1 (role V; basins PLACED) ===")
    r = run(cfg)
    print("-- (1) basin separability (LT-2 winding reliability) --")
    for s in r["separability"]:
        print("   W%d -> dominant=%s fraction=%.3f invalid=%.2f" % (s["basin"], s["dominant"], s["fraction"], s["invalid"]))
    print("-- (2) decision + ambiguity --  clean margins=%s  morph=%s"
          % ([round(c[1], 3) for c in r["clean_assign"]], r["morph"]))
    print("-- (3) degradation (noise -> invalid_fraction, margin) --")
    for d in r["degradation"]:
        print("   noise=%.2f  invalid=%.3f  margin=%.3f" % (d["noise"], d["invalid_fraction"], d["margin"]))
    print("-- (4) distance scales --  %s  -> S1 bands %s" % (r["scales"], r["calibrated_bands"]))
    print("-- (5) LT-3 local-vortex basin --  net_present=%d abs_absent=%d" % (r["lt3_basin"]["net_present"], r["lt3_basin"]["abs_absent"]))
    for k, ok in r["checks"].items():
        print("   [%s] %s" % ("PASS" if ok else "FAIL", k))
    passed = r["all_ok"]
    print("STATUS:", "GREEN" if passed else "RED", "(role V: basin-decision instrument calibrated on PLACED "
          "known states; no fast/slow dynamics run -- that is S1)")

    result = dict(experiment="e048_field_slow_field_calib", frontier="P07", rung="F1", role="V",
                  status="GREEN" if passed else "RED", config={k: v for k, v in cfg.items() if k != "seeds"}, **r)
    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "basin_calibration.json"), "w") as f:
            json.dump(result, f, indent=2, default=lambda o: list(o) if isinstance(o, tuple) else o)
        print("wrote", os.path.join(args.out, "basin_calibration.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
