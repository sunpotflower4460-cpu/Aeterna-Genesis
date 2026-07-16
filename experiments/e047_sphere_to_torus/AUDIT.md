# e047 sphere-to-torus — F1 audit (V0/V1)

Frontier: `docs/frontier/F0_P06_sphere_to_torus.md`. This module implements **only F1 (V0 + V1)** and
**stops**. It does **not** attempt S1/E2 (F2/F3): the shape `phi` is fixed throughout, so no hole opens
and no genus transition is claimed here.

## Claim (measured, role V)

- **V0.** The Topology Instrument v1 (`genesis/diagnostics/topology_betti.betti3d`) reads the **volume**
  Betti numbers of the fixed shapes correctly — solid ball `(b0,b1,b2,genus)=(1,0,0,0)`, solid torus
  `(1,1,0,1)`, double torus `(1,2,0,2)` — from the **same diffuse-interface level sets `phi>phi_c`** used
  in V1, and the torus `b1=1` is stable across the threshold `phi_c` and at a coarser resolution.
- **V1.** Evaluating the **full nematic droplet free energy on fixed shapes** and sweeping the
  elastic/capillary ratio `K` (planar anchoring held on), `F(torus)` crosses below `F(ball)` at
  **K\* ≈ 0.32** (full run, N=36). With anchoring **off** the crossing **vanishes** (mechanism control).

## What was PLACED vs MEASURED (育ったのか置いたのか)

- **Placed:** the shapes (`phi` ball / torus, volume-matched) and the planar-degenerate anchoring boundary
  condition. This is why the role is **V**, not E. The crossing is a fact about the free-energy *landscape*
  of placed shapes; **no hole grew**.
- **Measured:** volume Betti/genus, and the free energies `F(ball,K)`, `F(torus,K)` of the relaxed nematic
  texture on each fixed shape, the crossing `K*`, and the area penalty.

## Mechanism (why the crossing is real, not tuned)

Planar anchoring wants the director tangent to the interface. On a **sphere** a tangent director field must
carry total index **+2** (Poincaré–Hopf / hairy-ball) → forced defects → an elastic cost that grows with
`K`. On a **torus** a defect-free tangent director exists (`φ̂`) → no such floor. The torus pays a fixed
**extra interfacial area** (it is not the minimal-area shape). Small `K`: area wins → ball. Large `K`:
forced-defect energy exceeds the area penalty → torus. Sweeping `K` therefore *must* cross; we locate `K*`.

## Honest caveat / companion (F2-relevant)

The **full Q-tensor** functional (built in the same module, `nematic_qtensor.relax`) lets a defect core
**melt (S→0) and escape into 3D**; its core size `ξ=√(L1/|A|)≈0.5` cell is sub-grid, so a sphere satisfies
planar anchoring almost for free and **F(torus) stays above F(ball) — no crossing** at this resolution
(recorded in `results/sphere_to_torus.json → v1.qtensor_companion`). The crossing is exposed in the
**fixed-length (Frank) director limit** of the *same* free-energy family, where cores cannot melt. That
escape degree of freedom is exactly the ingredient the **F2 dynamic hole-opening** needs and V1 does not —
so its absence here is by design, not a bug.

## Independent audit + remediation

An independent audit (`EXTERNAL_AUDIT.md`, verdict SOUND-WITH-CAVEATS) finite-differenced the reported
energy against the analytic molecular field: LdG bulk, L2 elasticity and Fournier–Galatola anchoring are
**exact discrete gradients** (rel err ~1e-9), S_eq matches, every relaxation is strictly monotone. It flagged
one real, non-fatal item: the **elastic force originally used the compact Laplacian while the energy used
central-difference gradients** (inconsistent stencils; still a descent direction applied identically to both
shapes, so the crossing was unbiased). **Fixed:** the elastic energy now uses forward differences, for which
the compact Laplacian is the *exact* discrete gradient — the Frank director flow is now variational to
rel err ~2e-9. (K\* shifted 0.32→0.26 under the corrected flow; the crossing and control are unchanged.)
The remaining open items are correctly deferred to F2: ε/R (interface-width) and grid convergence of K\*.

## Frozen / determinism

- Physics constants frozen in `genesis/models/nematic_qtensor.FROZEN`; run geometry/sweep frozen in
  `CONFIG_FULL`/`CONFIG_QUICK`. `--quick` only coarsens grid/steps — it never changes a physics constant.
- Values were frozen at implementation time and not retuned after seeing results (F0 §2). The K-sweep range
  brackets `K*`; `K*≈0.30–0.33` across the tested resolutions (N=24/28/36).
- Deterministic: seeded RNG only for the shape-blind director IC ensemble (identical recipe for every shape).

## Discipline checks

- **no_touch:** `genesis/diagnostics/measures.py` and `rooms/official/**` untouched; new physics is added as
  new modules (`genesis/models/nematic_qtensor.py`) + a new experiment dir. No existing experiment number,
  result, Room, or schema changed.
- **8th audit (target encoding):** `F` contains no hole/handle/genus term and no target shape; the only
  anisotropy is standard L2 elasticity + planar-degenerate anchoring; the director seed ensemble is
  shape-blind. `target_encoded=false`.
- **C03:** the reported number is the **volume** `b1(Ω)`; the boundary **surface genus** equals it only for
  a cavity-free handlebody, and surface `b1 = 2·genus` is a distinct count. Kept explicit in code and output.
- **Language:** measured = Betti/genus/free energy. We do **not** say the difference "wanted" a hole, and we
  do **not** say life/mind/universe. "Same picture ≠ same thing."

## Reproduce

```
python experiments/e047_sphere_to_torus/sphere_to_torus.py            # full (writes results/*.json + crossing.png)
python experiments/e047_sphere_to_torus/sphere_to_torus.py --quick    # coarse smoke (GREEN in ~10 s)
pytest tests/test_e047_sphere_to_torus.py -q                          # V0/V1 unit checks
```

## Not claimed (stop line)

- Not claimed: that a hole opens on its own (S1/E2), that this is emergence (E), dynamic genus transition,
  or grid/`ε/R` convergence of `K*`. Those are F2/F3 and are deferred pending review.
