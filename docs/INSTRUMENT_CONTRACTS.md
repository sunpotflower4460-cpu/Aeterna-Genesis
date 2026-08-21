# Instrument-Before-Claim Contracts

Aeterna should not answer an unmeasured scientific question by adding a stronger interpretation. When the
current observables cannot distinguish the possibilities, the productive next step is an **instrument**.

`ai_lab/dream/instrument_registry.py` is the machine-readable registry for these measurement gaps.

An instrument contract is not evidence that its target phenomenon exists. It is a promise about how the
repository will measure the question without quietly supplying the desired answer.

## Shared rules

Every autonomous instrument request must:

1. have a registered ID and an explicit capability it is meant to measure;
2. define observables/association rules before inspecting the desired outcome;
3. state matched null/contrast/holdout controls;
4. avoid adding a new physical axiom merely to make the target measurable;
5. avoid seeding target morphology, division position/time, organism, brain or desired X outcome;
6. preserve numerical/non-finite failures as instrumentation status rather than negative physics;
7. keep scaffolded analogy lanes explicitly separate from Pure Genesis evidence;
8. list interpretations that remain blocked even if the measurement is positive.

CI fails if a frontier instrument ID is unregistered, duplicated, seeds target morphology, declares a new
physical axiom, or uses a scaffolded lane without the explicit non-proof boundary.

## Instrument state is not scientific state

The operational backlog distinguishes three importantly different situations:

- `OPEN`: the requested measurement is still missing;
- `MEASUREMENT_ACTIVE`: the instrument now runs, but no scientific lead is implied;
- `CAPABILITY_LEAD_REPORTED`: a predeclared measurement criterion produced a planning lead.

`MEASUREMENT_ACTIVE` is deliberately **not** treated as unresolved engineering debt. Otherwise the autonomous
researcher can request the same already-built instrument forever. Conversely, `CAPABILITY_LEAD_REPORTED` is
still only a research-planning lead; it does not promote a Room, assign an official Level, or convert a
candidate interpretation into physical truth.

## Current registry

### `metric-from-relations`

Measures whether a metric-like geometry can be reconstructed from relation observables. It requires
permutation/label controls, relation-destroying controls and out-of-sample checks. A positive fit is not a
claim of spacetime, gravity, fundamental dimension or geometry from strict nothing.

**Implemented primary lane:** `genesis/diagnostics/relation_structure.py`, attached observation-only to Pure
Genesis R0 by `ai_lab/dream/relation_instrument_adapter.py`.

The primary lane is intentionally stronger than measuring vortex geometry: it consumes the anonymous R0
relation matrix itself, where no coordinate, direction or spatial distance exists. Adjacency is derived only
after evolution from relation magnitudes. The diagnostic then compares graph-distance/ball-growth structure
against anonymous-label permutation, relation-destroying degree-preserving rewires and held-out relations.
The fitted `dimension_candidate` is a graph-growth diagnostic only; even a robust result is not automatically
a physical spatial dimension.

### `identity-continuity`

Measures whether an outcome-independently tracked relation-defined candidate persists as the same candidate
through time. It requires association-shuffle controls and explicit ambiguity for births, deaths, merges
and splits. Persistence is not automatically an organism, cell, self or life.

**Implemented primary lane:** the same relation-only diagnostic layer tracks non-trivial connected relation
components through a predeclared structural signature. Node IDs are not used as persistent identity, and the
whole system is excluded from being called an individual merely because it trivially persists. Shuffled-time
association is retained as a null control. A positive continuity candidate remains a structural persistence
candidate, not an organism or self.

### `damage-recovery`

Measures response to a predeclared perturbation only after persistent identity has been established. It
requires undamaged, sham and matched passive-relaxation controls. Relaxation toward an earlier state is not
automatically healing, homeostasis or living repair.

### `growth-accounting`

Measures persistent extent/complexity increase with explicit accounting of external drive/material/order and
predeclared differentiation metrics. Expansion alone is not metabolism, development or organism growth.

### `predictive-holdout`

Measures held-out prediction/response with frozen features and no future-label leakage. It requires simple
baseline, shuffled-label and fresh-condition transfer controls. Predictive advantage is not automatically
learning, intelligence, agency or a brain.

### `lineage-accounting`

Measures persistent parent identity, persistent daughter identities and predeclared parent-to-daughter
information/accounting. Transient relation-network separation or fragmentation alone is not biological
cell division, reproduction, heredity or life.

**Implemented primary lane:** relation-defined parent/daughter candidates are compared using structural
accounting only after a persistent parent exists. Two daughter candidates must persist into a later frame,
and their accounting must beat unrelated daughter-pair alternatives. Node labels are never accepted as
parent/daughter identity. A positive result is therefore a controlled lineage-accounting candidate, not
biological cell division, reproduction or heredity.

## Relation-instrument integrity boundary

The metric, identity and lineage instruments are observational attachments. They do **not**:

- change the R0 relation update law or its coefficient search;
- change the root event, initial conditions or normalization regulators;
- contribute to `_run_score`, law ranking, Why Gate or Root Integrity acceptance;
- seed a coordinate system, target geometry, body, division site/time or desired outcome;
- promote Rooms or official Emergence Levels.

Production summarizes repeated measurements across top R0 laws and multiple finite sizes. A multi-size
candidate may become a planner `LEAD`; otherwise a successfully running instrument remains `MEASURED`.
Both states retain all blocked interpretations above.

## Production-protocol drift guard

`ai_lab/dream/production_protocol.py` independently parses the actual `strict_goal_loop` command embedded in
`.github/workflows/dream-loop.yml` with the same Adaptive v8 parser used by production.

The contract checks that the deliberately broad research lanes have not been silently disabled:

- broad 2D search,
- native 3D anti-bias search,
- promising-lead follow-up,
- F reference-route control,
- Deep-Time extension,
- open-ended emergence discovery,
- recurrent-X verification,
- Pure Genesis R0 candidate-law search,
- information-yield frontier experiments.

Keeping a lane enabled does **not** require that lane to produce a positive result. This guard protects
coverage/configuration, not scientific success.

## Adding a new instrument

A future agent adding a frontier request should first add a registry entry with:

- capability ID,
- plain scientific question,
- implementation contract,
- required controls,
- blocked interpretations,
- scaffolded-lane policy.

Then add tests that demonstrate the request is start/outcome safe. Only after that should implementation
code be allowed to produce a measured report.

This ordering is intentional: **measurement capability first, scientific interpretation second**.
