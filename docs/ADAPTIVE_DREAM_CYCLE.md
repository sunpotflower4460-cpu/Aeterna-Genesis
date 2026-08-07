# Adaptive Dream Cycle v2

## Purpose

Aeterna optimizes for **discovery**, not raw trial count.  Four bounded research cycles per JST day form one connected scientific conversation:

- 03:17 — Cycle A
- 09:17 — Cycle B
- 15:17 — Cycle C
- 21:17 — Cycle D

Each cycle reads the previous report, chooses a search mix, runs experiments, updates compact memory, and writes the next research decision: **"this happened; therefore next try this."**

The Research Director is allowed to choose **where to search next**. It is not allowed to change Levels, success thresholds, physics evaluators, official Rooms, or the coarse/full-3D human approval gates.

## Daily default budget

Per cycle:

- Mass 2D: 2,048 direct t=0 trials
- Native 3D discovery: 100 direct t=0 Local-3D trials
- selected fresh-seed reproduction
- selected post-discovery paired 2D comparison for the strongest Native-3D trials
- a small existing orchestrator lane for recorded promotion evidence

Per day this targets roughly **8,192 Mass-2D + 400 Native-3D trials**, before reproduction/promotion work.

## Native 3D is independent

Native 3D is not a promotion from 2D. It starts directly at t=0 in a three-dimensional grid. A 2D result cannot veto it.

For a strong direct-3D observation, Aeterna may later run the same condition in 2D to understand dimensional dependence. That paired 2D run is **post-discovery evidence**, never a prerequisite.

This makes the following state legitimate and important:

```text
2D: weak / unknown
3D: interesting
```

If a paired comparison gives a deeper measured Level in 3D, the Night Report records it as a dimension-emergence candidate.

## Research Director anti-bias contract

The Director must keep several mutually competing explanations alive. Every decision includes:

- current hypothesis
- null hypothesis
- dimension-specific alternative
- parameter-confound alternative
- an explicit test that could weaken each explanation

Search budget has hard code-level constraints:

- at least 20% unexplored/global coverage
- at least 10% Assumption Breaker
- at least 10% random search
- no more than 35% hypothesis exploitation

A crucial asymmetry is deliberate: **when a belief becomes stronger, the challenge budget increases.** The Director cannot respond to confidence by concentrating everything on confirming evidence.

Hypothesis confidence is also capped:

- one-cycle evidence cannot exceed 0.65
- multi-cycle evidence cannot exceed 0.85

No hypothesis becomes certain. Contradictory paired trials remain in the belief bookkeeping.

## Five search lanes

### Unexplored
Low-discrepancy Halton sampling advances a persistent cursor through start-condition space. This supplies broad coverage without a giant per-trial history.

### Boundary
Searches a wider neighborhood around the previous headline condition, looking for where behavior changes.

### Hypothesis
Searches a narrow neighborhood around the current focus. This is intentionally capped.

### Assumption Breaker
Reflects away from the current focus and changes IC family. It exists specifically to find counterexamples to the Director's current story.

### Random
A permanent stochastic lane that cannot be optimized away. Its purpose is to preserve a path to discoveries outside the model's accumulated assumptions.

## Lightweight negative memory

Mass failures do not create one JSON/field/image/Room per trial.

Instead, `coverage_atlas.json` aggregates coarse cells by dimension, IC family and parameter bins. A cell tracks only compact statistics such as:

- trials tested
- stable trials
- interesting trials
- best reached Level
- best ranking score
- last burst

The global low-discrepancy cursor prevents the broad lane from repeatedly generating the same sequence. Thus negative knowledge stays useful without repository growth proportional to trial count.

## Evidence tiers

The implementation follows the intended tiering even though not every tier is a separate file type yet:

- **T0 Trace** — mundane/negative trials: Coverage Atlas only
- **T1 Interesting** — compact event/measurement metadata
- **T2 Candidate** — noteworthy Native-3D or top Mass-2D observation
- **T3 Discovery** — reproduction / promotion evidence through the existing ledgers and candidate Rooms

`native3d_discoveries.json` is bounded to noteworthy direct-3D events rather than all 3D trials.

## Progress certificate

Every burst produces a machine-readable progress certificate. A cycle counts as `ADVANCED` when it adds scientific information, for example:

- new coverage regions
- new behavior candidate
- fresh-seed reproduction
- dimension-emergence candidate
- paired dimensional evidence

If none occur, the cycle becomes `STALLED`. The prescribed recovery is to increase unexplored/random/breaker emphasis and reduce hypothesis exploitation rather than repeat the same strategy.

## Persistent research memory

The adaptive loop uses:

- `ai_lab/discoveries/coverage_atlas.json`
- `ai_lab/discoveries/hypothesis_ledger.json`
- `ai_lab/discoveries/research_decisions.json`
- `ai_lab/discoveries/native3d_discoveries.json`
- existing Event/Discovery/View ledgers
- `runtime/dream/state.json` cursors and run state

These are sufficient for the next cycle to understand where it has searched, what it currently believes, what contradicted it, and what it decided to try next without loading thousands of failed field files.

## Scientific guardrails retained

Adaptive Dream v2 does **not** grant the Director authority to:

- edit `measures.assess_level`
- edit success thresholds
- change scientific status by narrative
- seed target structures
- write `rooms/official/`
- auto-approve coarse-global-3d or full-3d

The system can become more adaptive about questions while remaining conservative about answers.
