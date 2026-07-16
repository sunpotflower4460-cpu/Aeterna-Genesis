# e049 field/slow-field basin memory — audit (P07 / S1, role S)

Frontier: `docs/frontier/F0_P07_field_slow_field_basin.md`. **S1** is the first rung that runs COUPLED fast/slow
DYNAMICS. It asks P07's central question at the **S (placed)** tier: does a slow local material field make the
ordered/disordered basin depend on history (memory), separably from the sweep-rate confound?

## Concept/physics alignment (checked BEFORE running — the drift audit)
- **育ったのか置いたのか:** `psi` (quenched/damaged) and `s` are PLACED → **role S**; we do not call this
  emergence. The slow field is a **fixed local law present from t=0** (not a runtime-injected buffer, not a
  mid-run function addition).
- **8th audit / target encoding:** `s` couples to the generic local amplitude `|psi|^2`, **not** to any
  winding/basin/target label; `s0` carries **no template** (starts at 0). The basin (order/disorder) outcome is
  emergent; the success test is a **differential vs a matched control**, never "reach the good basin". A
  physics finding from this audit: an amplitude-coupled slow field can only bias basins with an **amplitude
  signature**, so we use the order/disorder (amplitude) basin and its **hysteresis** — the most encoding-free
  memory signature (no `s0` template needed) — rather than a phase-winding basin.
- **関係したのか、同じ attractor へ崩れただけか:** the **matched g=0 OFF control** (identical alpha grid /
  seed / steps / dt) quantifies the sweep-rate/critical-slowing confound; the reported memory is the **excess
  ON−OFF**, not the raw hysteresis.
- **履歴を保持したのか、現在をコピーしただけか:** we measure the `s` vs `|psi|^2` **lag**; a ~0 lag would be
  `memory_copy_collapse`.
- **conservation:** the GL free energy is monitored every step; `energy_instability` is a declared failure
  outcome. No hidden corrections.
- **dimension:** 2D screen, `official_3d=false`. This is a mechanism study, not an official 3D Room.
- **north-star link:** history-dependent basin selection = a primitive of Level-4 "recovery after perturbation
  / persistence". The E-candidate (`s` itself emerging from an undifferentiated quench) is a later rung, **not
  done here**.

## Model (local, bidirectional, no central solver)
```
d_t psi = [alpha0 + g*s]*psi - |psi|^2*psi + lap(psi)      (5-point local Laplacian)
d_t s   = (1/tau)*(|psi|^2 - s) + Ds*lap(s)
```
Frozen: tau=10, Ds=0.5, dt=0.05, g_on=0.6, alpha 0.6→−0.6→0.6 (13 pts each way), settle 400, K steps/alpha.
Classification margins preregistered in the runner (NOT imported from Loop).

## Measured result (role S; 3 seeds, full)
- hysteresis area **ON=0.510** vs **OFF=0.200** → **excess 0.310** (> margin 0.06): the slow field adds
  hysteresis beyond the matched sweep-rate baseline.
- order retained at alpha≈0 (ordered branch) **ON=0.175** vs **OFF=0.021** → **gain 0.154** (> margin 0.05):
  the slow field sustains the ordered basin below the transition (undercooling memory).
- memory lag ON=0.029 (> 0.02) → `s` lags `|psi|^2`, **not** an instantaneous copy.
- energy bounded (max ≈ 4e2 ≪ cap).
- **Verdict: `slow_field_basin_memory_candidate`** — a matched-control-separated, non-copy, energy-stable
  basin-memory candidate at role S.

## Honest tier / claim
- **measured:** hysteresis areas, retained order, memory lag, energy — all with matched OFF control.
- **candidate (observed):** "a placed slow field makes basin selection history-dependent". role **S**.
- **NOT claimed:** emergence; that the slow field itself arose from zero; that this is memory/life; robustness
  across resolution/3D. Those are S2 / E-candidate and are deferred.

## Limits
- 2D screen; single g value (g=0.6) — the full g-threshold-band phase diagram (P2) and hysteresis-direction
  sweep are S2. The memory lag is modest (tau=10); a larger tau would strengthen the history-vs-copy margin.
- The OFF baseline hysteresis (0.20) is real (critical slowing) — that is why the claim is the excess, not the
  raw value.

## Reproduce
```
python experiments/e049_field_slow_field_basin/field_slow_field_basin.py            # full (writes results/*.json)
python experiments/e049_field_slow_field_basin/field_slow_field_basin.py --quick    # fast smoke
pytest tests/test_e049_field_slow_field_basin.py -q
```
