# ai_lab/relational (R-layer) -- PR-R1 + PR-R1.5 + PR-R1.75 + PR-R1.9 + PR-R2-precheck AUDIT

```yaml
id: relational_r1
role: E                     # candidate E for the proofs (Sec.3.1, Sec.10.1, Sec.10.2) and
                             # for the negative/structural findings -- but the ONE positive
                             # claim (memory=on x asymmetry=on sustains) is DOWNGRADED as of
                             # Sec.12.2: under saturation="none" (what Sec.10.3/11 actually
                             # swept), 10/11 of the damping=0.05 "sustained_and_settled" flags
                             # are shown, by direct 20x-longer re-integration, to be
                             # pre-blowup linear-instability transients, not genuine bounded
                             # oscillation -- see Sec.12 before trusting Sec.10.3/10.4/11's
                             # positive numbers as "a limit cycle exists."
claim_tier: mixed           # memory=off (symmetric or asymmetric): proven + measured zero --
                             # UNCHANGED, unaffected by Sec.12 (saturation is irrelevant to a
                             # provably-zero result). memory=on, symmetric W: proven +
                             # measured zero (Sec.10.1/9.2) -- also unaffected. memory=on x
                             # asymmetry=on x saturation="none": Sec.10.3/11's "116/600 runs
                             # sustained-AND-settled" is CORRECTED by Sec.12.2 -- these are
                             # measured-but-misinterpreted: analytically Re(lambda_max)>0 for
                             # essentially all of them, and extending the integration window
                             # 20x confirms unbounded growth in 10/11 spot-checked
                             # damping=0.05 cases (the 11th decays). memory=on x asymmetry=on
                             # x saturation="cubic": NOT yet swept -- two spot-checks
                             # (Sec.12.2) confirm genuine bounded oscillation exists there,
                             # but this is anecdotal (n=2), not measured across a sweep.
target_encoded: false
known_match: "N/A -- first measurement. The symmetric-W memory=off/on no-period results are
  qualitatively consistent with the textbook facts that gradient flows admit no limit cycles
  and that damped 2nd-order systems with no forcing converge to equilibria; the
  memory=on x asymmetry=on sustained-oscillation mechanism (inertia turning a
  Gershgorin-marginal complex eigenvalue into genuine growth) is a first measurement in this
  graph-relational form, though it is a specific instance of the general fact that adding
  inertia to a non-normal (non-symmetric) linear operator can destabilize modes the
  first-order operator alone cannot -- not claimed as a new mathematical result in general,
  only newly measured and derived here."
open_issues:
  - "R3 (reversal) needed two real bugfixes during PR-R1's own test-writing, both found by
     unit tests, not by the memory=off/on sweep: (a) a noise floor so a fully-converged flat
     trajectory does not register floating-point-noise 'reversals'; (b) trimming one moving-
     average window's worth of samples at each edge of the recording, because edge-padding
     biases the average there and could otherwise flag a spurious reversal for even a
     perfectly monotone series. After both fixes, the R4 false-positive rate measured under
     memory=off (Sec.3.3) dropped from 4/5760 node-checks (0.07%) to 0/5760 in the same
     sweep. See Sec.3.3 for why this is a legitimate instrument fix (an independent analytic
     proof, Sec.3.1, predicted exactly zero before any sweep was run), not gate-tuning toward
     a preferred outcome."
  - "PR-R1.5 (Sec.9): the memory=off no-period proof requires W symmetric; the question was
     narrower than PR-R1 first stated. Measured memory=off x asymmetry=on (360 runs / 8640
     node-checks): 0 periods found, sustained or not. Separately, re-checking PR-R1's own
     memory=on sweep with the new sustained/decaying instrument found 0/1200 previously-
     'periodic' node-checks are actually sustained -- all are decaying transients. This
     corrects, not just nuances, Sec.3.2's original headline; see Sec.9.2."
  - "PR-R1.75 (Sec.10): memory=on x asymmetry=on -- the cell Sec.9.1 left untested -- DOES
     produce sustained oscillation (133/600 runs, 708/14400 node-checks). Sec.10.2 proves
     (Gershgorin) memory=off can never destabilize under this construction at any strength;
     Sec.10.1 proves memory=on+symmetric-W always decays; Sec.10.3 derives exactly why
     memory=on+asymmetric-W escapes both (q^2 > p*gamma^2 per eigenvalue of L, inertia
     converting a marginal rotational mode into real growth). This is the R-layer's first
     sustained-oscillation result and the natural entry point for PR-R2's phase/winding work."
  - "ai_lab/dream/ (human_report.py, ceiling_ladder.py, multiworld.py, dry_run.py) does not
     exist in this repository. The spec's Sec.8.1 request to absorb
     ceiling_ladder.instrument_max_level() into instrument_audit.py was therefore skipped,
     not performed with a workaround -- see instrument_audit.py's module docstring."
  - "Instruments R2/R3 collapse the m-dimensional state to a scalar via sum-over-dimensions
     before measuring; this is adequate for PR-R1's m=1 default but is a deliberately
     unrefined placeholder for m>=2 (rotational-symmetry auditing is explicitly PR-R2 scope,
     spec Sec.4.5)."
  - "asymmetry=True + plasticity=True is a known, undesigned interaction:
     _plasticity_step re-symmetrizes W every call, so plasticity would erase asymmetry after
     one step. Not fixed (out of PR-R1.5 scope); the reported asymmetry sweep uses
     plasticity=False (the default)."
  - "PR-R1.9 (Sec.11): adding `settled` (a trailing-quarter-only check, distinct from
     `sustained`'s whole-window halves check) shrinks Sec.10.3's headline from 133/600 runs
     (708/14400 node-checks) to 116/600 runs (396/14400 node-checks) sustained-AND-settled --
     17 runs' sustained signal was entirely still-growing within the recorded window, not yet
     plateaued. Measuring R8's spatial precondition (do settled nodes cover entire cycles):
     only 41/2660 (1.5%) of the relation graph's fundamental cycles have every node
     sustained-and-settled, though this is ~20x the rate an independent-node null predicts
     (settled nodes cluster locally, in cycles of length <=5, not across extended loops).
     Per review's own instruction, R8 (winding number) was NOT built this PR -- 1.5%,
     concentrated on short local loops, is too close to zero to be structurally meaningful;
     'why does the settled regime stay local instead of propagating' is the open question
     -- SUPERSEDED IN PART by Sec.12.2's finding below, see that bullet first.
  - "PR-R2 pre-check (Sec.12): review asked to verify the strength=1.0-3.0 dip in sustained-
     run count was not numerical before designing PR-R2's sweep around it. It is not (0/600
     non-finite, RK4 CFL margin >7x inside the stable region) -- but the investigation
     surfaced a bigger problem: Sec.10.3/11's sweep used saturation='none', which makes the
     memory=on ODE EXACTLY LINEAR, so no configuration with Re(lambda_max)>0 (essentially
     all of them -- only 34/600 configs are within floating-point noise of the marginal
     Re=0 boundary) can have a true bounded limit cycle; there is no nonlinearity to cap
     growth. Extending 3 spot-checked damping=0.05 runs' integration window 20x confirms
     this directly: 10/11 previously-'sustained_and_settled' flagged nodes diverge
     unboundedly (one grows from 0.2 to 1.6e9), the 11th (the one near-exactly-marginal
     case) decays instead of sustaining. Re-running the same 2 divergent configs with
     saturation='cubic' (the codebase's existing, unused-in-this-sweep nonlinear cap)
     produces genuine, durable bounded oscillation over the same extended window. Separately
     (Sec.12.3), the 20x cycle-clustering enrichment (Sec.11.2) is confirmed NOT a
     barabasi_albert-hub artifact -- random_regular (no hubs) shows an even higher
     enrichment ratio (22.3x vs BA's 12.9x). Net: Sec.10.3/10.4/11's positive
     sustained-oscillation numbers, as measured under saturation='none', mostly describe
     slow pre-blowup transients rather than genuine limit cycles; R7 should not be built
     against that data without first re-sweeping under saturation='cubic'. Flagged for
     review rather than unilaterally re-swept and re-decided.
     carried forward instead of a ceiling claim."
```

---

## 0. Blocking discrepancy found before writing any code

The task briefing asserted `ai_lab/dream/human_report.py`, `ceiling_ladder.py`,
`multiworld.py`, and `dry_run.py` are "confirmed present" in this checkout. They are not.
Verified directly:

- `ls ai_lab/` (this worktree and the shared checkout `/home/user/Aeterna-Genesis`) shows no
  `dream/` subdirectory at all.
- `git log --all --diff-filter=A --name-only -- 'ai_lab/dream/*'` returns zero commits on
  any branch (`main`, `claude/aeterna-genesis-1000-trials-sadnbm`, or this worktree's
  branch).
- `grep -ril "ceiling_ladder\|dream" tests/ .` (excluding this PR's own new files) finds
  nothing.

Consequence: this PR is built as a fully self-contained module under `ai_lab/relational/`,
exactly as spec Sec.9's file layout already has it (nothing in PR-R1's own scope actually
*requires* the dream pipeline to exist -- only spec Sec.7's PR-R4 wiring and Sec.8.1's
`ceiling_ladder` absorption do). The `ceiling_ladder` absorption is skipped per this task's
own stated fallback ("if this refactor looks risky or the existing code doesn't cleanly
factor out, it is fine to skip ... and instead just build the audit module standalone with
a clear TODO note") -- here the file does not exist at all, which is a stronger case for
skipping than "looks risky." `--no-record` in `run.py` attempts
`ai_lab.dream.dry_run.activate()` and falls back to a documented no-op (with a stderr note)
if the import fails, while still always suppressing disk writes regardless.

---

## 1. What was built (PR-R1 scope only)

| File | Contents |
|---|---|
| `ai_lab/relational/substrate.py` | Nodes (indices only), relation graph, real state `x_i in R^m`. First-order (`memory=off`) and second-order/inertial (`memory=on`) update rules per spec Sec.4.2. All six ingredient axes (`memory`, `saturation`, `conservation`, `plasticity`, `topology`, `m`) as both constructor kwargs and result-dict keys, defaults all minimal. |
| `ai_lab/relational/topology.py` | `random_regular`, `erdos_renyi`, `watts_strogatz`, `barabasi_albert` (pure numpy, no new dependency). `grid` exists as a comparison control, is never the default, and sets `geometry_was_given: true` when selected. |
| `ai_lab/relational/instruments.py` | `Reading` dataclass (exact fields from spec Sec.6) and R1 (`difference`), R2 (`direction`), R3 (`reversal`), R4 (`period`). |
| `ai_lab/relational/instrument_audit.py` | The 9th audit: `INSTRUMENT_EXPRESSIBLE_MAX_RULES` registry + `audit_nonachievement_claim` / `audit_readings` checkers. `ceiling_ladder` absorption skipped (see Sec.0). |
| `ai_lab/relational/run.py` | CLI only. LAW.md Sec.1 ten-item header verbatim, filled in honestly. Not wired into any hourly loop, multiworld, or report (`ai_lab/dream/` does not exist to wire into, and this is PR-R4 scope regardless). |
| `tests/test_r_substrate.py`, `test_r_instruments.py`, `test_r_instrument_audit.py`, `test_r_layer_vocabulary.py` | See Sec.4 below. |

Out of scope (correctly not built here, per task constraints): R5-R11, any wiring into
`ai_lab/dream/multiworld.py` or `human_report.py` (both nonexistent regardless), any hourly
budget/timeout config.

---

## 2. The hard constraint: difference-only core, explicitly-disclosed exceptions

Spec Sec.4.2's constraint is: the relational core references ONLY `(x_j - x_i)` over graph
edges -- never absolute position (moot here; nodes have none), never an absolute target
value, never a global aggregate (mean/sum), **unless that reference is itself an explicit,
disclosed ingredient axis that defaults OFF**.

At the all-minimal defaults (`memory=off, saturation=none, conservation=off,
plasticity=off`), the entire right-hand side of the ODE is exactly

```
dx_i/dt = Sum_j w_ij (x_j - x_i)      =    -(L x)_i          (L = graph Laplacian)
```

-- a pure difference operator, nothing else. Two things reference a per-node or aggregate
quantity, and both are explicit, disclosed, OFF-by-default axes, not smuggled defaults:

- **`saturation="cubic"`** adds `-a * x_i^3`, a term that looks at `x_i` alone (not a
  difference). This is spec Sec.4.2's own `a*g(x_i)` term, explicitly listed as part of the
  update rule and explicitly a switchable "does the system need something to stop
  divergence" ingredient (spec Sec.4.3). It never references another node or an aggregate.
  Default `saturation="none"` sets its coefficient `a` to exactly 0, so at default it does
  not exist in the equation at all.
- **`conservation=True`** projects the per-step increment to remove its across-node mean
  (`_project_conserving` in `substrate.py`), which DOES reference a global aggregate (the
  mean). This is exactly spec Sec.4.3's disclosed "does turning on strict conservation
  change whether period emerges" ingredient axis -- the point of exposing it as a flag is to
  measure its necessity, not to hide it in the default rule. Default `conservation=False`
  means this projection never runs.

**Incidental finding, not designed in:** even with `conservation=False`, the pure diffusive
term already conserves `Sum_i x_i` exactly for any symmetric weight matrix (all four
topology generators here produce symmetric `W`), because
`Sum_i Sum_j w_ij(x_j - x_i) = Sum_ij w_ij x_j - Sum_ij w_ij x_i = 0` when `w_ij = w_ji`.
This is a mathematical property of the graph, not something the substrate code enforces --
worth stating so the `conservation` flag's role isn't overclaimed as "the only thing that
conserves Sum(x)." It is the only thing that conserves Sum(x) once `saturation="cubic"` is
also on (the cubic term alone is not sum-conserving).

`plasticity`'s rule `dw_ij/dt = eta * ((x_j - x_i)^2 - w_ij)` references only the pairwise
difference and the edge's own current weight -- no absolute value, no aggregate.

---

## 3. The one question PR-R1 must answer: does memory=off genuinely fail to oscillate?

### 3.1 An exact analytic argument (not just an empirical sweep)

For `memory=off` (with or without `saturation="cubic"`), the update rule is EXACTLY a
gradient flow:

```
dx_i/dt = -(L x)_i - a x_i^3  =  -dV/dx_i,   where V(x) = (1/2) x^T L x + (a/4) Sum_i x_i^4
```

`L` is positive semi-definite (a graph Laplacian), so `V` is bounded below, and

```
dV/dt = grad(V) . dx/dt = -|grad V|^2 <= 0
```

strictly decreasing except at critical points. A system with a strictly decreasing Lyapunov
function **cannot have a periodic orbit** (a periodic orbit would require `V` to return to
its starting value after one period, contradicting strict monotonic decrease). This is a
textbook dynamical-systems fact, not something discovered here -- but it is a real,
falsifiable prediction for THIS system: no topology, no seed, no epsilon should ever produce
a sustained period under `memory=off`.

### 3.2 The empirical sweep

| Condition | Runs | Node-checks | R4 defined (any period found) |
|---|---|---|---|
| `memory=off`, 30 seeds x {random_regular, erdos_renyi, watts_strogatz, barabasi_albert} x {saturation=none, cubic}, n=24, steps=2000 | 240 | 5760 | **0 node-checks** (final instrument version; see Sec.3.3 for the false positives found and fixed along the way) |
| `memory=on`, 10 seeds x damping in {0.03, 0.05, 0.1, 0.15, 0.2}, n=24, steps=3000 | 50 | 1200 | **50/50 runs** found >=1 periodic node; **605/1200 node-checks (50.4%)** periodic overall |

The contrast is stark and reproducible: `memory=on` finds a genuine period in every single
swept run, on roughly half the nodes on average; `memory=off` never does, in this final
instrument version, across the entire sweep.

### 3.3 The memory=off false positives -- found, investigated, and fixed (not hidden)

The task instructions require: if `memory=off` shows any periodic behavior, report it
prominently and investigate before concluding. During initial development it did, rarely,
and this is the investigation and the resulting fix:

- The first version of `R3`/`R4` (before this PR's own unit tests were written) flagged 4
  node-checks out of 5760 (0.07%) as periodic under `memory=off` -- all single nodes within
  an otherwise non-periodic 24-node run (2 of 240 runs affected; `random_regular` and
  `barabasi_albert` topologies).
- Every flagged node's global (whole-graph) variance trajectory was independently checked
  and found **monotonically non-increasing** -- i.e. the system as a whole was settling,
  exactly as Sec.3.1 predicts. The detected "periods" were all very short-lag (`lag_steps` in
  {6, 9, 15} out of an expressible ceiling of `L/2 = 1000` steps) -- found in the first
  0.6-1.5% of the recording window, exactly where the multi-modal transient (several
  decaying graph-Laplacian eigenmodes with different decay rates, superposing into a signal
  that can cross its own local moving average a couple of times before everything settles)
  lives.
- Writing `tests/test_r_instruments.py::test_r3_zero_for_perfectly_monotone_series` (a
  perfectly monotone two-node series, nothing to do with the memory sweep at all) caught a
  second, more fundamental issue: `R3`'s moving-average residual is biased at the array
  edges (edge-padding makes the average track the boundary value rather than the true local
  trend there), which registered a small but real spurious reversal near the start of even a
  straight line. A follow-up unit test on the SAME monotone series then caught a third,
  narrower issue: once edges are trimmed, a residual that is itself pure floating-point noise
  (~1e-16, a perfectly-tracked linear trend) has a "peak" that is also noise, so a floor
  computed relative to that peak filters nothing.
- The fixes -- (1) trim one moving-average window's worth of samples from each edge before
  counting reversals, (2) anchor the noise floor to the series' own amplitude rather than the
  residual's own peak, (3) raise the autocorrelation-peak height threshold `min_ac` from an
  initial 0.15 to 0.5 -- were each justified independently of the memory=off/on outcome: (1)
  and (2) were driven by a plain monotone-series unit test with no periodicity question
  involved at all, and (3) was tuned against `memory=off`'s own analytically-known-zero
  ground truth (Sec.3.1), the same fixed threshold applied to every series regardless of
  which condition produced it. None of the three was chosen by looking at whether the
  memory=off vs memory=on CONTRAST came out a particular way.
- After all three fixes, re-running the exact same 240-run / 5760-node-check sweep gives
  **0/5760** false positives (down from 4/5760), and `memory=on`'s true-positive rate is
  unaffected (period still found in 50/50 swept seed/damping runs). This zero was not chased
  by tuning a threshold down to nothing -- it fell out of fixing two independently-motivated
  instrument bugs plus one threshold choice validated against a known-zero ground truth. It
  should still be read as "clean in this sweep," not as a mathematical guarantee that no
  finite sweep could ever show a short-lag artifact again; Sec.3.1's Lyapunov argument is the
  actual guarantee, and the instrument now matches it exactly in every case checked.

**Why the bugfixes are legitimate and not post-hoc gate-tuning (stated explicitly, per
review):** the reason to trust "0/5760 after the fixes" rather than suspect it was tuned to
produce a preferred number is that **the target value was never free to choose** -- Sec.3.1's
Lyapunov argument independently and analytically predicts EXACTLY ZERO sustained periods
under `memory=off` (symmetric W), derived without reference to this instrument, this sweep,
or this codebase at all. The three fixes were each individually justified against evidence
that had nothing to do with that target: (1) and (2) were caught and fixed using a plain
two-node monotone-series unit test that never touches the memory question; (3)'s threshold
was calibrated against `memory=off`'s own already-known-zero ground truth specifically
because that ground truth exists independently of the instrument being calibrated. What
makes this a bugfix and not gate-tuning is that we had an external, instrument-independent
answer (zero) BEFORE writing R3/R4, and fixing real defects brought the measurement into
agreement with that pre-existing answer -- the opposite of adjusting a threshold until an
observed number matches a preference formed after seeing the data. A tuning exercise with no
independent target to check against would not have this property; this one does.

**Conclusion on the one question PR-R1 must answer, corrected in scope (see PR-R1.5,
Sec.9):** `memory=off` does not produce genuine, sustained reversal/period **when W is
symmetric** -- Sec.3.1's proof requires that precondition, and PR-R1.5 (Sec.9 below) found
that removing it changes the answerable question. Separately, PR-R1.5 also found that
`memory=on`'s own "period found" claim above needs a caveat: see Sec.9.2 -- none of the
605/1200 node-checks reported here are SUSTAINED oscillation once amplitude-envelope
disambiguation exists.

---

## 4. Tests

- `tests/test_r_substrate.py` -- ingredient axes present in both kwargs and result dict at
  their documented defaults; `Sum(x)` conservation property (incidental for the pure
  diffusive default, explicit for `conservation=True` with saturation on); grid sets
  `geometry_was_given`; **the core memory=off vs memory=on contrast**, using aggregate
  statistics across multiple seeds (robust to the disclosed 0.07% single-node noise floor
  rather than asserting a literal zero every run).
- `tests/test_r_instruments.py` -- `Reading` field shape; R1-R4 behavior including
  precondition failure paths (N<2, no edges, no variance) and R4's `expressible_max = L//2`
  being an actual carried value (not just a comment), enforced structurally in
  `_first_autocorr_peak`'s `max_lag` argument.
- `tests/test_r_instrument_audit.py` -- `audit_nonachievement_claim`'s three failure modes
  (precondition unmet, target exceeds expressible_max, both fine) against both real Readings
  and hand-built ones with an artificially low `expressible_max`.
- `tests/test_r_layer_vocabulary.py` -- scans `run.py`'s full JSON output (several ingredient
  combinations, including `memory=on` where R4 is defined) for all seven spec Sec.5 forbidden
  words/terms and asserts none appear. This PR never emits the literal word
  "frequency"/"頻度" at all (R4's `1/T_i` quantity is returned under the key `rate_i`
  instead) specifically so this test can be a flat assert-absence check rather than a
  conditional-licensing check -- see `instruments.py`'s module docstring for the reasoning.

All new tests pass locally; see the PR's final report for exact pytest output. No
pre-existing test suite exists to touch or re-run here (`ai_lab/dream`'s tests, which the
task asked to identify and preserve, do not exist because the module does not exist).

---

## 5. 7-audit (LAW.md Sec.2)

See `run.py`'s module docstring `AUDIT (7):` block for the full per-item answer + reason;
duplicated in full there rather than re-typed here to avoid drift between the two copies.
Summary: items 1, 2, 3, 6, 7 pass cleanly. Item 5 is a genuine analytic pass for the
`memory=off` side (Sec.3.1's Lyapunov argument) but only an "observed, first measurement"
for `memory=on`'s specific numbers (no external theory value exists yet to check against).
Item 4 (untargeted companion phenomena) cannot be fully assessed with only R1-R4 built.

## 6. 8th audit (LAW.md Sec.7 -- target-encoding self-check)

1. **Does the initial condition pre-encode the conclusion?** No. `x_i(0)` is i.i.d.
   `N(0, epsilon^2)` noise with no shape, pattern, or frequency content placed in it; `v(0)`
   is identically zero for `memory=on` (not a velocity pattern chosen to produce rotation).
2. **Does a gate write the conclusion as an `if`?** No evaluation gate exists in PR-R1 at
   all -- `run.py` reports whatever `instruments.measure_all()` returns, with no
   pass/fail branching on the outcome.
3. **Would the gate pass on a null/trivial system too?** N/A (no gate in this PR); the
   closest analogue -- the R4 `min_ac=0.5` threshold -- was explicitly checked against
   `memory=off` (the "trivial"/null-for-periodicity case) and shown to produce a near-zero
   (not exactly zero, disclosed) false-positive rate there, which is the opposite of a gate
   that passes trivially.
4. **Does normalization/scale/lattice bake in the answer?** No default lattice (topology
   default is `random_regular`; `grid` is opt-in and flagged). `dt` is a fixed numerical
   regulator, not scaled to any target period. No spacing formula like `L/sqrt(N)` appears
   anywhere in this module.

`target_encoded: false` (see YAML header above).

## 7. 9th audit (spec Sec.8 -- instrument audit)

1. For every non-achievement claim actually made in this PR's own text (Sec.3.3's "no
   sustained period" for `memory=off`), is `expressible_max` above the claimed value? Yes --
   `R4`'s `expressible_max = L//2 = 1000` steps, and the claim is about ANY sustained period
   within that window, which the instrument can represent (periods from a few steps up to
   1000 steps are all expressible; only periods longer than 1000 steps would be
   inexpressible, and none of this PR's claims are about periods that long).
2. Is a `None` returned due to unmet precondition being misread as "did not reach X" anywhere
   in this PR's own claims? No -- `instrument_audit.audit_nonachievement_claim` flags exactly
   this case (`Q1`) and `run.py`'s own header text distinguishes "R3 precondition not met for
   this node" from "no autocorrelation peak found" as different `reason` strings (see
   `instruments.py::period`).
3. Does the observation window (`L`, snapshot count, `N`) create a hidden ceiling not
   accounted for? No -- `expressible_max` for R3 and R4 is *computed from* `L` on every call
   (not a fixed constant), so a shorter run automatically gets a tighter, honestly-reported
   ceiling rather than silently reusing a stale one.

`instrument_limited` is computed per-Reading by `instrument_audit.audit_nonachievement_claim`
and surfaced as a top-level boolean in every `run.py` result (`result["instrument_limited"]`)
so a later CI check can grep it mechanically, per spec Sec.8's requirement.

---

## 8. Role & STATUS (honest, not inflated)

Per the current LAW.md role system (E/V/S/N/F/Q), this PR's central result, final form after
PR-R1.75 (Sec.10): **memory=off never produces sustained oscillation (proven for symmetric
W by a Lyapunov argument, Sec.3.1; proven for any-strength asymmetric W by a structural
Gershgorin argument, Sec.10.2); memory=on with symmetric W also never does (proven by an
energy/Lyapunov argument, Sec.10.1); memory=on with asymmetric W DOES, in a substantial
fraction of swept configurations (133/600 runs, Sec.10.3), via a mechanism derived from the
equations of motion (q^2 > p*gamma^2 per eigenvalue of L) and verified against direct
eigenvalue computation, not merely observed.** This is a candidate **E** across the whole
result: every one of the four sub-claims (three negative, one positive) has both a
derivation and matching measurement, none of the four was assumed and then confirmed by a
gate built to find it, and the positive result was reported with the same rigor and weight
as the three negative ones (review's explicit instruction 4). Not **V** (no external
reference value exists for any of the four numbers) or **S** (no oracle/hand-wired switch).
It is explicitly **not yet GREEN**: `STATUS: YELLOW` in `run.py`'s header, because (a) item
4 of the 7-audit can't be fully assessed with only R1-R4 built -- and is now MORE relevant,
since a genuine sustained-oscillation regime exists to check companion phenomena against;
(b) R4 carries a disclosed, nonzero (not eliminated) false-positive rate; (c) the
`q^2 > p*gamma^2` threshold's sign was checked against direct eigenvalue computation in only
one topology/seed pair (11/12 matches) -- broader cross-validation is a natural PR-R2-or-
sooner follow-up, not yet done. Promotion to GREEN, if warranted, should happen after R5-R8
exist (PR-R2) and can characterize the newly-found sustained regime (period diversity,
ratio-locking, and finally phase/winding, now derivable from a genuine oscillation instead
of a decaying transient), not by re-tuning a threshold until a residual disappears.

---

## 9. PR-R1.5 (post-review addendum): symmetry precondition + sustained/decaying

Two additions requested by review, both completed before PR-R2. Full sweep data:
`ai_lab/relational/results_pr_r1_5.json`.

### 9.1 Asymmetry axis (`substrate.py::_asymmetrize`) and the corrected question

Sec.3.1's Lyapunov argument needs `W` symmetric -- that is exactly what makes
`dx/dt = -Lx - a*x^3` a gradient flow (`-Lx = -grad((1/2) x^T L x)` requires `L = L^T`, i.e.
`W = W^T`). An asymmetric `W` makes `-L` a non-symmetric linear operator; `dx/dt = -Lx` is,
in general, no longer `-grad(V)` for any scalar `V`, so the proof's conclusion is not implied
-- a directed inhibition loop (`w_ij != w_ji`) is exactly the textbook route to complex
eigenvalues (oscillatory, undamped-in-principle solutions) without needing inertia at all.
**The question PR-R1 actually answered is therefore narrower than first stated: "does
memory=off fail to oscillate when the relation is symmetric (mutual)", not "...for any
relation."** Sec.3's text above and the YAML header's `known_match` have been read in that
corrected scope; no prior sentence was deleted, this section makes the scope explicit.

`asymmetry` (bool, default `False`) and `asymmetry_strength` (float, default `0.5`) are new
ingredient axes (both kwargs and result-dict keys, per spec Sec.4.3's requirement). For each
edge with base weight `w` from the topology-generation rule, a single scalar
`chi_ij ~ Uniform(-1, 1)` is drawn per edge (a magnitude given, not a direction/shape --
same standing as the initial epsilon) and `w_ij' = w(1 + s*chi_ij)`, `w_ji' = w(1 - s*chi_ij)`
-- edge EXISTENCE is untouched and the pair's AVERAGE coupling is preserved; only the
forward/backward split differs. Verified directly (not just by construction): edge existence
identical to the symmetric base, average of `w_ij'` and `w_ji'` matches the base weight,
all weights non-negative, and the initial condition draw for a given seed is byte-identical
regardless of `asymmetry` (a disjoint RNG stream is used). A computed (not asserted)
diagnostic `w_is_symmetric` is now carried on every `SubstrateResult`/result dict, so any
claim relying on Sec.3.1's precondition can be checked mechanically rather than assumed.

**Measurement: memory=off x asymmetry=on.** 30 seeds x 4 topologies x asymmetry_strength in
{0.3, 0.6, 0.9}, n=24, steps=2000, saturation=none (matching the linear case the proof
concerns) -- 360 runs, 8640 node-checks.

| | runs | node-checks |
|---|---|---|
| any period defined | **0 / 360** | **0 / 8640** |
| any sustained | 0 / 360 | 0 / 8640 |

Matched control (same 30 seeds x 4 topologies, `asymmetry=False`, otherwise identical): 0/120
runs defined, confirming this is the same known-zero baseline, not a sweep-configuration
artifact. `w_is_symmetric` was confirmed `False` for every asymmetry=on run and `True` for
every control run (the flag itself is exercised, not just assumed).

**Honest reading:** within the strengths tried (0.3-0.9, i.e. the two directions of an edge
differing by up to +/-90% of the base weight), this specific asymmetrization construction did
not produce ANY detected period, sustained or not -- not "produced decaying periods instead
of sustained ones" (Sec.9.2's finding for `memory=on`), but no period at all. This narrows,
but does not close, the review's hypothesis that non-reciprocity is a cheaper route to
oscillation than memory: either (a) this particular construction (average-preserving,
per-edge-independent skew) does not push the operator's eigenvalues far enough off the real
axis at these strengths/graph sizes, or (b) a genuinely oscillatory regime exists at higher
strength / different graph structure / larger n and this sweep did not reach it, or (c) it
does not exist for this update rule at all. None of these can be distinguished from a single
sweep; per the 9th audit (instrument_audit), R4's `expressible_max` (L/2 = 1000 steps here)
comfortably covers the tested window, so this is a genuine "not found in this range," not an
instrument ceiling -- but it is a claim about THIS sweep's range, not an exhaustive no-go.

### 9.2 Sustained vs. decaying (`instruments.py::_envelope_trend`) and its consequence

Rationale (per review): with `memory=on` and no external driving, damping (`gamma > 0`)
means every trajectory relaxes to a fixed point eventually -- a detected "period" (R4's
autocorrelation peak) may be a damped spiral's decaying ripple, not sustained structure.
Deriving a phase from a decaying transient (planned for R7/PR-R2) would measure the decay
rate, not the structure. `_envelope_trend` classifies a node's oscillation as
`sustained` / `decaying` / `growing` from the Hilbert-transform envelope MAGNITUDE only
(the angle half of the analytic signal is computed by `scipy.signal.hilbert` but never read
or reported -- "phase" stays undefined/unused until R7, respecting spec Sec.5's forbidden
vocabulary), comparing mean envelope amplitude in the second half vs. first half of the
trimmed recording window against a fixed, disclosed 15% tolerance
(`_ENVELOPE_SUSTAIN_TOL`, identical for every call). `R4_period`'s per-node entries now
always carry `sustained: bool` alongside `defined: bool` whenever `defined=True` -- exactly
the review's requirement that a decaying transient not be silently reported as if it were
equivalent to genuine periodic structure. `R3_reversal` also carries an unconditional
per-node `envelope` diagnostic (growing/decaying/sustained), independent of whether R4 later
finds a period on that node.

**Positive control (does the instrument actually detect "sustained" when it is genuinely
present, or does it just always say "decaying"?):** a synthetic pure sine (no decay) is
classified `sustained=True` (envelope ratio 1.01); a synthetic decaying sine, `sustained=False`
(ratio 0.40); a synthetic growing sine, `sustained=False`/`"growing"` (ratio 1.47). Physically,
`memory=on` with `damping=0.0` (a genuinely conservative, undamped run, n=24, steps=3000,
seed=7) gives `any_sustained=True`, `n_sustained_periodic_nodes=20/24` -- the instrument does
detect sustained oscillation when the physics actually has it.

**Re-examining Sec.3.2's own `memory=on` sweep (10 seeds x damping in {0.03,0.05,0.1,0.15,0.2},
n=24, steps=3000 -- the exact sweep already reported as "50/50 runs, 605/1200 node-checks
periodic"):**

| damping | node-checks defined | node-checks sustained |
|---|---|---|
| 0.03 | 170 | **0** |
| 0.05 | 148 | **0** |
| 0.10 | 106 | **0** |
| 0.15 | 94 | **0** |
| 0.20 | 87 | **0** |
| **total** | **605 / 1200** | **0 / 1200** |

**This corrects Sec.3.2's headline, not just adds nuance to it: of the 605 node-checks
originally reported as "period found" for `memory=on`, zero are sustained oscillation at any
damping value tested.** Every one is a damped spiral's decaying ripple during relaxation to
the fixed point -- exactly the review's predicted failure mode
("γ>0で外部入力がなければ全て固定点へ落ちる"). Sec.3.2's original table is left unedited above
(the numbers are correct as measured) but must now be read as "period WAS DETECTED, not that
it is sustained" -- the distinction this PR-R1.5 addendum exists to make. The instrument's
own positive control (damping=0.0, previous paragraph) confirms this is a real physical
absence in the damped sweep's parameter range, not an instrument bug hiding sustained
oscillation from view.

### 9.3 Combined honest statement (supersedes Sec.3's closing line for the sustained question)

No configuration measured in PR-R1 or PR-R1.5 -- `memory=off` (symmetric or asymmetric W) or
`memory=on` with any damping in {0.03, ..., 0.2} -- produces SUSTAINED oscillation. The one
condition that does (`memory=on, damping=0.0`) is an undamped conservative system with no
dissipation and no external input, included here only as an instrument positive control, not
as a claim about which ingredient axis "causes" sustained periodicity -- that question is
still open and is a natural target for PR-R2 or a further PR-R1.x, not resolved here.

### 9.3.5 (superseded by Sec.10 below -- kept as a pointer, not deleted)

Sec.9.3's "no configuration measured so far produces sustained oscillation" is now **corrected
by PR-R1.75 (Sec.10): memory=on x asymmetry=on DOES produce sustained oscillation**, in a
substantial fraction of swept configurations. Sec.9.3's text is left as written above because
it was an accurate summary of PR-R1.5's own measurements (which never combined memory=on with
asymmetry=on) -- see Sec.10 for the corrected combined picture and the mechanism.

### 9.4 9th-audit re-check on this section's own claims

"0/8640 node-checks periodic" (Sec.9.1) and "0/1200 node-checks sustained" (Sec.9.2): R4's
`expressible_max` (L/2 steps: 1000 for the n=24/steps=2000 asymmetry sweep, 1500 for the
n=24/steps=3000 memory=on re-check) is well above any period this repo's own positive
controls have shown (lag_steps in the tens, per Sec.3.3), so these are legitimate
non-achievement claims within the tested window, not instrument-ceiling artifacts --
checked via `instrument_audit.audit_nonachievement_claim` on representative Readings from
both sweeps before writing this section.

---

## 10. PR-R1.75 (second post-review addendum): memory=on x asymmetry=on

Requested by review, in order: (1) prove `memory=on`'s symmetric-W decay at the same rigor
as Sec.3.1's gradient-flow proof, (2) measure the untested cell (`memory=on x
asymmetry=on`), (3) locate the instability threshold analytically before sweeping, (4)
report whatever is found with equal weight either way. All four done; the untested cell
**does** produce sustained oscillation, and the mechanism is more specific than the
review's own hypothesis predicted -- see Sec.10.2/10.3. Sweep data:
`ai_lab/relational/results_pr_r1_75.json`.

### 10.1 The `memory=on`, symmetric-W, damped decay proof (requested Sec.1)

For `memory=on` with symmetric `W` (`L = L^T`), define the mechanical energy

```
E(x, v) = (1/2)|v|^2 + (1/2) x^T L x + (a/4) Sum_i x_i^4
```

(kinetic + the same potential `V` from Sec.3.1). The dynamics are `dx/dt = v`,
`dv/dt = -Lx - a*x.^3 - gamma*v` (substrate.py's actual `deriv2`, `_saturation` folded in).
Differentiating:

```
dE/dt = v^T (dv/dt) + d/dt[(1/2) x^T L x] + d/dt[(a/4) Sum x_i^4]
```

The middle term needs `L` symmetric: `d/dt[(1/2)x^T L x] = v^T L x` exactly, because
`x^T L v` and `v^T L x` are transposes of the same scalar and `L^T = L` makes them equal (so
the usual `(1/2)v^TLx + (1/2)x^TLv` collapses to a single `v^TLx`, with no leftover
cross-term -- **this cancellation is exactly where `W` symmetric is used**; Sec.10.2 shows
what survives when it is not). The last term is `a Sum_i x_i^3 v_i = a v^T (x.^3)`. Substituting
`dv/dt`:

```
dE/dt = v^T(-Lx - a*x.^3 - gamma*v) + v^T L x + a v^T(x.^3)
      = -v^T L x - a v^T(x.^3) - gamma|v|^2 + v^T L x + a v^T(x.^3)
      = -gamma |v|^2  <= 0   for gamma >= 0
```

exactly the review's derivation. `E` is bounded below (`(1/2)|v|^2 >= 0`; `L` PSD gives
`(1/2)x^TLx >= 0`; the quartic term `>= 0` for `a >= 0`), so `E` is monotonically
non-increasing and bounded below, hence converges. `dE/dt = 0` requires `v = 0`
identically -- and by LaSalle's invariance principle, the trajectory converges to the
largest invariant subset of `{v = 0}`, which (since `dv/dt` must also vanish there for
invariance) is exactly the set of fixed points `{(x, 0) : Lx + a*x.^3 = 0}`. **A trajectory
converging to a fixed point cannot be a sustained periodic orbit** -- this is the
second-order analogue of Sec.3.1's argument, and it is exact, not approximate: `E`'s
monotonic decrease was not observed, it was derived from the equations of motion.

One technical honesty note, not present in Sec.3.1's simpler first-order case: when
`saturation="none"` (`a = 0`, the PR-R1 default), `E`'s potential term `(1/2)x^TLx` is not
coercive along `L`'s kernel (the constant-vector / per-connected-component-mean direction,
since graph Laplacians always satisfy `L @ 1 = 0`). That direction is handled separately,
not by `E`: summing `dv_i/dt` over any connected component gives `d(v_mean)/dt =
-gamma*v_mean` exactly (the `Lx` and `x.^3` terms' component-sums vanish identically for
`a=0` and any `L@1=0`), a plain damped free particle with no restoring force, which
converges `v_mean -> 0` and `x_mean -> constant` on its own. Combining: every mode --
in `L`'s kernel or orthogonal to it -- converges to a fixed value. The conclusion (no
sustained oscillation) holds either way; only the *route* to proving it differs by whether
`saturation="cubic"` makes `E` fully coercive on its own.

**This proof is exactly what the empirical 0/1200 in Sec.9.2 is measuring**, closing the
loop the review asked for: Sec.9.2's re-check of PR-R1's own `memory=on` sweep found zero
sustained node-checks; this section is the reason why, for the symmetric-`W` case that
sweep used (all four topology generators here produce symmetric `W` by construction).

### 10.2 Why `memory=off x asymmetry=on` also found nothing: a structural (Gershgorin) proof

Before sweeping the untested cell, review asked for the instability threshold to be located
analytically. It was -- and the answer is sharper than "a threshold in asymmetry strength
exists": **for `memory=off` (first-order), no finite asymmetry strength of this
construction can ever destabilize the system, at any strength.** This is a consequence of
how `L` itself is built, independent of symmetry:

`_laplacian_diffusion` computes `dx/dt = (W@x) - deg[:,None]*x = -(D-W)x = -Lx` where
`D = diag(W.sum(axis=1))` -- the row sum, computed fresh from whatever `W` (symmetric or
asymmetrized) is actually in use. `Q := -L` therefore has `Q_ii = -deg_i` and
`Q_ij = w_ij >= 0` for `i != j`, with **every row summing to exactly zero** by
construction (`Q`'s row `i` sums to `-deg_i + Sum_{j!=i} w_ij = -deg_i + deg_i = 0`) --
this is precisely the generator matrix of a (possibly non-reversible) continuous-time
Markov chain, symmetric or not.

By the Gershgorin circle theorem, every eigenvalue of `Q` lies in the union of discs
centered at `Q_ii = -deg_i` with radius `Sum_{j!=i}|Q_ij| = deg_i` (all `w_ij >= 0`, so no
absolute value needed) -- **each disc's rightmost point is exactly `-deg_i + deg_i = 0`**,
regardless of `deg_i`'s value or how the row's weight is split between directions. So every
eigenvalue of `Q = -L` has `Re <= 0`, unconditionally -- hence every eigenvalue `mu` of `L`
has `Re(mu) >= 0`, **for any non-negative `W`, symmetric or asymmetric, at any strength**.
The `_asymmetrize` construction (Sec.9.1) only ever produces non-negative `W` (values are
clipped at 0, never made negative) with a row-sum-based `D` -- so this bound applies to it
exactly, with no strength-dependence: there is no threshold to cross, because `Re(mu)`
can never go negative in the first place.

**Verified, not just asserted:** an exhaustive numerical stress test (4 topologies x 15
seeds x asymmetry strength in {0.5, 2, 8, 30, 100} -- strengths far beyond the {0.3,0.6,0.9}
originally swept) found the worst `min(Re(eigenvalue))` across every one of those 300 cases
was `-7.8e-14`, i.e. exactly zero up to floating-point noise, never meaningfully negative.
This is why Sec.9.1's `memory=off x asymmetry=on` sweep (0/8640 node-checks periodic) found
nothing regardless of strength: **the first-order system's linear stability is
structurally guaranteed by this construction, not merely unobserved in the strengths
tried.** This also means Sec.9.1's honest reading ("(a) this construction does not push
eigenvalues far enough... or (b) a regime exists at higher strength...") can now be
narrowed: **(a) is proven correct and (b) is proven impossible for this exact
construction** -- a stronger, more useful negative result than the sweep alone could show.

### 10.3 The untested cell: `memory=on x asymmetry=on` -- sustained oscillation IS found

Sec.10.2's Gershgorin bound is about the *first-order* operator only. The review's
hypothesized mechanism was "asymmetry destabilizes `L` directly, past a threshold, which a
saturating nonlinearity then turns into a limit cycle" -- Sec.10.2 shows that specific
mechanism cannot happen (`L`'s own eigenvalues never destabilize). But **inertia
(`memory=on`) changes what "stable" means**, and this is where the review's intuition turns
out to be right for a more precise reason than first proposed.

**Derivation.** The second-order system's linear stability is governed not by `L`'s own
eigenvalues `mu` but by the characteristic equation of each mode, `lambda^2 + gamma*lambda +
mu = 0`, i.e. `lambda = (-gamma +/- sqrt(gamma^2 - 4*mu)) / 2`. Writing `mu = p + iq`
(Gershgorin guarantees `p >= 0`), solving `Re(lambda) > 0` for the '+' root reduces
(algebra: let `w = gamma^2 - 4mu = A + iB`, use `Re(sqrt(w)) = sqrt((|w|+A)/2)`, square
twice) to exactly:

```
q^2  >  p * gamma^2
```

-- **a clean, checkable per-mode threshold.** When `p = 0` (a purely imaginary `mu`, which
happens for `memory=off`'s "marginal" directions), *any* `q != 0` satisfies it: inertia
converts an undamped ROTATIONAL drift (which the first-order system merely carries forever
at constant amplitude, never growing) into genuine EXPONENTIAL GROWTH, because the
second-order characteristic equation is not linear in `mu`. When `p > 0`, growth requires
the imaginary part to dominate the real part scaled by `gamma^2` -- so weaker asymmetry
(smaller `q`) needs proportionally smaller damping to destabilize, and stronger damping
(`gamma`) suppresses it, matching the qualitative expectation that friction stabilizes.

**Verified against direct eigenvalue computation** (not just algebra): for `random_regular`,
seed=1, `gamma in {0.05, 0.08}`, asymmetry strength in `{0.1, ..., 1.0}`, the sign of
`max_k(q_k^2 - p_k * gamma^2)` over `L`'s 24 eigenvalues matched the sign of the directly-computed
`max_k Re(lambda_k)` in every case except one exact-zero boundary tie (floating-point noise at the
marginal strength=0.1 point, both quantities ~1e-5). This confirms the derived threshold
is the actual mechanism, not a coincidental correlation.

**Empirical sweep** (memory=on, damping in {0.0, 0.05}, 4 topologies, asymmetry strength in
{0.3, 1.0, 3.0, 8.0, 20.0}, 15 seeds each, n=24, steps=3000, saturation=none -- 600 runs,
14400 node-checks):

| | runs | node-checks |
|---|---|---|
| any period defined | 373 / 600 | 5749 / 14400 |
| **any sustained** | **133 / 600** | **708 / 14400** |

Sustained oscillation is not rare noise here -- it appears across a wide range of strengths
and both damping values, e.g. `damping=0.0, strength=0.3`: 32/60 runs sustained (363
node-checks); `damping=0.05, strength=1.0`: 3/60 runs sustained. The non-monotonic pattern
across strength (e.g. `damping=0.05`: 19 sustained runs at strength=0.3 but only 1 at
strength=8.0) is consistent with Sec.10.2's `q^2 > p*gamma^2` condition, since raising
strength grows BOTH `p` and `q` (not `q` alone) once strength is large enough that `p` stops
being pinned near its small-strength value -- there is no reason to expect monotonicity in
strength alone once both sides of the inequality are moving.

### 10.4 Combined honest statement (supersedes Sec.9.3)

**Sustained oscillation requires BOTH memory (inertia) AND asymmetry (non-reciprocal
coupling) together; neither alone produces it in any configuration measured across PR-R1,
PR-R1.5, or PR-R1.75.** The mechanism is understood analytically, not just observed:
`memory=off` is structurally barred from linear instability by Gershgorin (Sec.10.2, for
this construction, regardless of strength); `memory=on` with symmetric `W` is barred by the
energy/Lyapunov argument (Sec.10.1, for damping `gamma > 0`); `memory=on` with asymmetric
`W` escapes both barriers because inertia turns a marginal (Gershgorin-boundary) rotational
mode into genuine growth whenever `q^2 > p*gamma^2` for some eigenvalue of `L` -- and a
saturating nonlinearity (implicit even at `saturation="none"`, since `_laplacian_diffusion`
plus a bounded-degree graph and the RK4 integrator do not blow up unboundedly in the swept
range; a `saturation="cubic"` run was not separately re-verified here and is flagged as a
follow-up) then caps the resulting growth into a bounded, sustained oscillation rather than a
numerical blow-up. Checked directly (not just inferred from `any_defined` counts): 100
spot-checked configurations spanning all 4 topologies, all 5 swept strengths, and
`damping=0.0` (the least-stabilizing case in the sweep) all produced fully finite
trajectories (`np.all(np.isfinite(x_traj))`) over the full 3000-step run -- growth is
bounded, not merely undetected divergence.

Per review's instruction 4: **this positive result is reported with the same weight the
negative results (Sec.9.1, Sec.10.2) were.** It is not being treated as more or less
important for being the "found it" case. What is explicitly NOT done, per the same
instruction: no "gain mechanism" axis (e.g. amplitude-dependent negative damping) has been
added preemptively. It was not needed -- the existing `memory` x `asymmetry` combination
already supplies a gain mechanism (inertia converting rotational drift to growth), so
Sec.9.4's earlier framing ("this substrate only has a losing mechanism") is now known to be
incomplete: **the R-layer does have a mechanism for gaining amplitude, but it only exists in
the a memory-x-asymmetry interaction term, not in either ingredient's own equation.**
Whether a further, explicit gain axis is worth adding is a decision for a future PR, to be
made after R5-R8 exist and can actually characterize what has just been found (period
diversity, ratio-locking, and -- critically, since sustained oscillation finally exists to
derive it from -- phase and winding), not before.

### 10.5 9th-audit and 8th-audit re-check on Sec.10's own claims

- **9th audit:** "0/8640 periods, any strength" (Sec.10.2) is licensed by the same
  `expressible_max` reasoning as Sec.9.4 (window comfortably covers any period this repo's
  positive controls have shown). "133/600 runs sustained" (Sec.10.3) is a positive
  achievement claim, not a non-achievement claim, so the 9th audit's "before saying X did
  NOT happen, check the instrument could express X" does not apply to it directly -- the
  relevant check is instead that the *positive* claim is not an instrument artifact, which
  Sec.10.3's synthetic + physical positive controls (Sec.9.2) and the independent analytic
  derivation (matching sign in 11/12 direct checks) both support.
- **8th audit:** does the analytic threshold `q^2 > p*gamma^2` encode the answer into a
  gate? No gate was written from it -- it is a derived diagnostic used to explain the sweep
  *after* deriving it from the existing equations of motion (already-disclosed `memory=on`
  dynamics + `L`'s definition), not a new rule invented to match the data. The sweep itself
  (Sec.10.3) was run and reported in full (373/600, 133/600) rather than only reporting
  configurations that "worked."

## 11. PR-R1.9 (third post-review addendum): settled vs. still-growing, and where the
sustained regime lives spatially

Requested by review, before starting PR-R2, in this order: (1) measure whether
sustained-and-settled nodes concentrate on closed loops (R8's precondition), (2) add a
`settled` check distinguishing a genuinely plateaued oscillation from one still climbing
toward its eventual limit-cycle amplitude, and restrict any future R7/R8 to settled nodes,
(3) report where in the 600-run sweep the 133 sustained runs actually come from. All three
done. Analysis code and full per-run output: `topology.py::fundamental_cycles`,
`instruments.py::_envelope_trend`'s new `settled`/`settled_ratio` fields, and the rerun
script logged in this PR's commit (raw per-run JSON is reproducible from
`results_pr_r1_75.json`'s `kw`+`seed` for every run -- not itself re-committed, to avoid a
second multi-hundred-KB trajectory-adjacent artifact for data that regenerates
deterministically from the first one).

### 11.1 `settled`: a still-growing transient is not the same as a plateaued oscillation

Sec.10.3's `sustained` classification compares mean Hilbert-envelope magnitude between the
first and second HALF of the recorded window. Review's concern: a node that crossed
`q^2 > p*gamma^2` partway through the window and is still climbing toward its eventual
capped amplitude can average out to "roughly the same magnitude in each half" (most of the
window is already near-plateau) while its TRAILING portion is still visibly moving --
exactly the growing-transient mistake already avoided on the decaying side (Sec.9.2), now
on the growing side.

`_envelope_trend` (`instruments.py`) now also compares the mean envelope magnitude of the
LAST quarter of the window against the quarter immediately before it (not the whole first
half), with its own fixed tolerance (`_ENVELOPE_SETTLED_TOL = 10%`, disclosed, same for
every call). A synthetic positive control (flat-amplitude oscillation throughout) is both
`sustained` and `settled`; a synthetic negative control (flat for the first half, then a
25%-over-the-second-half ramp) passes the whole-window `sustained` check (ratio ~1.12, under
15%) while correctly failing `settled` (trailing-quarter ratio ~1.11, over 10%) -- this is
the exact failure mode review flagged, reproduced and caught (`tests/test_r_instruments.py`,
`test_envelope_settled_flags_a_still_growing_tail_even_when_sustained_by_halves`).

Re-running Sec.10.3's own 600-config sweep (identical `kw`+`seed` per run, so this is an
exact recheck, not a new sample) with the settled-aware instrument:

| | runs | node-checks |
|---|---|---|
| any sustained (Sec.10.3's original criterion, re-verified identical) | 133 / 600 | 708 / 14400 |
| **any sustained AND settled** | **116 / 600** | **396 / 14400** |

The `any_sustained` recheck reproduced Sec.10.3's 133/600 exactly (a determinism check on
the rerun itself, not just a restatement). Adding `settled`: 17 of the 133 runs' sustained
signal turns out to be entirely still-growing (no node in those runs plateaus within the
recorded window) -- a real correction, not a rounding difference. At the node-check level,
396/708 (56%) of the previously-"sustained" node-checks are genuinely plateaued; the
remaining 44% were caught mid-ramp. **The headline conclusion is not overturned** --
sustained oscillation still requires memory+asymmetry together, and a majority of the
originally-reported sustained node-checks survive the stricter check -- but the true
"finished settling into a limit cycle within this window" count is 396/14400 (2.75%), not
708/14400 (4.9%), and Sec.10.4's "133/600" headline should be read from here on as "133/600
runs showed a sustained signal, 116/600 of which had at least one node that had actually
settled by the end of the window."

### 11.2 Spatial distribution: does the settled regime concentrate on closed loops? (R8's precondition)

R8 (a future PR, winding number) needs a phase defined at every node around some closed
loop in the relation graph -- if settled nodes are scattered rather than clustered along a
cycle, R8 would have nothing to compute on even once built. Measured directly, not assumed:

**Method** (disclosed, not tuned to the answer): for each of the 116 any-settled-sustained
runs, rebuild the relation graph (edge existence only -- asymmetry never changes which edges
exist, `tests/test_r_topology.py::test_fundamental_cycles_unaffected_by_asymmetrization`),
compute its **fundamental cycle basis** (`topology.fundamental_cycles`: one cycle per
non-spanning-tree edge -- the standard, linear-time, well-defined stand-in for "the graph's
cycles"; enumerating every simple cycle is combinatorially infeasible in general and was
never attempted), and check whether every node on each cycle is `sustained_and_settled`.

**Result:** across all 116 runs, 2660 fundamental cycles were examined (mean length 4.92,
range 3-13 nodes). Only **41 / 2660 (1.5%)** have every node on the cycle
sustained-and-settled.

**This is close to zero, as review anticipated** -- but not featureless zero, and the shape
of the non-zero part matters for what comes next. The node-level density of
sustained-and-settled nodes among these 116 runs is p=14.2% (396/2784 node-checks, restricted
to just the qualifying runs). Under an independence null (nodes sustained-and-settled at
random with this same marginal probability, uncorrelated with their neighbours), the
expected fraction of length-L cycles fully covered is `p^L`; averaged over the actual
observed cycle lengths this predicts 0.077% (about 2 cycles out of 2660), roughly **20x
below** the observed 1.5%. So sustained-and-settled nodes are NOT scattered independently --
they cluster locally, more than chance would produce, consistent with the underlying
mechanism being a per-eigenmode phenomenon (Sec.10.3: a single unstable eigenvector of `L`
has spatially-correlated support, not i.i.d. per-node noise) rather than independent
per-node coin flips. But the clustering is SHORT-RANGE only: every one of the 41 fully-
covered cycles has length <= 5 (the shortest ones available in these graphs -- triangles and
near-triangles); no fully-covered cycle of length > 5 was found even though cycles up to
length 13 were examined. Sustained-and-settled nodes form small local neighbourhoods; they
do not organize into extended loops.

**Conclusion for R8 (per review's own conditional):** 1.5%, concentrated entirely on
short local loops, is close enough to zero that implementing R8 now would mostly return
"undefined," and on the rare loop where it did not, the loop would almost always be a
length-3-to-5 local cluster rather than a structurally interesting extended cycle -- not
evidence of anything R8 was built to measure. **Per review's instruction, this PR stops at
R7 (phase) and does not build R8.** The next question this raises, to take up before or
alongside R7: **why does the sustained-and-settled regime cluster into small local
neighbourhoods (20x above chance) rather than propagating along the graph to occupy an
extended loop?** -- not answered here; flagged as the open question PR-R1.9 leaves behind,
per review's own framing of what a near-zero (but non-random) result should become.

### 11.3 Where the 133/600 (and 116/600 settled-sustained) sustained runs actually are

From `results_pr_r1_75.json`'s per-run records (`kw`+`seed`, not re-aggregated by hand):

| axis | breakdown (sustained runs / 300 or /150 as noted) |
|---|---|
| damping | 0.0: **109/300** vs 0.05: 24/300 -- damping=0.0 accounts for 82% of all sustained runs |
| topology | barabasi_albert: **47**, erdos_renyi: 35, random_regular: 27, watts_strogatz: 24 (each /150) |
| asymmetry_strength | 0.3: **51**, 20.0: **38**, 8.0: **29**, 3.0: 11, 1.0: 4 (each /120) -- non-monotonic, a dip at 1.0-3.0, high at both the low (0.3) and high (8-20) ends, consistent with Sec.10.3's note that raising strength moves both `p` and `q` in the `q^2 > p*gamma^2` inequality, not `q` alone |

**Recommendation for PR-R2's scope:** concentrate on `damping=0.0`, `topology` in
`{barabasi_albert, erdos_renyi}`, `asymmetry_strength` in `{0.3, 8.0, 20.0}` (skip the
1.0-3.0 dip) -- this is where the sustained-and-settled signal actually lives; a full grid
sweep at PR-R2's presumably finer resolution is not needed and would mostly re-discover the
same near-empty regions Sec.10.3/11.3 already characterized.

### 11.4 Combined honest statement

Sustained oscillation (Sec.10.3) is real but, once "settled" is required, smaller than
first reported (116/600 runs and 396/14400 node-checks, not 133/600 and 708/14400) -- a
correction applied with the same rigor Sec.9.2 applied to PR-R1's own headline, not
smoothed over. Spatially, the settled regime clusters into small local neighbourhoods
(20x above an independent-node null) but does not extend to loops longer than 5 nodes, so
R8 (winding number) is not attemptable yet in any structurally meaningful way -- per
review's own conditional, this PR stops at R7 and leaves "why does clustering stay local"
as the next question, not "the ceiling," since nothing here rules out a longer-range
regime existing outside the sweep windows examined (Sec.10.3's 5 strengths, 2 damping
values, 4 topologies, 15 seeds -- a bounded, disclosed sample, not an exhaustive one).

### 11.5 9th-audit and 8th-audit re-check on Sec.11's own claims

- **9th audit:** "1.5% of cycles fully settled-sustained" and "116/600 runs, not 133/600"
  are both non-achievement-flavored claims (the near-zero R8 precondition; the shrinkage
  from Sec.10.3's headline), so the 9th audit does apply here. Instrument expressibility
  check: `fundamental_cycles` enumerates a well-defined complete basis (not a truncated or
  sampled subset -- every non-tree edge contributes exactly one cycle, verified in
  `tests/test_r_topology.py::test_cycle_space_dimension_matches_e_minus_n_plus_components`
  against the standard `E - N + components` formula), so "1.5%, not more" is not an artifact
  of under-searching the cycle space. `settled`'s own expressibility is bounded by the same
  window-length constraints as `sustained` (documented in `_envelope_trend`'s docstring;
  needs >=16 interior samples, well under the ~2900-sample windows these runs use).
- **8th audit:** does `_ENVELOPE_SETTLED_TOL = 10%` or the fundamental-cycle-basis choice
  encode the answer? Neither was tuned against Sec.10.3's sweep outcome: the tolerance was
  fixed before rerunning the sweep (chosen to be tighter than, but the same kind of
  constant as, `_ENVELOPE_SUSTAIN_TOL`), and the fundamental cycle basis is a standard
  graph-theory construction with no free parameter to tune -- the same basis is returned
  regardless of which nodes end up sustained-and-settled. The 20x-above-null clustering
  finding was computed, not assumed, against a pre-specified independence null (`p^L`
  averaged over the actual observed lengths), not a null chosen after seeing the 1.5%
  figure.

## 12. PR-R2 pre-checks: is the strength=1.0-3.0 dip numerical, is the cycle-clustering a
BA-hub artifact, and what does "settled" actually license before R7

Requested by review, before starting R7, in this order: (1) refocus the primary sustained
target on `damping=0.05` (dissipative), keeping `damping=0.0` (no dissipation channel) as a
control, not the main object -- review's reasoning: only `damping=0.05` has all three
ingredients of a genuine limit cycle (asymmetry injects, damping removes, a nonlinearity
caps), which is the mechanism that could plausibly connect to D3 (a loop that sustains
itself by running); (2) verify the 1.0-3.0 asymmetry-strength dip is not a numerical
artifact before designing around it; (3) verify the 20x cycle-clustering enrichment
(Sec.11.2) is not a `barabasi_albert`-hub artifact. All three were checked. (2) surfaced a
larger and more consequential finding than "is the dip numerical" -- reported in full below,
since burying it under (1)/(3)'s answers would violate the same equal-weight-reporting
standard applied throughout this PR series.

### 12.1 Refocusing on `damping=0.05` shrinks the sustained-and-settled count further

Re-filtering Sec.11.1's settled recheck to `damping=0.05` only: of the 24 runs Sec.11.3
originally reported as `any_sustained` at `damping=0.05`, only **11/24** are
`any_settled_sustained` once PR-R1.9's stricter check is applied (13 were still-growing, not
yet plateaued -- a substantially higher drop rate than `damping=0.0`'s 109->105, consistent
with review's own reasoning: with less dissipation to fight the asymmetry-driven growth,
`damping=0.05` runs take longer to visibly plateau within a fixed window, so more of them
were still mid-ramp at step 3000).

### 12.2 The strength=1.0-3.0 dip is NOT a numerical-integrity problem -- but "sustained" at
`saturation="none"` does not mean what it was reported to mean

**What was checked, exactly as requested:** re-running all 600 of Sec.10.3's configs and
recording, per run: whether `x_traj` is entirely finite; the trajectory's maximum absolute
value; the maximum-absolute-value ratio between the trajectory's first and last deciles (a
full-window growth check, coarser than but independent of `settled`'s quarter-only check);
and the analytically exact dominant growth rate `Re(lambda_max)` from the same
`lambda^2 + gamma*lambda + mu = 0` characteristic equation Sec.10.3 already derived (an
exact value, not a numerical estimate) plus the RK4 step's `dt*|lambda_max|` as a stability
margin.

**Result on the literal question asked:**
- **No NaN/Inf anywhere**: 0/600 runs have any non-finite value in `x_traj`.
- **No RK4 integration-stability problem**: `dt*|lambda_max|` ranges from ~0 to 0.363 across
  all 600 configs -- RK4's stability region extends to about 2.79 on the real axis and 2.83
  on the imaginary axis, so every config here sits more than 7x inside the stable region.
  The integrator is accurately resolving whatever the true ODE solution is; it is not
  introducing spurious growth or instability of its own.

**What those two clean results were actually measuring, though, exposed something bigger:**
`_max|x|` at strength>=1.0 is not merely large -- it is **astronomically** large (mean
`max|x|` climbs from ~1 at strength=0.3 to ~10^20 at strength=1.0, ~10^43 at strength=3.0,
~10^68 at strength=8.0, ~10^102 at strength=20.0, at `damping=0.05`; `damping=0.0` is
similar). These are IEEE-754-finite floating point numbers, so the naive
"finite = healthy" check above passes cleanly -- but a value of 10^100 is not a bounded
oscillation by any physical reading; it is mid-blowup. Investigating why: **`saturation="none"`
makes the `memory=on` ODE EXACTLY LINEAR** (`dv/dt = -Lx - gamma*v`, no `a*x^3` term when
`a=0`). A linear time-invariant ODE with any eigenvalue `Re(lambda) > 0` cannot have a
bounded limit cycle -- full stop, this is not a numerical claim, it is the textbook fact
that linear systems either decay, sit at a fixed point, orbit marginally (measure-zero,
`Re(lambda)=0` exactly), or diverge without any bound; there is no fourth option, because
there is no nonlinearity to cap growth. Checking directly: **only 34/600 configs (and 19/60
at the specific cell `damping=0.05, strength=0.3`) have `Re(lambda_max)` within floating-
point noise of exactly zero; every other config, INCLUDING every strength=0.3 config that
is not one of those 19, has a strictly positive `Re(lambda_max)`** (small at low strength --
e.g. 0.0011 to 0.046 at strength=0.3 -- but strictly positive, not zero).

**Direct confirmation by extending the integration window 20x** (steps=60000 instead of
3000, same `kw`+seed, so the same exact trajectory continued): every checked
`damping=0.05, strength=0.3` run previously classified `sustained_and_settled` (11 total; 3
spot-checked in full: `random_regular` seed=5, `erdos_renyi` seed=9, and the one
`Re(lambda_max)~=0` case, `random_regular` seed=12) shows one of two things once the window
is long enough to see past the original 150-time-unit recording:
- **10 of the 11** have `Re(lambda_max)` strictly positive (however small) and, when
  continued to 20x the original window, show **unmistakable, unbounded exponential
  growth** -- e.g. `random_regular` seed=5's flagged node grows from a max of 0.199 (within
  the original window, correctly reported as "settled" there) to 1.64x10^9 by the same
  point 20x further out; `erdos_renyi` seed=9 similarly grows from 0.196 to 648. The
  apparent "settling" PR-R1.9 measured was real WITHIN the recorded window -- not a coding
  bug -- but it reflects the window (150 time units) being short relative to the growth
  timescale (e-folding time ~22-900 time units at these strengths), not a genuine
  attractor.
- **The 1 case with `Re(lambda_max)~=0`** (`random_regular` seed=12, the sole
  quasi-marginal one of the 11) does NOT sustain either when extended 20x -- it decays
  (0.148 -> 0.020 over the extended window), meaning it is not on the unstable side of
  marginal, it is on the (very slowly) stable side.

**None of the 11 `damping=0.05` `sustained_and_settled` flags, extended past their original
window, represent a genuine indefinite limit cycle under `saturation="none"`.**

**Constructive confirmation -- the missing capping mechanism is exactly `saturation="cubic"`,
already in the codebase but not used in Sec.10.3/11's sweep.** Re-running both spot-checked
divergent configs (`random_regular` seed=5, `erdos_renyi` seed=9) with the ONLY change being
`saturation="cubic"` (default strength=0.1), same 20x-extended window: both grow initially
identically to their `saturation="none"` twins (confirming the early transient is unaffected
by the change -- the cubic term is genuinely small while amplitude is small) and then
**plateau and hold** -- seed=5's node settles into oscillating within roughly [3.9, 4.8] for
segments 4 through 19 (t=750 to t=3000, 15x the original window, no further growth); seed=9
similarly plateaus around [1.1, 1.5] after an initial rise. This is a real, durable, bounded
oscillation -- the thing `saturation="none"` cannot produce for any `Re(lambda_max)>0`
configuration, and does produce once the nonlinear cap Sec.10.4 assumed was "implicit" is
made explicit.

**Answer to the literal question (is the dip numerical):** the dip is not an integration bug
-- but the entire premise "count of sustained runs per strength measures where a real
limit-cycle mechanism operates" does not hold for `saturation="none"`. What that count
actually measures is closer to "how often was this strength's growth rate slow enough that a
3000-step window failed to reveal it" -- a window-length artifact, not evidence of two
distinct physical regimes. The non-monotonic pattern across strength is not explained by
this PR and should not be trusted as a real feature until re-measured under
`saturation="cubic"`.

**Consequence for R7:** R7 (phase) must not be built against `saturation="none"` sustained/
settled results -- there is essentially nothing genuinely sustained there to derive a phase
from; 10/11 of the current `damping=0.05` positive flags are pre-blowup transients and the
11th decays. Before R7 can proceed on solid ground, the `memory=on x asymmetry=on` sweep
needs to be re-run with `saturation="cubic"` (confirmed above to produce genuine bounded
oscillation on two independent spot-checks) so R7 has an actual attractor to measure, not a
slow transient. This is flagged here rather than decided unilaterally -- see the open
question this leaves for review.

### 12.3 The 20x cycle-clustering enrichment is NOT a `barabasi_albert`-hub artifact

Re-running Sec.11.2's fundamental-cycle-coverage analysis separately per topology (same
116 `any_settled_sustained` runs, same fundamental-cycle-basis method, no change):

| topology | any-settled-sustained runs | node density p | cycles examined | covered | fraction | observed/null ratio |
|---|---|---|---|---|---|---|
| `barabasi_albert` (hub-heavy) | 42 | 17.2% | 924 | 25 | 2.71% | **12.9x** |
| `erdos_renyi` | 30 | 17.8% | 636 | 12 | 1.89% | 18.4x |
| `random_regular` (**no hubs -- every node the same degree**) | 23 | 9.4% | 575 | 1 | 0.17% | **22.3x** |
| `watts_strogatz` | 21 | 8.5% | 525 | 3 | 0.57% | 29.1x |
| all pooled (Sec.11.2 baseline) | 116 | 14.2% | 2660 | 41 | 1.54% | 20.0x |

`random_regular`, which has NO hub structure at all (every node has identical degree), shows
an observed/null enrichment ratio (22.3x) that is not just present but HIGHER than
`barabasi_albert`'s own ratio (12.9x). If the clustering were an artifact of settled nodes
landing preferentially near BA's high-degree hubs (where short cycles concentrate
structurally), a hub-free topology should show a ratio close to 1x (no enrichment); it does
not. **The above-chance clustering (Sec.11.2) is not a BA-hub artifact -- it survives, and
is if anything stronger, in the topology with no hubs.** (Caveat carried over from Sec.12.2:
since this reuses the same `saturation="none"` `sustained_and_settled` flags, the clustering
finding inherits the same "measuring a slow transient, not a settled attractor" caveat and
should be re-checked once `saturation="cubic"` data exists -- flagged, not re-derived here,
since re-deriving Sec.11.2 under new data is R2 scope, not this pre-check's.)

### 12.4 Open question for review before R7 proceeds

Sec.12.2's finding is a course-correction, not a green light to keep going as planned: the
`damping=0.05` cell review asked to focus on does not currently contain a genuine sustained
oscillation under `saturation="none"`, and the fix (switch to `saturation="cubic"`) is
confirmed to work on two spot-checks but has not been swept. This PR stops here, before
building R7 or re-running the full sweep under `saturation="cubic"`, to report this rather
than silently substituting a different sweep than the one review asked to focus on.

### 12.5 9th-audit and 8th-audit re-check on Sec.12's own claims

- **9th audit:** "the dip is not numerical" and "the BA-hub clustering is not an artifact"
  are both non-achievement claims (rebutting a suspected problem), so the 9th audit applies:
  the finiteness check covers the entire `x_traj` array, not a subsample, and the CFL-margin
  check compares against RK4's documented stability region rather than an ad hoc threshold.
  The deeper "sustained is actually pre-blowup" finding is a positive discovery (a
  previously-unknown failure mode), not a non-achievement claim, but was still verified by
  direct 20x-window re-integration and an independent nonlinear-capping confirmation, not
  asserted from the analytic growth rate alone.
- **8th audit:** was the 20x extension window, the `saturation="cubic"` comparison, or the
  choice of which 3 configs to spot-check tuned to produce this result? The 20x figure was
  chosen before running any extended integration (a round, disclosed multiple, not fit to
  the data); the `saturation="cubic"` strength (0.1) is the codebase's existing default, not
  a value searched for; the 3 spot-checked configs were the first-listed
  `random_regular`/`erdos_renyi` runs plus the one exact-zero-growth-rate case (a
  structurally distinguished choice, not a cherry-picked one) -- and the finding (10/11
  diverge, 1/11 decays) was reported as a full count, not a curated example set.

## 13. PR-R2.1: re-sweeping under `saturation="cubic"`, with the definition of `sustained`
hardened against the failure mode that produced Sec.12.2's retraction

Requested by review, before the re-sweep: (1) separate what Sec.10.2/10.3's proofs still
establish from what Sec.10.4/11/12 wrongly concluded from them; (2) check
`saturation_strength` sensitivity before committing to a single value for the re-sweep; (3)
add an attractor-vs-orbit-family ("damage-recovery") instrument; (4) bake a long-window
re-check into the definition of `sustained` itself, not as a follow-up. All four addressed
below, in order, before the re-sweep's own results (Sec.13.5+).

### 13.1 What Sec.12.2 retracted, and what it did NOT retract

Sec.10.2's Gershgorin bound and Sec.10.3's `q^2 > p*gamma^2` threshold are both statements
about the **linear part** of the `memory=on` dynamics (`dv/dt = -Lx - gamma*v`, before any
`a*x^3` term is added) -- they are proofs/derivations from the linear operator's eigenvalues
and are **completely unaffected by whether `saturation` is `"none"` or `"cubic"`**, since
`saturation` only changes what gets ADDED to that same linear right-hand side. Nothing in
Sec.12.2 challenges either: Gershgorin's `Re(mu) >= 0` for `L` still holds exactly regardless
of `a`; the characteristic equation `lambda^2 + gamma*lambda + mu = 0` and its
`q^2 > p*gamma^2` instability condition are still exactly the LINEARIZATION of the dynamics
near the origin, valid for however long the trajectory stays close enough to the origin for
the cubic term to be negligible (empirically confirmed in Sec.12.2's own spot-checks: the
`saturation="none"` and `saturation="cubic"` trajectories for the SAME config were
numerically indistinguishable during the initial growth phase, only diverging once amplitude
grew large enough for the cubic term to matter).

**What Sec.12.2 retracted is a single additional INFERENCE that Sec.10.4/11 made on top of
those proofs**: "the linear instability, therefore, produces a bounded sustained
oscillation." That inference is false when `saturation="none"` (there is nothing to cap the
growth once it leaves the linear regime) and was never actually tested under
`saturation="cubic"` in Sec.10.3/11's own sweep, despite Sec.10.4 describing the cap as
"implicit."

**The correct two-stage structure** (a standard Hopf-bifurcation shape -- the linear part
sets the frequency, the nonlinear part sets the amplitude) is:

```
Stage 1 (PROVEN, saturation-independent): inertia + asymmetry -> linear instability
    Gershgorin (Sec.10.2): Re(mu) >= 0 for L, any W built by this construction.
    Characteristic equation (Sec.10.3): Re(lambda) > 0 iff q^2 > p*gamma^2 for some
    eigenvalue mu = p + iq of L. This is EXACT and requires nothing about saturation.

Stage 2 (TO BE CONFIRMED per configuration, saturation-DEPENDENT): linear instability +
    saturation -> bounded limit cycle. Requires saturation="cubic" (a > 0); with
    saturation="none" this stage cannot occur (Sec.12.2, an exact linear-ODE argument).
    Confirmed on 2 spot-checks with saturation="cubic" (Sec.12.2); the re-sweep in this
    section (Sec.13.5+) measures this stage properly, across many configurations, with the
    long-window definition hardening from Sec.13.4.
```

Everything downstream of this PR (R7's phase, and any future R8 winding-number work) depends
on Stage 2, not Stage 1 alone -- a linearly unstable mode without a nonlinear cap is not
structure to derive a phase from, it is a transient on its way to infinity.

### 13.2 `saturation_strength` sensitivity: is the default (0.1) a special value?

Before committing to a single `saturation_strength` for the re-sweep, checked whether
`a=0.1` (the codebase's pre-existing default, unrelated to this PR) is a boundary or
otherwise special value, or whether the capping mechanism is generic across `a`. Two of
Sec.12.2's spot-checked configs (`random_regular` seed=5 node=22; `erdos_renyi` seed=9),
each re-run at `a` in `{0.02, 0.1, 0.5, 2.0}` -- a 100x spread -- over a 20x-extended window
(steps=20000):

| `a` | `random_regular` seed=5 plateau mean\|x\| | `erdos_renyi` seed=9 plateau mean\|x\| |
|---|---|---|
| 0.02 | 4.398 | 2.535 |
| 0.10 | 2.038 | 1.831 |
| 0.50 | 0.908 | 0.727 |
| 2.00 | 0.446 | 0.442 |

**Every value produced genuine bounded oscillation** (no divergence at any `a` tried).
`random_regular` seed=5's plateau amplitude follows the standard Hopf-normal-form scaling
`amplitude ~ C / sqrt(a)` closely: `amplitude * sqrt(a)` is 0.622, 0.645, 0.642, 0.631
across the four `a` values -- consistent to within a few percent, which is itself evidence
this is a genuine (weakly) nonlinear Hopf-type mechanism rather than an artifact of one
particular `a`. `a=0.1` is an ordinary point on this curve, not a special or tuned one. The
re-sweep below (Sec.13.5+) uses `a=0.1`, the existing default, on this basis.

### 13.3 Hardening the definition of `sustained`: `verify.verify_long_window`

Two of this PR series's own positive-result retractions now trace to the identical root
cause -- a window too short to see continued change: PR-R1.5's re-check of PR-R1's memory=on
sweep (605/1200 "periodic" node-checks -> 0/1200 actually sustained, once the sustained/
decaying instrument existed) and Sec.12.2 (10/11 damping=0.05 `saturation="none"` flags ->
shown diverging once the window was extended 20x). Per review's instruction, this is now
addressed structurally rather than by a third after-the-fact correction:
`ai_lab/relational/verify.py::verify_long_window` re-runs the identical configuration at
`extend_factor=15` x the original step count and re-checks the node's classification on
that longer trajectory. **From PR-R2.1 onward, a node is only reported "sustained" in any
headline count if `verify_long_window` returns `verified_sustained=True`** -- a
short-window `sustained_and_settled` flag is a screening CANDIDATE only.

One implementation subtlety, caught while validating `verify_long_window` against a
config independently confirmed genuine by Sec.13.4's attractor check: the long-window
re-check uses `settled` (the trailing-quarter-vs-preceding-quarter comparison), NOT the
whole-window `sustained` classification (first-half-vs-second-half). Reason, found
empirically: a genuine limit cycle's initial transient (rise from near-zero to plateau
amplitude) takes a roughly fixed amount of TIME regardless of how long the total recording
is. At the original (screening) window length, that transient is a small fraction of the
recording, so the whole-window halves comparison is dominated by the (already-plateaued)
majority of the window and correctly reads "sustained." At `extend_factor=15`x that same
window, the SAME fixed-length transient is now a much smaller fraction of a much longer
recording -- but the first HALF of the extended recording still contains most of it, so the
first-half average is dragged down relative to the (fully plateaued) second half, and the
whole-window classification misreads a confirmed limit cycle as "growing"
(`random_regular` seed=5 node=22 under `saturation="cubic"`, extended to steps=45000:
`settled=True, settled_ratio~1.00` but `sustained=False, classification="growing",
ratio=1.59`, despite `check_attractor_recovery` independently confirming this exact
trajectory returns to its plateau amplitude after a perturbation, Sec.13.4). `settled`'s
trailing-quarter-only comparison does not have this failure mode -- it is unaffected by
how large a fraction of the recording the initial transient occupies -- so it is the
correct, window-length-robust criterion for a check whose entire purpose is to look far
past any transient. This is documented as a deliberate, disclosed design choice in
`verify.py`'s own docstring, not silently patched.

### 13.4 The damage-recovery / attractor-vs-orbit-family instrument

Per review's request (point 3): a genuinely sustained oscillation could still be either (a)
an ATTRACTING limit cycle -- perturb it and it returns to the same amplitude, i.e. it is
self-sustaining -- or (b) a member of a conservative FAMILY of periodic orbits (as in an
undamped oscillator, where every initial amplitude persists forever, unperturbed) -- perturb
it and it simply moves to a different family member, permanently. This is exactly the same
underlying measurement concept `ai_lab/dream/frontier_expander.py`'s capability roster
flags as `self_repair` / `damage-recovery` (status `UNMEASURED` there: "壊されたあと自分で
戻る" / "damage/recovery介入器が必要") for the separate, TDGL-based `dream/` system --
implemented here independently, for the R-layer's own physics, in
`ai_lab/relational/verify.py::check_attractor_recovery`. This file does not read or write
`frontier_expansion.json` or any `ai_lab/dream/` file; `achieved` is this module's own
explicit flag on the R-layer result it was computed from, not a change to the `dream/`
capability roster's own (differently-measured, differently-scoped) status.

**Method**: from a long (`extend_factor=15`x), settled trajectory, take a checkpoint at 60%
through the recording (well past the initial transient). Continue TWO independent runs from
that exact checkpoint state (same `x`, same `v`, same `W` -- `substrate.run`'s new
`x0_override`/`v0_override` continuation parameters, PR-R2.1): a CONTROL, unperturbed; and a
DAMAGED run, with the entire state (`x` and `v`) rescaled by `perturb_factor=0.4` at the
checkpoint (a deliberately large, disclosed perturbation -- 60% of the amplitude removed at
once). Both continue for `5x` the original screening window. Compare each run's own
plateau amplitude (mean `|x|` over its final quarter) for the originally-flagged node.
`achieved=True` iff the damaged run's plateau amplitude is within `RECOVERY_TOL=20%`
(relative, fixed and disclosed) of the control's.

**Result on the validated config** (`random_regular` seed=5, node=22,
`asymmetry_strength=0.3`, `damping=0.05`, `saturation="cubic"`, `a=0.1`): control plateau
amplitude 1.985, damaged plateau amplitude 2.001 -- a **0.8% relative difference**, far
inside tolerance. **`achieved=True`: this is a genuine attracting limit cycle.** Removing
60% of the amplitude at the checkpoint made no lasting difference; the trajectory returned
to essentially the identical plateau. This is the first direct, interventional (not merely
correlational) confirmation in this PR series that a measured R-layer oscillation is
self-sustaining in the specific sense review asked about, and the first R-layer result that
can be honestly compared to the `dream/` roster's `self_repair` capability concept (though,
again, as an independent measurement on different physics, not a shared instrument or a
change to that roster's own tracked status).
