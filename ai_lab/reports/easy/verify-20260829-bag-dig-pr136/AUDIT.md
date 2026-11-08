# AUDIT — why the yellow ground fills the room (bag dig, 2026-08-29)

```
MODULE:      verify-20260829-bag-dig  (dated report; NOT a Room)
QUESTION:    PR #135 measured "no bag" from white + TDGL. WHY? Is there ANY start
             (noise roughness, quench speed, final eps) in this same white for which
             a dense inside and a not-dense outside sit next to each other, and does
             the frozen bag gate ever pass?
PUT IN:      genesis/models/ginzburg_landau.py, imported UNMODIFIED (g001 TDGL).
             IC = uniform near-zero + tiny complex noise, optionally low-/high-pass
             filtered in Fourier and renormalised to the SAME rms
             (families white / white_lowk / white_highk — the same declared
             structureless families as ai_lab/dream/fission_path.MINIMAL_RANDOM_FAMILIES).
             Climate knobs pre-declared before the run: quench_duration in {1, 8, 40},
             eps_final in {-1, 0, 0.25, 1}. Grids 48^2 and 32^3. Seeds 0, 1.
             NOT put in: bag, vesicle, membrane field, metabolism field, circle, body
             location, body size, body count, any new field, any edit to existing code.
EMERGED:     Nothing new. Every ordered end state is ONE ground filling the box
             (dense_frac 0.992-1.000). The end amplitude histogram is single-peaked.
             The only surviving low-amplitude cells are phase-winding holes.
             Untargeted concomitants: the quench dip; the transient outside during
             growth; finite-size hole annihilation in 32^3 seed 1 (same family as
             PR #134); the shallow eps=0.25 room merely climbing slowly.
CLAIM TIER:  measured  — dense_frac, component tables, span_frac, persistence runs,
                         20-bin amplitude histograms, winding_defect_count, sha256.
             interpretive — the free-energy reading of WHY (single well, no conservation).
             analogy — cell / life / membrane: REFUSED.
KNOWN MATCH: textbook Model-A (non-conserved) relaxation to a single-well minimum
             |psi| = sqrt(eps); Allen-Cahn curvature-driven shrinking of any amplitude
             dip; Kibble-Zurek defect density falling with slower quench (reproduced:
             qd=1 leaves more hole patches than qd=40). docs/WHITE_CEILINGS.md g001 L2.
             The repo already states the mechanism in
             genesis/models/mass_conserved_3d.py: "the '+' state invades and FILLS the
             domain ... A conserved total forbids that front-invasion".
STATUS:      YELLOW / role N primary (asked bag NOT observed, now with a stated reason).
             Secondary V: the qd-dependence of the hole count reproduces Kibble-Zurek.
A_OR_B:      (A) faithful existing field law. The law is still put in by hand.
```

## The frozen gate — copied, not retuned

`BAG_CRITERION` in `replay.py` is a **verbatim copy** of
`ai_lab/reports/easy/verify-20260829-one-body-bag/replay.py` (PR #135). Values unchanged:

| key | value | meaning |
|---|---|---|
| `amp_max_grown` | 0.3 | local order above the noise floor |
| `dense_rel_max` | 0.5 | dense (yellow) = `|psi| >= 0.5 max|psi|` |
| `min_body_frac` / `max_body_frac` | 0.02 / 0.40 | not a speck, not the room |
| `max_span_frac` | 0.90 | not wrapping the box |
| `persist_snapshots` | 5 | consecutive bag frames required |
| `hole_rel_max` | 0.25 | holes — a **separate card**, never a bag |

Not a pass, then and now: `triangle`, `ring_pinch_1_to_2`, `F7`, `hole_count_as_body`,
and newly declared explicitly: `coexistence_alone`.

**A second, separate ruler** was added and declared *before* the run:
`OUTSIDE_CRITERION = {outside_rel_max: 0.5, min_outside_frac: 0.10}`. It answers only
"is there still an outside at all?". It **cannot make a bag pass** and is never combined
with the bag gate. `measurements.json` carries
`outside_criterion_is_not_a_bag_pass: true`.

## Results — 32 runs (30 distinct configurations; the white/qd=8/eps=1 pair is listed in both group A and group B), 0 bag frames

`cases_with_any_bag_frame = 0`. `cases_with_persistent_bag = 0`. Longest bag run = 0 everywhere.

### A. noise roughness x cooling speed (2D 48^2, eps_final = 1)

| family | qd | seed | dense_frac end | outside end | hole patches | windings | sha256[:16] |
|---|---|---|---|---|---|---|---|
| white | 1 | 0 | 0.995 | 0.005 | 0 | 4 | fbeb3069212b5cdf |
| white | 1 | 1 | 0.993 | 0.007 | 4 | 6 | a76a4a64a79c4c44 |
| white | 8 | 0 | 0.998 | 0.002 | 1 | 2 | 9c30d84b7e948190 |
| white | 8 | 1 | 0.995 | 0.005 | 0 | 4 | a7a7edb633518061 |
| white | 40 | 0 | 0.997 | 0.003 | 0 | 2 | 2204b5e3a29597a5 |
| white | 40 | 1 | 0.998 | 0.002 | 1 | 2 | 3a1138f0e5b6f9bf |
| white_lowk | 1 | 0 | 0.997 | 0.003 | 1 | 4 | 90a9a26bffe7de52 |
| white_lowk | 1 | 1 | 0.992 | 0.008 | 4 | 6 | 3e28bbb6edff5b97 |
| white_lowk | 8 | 0 | 0.997 | 0.003 | 1 | 2 | 572f5fbdfdeb972d |
| white_lowk | 8 | 1 | 0.995 | 0.005 | 2 | 4 | bec4ffdaba81ab6f |
| white_lowk | 40 | 0 | 0.997 | 0.003 | 0 | 2 | 824ee9dc9bb82447 |
| white_lowk | 40 | 1 | 0.998 | 0.002 | 2 | 2 | a2dd2c745d31a2cc |
| white_highk | 1 | 0 | 0.996 | 0.004 | 3 | 4 | 5dfa6ec203e10583 |
| white_highk | 1 | 1 | 0.996 | 0.004 | 4 | 4 | 1345d15051883280 |
| white_highk | 8 | 0 | 1.000 | 0.000 | 0 | 0 | 9fcb0f6b7e005aa7 |
| white_highk | 8 | 1 | 0.996 | 0.004 | 2 | 4 | c17a98c5d4301932 |
| white_highk | 40 | 0 | 1.000 | 0.000 | 0 | 0 | d9edda14add06a1e |
| white_highk | 40 | 1 | 1.000 | 0.000 | 0 | 0 | 97d250582d315939 |

Roughness moves the hole count a little and the ending not at all. Cooling speed moves the
hole count the expected (Kibble-Zurek) way — faster quench, more holes — and the ending not
at all. **Every ordered case fails the bag gate with the same reason string:**
`room_bulk (dense side larger than max_body_frac)`.

### B. the room's switch (2D 48^2, white, qd = 8)

| eps_final | seed | amp_max end | dense_frac end | bag reason at end |
|---|---|---|---|---|
| -1.0 | 0 | 1.39e-17 | (meaningless) | `nothing_grew (amp_max < 0.3)` |
| -1.0 | 1 | 1.10e-17 | (meaningless) | `nothing_grew` |
| 0.0 | 0 | 8.05e-04 | (meaningless) | `nothing_grew` |
| 0.0 | 1 | 6.58e-04 | (meaningless) | `nothing_grew` |
| 0.25 | 0 | 0.466 | 0.805 | `room_bulk` (still climbing at t=38) |
| 0.25 | 1 | 0.452 | 0.815 | `room_bulk` (still climbing) |
| 1.0 | 0 | 1.000 | 0.998 | `room_bulk` |
| 1.0 | 1 | 1.000 | 0.995 | `room_bulk` |

**Honesty note on eps <= 0:** the dense/hole masks are *relative* to `max|psi|`, so on a field
that decayed to ~1e-17 (eps=-1) or ~1e-3 (eps=0) they report `dense_frac ~ 0.45` and a couple of "hole patches".
Those numbers are noise-floor garbage and carry no meaning — exactly the same honesty as
PR #135's t=0 winding count of ~600. `local_order = false` is what the gate actually uses.

The physical content of this table: **eps chooses "all outside" or "all inside". There is no
setting of it at which the two sit next to each other.** That is the switch with no middle.

### C. small 3D (32^3, qd = 8, eps = 1) — NOT an official Room

| family | seed | dense_frac end | hole patches | windings | sha256[:16] |
|---|---|---|---|---|---|
| white | 0 | 0.994 | 35 | 43 | 75d6e9f7d18f5a61 |
| white | 1 | 1.000 | 0 | 0 | a09666bdedf5f862 |
| white_lowk | 0 | 0.993 | 35 | 45 | b112e0ebae3ee40a |
| white_lowk | 1 | 1.000 | 0 | 0 | 54a88677ee829e9e |

Seed 1 annihilates all defects in the small box (same finite-size effect PR #134 reported;
do not promote to 64^3). Seed 0 keeps 35 hole patches in a filled bulk. Slices show dark dots
where vortex **lines pierce the plane** — not bodies, not a bag.

### D. the one loose end, closed

The shallow eps = 0.25 room was the ONLY configuration whose *end frame* still had an outside
(19.5%). Run to t = 408 instead of t = 38: `dense_frac = 1.000`, `outside_frac = 0.000`.
It was not coexistence, it was a slow climb. Kept in the record rather than dropped.

### The transient outside

`cases_with_a_transient_outside_while_amplitude_climbs = 21` of 32 runs;
`cases_where_outside_still_there_at_end = 2` (both closed by run D).
An outside exists only while the single ground is still filling in. It is a stage of one
ground, not two grounds. It was **never scored as a bag**, and `NOT_SUCCESS` names
`coexistence_alone` explicitly.

### The histogram

`amp_hist_20_rel` at the end frame is single-peaked in every ordered case (`fig09`).
A bag needs two peaks that both stay. There is only one well to fall into:
`V(|psi|) = -eps|psi|^2/2 + |psi|^4/4` has a single minimum at `|psi| = sqrt(eps)`
for `eps > 0` and at `0` for `eps <= 0`. Never two at once. And the dynamics is
**non-conserved** (Model A) — no bookkeeping forces any part of the box to stay low.
Those two facts, not the seed / roughness / cooling / resolution, are the reason.

## Official Rooms re-read with bag eyes (`official_room_reread.json`)

Nothing recomputed, nothing written back, no official file modified.

### room-g001-a (official, 3D, physics grid 64^3)

- The official record's `reached_level: 2`, `localization: true`, `defect_count: 241`
  is a **hole count**. `rooms/official/room-g001-a/diagnostics.yaml` states
  `level_2: winding_defect_count`. 241 is not 241 bodies.
- The word "localization" there means a *defect* is localized, not a *body*.
- `runs/seed-0000/summary.json` `final_mean_amplitude = 0.973843` against an equilibrium of
  exactly 1.0 for `eps_final = 1`: **the ordered ground occupies ~97% of the physics box.**
  This is a physics-grade number and it alone settles the bag question: `room_bulk`.
- The only stored *field* is the display lens: `grid [20,20,20]`,
  `downsample: scipy.ndimage.zoom(order=1)`, `quantized_uint8: true`. Scored on it:
  `dense_frac 0.983`, one dense component with `span_frac [1.0, 1.0, 1.0]`.
  **Display grade.** Adequate for "does the dense side fill the box" (a bulk property);
  **not** adequate for counting holes or resolving a thin skin. **The 64^3 run was not rerun.**
- Verdict: **not a bag.** Holes were not counted as bodies anywhere in this re-read.

### room-g003-a (official, 2D Model H, physics grid 128^2)

- Already-existing phase-separating white. Two grounds (`phi ~ +-0.73`), sharp interface,
  mass conserved to machine precision, grown from uniform + noise.
- Re-read on the stored `composition` lens (48^2 display grade):
  `plus_frac 0.4965`, `minus_frac 0.5035`, `interface_frac 0.338`,
  14 plus-components, largest `span_frac [0.79, 0.88]`.
- **An outside genuinely survives here** — the thing that never survived in g001.
- Still **not a bag**: at `mean_phi = 0` each ground is ~half the box (over
  `max_body_frac = 0.40`) and the majority ground is not one lump. Bicontinuous.
- **Coexistence alone is not promoted to a bag.** Declared in `NOT_SUCCESS`.

## Mixing audit — is the "one body with a skin" logic entangled with hole / triangle logic?

| module | what it counts | mixed with the bag? |
|---|---|---|
| `genesis/diagnostics/measures.py::winding_defect_count` | holes (phase winding, masked to ordered bulk) | no. But it *is* the content of official Level 2 |
| `genesis/diagnostics/measures.py::assess_level` | Level 2 from `defects > 0 and persistent` | no code mixing; the **name** "localization" is the trap |
| `genesis/diagnostics/higher_levels.py::assess_individuality_level` | spot count, area fraction, self-healing, size-independence | **clean** — never reads a winding count |
| `genesis/diagnostics/higher_levels.py::assess_self_propulsion` | single-body count, compactness, drift randomness | **clean** — and already carries the replication-drift trap guard |
| `genesis/diagnostics/geometry_events.py` | triangles / triads of **vortex points** (holes) | lane 2. Never consulted by any bag logic |
| `genesis/diagnostics/relation_structure.py` | anonymous relation graph, `_triangle_count` | lane 2/3. Its own docstring refuses organism/cell/life |
| `ai_lab/dream/fission_path.py` (F0..F7) | F2 = `reached_level >= 2` = **holes exist**; F3..F7 are relations among those holes | **the whole F ladder stands on lane 2.** It declares `network_fission_is_biological_cell_division: false` and `triangle_is_required: false` |
| PR #135 `verify-20260829-one-body-bag/replay.py::classify_amp` | dense components decide `one_bounded`; hole rows go to a separate key | **clean, not mixed** |

**Findings, reported not patched:**

1. `localization` in official Level 2 means a *hole* is localized. Read from
   `emergence.json` alone (`"localization": true`, `"defect_count": 241`) it slides toward
   "241 localized bodies". `diagnostics.yaml` disambiguates it; `emergence.json` does not.
2. The F0->F7 ladder's floor is holes, so **F7 can never be evidence for the bag lane**,
   however deep it goes. The code says so; keep that line.
3. No existing gate was widened. **No existing file was modified by this report.**
   The only new code is this report's own `replay.py`, `reread_official_rooms.py`,
   `tinyfont.py` (a font for the legends).

## Already-existing phase-separating / two-ground / interface fields (nothing added)

| file | two grounds? | conserved? | interface grown or placed? | usable for the bag lane |
|---|---|---|---|---|
| `genesis/models/model_h.py` (g003, **official Room**) | yes (`phi ~ +-0.73`) | yes, machine precision | **grown** from uniform + noise | **best existing candidate** |
| `genesis/models/mass_conserved_3d.py` | activator/inhibitor | yes, exactly | ball settles, but IC is a **placed symmetric bump** | localization is placed, not grown |
| `genesis/models/mass_conserved_nr_3d.py` | as above + slow `w` | yes | placed bump; recorded null (moves => fragments) | not the bag lane |
| `genesis/models/three_component_rd.py` | dissipative soliton | no | placed bump; record says "'+' invades and fills" | existence itself is frontier |
| `genesis/models/gray_scott.py` | spots | no | seeds placed; spots replicate | **no inheritance. Spots are not cells. Not promoted** |
| `genesis/models/nematic_qtensor.py` | fixed droplet `phi` | — | **shape PLACED** (module says so) | validator only, not evidence |
| `genesis/diagnostics/vessel_permeability.py` | fixed tanh sphere | — | **vessel PLACED deliberately** (module says so) | validator only, not evidence |

**A new phase-separating field does NOT need to be added — one already exists (g003).**
Nothing was implemented for it in this report.

## What did NOT happen

- No bounded persistent dense body on any frame of any of the 32 runs.
- No bag / vesicle / membrane / metabolism field, no circle, no body location or size in any IC.
- No triangle, ring-pinch, or F7 scored, hunted, or claimed.
- No hole count used to rescue the bag question.
- `ai_lab/discoveries/goal_progress.json` **read only**. All 10 required items remain
  `satisfied: false`, `progress_fraction: 0.0`, `goal_reached: false`. Not edited, not claimed.
- No official Room file written. No 64^3 rerun. No new Room registered.
- No existing repo module changed.
- No life / consciousness / universe / new-law language.

## Repro

```bash
python3 ai_lab/reports/easy/verify-20260829-bag-dig/replay.py
python3 ai_lab/reports/easy/verify-20260829-bag-dig/reread_official_rooms.py
```

Needs `numpy`, `scipy` (`requirements.txt`). Deterministic: seeds 0 and 1, explicit Euler,
`dt = 0.1`, `Du = 1.0`, end-field sha256 recorded per case in `measurements.json`.

Uses: `genesis.models.ginzburg_landau`, `genesis.diagnostics.measures.winding_defect_count`,
`scipy.ndimage.label`, `tools.snapshot.colormap/write_png`.

## Limits (floors, stated not hidden)

1. 48^2 and 32^3 are cheap exploration grids. Not Rooms. The official 64^3 was **not** rerun.
2. Only the g001 relaxational TDGL white. The claim "no bag" is about **this white**, not
   about physics. g003 Model H is measured here only through its stored display lens.
3. Vortex cores are ~1 cell wide at this resolution; a thin skin, if one existed, would be
   poorly resolved. The bulk statement (`dense_frac -> 1`) does not depend on that.
4. Persistence is measured at snapshot cadence (11 snapshots per run), not by tracking an ID.
5. The periodic box is labelled with a non-periodic 6-connected labeller plus `span_frac`;
   a body that wrapped the box would be rejected as percolating — correct for "bounded lump".
6. Filtered noise (`white_lowk` / `white_highk`) is weaker zero-purity than plain white,
   because it imposes a declared correlation scale. It places no object. Recorded as such.
7. The single-well / non-conserved reading of *why* is `interpretive`. What is `measured`
   is the single-peaked histogram and `dense_frac -> 1` across every knob tried.
