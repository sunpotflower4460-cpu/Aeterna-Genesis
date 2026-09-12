# AUDIT — independent 3D ring-pinch check (not an official Room)

```
MODULE:      verify-20260829-ring-pinch (non-official dated report; not a Room)
QUESTION:    Can this physics show one ring-like vortex (a closed loop of
             winding) persisting as one, cinching, then becoming two
             separately trackable loops?
PUT IN:      (A) grown: g001 TDGL + undifferentiated uniform+noise IC, 32^3
             local-3d, seeds 0 and 1, t=0 uninterrupted.
             (B) placed diagnostic: one circular vortex-ring imprint
             (same phase as core.field.vortex_ring_phase), no waist, no
             figure-8, no seeded split site/time. TDGL eps=+1 and a short
             GPE split-step. Labeled 置いた.
             Official 64^3 Room was READ, not rerun.
EMERGED:     Placed circular ring traces as ONE closed bulk loop and stays
             one (TDGL: radius 8.51→5.43 shrink; GPE: radius ~7 persist).
             Grown 32^3: no isolated bulk closed loop that then becomes two.
             Official stored 64^3: 241/173/117 xy-plaquette piercings =
             vortex-line tangle, not one ring.
CLAIM TIER:  measured (loop counts, radii, hashes, 3D authenticity, heatmaps).
             interpretive: tracer 1→0 blinks on the placed ring are
             discretization dropouts, not fission. analogy: cytokinesis
             (explicitly refused).
KNOWN MATCH: e003 placed GPE ring self-propagates as one; e008 3D KZ lines
             mostly wrap the torus (contractible fraction ~0.30); e009
             Hopf-linked rings shrink; e026 dynamic pinch is frontier;
             WHITE_CEILINGS g001 TDGL ceiling L2 (no momentum).
AUDIT (7):
  1. Rule does not name the result: Yes — TDGL / GPE local laws. Pinch is
     observed after the fact against an a-priori 1→2 criterion.
  2. Faithful physics: Yes — existing g001 stepper and e003 GPE split-step.
     GPE FFT is a shortcut (fidelity lower than local×parallel).
  3. Result not in IC (grown): Yes — white noise, no ring.
     Placed lane: the RING is in the IC (置いた). The SPLIT is not.
  4. Untargeted concomitants: Yes — tracer seam-open paths; TDGL ring
     shrinkage; GPE boundary sheet; 32^3 seed-1 defect annihilation;
     colormap stretch of a nearly uniform field.
  5. Numbers: Yes — see measurements.json loop tables. Not a
     continuum-resolved Crow-instability proof.
  6. Robust: Partial — two grown seeds + two placed whites (TDGL, GPE).
     One cheap 32^3 window. Official 64^3 not rerun.
  7. Code discovers vs asserts: Yes — genesis.diagnostics.vortex_lines_3d
     + a-priori isolated-1-then-2 criterion. No threshold edit after
     seeing pictures.
STATUS:      YELLOW / role N primary (the asked 1→2 pinch-split was not
             observed). Secondary V (placed ring is hostable and countable
             as one loop) and F (whether a 64^3 tangle contains a 1→2
             event is unmeasured).
A_OR_B:      Grown = (A) faithful TDGL quench from white. Placed = capability
             check, not emergence. Law not derived from 0.
```

## Jobs kept separate

| job | what it is | this report |
|---|---|---|
| triangle of 3 point vortices | sitting / 3-way meeting | PR 133 / F4. Not re-run. |
| two leftover point cores on a plane | ± pair, or a meridional slice of ONE ring | measured as a picture-trap, not scored as split |
| ring pinch 1→2 | one closed loop cinches into two trackable loops | **not observed** |
| F7 network fission | relation-graph split | not cell division; not this gate |
| cytokinesis / cell division | bag + metabolism + inheritance | **refused even if 1→2 had appeared** |

Vortex cores here are **amplitude holes with winding**, not dense high-amp blobs.

## Claims vs measurements

### Official Room `room-g001-a` (stored; 64^3 not rerun)

| item | stored | this report | tier |
|---|---|---|---|
| law / IC | g001 TDGL, uniform+noise 0.01, no ring | read as-is | — |
| dimension | full-3D 64^3, 700 steps | not recomputed | measured (ledger) |
| reached_level | 2; candidate 3 | same | measured (ledger) |
| defect_count seeds 0/1/2 | 241 / 173 / 117 | same | measured (ledger) |
| isolated 1-ring → 2-rings | not a Room diagnostic | **cannot be read from defect_count**; tangle scale | interpretive |
| display field.json | 20^3 uint8, interpolated_for_display | PNGs labeled display-only | not physics |

Honest reading: hundreds of xy-plaquette piercings is a **line tangle**, not one ring. Official L3 (motion / reconnection) remains candidate. A tangle reconnection is not the asked isolated ring-pinch.

### Grown local-3d 32^3 TDGL (育った; NOT an official Room)

Same genesis knobs as the Room (`noise_amplitude=0.01`, quench duration 8, `dt=0.1`), edge 32, 280 steps.

**seed 0** (endpoint sha256 `5bea36a56a305d49…`):

| t | mean_amp | xy_plaquette_defects | n_loops_bulk | n_open_paths |
|---|---|---|---|---|
| 0 | 0.0125 | 5663 (noise) | 0 | 5357 |
| 8–16 | ~0 | 0 | 0 | 0–7 |
| 18.6 | 0.83 | 41 | 0 | 12 |
| 28 | 0.955 | 76 | 0 | 29 |

`three_d_authenticity.genuinely_3d = true` (z_variation_fraction 0.186). Official assess_level = 2.

**No isolated bulk closed loop at any sampled frame** (criterion `min_n_points=8`, `min_length=8`). Open paths at late times are consistent with the tracer's documented refusal to close across the periodic seam (wrapping lines). e008's independent 3D KZ harvest already reported most lines wrap the torus (contractible fraction ~0.30).

Human xy/xz slices at the end show a few dark holes. Those are **line piercings of a plane**, not two daughter rings. `ring_pinch_split_observed = false`.

**seed 1** (endpoint sha256 `34409ae5d17b5ed9…`):

Late field is almost uniform: mean_amp 0.996, amp_min 0.981, amp_std 0.0027, xy_defects 0, n_open 0, assess_level 1 (defects did not persist). A t=0 “loop” of effective radius 1.42 among 42 raw loops / 5442 open paths at mean_amp 0.012 is **noise-winding garbage**, not a grown ring.

**Colormap trap:** `grown_s1_end_xy_amp.png` looks contrasty because `render_field` stretches min→max. The physical range is 0.981–~1. That picture is **not two vortices**.

32^3 finite-size: this seed's tangle annihilated. Official 64^3 of the same seed family keeps 117–241 piercings. Do not promote 32^3 annihilation to a 64^3 claim.

### Placed circular ring, TDGL 32^3 R=8 (置いた capability)

`quench_duration=0` so eps=+1 (ordered background). Tiny 10⁻³ complex noise; **no waist, no figure-8, no seeded pinch coordinate**.

| t | n_loops_bulk | n_open | R_eff | length |
|---|---|---|---|---|
| 0 | 1 | 0 | 8.51 | 53.5 |
| 4.0 | 1 | 0 | 7.61 | 47.8 |
| 8.0 | 1 | 0 | 7.23 | 45.5 |
| 12.0 | 1 | 0 | 6.33 | 39.8 |
| 16.0 | 1 | 0 | 5.43 | 34.1 |

`ring_pinch_split_observed = false`. `max_bulk_loops_in_series = 1`.

Frames with n_loops_bulk=0 (t=0.8, 9.6–10.6, 15.2) coincide with n_open_paths=8–16. That is the tracer's known tangent/grazing dropout (module docstring: dangling-face healing; does not close every discretization gap). The loop is present again on the next samples and at the end. **`collapse_1_to_0_after_isolated_one=true` is a criterion flag on those dropouts, not a physical 1→0 annihilation.** Do not quote it as “the ring died.”

`winding_defect_count` (xy plaquettes summed over z) stays **0** for this ring. A ring lying in a z=const plane pierces **xz/yz** faces, so the official Room Level-2 proxy can **miss** it. Loop tracing is the right instrument for this question.

Picture language (t=0): xy mid-slice = **one dark circle**; xz/yz = **two dark dots**. Blob counts: xy 1, xz 2, yz 2. That is ONE ring. At late times the blob counter on xz rises (periodic wrap + core pixels); the **xy picture and the tracer still say one loop**. Do not promote extra dark pixels on a meridional slice into two rings.

`three_d_authenticity.genuinely_3d = true` (z_variation 0.339).

Core resolution: ξ ~ 1 cell. `3D_NATIVE_POLICY` asks cells_per_core_radius ≥ 8. This is a **coarse host check**, not a converged Crow-instability study.

### Placed circular ring, GPE 32^3 R=7 (置いた; FFT shortcut)

Same imprint family as e003 / e059. Spectral split-step = shortcut (AGENTS.md: answer can be right, “how it happens” fidelity is lower).

| t | n_loops_bulk | n_open | R_eff |
|---|---|---|---|
| 0 | 1 | 0 | 7.01 |
| 1.6 | 1 | 0 | 7.01 |
| 8.0 | 1 | 0 | 7.23 |
| 16.0 | 1 | 28 | 7.23 |

Never 2 bulk loops. Open-path growth and late xy_plaquette_defects=16 match e003's honesty floor (non-periodic z imprint seeds a boundary sheet; sound). Radius does **not** shrink like TDGL — expected for Hamiltonian GPE vs relaxational TDGL.

`ring_pinch_split_observed = false`.

## What did NOT happen

- No 1 closed bulk loop → 2 persistent closed bulk loops on any lane.
- No cytokinesis, cell, bag, metabolism, inheritance.
- No F7 / network fission claim.
- No new law, no official Room write, no 64^3 rerun dressed as this check.
- No 2D 48² leftover-two-core redo scored as a ring split.
- Split location / target morphology / figure-8 were not placed.
- Dense high-amp blob fission was not the lane (not seen).

## A-priori pinch criterion (not retuned)

See `PINCH_SPLIT_CRITERION` in `replay.py`: isolated n_loops_bulk==1 for ≥3 sampled frames (n_open≤2), then isolated n_loops_bulk==2 for ≥3 frames. Tangle, 1→0, two dots on a slice, and F7 are listed as non-passes **before** this run.

## Repro

```bash
python3 ai_lab/reports/easy/verify-20260829-ring-pinch/replay.py
```

Uses: `genesis.models.ginzburg_landau.step`, `genesis.diagnostics.vortex_lines_3d.trace_vortex_lines`, `genesis.diagnostics.topology3d.three_d_authenticity`, `genesis.diagnostics.measures`, `core.field` 3D GPE split-step, `tools.snapshot`.

## Discipline

- no_touch: measures.py / official rooms / F-path gates / vortex_lines_3d heuristics untouched.
- 第8監査: grown IC is white. Placed lane encodes a **ring**, not a **split**; role of that lane is V/capability, not E.
- Visualization separated from physics. Official 20^3 display volume is not used for loop counts.
- Deterministic seeds 0 and 1 (grown); placed TDGL noise seed 0.
- Claim tiers not raised. F-stages ≠ Emergence Levels. L3 remains candidate on the official Room.
- Failures kept: no pinch-split; 32^3 seed-1 defect-free end; tracer blinks; colormap stretch.

## Limits (floors)

1. 32^3 is cheaper than official 64^3; wrapping lines are under-closed by the tracer.
2. Core ~1 cell: pinch physics (Crow / self-reconnection) is not resolved if it needs a thin neck of many cells.
3. Neck min-self-distance in the JSON (~2.8) is a local chord on a dense polyline, **not** a waist diameter — unused as evidence.
4. Blob counts on slices overcount at coarse cores; pictures + tracer beat the blob counter.
5. GPE lane is FFT, not local hops.
6. Whether some loop in the official 64^3 tangle ever goes 1→2 is **unmeasured**.
