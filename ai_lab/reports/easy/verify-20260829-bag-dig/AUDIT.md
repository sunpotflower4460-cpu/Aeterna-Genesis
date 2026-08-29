# AUDIT — why white+TDGL does not leave a bag (not an official Room)

```
MODULE:      verify-20260829-bag-dig (dated report; not a Room)
QUESTION:    Why does undifferentiated white + existing TDGL fill the box with
             one dense ground, and does a bounded persistent inside appear if
             only noise coarseness / cooling are changed?
PUT IN:      existing g001 TDGL (genesis.models.ginzburg_landau).
             IC = uniform near-zero + noise (optional Gaussian smoothing of
             the same rms; no extra amplitude). No bag, vesicle, membrane,
             circle, or body location. Quench duration varied; law unchanged.
             Official rooms: stored summaries + display lenses only (no 64³ rerun).
EMERGED:     After growth, dense_frac → ~0.99 on every grown TDGL variant.
             Holes (windings) remain as a separate card. No persistent one-body
             bag. Slow short window stays dim because order has not grown yet;
             waiting after the same slow quench fills yellow again.
CLAIM TIER:  measured: dense_frac, outside_abs_frac, component counts, span,
             persist, windings, official mean_amp / defect_count, G003
             two-ground maze, hashes, heatmaps.
             interpretive: unique bulk well ⇒ no second ground to sit as "outside".
             analogy: cell / life / vesicle — refused.
KNOWN MATCH: WHITE_CEILINGS g001 TDGL ceiling L2 (phase-winding defects in an
             ordered bulk). e008/e010 Kibble–Zurek: amplitude order + holes.
             G003 Model H: spinodal two grounds, 50–50, bicontinuous (mapped,
             not promoted).
AUDIT (7):
  1. Rule does not name the result: Yes — TDGL local law. Bag scored after
     the fact on frozen gates.
  2. Faithful physics: Yes — existing g001 stepper (np.roll Laplacian).
     Coarse IC is filtered noise, not a drawn body.
  3. Result not in IC: Yes — white / smoothed white. No bag seeded.
  4. Untargeted concomitants: Yes — slow short window stays near-zero;
     coarse noise reduces hole count; 20³ lens undercounts defects;
     frozen ruler can mark one maze island on G003 for a single frame.
  5. Numbers: Yes — measurements.json. Cheap 48²; official 64³ unread as
     a rerun.
  6. Robust: Partial — two default seeds + quench/corr variants, one window.
     Not a continuum droplet study.
  7. Code discovers vs asserts: Yes — ndimage.label + frozen frac/span
     gates. tests/test_bag_dig.py: filled bulk + holes is NOT a bag.
     Thresholds not edited after seeing grown pictures (G003 island leak
     documented, not patched this round).
STATUS:      YELLOW / role N primary (asked bag not observed).
             Secondary V: unique-well explanation of fill; G003 two-ground map.
A_OR_B:      (A) faithful TDGL from white. Law not derived from 0.
```

## Jobs kept separate

| job | what it is | this report |
|---|---|---|
| **bag / one inside with a skin** | dense connected inside, bounded, persistent | **not observed** |
| vortex-hole relations | pairs, triangles, leftover cores | informational only. PR 133 is history |
| ring pinch 1→2 | loop of holes cinches | not this gate. PR 134 is history |
| F7 network fission | relation-graph split | not scored |
| official L2 localization | winding defects persist | **holes, not a bag** |
| two grounds sitting (G003) | composition ± phases + interface | mapped; maze; **not promoted** |
| life / cell | — | **refused** |
| goal_progress.json 10/10 | fission mission | **untouched** (still 0/10) |

## Mixing audit (asked)

1. **Official Level 2 `localization`** in `genesis/diagnostics/measures.py::assess_level` is `defects>0 and persistent_defects`. `room-g001-a` has `detected.localization=true` because `defect_count=241` (holes) with `final_mean_amplitude≈0.97`. That is **not** a dense body with a skin. `measures.py` was **not** changed (no_touch; L2 is the vortex gate).
2. **Bag ruler** (frozen, same numbers as PR 135) does **not** pass on hole count, triangle, or ring 1→2. `bag_rescued_by_holes` is always false. Unit tests lock this.
3. **Ruler leak (not retuned):** on the G003 48² composition lens, two isolated frames (`t=35` phase A, `t=45` phase B) satisfy `bag_candidate` because one island is ≥2% and other same-phase patches are each below `min_body_frac`. Those frames still have tens of components. Persistence = 1 < 5. Documented as a maze-island leak. Gates were **not** loosened or tightened after seeing it.

## Why yellow fills (measured + interpretive)

Post-quench `eps=+1`: bulk potential `V(r) = -r²/2 + r⁴/4` has a unique minimum at `r=1` and a maximum at `r=0`. There is no second stable amplitude. Low amplitude survives only as topological cores. Therefore "outside remaining" in the bag sense (a neighboring ground that is not a hole) **cannot sit in this white**. Coarseness and cooling change **when** order arrives and **how many holes** remain, not whether a second ground exists.

## TDGL variants (48², not official)

| name | quench | corr | end mean | dense_frac | outside\|ψ\|<0.5 | holes | windings | persistent bag |
|---|---|---|---|---|---|---|---|---|
| default s0 | 8 | 0 | 0.971 | 0.996 | 0.004 | 3 | 4 | no |
| default s1 | 8 | 0 | 0.963 | 0.994 | 0.006 | 4 | 4 | no |
| fast | 1 | 0 | 0.966 | 0.992 | 0.008 | 1 | 6 | no |
| slow (t=22, still pre-growth) | 24 | 0 | 5.3e-5 | (relative noise) | 1.0 | — | 0 | no |
| slow wait t=50 | 24 | 0 | 0.987 | 0.998 | 0.002 | 1 | 2 | no |
| coarse | 8 | 4 | 0.983 | 0.998 | 0.002 | 2 | 2 | no |
| very coarse | 8 | 8 | 0.985 | 0.997 | 0.003 | 1 | 2 | no |

Hashes in `measurements.json`. Default s0 end sha256 `e29dec36a80d53a8…`.

## Official rooms (stored; no 64³ rerun)

**room-g001-a** full-3D 64³ summaries:

| seed | reached_level | final_mean_amplitude | defect_count (seed 0 emergence) |
|---|---|---|---|
| 0 | 2 | 0.9738 | 241 |
| 1 | 2 | 0.9818 | 173 (README) |
| 2 | 2 | 0.9868 | 117 (README) |

Display lens 20³: interpolated, uint8. End dense_frac≈0.995, bag never. Lens hole count 0–1 at late times ≠ 241. Honesty: `interpolated_for_display=true`. Mid-z / mid-y slices are pictures, not the 64³ field.

**room-g003-a** 2D 128² Model H, mean φ=0 + noise 0.05 (no droplet placed):

- two grounds present on every lens frame
- interface_fraction_final 0.325, domain_scale_final 13.3
- pos/neg ≈ 0.50/0.50, many components (end n_pos=14, n_neg=18)
- `persistent_one_body=false` (longest consecutive bag_candidate = 1)
- **not promoted to bag mainline**

## Existing two-ground map (no new law this round)

| id | grown without placing a bag? | bag mainline? |
|---|---|---|
| room-g003-a Model H | yes (uniform+noise → two phases + interface) | no (maze) |
| e033 Cahn–Hilliard / Flory–Huggins | yes (χ>2 spinodal) | no |
| e020 vesicle_division | **no** — shapes PUT | do not use |
| gray_scott | spots/stains | no (no inheritance; not this lane) |
| swift_hohenberg | localization seeded | no |
| F0 P01 active droplet | docs only | not implemented |

Phase-separating fields were **not added** this round.

## Repro

```bash
python3 -m pytest tests/test_bag_dig.py -q
python3 ai_lab/reports/easy/verify-20260829-bag-dig/replay.py
```

Uses: `genesis.models.ginzburg_landau`, `scipy.ndimage`,
`genesis.diagnostics.measures.winding_defect_count`,
`genesis.diagnostics.topology3d`, `tools.snapshot`.
Stored lenses: `rooms/official/room-g001-a`, `rooms/official/room-g003-a`.

## Discipline

- no_touch: `measures.py`, official rooms, F-path gates, `goal_progress.json` untouched.
- 第8監査: IC is white / smoothed white. Criterion does not encode a drawn circle. Filling the box fails `max_body_frac=0.40`. G003 island leak not patched to manufacture a pass or a fail.
- Visualization separated from physics. Physical 0–1 PNGs vs `*_stretched_not_physics.png` labeled. G001/G003 lenses tagged interpolated.
- Deterministic seeds 0 and 1.
- Claim tiers not raised. Failures kept.
- PR 133 / 134 / 135 are history, not success conditions.

## Limits (floors)

1. 48² cheap window. Official 64³ not recomputed.
2. 20³ / 48² lenses are display downsamples. G003 bag_candidate leak is on the lens, not the 128² native field.
3. Core ~1 cell.
4. Persistence is snapshot cadence, not tracked IDs.
5. Periodic wrapping: a wrapping body fails as percolating (correct for "bounded lump").
6. Unique-well argument is for this TDGL white after quench; it is not a proof about every white.

## Next honest move (one)

Score the existing two-ground white (G003 / Cahn–Hilliard) for maze vs one remaining inside by changing **only mean composition** of a uniform+noise start. Do not place a droplet. Do not add a membrane field to TDGL. Do not return to triangles.
