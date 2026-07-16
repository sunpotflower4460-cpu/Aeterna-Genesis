# Phenomenon Atlas — controlled vocabulary (Loop-Trinity integration, Phase LT-4)

**Docs-only.** This defines a controlled vocabulary for *what happened in a run*, on an axis **separate** from
the existing role `E/V/S/N/F/Q` (which classifies *what kind of experiment it is*). No schema is changed here;
§4 proposes an additive, optional `phenomena` block for a **separate** future PR. Nothing existing is touched.

## Why a separate axis
`role` answers "is this pure emergence / validation / synthesis / negative / frontier / quality?". It does not
capture the *observed dynamical phenomenon* (a slip, a merge, a plateau). Loop's atlas keeps these apart so a
run can be, e.g., role **S** with observed phenomenon `single_slip_merge` and interpretive
`memory_biased_basin_selection_candidate`. Mixing them loses information and invites over-claiming.

## Evidence tiers (each tag is filed under exactly one)
- **measured** — a number with a known-answer-calibrated observer behind it (e.g. `phase_slip` timed from a
  winding change confirmed by the reliability observer).
- **observed** — seen in a run but not yet control-separated / calibrated.
- **interpretive** — a reading that needs a matched control or more evidence before it is measured.
- **frontier** — a target phenomenon not yet reached.
- **limitations** — scope caveats that qualify the above (e.g. `x_line_winding_only`, `central_slice_only`,
  `2d_only`, `reliability_limited`, `single_seed`).

## Vocabulary (extensible; add via this file first)
### Phase / synchronization
`phase_locking` · `phase_drift` · `phase_slip` · `single_slip_merge` · `synchronized_slip_candidate`

### Structure / identity
`structural_convergence` · `structural_identity_collapse` · `near_identity` · `field_flattening`
· `common_attractor_relaxation_candidate` *(the key confound: both fields fell into one attractor, no interaction)*

### Topology
`topology_preserved` · `topology_annihilated` · `topological_frustration_plateau` · `winding_recovery_candidate`
· `winding_recovery_clean` *(dominant_fraction ≥ preregistered AND invalid_fraction ≤ preregistered)*

### Memory / slow field (all **candidate** until matched-control + non-copy verified)
`memory_biased_basin_selection_candidate` · `field_rewrites_slow_field_candidate`
· `slow_field_rewrites_field_candidate` · `memory_copy_collapse` · `memory_detachment` · `trace_saturation`

### Relation (meeting ≠ maintenance)
`no_meeting_observed` · `transient_interaction_candidate` · `maintained_distinct_interaction_candidate`
*(requires: initial distinctness, matched OFF control separation, guardrails intact, finite maintained window)*

### Reliability / numerical
`reliability_limited` · `numerical_instability` · `energy_instability`

## Usage rules (the discipline, enforced by convention now, by schema later)
1. **Strong-claim tags require a matched OFF control.** `mutual_*`, `restores_*`, `causes_*`,
   `*_rewrites_*`, `maintained_distinct_interaction_candidate` may **not** be filed as `measured`/`observed`
   without a recorded matched control (same layout/seed/horizon/dt/res, mechanism off) whose ID is cited.
2. **A shrinking raw distance is not `structural_convergence`.** Use the gauge-aligned `aligned`/`invariant`
   distance (LT-1); if both fields merely relaxed to one attractor, the tag is
   `common_attractor_relaxation_candidate`, not an interaction. (The second audit question:
   「関係したのか、ただ同じ attractor へ崩れただけか？」)
3. **`winding_recovery_clean` needs the reliability observer** (LT-2): dominant winding over VALID lines with
   high dominant_fraction AND low invalid_fraction — never "final majority is W=1" alone.
4. **Plaquette counts are not identity.** `structural_convergence` may not rest on matching plaquette totals
   (LT-3); use the position-aware map distance and keep volume-Betti vs phase-defect separate.
5. **No life/mind/self words.** These tags are dynamical descriptors; interpretive spiritual/relational
   language stays out of measured/observed and is handled by the tier ladder, not this vocabulary.

## §4 — compatibility proposal (NOT applied here; a separate schema PR)
An additive, **optional** block on `experiment.yaml`, kept orthogonal to `role`:
```yaml
phenomena:
  measured: [phase_slip]
  observed: [common_attractor_relaxation_candidate]
  interpretive: [memory_biased_basin_selection_candidate]
  frontier: [maintained_distinct_interaction_candidate]
  limitations: [x_line_winding_only, single_seed]
controls:
  matched_control_ids: []          # required if any strong-claim tag is measured/observed
  comparison_rule: ""
```
Constraints for that future PR (so legacy stays valid): **all fields optional**; `experiment.schema.json` gains
one optional `phenomena` property (its current `additionalProperties:false` otherwise rejects it); a validator
enforces rule 1 (strong-claim ⇒ `matched_control_ids` non-empty); tags restricted to this vocabulary with an
`unknown_tag` escape hatch that warns, not fails. **Do not** implement the schema change until this vocabulary
is reviewed — per the integration directive (docs-only first, schema PR separate).

## Status
Vocabulary: **defined (docs-only).** Schema field: **proposed, not implemented.** Adoption: experiments may
begin citing these tags in their AUDIT.md prose now; machine metadata waits for the reviewed schema PR.
