# External Adversarial Audit — e047 sphere-to-torus (P06 / F1, role V)

Auditor: independent physics/code review (read-only; no source files modified).
Date: 2026-07-15. Scope: **V0 + V1 only** (explicitly NOT S1/E2). Files audited:
`genesis/models/nematic_qtensor.py`, `experiments/e047_sphere_to_torus/{sphere_to_torus.py,experiment.yaml,AUDIT.md,results/sphere_to_torus.json}`,
`tests/test_e047_sphere_to_torus.py`, with context `docs/frontier/F0_P06_sphere_to_torus.md`, `AGENTS.md`, `genesis/diagnostics/topology_betti.py`.

## Verdict: **SOUND-WITH-CAVEATS**

The V0 instrument check and the V1 fixed-shape free-energy crossing are correct, honestly framed, and reproduce as claimed. The role is correctly kept at **V** (shapes are placed; no hole opens; no emergence claimed). The Landau–de Gennes bulk, the L2 elasticity, and the Fournier–Galatola planar-degenerate anchoring molecular fields were verified to be **exact discrete gradients** of the reported energy (sign- and factor-correct to ~1e-8). One genuine, non-fatal defect was found: the **L1 (one-constant) elastic force and the Frank elastic force are discretized inconsistently with their own energy** — they use the compact 7-point Laplacian while the energy uses central-difference gradients, and the Frank force additionally omits the interface `∇h·∇n` term. This is a *preconditioned* / approximate gradient flow, not the exact variational flow of the stated functional. It does **not** break any V0/V1 claim (it is a guaranteed descent direction, monotone in practice, and applied identically to both shapes so the comparison is unbiased), but it must be disclosed and it means the relaxed states are approximate, slightly under-relaxed critical points — which the code already hedges honestly.

---

## Verification checklist

| # | Item | Result |
|---|------|--------|
| 1 | Quick runner `--quick --no-write` runs GREEN | **PASS** (K*=0.331) |
| 2 | `pytest tests/test_e047_sphere_to_torus.py -q` | **PASS** (8/8) |
| 3 | S_eq analytic vs numeric minimiser of f(S) | **PASS** (0.649675 vs 0.649674, diff 1e-6) |
| 4 | LdG bulk molecular field = exact −δF/δQ (FD directional deriv) | **PASS** (rel err 6e-9) |
| 5 | L2 elastic molecular field = exact −δF/δQ | **PASS** (rel err 6e-9) |
| 6 | Fournier–Galatola anchoring molecular field = exact −δF/δQ | **PASS** (rel err 9e-9; N=Q̃−PQ̃P, factor −2Wg correct) |
| 7 | **L1 elastic force = exact −δF/δQ of reported L1 energy** | **FAIL** (rel err 17%; compact `_lap` vs central-diff `_d` energy — see Bug 1) |
| 8 | Full-Q gradient flow monotonically decreases the reported F | **PASS** (300 steps, max positive ΔE = −1.2e-3, strictly ≤0) |
| 9 | Full-Q flow direction is a genuine descent (D_fd<0) despite Bug 1 | **PASS** (per-mode overlap positive; no sign error) |
| 10 | Frank force = exact −δF/δn of frank_energy | **FAIL** (rel err 45%; same `_lap` vs `_d` issue + omitted `∇h·∇n` — Bug 1/2) |
| 11 | Frank gradient flow monotone decrease | **PASS** (max positive ΔE = −0.39) |
| 12 | V0 reads ball/torus/double-torus b1=0/1/2, genus 0/1/2 (analytic + diffuse φ>φc) | **PASS** |
| 13 | V0 φc- and resolution-robustness of torus b1=1 | **PASS** |
| 14 | V1 crossing exists (small K→ball, large K→torus), K*≈0.32 | **PASS** (full K*=0.3196, quick K*=0.331) |
| 15 | V1 anchoring-OFF control removes crossing (mechanism isolation) | **PASS** (dF≈+32.36 flat = pure area penalty, elastic≈0) |
| 16 | Full Q-tensor companion honestly reported as NOT crossing | **PASS** (dF>0 at W=0.5, 2.0) |
| 17 | C03 (volume b1 vs surface genus) stated, not conflated | **PASS** |
| 18 | target_encoded=false justified (no hole/handle/genus term; standard anisotropy only) | **PASS** (with minor note, §C) |
| 19 | no_touch: `genesis/diagnostics/measures.py`, `rooms/official/**` untouched | **PASS** (git status: only new module/test/dir + ci.yml) |
| 20 | Determinism: all RNG seeded (`np.random.default_rng(seed)`), no time/date, K* reproducible | **PASS** (identical K* on rerun) |
| 21 | Frozen constants; `--quick` only subsamples (grid/steps/sweep), never touches physics | **PASS** (nq.FROZEN unchanged; CONFIG_QUICK differs only in N/steps/seeds/sweep) |
| 22 | Scope stops at F1: φ is fixed, no Cahn–Hilliard evolution of φ implemented | **PASS** (no φ update anywhere) |

---

## A. Physics correctness

- **S_eq**: `s_eq` solves `3A + BS + 2CS² = 0` on the nonzero branch; matches the numeric minimiser of the uniaxial Landau energy to 1e-6. The `relax`→S_eq unit test (tol 0.02) is a valid end-to-end confirmation.
- **LdG bulk molecular field** `−(A_eff Q + B(Q²−trQ²/3 I) + C trQ² Q)` (then detraced): verified an **exact** discrete gradient (rel err 6e-9). `(Q²)_zz` reconstruction `= trQ² − (Q²)_xx − (Q²)_yy` is correct. `A_eff` interpolation `A_in·h + A_out·(1−h)` with `h=clip(½(φ+1))` correctly drives Q→0 outside.
- **L2 elasticity** `½L2 (div Q)²` and its molecular field `L2·ST(∂_i(divQ)_j)` symmetrised: **exact** (rel err 6e-9). Good.
- **Fournier–Galatola planar-degenerate anchoring**: `N = Q̃ − P Q̃ P`, `Q̃ = Q + (S_eq/3)I`, `P = I − νν`, energy `W|∇φ| ‖N‖²`, molecular field `−2W|∇φ| ST(N)`: **exact** (rel err 9e-9). The `‖N‖²` off-diagonal double-count (factor 2) and the `−2` prefactor are consistent. Anchoring is correctly localised to the interface via `|∇φ|`, and the unit test confirms homeotropic ≫ tangential anchoring energy.
- **Descent / sign discipline**: for every term the finite-difference directional derivative of F along +H is **negative** — no sign errors anywhere. The full-Q and Frank energy histories are strictly monotone non-increasing. The gradient flow **does descend the same energy `energy_terms`/`frank_energy` report**.

## B. Is the crossing an artifact or real?

Real, and the isolation is clean:
- **Shape-blind ensemble**: `frank_min`/`relax_min` apply the *identical* seed recipe (`kinds=(azimuthal, random, uniform) × seeds`) to both ball and torus; the min-over-seeds is taken identically for both. This is a fair protocol, not a shape-specific placement.
- **Mechanism control**: with `W=0` the dF collapses to a flat ≈+32.36 (pure interfacial-area penalty, elastic≈0 at all K) — no crossing. So the crossing *requires* the anchoring-forced defects, exactly the F0 §5 causal control. The energy decomposition confirms the mechanism: the **ball** pays growing elastic **and** anchoring (0.01→24.2) because a tangent field on S² is obstructed (Poincaré–Hopf index +2), while the **torus** keeps both near zero (defect-free φ̂ tangent field) and only pays the fixed area penalty. This is the Koizumi/Lin–Wang mechanism, not a tuned coincidence.
- **Honesty about the limit**: the crossing lives in the fixed-length **Frank** limit. The **full Q-tensor** (which lets cores melt/escape, ξ=√(L1/|A|) sub-cell) is reported to **not** cross — prominently, in code, results JSON, AUDIT.md and docstrings. This is an unusually candid companion; the "reproduce the crossing" claim is not overstated.

## C. 8th audit / target-encoding

`target_encoded=false` is **justified**: F contains no hole/handle/genus/target-shape term; the only anisotropies are standard L2 splay/bend elasticity and standard planar-degenerate anchoring; the energy functional has no preferred axis. The crossing *direction* is selected by the swept ratio K, not by any seed.
- **Minor note (not a defect)**: the `azimuthal` seed (φ̂ about z) and the placed torus share the z-axis, so that ansatz is "aligned" to the torus. This is not target-encoding because (i) the same seed set is offered to the ball too, (ii) random and uniform seeds are also in the ensemble, and (iii) the functional, not the seed, evaluates the energy. Worth a one-line disclosure but does not undermine `target_encoded=false`.

## D. C03 distinction (volume b1 vs surface genus)

Correctly stated and not conflated. `betti3d` reports **volume** `b1(Ω)` via `b1 = b0 + b2 − χ` (valid for solids, b3=0), with `genus = b1` only when `b0=1 ∧ b2=0` (cavity-free handlebody). Code/output/AUDIT explicitly note that the boundary **surface** genus equals this and that **surface b1 = 2·genus** is a distinct count. Solid torus: volume b1=1, χ=0, genus 1 ✓. Double torus: b1=2, χ=−1, genus 2 ✓.

## E. no_touch discipline

Clean. `git status` shows only: new `genesis/models/nematic_qtensor.py`, new `tests/test_e047_sphere_to_torus.py`, new `experiments/e047_sphere_to_torus/` dir, and a **benign** `.github/workflows/ci.yml` edit (adds the e047 `--quick` CI step and a `test -f results/sphere_to_torus.json` existence check). `genesis/diagnostics/measures.py` and `rooms/official/**` are **untouched**. No existing experiment number, result, Room, or schema was changed.

## F. Determinism / frozen constants

Deterministic: the only randomness is `np.random.default_rng(seed)` in `seed_Q`/`_frank_seed`; no `time`, `datetime`, global `np.random`, or date dependence. K* is bit-identical on rerun. Physics constants are frozen in `nq.FROZEN` and echoed into the results JSON. `--quick` changes only N, steps, seed count, sweep lists and φc list (CONFIG_QUICK vs CONFIG_FULL); it never alters a physics constant. Consistent with F0 §2 discipline.

## G. Scope discipline

Correctly stops at F1. φ is **fixed** throughout — `relax`/`frank_relax` step only Q/n; there is no Cahn–Hilliard `∂_t φ` term implemented (the F0 pre-reg mentions it, but F1 deliberately omits it). No hole can open, no genus transition is attempted or claimed. The status line and AUDIT.md repeatedly and correctly refuse the emergence framing.

---

## Bugs / defects found

**Bug 1 (real, non-fatal — discretization inconsistency in the elastic term).**
The L1 elastic energy is `½L1 Σ(_d Q)²` using the *central-difference* gradient `_d f = ½(f₊−f₋)`, but the L1 molecular field uses the *compact* 7-point Laplacian `_lap` (`f₊ − 2f + f₋`). The exact discrete gradient of that energy is the **wide** operator `−_d(_d f) = −(f₊₊ − 2f + f₋₋)/4`, not `_lap`. Measured mismatch: L1 term rel err ≈ 17%; Frank elastic ≈ 45%. Consequences:
- It is still a **guaranteed descent direction** (in Fourier the two operators have symbols of the same sign, so ⟨δF/δQ, H⟩ retains sign; empirically every energy history is monotone). So *no V0/V1 claim is invalidated* and there is no sign error.
- But H is **not** the exact variational gradient of the reported F, so the relaxation converges to the stationary point of the compact-Laplacian operator, i.e. a slightly different / under-relaxed state than the true minimiser of the *reported* energy. Since the same operator is used for both shapes, the ball–torus **comparison is unbiased** and the crossing stands.

**Bug 2 (minor — omitted interface term in Frank force).**
`frank_relax` uses force `K·h·_lap(n) − 2W|∇φ|(n·ν)ν`, but the exact EL of `½K∫h|∇n|²` is `∇·(Kh∇n) = Kh∇²n + K∇h·∇n`. The `K∇h·∇n` term (nonzero only in the interface boundary layer) is dropped. Same character as Bug 1: descent preserved, comparison unbiased, but the reported energy is minimised only approximately.

**No overclaims found.** The docstrings already describe the relaxed states as "an honest, protocol-identical *approximation* of each shape's free-energy minimum," which is the correct hedge given Bugs 1–2. The literature is cited as *established mechanism*, not as a numerical K* match (contrast the e046 J* discrepancy noted in F0).

---

## Limits that MUST be disclosed (and mostly already are)

1. **Approximate gradient flow.** The elastic force (L1 and Frank) is a *preconditioned/inconsistent-stencil* descent, not the exact variational derivative of the reported energy; the interface `∇h·∇n` term is dropped. Relaxed states are approximate critical points. (Already partially covered by the "approximation of the minimum" wording; the stencil inconsistency itself should be stated.)
2. **Local, not global, minimum.** Energies are min-over-a-finite-seed-ensemble; no guarantee of the global minimiser for either shape. Honestly labelled, but a real limit on K*.
3. **ε/R and defect-core convergence.** K* is a single-resolution result; F0 §6's `ε/R→0` interface-artifact falsifier is explicitly deferred to F2. K*≈0.30–0.33 across N=24/28/36 is reassuring but not a convergence proof.
4. **Frank vs full Q-tensor.** The crossing exists only in the fixed-length Frank limit; the full Q-tensor does not cross at this resolution because cores escape sub-grid. This is the intended F2 ingredient and is disclosed — but it means V1 validates the *free-energy landscape mechanism*, not a resolution-converged full-Q result.
5. **K as control parameter.** Sweeping K/(σR) at fixed W, σ0, aspect, Rb is legitimate (all other constants frozen), but the crossing is a statement about one line through parameter space, not a phase diagram. Split/multi-handle/collapse regions (F0 §5) are out of F1 scope.
6. **Seed–axis alignment (minor).** The azimuthal ansatz shares the torus's z-axis; applied to both shapes and not decisive for the crossing, but worth an explicit line.

## Bottom line

V0 and V1 do exactly what they claim, with correct topology bookkeeping, correct bulk/L2/anchoring physics, a clean mechanism control, and disciplined role/scope/no_touch/determinism. The elastic force uses an inconsistent stencil (Bug 1) and drops an interface term (Bug 2); both are descent-preserving, shape-symmetric, and already implicitly hedged, so they lower the result from SOUND to **SOUND-WITH-CAVEATS** rather than to PROBLEMS. Recommend the team add a one-line note in `nematic_qtensor.py` and AUDIT.md that the elastic relaxation is a consistent *descent* operator but not the exact discrete gradient of the reported energy, and that this is why the flow's fixed point is an approximate (protocol-identical) minimiser.
