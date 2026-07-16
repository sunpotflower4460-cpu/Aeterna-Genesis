# e050 slow-field basin memory — robustness + 3D (P07 / S2, role S)

Stress-tests the S1 candidate (e049): does the slow-field basin memory (hysteresis EXCESS over the matched g=0
OFF control) survive coupling-strength, resolution, seed, and dimension changes? Same honest frame as S1
(role S, local bidirectional coupling, matched OFF control, energy monitored, `s` couples to `|psi|^2` with no
target/template).

## Measured result (full)
- **(a) coupling band:** excess vs g = [0, 0.042, 0.10, 0.19, 0.33, 0.59] for g=[0,0.15,0.3,0.45,0.6,0.75] —
  a clean **onset at g\*≈0.3** and smooth monotone growth (a phase diagram, not an on/off artifact).
- **(b) resolution:** excess = 0.310 / 0.304 / 0.298 at L = 32 / 48 / 64 — **flat → not a finite-size artifact.**
- **(c) seeds:** excess = 0.318 ± 0.013 over 4 seeds — robust.
- **(d) 3D promotion:** excess = **0.257** in 3D (L=24³), energy bounded — **the memory survives 2D→3D.**
- **Verdict: `robust_slow_field_basin_memory_candidate`.**

## Discipline
- **role S** (psi and s placed). measured: excess across g/L/seed/dim with matched OFF control. observed
  (candidate): a placed slow field gives a robust, dimension-surviving history-dependent basin. **Not** emergence.
- **8th audit:** `target_encoded=false` — s couples to generic `|psi|^2`, no template; the signal is the excess
  over the matched OFF control at every point.
- **official_3d=false:** this confirms the memory *survives* in a 3D screen; it is NOT a promotion to an
  official 3D Room (that needs the full Room pipeline + its own audit).
- **no_touch:** measures.py, rooms/official, existing experiments/schema/registry untouched; new experiment only.

## Limits / next
- 3D at a single resolution (24³) and single g; a full-3D Room, a wide (g, tau) phase diagram, and larger-tau
  "history vs copy" strengthening are open (S2+).
- The E-candidate — whether `s` itself, grown from an undifferentiated quench (not placed), reproduces the
  effect — is the north-star bridge and is a SEPARATE experiment (e051) with its own prereg addendum.

## Reproduce
```
python experiments/e050_field_slow_field_basin_s2/field_slow_field_basin_s2.py            # full
python experiments/e050_field_slow_field_basin_s2/field_slow_field_basin_s2.py --quick    # smoke
pytest tests/test_e050_field_slow_field_basin_s2.py -q
```
