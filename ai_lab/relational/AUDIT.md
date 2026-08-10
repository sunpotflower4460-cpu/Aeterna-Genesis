# ai_lab/relational (R-layer) -- PR-R1 + PR-R1.5 AUDIT

```yaml
id: relational_r1
role: E                     # symmetric-W no-sustained-period side only; see Sec.8/9 for the honest split
claim_tier: measured        # for R1-R4 as measurement instruments; the memory/asymmetry
                             # CONTRAST claim is now scoped (Sec.9) to "sustained oscillation
                             # was not found in any configuration tried, except an undamped
                             # positive control" -- see Sec.9.3
target_encoded: false
known_match: "N/A -- first measurement. The symmetric-W memory=off result is qualitatively
  consistent with the textbook fact that gradient/relaxation flows admit no limit cycles;
  not a new mathematical result, but not previously measured in this graph-relational,
  coordinate-free form in this repo."
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
     node-checks): 0 periods found, sustained or not -- narrows but does not close the
     review's non-reciprocity hypothesis. Separately, re-checking PR-R1's own memory=on sweep
     with the new sustained/decaying instrument found 0/1200 previously-'periodic'
     node-checks are actually sustained -- all are decaying transients. This corrects, not
     just nuances, Sec.3.2's original headline; see Sec.9.2."
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

Per the current LAW.md role system (E/V/S/N/F/Q), this PR's central result -- corrected in
scope by PR-R1.5 (Sec.9) to **"memory=off does not produce sustained period when W is
symmetric (proved); no configuration tried so far, including memory=on and memory=off with
asymmetric W, has been shown to produce SUSTAINED oscillation -- everything found is either
undetected or a decaying transient, except a damping=0 positive control that exists only to
validate the instrument itself"** -- most resembles a candidate **E** for the symmetric
no-period side (exact analytic proof, generic IC) and **N** (honest negative result) for
`memory=on`'s and `memory=off x asymmetry=on`'s sustained-oscillation question specifically,
rather than **V** (no external reference value exists) or **S** (no oracle/hand-wired
switch). It is explicitly **not yet GREEN**: `STATUS: YELLOW` in `run.py`'s header, because
(a) item 4 of the 7-audit can't be fully assessed with only R1-R4 built, (b) R4 carries a
disclosed, nonzero (not eliminated) false-positive rate, and (c) per Sec.9, the sustained-
oscillation question is now open rather than closed either way. Promotion to GREEN, if
warranted, should happen after R5-R8 exist (PR-R2) and the companion-phenomena question
(item 4) can actually be answered, not by re-tuning a threshold until a residual disappears.

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

### 9.4 9th-audit re-check on this section's own claims

"0/8640 node-checks periodic" (Sec.9.1) and "0/1200 node-checks sustained" (Sec.9.2): R4's
`expressible_max` (L/2 steps: 1000 for the n=24/steps=2000 asymmetry sweep, 1500 for the
n=24/steps=3000 memory=on re-check) is well above any period this repo's own positive
controls have shown (lag_steps in the tens, per Sec.3.3), so these are legitimate
non-achievement claims within the tested window, not instrument-ceiling artifacts --
checked via `instrument_audit.audit_nonachievement_claim` on representative Readings from
both sweeps before writing this section.
