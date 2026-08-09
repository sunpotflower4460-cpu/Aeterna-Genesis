# Adaptive Dream v7 — Hypothesis Evolution

## Purpose

Adaptive Dream v7 adds a research-planning layer above v6.  The new layer lets Aeterna keep many competing hypotheses alive, strengthen or weaken them from evidence, create bounded automatic refinements, synthesize new falsifiable route questions from recurrent X-patterns, and divide the already-capped hypothesis lane among a portfolio of active ideas.

v7 does **not** change the physics timestep loop, measurement code, success thresholds, official Emergence Levels, official Rooms, or human approval gates.

## Mission and route are separate

The default mission is `ai_lab/missions/zero_to_division_like.json`.

It deliberately does not say "reach F7".  It requires explicit evidence for strict start purity, a persistent individual-like body, identity continuity, a one-to-two transition, persistence of both descendants, accounting, inheritance, fresh-seed reproduction, and Prefix Identity integrity.

F0–F7 remains one human-written reference route.  F7 or relation/network separation alone cannot satisfy the mission and cannot be called biological cell division.

The mission is an evidence checklist, not an initial-condition template.  Target morphology, vortex locations/charges, pair/triangle geometry, division location, division time, and energy landscape remain forbidden as seeded answers.

## New modules

- `ai_lab/dream/evidence_cards.py` — converts heterogeneous evidence into a common bounded envelope. Quarantined evidence gets zero weight.
- `ai_lab/dream/hypothesis_evolution.py` — maintains `hypothesis_graph.json`, migrates legacy hypotheses, updates planning confidence, and creates bounded branches.
- `ai_lab/dream/hypothesis_synthesizer.py` — provider-free first implementation that proposes falsifiable route questions from recurrent condition-specific X-patterns. It cannot set scientific confidence.
- `ai_lab/dream/portfolio_director.py` — ranks active hypotheses by information-value proxy, goal relevance, novelty and uncertainty, then subdivides only the existing hypothesis lane.
- `ai_lab/dream/goal_engine.py` — evaluates only explicitly recorded mission evidence and refuses to infer cell division from F-depth.
- `ai_lab/dream/adaptive_v7.py` — wraps v6 and writes v7 planning outputs into reports.
- `ai_lab/dream/strict_goal_loop.py` — strict geometry/Prefix-Audit entry point for v7.

## Hypothesis states

The graph can use:

- `PROPOSED`
- `SCOUTING`
- `TESTING`
- `GROWING`
- `CONDITIONAL`
- `CHALLENGED`
- `WEAKENED`
- `DORMANT`
- `FALSIFIED`

Nodes are not deleted merely because they weaken.  Their evidence history remains available for later reinterpretation.

## Automatic branching

The first bounded branch rule uses evidence that already exists today.  When a recurrent X-pattern has at least two exact/nearby hits and zero contrast hits, v7 creates a narrower `condition-specific` child node.  This is a research refinement, not a physical-law claim.

The deterministic synthesizer may then create a separate route question such as whether that X-pattern predicts a later persistent relation or self-separation marker.  The proposal starts at confidence 0.5, contains a counter-hypothesis and falsification condition, and explicitly makes no causal claim.

## Evidence integrity

Evidence cards preserve source kind and integrity status.  `scientific_usable=false` or known Prefix/Field reconstruction quarantine statuses force card weight to zero.  A dramatic long-horizon result therefore cannot strengthen a hypothesis when its prefix identity fails.

Aggregate legacy support/contradiction counts are treated as aggregate cards rather than pretending every count is an independent observation.

## Portfolio and anti-bias contract

The portfolio ranks hypotheses, but it can only subdivide the existing hypothesis lane.  It cannot reduce the global floors inherited from Adaptive Dream:

- unexplored >= 20%
- Assumption Breaker >= 10%
- random >= 10%
- total hypothesis exploitation <= 35%

A stronger planning belief also receives higher `challenge_pressure`; confidence must not cause confirmation-only search.

The first v7 implementation records per-hypothesis effective shares inside the bounded hypothesis lane.  Broad-search lanes remain unchanged.

## Provider-free synthesis first

Hourly research must not depend on an external model, API key, or network service.  Therefore v7 initially uses a deterministic synthesizer for obvious evidence-driven branches.

A future LLM adapter can propose richer hypotheses, but proposals must pass the same validator.  The model may propose statements, counter-statements, falsification tests and next experiments.  It may not directly update confidence or scientific status.

## Generated state

When record mode is enabled, v7 writes:

- `ai_lab/discoveries/hypothesis_graph.json`
- `ai_lab/discoveries/hypothesis_history.json`
- `ai_lab/discoveries/hypothesis_portfolio.json`
- `ai_lab/discoveries/goal_progress.json`

The v7 report also contains `hypothesis_evolution_v7`, `hypothesis_portfolio_v7`, and `goal_mission_v7` sections.

## Safety invariants tested in CI

The unit tests require that:

- quarantined Deep-Time evidence has zero weight;
- a condition-specific X-pattern can branch without becoming a causal claim;
- synthesized proposals have a falsification condition and cannot set confidence;
- proposals that request target seeding or threshold changes are rejected;
- stronger beliefs receive more challenge pressure;
- portfolio allocation cannot lower broad anti-bias floors;
- F7 alone never satisfies the division-like mission.

## Deployment plan

v7 is designed as a wrapper around v6 so it can be validated without destroying the existing research loop.  CI first runs a tiny `strict_goal_loop` burst.  Production can switch from `strict_fission_loop` to `strict_goal_loop` after those tests pass and the new ledgers are added to the workflow cache/artifact/persist lists.
