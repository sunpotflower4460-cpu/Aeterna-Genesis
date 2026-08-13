# Aeterna Reproducibility Contract

Aeterna distinguishes **scientific reproducibility** from **scientific truth**.

Reconstructing the same source code, evidence files and numerical environment makes a result easier to
reproduce and audit. It does not by itself establish that the model describes fundamental nature.

## Per-burst anchors

A completed research burst should be traceable through four complementary anchors:

1. `burst_id` — logical experiment-batch identity.
2. `research_source_git_sha` — source/workflow commit under which the Dream run started.
3. `evidence_snapshot_git_sha` — exact Git commit containing the persisted scientific evidence before
   postflight adds operational records.
4. `manifest_content_sha256` — immutable hash of the manifest that enumerates and hashes the burst files.

The manifest archive lives at:

`ai_lab/reports/easy/manifests/<burst-id>.json`

Git remains the byte-recovery mechanism for historical evidence; the manifest is the integrity/provenance
map that tells a future researcher which commit/files belong together.

## Numerical environment fingerprint

Each production `strict_goal_loop` records:

`ai_lab/reports/easy/environment_latest.json`

The fingerprint is generated **inside the same Python process/environment that ran the research** and
records:

- Python implementation/version/compiler,
- OS/kernel/architecture/CPU count,
- installed Python distribution versions,
- NumPy configuration output (including available numerical backend/build information),
- selected numerical-thread environment variables,
- SHA-256 of `requirements.txt`,
- SHA-256 of the `Genesis Dream Loop` workflow,
- GitHub run/source identifiers.

Only an allowlisted set of numerical environment variables is recorded. Arbitrary environment variables
or secrets are not copied into the report.

Because `requirements.txt` currently expresses compatible ranges rather than a complete frozen lock, the
**actual installed distribution map** is important provenance. Future dependency changes should preserve
old environment fingerprints rather than rewriting their interpretation.

## Manifest-backed research index

Postflight maintains:

`ai_lab/discoveries/research_index.json`

and a compact human view:

`ai_lab/reports/easy/research_history_latest.md`

The index is an acceleration layer for future agents. It points each burst to its immutable manifest and,
when available, exact evidence Git commit. It may also expose infrastructure-health, backlog and planning
progress summaries so an agent can decide what to inspect without scanning the entire repository history.

Those summaries are **navigation metadata only**:

- health is not scientific confidence,
- new-question count is not physical progress,
- backlog priority does not allocate physical search compute,
- manifest hash does not validate a physical claim.

A burst already present in the index cannot silently change to another manifest identity. A mismatch is an
integrity error.

## Reproduction workflow for a future researcher

For an old burst:

1. Find the burst in `research_index.json`.
2. Open its immutable manifest.
3. Check `evidence_snapshot_git_sha` and the environment fingerprint hash listed in the manifest.
4. Inspect the exact evidence at that Git commit.
5. Reconstruct the package/runtime environment from `environment_latest.json` at that evidence commit.
6. Use the source/workflow SHA and recorded seeds/conditions in the scientific reports to rerun the relevant
   experiment.
7. Compare observables/digests under the appropriate existing scientific audit (for example Prefix Identity
   where applicable).
8. Treat a numerical mismatch first as a reproducibility/instrumentation question, not immediately as new
   physics.

## Scientific boundary

None of these provenance tools changes:

- physics equations or solvers,
- initial-condition purity,
- NØ strictness,
- X fingerprint scientific status,
- Cross-World universality limits,
- F0–F7 meaning,
- Prefix Identity semantics,
- Local Vortex Energy interpretation,
- Room promotion or official Emergence Levels.

A matching environment can reproduce a model-internal phenomenon. That remains distinct from establishing a
fundamental physical law or emergence from strict nothing.
