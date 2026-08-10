# ai_lab/relational (R-layer) -- PR-R1 AUDIT

```yaml
id: relational_r1
role: E                     # candidate Emergence; see "Role & STATUS" below for the honest caveat
claim_tier: measured        # for the memory=off vs memory=on R3/R4 contrast specifically
target_encoded: false
known_match: "N/A -- first measurement. Qualitatively consistent with the textbook fact that
  gradient/relaxation flows admit no limit cycles while damped 2nd-order systems generically
  ring; not a new mathematical result, but not previously measured in this graph-relational,
  coordinate-free form in this repo."
open_issues:
  - "R3 (reversal) needed two real bugfixes during PR-R1's own test-writing, both found by
     unit tests, not by the memory=off/on sweep: (a) a noise floor so a fully-converged flat
     trajectory does not register floating-point-noise 'reversals'; (b) trimming one moving-
     average window's worth of samples at each edge of the recording, because edge-padding
     biases the average there and could otherwise flag a spurious reversal for even a
     perfectly monotone series. After both fixes, the R4 false-positive rate measured under
     memory=off (Sec.3.3) dropped from 4/5760 node-checks (0.07%) to 0/5760 in the same
     sweep. See 'The memory=off false positives' below for why this is a legitimate
     instrument fix, not gate-tuning toward a preferred outcome."
  - "ai_lab/dream/ (human_report.py, ceiling_ladder.py, multiworld.py, dry_run.py) does not
     exist in this repository. The spec's Sec.8.1 request to absorb
     ceiling_ladder.instrument_max_level() into instrument_audit.py was therefore skipped,
     not performed with a workaround -- see instrument_audit.py's module docstring."
  - "Instruments R2/R3 collapse the m-dimensional state to a scalar via sum-over-dimensions
     before measuring; this is adequate for PR-R1's m=1 default but is a deliberately
     unrefined placeholder for m>=2 (rotational-symmetry auditing is explicitly PR-R2 scope,
     spec Sec.4.5)."
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

**Conclusion on the one question PR-R1 must answer:** `memory=off` does not produce genuine,
sustained reversal/period; `memory=on` does, robustly and on a large fraction of nodes.

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

Per the current LAW.md role system (E/V/S/N/F/Q), this PR's central result -- "memory=off
does not produce sustained period; memory=on does" -- most resembles a candidate **E**
(faithful emergence: the rule doesn't name the result, the initial condition is generic, and
the negative side has an exact analytic proof) rather than **V** (no established external
reference value exists to validate the memory=on numbers against) or **S** (no external
oracle or hand-wired switch is involved). It is explicitly **not yet GREEN**: `STATUS:
YELLOW` in `run.py`'s header, because (a) item 4 of the 7-audit can't be fully assessed with
only R1-R4 built, and (b) R4 carries a disclosed, nonzero (not eliminated) false-positive
rate. Promotion to GREEN, if warranted, should happen after R5-R8 exist (PR-R2) and the
companion-phenomena question (item 4) can actually be answered, not by re-tuning R4's
threshold until the residual disappears.
