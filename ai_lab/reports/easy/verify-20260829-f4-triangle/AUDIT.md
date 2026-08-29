# AUDIT — independent t=0 replay of cited F4 / X-b991d59a4d

MODULE:      verify-20260829-f4-triangle (non-official dated report; not a Room)
QUESTION:    In one uninterrupted near-zero TDGL run, does a 3-vortex triangle grow, and is unlabeled amp_std:+L the same event as object birth?
PUT IN:      g001 TDGL law (`genesis.models.ginzburg_landau.step`); family=white / white_lowk IC via `lab.make_ic` (no winding, no triangle); cited start-side knobs; fixed seeds. Quick 2D screen only (48², 260 macro-steps, dt=0.1, nsub=1).
EMERGED:     Official Level 2 (amplitude growth + persistent winding defects) on the cited white run. Detector-F4 (persistent local mutual-nearest triangle) on both listed white F4 seeds. Later many Kibble–Zurek cores. X-b991d59a4d episode with defect_count 0→0 classified AMPLITUDE_SCALE_TRACKING.
CLAIM TIER:  measured (detector flags, hashes, time series, heatmaps of |ψ| / arg(ψ)). interpretive: that the early F4 flag is a noise-winding geometry, not an isolated 3-body. Not life / cell division / new law.
KNOWN MATCH: Post-quench defect nucleation after a near-zero quench is the standard Kibble–Zurek / TDGL story (role V-adjacent). The F-path is not an official Emergence Level.
AUDIT (7):
  1. Rule does not name the result: Yes — TDGL + white noise. Triangle is observed after the fact.
  2. Faithful physics: Yes — existing g001 stepper, not a triangle generator.
  3. Result not in IC: Yes — white / white_lowk place no organized winding. `triangle_was_seeded=false`.
  4. Untargeted concomitants: Yes — early noise-winding flood, annihilation to 0, later crowded KZ lattice, amp_cv collapse.
  5. Numbers: Yes — hashes, vortex counts, regularity/area_ratio, amp_std/mean_amp/cv. Not a continuum-resolved 3-body proof.
  6. Robust: Partial — second listed F4 also detector-F4; X-pattern class reproduced on stored follow-up knobs. One 48² quick window only.
  7. Code discovers vs asserts: Yes — `strict_geometry._geometry_probe`, `lab._screen_ic`, `prefix_audit`, `open_ended._probe`, `x_mechanism_discovery._classify_event`. No threshold edits.
STATUS:      YELLOW — detector F4 and field hashes reproduce; the human-scale claim “three vortices sitting in a triangle grown from empty in one run” is not supported by the field pictures. F5/F7 absent as reported.
A_OR_B:      (A) faithful TDGL quench. Law not derived from 0.

## Claims vs measurements

### Hypothesis A (human report): strict-near-zero path reached a temporary 3-vortex triangle in the same run; not balance-collapse or split

| item | reported | this replay | tier |
|---|---|---|---|
| family / seed / knobs | white, 517111, cited knobs | same | — |
| endpoint field sha256 | `b1f69464…a25fb44` | MATCH | measured |
| observation-series sha256 | `206d189e…d68a316` | VALUE MATCH (21 snapshots) | measured |
| official Level | (implied ≥2 for F2+) | L2; defect_count=50; persistent_defects=true | measured |
| `triangle_seen` | F4 | True (steps 39 and 52, persistence=2) | measured |
| regularity / area_ratio / pattern | (not in easy one-liner) | 0.8944 / 0.40 / +−−, sides 4, 4.47, 4.47 | measured |
| `balance_collapse_seen` | 0 | False | measured |
| `network_fission_candidate` | 0 | False | measured |
| `fission_like_after_triangle` | some runs | True at step 130 | measured |
| isolated 3-vortex body | implied by “三角の3つ組” | **False** at detection: mean_amp=2.56e-8, 45 windings; at end: 50 cores, triangle=false | measured + observed |

Second listed F4 (seed=948530): endpoint sha256 `3fc8dcf1…868b58f` MATCH. Detector triangle at step 156 among ~40 cores, still `triangle=true` at end with 32 cores. Still not three objects in empty space.

**F-path depth F4 is a detector statement, not official Emergence Level 4.** Official L4 (persistent individuality) was not assessed and is not claimed.

### Hypothesis B: unlabeled X-b991d59a4d (amp_std:+L, defect_count staying 0) is the same thing as a vortex/body being born

Replay of stored follow-up source (`unknown_followups.json` search_focus: white_lowk, trial 809780 knobs; seed 366216 is a listed white-family seed for the fingerprint — **not** unpublished trial-249 `single_seed` knobs, which were not stored).

| t | mean_amp | amp_std | amp_cv | winding count | note |
|---|---|---|---|---|---|
| 0 | 1.36e-5 | 5.60e-6 | 0.412 | 0 | start |
| 11.2 | 0.020 | 0.0083 | 0.414 | 0 | contrast up, no vortex |
| 11.3 episode | log-gain mean≈3.22, std≈3.22, cv_log_gain≈0.0001 | 0→0 | AMPLITUDE_SCALE_TRACKING; fingerprint amp_std:+L |
| 13.1 | — | — | — | 2 | different episode; vortices_appear |
| 26 | 2.23 | 0.0075 | 0.0034 | 2 | two cores; no triangle |

On the cited F4 run itself, the large amp_std jump at t=11.3 is **with** vortices_appear (0→1) and still classified AMPLITUDE_SCALE_TRACKING (cv almost flat). By t=12.9 amp_std **falls** while ~70 cores sit in a saturating background (cv 0.20→0.030). Relative contrast of the bulk drops when objects exist as localized cores.

**Verdict: amp_std:+L with defect_count frozen at 0 is not object birth.** It is overall amplitude growth at nearly constant cv. Object birth is a later, separately fingerprinted transition.

## What did NOT happen

- No seeded triangle, vortex, or division site.
- No F5 (balance collapse while still one connected group).
- No F6/F7 network-fission candidate.
- No official Emergence Level 4/5/7 claim.
- No 3D authenticity claim (2d-screen-quick-48 only).
- No new law, no threshold change, no official Room write.
- Cited F4 did not end as three vortices. It ended as a crowded defect field.
- X-pattern representative trial 249 (`single_seed`, seed=870754) knobs were not in the ledger; that exact row was not reconstructed.

## Repro

```bash
python3 ai_lab/reports/easy/verify-20260829-f4-triangle/replay.py
```

Uses: `ai_lab.lab._screen_ic`, `ai_lab.dream.strict_geometry._geometry_probe`, `ai_lab.dream.prefix_audit`, `ai_lab.dream.open_ended._probe`, `ai_lab.dream.x_mechanism_discovery._classify_event`, `tools.snapshot.render_field`.

## Discipline

- no_touch: measures.py / geometry thresholds / F-path gates / official rooms untouched.
- 第8監査: IC is white / white_lowk. Correlation_length is unused for family=white (`ic_family_uses_correlation_length=false`); recorded as in the original trial.
- Visualization separated from physics (`honesty.visualization_separated_from_physics`).
- Deterministic seeds 517111 / 948530 / 366216.
- Claim tiers not raised. F-stages ≠ Emergence Levels.
- Failures kept: F5/F7 absent; isolated-trio picture absent; observation compare_digest wrapper false-mismatch documented.
