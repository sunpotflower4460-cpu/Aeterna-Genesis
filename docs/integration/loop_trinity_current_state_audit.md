# Loop-Trinity × Genesis — Phase LT-0 current-state audit

**Docs-only.** No physics, schema, experiment number, or artifact was changed by this audit. It fixes what
already exists in Genesis, what is missing, and the smallest safe first step, so the integration does not
duplicate or overwrite anything. Re-verified against **Genesis HEAD**; the Loop side is taken from the
integration pack only (see Limitations).

## Genesis HEAD state (verified)
- Branch `claude/aeterna-genesis-core-kduyhi`; tip `26eba43` (e047 F1) on top of `77fe84d` (main, PR #63).
- **Open PRs: none.**
- **Experiment numbers: e001–e047 exist. e047 is already taken** by `e047_sphere_to_torus` (P06/F1, role V).
  → The pack's example numbering (`e047 = gauge observer`, `e048 = ledger`, …) is **stale for this repo**.
  Per the kickoff, **we reserve no number**. LT observers below are **diagnostic modules** (no experiment
  number). A future calibration *experiment* (pack LT-6) claims the next free number **at creation time**.
- Frontier preregistrations present: `docs/frontier/F0_P01_active_droplet.md`, `docs/frontier/F0_P06_sphere_to_torus.md`.
- Diagnostics present: `genesis/diagnostics/{measures,higher_levels,angular_modes,coupled_spectrum,topology_betti,topology3d,corroborate}.py`; complex-field/winding tooling in `core/{vortex,holonomy,field,hopf,fft,measure}.py`.

## The two audit questions (carried on every claim)
- **育ったのか、置いたのか？** (grown vs placed) — Genesis's existing 8th-audit / ANTI_DRIFT.
- **関係したのか、ただ同じ attractor へ崩れただけか？** (a real interaction vs both relaxing to one attractor)
  — Loop's addition. Operationalized by **matched OFF controls** (same layout/seed/horizon/dt/res, coupling
  off) and by the gauge-aligned distance below (a shrinking *raw* distance is not structural convergence).

## Observer status — exists / partial / missing
| Loop observer | Status in Genesis HEAD | Evidence / gap |
|---|---|---|
| **(a) Gauge-aligned complex-field distance** (raw L2, global-phase-aligned L2, `θ*`, invariant `D_inv`, gauge overlap) | **DONE this PR** | New `genesis/diagnostics/gauge_aligned_distance.py` + `tests/test_gauge_aligned_distance.py`. Confirmed **no prior** `theta_star`/aligned/`D_inv` existed anywhere in `genesis/ core/ tools/`. |
| **(b) Phase/winding reliability observer** (per-line min amplitude, wrapped-step max/mean, near-π edge count, invalid-line flag, dominant winding + fraction) | **DONE (LT-2)** | New `genesis/diagnostics/winding_reliability.py` + tests. Turns the amplitude gate that was buried inside `count_defects`/`_plaquette_defects` into a first-class per-line report; dominant_fraction is over VALID lines only; closed-loop residual is float-sanity only. |
| **(c) Orientation-complete plaquette ledger** (XY/YZ/ZX signed +/−/net/invalid) | **DONE (LT-3)** | New `genesis/diagnostics/plaquette_ledger.py` + tests. 3-orientation signed plaquette winding, per-slice tallies, gauge-invariant map hash, A/B map distance. Documented DISTINCT from volume Betti (`topology_betti`) and from global line winding (`winding_reliability`); tests pin both boundaries. Not an exact 3D topology proof (no vortex-core graph yet). |

## Duplication / conflict guard (do NOT rebuild)
- **Volume Betti ≠ phase-defect ledger.** `topology_betti.betti3d` measures the material region's `b0/b1/b2/χ/genus`; a Loop plaquette ledger measures complex-phase winding. Keep them **separate** (LT-3 must document the boundary), as the pack itself requires.
- **e046** already validates fixed-cell-complex `H1 = b1 = 2g` holonomy channels (role V, placed) — do not conflate with a lattice plaquette ledger.
- **G001** already *grows* 3D vortex lines from a near-uniform quench (official Room, reached L2). Loop's manual W-fixtures are **positive controls / perturbation tests only**, never mixed into G001's natural-emergence artifacts.
- **e028 / e019** (non-local winding memory design-hypothesis / bidirectional backreaction) are the natural homes for the *later* memory/coupling phases — **not this round**.

## What this round did (LT-1) and its position
- **Implemented:** `gauge_aligned_distance(A, B)` → `{raw_distance, aligned_distance, invariant_distance, gauge_overlap, theta_star, finite_count, total_count, zero_norm, invariant_clip, sign_convention}`.
- **role V** (measurement only), **dimension-agnostic** (any complex field; 2D/3D/Room), **claim tier: measured**.
  It changes **no physics** and encodes **no target** (it compares two given fields; it sets no pass/fail band).
- **Sign convention (fixed & tested):** `θ* = arg(Σ A·conj B)`, applied to the second field `B_aligned = e^{iθ*}B`;
  at that angle `aligned_distance == invariant_distance` (a built-in self-check).
- **Synthetic controls (all GREEN):** identical→0; +π/5 global phase→raw large but aligned≈0 & overlap≈1;
  structurally different / opposite winding→aligned stays >0; zero-norm→overlap None; NaN/inf excluded & counted;
  seeded-noise monotonicity; sign-convention regression. 9/9 tests pass.
- **Honest floor:** this is a *comparison* observer. A shrinking **raw** distance is **not** structural
  convergence or "fusion"; use `aligned`/`invariant` for structure and `gauge_overlap` for "same-up-to-phase".

## No-touch (unchanged, verified by `git status`)
`genesis/diagnostics/measures.py`, all existing `genesis/`, `core/`, `experiments/e001–e047`, `rooms/official/**`
(fields, `emergence.json`, `manifest.json`, checksums), all `schemas/`, `genesis/registry/*`, `.github/workflows/ci.yml`,
`app/**`. Only **two new files** were added.

## PR split (numbers assigned at creation, not reserved here)
1. **LT-1:** gauge-aligned distance observer + tests. **Done.**
2. **LT-2:** phase/winding **reliability** observer (per-line min amp, wrapped-step stats, near-π count,
   invalid flag, dominant winding + fraction over valid lines). **Done.**
3. **LT-3:** 3-orientation XY/YZ/ZX **plaquette ledger** (signed +/−/net/invalid), explicitly distinct from
   volume Betti and global line winding. **Done.**
4. **G4 (continuity):** result-integrity guard — `tools/verify_result_integrity.py` + `tools/result_integrity.json`
   hash-ledger, CI-verified, so a past result cannot be silently overwritten. **Done.**
5. **LT-4 (next, docs→schema):** phenomenon-vocabulary (phase_slip, common_attractor_relaxation_candidate, …)
   as an **additive** metadata axis; docs-only first, schema PR separate.
6. **Only after the V-observer stack:** the memory / slow-field / coupling **physics** phases — only as
   preregistered S experiments with matched OFF controls.

## Not implemented this round (by directive)
New physics, slow-field/memory/trace/coupling experiments, schema migrations, Room changes, experiment-number
reservations. LT-2/LT-3/LT-4 are recommendations, not started.

## Limitations
- **Loop repo (Aeterna-loop-trinity) HEAD was NOT accessible** in this session (scope restricted to
  `sunpotflower4460-cpu/aeterna-genesis`; the uploaded pack contains only the integration docs, not Loop
  source). Loop-side claims are therefore taken from the pack **unverified against Loop HEAD** — the equations
  and known-answer fixtures were re-derived independently here, but Loop's numeric results/thresholds are not
  imported and must be re-derived/re-calibrated in Genesis before use.
- A companion continuity audit (`docs/integration/research_continuity_audit.md`) records how well the repo
  durably remembers prior work, since "forgetting" would defeat the integration.
