# Instrument-Before-Claim Contracts

Aeterna should not answer an unmeasured scientific question by adding a stronger interpretation.  When the
current observables cannot distinguish the possibilities, the productive next step is an **instrument**.

`ai_lab/dream/instrument_registry.py` is the machine-readable registry for these measurement gaps.

An instrument contract is not evidence that its target phenomenon exists.  It is a promise about how the
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

## Current registry

### `metric-from-relations`

Measures whether a metric-like geometry can be reconstructed from relation observables.  It requires
permutation/label controls, relation-destroying controls and out-of-sample checks.  A positive fit is not a
claim of spacetime, gravity, fundamental dimension or geometry from strict nothing.

### `identity-continuity`

Measures whether an outcome-independently tracked relation-defined candidate persists as the same candidate
through time.  It requires association-shuffle controls and explicit ambiguity for births, deaths, merges
and splits.  Persistence is not automatically an organism, cell, self or life.

### `damage-recovery`

Measures response to a predeclared perturbation only after persistent identity has been established.  It
requires undamaged, sham and matched passive-relaxation controls.  Relaxation toward an earlier state is not
automatically healing, homeostasis or living repair.

### `growth-accounting`

Measures persistent extent/complexity increase with explicit accounting of external drive/material/order and
predeclared differentiation metrics.  Expansion alone is not metabolism, development or organism growth.

### `predictive-holdout`

Measures held-out prediction/response with frozen features and no future-label leakage.  It requires simple
baseline, shuffled-label and fresh-condition transfer controls.  Predictive advantage is not automatically
learning, intelligence, agency or a brain.

### `lineage-accounting`

Measures persistent parent identity, persistent daughter identities and predeclared parent-to-daughter
information/accounting.  Transient relation-network separation or fragmentation alone is not biological
cell division, reproduction, heredity or life.

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

Keeping a lane enabled does **not** require that lane to produce a positive result.  This guard protects
coverage/configuration, not scientific success.

## Adding a new instrument

A future agent adding a frontier request should first add a registry entry with:

- capability ID,
- plain scientific question,
- implementation contract,
- required controls,
- blocked interpretations,
- scaffolded-lane policy.

Then add tests that demonstrate the request is start/outcome safe.  Only after that should implementation
code be allowed to produce a measured report.

This ordering is intentional: **measurement capability first, scientific interpretation second**.
