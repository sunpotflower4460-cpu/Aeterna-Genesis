# e048 field/slow-field basin-decision calibration — audit (P07 / F1)

Frontier: `docs/frontier/F0_P07_field_slow_field_basin.md`. This is the **F1 (role V)** rung: it calibrates the
**basin-decision instrument** on KNOWN, PLACED basin states using the Loop-Trinity observers (LT-1 gauge
distance, LT-2 winding reliability, LT-3 plaquette ledger). It **does not run any fast/slow dynamics** — that is
S1 and is not implemented here.

## Claim (measured, role V)
- **Basins are separable.** W0/W1/W2 line-winding states read as dominant winding 0/1/2 (LT-2), fraction≈1,
  zero invalid lines; a 3D vortex-line-present vs absent basin separates by plaquette net (LT-3).
- **A basin-decision rule works.** Assign a field to `argmin_k invariant_distance(·, R_k)` (LT-1, gauge-
  invariant); clean states assign to their own basin with a large margin, a 50/50 spatial morph is flagged
  ambiguous (margin < ½ of clean).
- **Degradation is monotone.** Increasing noise on W1 raises the winding invalid-fraction and shrinks the basin
  margin monotonically.
- **The distance scale is separated,** so S1's copy/detachment bands are meaningful: `d(identical)=0 <
  d(same-basin spread) < d(different basin)`, ratio ≈ 4.7. We derive the **dimensionless S1 bands** here
  (copy_band = ½·d_same, detachment_band = ½·(d_same+d_diff)) from THIS repo's known states — **Loop's 0.05/0.35
  are not used**.

## What is PLACED vs MEASURED
- **Placed:** the basin states (W0/W1/W2 phase ramps; a 3D vortex line; a morph). This is why the role is **V**,
  not E. We validate the *decision instrument*, not emergence.
- **Measured:** dominant winding + reliability (LT-2), gauge-invariant basin distances + margins (LT-1),
  plaquette net (LT-3), the noise-degradation curve, and the same/different-basin distance scales.

## Discipline
- **育ったのか置いたのか:** basins are placed → role V. No dynamics, no growth claim.
- **8th audit / target encoding:** `target_encoded=false`. We place known states and measure distances; there is
  no law, no gate that rewards a "good" basin, no dynamics. The morph/ambiguity test guards against a decision
  rule that always answers the same basin.
- **no_touch:** `measures.py`, `rooms/official/**`, existing experiments/schema/registry untouched. New
  experiment dir + reuse of the LT observers only.
- **No imported thresholds:** the S1 copy/detachment bands are calibrated from this experiment's own known
  states, dimensionlessly (recorded `same_basin_noise`, `separation_ratio`).

## Limits / next
- This calibrates the *instrument*; it does **not** show that a slow field changes basin selection (S1) — that
  requires the coupled fast/slow dynamics + matched OFF control, and is **not** done here.
- 2D line-winding + a single 3D vortex fixture; full-3D basin calibration and seed/resolution robustness of the
  bands are for the S1/S2 stages.
- The within-basin scale depends on the chosen `same_basin_noise` (0.15, a clean same-basin variation); the band
  definitions are preregistered choices to be re-confirmed in S1.

## Reproduce
```
python experiments/e048_field_slow_field_calib/field_slow_field_calib.py            # full (writes results/*.json)
python experiments/e048_field_slow_field_calib/field_slow_field_calib.py --quick    # fast smoke (GREEN)
pytest tests/test_e048_field_slow_field_calib.py -q
```

## Not claimed (stop line)
Not claimed: that a slow field biases basin selection, that anything grew, or that this is emergence. Those are
S1+ and are deferred pending review of this calibration.
