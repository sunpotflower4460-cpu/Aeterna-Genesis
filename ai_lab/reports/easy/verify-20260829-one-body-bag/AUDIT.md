# AUDIT — first honest one-body-bag check (not an official Room)

```
MODULE:      verify-20260829-one-body-bag (dated report; not a Room)
QUESTION:    After amplitude grows from undifferentiated white, is there
             ONE connected dense inside with a closed skin that persists?
PUT IN:      existing g001 TDGL (genesis.models.ginzburg_landau) +
             make_initial = uniform near-zero + noise_amplitude=0.01.
             No bag, vesicle, membrane field, circle, or body location.
             Quench protocol unchanged (duration 8, dt=0.1, Du=1).
EMERGED:     Whole-domain high-amp bulk (dense_frac → 0.99). Vortex holes
             on a separate card. No bounded persistent body on any frame.
CLAIM TIER:  measured (dense_frac, component counts, span, persistence,
             winding_defect_count, 3D authenticity, hashes, heatmaps).
             interpretive: xz two-dots = line piercing a plane.
             analogy: cell / life — refused.
KNOWN MATCH: WHITE_CEILINGS g001 TDGL ceiling L2 (phase-winding defects
             in an ordered bulk). PR 134 32³ seed-1 defect annihilation
             in a small box. e008/e010 KZ: amplitude order + holes, not
             a localized bag.
AUDIT (7):
  1. Rule does not name the result: Yes — TDGL local law. Bag is scored
     after the fact on a frozen a-priori criterion.
  2. Faithful physics: Yes — existing g001 stepper. Local Laplacian
     (np.roll), not a new law.
  3. Result not in IC: Yes — white noise. No bag seeded.
  4. Untargeted concomitants: Yes — quench dip of mean amp; 32³ seed-1
     hole annihilation; colormap stretch of a nearly uniform field;
     t=0 winding garbage.
  5. Numbers: Yes — measurements.json. Not a continuum-resolved
     droplet study.
  6. Robust: Partial — two 2D seeds + two 3D seeds, one cheap window.
     Official 64³ Room not rerun.
  7. Code discovers vs asserts: Yes — ndimage.label + pre-registered
     frac/span gates. Synthetic controls in tests/test_one_body_bag.py
     (filled bulk with holes is NOT a bag). Thresholds not edited after
     seeing grown pictures (amp_max_grown vs mean_amp_grown was fixed
     on synthetic blobs so a localized lump is not rejected for having
     low global mean; that was before the TDGL run).
STATUS:      YELLOW / role N primary (asked bag not observed).
             Secondary V: classifier rejects swiss-cheese bulk.
A_OR_B:      (A) faithful TDGL quench from white. Law not derived from 0.
```

## Jobs kept separate

| job | what it is | this report |
|---|---|---|
| **bag / one inside with a skin** | dense connected inside, bounded, persistent | **not observed** |
| vortex-hole relations | pairs, triangles, leftover cores | counted on a **separate card**; not a cell. PR 133 |
| ring pinch 1→2 | loop of holes cinches | not this gate. PR 134 |
| F7 network fission | relation-graph split | not scored |
| torus of the body | balloon vs doughnut of the one inside | **not applicable** (no bounded body). Not required |
| world torus | periodic box | the room, not the body |
| life / cell | — | **refused** |

Vortex cores are **amplitude holes with winding**. They are the opposite of a bag. Dark cores were not scored as the body.

## A-priori bag criterion (frozen)

See `BAG_CRITERION` in `replay.py`:

- local order: `amp_max >= 0.3`
- dense mask: `|ψ| >= 0.5 max|ψ|` (yellow ground)
- exactly one significant dense component (`frac >= 0.02`)
- that component's frac in `[0.02, 0.40]` (not a speck, not the room)
- not percolating (`span_frac < 0.90` on every axis)
- same verdict for `persist_snapshots=5` consecutive snapshots

Not a pass: triangle, ring 1→2, F7, hole count.

Synthetic controls (`tests/test_one_body_bag.py`): filled bulk + two holes → not a bag; localized square → balloon bag; annulus → doughnut topology **measured, not required**; two blobs → not one body; 3D ball vs solid torus.

## Claims vs measurements

### 2D 48² TDGL (pictures; NOT official; NOT the PR 133 triangle job)

Same knobs as g001 defaults. 260 steps, snap every 26, seeds 0 and 1.

**seed 0** (end sha256 `3044c986d0ad4f86…`):

| t | mean | amp_max | dense_frac | n_holes | windings | bag |
|---|---|---|---|---|---|---|
| 0 | 0.0126 | 0.040 | 0.131 | 259 | 598 | no (noise) |
| 13.0 | 0.062 | 0.139 | 0.379 | 9 | 0 | no (`amp_max<0.3`) |
| 15.6 | 0.517 | 0.851 | **0.646** | 7 | 0 | no (room bulk) |
| 26.0 | 0.975 | 1.00 | **0.994** | 3 | 4 | no |

`persistent_one_body = false`. Longest bag run = 0. There is **no window** where a localized lump exists: the field jumps from still-too-small to room-filling.

**seed 1** (end `274c13b996551088…`): same story. End dense_frac 0.995, 3 holes, 4 windings.

t=0 winding counts (~600) are noise-phase garbage (same honesty as PR 134). Not holes of an ordered bulk.

### 3D 32³ TDGL (local-3d size; NOT an official Room)

Runner `local-3d` edge 32, 300 steps, snap every 30. `three_d_authenticity.genuinely_3d = true` on all sampled frames.

**seed 0** (end `5394a782bffb18da…`):

| t | mean | dense_frac | n_holes | xy-windings | bag |
|---|---|---|---|---|---|
| 0 | 0.0125 | 0.053 | 319 | 5663 | no |
| 15 | 0.087 | 0.251 | 2 | 0 | no (`amp_max=0.23<0.3`) |
| 18 | 0.718 | **0.868** | 13 | 0 | no (room bulk) |
| 30 | 0.958 | **0.990** | 49 | 70 | no |

End xy slice: yellow ground, a few dark spots. End xz: dark spots. **A slice with two dark dots is a line piercing a plane, not two bodies and not a bag.** Hole card only.

**seed 1** (end `5bf83b3e7977df94…`):

Late field is almost uniform: t=30 mean 0.997, min 0.989, dense_frac 1.0, holes 0, windings 0. Finite-size annihilation in 32³ (same family as PR 134 grown seed 1). Do not promote to 64³.

**Colormap trap:** `grown3d_s1_end_xy_amp.png` looks contrasty because `render_field` stretches min→max over ~0.989–1.000. The legend PNG `…_dense_holes.png` is flat yellow with a red frame (morphological skin of a **domain-filling** mask = the room's edge, not a body's skin). Physical range, not the stretched heatmap, is the measurement.

## What did NOT happen

- No one bounded persistent dense body on any frame of any seed.
- No balloon/doughnut **body** topology to report (`not_applicable_no_bounded_body`).
- No triangle / ring-pinch / F7 scored as unicellular success.
- No vesicle field, no metabolism field, no inherited tag.
- No official Room write. No 64³ rerun dressed as this check.
- Holes were counted and **not** used to rescue the bag question.

## Repro

```bash
python3 -m pytest tests/test_one_body_bag.py tests/test_research_compass.py -q
python3 ai_lab/reports/easy/verify-20260829-one-body-bag/replay.py
```

Uses: `genesis.models.ginzburg_landau`, `scipy.ndimage.label`,
`genesis.diagnostics.topology3d.three_axis_percolation`,
`genesis.diagnostics.topology_betti.betti3d`,
`genesis.diagnostics.measures.winding_defect_count`,
`tools.snapshot`.

## Discipline

- no_touch: measures.py / official rooms / F-path gates / vortex_lines_3d untouched.
- 第8監査: IC is white. Criterion does not encode a drawn circle. Filling the box fails the bag gate (max_body_frac=0.40).
- Visualization separated from physics. Stretched heatmaps are labeled.
- Deterministic seeds 0 and 1.
- Claim tiers not raised. Compass pin is ORIENTATION, not a measured bag.
- Failures kept: this negative result is the finding.

## Limits (floors)

1. 48² / 32³ are cheap. Official 64³ `room-g001-a` is a tangle of holes in an ordered bulk by stored defect_count (241/173/117) — unread here as a bag, and not recomputed.
2. Core ~1 cell. A thin-skinned droplet, if it existed, would be poorly resolved.
3. Only this white (relaxational TDGL). Other whites (phase-separating Model H, etc.) are **unmeasured** for this question.
4. Persistence window is snapshot cadence (2D Δt=2.6, 3D Δt=3.0), not continuous tracking of an ID.
5. Periodic wrapping uses non-periodic 6-connected label + span_frac. A wrapping body would fail as percolating — correct for "bounded lump".
6. Dense-mask skin on a filling bulk is the domain frame. Do not call that a cell wall.
