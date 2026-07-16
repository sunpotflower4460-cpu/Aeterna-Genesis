# Research-continuity audit — does the repo durably remember what it built?

**Question (うえきさん):** 「積み上げてきたものを忘れず記録できていて、研究が前進し続ける仕組みになっているか。
やってもやっても前のを忘れていたら進まない。」

**Verdict:** **Mostly yes for structured artifacts, partly no for the narrative + integrity layer.** The
machine-readable spine (per-experiment `experiment.yaml`, schemas, registries, the emergence-ladder pin) is
**CI-enforced** and hard to forget. But the *knowledge* layer (white ceilings, trust map, lineage) is
**unenforced markdown that can silently drift from the code**, and committed result JSONs / Room fields are
**not tamper-verified**, so an observer change could overwrite past numbers without CI noticing. None of this
is currently *broken*; the risk is silent rot over time. Docs-only; nothing changed by this audit.

## What is strong (won't be forgotten)
- **Every experiment carries `experiment.yaml`** (all 43 present) — role, claim_tier, put_in/emerged,
  target_encoded, results[]. `tools/validate_schemas.py` (CI) **fails** on a missing/invalid file, on an
  `id` that doesn't match its directory, and on the 8th-audit rule (`target_encoded=true ⇒ role ∉ {E,V}`);
  `tools/audit_roles.py` independently re-checks the role badges. → experiments cannot silently lose metadata.
- **Registries validate** (`genesis/registry/{models,solvers,diagnostics,invariants,param_ranges}.yaml`):
  schema-checked, duplicate ids rejected, and every `related_experiments` ref must resolve to a real dir.
- **The emergence ladder is CI-pinned** — `ci.yml` asserts `room-g001-a.reached_level==2`,
  `g002==1`, `g003==2`. A silent regression in how far a Room climbed **breaks the build**. This is the
  strongest continuity guarantee, and progress is catalog-driven (`tools/build_catalog.py` →
  `app/generated/catalog.json`, read by the Observatory app — not hardcoded).
- **Ledgers exist and their presence is checked**: `docs/working_ledger/H001–H020`, `docs/claim_ledger.md`,
  `docs/PIECES.md`, `docs/traps_museum.md`, `docs/honest_floors.md`, `docs/WHITE_CEILINGS.md`,
  `ai_lab/discoveries/ledger.json` (machine-reviewed by `ai_lab/lab.py --review`).
- **Provenance schema exists** (`schemas/provenance.schema.json`: fundamental_relation / prepared_state /
  environmental_condition / emerged_state; `outcome_targeted:false`) and per-run **checksums are recorded**
  (`rooms/official/*/runs/seed-*/manifest.json → checksum.final_field_sha256`, `code_version`).

## Gaps (where knowledge can be forgotten or overwritten) + quick wins
| # | Gap | Why it matters | Quick win (small, additive) |
|---|---|---|---|
| **G1** | Registration is one-directional: **~18 experiments are referenced by no registry entry** (e004, e009, e014, e019, e020, e022–e024, e027, e029, e030, e036, e038–e041, e046, e047). A new experiment can exist with zero registry linkage and CI stays green. | The registry stops being a complete index of what was built. | Add a **reverse check** in `validate_schemas.py`: every `experiments/e0*/` must be `related_experiments` of ≥1 registry entry, or carry an explicit exemption. |
| **G2** | `WHITE_CEILINGS.md`, `TRUST_MAP.md`, `GENESIS_MAP.md` are **hand-maintained prose with no content validator** — only `test -f` existence. They can drift from `experiment.yaml`/`emergence.json`. | The "how far each white climbed / why it stopped" memory can quietly go stale — exactly the "forgetting" risk. | Generate the TRUST_MAP / ceiling rows **from** `experiment.yaml` + `emergence.json`; CI diff-checks generated vs committed. |
| **G3** | Results-existence is a **hand-curated `test -f` list** in `ci.yml`, not schema-driven; 9 experiments have no `results/` dir. Adding an experiment doesn't force its results check. | The "which results must exist" ledger drifts from the experiment set by hand. | Have `validate_schemas.py` read `experiment.yaml.results[]` and assert each path exists. |
| **G4** | `final_field_sha256` is **recorded but never re-verified**; result JSONs / Room `emergence.json` are **plain committed files with no integrity check**. CI checks they *exist* and *schema-validate*, never that their numbers are unchanged/reproduced. | An observer/measure change could **silently rewrite past results in place** — the precise Loop-Trinity concern ("historical artifact protection"). | Add a CI step that re-runs a Room smoke and compares `final_field_sha256`, or asserts committed result JSONs are byte-identical to a fresh `--quick` re-gen (where deterministic). |
| **G5** | `rooms/official/*/lineage.yaml` is an **empty stub** (`parent: null, children: [], changes_from_parent: []`); no generator-commit / parameter lineage tying fields to the code that made them. | Can't reconstruct *which commit + parameters* produced a Room's committed fields. | Populate `changes_from_parent` + `generator_commit` at build time in `tools/build_room_g00*.py`; schema-require it. |
| **G6** | Nothing enforces that discovering a **new white updates `WHITE_CEILINGS.md`**, nor cross-checks a Room's `reached_level` against its ceiling row. | A failed avenue can be blindly retried; a new white can be claimed with no honest-ceiling entry. | Validator linking each Room's `emergence.reached_level` to a WHITE_CEILINGS row; fail if a white is claimed without one. |
| **G7** | The ladder pin is a **hardcoded literal** in `ci.yml`. | Must be hand-edited when a Room legitimately climbs; easy to forget or fudge. | Move expected levels into a committed `expected_levels.json` the test reads. |
| **G8** | **New diagnostic modules are not required to be registered.** `diagnostics.yaml` lists only 8 legacy Level-measures; `higher_levels`, `angular_modes`, `coupled_spectrum`, `topology3d`, `topology_betti`, and the new `gauge_aligned_distance` are **absent**, and nothing flags it. (This registry is also Level-keyed, so "infrastructure" observers have no home.) | The catalogue of *how we can measure* drifts from what's in `genesis/diagnostics/`. | Add a `kind: infrastructure` section (or a second registry) and require every `genesis/diagnostics/*.py` public observer to be listed. |

## Bottom line
The repo **will not forget** an experiment's role/claim/results-schema or a Room's reached level — those are
CI-enforced. It **can gradually forget** (a) the complete index of what exists (registry gaps), (b) the honest
ceiling/trust narrative (prose drift), (c) the exact provenance of Room fields (empty lineage), and (d) whether
a past result was silently overwritten (no integrity re-check). The eight quick wins above are small, additive,
and would close the "did we already try/learn this?" loop that keeps research moving forward instead of
re-treading. **Recommended priority: G4 (integrity) and G2/G6 (ceiling memory) first** — they most directly
protect accumulated knowledge; G1/G3/G8 (index completeness) next.

*This is an audit only. Implementing any quick win is a separate, small PR — not done here.*
