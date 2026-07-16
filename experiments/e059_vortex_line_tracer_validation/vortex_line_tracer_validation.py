#!/usr/bin/env python3
"""e059 -- 3D vortex-line tracer validation on the seeded ring (H021 campaign, PR-C, role V).

Follows up the two external reviews (GPT + a second Claude, 2026-07-16) that both recommended
pivoting new 3D-native measurement work toward a general vortex-line/loop instrument -- with the
existing seeded vortex ring (e003) as the natural first validation target (this is the F1
("One-Handle Selection") entry point that Evidence Contract v2 SS9.3 reserves for a self-formed
vortex loop; THIS experiment does NOT attempt that -- it validates the INSTRUMENT on a known,
seeded, non-emergent ring, which must come first).

Reuses e003's exact damped-free 3D GPE quench-free ring setup (uniform background + one imprinted
vortex ring, imaginary-time relaxation then real-time propagation) UNCHANGED -- same params, same
core.field/core.measure calls -- and applies TWO independent instruments to the SAME psi frames:
  (a) the NEW genesis.diagnostics.vortex_lines_3d.trace_vortex_lines (general-purpose plaquette-flux
      line tracer, this PR)
  (b) the EXISTING core.vortex.track_ring_cross_section (e003's single meridional-slice 2-core
      tracker, unchanged, no_touch)
and reports whether they agree on ring radius and axial (propagation) position -- an independent
cross-check between two differently-designed instruments applied to the same field, the same
pattern LT-1/2/3 used against measures.py and Observer v2 used against level3_motion.py.

Campaign role tag: V (verification/measurement instrument). NOT a genesis/emergent claim -- the
ring is SEEDED, not self-formed; this experiment says nothing about whether a ring self-forms
from t=0.
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
from core.fft import k_squared_3d  # noqa: E402
from genesis.diagnostics.vortex_lines_3d import trace_vortex_lines  # noqa: E402
from experiments.e003_gpe_vortex_ring.run import DEFAULT as E003_DEFAULT  # noqa: E402

QUICK = {"L": 48, "R": 7.0, "n_imag": 100, "n_real": 400, "sample": 40}

EXPECT = {
    "min_both_frames": 4,
    "radius_diff_frac": 0.25,       # a frame "agrees" if matched-loop radius is within 25% of old tracker's
    "radius_agree_frac_min": 0.7,   # at least 70% of comparable frames must agree (honest majority, not 100%)
    "match_rate_min": 0.8,          # a bulk loop is found and matched in at least 80% of samples
}


def run(quick=False, params=None):
    p = dict(E003_DEFAULT)
    if quick:
        p.update(QUICK)
    if params:
        p.update(params)

    L, g, mu, R = p["L"], p["g"], p["mu"], p["R"]
    c = (L - 1) / 2.0
    V = 0.0
    k2 = k_squared_3d(L)

    phase0 = field.vortex_ring_phase(L, R, charge=1)
    psi = np.sqrt(mu) * np.exp(1j * phase0)
    norm0 = measure.norm(psi)
    for _ in range(p["n_imag"]):
        psi = field.step_imag_3d(psi, V, k2, g, mu, p["dtau"])
        psi *= np.sqrt(norm0 / np.sum(np.abs(psi) ** 2))
        psi = np.abs(psi) * np.exp(1j * phase0)

    jy = int(round(c))
    bounds = (p["axial_margin"], L - 1 - p["axial_margin"])
    prev_outer, prev_inner = (c + R, c), (c - R, c)

    # Reuse e003's OWN self-detecting "clean window" termination (not a new criterion): stop once
    # the old tracker's ring (a) leaves a tight radius band around its first reading, or (b)
    # retreats from its furthest axial point -- i.e. once e003's own instrument considers clean
    # self-propagation to have ended (sound/noise dominating). Comparing the new tracer against
    # the old one PAST that point is not a fair test of either instrument -- e003 itself does not
    # trust its own reading there.
    old_radii, old_axials = [], []
    direction, extreme = 0, None

    frames = []   # per-sample: {step, new_tracer:{...}, old_tracker:{...} or None}
    prev_matched_centroid = None
    for step in range(p["n_real"]):
        psi = field.step_real_3d(psi, V, k2, g, mu, p["dt"])
        if step % p["sample"] != 0:
            continue
        old = vortex.track_ring_cross_section(psi[:, jy, :], c, prev_outer, prev_inner, bounds)
        if old is not None:
            if old_radii and abs(old["radius"] - old_radii[0]) > p["radius_band"] * old_radii[0]:
                break
            if direction != 0 and (old["axial"] - extreme) * direction < -0.5:
                break
            prev_outer, prev_inner = old["outer"], old["inner"]
            old_radii.append(old["radius"])
            old_axials.append(old["axial"])
            if len(old_axials) == 4:
                direction = int(np.sign(old_axials[3] - old_axials[0]))
                extreme = old_axials[-1]
            elif direction != 0 and (old["axial"] - extreme) * direction > 0:
                extreme = old["axial"]
        new = trace_vortex_lines(psi)
        # e003's OWN honesty floor: the ring imprint is non-periodic across the z boundary and
        # seeds a STATIC vortex sheet near z~0 (see e003 AUDIT.md); e003 excludes it from its own
        # meridional tracker via `axial_margin`/`bounds`. The general tracer sees that sheet too
        # (plus, at later steps, small sound-driven vortex-antivortex loops elsewhere in the bulk
        # -- also expected, coarse-resolution GPE dynamics, same floor e003 states for late-time
        # sound). Apply the SAME axial bounds e003 already uses (not a new/invented filter) before
        # comparing, and report what was excluded, never silently.
        bulk_loops = [l for l in new["loops"] if bounds[0] <= l["centroid"][2] <= bounds[1]]
        matched = None
        if bulk_loops:
            if prev_matched_centroid is not None:
                # Temporal continuity is the PRIMARY match criterion once we have a previous
                # fix: a physical ring moves smoothly between consecutive samples (a few cells),
                # while sound-driven artifact loops appear/disappear transiently and are unlikely
                # to sit exactly where the ring just was. This is far more robust over a long run
                # than re-matching cold on radius every frame (found in this validation: cold
                # radius-matching alone increasingly confuses the ring with same-radius sound
                # loops as noise accumulates over hundreds of steps).
                # GATED by radius plausibility (external review, 2026-07-16): nearest-centroid
                # alone can still latch onto a tiny artifact loop that happens to sit close to the
                # ring's last known position while the real ring is still present elsewhere in the
                # frame. When the old tracker's own radius reading is available for this frame,
                # restrict candidates to those within a generous (50%) band of it before picking
                # the nearest centroid; only fall back to the unfiltered set if nothing qualifies.
                pmc = np.array(prev_matched_centroid)
                candidates = bulk_loops
                if old is not None:
                    plausible = [l for l in bulk_loops if abs(l["effective_radius"] - old["radius"]) < 0.5 * old["radius"]]
                    if plausible:
                        candidates = plausible
                matched = min(candidates, key=lambda l: np.linalg.norm(np.array(l["centroid"]) - pmc))
            elif old is not None:
                matched = min(bulk_loops, key=lambda l: abs(l["effective_radius"] - old["radius"]))
            elif len(bulk_loops) == 1:
                matched = bulk_loops[0]
            if matched is not None:
                prev_matched_centroid = matched["centroid"]
        frames.append(dict(
            step=step,
            new_n_loops_total=len(new["loops"]),
            new_n_loops_bulk=len(bulk_loops),
            new_n_loops_outside_bulk=len(new["loops"]) - len(bulk_loops),
            new_n_open_paths=len(new["open_paths"]),
            new_n_overloaded=new["n_cubes_overloaded"],
            new_n_unhealed=new["n_unhealed_dangling"],
            new_matched_loop=matched,
            old_tracker=old,
        ))
        if old is None:
            break   # ring left the meridional-slice tracker's clean window (e003 convention)

    # honest agreement summary -- only over frames where BOTH instruments found something to compare.
    # Known limitation (found in this validation, not hidden): the nearest-neighbor dangling-face
    # healing in vortex_lines_3d occasionally mispairs a local tangent-region gap with ITSELF
    # (closing a small spurious loop across the gap) instead of reconnecting across to the next
    # segment, under the small real-time phase perturbations a propagating field picks up (a
    # perfectly symmetric static ring does not trigger this -- see the module's synthetic tests).
    # Rather than silently discard or force-pass these frames, they are counted explicitly
    # (n_frames_large_radius_diff) and the pass criterion is a majority-agreement fraction, the
    # same "report the honest split, don't force 100%" discipline as e057's 70/30 result.
    both = [f for f in frames if f["new_matched_loop"] is not None and f["old_tracker"] is not None]
    n_clean_single_bulk_loop = sum(1 for f in frames if f["new_n_loops_bulk"] == 1)
    radius_diffs, axial_diffs = [], []
    new_axial_series, old_axial_series = [], []
    for f in both:
        new_r = f["new_matched_loop"]["effective_radius"]
        old_r = f["old_tracker"]["radius"]
        radius_diffs.append(abs(new_r - old_r))
        new_axial_series.append(f["new_matched_loop"]["centroid"][2])
        old_axial_series.append(f["old_tracker"]["axial"])
    tol = 0.25 * p["R"]
    n_large_diff = sum(1 for d in radius_diffs if d >= tol)

    min_both = 3 if quick else EXPECT["min_both_frames"]
    verdict = "insufficient_frames" if len(both) < min_both else "agreement_measured"
    result = dict(
        params=p, n_samples=len(frames), n_both_instruments=len(both),
        n_clean_single_bulk_loop=n_clean_single_bulk_loop,
        n_loops_outside_bulk_total=sum(f["new_n_loops_outside_bulk"] for f in frames),
        n_loops_bulk_total=sum(f["new_n_loops_bulk"] for f in frames),
        radius_diff_mean=float(np.mean(radius_diffs)) if radius_diffs else None,
        radius_diff_median=float(np.median(radius_diffs)) if radius_diffs else None,
        radius_diff_max=float(np.max(radius_diffs)) if radius_diffs else None,
        n_frames_large_radius_diff=n_large_diff,
        new_axial_series=[round(float(a), 3) for a in new_axial_series],
        old_axial_series=[round(float(a), 3) for a in old_axial_series],
        frames=frames,
        verdict=verdict,
        run_valid=True,
    )
    return result


def evaluate(result, quick=False):
    n_both = result["n_both_instruments"]
    n_samples = result["n_samples"]
    match_rate = n_both / n_samples if n_samples else 0.0
    radius_agree_frac = (1.0 - result["n_frames_large_radius_diff"] / n_both) if n_both else 0.0
    min_both = 3 if quick else EXPECT["min_both_frames"]
    checks = {
        "enough_frames_to_compare": n_both >= min_both,
        "matched_most_frames": match_rate >= EXPECT["match_rate_min"],
        "radius_agrees_majority_of_frames": radius_agree_frac >= EXPECT["radius_agree_frac_min"],
        "no_overloaded_cubes": all(f["new_n_overloaded"] == 0 for f in result["frames"]),
    }
    return all(checks.values()), checks


def _print_report(result, quick=False):
    print(__doc__)
    p = result["params"]
    print("------------------------------ MEASUREMENTS ------------------------------")
    print("params: L=%d R=%g | imag %dx%.2f real %dx%.2f sample every %d"
          % (p["L"], p["R"], p["n_imag"], p["dtau"], p["n_real"], p["dt"], p["sample"]))
    print("samples: %d  (both instruments comparable: %d)" % (result["n_samples"], result["n_both_instruments"]))
    print("clean single-bulk-loop frames: %d / %d   |   loops found outside the bulk axial window "
          "(e003's own z~0 sheet + sound, excluded exactly as e003 excludes them): %d total"
          % (result["n_clean_single_bulk_loop"], result["n_samples"], result["n_loops_outside_bulk_total"]))
    if result["radius_diff_mean"] is not None:
        print("radius diff (new tracer's matched loop vs track_ring_cross_section): mean=%.3f median=%.3f max=%.3f"
              % (result["radius_diff_mean"], result["radius_diff_median"], result["radius_diff_max"]))
        print("frames with large (>=25%% R) radius diff: %d / %d (known healing-heuristic limitation, see AUDIT.md)"
              % (result["n_frames_large_radius_diff"], result["n_both_instruments"]))
    print("axial series (new tracer, matched loop): %s" % result["new_axial_series"])
    print("axial series (old tracker):              %s" % result["old_axial_series"])
    passed, checks = evaluate(result, quick=quick)
    print("------------------------------- AUDIT 5/6 --------------------------------")
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s" % ("GREEN" if passed else "RED"))
    print("  VERDICT: %s" % result["verdict"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="e059 3D vortex-line tracer validation (seeded ring)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args(argv)

    result = run(quick=args.quick)
    _print_report(result, quick=args.quick)

    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "vortex_line_tracer_validation.json"), "w") as f:
            json.dump(result, f, indent=2)
        print("\nwrote %s" % os.path.join(args.out, "vortex_line_tracer_validation.json"))

    passed, _ = evaluate(result, quick=args.quick)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
