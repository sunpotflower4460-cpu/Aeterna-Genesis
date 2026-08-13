# ai_lab/relational (R-layer) -- PR-R1 + PR-R1.5 + PR-R1.75 + PR-R1.9 + PR-R2.1 + PR-R2.2 + PR-R2.3 + PR-R2.4 + PR-R2.5 + PR-R2.6 + PR-R2.7 + PR-R2.8 + PR-R3 + PR-R3.1 + PR-R4 + PR-R5 + PR-R6 + PR-R7 AUDIT

```yaml
id: relational_r1
role: E                     # candidate E throughout: proofs (Sec.3.1, Sec.10.1, Sec.10.2,
                             # both saturation-independent per Sec.13.1), a fully corrected
                             # positive claim (Sec.13: genuine sustained oscillation
                             # requires memory+asymmetry+damping+a nonlinear cap together,
                             # verified at 15x window AND confirmed interventionally via
                             # damage-recovery, not merely observed), an explicit, structural
                             # fix (verify.py) preventing the SAME window-length mistake
                             # (Sec.9.2, Sec.12.2) from recurring a third time, and (Sec.14)
                             # R7 (phase) built on the corrected N with a fixed, disclosed
                             # transient-trim rule. PR-R2.6 (Sec.18, S-015 PENDING) applied
                             # that SAME window-length fix a fourth time, now to the
                             # SCREENING step itself (not just verification), and found the
                             # instrument's own false-negative rate is large enough that the
                             # reported persistent density is very likely understated by a
                             # factor of roughly 2.6-7.8x -- not yet confirmed exhaustively,
                             # but no longer safely assumed to be a minor correction either.
                             # PR-R2.7 (Sec.19) answered R8's viability DIRECTLY instead of
                             # via density: exact cycle-coverage counting on the expanded
                             # candidate pool (an upper bound) found exactly 2 length-5
                             # cycles covered, both from one run, both long-window verified
                             # TRUE -- R8's first-ever confirmed coverage in this series --
                             # but the measured winding on both is null (0, failing the
                             # smoothness gate). Also found the 24.0%-vs-30% comparison used
                             # mismatched denominators (conditional vs unconditional) and is
                             # not a valid comparison either way -- moot, since the direct
                             # count above already answers the question it was a proxy for.
                             # Also found (Sec.19.3) that long-window verification, batched
                             # per run instead of per node (`verify_long_window_all_nodes`,
                             # new), is ~13-17x cheaper than every prior PR in this series
                             # assumed -- exhaustive verification of the full sweep is ~58
                             # minutes, not many hours. PR-R2.8 (Sec.20) RAN that exhaustive
                             # verification: S-015 is now MEASURED, not pending (27.7%/31.6%
                             # density, exceeding even PR-R2.6's sampled 24.0%). This also
                             # falsified PR-R2.7 Sec.19.1's "candidates are an upper bound"
                             # assumption (only 44.3% of candidates truly verify; 73.9% of
                             # true positives were never candidates) -- recomputing cycle
                             # coverage on the TRUE verified set found 178 covered length>=5
                             # cycles (not 2), across 35 independent runs and all 4
                             # topologies: material is abundant, not scarce. Winding measured
                             # on all 178: 86 (48.3%) show nonzero raw winding, but 0/178
                             # pass the smoothness gate -- R8's determination is recorded as
                             # "this substrate's diffusive coupling does not produce a cycle
                             # on which winding survives the smoothness gate," not "material
                             # doesn't exist" and not "R8 is impossible." PR-R3 (Sec.21,
                             # S-016) added `coupling_form` as a switchable axis (default
                             # unchanged, diffusive) -- three new forms tested (bounded_tanh,
                             # cubic_odd, sinusoidal), full battery (exhaustive verification,
                             # cycle coverage, winding, damage-recovery) on the same 300-
                             # config sweep, screening abolished per S-015's exact FNR
                             # measurement. cubic_odd collapses to near-zero persistence
                             # (0.04%), exactly matching its predicted degenerate origin
                             # Jacobian (Sec.21.3) -- diagnosed as decay-or-blowup, not a
                             # numerical bug. bounded_tanh roughly DOUBLES density (40.9% vs
                             # diffusive's 27.7%) and cycle coverage (314 vs 178).
                             # bounded_tanh AND sinusoidal each produce exactly ONE
                             # smooth-winding cycle -- the SAME underlying graph
                             # (erdos_renyi seed=9, strength=0.3, 6-cycle) under both forms,
                             # robust to doubling the verification window -- the first
                             # nonzero result on this criterion in the entire series.
                             # Explicitly reported as a CANDIDATE/LEAD, not an achieved
                             # result: a naive chance-alone estimate puts P(>=1 false
                             # positive across ~504 trials) at ~22%, so one example cannot
                             # settle real-vs-chance on its own -- flagged for a future,
                             # broader sweep, not declared. PR-R3.1 (Sec.22) tested this ONE
                             # example directly, per review's correction that 2 hits on the
                             # SAME graph under 2 coupling forms is replication, not 2
                             # independent chance draws. Sign-symmetry (W->W^T): INCONCLUSIVE
                             # (eigenvalues of W/W^T are identical, so this test cannot
                             # isolate sign from spatial localization for this system).
                             # Perturbation robustness: STRONG CONFIRM, 14/14 (12 independent
                             # initial conditions + 2 amplitude-perturbation recoveries)
                             # reproduce winding=-1 with near-identical max_adjacent_step.
                             # Cycle-shift (223 nearby cycles tested): MIXED but coherent --
                             # survives deformation through the coherent node cluster
                             # (2 genuine detour confirmations), fails when substituting a
                             # diagnosed peripheral (low-degree) node. Combined verdict: NOT
                             # NOISE. Review accepted, corrected, and formally recorded
                             # S-017 ("winding arises from relation, but depends on coupling
                             # form and is spatially localized -- NOT to be generalized")
                             # and S-018 (persistence density is set by the coupling's
                             # nonlinear shape, not its linear part) verbatim (Sec.22.7).
                             # PR-R4 (Sec.23) then swept `bounded_tanh` broadly on 300
                             # entirely independent seeds (disjoint from the discovery
                             # sweep): density REPLICATED (41.7% vs 40.9%), but ZERO new
                             # smoothness-gate hits appeared across 284 new covered cycles.
                             # Combined total: 1 unique winding location out of 788
                             # covered-cycle checks across 133 independent graphs -- rarer
                             # than known when S-017 was written. Two plausible structural
                             # predictors (node degree, run-level 100% persistence
                             # saturation) were checked against the broader population and
                             # NEITHER survived (the density=1.0 hypothesis was explicitly
                             # retracted after checking 7 other fully-saturated runs: 0/72
                             # of their covered cycles were smooth). R8 was NOT built
                             # (review's explicit condition -- multiple independent hits --
                             # was not met). PR-R5 (Sec.24): review corrected S-017 itself
                             # (Sec.22.7, both original and revised text kept, verbatim) --
                             # the 14-trial perturbation battery was evidence the ONE known
                             # location is internally robust, not evidence the phenomenon
                             # occurs generally; that correction is now the standing text.
                             # Computed search power (need ~2360 covered-cycle checks for
                             # 95% confidence at the 1/788 point estimate), then found a
                             # near-free lever -- a broader (non-fundamental) simple-cycle
                             # basis applied to ALREADY-SWEPT PR-R4 data -- yielding 149x
                             # more candidates (214 -> 31,869) with no new simulation for
                             # the coverage check. This surfaced 5 NEW candidate locations;
                             # a window-doubling check (matching PR-R3.1's precedent) found
                             # 3/5 do NOT survive (the same short-window artifact this
                             # series has repeatedly diagnosed elsewhere) and 2/5 DO --
                             # bringing the total to 3 independent, window-robust winding
                             # locations (up from 1), though the 2 new ones have not yet
                             # had the FULL validation battery the original received.
                             # Directly relevant to PR-R4's own stated R8 condition
                             # (multiple independent graphs) -- flagged for review's
                             # decision, not acted on unilaterally. PR-R6 (Sec.25): review's
                             # own cross-referencing found the 3 known locations share ONE
                             # cell (erdos_renyi, strength=0.3) of a 20-cell grid; a
                             # concentrated re-sweep (300 new configs, 30x window baked in
                             # from the start, not a follow-up) REFUTED both the resulting
                             # predictions -- lower strength does NOT raise the hit rate (the
                             # 2 lowest strengths, 0.1/0.2, show ZERO hits out of 30 each;
                             # PR-R6's own "peak at 0.5" reading of 0,0,1,2,1 raw hits was
                             # ITSELF review's own error repeated -- see CORRECTION note
                             # below, counts this small cannot establish a peak, only that
                             # 0.1/0.2 are lower) and erdos_renyi is NOT confirmed as the
                             # highest-rate topology on this sample (random_regular's pooled
                             # count, 4/50, is nominally higher than erdos_renyi's 4/150, but
                             # see the same correction: also too few graphs, per topology, to
                             # rank confidently) -- both reported plainly, per review's
                             # explicit instruction. Unplanned positive finding: clustering +
                             # window-robustness together find the TRUE rate is 9/300=3.0%
                             # graphs (up from the earlier 2/300=0.67%), bringing the running
                             # total to 12 known window-robust locations. Denominator
                             # corrected from covered cycles to independent graphs
                             # (Sec.25.2, now the primary metric going forward); multiple-
                             # comparisons math explicitly documented (Sec.25.3: ~16 of 123
                             # and ~129 of 174 raw hits could be chance alone at the <0.05%
                             # null-rate ceiling, neither dispositive alone -- clustering +
                             # window-robustness together, not either alone, is the actual
                             # answer). WINDING_CANDIDACY_MIN_EXTEND_FACTOR=30 baked into
                             # winding_precheck.py's own definition of "candidate" (Sec.25.4)
                             # -- the 4th recurrence of the same short-window artifact, now
                             # structural rather than a follow-up check. The 2 PR-R5
                             # locations (seed=55/62) passed the FULL validation battery at
                             # seed=9's exact depth (Sec.25.5: 6/6 independent ICs,
                             # damage-recovery, 58/560 and 7/304 nearby-cycle confirmations)
                             # -- review's own precondition for building R8. R8
                             # (instruments.py::winding()) is now IMPLEMENTED (Sec.25.6),
                             # following R7's exact precedent: gated on R4's
                             # sustained_and_settled for every node in a caller-supplied
                             # cycle, discloses the same window-verification-is-the-caller's-
                             # responsibility caveat R7 discloses, reproduces the manual
                             # scripts' own numbers exactly on the seed=55 positive control.
claim_tier: mixed           # memory=off (symmetric or asymmetric): proven + measured zero --
                             # unaffected by saturation throughout (Sec.13.1). memory=on,
                             # symmetric W: proven + measured zero (Sec.10.1/9.2) -- also
                             # unaffected. memory=on x asymmetry=on x saturation="none":
                             # Sec.10.3/11's positive numbers are RETRACTED (Sec.12.2) --
                             # pre-blowup transients, not genuine oscillation, for an
                             # exactly-linear ODE with no capping mechanism. memory=on x
                             # asymmetry=on x saturation="cubic", damping=0.05: MEASURED,
                             # VERIFIED (Sec.13.6: 100/300 runs, 223 node-checks -- the
                             # damping=0.05-only N, see Sec.14.2), and ACHIEVED
                             # interventionally (Sec.14.1: damage-recovery/self-sustaining
                             # limit cycle confirmed, 8/8 sampled cases, D3's content) --
                             # this is the R-layer's first claim at the "measured, verified,
                             # AND achieved" tier, not just "observed." Cycle-clustering
                             # (Sec.14.3): reframed, not retracted -- verified oscillation
                             # localizes in degree-heterogeneous (hub-like) regions.
                             # R8 (winding): DETERMINATION RECORDED (Sec.20, PR-R2.8) -- NOT
                             # "impossible" and NOT "no material" (that was Sec.15/Sec.19.1's
                             # framing, both since superseded): the exhaustive TRUE-verified
                             # set covers 178 length>=5 cycles (35 independent runs, all 4
                             # topologies) -- material is ABUNDANT. Winding measured on all
                             # 178: 86 (48.3%) show nonzero raw winding, but 0/178 pass the
                             # smoothness gate (winding!=0 AND max step<pi/2) -- far below the
                             # <0.05% null rate expected under random phases at N>=5, so this
                             # is a real structural finding: this substrate's diffusive
                             # coupling clusters phases locally rather than permitting smooth
                             # spatial rotation. Recorded as "in this substrate/coupling-form/
                             # topology, no cycle currently produces winding that survives the
                             # smoothness gate" -- a substrate-specific null result, not a
                             # general claim about winding-number measurement. (History:
                             # Sec.15/S-012 found only triangles, structurally too short;
                             # PR-R2.7/Sec.19.1 found "2 covered cycles, both null" but that
                             # was later shown (Sec.20.2) to rest on a false "candidates are
                             # an upper bound" assumption and undercounted true coverage by
                             # ~89x.) PR-R2.4 (Sec.16) adds the SMOOTHNESS
                             # GATE review specified (winding!=0 AND max step < pi/2) --
                             # structurally requires N>=5 (not just "probably better than
                             # 3"), and collapses the null rate to <0.05% (5-100x below
                             # review's own naive (1/2)^N estimate). Priority interventional
                             # test (cut verified nodes' edges, watch neighbors): 53.3%
                             # (172/323) of non-verified direct neighbors are
                             # SELF-SUSTAINING once disconnected, not merely driven -- a
                             # genuine ~50/50 split (bimodal, not review's predicted
                             # "mostly driven"), reframing rather than resolving the
                             # propagation question. PR-R2.5 (Sec.17) classified those 172
                             # connected-state waveforms: OSCILLATION DEATH IS ZERO (0/172)
                             # -- review's own hypothesis is NOT supported by this data.
                             # Dominant category (119/172, 69.2%) is "missed detection":
                             # genuinely periodic motion that fails sustained_and_settled's
                             # gates -- most plausibly the SAME short-window artifact
                             # already fixed twice elsewhere (Sec.9.2, Sec.12.2/13.3),
                             # not yet applied to this population (flagged, not run). Per
                             # review's own conditional, NO coupling-form axis was added
                             # (oscillation death is the empty category, not dominant).
                             # PR-R2.6 (Sec.18, S-015 PENDING) ran that flagged fix: applying
                             # `settled` (not `sustained_and_settled`) to the SCREENING step
                             # rescues 21/119 (17.6%) of the missed-detection group for free
                             # (no new simulation), and long-window-verifies 58 of the
                             # remaining 98 (59.2%) -- 79/119 (66.4%) of that group is
                             # genuinely persistent. Applied sweep-wide, the same free fix
                             # nearly triples the raw candidate pool (423 -> 1175 node-checks
                             # out of 7200). A disclosed, seeded (2026) random sample of the
                             # two populations this creates (screened_out, n=6025, sampled 75,
                             # 15 verified = 20.0%; newly_promoted, n=752, sampled 50, 20
                             # verified = 40.0%) yields a corrected density estimate of 24.0%
                             # (1729/7200 estimated true positives) versus the previously
                             # reported 3.1% (223/7200) or 9.3% (223/2400) -- a 7.8x or 2.6x
                             # correction respectively, rough 95% CI approximately
                             # 15.0%-33.0%. This is close to, and cannot yet rule out being
                             # above, the ~30% density Sec.15 estimated as necessary for a
                             # length-6 cycle to become non-negligibly likely to be fully
                             # covered -- R8's outlook may change substantially, but this is
                             # explicitly marked PENDING (a 2-sample estimate, not an
                             # exhaustive resweep) not settled. Density-increasing
                             # implementation remains explicitly NOT pursued pending review's
                             # decision on how to act on this correction. CORRECTED by
                             # PR-R2.7 (Sec.19.2): the "24.0% close to 30%" comparison above
                             # used mismatched denominators (24.0% unconditional over 7200;
                             # ~30% conditional, matching 9.3%=223/2400's convention) and was
                             # not a valid comparison -- moot regardless, since PR-R2.8's
                             # EXHAUSTIVE, exact verification (Sec.20) superseded density-
                             # estimation entirely: S-015 is RESOLVED at 27.7%/31.6%, and
                             # cycle coverage recomputed on the TRUE verified set (not the
                             # candidate proxy Sec.19.1 used, which undercounted by ~89x)
                             # finds 178 covered cycles, not 2 -- see Sec.20 for the final
                             # account, including the winding measurement on all 178.
                             # PR-R6 (Sec.25): R8 IS NOW BUILT (instruments.py::winding()) --
                             # the review-stated precondition (matching validation depth
                             # across the locations used to justify it) was met first
                             # (Sec.25.5: seed=55/62 both pass the full battery at seed=9's
                             # depth), not retrofitted. Separately, the underlying phenomenon
                             # itself is now measured at 12 known window-robust locations
                             # (up from 3), 9 of which have ONLY the window-robustness check,
                             # not the fuller battery -- flagged, not yet run. The concentrated
                             # sweep also refuted both structural predictions review's own
                             # cross-referencing suggested (lower-strength enrichment,
                             # erdos_renyi-exclusivity) -- reported as refutations, not
                             # smoothed into the positive 3.0%-rate headline. CORRECTED by
                             # review immediately after: PR-R6's own write-up over-read
                             # those same small counts (0,0,1,2,1; 4 vs 4) as a "peak" and a
                             # topology ranking -- neither distinguishable from noise at this
                             # sample size, a third occurrence of the exact small-sample
                             # mistake this series keeps flagging. Corrected in place
                             # (Sec.25.1.1), scope narrowed to only what the counts support.
                             # PR-R7 (Sec.26): applied the full new pipeline (wide basis +
                             # clustering + native 30x window) to `diffusive` coupling --
                             # the one dataset with an independent theoretical prior of zero
                             # (S-016's gradient-flow argument) -- as a negative control.
                             # Result: NOT zero -- 3/300 graphs (1.0%) passed the same
                             # window-robustness check PR-R6's 9 unconfirmed locations
                             # passed. Per review's explicit instruction, none were
                             # auto-labeled a false positive; all 3 received the SAME full
                             # battery seed=9/55/62 passed. ALL 3 FAILED (0/6, 0/6, 1/6
                             # independent initial conditions reproduced smoothness, vs.
                             # 6/6 for every confirmed bounded_tanh location) -- a decisive,
                             # unambiguous false-positive result (review's branch (a), not
                             # (b)): S-016/S-017 are NOT overturned, but the window-
                             # robustness-alone check is now directly shown, on this
                             # project's own data, to admit false positives. Consequence:
                             # the "12 known locations" claim (Sec.25.8) is corrected to 3
                             # CONFIRMED (full battery passed) + 9 CANDIDATE (window-
                             # robustness only, now actively suspect, not yet battery-
                             # tested) -- Sec.25.8 annotated in place. New standing rule
                             # (Sec.26.5): "validated location" requires the full battery,
                             # not window-robustness alone. The phase-shuffle null rate
                             # (0.028%) was confirmed near-uninformative exactly as review
                             # predicted before it was measured (diffusive's locally-
                             # clustered phases only get MORE jagged when shuffled) --
                             # decision weight was placed on the full battery, not the
                             # shuffle, per review's explicit instruction.
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
     review rather than unilaterally re-swept and re-decided."
  - "PR-R2.1 (Sec.13): re-swept memory=on x asymmetry=on under saturation='cubic' with the
     definition of 'sustained' hardened (verify.py::verify_long_window, a mandatory 15x-
     window re-check baked into the definition itself, not a follow-up -- the third time
     this PR series has hit the same short-window mistake, now structurally prevented).
     Screening: 363/600 candidates. Verified: 240/600 runs, 663/1153 node-checks -- the
     R-layer's first genuinely robust positive sustained-oscillation count. A new
     interventional instrument, check_attractor_recovery (the R-layer's own instance of the
     measurement concept ai_lab/dream/frontier_expander.py's roster calls
     self_repair/damage-recovery, implemented independently, no dream/ files touched), finds
     damping=0.05 produces genuine self-sustaining attractors (8/8 sampled cases recover
     from a 60% amplitude perturbation) while damping=0.0 mostly does not (2/8) -- consistent
     with damping=0.0 lacking the dissipation channel needed to select a unique attracting
     amplitude rather than a conservative orbit family. Re-running the fundamental-cycle
     coverage analysis on this corrected data REVERSES Sec.12.3's conclusion: random_regular
     (no hubs) now shows ZERO cycle coverage while barabasi_albert/erdos_renyi (degree-
     heterogeneous) show strong enrichment (14.9x/29.7x) -- Sec.12.3's 'not a hub artifact'
     claim is retracted, though Sec.13.8 flags random_regular's sample as underpowered to
     fully rule out a weaker effect. R7 can now proceed against the damping=0.05,
     saturation='cubic', verify_long_window-confirmed subset specifically."
  - "PR-R2.2 (Sec.14): damage-recovery formally recorded ACHIEVED (Sec.14.1) -- D3's
     content, satisfied by the R-layer's own independent implementation of the dream/
     roster's self_repair concept (no dream/ files touched). The damping=0.05-only N
     (Sec.14.2) is 100 runs / 223 node-checks, not 240/663 -- the correct target for R7.
     Cycle-clustering (Sec.14.3) reframed, not retracted: verified oscillation localizes in
     degree-heterogeneous regions; at least one fully-covered cycle exists in
     damping=0.05-verified barabasi_albert (triangle [7,4,22], seed=0, strength=20.0) and
     watts_strogatz (2 triangles) -- a concrete, small, disclosed green light for a future
     R8, not built this PR. R7 (phase, instruments.py::phase()) is built, gated on R4's
     sustained_and_settled, with a FIXED transient-trim rule (last half of the recording,
     reusing the same boundary `settled` already validates, plus R3/R4's own edge-trim) --
     documented at the same location as the R3 moving-average edge-bias fix, per review's
     explicit instruction. R7's phase-unwrapping rate cross-checks R4's autocorrelation
     rate to within 3-5% on the validated example. Recorded as open, not resolved: 2/8
     sampled damping=0.0 cases DID recover (Sec.14.5) -- Sec.13.7's 'no dissipation, no
     attractor' account is not asserted as a universal law, since asymmetry's own energy
     redistribution is not ruled out as an alternative dissipation-like channel in some
     configurations."
  - "PR-R2.3 (Sec.15, S-012): R8 remains blocked, confirmed NOT a sample-size problem -- all
     3 fully-covered cycles are triangles (length 3), and length 3 is structurally unsuited
     to winding: null rate 0.25 at N=3, RISING to 0.57 at N=10 (winding_precheck.py, Monte
     Carlo, cross-validated against the exact N=3 closed form). The one real triangle's
     observed winding is 0 (phases cluster within 1.19 rad, below a semicircle) -- not
     evidence either way. Investigated why persistence stays local, per review's request:
     coupling strength is RULED OUT structurally (every edge has identical weight by
     construction); amplitude reaches most of the graph (72%/61% retention at one/two hops)
     so amplitude-reach is not the primary blocker; the leading untested hypothesis is
     phase-coherence/entrainment failure. Verified nodes have a modest (+10%) degree bias
     that cannot alone explain the much larger (7-30x) cycle-level clustering, implying
     spatial clustering beyond simple degree preference. Quantified the gap: the observed
     verified-node density (9.3%, 223/2400; or 3.1%, 223/7200, denominator-dependent) would
     need to roughly TRIPLE (to ~30%, even crediting the full observed enrichment) before a
     length-6 fully-covered cycle becomes even 1%-per-cycle likely -- a structural gap, not
     a sampling one. winding_precheck.py is a standalone precondition module, explicitly
     NOT R8 and not wired into instruments.py."
  - "PR-R2.4 (Sec.16, S-013): added the smoothness gate review specified (winding!=0 AND
     max adjacent step < pi/2) -- structurally requires N>=5 (3*(pi/2) and 4*(pi/2) both
     fail to exceed 2*pi, so triangles/squares can NEVER pass, for any phase assignment),
     and collapses the re-measured null rate to <0.05% for N>=5, itself 5-100x below
     review's own naive (1/2)^N estimate (e.g. N=6: measured 0.0005 vs guessed 0.0156).
     R8's launch condition is now: multiple fully-covered cycles of length >=5 (not 6),
     ideally N=5-10. Priority interventional test (verify.py::check_driven_vs_self_sustaining,
     substrate.py's new W_override): cut every edge between the verified node set and its
     non-verified direct neighbors at a checkpoint, compare each neighbor's post-cut
     plateau amplitude to a connected control, across ALL 100 verified damping=0.05 runs
     (not a sample). Result: 172/323 (53.3%) of non-verified direct neighbors are
     self-sustaining once disconnected, not merely driven -- a genuine, bimodal ~50/50
     split (31.6% clearly driven-only at <10% retention, 34.1% clearly self-sustaining at
     >=80% retention), NOT the 'mostly driven' pattern review's own hypothesis predicted.
     Self-sustaining fraction is highest in the hub-free topology (random_regular, 73.3%)
     and lowest in the hub-heavy one (barabasi_albert, 42.3%). This reframes, not resolves,
     Sec.15's propagation question: roughly half of the amplitude-receiving non-verified
     neighborhood already has its own capacity to sustain, yet still fails `verified`
     classification -- narrowing the open question to why self-sustaining-CAPABLE nodes
     fail R3/R4/settled's specific criteria. Per review's explicit instruction, no
     density-increasing work was attempted pending this split's resolution."
  - "PR-R2.5 (Sec.17, S-014): classified all 172 self-sustaining-when-cut node-checks'
     CONNECTED-state waveforms before theorizing, per review's instruction: (i) oscillation
     death (settles to a nonzero constant) = 0/172 -- review's own diffusive-coupling
     hypothesis is NOT supported by this data, so per review's explicit conditional, NO new
     coupling-form ingredient axis was added. (ii) frustration (aperiodic/irregular) =
     48/172 (27.9%). (iii) missed detection (genuinely periodic, fails
     sustained_and_settled's gates) = 119/172 (69.2%, the dominant category) -- a subset
     (21/119) shows exactly the settled=True/sustained=False transient-drag signature
     already diagnosed at the long window (Sec.13.3), now appearing at the short
     (screening) window too. Topology breakdown of this classification is roughly uniform
     (65-74% missed detection across all 4 topologies) and does NOT explain Sec.16.2's
     topology-dependent self-sustaining split -- that remains open. Leading, NOT-yet-tested
     hypothesis flagged for a future PR: 'missed detection' may resolve substantially via
     the same 15x-window verification already validated elsewhere in this series, since
     these 172 nodes never had that check applied (they failed short-window screening, so
     were never candidates for it) -- not run this PR (substantial compute cost, review's
     prioritization needed first). Density-increasing work remains explicitly not pursued."
  - "PR-R2.6 (Sec.18, S-015 PENDING): ran the fix Sec.17 flagged but did not run. The free
     fix (screening judged by `settled` alone, matching the already-fixed long-window
     criterion) rescues 21/119 (17.6%) of the missed_detection group with zero new
     simulation; long-window-verifying the remaining 98 directly (not sampled) confirms 58
     more (59.2%) -- 79/119 (66.4%) of that group is genuinely persistent, corroborating
     Sec.17.3's flagged hypothesis. Applied to the FULL original 2400-node-check sweep, the
     same free fix nearly triples the raw candidate pool (423 -> 1175). A disclosed, seeded
     (2026) random sample of the two resulting disjoint populations (screened_out, n=6025,
     sampled 75, 15 verified = 20.0%; newly_promoted, n=752, sampled 50, 20 verified =
     40.0%) gives a stratified corrected-density estimate of 24.0% (1729/7200 estimated
     true positives) against the previously reported 3.1% (223/7200) / 9.3% (223/2400) --
     a 7.8x / 2.6x correction, rough 95% CI ~15.0%-33.0%. This brings the density close to,
     and does not rule out exceeding, the ~30% Sec.15 estimated as necessary for a length-6
     cycle's full-coverage probability to become non-negligible -- R8's outlook may change
     substantially, matching review's own prediction, but this is a 2-sample estimate, not
     an exhaustive resweep, so it is recorded PENDING, not settled. CORRECTED by PR-R2.7
     (Sec.19.2): the '24.0% is close to 30%' comparison above uses MISMATCHED denominators
     (24.0%=1729/7200 unconditional; the ~30% figure is conditional, 9.3%=223/2400's style)
     and is not actually a valid comparison -- see Sec.19.2, and Sec.19.1 for the direct
     measurement that answers R8's viability without needing this comparison resolved. The
     48 frustration cases from Sec.17.2 were preserved (not discarded) in a new
     d0_registry.json, registered under destination D0 (open-ended exploration, no
     pre-chosen target shape) per review's explicit instruction. Density-increasing
     implementation remains explicitly NOT pursued, per review's instruction, pending
     review's decision on this correction."
  - "PR-R2.7 (Sec.19): per review's instruction, did NOT pursue firming up the density
     estimate; instead directly counted what density was always a proxy for. Across all 300
     damping=0.05 configs, 4155 fundamental cycles of length>=5 exist; using the free-fix
     candidate pool (settled=True, an upper-bound superset of true-verified) as the covering
     set, exactly 2 are fully covered -- both from ONE run (erdos_renyi, seed=4), sharing 4
     of 5 nodes. Long-window-verifying only those cycles' nodes (via the new
     verify_long_window_all_nodes, Sec.19.3): both verify TRUE, 2/2 -- the first confirmed
     length>=5 fully-covered cycle in this PR series. Applying winding_precheck.py (still
     explicitly NOT R8) to the real instantaneous phases: BOTH give winding=0 and fail the
     smoothness gate (one from tight local phase clustering, the other from a single
     outlier node's large phase jump) -- a disclosed null result on the one measurable
     example, reported with the same weight a positive result would get. Sec.19.2 confirmed
     review's suspicion that the 24.0%-vs-30% comparison used mismatched denominators
     (unconditional vs conditional) and is not valid either way -- moot, since Sec.19.1's
     direct count already answers what that comparison was a proxy for. Sec.19.3 found
     every long-window check run so far in this series called verify_long_window once PER
     NODE despite one rerun computing all 24 nodes' results at once; batching (new
     verify_long_window_all_nodes) measures a ~13-17x cost reduction, making exhaustive
     verification of the full 7200-node-check sweep ~58 minutes, not ~13-17 hours -- and
     found screening's own false-negative rate is comparable at the run level (37.5% within
     a small n=8 zero-candidate-run sample) to the node level, so run-level screening would
     not have rescued the problem either. Recommends screening's current use as a permanent
     filter is not well justified given these numbers, but this was NOT acted on --
     exhaustive verification was not run, per the standing instruction not to pursue firming
     up the density estimate. S-015 remains PENDING (Sec.19.4): not needed for this PR's R8
     determination, not resolved either." RESOLVED by PR-R2.8 immediately next: S-015 is now
     MEASURED (27.7%/31.6%), not pending -- see below.
  - "PR-R2.8 (Sec.20): ran the now-affordable exhaustive verification (Sec.19.3), the
     single largest thing this PR series had left unmeasured. S-015 is RESOLVED: exact
     density is 27.7% unconditional / 31.6% conditional (both exceed even Sec.18.3's
     sampled 24.0%). This also exactly falsified PR-R2.7 Sec.19.1's 'candidates are an
     upper bound' assumption (only 44.3% of candidates truly verify; 73.9% of true
     positives were never candidates) -- annotated as a correction in place, not silently
     fixed. Recomputing length>=5 cycle coverage on the TRUE (not candidate) verified set:
     178 covered cycles (not 2), spanning 35 independent runs and all 4 topologies --
     material is abundant, overturning review's own working assumption going into this PR.
     Computed winding on all 178 (batched, 35 reruns, ~100s): 86/178 (48.3%) show nonzero
     raw winding, but 0/178 pass the smoothness gate -- far below the <0.05% null rate
     Sec.16.2 predicts for RANDOM phases at N>=5, so this is a real structural finding, not
     insufficient sampling. R8's determination is recorded per review's requested framing:
     NOT 'R8 is impossible,' NOT 'material doesn't exist' (it does, abundantly) -- but 'in
     this substrate, under diffusive coupling, on these topologies, no cycle currently
     produces winding that survives the smoothness gate.' Item 2 (coupling-form axis)'s
     literal trigger condition ('still ~1-2 cycles') was not met, so it was NOT implemented
     this PR -- but Sec.20.4's 0/178 smoothness-gate pass rate is flagged as strong,
     at-scale evidence for exactly the mechanism review's own hypothesis for that axis
     proposed, left as an explicit open decision for review rather than acted on
     unilaterally."
  - "PR-R3 (Sec.21, S-016): review replaced the 'still ~1-2 cycles' trigger with a stronger
     one -- Sec.20.4's 0/178 smoothness-gate result on abundant material, plus review's own
     mechanistic account (diffusive coupling entrains phases locally, opposite to what
     winding requires) -- and asked for `coupling_form` as a switchable axis. Implemented
     (`substrate.py`, default unchanged): `bounded_tanh`, `cubic_odd`, `sinusoidal`, chosen
     as the natural next 'odd function of the pairwise difference' family, NOT designed
     toward winding -- Sec.21.2 discloses the one real tension (awareness of sinusoidal's
     Kuramoto-literature association) rather than concealing it. Sec.21.3 re-derived the
     theorem chain: the gradient-flow no-periodicity argument (memory=off, symmetric W) and
     the energy-decay argument (memory=on, symmetric W, damping>0) generalize to all three
     new forms (each is a gradient flow of a bounded-below potential); the q^2>p*gamma^2
     linear-instability argument does NOT generalize uniformly -- bounded_tanh/sinusoidal
     share diffusive's EXACT origin Jacobian (=-L, confirmed numerically), cubic_odd's
     origin Jacobian is the ZERO matrix. Full battery (Sec.21.4, screening abolished per
     S-015's exact 44.3%-precision/26.1%-recall measurement): cubic_odd collapses to 0.04%
     density (0 covered cycles), diagnosed as a genuine decay-or-blowup split, not a bug --
     confirming the predicted theorem breakage directly. bounded_tanh roughly DOUBLES
     density (40.9% vs diffusive's 27.7%) and cycle coverage (314 vs 178). bounded_tanh AND
     sinusoidal each produce exactly ONE smooth-winding cycle -- the SAME underlying graph
     (erdos_renyi seed=9, strength=0.3, length-6 cycle) under both forms, robust to doubling
     the verification window (15x->30x) -- the first nonzero result on this criterion in
     the entire series. Reported explicitly as a CANDIDATE/LEAD: a naive chance-alone
     estimate across ~504 total covered-cycle checks puts P(>=1 false positive) at ~22%, so
     this cannot be called achieved from one example; no new SETTLED.md achievement entry
     was written, left for review's decision. Screening formally abolished
     (`verify.py`'s module docstring, a standing note): every sweep from this PR onward uses
     `verify_long_window_all_nodes` directly, no short-window pre-filter."
  - "PR-R3.1 (Sec.22): review corrected the ~22% chance-alone estimate (Sec.21.4.2) -- 2
     hits on the SAME graph/seed/strength/cycle under 2 coupling forms is replication, not
     2 independent chance draws -- and asked for 3 targeted tests on this ONE example before
     any broader sweep. Sign-symmetry (W->W^T, global and local-edge-only): INCONCLUSIVE,
     not failed -- both reversals eliminate sustained oscillation on this node set entirely
     rather than flipping sign, diagnosed as expected given eigenvalues of W/W^T are
     IDENTICAL (only eigenvectors, i.e. spatial localization, differ under transpose) -- the
     test cannot isolate sign from location for this system. Perturbation robustness: STRONG
     CONFIRM -- 12 independent random initial conditions + 2 amplitude-perturbation
     recoveries (14 trials, 2 coupling forms) all reproduce winding=-1 with
     `max_adjacent_step` clustered in [1.4818, 1.4957]. Cycle-shift (223 nearby cycles
     found via manual DFS, networkx unavailable): MIXED but coherent -- 2 genuine 'detour'
     deformations through well-connected extra nodes preserve the same winding sign (plus 1
     trivial same-loop-reversed duplicate, disclosed as not new evidence); the one direct
     same-length node-swap this graph's structure offers FAILS (winding=0), diagnosed to a
     peripheral (degree-2) substituted node with a phase ~pi away from the original --
     consistent with a spatially bounded real structure, not unstructured noise. Combined
     verdict: NOT NOISE. A candidate S-017 write-up is drafted (Sec.22.4) for review to
     accept/edit/decline, not written into SETTLED.md unilaterally. Independently, recorded
     bounded_tanh's density-doubling (27.7%->40.9%) as its own finding: since bounded_tanh
     shares diffusive's exact origin linearization, the difference is entirely a large-
     amplitude effect; comparing all 3 linearization-matched forms suggests monotonicity
     (not boundedness alone) is the more load-bearing property (sinusoidal, also bounded but
     non-monotonic, has the LOWEST density of the three) -- offered as the most consistent
     interpretation of 4 data points, explicitly not a proven, isolated mechanism (would
     need an unbounded+non-monotonic 4th form to complete a 2x2 factorial, not built)."
  - "S-017/S-018 formally recorded (Sec.22.7, review's verbatim accepted text). PR-R4
     (Sec.23) opened S-017's own identified question ('why only here') with a broad,
     independent-seed sweep (`bounded_tanh`, 300 configs, seeds 50-64 disjoint from the
     discovery sweep's 0-14): density REPLICATED (41.7% vs 40.9%, confirming S-018 is not a
     fluke of the original seeds), but ZERO new smoothness-gate-passing cycles appeared
     across 284 newly covered cycles (`bounded_tanh` + a `sinusoidal` control sweep).
     Combined across both PR rounds: 1 unique winding location out of 788 covered-cycle
     checks spanning 133 independent graphs -- rarer than known when S-017 was written.
     Compared the hit against the pooled population on node degree (not distinguishing,
     44th percentile) and run-level persistence density (the hit's run is 100% saturated,
     but checked against 7 OTHER 100%-saturated runs in the new sweep: 0/72 of their
     covered cycles were smooth, several with LARGER max_adjacent_step than average --
     this hypothesis is explicitly RETRACTED, not left unchecked). No structural predictor
     was found. R8 was NOT built (review's explicit condition -- multiple independent hits
     -- not met). The 4th coupling form (S-018's factorial) was deferred, explicitly lower
     priority than this PR's other work, per review's own prioritization."
  - "PR-R5 (Sec.24): review identified their own judgment error in S-017 -- the 14-trial
     perturbation battery (Sec.22.2) showed the ONE known location is internally robust,
     not that the phenomenon occurs generally; S-017 is REVISED (Sec.22.7, both original
     and corrected text kept verbatim) to state only what is established: 1 location,
     internally robust, not yet reproduced elsewhere. Computed search power: ~2360
     covered-cycle checks needed for 95% confidence at the 1/788 point estimate (Wilson 95%
     CI [0.0224%, 0.7153%] -- wide, from a single observation). Found the cheapest
     production lever: a broader (non-fundamental) simple-cycle basis applied to the
     ALREADY-SWEPT PR-R4 data (300 graphs) -- 149x more candidates (214 -> 31,869 covered
     cycles) for ~10 minutes of new compute (winding only, no new verification). This
     surfaced 5 new candidate locations (clustered by shared nodes into 1 per underlying
     graph); a window-doubling robustness check eliminated 3/5 (the same short-window
     artifact diagnosed repeatedly elsewhere in this series) and confirmed 2/5 -- bringing
     the total to 3 independent, window-robust winding locations, though the 2 new ones
     have NOT yet had the full validation battery (independent initial conditions, damage-
     recovery) the original received. This is directly relevant to PR-R4's own stated R8
     condition (multiple independent graphs) -- flagged for review's decision, not acted on
     unilaterally; R8 was not built this PR either. Directly described (not compared) the
     original hit: winding is present continuously across ~90% of the analysis window (not
     a transient), the 6 cycle nodes oscillate at visibly different amplitudes, and direct
     graph-neighbors outside the cycle are also clearly oscillating. Implemented (but did
     not sweep) a 4th coupling_form, `cubic_repulsive` (phi(z)=z^3-z, unbounded and non-
     monotonic, origin derivative -1 -- locally repulsive, unlike every prior form),
     completing S-018's 2x2 design; the sweep itself is deferred to a future PR."
  - "PR-R6 (Sec.25): review's own cross-referencing found the 3 known window-robust
     locations share exactly ONE cell (erdos_renyi, strength=0.3) of a 4-topology x
     5-strength grid, motivating a concentrated re-sweep (300 new configs, 30x window baked
     in from the start, not applied as a follow-up filter). BOTH resulting predictions were
     tested and REFUTED at the ONLY resolution the raw counts support: 0.1 and 0.2 (0/30
     each) show zero hits. Review CORRECTED my own initial over-read of this same data (a
     third occurrence of the exact small-sample-pattern mistake review is itself flagging,
     see below): 0,0,1,2,1 raw hits across 5 strength bins does not establish a peak at 0.5,
     and 4/50 (random_regular) vs 4/150 (erdos_renyi) does not establish a topology ranking
     either -- both corrected in place (Sec.25.1) to state only what the counts support.
     The unplanned positive finding: clustering + window-robustness together (Sec.25.1)
     find the true rate is 9/300=3.0% graphs, far
     higher than the earlier 2/300=0.67% estimate, bringing the running total to 12 known
     window-robust locations (9 with window-robustness only, not yet the fuller battery).
     Per review's two required corrections: the denominator is now GRAPHS, not covered
     cycles (Sec.25.2, established as the primary going-forward metric), and the multiple-
     comparisons math is explicitly documented (Sec.25.3: at the <0.05% null-rate ceiling,
     ~16 of PR-R5's 123 raw hits and ~129 of this PR's 174 could be chance alone -- neither
     figure is dispositive on its own; clustering + window-robustness TOGETHER, not either
     alone, is the actual methodological answer, evidenced by the 174->9 and 123->5->2
     reductions). `WINDING_CANDIDACY_MIN_EXTEND_FACTOR=30` is now baked into
     `winding_precheck.py`'s own definition of a reportable candidate (Sec.25.4) -- the 4th
     recurrence of the same short-window artifact (605/1200, 116/600, 119 missed-detection
     nodes, PR-R5's 3/5), now structural rather than caught after the fact each time. The 2
     PR-R5 locations (seed=55/62) received the FULL validation battery at seed=9's exact
     depth (Sec.25.5: 6/6 independent initial conditions, damage-recovery, 58/560 and 7/304
     nearby-cycle-shift confirmations, both unanimous) -- satisfying review's own stated
     precondition for building R8. R8 (`instruments.py::winding()`) is now IMPLEMENTED
     (Sec.25.6), gated on R4's `sustained_and_settled` for every node in a caller-supplied
     cycle (mirroring R7's exact division of labor -- this instrument does not discover
     cycles itself), and discloses the same window-verification-is-the-caller's-
     responsibility caveat R7 already discloses for its own precondition. A positive control
     run through the actual instrument (seed=55, `erdos_renyi`, strength=0.3, 30x window)
     reproduces `winding=-1`, smooth, exactly matching Sec.25.5's manually-scripted number on
     the identical trajectory."
  - "Immediately after PR-R6: review caught a third occurrence of the exact small-sample
     over-read mistake this series keeps flagging -- PR-R6's own write-up called strength
     0.5 a 'peak' and random_regular the 'highest-rate topology' from raw counts of 0,0,1,2,1
     and 4 vs. 4, neither distinguishable from noise. Corrected in place (Sec.25.1.1);
     scope narrowed to only 'strengths 0.1/0.2 show zero hits,' the one claim the counts
     support."
  - "PR-R7 (Sec.26): applied the full new pipeline (wide basis + clustering + native 30x
     window) to `diffusive` coupling, S-016's independent theoretical negative control, per
     review's explicit instruction and pre-briefed interpretive frame (a diffusive hit must
     not be auto-labeled a false positive; the phase-shuffle null was predicted to be
     near-uninformative). Result: 3/300 graphs (1.0%) passed the window-robustness check --
     NOT zero. All 3 received the SAME full battery seed=9/55/62 passed (independent
     initial conditions, damage-recovery, cycle-shift) and ALL 3 FAILED (0/6, 0/6, 1/6
     independent conditions reproduced smoothness, vs. 6/6 for every confirmed location) --
     a decisive false-positive result, review's branch (a). S-016/S-017 stand, now tested
     far more severely than before and still holding. Consequence: the '12 known locations'
     claim (Sec.25.8) is corrected to 3 CONFIRMED + 9 CANDIDATE-NOW-SUSPECT (window-
     robustness only, not yet battery-tested) -- the SAME check that produced the 9 is now
     directly shown, on this project's own data, to admit false positives. New standing
     rule (Sec.26.5): 'validated location' requires the full battery, not window-robustness
     alone. Phase-shuffle null rate (0.028%) confirmed near-uninformative exactly as
     predicted -- decision weight was placed on the full battery per review's instruction.
     Operational note: this sweep was silently killed by container restarts twice before
     completing; fixed by per-config checkpointing and small foreground-driven batches
     instead of one long unattended background job. Next PR's natural priority: apply the
     full battery to the 9 now-suspect bounded_tanh locations before citing any of them as
     confirmed, before any R8-based automated search."
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

### 13.5 The `saturation="cubic"` re-sweep: screening

Same grid as Sec.10.3/11 (15 seeds x 4 topologies x 5 asymmetry strengths x 2 damping
values, n=24, steps=3000, dt=0.05), the ONLY change being `saturation="cubic"`,
`saturation_strength=0.1` (Sec.13.2 confirms this is not a special value):

| | Sec.10.3 (`saturation="none"`) | this re-sweep (`saturation="cubic"`) |
|---|---|---|
| any period defined | 373 / 600 | **600 / 600** |
| any sustained (whole-window halves check) | 133 / 600 | 478 / 600 |
| any sustained_and_settled (screening candidate) | n/a (PR-R1.9 addition) | **363 / 600** |

Capping growth changes the picture substantially at the SCREENING level -- every
configuration now shows SOME periodic structure, since nothing diverges to numerical
extremes anymore. This alone is not yet trustworthy (per Sec.13.3, a short-window
`sustained_and_settled` flag is a candidate, not a result) -- Sec.13.6 applies
`verify_long_window` to all 363 candidates.

### 13.6 Long-window verification: the authoritative sustained count

Applying `verify.verify_long_window` (steps x 15 = 45000, re-checking `settled` per
Sec.13.3's window-length-robust definition) to every one of the 363 screening candidates
(one long rerun per candidate RUN, re-checking every originally-flagged node from that
single simulation):

| | candidates (screening) | **verified** (`verify_long_window`) |
|---|---|---|
| runs with >=1 qualifying node | 363 / 600 | **240 / 600 (40%)** |
| node-checks | 1153 | **663** |

**240/600 runs and 663/1153 node-checks survive 15x-longer re-integration.** This is now
the R-layer's authoritative sustained-oscillation count -- a substantially larger and more
robust positive result than Sec.10.3/11's `saturation="none"` numbers ever were, precisely
because `saturation="cubic"` supplies the missing capping mechanism Sec.12.2 showed was
required. 490 candidate node-checks (1153-663, 42%) did NOT verify at 15x -- consistent
with some candidates being genuinely slower-converging transients even under
`saturation="cubic"` (still approaching their plateau at 15x the screening window) rather
than a fixed population of false positives; this was not separately investigated further
(e.g. by trying an even longer window) and is left as a known limit of this PR's testing
budget, not asserted either way.

By damping, node-check level: `damping=0.0`: 440/730 verified (60%); `damping=0.05`:
223/423 verified (53%) -- comparable verification RATES at the screening-to-verified step
for both damping values, in contrast to Sec.13.7's finding that verification alone does not
distinguish genuine self-sustaining limit cycles from conservative orbit families.

By asymmetry_strength (run count, `any_verified`): `0.3`: 17, `1.0`: 10, `3.0`: 45, `8.0`:
72, `20.0`: 96 -- **a clean, close-to-monotonic increase with strength** (only a small dip
at 1.0 relative to 0.3), unlike Sec.11.3's non-monotonic `saturation="none"` pattern (high
at 0.3, dip at 1.0-3.0, secondary rise at 8-20). This resolves that earlier puzzle
retroactively: the non-monotonicity was itself an artifact of window-length-vs-growth-rate
interactions under an uncapped system (Sec.12.2) -- once growth is genuinely capped,
stronger asymmetry straightforwardly produces a faster, more reliably-verified approach to
a stable plateau, matching the ordinary intuition that stronger destabilization settles into
its limit cycle sooner (within a fixed observation window) rather than exhibiting a
mysterious middle-strength gap.

### 13.7 Damage-recovery result: `damping=0.05` produces genuine attractors; `damping=0.0`
mostly does not

Ran `check_attractor_recovery` on a disclosed, non-cherry-picked sample: up to 2
verified-sustained runs per (topology, damping) combination (8 topology-damping cells x up
to 2 = 16 samples), selected by sorting on (topology, damping, strength, seed) and taking
the first 2 per cell -- a deterministic rule fixed before looking at any result, not a
search for favorable examples.

| damping | achieved | rel_diff of achieved cases | rel_diff of non-achieved cases |
|---|---|---|---|
| **0.05** | **8 / 8 (100%)** | 0.002 - 0.090 | n/a (none failed) |
| **0.0** | **2 / 8 (25%)** | 0.012, 0.059 | 0.229, 0.566, 0.593, 0.593, 0.598, 0.603 |

**Every single `damping=0.05` sample (8/8) recovers to within a few percent of its
pre-perturbation plateau amplitude after a 60%-amplitude perturbation. Only 2/8
`damping=0.0` samples recover, and the 6 that do not stay near 55-60% relative difference --
essentially the perturbed amplitude itself, not a partial return.** This is exactly review's
own physical prediction from the original focus-correction request: with `damping=0.0`
there is no linear dissipation channel, so a cubic term alone (a conservative, spring-like
restoring nonlinearity, not friction) caps growth into a BOUNDED but still
energy-parametrized family of periodic orbits -- perturbing the amplitude just moves the
trajectory to a different family member, and nothing pulls it back. `damping=0.05` supplies
the actual dissipative balance (asymmetry injects, damping removes, the cubic caps) that
makes a specific amplitude an attractor rather than one of a continuum. **The
`saturation="cubic"`, `damping=0.05` cell is confirmed, directly and interventionally, to be
where genuine self-sustaining limit cycles live in this substrate; `damping=0.0`'s
"verified sustained" count (Sec.13.6) is now understood to be, for the most part, a
different and weaker structure (a conservative orbit family, not a self-maintaining one) --
`verify_long_window`'s settled/plateau check alone cannot see this distinction (a
conservative orbit is just as flat-amplitude as an attracting one on an unperturbed
trajectory), which is exactly why review asked for an interventional check in addition to a
passive one.**

This sample is disclosed as n=16, not exhaustive -- the 100%-vs-25% split is a strong
pattern on a fair sample, not a claim that every `damping=0.0` case fails or every
`damping=0.05` case succeeds; a fuller sweep of `check_attractor_recovery` across all 240
verified runs is future work, flagged rather than assumed complete.

### 13.8 Cycle-clustering redone on verified `saturation="cubic"` data -- a correction to
Sec.12.3's "not a hub artifact" conclusion

Sec.11.2/12.3's fundamental-cycle-coverage analysis used the `saturation="none"`, short-window
(pre-Sec.13.3-hardening) `sustained_and_settled` flags -- data Sec.12.2 has since shown to be
mostly pre-blowup transients. Redone here on the 240 `saturation="cubic"`,
`verify_long_window`-VERIFIED runs:

| topology | verified runs | node density p | cycles examined | covered | fraction | observed/null ratio |
|---|---|---|---|---|---|---|
| `barabasi_albert` (hub-heavy) | 58 | 14.5% | 1276 | 23 | 1.80% | **14.9x** |
| `erdos_renyi` | 64 | 12.2% | 1485 | 14 | 0.94% | **29.7x** |
| `watts_strogatz` | 59 | 10.3% | 1475 | 2 | 0.14% | 3.8x |
| `random_regular` (**no hubs**) | 59 | 9.0% | 1475 | **0** | **0.00%** | **0.0x** |
| all pooled | 240 | 11.5% | 5711 | 39 | 0.68% | 18.7x |

**This reverses the direction of Sec.12.3's conclusion.** Under the corrected data,
`random_regular` -- the ONE topology with no hub structure at all -- shows ZERO covered
cycles, while the two topologies with the most degree heterogeneity (`barabasi_albert`'s
explicit hubs; `erdos_renyi`'s Poisson-tailed degree spread) show the STRONGEST enrichment.
`watts_strogatz` (mostly-uniform degree, small-world rewiring) sits in between, weakly
enriched. This is the opposite pattern from Sec.12.3's `saturation="none"` finding (where
`random_regular` showed the HIGHEST ratio, 22.3x) -- that earlier result is now understood
to have been computed from data (short-window, uncapped, pre-blowup-transient flags) that
did not reliably reflect genuine sustained structure, so its topology-dependence should not
be trusted either. **Sec.12.3's claim ("the 20x cycle-clustering enrichment is NOT a
barabasi_albert-hub artifact") is retracted; the corrected data instead suggests degree
heterogeneity (hubs, or hub-like variance) may be RELEVANT to whether verified-sustained
nodes cluster on cycles, though this needs the caveat below before being read as
confirmed.**

Honesty caveat, not glossed over: `random_regular`'s expected count under the independence
null itself is small (p^L averaged over its own cycle lengths predicts ~0.10 covered cycles
out of 1475) -- so 0 observed is also fully consistent with a modest (not necessarily zero)
enrichment that this particular sample was underpowered to detect, not unambiguous proof of
"no clustering mechanism at all in a hub-free graph." What CAN be said cleanly: `random_regular`
shows no evidence of clustering anywhere near `barabasi_albert`'s or `erdos_renyi`'s
strength (14.9x-29.7x), and the ordering (hub-heavy > moderate-heterogeneity > small-world >
homogeneous) is monotonic in a plausible degree-heterogeneity ranking, which a pure
false-negative-on-random_regular explanation would not by itself predict. This is reported
as a genuine open question for a future PR with a larger `random_regular` sample, not
resolved here.

### 13.9 Combined honest statement

The R-layer's first genuine, verified, interventionally-confirmed sustained oscillation is:
`memory="on"`, `asymmetry=True` (any strength tried, though verification rate climbs with
strength), `damping=0.05`, `saturation="cubic"` (any tested `a` from 0.02-2.0). This
required: (1) the linear-instability mechanism proven in Sec.10.2/10.3, unaffected by
saturation (Sec.13.1); (2) a nonlinear cap, `saturation="cubic"`, without which nothing
sustains (Sec.12.2); (3) linear dissipation, `damping>0`, without which the capped
oscillation is a conservative orbit family rather than a self-sustaining attractor
(Sec.13.7); and (4) a long-window re-check baked into the definition of "sustained" itself,
without which short-window artifacts keep reappearing (Sec.13.3, this PR's third instance of
the same underlying mistake, now structurally prevented rather than corrected after the
fact). The spatial-clustering question (Sec.13.8) is genuinely reopened, not closed, by the
corrected data -- reported as such rather than either re-asserting Sec.12.3's retracted
claim or overclaiming the reversed pattern as settled.

### 13.10 9th-audit and 8th-audit re-check on Sec.13's own claims

- **9th audit:** "`damping=0.0` mostly does not recover" and "`random_regular` shows zero
  cycle coverage" are both non-achievement-flavored claims, so the 9th audit applies. The
  attractor-recovery instrument's own expressibility: `continue_steps = base_steps*5` (15000
  steps, 750 time units) is long relative to the oscillation periods observed in this
  substrate (single-digit to low-double-digit time units), so the window comfortably covers
  many cycles of relaxation back toward (or away from) the pre-perturbation plateau -- not a
  short-window artifact of the kind Sec.12.2/13.3 flagged elsewhere. The cycle-coverage
  null-rate caveat (Sec.13.8) is exactly this audit's own discipline applied to itself:
  explicitly stated, not glossed over, that `random_regular`'s zero count is not
  distinguishable from a weak-but-nonzero effect given the sample size.
- **8th audit:** was the attractor sample's selection rule, the `perturb_factor=0.4`, or the
  `RECOVERY_TOL=20%` chosen to produce the 100%-vs-25% split? No: the selection rule (first
  2 per topology-damping cell, sorted by a fixed key) was written into the script before any
  `check_attractor_recovery` call ran; `perturb_factor` and `RECOVERY_TOL` are both fixed
  constants in `verify.py`, set once (Sec.13.4) before this section's sampling, not
  re-tuned per result -- and the split is stark enough (achieved cases cluster under 10%
  relative difference, non-achieved cases cluster over 55%) that no reasonable nearby
  tolerance choice would change the qualitative 8/8-vs-2/8 pattern.

## 14. S-011: damage-recovery ACHIEVED (D3), R7 (phase) built on the corrected `damping=0.05`
subset, and the cycle-clustering finding reframed as hub-localization

Per review's acceptance of PR-R2.1 and instruction to (1) formally record the damage-
recovery achievement, (2) report the `damping=0.05`-only breakdown of the 240 verified runs
and 663 node-checks -- the real N for R7, (3) re-measure fundamental-cycle coverage on the
`damping=0.05` verified `saturation="cubic"` data specifically, reframing the earlier
reversal as a discovery (hub-localization) rather than a bare retraction, and check whether
`barabasi_albert` has any fully-covered cycle (a green light for R8), and (4) build R7
(phase) restricted to this corrected subset, with the initial transient -- not just the
Hilbert edge -- trimmed by a fixed rule. All four done, in order, below.

### 14.1 Damage-recovery: ACHIEVED

**Formal record**: `memory=on x asymmetry=on x saturation="cubic" x damping=0.05` produces
genuine self-sustaining limit cycles, confirmed interventionally (Sec.13.4/13.7): 8/8
sampled cases return to within a few percent of their pre-perturbation plateau amplitude
after 60% of that amplitude is removed at a checkpoint. This is the R-layer's own,
independently-implemented instance of the measurement concept `ai_lab/dream/
frontier_expander.py`'s capability roster calls `self_repair` / `damage-recovery`
("壊されたあと自分で戻る" -- "returns by itself after being broken"; "自然にできたまとまりを
後から部分的に乱したとき、同じ統計的個性へ戻るか" -- "when a naturally-formed structure is
later partially perturbed, does it return to the same statistical identity"). **Per review:
this satisfies that requirement's content -- a self-maintaining structure confirmed by
intervention, not correlation -- and is the concrete substance of destination D3 (a loop
that continues by running itself).** `achieved=True` is `verify.check_attractor_recovery`'s
own explicit field on every R-layer result it is computed from (Sec.13.4); this section is
the formal, human-readable record of that achievement for the R-layer's own tracking. As
stated in PR-R2.1 (Sec.13.4) and repeated here for clarity: this module does not read or
write `frontier_expansion.json` or any `ai_lab/dream/` file -- the `dream/` roster's own
`self_repair` status (tracking the separate, TDGL-based `dream/` system) is unaffected by
and unrelated to this record; the two are independent measurements of the same underlying
concept on different physics.

### 14.2 The `damping=0.05` breakdown: the real N for R7

Sec.13.6's "240/600 runs, 663/1153 node-checks verified" is the SUM of both damping values.
Split (from `verify.verify_long_window`'s own per-run records, `results_pr_r2_1.json`):

| | `damping=0.0` | **`damping=0.05` (R7's actual target)** | total |
|---|---|---|---|
| candidate runs (screening) | 195 | 168 | 363 |
| **verified runs** | 140 | **100** | 240 |
| candidate node-checks | 730 | 423 | 1153 |
| **verified node-checks** | 440 | **223** | 663 |

**R7 is built and exercised against the `damping=0.05` verified subset specifically: N=100
runs, 223 node-checks.** The `damping=0.0` verified count (140 runs, 440 node-checks) is
NOT R7's target -- per Sec.13.7, most of it is not a self-sustaining structure (only 2/8
sampled `damping=0.0` cases recover from perturbation) -- but see Sec.14.5 for why "most"
is not "all," and why that residual is recorded as open rather than closed.

### 14.3 Cycle coverage redone on `damping=0.05` verified data -- a reframing, not a
retraction, and a concrete green light for R8

Sec.13.8 redid Sec.12.3's cycle-coverage analysis on the pooled (both damping values) 240
verified runs and found the enrichment REVERSED direction relative to the `saturation="none"`
data: `random_regular` (no hubs) went from the highest ratio to zero, while
`barabasi_albert`/`erdos_renyi` (degree-heterogeneous) became the strongest. Per review:
**this is not merely a retraction of "not a hub artifact" -- it is a positive finding in its
own right, restated here as such: verified-sustained oscillation in this substrate localizes
preferentially in degree-heterogeneous regions (hubs or hub-like variance), not uniformly
across the graph.** Sec.12.3's literal claim ("not a hub artifact") remains retracted (it was
wrong); the underlying enrichment phenomenon it was trying to explain is not retracted, only
re-explained.

Redone restricted to `damping=0.05` verified runs specifically (the corrected N from 14.2):

| topology | verified runs (damping=0.05) | node density p | cycles examined | covered | fraction | observed/null ratio |
|---|---|---|---|---|---|---|
| `barabasi_albert` | 19 | 9.0% | 418 | **1** | 0.24% | 8.8x |
| `watts_strogatz` | 30 | 11.1% | 750 | **2** | 0.27% | 6.0x |
| `erdos_renyi` | 24 | 8.7% | 577 | 0 | 0.00% | -- |
| `random_regular` | 27 | 8.0% | 675 | 0 | 0.00% | -- |
| all pooled | 100 | 9.3% | 2420 | 3 | 0.12% | 6.7x |

Smaller N (100 vs 240 runs) than Sec.13.8's pooled figure, so the absolute counts are small,
but the direction is the same: hub-containing/degree-heterogeneous topologies
(`barabasi_albert`, `watts_strogatz`) show coverage; the two more-homogeneous topologies
(`erdos_renyi` at this N, `random_regular`) show none. Given the small counts, this
`damping=0.05`-only breakdown is read as corroborating, not independently establishing,
Sec.13.8's pattern -- both were needed because Sec.13.8's pooled data is not yet the correct
N for R7 (Sec.14.2), while this section's smaller N alone would be underpowered on its own.

**The concrete finding review asked for: does `barabasi_albert` have any fully-covered
cycle?** **Yes.** One fundamental cycle is fully covered: `barabasi_albert`, seed=0,
`asymmetry_strength=20.0`, `damping=0.05` -- the triangle (nodes 7, 4, 22), all three
`verify_long_window`-verified. Two more fully-covered cycles exist in `watts_strogatz`
(seed=4, strength=20.0, triangle [1,0,23]; seed=11, strength=20.0, triangle [19,23,21]).
**This is a green light for R8 in the specific, narrow sense review asked about: there now
exists at least one closed loop, in the corrected `damping=0.05`/`saturation="cubic"`/
`verify_long_window`-confirmed data, where R8's precondition (phase defined all the way
around a cycle) could actually be met** -- unlike Sec.11.2's original (`saturation="none"`)
finding, which review already flagged as too close to zero to be structurally meaningful
even before Sec.12.2 showed that data was mostly artifactual. All 3 examples found so far
are triangles (length 3, the shortest possible cycle) at the highest swept asymmetry
strength (20.0) -- consistent with Sec.13.6's finding that higher strength verifies more
reliably (more nodes cross into the verified regime, raising the odds that an entire short
local loop is covered). **R8 itself is NOT built in this PR** -- review's request was to
report whether the precondition is met, which it now is on a small, disclosed number of
examples; whether to build R8 against this specific (still small) evidence base is left for
review's own decision, not assumed here.

### 14.4 R7 (phase): built on the `damping=0.05` subset, with the transient trimmed by a
fixed rule

Implemented `instruments.py::phase()` -- this codebase's first instrument licensed to
report 位相/phase (spec Sec.5). Gated on R4's `sustained_and_settled` per node (the
instrument's own precondition; the caller must separately apply `verify_long_window` /
`check_attractor_recovery`, Sec.13.3/13.7, to trust a `phase` Reading as describing a
genuine self-sustaining attractor rather than merely a screening-window-sustained node --
this instrument alone cannot see that distinction).

**Transient trim, per review's point 3.** Sec.13.3 found that a long recording's whole-
window `sustained` comparison is dragged down by the initial transient once that transient
is a small-but-nonzero fraction of a much longer window -- direct evidence the transient
itself is not negligible in duration. Per review, R7 must discard the transient itself, not
just the Hilbert-transform edge-padding region R3/R4 already trim. **Fixed rule
(`instruments.py::_phase_analysis_window`, same location in the pipeline as the R3 moving-
average edge-bias fix): the phase-analysis window is the LAST HALF of the recording,
further trimmed at both new boundaries of that half by R3/R4's own edge-trim formula
(`win = max(5, L//20)`).** "Last half" is not an arbitrarily chosen fraction -- it is
exactly the region `_envelope_trend`'s `settled` check already restricts itself to (its own
trailing-quarter-vs-third-quarter comparison operates entirely within this same half), so
R7 reuses that already-established, already-tested boundary rather than introducing a
second, independently-tunable one. This is a pure function of the recording length `L`
alone (`tests/test_r_instruments.py::test_phase_analysis_window_fixed_rule_not_tunable_per_call`
checks the same `L` always yields the same window) -- not a per-config or per-outcome
choice.

**Built-in cross-check.** R7 reports `mean_rate_from_phase` (from unwrapping the analytic
signal's angle -- the first read of that angle anywhere in this codebase; R3/R4 use only
the Hilbert-transform MAGNITUDE, per their own docstrings) alongside R4's own `rate`
(1/T from autocorrelation peak-picking). On the validated example (`random_regular`
seed=5, `damping=0.05`, `strength=0.3`, `saturation="cubic"`), the two independent
measurements agree to within 3-5% (node 22: R7=0.3126, R4=0.3226; node 23: R7=0.3144,
R4=0.2985) -- two different derivations of the same quantity from the same trajectory,
agreeing, is itself evidence the phase extraction is measuring something real.

**Vocabulary discipline.** `tests/test_r_layer_vocabulary.py` was restructured (not just
patched) into `STILL_FORBIDDEN_WORDS` (渦/vortex, 次元/dimension, 力/force, エネルギー/
energy, コヒーレンス/coherence, plus 頻度/frequency by the pre-existing convention) and
`NOW_LICENSED_WORDS` (位相/phase). Both directions are tested: a config known to produce a
`verify_long_window`-confirmed node yields a `defined` R7 reading that legitimately contains
"phase" (the license is exercised, not merely permitted); still-forbidden words remain
absent even in that same phase-bearing output.

### 14.5 Open, not closed: `damping=0.0`'s 2/8 recovering cases

Per review's explicit instruction: the 2/8 `damping=0.0` samples that DID recover
(Sec.13.7: relative differences 0.012 and 0.059, both comfortably inside tolerance, not
borderline) are recorded as an unresolved minor finding, not explained away. Sec.13.7's own
physical argument (no linear dissipation channel, therefore a conservative orbit family) is
a good account of the MAJORITY (6/8) but is not asserted as a universal law here: asymmetry
itself moves energy between nodes (it is precisely the injection mechanism, Sec.10.3), so it
is not ruled out that some specific graph/seed configurations let asymmetry's own
redistribution act as an effective dissipation-like channel even at `damping=0.0`,
producing a genuine attractor without linear friction. This is NOT investigated further in
this PR -- flagged, with both data points on record, as a question for whenever
`damping=0.0` is revisited, rather than either (a) claimed as a mechanism understood, or (b)
dismissed as noise within an otherwise-clean 6/8 pattern.

### 14.6 9th-audit and 8th-audit re-check on Sec.14's own claims

- **9th audit:** "barabasi_albert has a fully-covered cycle" and "damping=0.05's verified
  count is 100/223, not 240/663" are both achievement-flavored or scope-narrowing claims,
  not non-achievement claims, so the 9th audit's core question does not directly apply --
  the relevant discipline instead is that both are reported as exact counts from the full,
  un-truncated `verify_long_window` output, not estimated or sampled. R7's own
  `expressible_max` (the trimmed window length) is recorded on every Reading per the same
  convention as R1-R4, so a future non-achievement claim about phase can itself be audited
  the same way R4's ceiling already is.
- **8th audit:** does `_phase_analysis_window`'s "last half" choice encode an answer? No --
  it was derived from an already-existing, already-tested boundary (`settled`'s own
  region), fixed before any R7 output was inspected, and verified to be a pure function of
  `L` alone (test above) rather than tunable per result. Does reporting "damping=0.05: 100
  verified" instead of "240 verified" understate the result to match review's framing? No --
  both numbers are true and both appear in this document (14.2's table shows the full
  breakdown); 100/223 is reported as the correct N for R7 specifically because Sec.13.7
  independently (via intervention, not assumption) showed `damping=0.0`'s count mostly does
  not represent the same kind of structure.

## 15. S-012: R8 stays blocked -- triangles are structurally unsuited to winding, not merely
few in number; propagation investigation opened as the next PR's theme

Per review's acceptance of PR-R2.1's phase/R4-rate cross-check (agreement to within 3-5%,
independent evidence the instrument is measuring something real) and instruction NOT to
start R8: the blocker is not sample size, it is that all 3 fully-covered cycles found so
far are triangles, and triangles are doubly unsuited to a winding-number measurement (high
null rate; aliasing at |winding|<=1). Confirmed and quantified below, plus the three
measurements review requested toward the real blocking question: why does the
sustained-and-verified regime stay local instead of propagating.

### 15.1 All 3 fully-covered cycles are triangles (length 3) -- confirmed exactly

Re-extracted directly from the same `verify_long_window` output Sec.14.3 used (no new data):

| topology | seed | strength | cycle (node indices) | length |
|---|---|---|---|---|
| `barabasi_albert` | 0 | 20.0 | [7, 4, 22] | **3** |
| `watts_strogatz` | 4 | 20.0 | [1, 0, 23] | **3** |
| `watts_strogatz` | 11 | 20.0 | [19, 23, 21] | **3** |

No length-6-or-longer fully-covered cycle exists in the current data. This is not a
sampling gap to be closed by finding a 4th example -- Sec.15.2 shows why length itself, not
count, is the operative constraint.

### 15.2 Winding-number null rate, measured before any R8 code exists
(`ai_lab/relational/winding_precheck.py` -- explicitly NOT R8; a standalone precondition
module, not wired into `instruments.py`/`measure_all()`)

**Method**: `compute_winding` sums wrapped consecutive phase differences around a FIXED
cyclic order (the order the relation graph's own edges impose -- NOT re-sorted by phase
value, since a real cycle's node-to-node adjacency is fixed by the graph, independent of
whatever phase later lands on each node) and divides by `2*pi`. `monte_carlo_null_rate`
draws N i.i.d. `Uniform(0, 2*pi)` phases in that fixed order and measures how often the
result is nonzero, for N=3..10 (200,000 trials each):

| N (cycle length) | null rate (Monte Carlo) |
|---|---|
| 3 | **0.250** (matches the exact closed form `1 - 3/2^2 = 0.25` to 3 decimal places) |
| 4 | 0.335 |
| 5 | 0.402 |
| 6 | 0.449 |
| 7 | 0.488 |
| 8 | 0.521 |
| 9 | 0.548 |
| 10 | 0.571 |

N=3's Monte Carlo result (0.2495) matches the analytic "probability 3 random points on a
circle do not all lie in one semicircle" formula (`1 - N/2^(N-1)`, review's own derivation)
almost exactly -- cross-validating `compute_winding`'s implementation independently of the
formula. **Non-obvious finding, worth flagging on its own: the null rate does NOT fall as N
grows -- it RISES (0.25 at N=3 to 0.57 at N=10).** This is because the graph's fixed
(not phase-sorted) traversal order means a longer cycle gives a random phase assignment MORE
opportunities to produce a self-crossing, winding path by pure chance, not fewer. A naive
expectation that "a longer cycle will be easier to interpret" is therefore wrong on the
null-rate axis specifically (it is right on the RESOLUTION axis, review's second point) --
a future R8 needs a real signal strong enough to clear a HIGHER bar at larger N, not a lower
one.

**Applied to the one real example available**: computed the actual instantaneous phase
(analytic-signal angle, at the midpoint of R7's analysis window) for `barabasi_albert`
seed=0's verified triangle [7, 4, 22]: phases 2.166, 1.589, 0.972 radians -- all three
within a 1.19-radian span (less than pi), so **the observed winding number is 0** by
construction (three points spanning less than a semicircle can never wind, regardless of
connection order). The permutation-test null rate computed on these exact 3 phase values
(`shuffled_null_rate`, review's alternative method) is also 0.0 for the same reason. This is
consistent with genuine local phase-CLUSTERING among these 3 nodes (an interesting
observation in its own right -- their phases are close together, suggestive of local
entrainment) but is not itself a winding measurement result, and is not claimed as one.

**Conclusion for R8**: the null-rate table above is now a standing reference. Per review's
stated conditions, R8 should not be attempted until (a) multiple fully-covered cycles of
length >= 6 exist, AND (b) any observed winding rate is compared against this table's
null, not treated as meaningful on its own merit.

### 15.3 Why does persistence stay local? Three measurements, as requested

**(a) Degree distribution: verified vs. all nodes**, damping=0.05, `saturation="cubic"`,
`verify_long_window`-verified data (100 runs, 2400 total node-checks):

| | mean degree | median | n |
|---|---|---|---|
| all nodes | 3.927 | 4.0 | 2400 |
| **verified nodes** | **4.318** | 4.0 | 223 |
| non-verified nodes | 3.887 | 4.0 | 2177 |

Verified nodes have ~10% higher mean degree than the population -- a real bias, consistent
in direction with Sec.14.3's topology-level clustering finding, but **modest on its own**.
A 10% single-node degree bias could not, by itself, produce the 7-30x cycle-level
enrichment Sec.14.3 measured -- multiple ADJACENT nodes all being verified compounds a
modest per-node bias nonlinearly, so the cycle-level effect is larger than the node-level
degree bias alone would predict. This suggests spatial CLUSTERING of verified nodes (they
tend to sit next to each other, not just individually prefer high-degree positions) beyond
what a per-node degree preference explains on its own -- not resolved further here.

**(b) Why doesn't oscillation propagate to non-verified neighbors?** Checked the two
candidate mechanisms review named directly:

- **Coupling strength**: every edge in every topology used here has identical weight
  (`w_vv` mean 1.0000, `w_vn` mean 1.0000, `w_nn` mean 1.0000, n=88/787/3837 edges
  respectively) -- **RULED OUT structurally, not just empirically**: the topology
  generators (`topology.py`) always produce a binary 0/1 adjacency before asymmetrization,
  and asymmetrization (Sec.9.1) preserves each edge's AVERAGE weight exactly -- there is no
  coupling-strength heterogeneity anywhere in this substrate for "weak coupling" to
  describe. Non-propagation is not a coupling-strength effect.
- **Amplitude falloff**: measured each node's own final-quarter mean `|x|` (a full
  trajectory rerun per config, not derived from the screening summary):

  | | mean amplitude | vs. verified |
  |---|---|---|
  | verified nodes | 12.18 | -- |
  | non-verified, DIRECT neighbor of a verified node | 8.76 | **72%** |
  | non-verified, no verified neighbor | 7.38 | 61% |

  Amplitude does NOT sharply cut off at the verified/non-verified boundary -- direct
  neighbors retain 72% of the verified amplitude, and even non-adjacent nodes retain 61%.
  **Amplitude is reaching most of the graph; classification as "verified" is not.** This
  points away from "the drive doesn't reach them" and toward a THIRD mechanism review
  listed but this section did not directly test: PHASE mismatch / lack of coherent
  entrainment -- neighboring nodes are visibly driven (large amplitude) but apparently do
  not lock into a clean enough periodic pattern to pass R3's reversal-count precondition,
  R4's autocorrelation-peak detection, or `settled`'s plateau check. This is reported as
  the leading HYPOTHESIS from this data, not a conclusion -- confirming it directly (e.g.
  checking driven-but-unverified neighbors' own R3/R4 diagnostics specifically) is natural
  next-PR work, not done here.

**(c) Persistent-node density needed for long cycles to be plausible.** Using the
independence approximation (`p^N`, Sec.11.2/14.3) combined with the observed clustering
enrichment (~7-30x across topologies, Sec.14.3):

| target P(>=1 fully-covered cycle) | N=3 | N=6 | N=10 |
|---|---|---|---|
| 1% (no enrichment) | p=0.215 | p=0.464 | p=0.631 |
| 1% (15x enrichment) | p=0.087 | p=0.296 | p=0.481 |
| 10% (15x enrichment) | p=0.188 | p=0.434 | p=0.606 |

**The observed density is p=0.093 (9.3%, Sec.14.2's 223/2400).** Even crediting the full
observed 15x clustering enrichment, this predicts a probability of order 1e-5 per length-6
cycle -- consistent with finding zero length-6-or-longer covered cycles across the entire
sweep. Reaching even a 1%-per-cycle chance at N=6 would require p~0.30, roughly **3x the
currently observed density**. This is a structural gap, not a sampling one: more seeds at
the current dynamics would not meaningfully change this, since the required density is far
outside the range this substrate currently produces.

**(d) Persistent fraction, with denominator, stated plainly**: 223 verified node-checks
out of **2400** (100 runs x 24 nodes, the runs that have >=1 verified node) = **9.3%**;
223 out of **7200** (all 300 `damping=0.05` configs x 24 nodes, most of which have ZERO
verified nodes) = **3.1%**. Both denominators are reported because they answer different
questions: 9.3% describes density WITHIN a graph that already has some persistent
structure; 3.1% describes density across the full swept parameter space including
configs with no persistence at all.

### 15.4 Combined statement and the next PR's theme

Confirms S-012 exactly: R8 is not blocked by example count, it is blocked because (i) the
one available cycle SHAPE (triangles) has both a high, RISING-with-length null rate and
poor resolution, and (ii) the dynamics that produce verified nodes do not currently produce
enough of them, densely enough, adjacent to each other, to cover a longer cycle -- a gap of
roughly 3x in density even crediting the observed clustering bonus. Per review: **the next
PR's theme is why persistence stays local** -- this section's three measurements narrow
that question concretely: not a coupling-strength effect (ruled out structurally); not
primarily an amplitude-reach effect (72%/61% retention at one and two hops); most likely a
phase-coherence/entrainment effect (hypothesis, not yet directly tested) combined with a
modest-but-real degree preference (10%) that does not by itself explain the larger
cycle-level clustering (7-30x) -- implying verified nodes cluster spatially beyond simple
degree preference, a mechanism not yet identified.

### 15.5 9th-audit and 8th-audit re-check on Sec.15's own claims

- **9th audit:** the null-rate table's own expressibility is exact by construction (a
  closed-loop sum of wrapped differences is always an integer multiple of `2*pi` up to
  floating-point error; `compute_winding` is validated against the N=3 analytic formula, not
  merely self-consistent). The "amplitude reaches non-verified nodes" finding is an
  achievement-flavored claim about propagation, not a non-achievement claim about winding,
  so the 9th audit's core question does not directly bind it -- the relevant discipline is
  that it was measured from full trajectory reruns (not inferred from the cheaper screening
  summary) specifically so it would not silently inherit the screening pass's own
  limitations.
- **8th audit:** was `winding_precheck.py`'s Monte Carlo trial count (200,000), the
  `enrichment~15x` figure used in 15.3(c), or the choice to check coupling-strength and
  amplitude specifically (of review's three suggested mechanisms) chosen to produce a
  particular narrative? No: 200,000 trials was fixed before any N was run (and N=3's result
  independently matches the closed-form check, which is the actual validation, not the
  trial count); 15x is the middle of Sec.14.3's own already-reported 7-30x range, not
  cherry-picked; coupling-strength and amplitude were checked because they were the two
  concrete, directly-measurable-from-existing-data mechanisms among review's three
  suggestions -- phase-coherence is reported as the remaining, NOT-yet-tested hypothesis
  precisely because it could not be checked from data already in hand, not because it was
  avoided.

## 16. S-013: winding needs a smoothness gate, not just a nonzero value; and "driven vs.
self-sustaining" is a real ~50/50 split, not the near-total drive review's own hypothesis
predicted

Per review's acceptance of Sec.15's null-rate finding, PR-R2.4 does two things: (1) adds
the smoothness gate review specified and re-measures the null rate under the corrected
composite criterion; (2) runs the priority interventional test -- freezing/disconnecting
the verified node set and watching whether non-verified neighbors' oscillation survives --
across ALL 100 verified `damping=0.05` runs, not a sample. Per review's explicit
instruction, no density-increasing work is attempted here regardless of what (2) shows.

### 16.1 The smoothness gate: winding != 0 AND max adjacent step < pi/2

`winding_precheck.py` (PR-R2.3) gained `is_smooth_winding` (AUDIT.md's own module docstring
now documents this as the composite criterion): a winding counts only if `compute_winding`
is nonzero AND every wrapped consecutive phase step has magnitude under a fixed threshold
(`pi/2` by default). **Structural consequence, not probabilistic**: N steps each strictly
under `pi/2` sum to strictly under `N*pi/2`; representing a full loop (`2*pi`) therefore
requires `N*pi/2 > 2*pi`, i.e. `N > 4`, i.e. **N >= 5 is a hard necessary condition** --
confirmed empirically (`MIN_LENGTH_FOR_SMOOTH_WINDING = 5`; 300,000-trial Monte Carlo checks
at N=3 and N=4 both return exactly 0.0, matching the structural argument exactly, not just
approximately).

**Re-measured null rate under the composite criterion** (300,000 trials per N):

| N | plain null rate (Sec.15.2) | **smooth null rate** | naive `(1/2)^N` guess |
|---|---|---|---|
| 3 | 0.249 | **0.0** (structurally impossible) | 0.125 |
| 4 | 0.335 | **0.0** (structurally impossible) | 0.0625 |
| 5 | 0.402 | **0.0003** | 0.0313 |
| 6 | 0.450 | **0.0005** | 0.0156 |
| 7 | 0.488 | **0.0005** | 0.0078 |
| 8 | 0.521 | **0.0004** | 0.0039 |
| 10 | 0.570 | **0.0002** | 0.0010 |
| 12 | 0.607 | **0.0001** | 0.0002 |

The smoothness gate essentially eliminates the null-rate problem Sec.15.2 identified (from
25-60% down to under 0.05% everywhere it can be nonzero at all) -- but the empirical rate is
**5-100x LOWER than review's own `(1/2)^N` back-of-envelope estimate** (e.g. at N=6:
measured 0.0005 vs. guessed 0.0156, a 31x gap), because "winding is nonzero" and "every step
is small" are not independent events -- treating them as an independent product
overestimates the joint rate substantially. A second non-obvious pattern: the smooth null
rate is not monotonic in N -- it peaks around N=6-7 and DECREASES again for larger N (0.0005
at N=7 down to 0.0001 at N=12), because the "every step small" requirement's cost keeps
compounding multiplicatively with N faster than the added combinatorial routes to a nonzero
sum can compensate.

**R8's launch condition, restated with the composite criterion**: multiple fully-covered
cycles of length >= 5 (structurally required), ideally in the N=5-10 range where the
smooth null rate is well-characterized here and near its (already very low) ceiling. This
supersedes Sec.15.4's "length >= 6" as the operative minimum (N=5 is now known to be exactly
sufficient, not merely "probably better than 3").

### 16.2 Driven vs. self-sustaining: an interventional test, run across all 100 verified runs

Per review's priority instruction: Sec.15.3(b)'s finding that non-verified direct neighbors
retain 72% of a verified node's amplitude does NOT by itself distinguish "the neighbor
generates its own oscillation" from "the neighbor is merely being shaken by the verified
node and would stop without it." Answered directly, with the same interventional logic as
`check_attractor_recovery` (Sec.13.4) but cutting EDGES instead of perturbing amplitude:
`verify.py::check_driven_vs_self_sustaining` (PR-R2.4) takes a long (`extend_factor=15`x)
trajectory, and at a checkpoint zeroes every edge between the verified node set and the rest
of the graph (`substrate.run`'s new `W_override`, PR-R2.4 -- replaces the constructed W
entirely for a continuation run, same tooling-knob status as `x0_override`/`v0_override`).
Both a CUT and a CONNECTED-control continuation run from the identical checkpoint; each
non-verified direct neighbor's plateau amplitude after the cut is compared to its own
connected-control amplitude. `self_sustaining` = retains >= 50% (fixed, disclosed
`DEFAULT_SELF_SUSTAINING_TOL`); `driven_only` = below that.

**Run across all 100 `damping=0.05` verified runs (not a sample -- every run with >=1
checkable non-verified neighbor; 6/100 runs had none)**:

| | count | fraction |
|---|---|---|
| non-verified direct-neighbor node-checks tested | 323 | -- |
| **self-sustaining** (ratio >= 50%) | **172** | **53.3%** |
| **driven-only** (ratio < 50%) | **151** | **46.7%** |

**This is genuinely close to an even split -- NOT the "mostly driven" pattern review's own
hypothesis predicted** ("隣はハブに揺すられているだけである可能性が高い"). The distribution
is bimodal, not concentrated in the middle: 31.6% of neighbors have ratio < 0.1 (collapsed
almost completely -- unambiguously driven-only) and 34.1% have ratio >= 0.8 (retained almost
all their amplitude -- unambiguously self-sustaining on their own), with the remainder
spread between. **There appear to be two genuinely distinct populations of non-verified
neighbor, not one graded continuum.**

By topology (node-check counts):

| topology | checked | self-sustaining | **driven-only** | self-sustaining fraction | **driven-only fraction** |
|---|---|---|---|---|---|
| `random_regular` (no hubs) | 75 | 55 | 20 | **73.3%** | **26.7%** |
| `erdos_renyi` | 73 | 42 | 31 | 57.5% | 42.5% |
| `watts_strogatz` | 104 | 45 | 59 | 43.3% | 56.7% |
| `barabasi_albert` (hub-heavy) | 71 | 30 | 41 | **42.3%** | **57.7%** |

**Confirmed, not merely plausible (per review's own read of these same numbers): the
driven-only fraction is what tracks topology, and it does so cleanly** --
`barabasi_albert`'s driven-only rate (57.7%) is more than DOUBLE `random_regular`'s (26.7%).
This is a direct, sufficient explanation, not a speculative one: near an actual hub, a
neighbor is structurally likely to be dominated by the hub's own drive and stops oscillating
once cut (driven-only); in a degree-homogeneous graph there is no single dominant driver, so
a neighbor of a "verified" node is, structurally, just as capable of independent oscillation
as the verified node itself (self-sustaining). The topology-dependence of Sec.16.2's overall
split is EXPLAINED by this same table, not merely consistent with it -- see Sec.17.3's
correction, which had understated this.

### 16.3 What this changes about "why does persistence stay local"

Sec.15.4 framed the open question as propagation failure with phase-coherence as the
leading (untested) hypothesis. Sec.16.2 does not resolve that hypothesis, but it reframes
the question review asked to prioritize: **roughly half of the amplitude-receiving,
non-verified neighborhood is NOT merely driven -- it has its own capacity to sustain
oscillation once disconnected, yet still fails the `verified` classification.** This means
the gap between "verified" (9.3% density, Sec.14.2/15.3) and "amplitude reaches" (much
broader, Sec.15.3(b)) is not simply "drive reaches further than self-maintenance does" --
a substantial fraction of that broader region can ALREADY self-maintain, and something
else -- most plausibly still the phase-coherence/entrainment hypothesis, i.e. these nodes
oscillate on their own but not cleanly enough (or not in the right relationship to their
neighbors) to pass R3's reversal-count, R4's autocorrelation-peak, or `settled`'s
plateau-flatness checks -- is what keeps them out of the verified count specifically. This
narrows, rather than answers, the next question: why do self-sustaining-capable nodes fail
verification's SPECIFIC criteria. Not investigated further here.

### 16.4 Density target: explicitly not pursued this PR

Per review's explicit instruction, Sec.15.3(c)'s "~30% density needed for a length-6 cycle
to be 1%-likely" figure is NOT acted on in this PR -- no work increasing verified-node
density was attempted, since Sec.16.2 shows roughly half of what a density-increase might
capture is driven-only, not self-sustaining, and inflating density with driven nodes would
not represent genuine self-maintaining structure expanding. This is left for a future PR
once Sec.16.3's narrower question (why do self-sustaining-capable nodes fail verification)
is itself resolved.

### 16.5 9th-audit and 8th-audit re-check on Sec.16's own claims

- **9th audit:** "the smooth null rate is far below the naive `(1/2)^N` guess" and "53% is
  self-sustaining" are both achievement/measurement claims with a specific numeric
  comparison, not non-achievement claims -- the discipline applied is that both are full
  counts from the complete run (323/323 node-checks reported, not a subsample) and the
  smooth-null-rate table is exact Monte Carlo output at a fixed, pre-declared trial count,
  not selectively reported favorable N values (all of N=3,4,5,6,7,8,10,12 appear).
- **8th audit:** was `DEFAULT_SELF_SUSTAINING_TOL=0.5`, the checkpoint fraction, or the
  choice to run all 100 (rather than a sample) chosen to produce the ~53% figure? No: 0.5
  is a natural, symmetric "majority retained" threshold fixed in `verify.py` before any
  driven-vs-self-sustaining call ran; `checkpoint_frac=0.6` and `extend_factor=15` reuse
  the exact constants already fixed for `check_attractor_recovery` (Sec.13.4), not new
  values chosen for this measurement; running all 100 (not a sample) was reported as the
  design from the start of this section, not a post-hoc justification for an inconvenient
  result -- and the result itself (53/47, bimodal) is reported as genuinely mixed rather
  than rounded toward either "mostly driven" (review's prior) or "mostly self-sustaining."

## 17. S-014: oscillation death does NOT explain the pattern (0/172) -- the dominant
finding is an instrument gap, not a physical suppression mechanism

Per review's request: look at the actual waveforms, BEFORE theorizing, for all 172
node-checks that are self-sustaining once disconnected (Sec.16.2) but fail `verified`
classification while connected. Classified each into (i) oscillation death (settles to a
nonzero constant), (ii) frustration (irregular/aperiodic), (iii) missed detection (genuinely
periodic but fails R3/R4/`settled`'s specific gates) -- using the SAME already-tested
instrument logic (`reversal`/`period`'s own `reason` and `defined` fields) that classifies
every other node in this PR series, not a new heuristic invented for this section.

### 17.1 Classification result (all 172, connected-state trajectories, standard screening window)

| category | count | fraction |
|---|---|---|
| **(iii) missed detection** (periodic, fails `sustained_and_settled`) | **119** | **69.2%** |
| (ii) frustration (no autocorrelation peak -- aperiodic) | 48 | 27.9% |
| **(i) oscillation death** (reversal count < 2 -- settled to ~constant) | **0** | **0.0%** |
| (short-window screening actually passed; would need its own long-window recheck) | 5 | 2.9% |

**Zero of 172 show oscillation death.** The fifth category (5 cases) is not a bug: these
nodes DO pass the standard short-window `sustained_and_settled` check when rerun (matching
this codebase's own deterministic reproducibility), which means they were excluded from
Sec.16.2's "verified" set only because `verify_long_window`'s stricter 15x-window recheck
(applied only to nodes that already passed short-window screening in the original sweep,
Sec.13.3) had not yet been run on them in that role -- an artifact of which nodes were
screened as CANDIDATES in the first place, not a contradiction.

**Representative numeric examples** (downsampled to ~40 points per series, connected-state,
standard screening window, `random_regular`, `damping=0.05`, `saturation="cubic"`,
`asymmetry_strength=0.3`, seed=5 unless noted):

- **missed detection** (node 4, `settled=True, sustained=False` -- the transient-drag
  pattern already diagnosed in Sec.13.3, now showing up at the SHORT window too): `[0.114,
  0.011, -0.002, -0.013, -0.101, -0.040, -0.006, 0.038, 0.002, -0.043, -0.084, -0.085,
  -0.007, 0.012, -0.032, -0.005, -0.023, -0.008, 0.014, -0.006, 0.004, 0.040, 0.067, 0.014,
  0.002, 0.018, 0.028, 0.048, 0.018, -0.042, -0.021, 0.014, -0.013, -0.063, -0.075, -0.060,
  -0.031, -0.026, -0.093, -0.104, -0.029]` -- small, bounded, visibly oscillatory around
  zero, no trend toward a fixed point.
- **missed detection** (node 6, `settled=False, sustained=False`): `[-0.055, -0.043,
  -0.062, -0.012, -0.052, -0.028, -0.005, -0.033, -0.036, 0.016, 0.032, 0.019, 0.005,
  -0.030, -0.018, 0.078, 0.048, -0.014, -0.024, -0.024, 0.000, 0.013, -0.038, -0.079,
  -0.031, -0.006, -0.070, -0.088, -0.070, -0.031, 0.011, -0.023, -0.086, -0.036, 0.068,
  0.070, 0.019, 0.012, 0.045, 0.124, 0.137]` -- similarly small and bounded; amplitude
  drifts modestly across the window (consistent with `settled=False`) but never approaches
  either zero or unbounded growth.
- **frustration** (seed=11, node 12, `no autocorrelation peak found`): `[0.068, 0.032,
  -0.033, 0.369, -0.997, -0.417, 3.682, -6.080, -7.523, 8.069, -11.764, -4.219, -6.894,
  -4.721, 2.267, 0.972, -2.222, -5.779, 1.560, 8.725, 8.758, -0.322, 3.766, 0.563, 2.192,
  12.091, -9.646, 15.248, -0.107, 1.322, -5.107, -4.018, -0.412, -0.543, -0.640, -2.596,
  -11.158, -7.108, 8.079, 3.738, -0.275]` -- large, wildly irregular swings with no visible
  periodicity, an entirely different character from the two examples above.

### 17.2 Oscillation death: not supported by this data

Review's hypothesis -- that diffusive coupling `Sum_j w_ij(x_j - x_i)` (a textbook
oscillation/amplitude-death-inducing coupling form, since it pulls each node toward its
neighbors' values) suppresses standalone-capable oscillators once connected -- predicts a
substantial oscillation-death count. **The measured count is exactly zero out of 172.**
Every single node classified is either genuinely oscillating (cleanly, 69.2%, or
irregularly, 27.9%) in its connected state, not settling toward a shared fixed point. This
does not rule out oscillation death occurring in some OTHER part of parameter space this PR
did not sample, but within the specific population review asked about (non-verified direct
neighbors that are independently confirmed self-sustaining once cut), there is no evidence
for it.

**Per review's own explicit conditional ("結合形を軸として追加してください" only if (i)
dominates): no new coupling-form axis is added.** (i) is the empty category, not the
dominant one -- the conditional's premise does not hold, so its action is not taken.

### 17.3 Topology breakdown of the classification (a narrower question than Sec.16.2's split
-- CORRECTED: that split is already explained, not open)

| topology | missed detection | frustration | short-window-passed | total |
|---|---|---|---|---|
| `random_regular` | 36 (65.5%) | 18 (32.7%) | 1 | 55 |
| `erdos_renyi` | 31 (73.8%) | 10 (23.8%) | 1 | 42 |
| `watts_strogatz` | 30 (66.7%) | 12 (26.7%) | 3 | 45 |
| `barabasi_albert` | 22 (73.3%) | 8 (26.7%) | 0 | 30 |

Missed-detection and frustration proportions are similar across all four topologies (65-74%
/ 24-33%) -- this table characterizes nodes ALREADY WITHIN the self-sustaining group, and
correctly shows those PROPORTIONS do not track topology. **This was originally
(mis)reported here as leaving Sec.16.2's topology-dependent split "open" -- that was wrong,
and is corrected per review.** Sec.16.2's split is fully explained by numbers already in
that section's own table: the DRIVEN-ONLY fraction (not the self-sustaining group's later
composition) is what tracks topology, cleanly (26.7% at `random_regular` vs. 57.7% at
`barabasi_albert`, more than double). This section's finding and Sec.16.2's are simply
answers to two different questions -- "of the self-sustaining ones, what do they look like"
(this section, topology-independent) vs. "what fraction ARE self-sustaining in the first
place" (Sec.16.2, topology-dependent and explained by hub-driving) -- not competing or
unresolved accounts of the same one.

### 17.4 A better-supported hypothesis for "missed detection": the same short-window
artifact, not yet applied here

Not requested this PR, flagged rather than investigated: 69.2% of the population is
genuinely oscillating (one subgroup, 21/119, showing exactly the `settled=True,
sustained=False` transient-drag signature Sec.13.3 already diagnosed at the LONG window).
Every node in the ORIGINAL `damping=0.05` sweep that was called "verified" only became so
after `verify_long_window`'s 15x-window recheck (Sec.13.3/13.6) -- but that recheck was only
ever applied to nodes that had ALREADY passed short-window screening as candidates
(Sec.13.6). The 172 nodes examined here never had that chance, because they failed
short-window screening to begin with. Given 119/172 show clean periodic motion in their
connected state, it is a natural, testable, NOT-yet-tested hypothesis that a meaningful
fraction of "missed detection" would resolve to genuinely `verified` given the same 15x
window treatment already validated elsewhere in this PR series. This is exactly the kind of
follow-up review has repeatedly asked to be flagged rather than assumed -- recorded here as
the leading candidate for a future PR's `pt1`, not run in this one (running
`verify_long_window` on all 119 would be a substantial compute cost -- 15x the screening
window per node -- undertaken only if review prioritizes it).

### 17.5 Explicitly not pursued this PR

Per review's instructions 3 and 4: no coupling-form axis was added (Sec.17.2's conditional
did not trigger); no density-increasing work was attempted (continuing Sec.16.4's holding
pattern) -- both because this section's central finding (missed detection, not oscillation
death, dominates) points toward an INSTRUMENT gap as the leading explanation, not a physical
mechanism that either of those two actions would address.

### 17.6 9th-audit and 8th-audit re-check on Sec.17's own claims

- **9th audit:** "0/172 oscillation death" is a non-achievement claim (rebutting review's
  own hypothesis), so the 9th audit applies directly: the classification instrument
  (`reversal`/`period`, unmodified from PR-R1/PR-R1.9) is exactly the same one already
  validated with synthetic positive/negative controls throughout this PR series -- no new,
  unvalidated classifier was built for this specific negative result. The category
  boundaries (`reversal_count < 2`, "no autocorrelation peak", `sustained_and_settled`) are
  the SAME thresholds already fixed and audited in Sec.3.3/Sec.13.3, reused here rather than
  redefined to produce a particular count.
- **8th audit:** was the 3-way classification's boundary conditions chosen to make
  oscillation death come out at zero? No -- `reversal_count < 2` for oscillation death is
  the SAME R3 precondition threshold used throughout this codebase since PR-R1 (predates
  this section by many PRs), not introduced or tuned here; the classification was run on
  all 172 node-checks and reported as a full count (119/48/0/5), not a filtered or curated
  subset. The representative examples (17.1) were the FIRST example found for each
  `(sustained, settled)` combination within `missed_detection`, and the first `frustration`
  entry in iteration order -- a disclosed, mechanical selection rule, not hand-picked for
  visual clarity.

## 18. S-015 (pending): the screening pipeline itself was undercounting -- a free fix
recovers 66% of "missed detection," and a sampled false-negative rate suggests the true
persistent density may be 2.6-7.8x the reported figure

Per review's priority ordering: (1) apply the SAME window-length fix already used for
`verify_long_window` to the SCREENING criterion itself, for free, on already-computed data;
(2) send only what remains to long-window verification; (3) the main event -- sample the
DROPPED population at large (not just PR-R2.5's 172) to estimate the screening pipeline's
general false-negative rate and correct the reported density; (4) register, not discard,
the 48 frustration cases; (5) continue not pursuing density-increasing implementation. All
five done, in order, below.

### 18.1 The free fix: screening should use `settled`, not `sustained_and_settled`

Sec.13.3 already established that `sustained`'s whole-window halves comparison is not
window-length-robust -- it is dragged down by the initial transient once that transient is
a non-negligible fraction of the window -- and fixed `verify_long_window` to use `settled`
alone. **The original SCREENING step (the short, 3000-step pass that decides which nodes
even become long-window-verification CANDIDATES) still used the unfixed
`sustained_and_settled` criterion.** Applying the same fix there, on data already computed
(no new simulation for this step):

- Of PR-R2.5's 119 `missed_detection` nodes, **21 (17.6%) are rescued immediately** --
  they already have `settled=True` in the existing short-window trajectory, and were only
  excluded because `sustained` (the transient-drag-prone check) said no.
- **Applied across the ENTIRE 300-config `damping=0.05` sweep** (a full, cheap rerun --
  short window only, no long-window cost): the original `sustained_and_settled` screening
  found **423** candidate node-checks. The corrected `settled`-only screening finds
  **1175** -- **essentially 3x as many candidates**, from the identical trajectories,
  changing nothing about the physics or the sweep, only the classification rule.

This alone is a substantial, free correction, independent of anything sampled below.

### 18.2 The remaining 98: long-window verified directly (not sampled)

The 98 `missed_detection` nodes NOT rescued by 18.1 (still `settled=False` even under the
corrected screening rule) were sent to `verify_long_window` directly, per review's
instruction 2 -- this population is small enough to check exhaustively rather than sample.

**58 of 98 (59.2%) verify at the long window.** Combined with 18.1's 21 free rescues:
**79 of the original 119 `missed_detection` node-checks (66.4%) are genuinely persistent**
-- two-thirds of what PR-R2.5 called "missed detection" was exactly that: MISSED, not
absent.

### 18.3 The main event: a sampled false-negative rate for the whole screening pipeline

Per review's instruction 3, the question is not PR-R2.5's specific 172 -- it is whether the
corrected screening pipeline (18.1) is STILL missing structure broadly, across the entire
sweep. Sampled two populations from the full 300-config `damping=0.05` sweep (fixed seed
2026, disclosed), each `verify_long_window`-verified in full (not itself sampled further):

| population | size | sample | verified in sample | rate | 95% CI (normal approx) |
|---|---|---|---|---|---|
| **B: newly promoted by 18.1's fix** (`settled=True`, was NOT `sustained_and_settled`) | 752 | 50 | 20 | **40.0%** | 26.4%-53.6% |
| **A: still screened out even after 18.1's fix** (`settled=False`) | 6025 | 75 | 15 | **20.0%** | 10.9%-29.1% |

**Both rates are far from zero.** Population A -- nodes the CORRECTED screening still
rejects -- verifies at long window one time in five. Population B -- nodes the correction
newly admits as candidates but have not yet been long-window checked -- verifies two times
in five.

**Corrected density estimate**, combining the known exact count (223 already-verified, from
the original 423 candidates) with these two sampled rates applied to their full population
sizes:

```
corrected_TP  =  223 (known)  +  0.40 x 752 (population B)  +  0.20 x 6025 (population A)
             =  223 + 301 + 1205
             =  1729 (of 7200 total damping=0.05 node-checks)

corrected_density  =  1729 / 7200  =  24.0%
```

**Compared to the previously-reported figures**: 3.1% (223/7200, across the full sweep) --
a **7.8x** correction; 9.3% (223/2400, within the 100 originally-verified-containing runs)
-- a **2.6x** correction. The rough combined-CI range (propagating each sampled rate's own
95% interval independently, not a full joint interval) is approximately **15.0%-33.0%**.

**This changes R8's outlook directly, per review's own prediction.** Sec.15.3(c)/Sec.16.4
estimated that a length-6 fully-covered cycle needs roughly 30% verified-node density
(crediting the observed clustering enrichment) to become even 1%-likely per cycle. The
corrected point estimate (24%) is close to that threshold, and the upper end of the rough
CI range (33%) EXCEEDS it. **The R8 blocker quantified in Sec.15.3(c) may already be far
smaller than previously measured, or possibly no longer a blocker at all** -- this is not
yet confirmed (a point estimate from n=75/n=50 samples, not an exhaustive resweep), but it
is no longer safely assumed to be a 3x gap either.

**Honesty on the sampling itself**: `verify_long_window`'s own settled-window criterion
(Sec.13.3) is reused unmodified for this sampling -- no new instrument was built to produce
this number. The two sample sizes (75, 50) are within review's requested 50-100 range,
drawn with a disclosed, fixed seed (2026) before either sample was verified (not resampled
after seeing an inconvenient early result). The corrected-density FORMULA combines a known
exact count with two independently-sampled rates on disjoint populations (`(known) + rate_B
* n_B + rate_A * n_A`, over the true total N) -- a standard stratified estimator, not an ad
hoc combination.

### 18.4 What this does NOT yet establish

This is reported as `S-015 (pending)`, not settled, because: (a) the corrected density is
an ESTIMATE from two samples, not an exhaustive re-verification of all 6777 non-original-
candidate node-checks (that would cost far more compute than this PR's budget allowed);
(b) it has not yet been checked whether the NEWLY-implied true-positive population (an
estimated ~1500 additional node-checks beyond the known 223) changes Sec.14.3's cycle-
clustering topology pattern, Sec.16.2's driven-vs-self-sustaining split, or any other
finding computed against the smaller, known-223 baseline -- all of those would need
re-deriving against the corrected population before being trusted at the new scale; (c) no
attempt was made in this PR to determine WHY the original screening criterion missed so
much (beyond the already-diagnosed transient-drag mechanism, Sec.13.3, which explains only
the 18.1 portion, not population A/B's sampled rates, which reflect genuinely NEW
information the short window simply could not see within its own recorded length). These
are the natural next steps, not resolved here.

### 18.5 Explicitly not pursued this PR

Per review's instruction 5: **no density-increasing implementation work was attempted**,
even though 18.3's finding makes such work look more promising than it did before this
section -- the instruction was to correct the MEASUREMENT first, and that correction
itself is not yet a settled result (18.4). Registering the 48 frustration cases (Sec.17.1)
as D0 (`ai_lab/relational/d0_registry.json`) was completed per review's instruction 4 (see
that file's own header for the registry's structure and rationale) -- not analyzed further
here.

### 18.6 9th-audit and 8th-audit re-check on Sec.18's own claims

- **9th audit:** "the corrected density may be 2.6-7.8x higher" is an achievement-flavored
  claim built from sampled data, so the 9th audit's core question (could the instrument
  express this) is satisfied by construction -- `verify_long_window` is the exact same,
  already-validated instrument used throughout Sec.13-17, applied here to new populations,
  not a new or loosened check. The claim is explicitly hedged as "S-015 (pending)," not
  asserted as established, specifically because a 2-sample estimate is a materially weaker
  claim tier than an exhaustive resweep -- this section says so directly rather than
  presenting a point estimate as a confirmed correction.
- **8th audit:** were the sample sizes (75, 50), the random seed (2026), or which two
  populations (A: still-rejected, B: newly-promoted) to sample chosen to produce a
  favorable density correction? No: 75 and 50 are within review's own requested 50-100
  range; the seed was fixed in the sampling script before any verification ran; both
  populations were reported (not just the more favorable B, 40%, alone) -- population A's
  lower 20% rate is the one carrying the bulk of the correction's WEIGHT (6025 vs 752 in
  population size), so if anything the larger, less dramatic-looking rate dominates the
  final number, not a cherry-picked favorable one.

## 19. PR-R2.7: density is a proxy -- direct cycle-coverage counting answers R8's viability
without it; the two comparisons ("30%" vs "24.0%") were never on the same footing; and the
screening step's own cost/benefit case is weaker than assumed once verification is batched
correctly

Per review's explicit instruction: this PR does NOT pursue firming up the density estimate.
S-015 stays PENDING (Sec.18). Instead, review asked for the measurement density was always
a PROXY for -- direct cycle coverage -- counted exactly, plus a consistency check on the
30%-vs-24.0% comparison, plus a cost/benefit re-assessment of the screening step itself.

### 19.1 Direct cycle coverage, counted exactly, on the expanded (free-fix) candidate pool

**CORRECTED by PR-R2.8 (Sec.20.2): the "candidates are a SUPERSET of true-verified" claim
below is WRONG, and this section's "2 covered cycles" result is consequently a severe
undercount (the true figure, Sec.20.3, is 178).** Candidate status is computed from a
SHORT-window trailing-quarter check; true-verified status is computed from a LONG-window
(15x) trailing-quarter check -- these are DIFFERENT segments of the same trajectory (steps
~2250-3000 vs ~33750-45000), not a strict/relaxed version of the same check, so neither is a
superset of the other. PR-R2.8's exact cross-tabulation (Sec.20.2) found only 520/1175
(44.3%) of candidates are truly verified, and 1472/1992 (73.9%) of truly-verified nodes were
NOT candidates -- the assumption below does not hold empirically. Left in place, uncorrected
in its original wording, as a disclosed record of the error; do not trust its "2 covered
cycles" conclusion. See Sec.20 for the corrected determination.

**Method** (as originally written, now known to rest on a false premise): candidates
(`settled=True` under the free-fix criterion, Sec.18.1) are a SUPERSET of true
long-window-verified nodes -- every verified node is a candidate, but not every candidate
verifies. This makes the candidate set a valid UPPER BOUND for cycle coverage: if zero
length>=5 cycles are covered even by the generous candidate set, zero can possibly be
covered by the smaller true-verified set, and the question is settled without needing to
know the exact verified count at all.

For each of the 300 `damping=0.05` configs: rebuilt the topology directly
(`topology.build_topology`, no dynamics needed for graph structure) and extracted every
fundamental cycle of length >= 5 (`topology.fundamental_cycles`); separately reran the
config at its original (short) window and computed the corrected candidate mask
(`settled=True`, the same free fix as Sec.18.1, ~91s total for all 300 configs including
the topology work -- effectively free). Checked which length>=5 cycles have EVERY node in
the candidate mask.

**Result**:

| | value |
|---|---|
| total length>=5 fundamental cycles, across all 300 configs | **4155** |
| by length | 5: 1505, 6: 1315, 7: 820, 8: 175, 9: 130, 10: 115, 11: 55, 12: 15, 13: 25 |
| total candidate node-checks (damping=0.05, `settled=True`) | 1175 |
| cycles fully covered by the CANDIDATE (upper-bound) set | **2** |

Both covered cycles come from the SAME single run (`erdos_renyi`, seed=4,
`asymmetry_strength=8.0`) and share 4 of their 5 nodes (`[6, 20, 4, 9, 13]` and
`[6, 20, 4, 9, 22]` -- nodes 6, 20, 4, 9 in common, differing only in the 5th). This is
**one run out of 300, not multiple independent examples** -- reported exactly as such, not
rounded up to "multiple cycles" just because the raw count is 2.

**Long-window verification of exactly those 2 cycles' nodes** (not the 1175-candidate pool
-- only the 6 distinct nodes these 2 cycles touch, using the new
`verify_long_window_all_nodes`, Sec.19.3): **both cycles verify TRUE, 2/2** -- every node in
both cycles is genuinely long-window sustained, not just short-window-candidate. This is
the first length>=5 fully-covered cycle found anywhere in this PR series; R8's previously
stated launch precondition ("multiple fully-covered cycles of length >=5", Sec.16.4) is
technically met at n=2, though from a single run, which is a materially weaker form of
"multiple" than independent examples from different runs/seeds would be.

**Applying `winding_precheck.py` (explicitly NOT R8) to the real, confirmed example** -- the
same method Sec.15.2 used on the earlier triangle (analytic-signal angle at the midpoint of
R7's phase-analysis window, fixed graph cyclic order):

| cycle | phases (rad) | winding | max adjacent step | smoothness gate |
|---|---|---|---|---|
| `[6, 20, 4, 9, 13]` | all within `[-2.57, -2.47]` (0.08 rad span) | **0** | 0.080 | fails (winding=0) |
| `[6, 20, 4, 9, 22]` | 4 nodes near -2.5, node 22 at +0.60 | **0** | 3.118 | **fails** (>pi/2) |

Both cycles give **winding=0** -- one from tight local phase clustering (same pattern as
the earlier triangle, Sec.15.2), the other from a single outlier node (22) producing one
large jump that both breaks the smoothness gate and, by construction, does not accumulate a
net rotation either. Neither example shows anything resembling genuine winding. This is a
disclosed NULL result on the one real, confirmed length>=5 example available -- reported
with the same weight as a positive result would carry, not downplayed for being negative.

**Bottom line for R8's viability** (as originally written -- SUPERSEDED, see Sec.20.3-20.4
for the corrected determination on the exhaustive TRUE-verified set: 178 covered cycles,
not 2): coverage now exists (a first, for this PR series), so R8 is not structurally dead
the way Sec.15 found triangles to be -- but the sample is a single run producing 2
overlapping cycles, and the one measurement made on it is null. This does not resolve
whether R8 is viable in general; it resolves that the CURRENT sweep gives exactly one place
to look, and that one place does not show winding.

### 19.2 Denominator alignment: "30%" and "24.0%" were never comparable, and this is now moot

Review asked whether the ~30% threshold (Sec.15.3(c)) and the 24.0% corrected density
(Sec.18.3) share a denominator before treating "24.0% is close to 30%" as meaningful.
Checked directly against Sec.15.3(c)'s own text: **they do not.**

- The ~30% figure was derived from **p = 9.3% = 223/2400** -- Sec.14.2's density
  CONDITIONAL on the run already having >=1 verified node (100 runs x 24 = 2400) -- combined
  with the observed 15x clustering enrichment (Sec.14.3), in a `p^N` independence-style
  model. Sec.15.3(c) states this explicitly: "The observed density is p=0.093 (9.3%,
  Sec.14.2's 223/2400)... Reaching even a 1%-per-cycle chance at N=6 would require p~0.30."
- The 24.0% figure (Sec.18.3) is **1729/7200** -- the UNCONDITIONAL density across the
  entire 300-config damping=0.05 sweep, matching the OLD 3.1% (223/7200) figure's
  denominator, NOT the 9.3% one.

These are genuinely different quantities: 9.3%/30% describe density WITHIN graphs that
already show persistent structure; 3.1%/24.0% describe density across the full swept
parameter space, most of which has no persistent structure at all. **Comparing 24.0%
directly to 30% and concluding "getting close" is not a valid inference** -- review's
instinct to check this before trusting that comparison was correct.

Recomputing a properly conditional (2400-style) version of the corrected estimate would
require knowing which SPECIFIC runs the ~554 newly-confirmed-but-previously-screened-out
node-checks (from Sec.18.3's sampling) belong to -- whether they cluster into a few runs
(raising the conditional density sharply) or spread thinly across many (barely moving it).
That is not derivable from the disclosed samples already in hand without either exhaustive
re-verification (the direction review explicitly said not to pursue this PR) or a new,
separately-disclosed sampling pass (also not run here, for the same reason).

**This mismatch turns out not to matter**: Sec.19.1's direct count does not depend on the
`p^N` independence model, the enrichment factor, or either density percentage at all -- it
is an exact enumeration against the real graph structure and the real (upper-bound)
candidate mask, for every one of the 300 configs. It already answers the question the
density comparison was a PROXY for. Per review's own framing (instruction 4): the direct
measurement settles what the debate over 24.0%-vs-30% was trying to approximate, so that
debate does not need to be resolved further this PR. Flagged for any future work that DOES
want a conditional density figure: use the SAME (2400-style, structure-conditional)
denominator on both sides of any such comparison -- not done here.

### 19.3 Screening's cost/benefit, re-examined -- and a real inefficiency found along the way

While investigating verification cost, found that every long-window check run so far in
this PR series (Sec.13 onward, including all of PR-R2.6's sampling) called
`verify_long_window` once PER NODE -- even when many nodes from the identical (seed,
run_kwargs) needed checking. `verify_long_window` reruns `substrate.run` in full each call;
one rerun's R4 (`instruments.period`) already computes every node's `settled` status at
once, so calling it once per node repeats the IDENTICAL rerun `n` (24) times for no reason.
Added `verify.verify_long_window_all_nodes` (tested, `tests/test_r_verify.py`): the same
criterion, reading every node's result off one rerun.

**Measured cost, both ways, on real damping=0.05 configs** (not extrapolated from a single
earlier timing -- benchmarked directly, 12 runs):

| step | cost | for all 7200 node-checks (300 runs) |
|---|---|---|
| short-window screening (settled-only, free fix) | ~0.20-0.30 s/run | **~61-91 s total** |
| long-window verify, PER-NODE (as every prior PR in this series did it) | 6.5-8.4 s/**node** (measured across PR-R2.6's 3 sampling runs) | **~13.1-16.7 hours** |
| long-window verify, BATCHED per run (`verify_long_window_all_nodes`, this PR, 12-run benchmark) | ~11.7 s/**run** | **~3505 s (~58 minutes)** |

Batching by run instead of by node measures out to a **~13-17x** empirical cost reduction
(structurally up to n=24x, since one rerun now serves all 24 nodes instead of 1; the
measured multiplier is somewhat below the theoretical 24x, most likely per-call/Hilbert-
transform overhead that does not scale perfectly with how many of a run's nodes are read
off it) -- exhaustively long-window-verifying the ENTIRE 7200-node-check sweep is
affordable in under an hour, not the many-hours figure the per-node pattern used throughout
this series would imply. This was not run this PR (see below -- explicitly not pursued, per
review's instruction not to firm up the density estimate), but the cost figure itself is
now measured, not assumed.

**Does screening still net a benefit, given its own ~20% false-negative rate (Sec.18.3)?**
Checked two things directly, no new sampling (reusing Sec.18's already-collected data):

- **Run-level screening does not rescue the FNR either.** 34/300 damping=0.05 runs have
  ALL 24 nodes screened out (zero candidates) under the corrected criterion. Within
  Sec.18.3's sample_A (screened-out node-checks), splitting by whether the node's run had
  zero candidates elsewhere or at least one: 3/8 (37.5%) of zero-candidate-run node-checks
  verified true anyway, versus 12/67 (17.9%) for screened-out nodes in runs that DO have
  other candidates. The small zero-candidate-run sample (n=8) is too small to trust the
  exact 37.5% figure, but directionally, skipping entire runs with zero short-window
  candidates would NOT have solved the false-negative problem -- it is at least as large at
  the run level as at the node level, not a node-level-only artifact.
- **Screening's cost saving is smaller than its false-negative cost suggests it should be.**
  Because the expensive step's cost is essentially PER RUN (once batched), not per
  candidate node, screening's node-level filtering provides no computational benefit for
  the long-window step at all -- the only lever screening has left is skipping whole runs
  with zero candidates, which saves at most 34/300 (~11%) of the exhaustive cost while (per
  the point above) still discarding real persistent nodes at a comparable rate to the
  general population.

**Conclusion, disclosed as a recommendation, not acted on this PR**: for a ONE-TIME
measurement pass (which is what this project's sweeps are), screening's net benefit is
weak -- it is nearly free to run (~61-91s) but so is exhaustive batched verification
(~58 minutes), and screening's false-negative rate (~20%, comparable at the run level) means
its survivors should not be treated as a ground-truth population for density claims without
the kind of correction Sec.18 had to apply after the fact. Screening remains useful as a
cheap FIRST-PASS triage (e.g., for prioritizing which runs to look at, or in a setting where
the same sweep is re-run repeatedly and the ~24x-57x cost difference compounds), but this
project's screening-then-only-occasionally-spot-check pattern is not well justified by the
numbers measured here. Whether to actually run the now-affordable exhaustive pass (which
would also resolve S-015 outright) is left to review's decision -- not run this PR, per the
standing instruction not to pursue firming up the density estimate.

### 19.4 S-015's status is unchanged by this section, exactly as review anticipated

Per review's instruction 4: S-015 (Sec.18) remains PENDING. Sec.19.1's direct measurement
did not need it -- R8's viability question was answered (for the current sweep: coverage
exists in exactly one run, and the one measurable example shows null winding) without
resolving the corrected-density point estimate or its conditional-denominator alignment.
S-015 is recorded as "not required for this PR's R8 determination," not as resolved,
superseded, or no longer worth investigating -- a future PR may still want the exhaustive
figure for other reasons (e.g., quantifying screening's true FNR precisely, or informing
substrate-parameter search), now known to be affordable (Sec.19.3) whenever review wants it.

### 19.5 9th-audit and 8th-audit re-check on Sec.19's own claims

- **9th audit:** "2 candidate-covered cycles, both truly verified, both null winding" is
  reported at exactly the resolution the data supports -- explicitly flagged as ONE run,
  not "multiple independent cycles," and the winding result is reported as null with the
  same directness a positive winding value would get, not hedged into ambiguity. The
  denominator-mismatch finding (19.2) is a NEGATIVE finding about the review's own prior
  framing (24.0% is not validly "close to" 30%) and is stated as such, not soft-pedaled
  because it complicates an otherwise encouraging picture (coverage now exists).
- **8th audit:** was the erdos_renyi/seed=4 example, or the specific 2 cycles reported,
  selected in any way? No -- it is the ONLY run out of 300 whose candidate mask fully
  covers any length>=5 cycle; there was no alternative example to choose between. The
  cost-benchmark configs (12 runs) were the first 12 damping=0.05 entries in the existing
  sweep file in stored order, not selected for a favorable number -- and the resulting
  recommendation (screening's benefit is weak) is not the "protect existing infrastructure"
  answer a motivated selection might have produced; it recommends work (exhaustive
  verification) beyond what review asked to be run this PR, and says so plainly rather than
  either quietly running it or quietly avoiding the recommendation.

## 20. PR-R2.8: R8's final determination -- 178 covered cycles exist (not 2), nonzero
winding occurs on 48% of them, but ZERO pass the smoothness gate; Sec.19.1's "candidates
are an upper bound" assumption was wrong and is corrected here

Per review's instruction: ran the now-affordable (Sec.19.3) exhaustive, batched long-window
verification of the FULL 300-config damping=0.05 sweep -- the single largest outstanding
gap this PR series had left unmeasured because it was assumed too expensive. Also computed
winding on the resulting real, abundant material (not requested in so many words, but a
direct, cheap, disclosed extension of the same "measure before theorize" pattern review has
required throughout, now applied at scale instead of to one example).

### 20.1 Exhaustive verification: S-015 resolved from estimate to exact measurement

`verify.verify_long_window_all_nodes` (PR-R2.7), one call per run (not per node), across all
300 `damping=0.05` configs. Wall-clock: 2875s (~48 minutes, close to Sec.19.3's ~58-minute
projection).

| | value |
|---|---|
| total verified node-checks (TRUE, long-window) | **1992 / 7200** |
| density, unconditional (7200-denominator, "3.1%/24.0%-style") | **27.7%** |
| runs with >=1 verified node | 263 / 300 |
| density, conditional on run having >=1 verified (2400/9.3%-style) | **31.6%** |

**S-015 is no longer pending -- it is MEASURED.** Both figures exceed every prior estimate
in this series: the original 3.1% (223/7200), the original 9.3% (223/2400), and even
Sec.18.3's own sampled correction of 24.0%. The sampled estimate was directionally correct
(density is much higher than 3.1%/9.3% suggested) but, being a 2-population sample, modestly
UNDERSHOT the true figure (24.0% vs the now-measured 27.7%) -- reported here for the record,
not to claim the earlier estimate was wrong in kind, only in degree, which is exactly the
kind of gap a "PENDING" label exists to cover.

### 20.2 Exact screening precision/recall -- and Sec.19.1's error, found and corrected

Cross-tabulated the free-fix candidate mask (short window, Sec.18.1) against the TRUE
(long-window) verified mask, exactly, for all 7200 node-checks:

| | candidate | not candidate |
|---|---|---|
| **true-verified** | 520 (TP) | 1472 (FN) |
| **not true-verified** | 655 (FP) | 4553 (TN) |

- exact screening precision (TP / all candidates): **44.3%** -- more than half of
  short-window candidates (655/1175, 55.7%) do NOT hold up at long window.
- exact FNR of all true-verified nodes: **73.9%** -- nearly 3 in 4 genuinely persistent
  nodes were NOT short-window candidates at all.
- exact FNR within the screened_out population specifically: **24.4%** -- close to, and
  slightly above, Sec.18.3's sampled 20.0% estimate (n=75), good corroboration that the
  earlier sampling was not a fluke, just imprecise.

**This directly falsifies PR-R2.7 Sec.19.1's stated assumption** that short-window
candidates are a SUPERSET of true-verified nodes (an upper bound for cycle coverage).
Candidate status and long-window-verified status are computed from DIFFERENT segments of
the same trajectory (short window's trailing quarter is steps ~2250-3000; long window's
trailing quarter is steps ~33750-45000) -- there is no logical containment relationship
between them, and the empirical numbers above show neither direction holds cleanly. Sec.19.1
has been annotated in place with this correction; its "2 covered cycles" conclusion is
superseded by Sec.20.3 below, not merely refined.

### 20.3 Cycle coverage on the TRUE verified set -- R8's final determination

Same cycle extraction as Sec.19.1 (`topology.fundamental_cycles`, length>=5, all 300
configs, 4155 total cycles), now checked against the EXACT verified mask from Sec.20.1
instead of the flawed candidate proxy:

| | value |
|---|---|
| length>=5 cycles fully covered by the TRUE verified set | **178** (vs. 2 from the flawed candidate-based method) |
| by length | 5: 74, 6: 47, 7: 34, 8: 7, 9: 6, 10: 7, 11: 3 |
| by topology | random_regular: 65, watts_strogatz: 52, erdos_renyi: 32, barabasi_albert: 29 |
| unique (seed, topology, strength) runs contributing | 35 (i.e. not one run's overlapping duplicates -- genuinely spread across many independent runs, all 4 topologies, seeds 0-14) |

Material for R8 is **abundant**, not scarce -- the opposite conclusion from Sec.19.1's
undercount. This alone overturns review's own working hypothesis going into this PR ("被覆
は2本...R8は現状の材料では成立しません") on the MATERIAL-availability question
specifically; the material-scarcity framing does not survive contact with the exhaustive
measurement. Whether R8 is viable on this abundant material is a separate question, answered
next.

### 20.4 Winding on all 178 covered cycles: 48% show nonzero raw winding, 0% pass the
smoothness gate

Computed the real instantaneous phase (analytic-signal angle at the midpoint of R7's
phase-analysis window, same method as Sec.15.2/19.1) for every node touched by the 178
covered cycles, batched by the 35 unique underlying runs (not 178 separate reruns).
`winding_precheck.py` (still explicitly NOT R8) applied to each:

| | value |
|---|---|
| cycles with nonzero raw winding (`compute_winding() != 0`) | **86 / 178 (48.3%)** |
| cycles passing the smoothness gate (`winding!=0 AND max_adjacent_step < pi/2`) | **0 / 178 (0.0%)** |
| raw winding value distribution | 0: 92, -1: 42, +1: 39, -2: 3, +2: 2 |

This is the decisive result. Nonzero winding is NOT rare here -- it occurs on nearly half
the covered cycles, mostly |winding|=1. But it NEVER survives the smoothness gate: every
single nonzero-winding cycle has at least one adjacent phase step exceeding pi/2. Per
Sec.16.2's own null-rate table, the composite (nonzero AND smooth) criterion has a null rate
below 0.05% for N>=5 under i.i.d. random phases -- so a 0/178 pass rate, on cycles that are
NOT random (they come from a substrate with real, measured phase structure), is not
consistent with "we just haven't sampled enough cycles yet." It is consistent with a
STRUCTURAL fact about this substrate: nodes within a covered cycle cluster in phase (locally
entrained/synchronized) rather than smoothly rotating around the loop, so the nonzero raw
winding values that do appear are attributable to one or two outlier nodes' large phase
jumps (exactly what the smoothness gate is built to catch), not genuine coherent spatial
phase propagation.

### 20.5 R8's determination, recorded per review's requested framing

Per review's explicit instruction: this is recorded as **"in this substrate, under this
coupling form (diffusive, Sigma w_ij(x_j - x_i)), on these topologies, no cycle currently
produces a winding measurement that survives the smoothness gate"** -- NOT as "R8 is
impossible" and NOT (unlike Sec.19.1's premature framing) as "no measurable material
exists." Material is abundant (178 cycles, Sec.20.3); nonzero raw winding is common (48.3%,
Sec.20.4); the block is specifically that raw winding does not co-occur with smooth phase
transport, at a rate far below what chance alone would produce. This is a materially
stronger and more specific null result than either Sec.15's "only triangles exist" or
Sec.19.1's "only 2 cycles, both null" -- it rules out the "not enough data" objection
explicitly, on real (not synthetic) material, at scale.

### 20.6 Item 2 (coupling-form axis): condition not met, NOT implemented this PR -- but the
underlying evidence for it just got much stronger

Review's stated trigger for adding a coupling-form axis was explicit: "1の結果が『実質1〜2本
のまま』だった場合" (if (1)'s result stays at essentially 1-2 cycles). It did not -- 178
cycles, 35 independent runs, all 4 topologies (Sec.20.3). Per the literal condition, this PR
does NOT implement a coupling-form axis.

Flagged for review's decision, not acted on unilaterally: Sec.20.4's result (86/178 nonzero
raw winding, 0/178 smooth) is DIRECT, at-scale evidence consistent with exactly the
mechanism review's own hypothesis for item 2 proposed -- diffusive/attractive coupling
(Sigma w_ij(x_j - x_i) pulls neighboring nodes' states together) entraining phases into local
clusters rather than permitting the slow, coherent spatial phase rotation winding requires.
This was not the trigger condition review specified (which was about MATERIAL scarcity, now
resolved as abundant), but it is a different, and arguably stronger, piece of evidence for
the SAME underlying question review's item 2 was designed to test. Whether to proceed with a
second coupling-form axis on this basis -- now backed by an exact 0/178 smoothness-gate pass
rate on real material rather than either a material shortage or a hypothesis alone -- is left
to review.

### 20.7 9th-audit and 8th-audit re-check on Sec.20's own claims

- **9th audit:** the exhaustive verification and the winding measurement are both computed
  by the SAME, already-validated instruments used throughout this series
  (`verify_long_window_all_nodes` is the batched form of the identical criterion as
  `verify_long_window`, tested equivalent in PR-R2.7; `winding_precheck.py` is unchanged
  since Sec.16). No gate was loosened or instrument altered to produce either the 178-cycle
  count or the 0/178 smoothness result. The correction of Sec.19.1's error is stated as a
  correction, with the exact numbers that falsify it (Sec.20.2), not quietly folded in.
- **8th audit:** was the decision to compute winding on all 178 cycles (rather than, say, a
  sample, or none at all) made to produce a particular outcome? No -- it was cheap (35
  unique reruns, ~100s total, batched) and directly extends the exact same method already
  used on the 2-cycle sample in Sec.19.1, at no additional design choice; every one of the
  178 was checked, not a subset chosen after seeing partial results. Was the 0/178 result
  itself surprising, or did prior sections anticipate it? Sec.16.2's null-rate table
  predicted <0.05% for the composite criterion under RANDOM phases -- 0/178 on real,
  non-random material is consistent with that table only if the substrate's real phase
  structure is EVEN LESS favorable to smooth winding than random chance, which is itself a
  notable, disclosed finding, not swept past. Item 2's flagged-but-not-implemented status
  (Sec.20.6) is reported as a live open question for review, not silently decided either
  way.

## 21. PR-R3 (S-016 recorded): coupling_form -- diffusive coupling was the only functional
shape this substrate ever offered; it becomes a switchable axis

Per review's decision (S-016): Sec.20.4's 0/178 smoothness-gate pass rate, on abundant
material (178 covered cycles, not a scarcity artifact), is recorded as a real structural
result, not a sampling gap. Review's own condition for adding a coupling-form axis ("still
~1-2 cycles") was not met, but review explicitly REPLACED that condition with a stronger
one: the 0/178 result itself, combined with review's mechanistic account (diffusive
coupling entrains phases toward local agreement; winding requires them to decorrelate while
circling a loop -- opposite requirements), is reason enough on its own. This section
implements that.

### 21.1 What changed and why (S-016's reasoning, recorded verbatim in spirit)

The chain "difference -> direction -> repetition -> period -> phase -> cycle -> winding"
reached phase and stopped at winding (Sec.20). Diffusive coupling, Sum_j w_ij(x_j - x_i), is
a MONOTONIC, unboundedly-attractive response to a pairwise difference -- larger differences
pull harder, always toward agreement. Every other axis in this module (memory, asymmetry,
saturation, damping, topology) varied something about HOW the system evolves; the
functional SHAPE of the pairwise response itself, phi(z) in w_ij * phi(x_j - x_i), was never
varied -- phi(z)=z was implicit and universal since PR-R1. `coupling_form` (new,
`substrate.py`, default "diffusive", unchanged formula) makes phi itself a switchable
ingredient axis, the same way every other ingredient here is switchable.

### 21.2 8th audit: was this designed toward making phase wind? (review's explicit
instruction to self-report)

Three new forms were added: `bounded_tanh` (phi=tanh(z), bounded, still monotonic),
`cubic_odd` (phi=z^3, unbounded, superlinear, vanishes faster than linear near z=0),
`sinusoidal` (phi=sin(z), bounded and NON-monotonic -- the only one of the four whose sign
is not fixed by the sign of z alone). Framing used to choose them: the next natural members
of "odd functions of the pairwise difference" (phi(-z)=-phi(z), so a symmetric W still gives
a symmetric attraction) beyond the existing linear case -- NOT a search over forms known to
produce phase-locking/winding.

Direct, disclosed answer to review's question: **partially, and it is disclosed rather than
hidden.** `sinusoidal` (phi=sin(z)) is honestly the textbook coupling form associated with
phase synchronization in the outside literature (the Kuramoto model's coupling term has this
exact shape) -- awareness of that association was part of why it, rather than some other
non-monotonic odd function, was the one selected to represent the "bounded and
non-monotonic" cell of the family. That is a real point of tension with review's
instruction, named here rather than concealed. What was NOT done, and is the operative
distinction: no free parameter of `sinusoidal` (amplitude, an added phase offset, a
per-cycle-length-tuned frequency) was introduced or tuned toward making any particular cycle
wind; `phi(z)=sin(z)` uses no such parameter at all. Three forms were tested, not one
cherry-picked form, so a failure of `bounded_tanh` or `cubic_odd` to change anything remains
informative rather than being quietly dropped. The winding measurement itself
(`winding_precheck.py`, the smoothness-gate threshold pi/2, the <0.05% null-rate table) is
completely unchanged from Sec.16 -- fixed BEFORE this PR's coupling-form idea existed, so
it could not have been tuned toward this section's outcome in either direction. Sec.21.4
reports whatever the exhaustive measurement finds for ALL THREE forms, including
`bounded_tanh` and `cubic_odd`'s results, specifically so a possible "sinusoidal alone winds
because it was chosen to" story is falsifiable by the other two forms' data being visible
alongside it, not omitted.

### 21.3 Re-deriving the theorem chain (S-002/S-003/S-010-equivalents) for each new form

**S-002-equivalent (memory=off, symmetric W: no sustained periodicity -- originally a
gradient-flow/Lyapunov argument, Sec.3.1/10.2, Gershgorin-based).** The original argument
uses that diffusive coupling is the gradient of a potential, V(x) = (1/2) Sum_{i<j}
w_ij (x_j-x_i)^2, so dx/dt = -grad(V) strictly decreases V except at critical points --
excluding sustained periodic orbits. This generalizes to any coupling_form phi that is odd
(phi(-z)=-phi(z)) with an EVEN antiderivative Phi (Phi'=phi, Phi(-z)=Phi(z)): the pairwise
force w_ij*phi(x_j-x_i) is then the gradient of V(x) = Sum_{i<j} w_ij * Phi(x_j-x_i), and the
same "V strictly decreases" argument applies regardless of Phi's specific shape, as long as
it is bounded below. Checked for all three new forms:
  - `bounded_tanh`: integral of tanh(z) is ln(cosh(z)) -- even, bounded below (>=0) -- valid.
  - `cubic_odd`: integral of z^3 is z^4/4 -- even, bounded below (>=0) -- valid.
  - `sinusoidal`: integral of sin(z) is -cos(z) -- even, bounded (in [-1,1]) -- valid.

  All three remain gradient flows of a bounded-below potential, so the SAME no-periodicity
  conclusion is expected to hold for symmetric W, memory=off, for all three -- not merely by
  analogy, but by the same structural argument (existence of Phi), independent of the local
  linear (Gershgorin/eigenvalue) machinery. Empirically spot-checked (n=16,
  `random_regular`, symmetric W, `saturation="cubic"`, 2000 steps): 0/16 nodes
  `sustained_and_settled` for memory=off, all four coupling_forms including diffusive --
  consistent with the argument, not yet an exhaustive sweep.

**S-003-equivalent (memory=on, symmetric W, damping>0: energy decays, no sustained
oscillation).** The original argument uses total mechanical energy E = (1/2)Sum_i|v_i|^2 +
V(x); dE/dt = -damping*Sum_i|v_i|^2 <= 0 regardless of V's specific functional form, as long
as the force is still -grad(V) for SOME V (shown above, for all three new forms) --
dissipation removes energy monotonically until the system settles at a V-minimum. This
argument never used the LINEAR/quadratic form of V at all, so it transfers to all three new
forms with no additional caveat. Empirically spot-checked (same config, memory=on,
damping=0.1): total |v| (a kinetic-energy proxy) decayed by 96-98% from the first quarter to
the end of the recording for ALL FOUR forms, including a near-zero-magnitude but still
clearly decaying `cubic_odd` trajectory (see caveat below) -- consistent with decay, not yet
an exhaustive sweep.

**S-010-equivalent (memory=on, asymmetric W: q^2 > p*gamma^2 threshold for linear
instability, hence sustained oscillation once capped by saturation).** This argument is
SPECIFICALLY a linear (eigenvalue-of-L) argument -- it does not generalize the way the
gradient-flow argument does, because it depends on the coupling being EXACTLY linear, not
merely conservative. What DOES generalize: the LOCAL linearization of the full nonlinear
system at x=0 (the Jacobian of `_relation_coupling(x, W, form)` with respect to x, evaluated
at x=0), which governs whether a SMALL perturbation from equilibrium grows or decays.
Computed both analytically (phi'(0)) and numerically (finite-difference Jacobian, n=6,
`erdos_renyi`, exact to floating-point precision):

  | form | phi'(0) | numerical Jacobian at x=0 |
  |---|---|---|
  | `diffusive` | 1 | exactly -L |
  | `bounded_tanh` | tanh'(0) = 1 | exactly -L (matches diffusive to float precision) |
  | `sinusoidal` | cos(0) = 1 | exactly -L (matches diffusive to float precision) |
  | `cubic_odd` | d/dz[z^3] at 0 = 0 | exactly the ZERO matrix |

  **`bounded_tanh` and `sinusoidal` share diffusive's EXACT linearization at the origin** --
  so the q^2 > p*gamma^2 threshold, which is a statement purely about L's eigenvalues,
  applies IDENTICALLY to these two forms in the small-amplitude regime near equilibrium: the
  same inertia + asymmetry + damping combination that destabilizes the origin for diffusive
  coupling destabilizes it identically for `bounded_tanh`/`sinusoidal`, since the linear
  operator governing that regime is the SAME matrix, -L, in all three cases. **`cubic_odd`'s
  linearization at the origin is the ZERO operator** -- there is NO linear growth mechanism
  near equilibrium at all; the entire "inertia converts a marginal rotational mode into
  growth" mechanism (Sec.10.3) has nothing to act on locally, since the leading-order
  response to any small perturbation is cubically, not linearly, weak. This is exactly the
  kind of theorem-breakage review asked to have recorded as a result in its own right, not
  silently patched around: **`cubic_odd` coupling is not expected to reproduce sustained
  oscillation via the SAME mechanism the other three forms share**, and Sec.21.4 checks this
  prediction directly against the exhaustive sweep.

### 21.4 Full battery: exhaustive verification, cycle coverage, winding, damage-recovery --
same 300-config damping=0.05/saturation=cubic sweep space as the diffusive baseline
(PR-R2.8), no screening (Sec.21.5), for all three new forms

| coupling_form | density (uncond / cond) | length>=5 cycles covered | nonzero winding | **smooth winding** | damage-recovery sample |
|---|---|---|---|---|---|
| `diffusive` (baseline, PR-R2.8) | 27.7% / 31.6% | 178 | 86 (48.3%) | **0 (0.0%)** | 8/8 (100%, Sec.13.6/14.1) |
| `bounded_tanh` | **40.9% / 45.4%** | **314** | 114 (36.3%) | **1 (0.3%)** | 7/8 (87.5%) |
| `sinusoidal` | 9.4% / 26.9% | 190 | 98 (51.6%) | **1 (0.5%)** | 6/8 (75.0%) |
| `cubic_odd` | 0.04% / 6.25%* | 0 | 0 | 0 | 0/3 (0.0%) |

*`cubic_odd`'s conditional density is not a meaningful percentage -- only 2/300 runs had
ANY verified node, so the denominator is 2*24=48, not a comparable population to the other
rows'.

**`bounded_tanh` roughly doubles persistence density and cycle coverage relative to
diffusive** -- a substantial, disclosed positive finding about the coupling-form axis on
its own, independent of the winding question. **`cubic_odd` collapses to near-total
absence of persistence**, exactly as Sec.21.3 predicted from its vanishing origin
Jacobian. **`bounded_tanh` and `sinusoidal` each produce exactly ONE smooth-winding
cycle** -- the first nonzero result on this criterion anywhere in this PR series. All of
this is examined in detail below, with the same scrutiny applied whether the result looks
encouraging or not.

#### 21.4.1 `cubic_odd`'s near-total collapse: diagnosed, not a numerical bug

The sweep log shows `RuntimeWarning: overflow` for `cubic_odd` at high
`asymmetry_strength`. Diagnosed directly (not assumed): at the DEFAULT/low strength
(0.3, `random_regular`, 5 seeds spot-checked), all trajectories stay FINITE and DECAY (peak
amplitude ~0.2-0.3 early, ~0.006-0.04 by a 20000-step tail) -- consistent with Sec.21.3's
prediction that no linear growth mechanism exists near the origin, so the initial small
epsilon-perturbation simply relaxes away. At HIGH strength (20.0, spot-checked 3 seeds),
trajectories are confirmed NON-FINITE (`|x|` reaching 1e39-1e85 within the original
3000-step window) -- the cubic (superlinear) response, once ANY difference exceeds O(1),
grows as that difference's CUBE, a genuine positive-feedback blowup absent from the other
three (bounded or exactly-linear) forms. Confirmed `instruments.period()` correctly returns
`defined=False` for a non-finite trajectory (spot-checked directly), so
`verify_long_window_all_nodes` correctly reports `verified_sustained=False` for these runs
-- the near-zero density is NOT an artifact of mishandled overflow, it is the honest,
correctly-measured consequence of a coupling form with (a) no destabilizing mechanism near
equilibrium and (b) an unbounded, superlinear response once perturbed away from it: `cubic_odd`
has essentially no intermediate regime between "decays back to near-zero" and "diverges,"
exactly the two outcomes Sec.21.3's Jacobian argument would predict for a form with a
degenerate local linearization and no saturating ceiling of its own on the coupling term
(the saturation axis's cubic cap acts on x_i alone, not on the coupling response to a
difference).

#### 21.4.2 The one smooth-winding example: full account, with the scrutiny an unusual
result requires

Both `bounded_tanh` and `sinusoidal`'s single smooth-winding cycle are THE SAME underlying
graph: `erdos_renyi`, seed=9, `asymmetry_strength=0.3`, cycle `[4, 14, 9, 0, 12, 21]`
(length 6). This is NOT two independent events -- it is one real-world graph/topology
instance, observed to produce genuine smooth winding under two different (but
linearization-matched, Sec.21.3) coupling functional shapes. It was NOT a covered cycle at
all under `diffusive` coupling on the same seed/strength (fewer nodes verified there, so
this specific cycle never had all 6 nodes persist).

| coupling_form | winding | max adjacent step | smoothness gate (< pi/2 = 1.5708) |
|---|---|---|---|
| `bounded_tanh` | -1 | 1.4888 | PASS |
| `sinusoidal` | -1 | 1.4951 | PASS |

**Robustness check** (disclosed, fixed choice -- extend_factor doubled from 15x to 30x, not
a search over many windows for a favorable one): re-verified on the SAME cycle at a 30x
window instead of 15x. Result is essentially unchanged for both forms (`bounded_tanh`:
winding=-1, max_step=1.4882; `sinusoidal`: winding=-1, max_step=1.4944) -- this is not an
artifact of one particular snapshot moment; it persists under a substantially longer
observation window.

**Statistical caution, stated plainly.** The margin below the smoothness threshold
(pi/2=1.5708) is modest -- about 0.08 rad (~5 degrees) for both forms, not a wide margin.
Treating the two sweeps' 314+190=504 total covered-cycle checks as if they were independent
draws against Sec.16.2's <0.05% null rate (which assumes i.i.d. RANDOM phases -- not
strictly applicable here, since these are correlated, real dynamical trajectories, not
random draws, but useful as an order-of-magnitude sanity bound): the expected count of
false positives by chance alone is ~504 * 0.0005 ~= 0.25, and P(at least one hit | that
expected rate, Poisson) ~= 22%. **This means a single hit, on its own, across ~500 trials
is NOT strong enough evidence to rule out chance.** What raises this above a pure
coincidence, without settling the question, is the CROSS-FORM replication: the SAME graph,
under two different coupling shapes that happen to share the same near-origin
linearization, both produced a smooth-winding result on the SAME cycle -- a coincidence
occurring independently on the same graph under two different dynamics is less likely than
a single one-off hit, though this is a qualitative, not a formally quantified, argument (no
attempt is made here to compute a p-value for the cross-form coincidence specifically --
that would require a null model for how correlated two different coupling forms' winding
outcomes are on the same graph, which is not established).

**Explicit conclusion, matching this series' standing discipline against overclaiming: this
is reported as a CANDIDATE / LEAD, not as an achieved result.** R8 (winding number as an
instrument) is still NOT built. No new SETTLED.md entry claiming winding is "achieved" is
written this PR -- that determination is left to review, consistent with every prior PR in
this series treating a first positive signal as something to flag and scrutinize, not
something to declare. The concrete, disclosed next step this finding suggests (not run
this PR): sweep `bounded_tanh`/`sinusoidal` more broadly (more seeds, more topologies) to
see whether MORE examples of smooth winding turn up elsewhere, which would be the actual
resolution of the "chance vs. real" question above -- a single example, however robust to
window length, cannot answer it alone.

### 21.5 Screening abolished (review's explicit instruction)

Per review's instruction, given PR-R2.8's exact measurement of screening's error rate
(precision 44.3%, recall 26.1% -- i.e. missing 73.9% of true positives, Sec.20.2): no
short-window pre-filter was used anywhere in this PR's sweeps. `verify_long_window_all_nodes`
was called directly on the full 7200-node-check candidate space for each of the three new
coupling forms, exactly as it was for the diffusive re-verification in PR-R2.8. Documented
in `verify.py`'s module docstring (a standing note, not a one-time remark) so this is not
silently reintroduced by a future PR reaching for the old, cheaper-looking pattern.

### 21.6 9th-audit and 8th-audit re-check on Sec.21's own claims

- **9th audit:** every measurement in this section uses instruments already validated
  earlier in this series (`verify_long_window_all_nodes` from PR-R2.7/2.8,
  `winding_precheck.py` unchanged since Sec.16, `check_attractor_recovery` unchanged since
  Sec.13) -- no threshold, window rule, or gate was loosened, tightened, or introduced fresh
  to produce Sec.21.4's results. The smooth-winding finding is reported with an EXPLICIT
  statistical-caution paragraph (the ~22% chance-alone probability) rather than as a bare
  positive count -- the discipline this series applies to non-achievement claims (never
  assert without checking expressibility) is applied here in the mirror-image direction:
  never assert achievement without checking whether the positive result could plausibly be
  chance.
- **8th audit, on the section as a whole:** did discovering ONE smooth-winding example
  change how anything upstream was measured or reported? No -- the comparison table
  (Sec.21.4) reports ALL three new forms' full results, including `cubic_odd`'s complete
  failure and `bounded_tanh`/`sinusoidal`'s density/coverage numbers, not just the winding
  finding in isolation; the robustness check (extend_factor 15x->30x) and the chance-alone
  calculation were BOTH performed and BOTH reported, including the calculation that argues
  AGAINST over-trusting the result, not only checks that would have supported it. Was the
    smooth-winding example itself found by searching multiple windows/checkpoints for a
  favorable one? No -- it was found on the FIRST computation, at the SAME fixed midpoint-of-
  window rule used throughout this series (Sec.14.4/15.2/19.1/20.4); the SECOND (30x)
  computation was run afterward, specifically as a disclosed robustness check, and its
  result (not materially different) is reported regardless of whether it had changed the
  conclusion. Sec.21.2's disclosed tension (choosing `sinusoidal` partly due to awareness of
  its literature association with phase coupling) is revisited here: that awareness could
  have created pressure to report this section's result more confidently than the data
  supports -- the explicit "CANDIDATE / LEAD, not achieved" framing and the chance-alone
  calculation are the concrete, checkable evidence that this pressure was not acted on.

## 22. PR-R3.1: three targeted tests on the single winding example -- one inconclusive
(not failed), one strongly confirming, one mixed but physically coherent; combined verdict
is NOT NOISE

Per review's correction: 2 hits (bounded_tanh AND sinusoidal), on the SAME graph/seed/
strength/cycle, with the SAME sign, is a form of replication, not two independent draws
against a chance table -- review's instruction to test this example directly, before any
broader sweep, is executed here. Target example throughout: `erdos_renyi`, seed=9,
`asymmetry_strength=0.3`, cycle `[4, 14, 9, 0, 12, 21]` (length 6), which gave winding=-1,
`max_adjacent_step`~1.49 for both `bounded_tanh` and `sinusoidal` (Sec.21.4.2).

### 22.1 Test 1: sign symmetry under orientation reversal -- INCONCLUSIVE (not failed)

Two reversals tested: (a) global `W -> W^T` (equivalent to flipping the sign of the
asymmetry construction's `chi` for every edge); (b) a more surgical LOCAL reversal of only
the 6 edges belonging to the cycle itself, leaving the rest of the graph untouched. Neither
produced winding=+1 on the same 6 nodes -- both instead ELIMINATED sustained oscillation on
this node set entirely (`winding=0`, `max_adjacent_step`~0.0000-0.0001, `all_settled=False`
for both forms, both reversal types).

**This is not a failed prediction -- it is a test that does not cleanly apply, for a
reason grounded in linear algebra, checked directly rather than assumed:** the eigenvalues
of a real square matrix W and its transpose W^T are IDENTICAL (`det(W-lambda*I) =
det((W-lambda*I)^T)`, always, for any real square matrix). The q^2 > p*gamma^2 threshold
(Sec.10.3/21.3) depends ONLY on eigenvalues of the coupling operator -- so a global
transpose changes NOTHING about which growth rates/rotation magnitudes exist in the system.
What transpose DOES change is the EIGENVECTORS -- which spatial pattern of nodes hosts a
given unstable mode -- and there is no guarantee that the SAME 6 nodes remain the
localization of an analogous mode after transpose; empirically, they do not (this specific
node set stops oscillating altogether under both reversal variants). The naive "same cycle,
opposite sign" expectation implicitly assumes a level of structural symmetry (e.g. a normal
operator, where eigenvectors ARE preserved under transpose up to conjugation) that this
general asymmetric, inertial, saturated, nonlinear-coupling system does not provide by
construction. **Verdict: this test neither confirms nor refutes the original finding** --
it was not possible to execute in a way that isolates sign from spatial localization for
this specific system.

### 22.2 Test 2: perturbation robustness -- STRONGLY CONFIRMS

Two independent perturbation designs, both against the FORWARD (original) graph:

- **6 independent random initial conditions** (disclosed seeds 100-105, fixed in the script
  before any run, not searched for a favorable outcome), same graph W, same seed=9 topology,
  for each of `bounded_tanh` and `sinusoidal` (12 trials total).
- **Amplitude perturbation** (damage-recovery style, reusing `verify.py`'s own
  `DEFAULT_PERTURB_FACTOR=0.4` / `DEFAULT_CHECKPOINT_FRAC=0.6` constants unchanged): the
  settled trajectory's entire state is rescaled by 0.4 at a checkpoint and continued, for
  each of the 2 forms (2 trials).

**Result: 14/14 trials give `winding=-1`, PASS the smoothness gate, with
`max_adjacent_step` clustered tightly in [1.4818, 1.4957]** -- essentially the same value
every time, across independent random draws AND after being knocked off-plateau and
allowed to re-settle. Two of the fourteen (`bounded_tanh` and `sinusoidal` both at
`ic_seed=101`) show `all_settled=False` on the strict per-node flag despite still producing
a consistent, smooth, correctly-signed winding value -- noted, not concealed, but does not
change the overall pattern. **A pure one-off coincidence would not be expected to reproduce
identically across 12 independent random initial conditions plus 2 different perturbation
recoveries, for 2 different coupling forms.** This is the single strongest piece of evidence
in this section.

### 22.3 Test 3: cycle-shift (loop-boundary deformation) -- MIXED, but physically coherent,
not consistent with pure noise

Manually enumerated (networkx unavailable in this environment; DFS restricted to the local
19-node neighborhood) all simple cycles sharing >=4 of the original 6 nodes: **223
candidates**, lengths 4-9. Winding was evaluated on ALL 223, for both forms, reusing a
SINGLE trajectory snapshot per form (no new simulation per candidate cycle -- phase is a
per-node quantity, read off once for all 19 local nodes).

**Result: exactly 3/223 pass the smoothness gate, for BOTH forms, identically:**

1. `[0, 9, 14, 4, 21, 12]` (length 6) -- on inspection, this is the EXACT SAME 6 edges as
   the original cycle, just traversed in the opposite rotational order (a rotation of the
   REVERSED original sequence). Its winding=+1 is the trivial algebraic consequence of
   reversing a cyclic sum's traversal direction (`compute_winding` sums signed differences
   around a loop; reversing the order negates every term) -- **not new physical evidence**,
   just a re-discovery of the same loop via the DFS search, disclosed rather than silently
   dropped.
2. `[0, 9, 2, 15, 1, 14, 4, 21, 12]` (length 9) -- the same reversed loop with its 9-14 edge
   replaced by a 4-hop detour through nodes 2, 15, 1. winding=+1 (matches the reversed
   loop's sign, consistent with a smooth deformation of the same enclosed structure).
3. `[0, 9, 2, 15, 6, 14, 4, 21, 12]` (length 9) -- the same detour with node 6 substituted
   for node 1. winding=+1, same as above.

**These two detour cycles ARE genuine new evidence**: rerouting through 3 extra,
well-connected nodes (all part of the same local neighborhood) while preserving the
enclosed structure's winding sign is consistent with a real, spatially coherent rotating
region -- exactly what a topological quantity should do under a smooth boundary
deformation that does not cross the structure's core.

**The most direct test the graph's actual structure offers -- swap exactly ONE node,
same length 6** -- `[0, 12, 21, 4, 14, 13]` (node 9 replaced by node 13, the only such
same-length alternative this graph provides) -- **FAILS**: `winding=0`,
`max_adjacent_step=2.27` (well past pi/2, not a marginal miss), for both forms. Diagnosed
directly, not left unexplained: node 13 has degree 2 (peripheral in this graph, versus
node 9's degree 4) and an instantaneous phase (~-3.12 rad) nearly pi away from node 9's
(~-0.12 rad) -- consistent with node 13 sitting OUTSIDE the coherent cluster's actual
spatial extent, not with the phase field being unstructured noise (unstructured noise would
not correlate a large phase jump with low graph degree/peripherality in this specific,
interpretable way).

**Verdict: MIXED, not a clean pass.** The phenomenon survives deformation through nodes
that are actually part of the coherent structure, but does not survive substituting in a
node that is not -- a spatially BOUNDED coherent region is exactly what a real, localized
physical structure would produce (finite extent, sharp-ish edge), and is a more specific,
harder-to-fake pattern than either "works everywhere" or "works nowhere but the one exact
cycle" would be.

### 22.4 Combined verdict

Per review's framing ("1〜3が通れば...決着します"): weighing the three tests together --
Test 1 is inconclusive by construction (not evidence either way); Test 2 is a strong,
clean confirmation (14/14, independent draws, two different perturbation mechanisms); Test
3 is mixed but internally coherent (survives structure-respecting deformation, fails at a
diagnosed peripheral-node boundary, exactly as a real local structure would). **Overall
verdict: NOT NOISE.** A one-off numerical coincidence would not be expected to reproduce
identically across 12 independent random initial conditions and 2 independent perturbation
recoveries (Test 2), nor would it be expected to survive specifically the deformations that
stay within the coherent node cluster while failing specifically at a diagnosably
peripheral node (Test 3). This is reported as review requested -- a decisive-enough result
to write up without a broader sweep first -- while still stopping short of building R8 as
a formal instrument this PR, since that remains a distinct, larger undertaking (per this
series' standing discipline against getting ahead of what has been measured). A candidate
S-017 write-up is offered below for review's decision, not asserted unilaterally as
achieved -- consistent with every other achievement-flavored claim in this series requiring
review's own sign-off on the exact wording.

**Proposed S-017 (candidate text, for review to accept, edit, or decline):** "Genuine
smooth phase winding (winding number != 0, all adjacent phase steps < pi/2) has been
measured on a real, reproducible closed loop in the R-layer substrate, under two coupling
forms (`bounded_tanh`, `sinusoidal`) that share diffusive coupling's exact linearization at
the origin. The result -- `erdos_renyi`, seed=9, `asymmetry_strength=0.3`, 6-node cycle
`[4,14,9,0,12,21]`, `winding=-1` -- is robust to 12 independent random initial conditions,
2 independent amplitude-perturbation recoveries, doubling the verification window (15x to
30x), and smooth boundary deformation through the coherent node cluster (detour cycles);
it is NOT robust to substituting a structurally peripheral (low-degree) node into the loop.
Diffusive coupling itself does not produce this result on any of 178 covered cycles
(Sec.20.4); `cubic_odd` coupling does not sustain oscillation on this node set at all. This
does not constitute an R8 (winding-number) instrument -- no such instrument is built this
PR -- and is not asserted to generalize beyond this one located structure without a
broader, independently-seeded sweep (not yet run, review's decision pending)."

### 22.5 bounded_tanh's density-doubling: an independent finding, boundedness vs
non-monotonicity

Recorded on its own merit, independent of the winding question. Restricting to the three
forms that share diffusive's EXACT origin linearization (Sec.21.3 -- `diffusive`,
`bounded_tanh`, `sinusoidal`; `cubic_odd` is excluded from this comparison, its collapse
already explained by a different, local mechanism):

| form | bounded? | monotonic? | density (uncond) | covered cycles (len>=5) |
|---|---|---|---|---|
| `bounded_tanh` | YES | YES | **40.9%** | **314** |
| `diffusive` | no | YES | 27.7% | 178 |
| `sinusoidal` | YES | **no** | 9.4% | 190 |

All three share the SAME small-amplitude linear instability onset (identical Jacobian at
x=0, Sec.21.3) -- so the density DIFFERENCES among these three arise entirely from
LARGE-amplitude behavior (away from the origin), where the three forms diverge: `diffusive`
grows unboundedly (linearly); `bounded_tanh` saturates while remaining monotonically
attractive; `sinusoidal` saturates AND reverses sign past `z=pi`.

**Boundedness alone does not explain the ordering**: `bounded_tanh` (bounded) has the
HIGHEST density, but `sinusoidal` (also bounded) has the LOWEST of the three --
substantially below even the unbounded `diffusive` baseline. If boundedness were the
dominant factor, both bounded forms should exceed the unbounded one; only one does.
**Monotonicity (sign never reversing) appears to be the more load-bearing property**: the
two forms that stay monotonically attractive at all differences (`diffusive`,
`bounded_tanh`) both produce substantial persistence, with the BOUNDED one of the two
producing MORE (40.9% vs 27.7%) -- consistent with a two-factor account: (a) staying
monotonic/attractive avoids introducing a competing REPULSIVE regime past some difference
threshold, which for `sinusoidal` (repulsive past `z=pi`) plausibly fragments or
destabilizes what would otherwise be coherent oscillation, pushing density down; (b) GIVEN
monotonicity is preserved, boundedness (`bounded_tanh` vs `diffusive`) still provides a
further, independent boost -- plausibly because a bounded coupling response prevents any
single large pairwise difference from dominating/overwhelming the local dynamics, working
cooperatively with the already-present `saturation="cubic"` self-term to keep more
configurations in a well-regularized, persistence-friendly regime rather than a
runaway-then-abruptly-capped one.

**Honest limit on this analysis**: only 4 coupling forms were tested, spanning 3 properties
(boundedness, monotonicity, origin-linearization) without a full factorial design -- a
genuinely isolating test would need a 4th form that is UNBOUNDED and NON-MONOTONIC (e.g.
`z*sin(z)`-style), which was not built or run this PR. The account above is offered as the
most consistent INTERPRETATION of the four data points in hand, not a proven, isolated
mechanism -- flagged explicitly as an open item for a future PR if review wants the
2x2 factorial completed.

### 22.6 9th-audit and 8th-audit re-check on Sec.22's own claims

- **9th audit:** every number in this section comes from re-running the SAME, already-
  validated instruments (`substrate.run` with `W_override`/`x0_override`, `instruments.
  _phase_analysis_window`, `winding_precheck.compute_winding`/`is_smooth_winding`,
  `verify.check_attractor_recovery`'s own constants reused unmodified for the perturbation
  test) -- no threshold was adjusted to make Test 2 pass more cleanly or Test 3's mixed
  result look more favorable than it is. Test 1's "inconclusive" framing is stated as such,
  not silently reframed as a pass. Test 3's ONE trivial duplicate (the reversed-traversal
  cycle) is explicitly flagged as not new evidence, rather than folded into "3/223 confirm"
  without qualification.
- **8th audit:** was the local-neighborhood DFS search (223 cycles) tuned to find a
  favorable set, e.g. by adjusting the shared-node threshold or hop radius until 3 hits
  appeared? No -- the search used a single, disclosed, fixed rule (>=4 shared nodes, local
  neighborhood = cycle nodes + their direct neighbors, length capped at 9) decided BEFORE
  running it, and reported the complete result (all 223, not a filtered subset) including
  the ONE swap-test failure that argues against unconditional robustness. Were the 6
  initial-condition seeds (100-105) or the 2 perturbation trials selected after checking
  which ones would confirm the sign? No -- both were fixed, small, sequential seed choices
  made before any run, standard practice throughout this series (matching e.g. Sec.18.3's
  seed=2026 disclosure). The proposed S-017 text (Sec.22.4) is offered as a DRAFT for
  review to accept/edit/decline, not written into SETTLED.md directly by this PR --
  preserving review's standing role as the one who commits achievement-tier language, per
  every prior S-0XX entry in this series.

### 22.7 S-017 and S-018, formally recorded (review's own text, verbatim)

Review accepted PR-R3.1's tests, corrected Sec.22.4's draft framing from "winding arises
from relation" to the narrower, explicitly non-generalized form below, and provided both
entries' final text directly.

**S-017 was WRITTEN with this text, then REVISED by review one PR round later (PR-R5) --
both versions kept here, in order, as the disclosed record of the correction itself.**

**S-017 (original, PR-R3.1 -- SUPERSEDED, see the revision immediately below):
巻きは関係から生じる。ただし結合形に依存し、空間的に局在する**

> 確定したこと :
>   ・拡散結合では 0/178 の閉路しか滑らかさゲートを通らなかったが、
>     単調な結合形（bounded_tanh / sinusoidal）では通過例が出現した
>   ・同一グラフ（erdos_renyi, seed=9, strength=0.3, 6ノード閉路）で、
>     2つの異なる結合形がともに winding=-1 を示した
>   ・独立な初期条件6通り×2結合形＋振幅摂動からの回復2件、計14試行すべてで
>     winding=-1、滑らかさゲート通過、max_adjacent_step が 1.4818〜1.4957 に集中
>     （符号だけでなく位相の刻み方まで一致しており、ノイズでは説明できない）
>   ・近傍閉路223個のうち、迂回変形2個が同符号を維持（巻きは面に属する）
>   ・一方、1ノード入替の代替閉路は不合格。置換ノードは次数2の周辺ノードで
>     位相がほぼπずれており、構造に空間的境界があることと整合する
>
> どう確定したか: 実測＋介入。摂動頑健性と閉路変形の両方を通過。
>                符号対称性の検定（W→W^T）は、WとW^Tの固有値が厳密に同一で
>                閾値が変わらないため、この系には原理的に適用できないと判明した
>
> これでできること:
>   ・「差→向き→反復→周期→位相→閉路→巻き」の連鎖が、限定つきで通った
>   ・次の問いが確定した：なぜ巻きは一箇所にしか生じないのか
>
> これで消えたこと:
>   ・「巻きは関係からは生じない」は誤り。拡散結合という一つの結合形の性質だった
>   ・ただし「関係から円が生まれる」と一般化してはならない。
>     現時点で確認されているのは、特定のグラフの特定の一箇所である

**Review's own correction (PR-R5), verbatim**: "私は前者を後者の証拠として扱いました。
S-017を書けと言ったのは、私の判断ミスです。" -- the 14-trial perturbation-robustness
result (Sec.22.2) is evidence that the ONE located structure is internally robust, not
evidence that the phenomenon occurs generally across the substrate; PR-R4's independent-
seed sweep (Sec.23, 0/284 new hits) is what actually tests generality, and the original
S-017 was written before that test existed. Superseded by:

**S-017（改訂）巻きの通過例は1箇所のみ。再現していない**

> 確定したこと :
>   ・拡散結合では 0/178。単調な結合形では通過例が出現した
>   ・通過箇所は、独立グラフ133個・被覆閉路788件を通じて依然1箇所のみ
>     （erdos_renyi, seed=9, strength=0.3, 6ノード閉路）
>   ・その1箇所は内部的には極めて頑健。独立初期条件6通り×2結合形＋摂動回復2件の
>     計14試行すべてで winding=-1、max_adjacent_step が 1.4818〜1.4957 に集中。
>     近傍閉路の迂回変形2個も同符号を維持
>   ・しかし発見時と独立なseed 50〜64 での284件では通過0件
>   ・構造的な予測因子は見つかっていない。次数は中央付近（44パーセンタイル）、
>     「グラフ全体が100%持続密度」仮説は同条件の他7run・72閉路で 0/72 となり撤回
>
> これでできること:
>   ・この現象が 1/788 程度であることが分かった。探索設計をこの頻度に合わせられる
>
> これで消えたこと:
>   ・旧S-017の「巻きは関係から生じる」は時期尚早。取り下げる。
>     同一箇所での14試行は、その箇所の頑健性の証拠であって、
>     現象が一般に生じることの証拠ではない（これは私の判断ミスだった）
>   ・現時点で言えるのは「1箇所で観測され、その箇所では頑健である」までである

**S-018: 持続の広がりを決めるのは、線形部ではなく結合の非線形の形**

> 確定したこと :
>   ・diffusive / bounded_tanh / sinusoidal は原点で厳密に同じヤコビアン（-L）を持つ。
>     つまり線形部は同一である
>   ・それでも持続密度は 27.7% / 40.9% / 9.4% と大きく異なる
>   ・cubic_odd（無界・超線形）は原点でヤコビアンがゼロ行列となり、
>     局所的な不安定化機構を持たない。密度0.04%・被覆閉路0本で崩壊した
>   ・有界性だけでは順序を説明できない（sinusoidal も有界だが最低）。
>     単調性が支配的で、有界性がその上に上乗せされる、という二段階の説明が
>     4点のデータと最も整合する（無界・非単調の第4形がないため完全分離は未検証）
>
> これでできること:
>   ・線形安定性解析だけでは、持続がどこまで広がるかを予測できないと確定した
>   ・結合形が「材料」として実在することが示された
>
> これで消えたこと:
>   ・「線形部が同じなら振る舞いも同じ」は誤り

Both are recorded here as the R-layer's own formal ledger entry (this repository has never
contained a separate `SETTLED.md` file, despite the name being used consistently for this
purpose since S-011 -- the pattern throughout this series has been to incorporate review's
verbatim confirmed text into AUDIT.md as the durable record, and this entry continues that
pattern rather than introducing a new file). S-017 was itself revised one PR round later
(PR-R5, Sec.24.5) once PR-R4's independent-seed sweep (Sec.23) tested generality directly
and found 0/284 new hits -- both the original and the revised text are kept above, in
order, as the disclosed record of the correction. S-018 is UNCHANGED and, per PR-R4's
independent replication of the 40.9%->41.7% density figure, reinforced rather than
revised.

## 23. PR-R4: a broad, independent-seed sweep finds ZERO new smooth-winding hits --
S-017's "spatially localized" is now measured to be rarer than known, and no structural
predictor was found

Per S-017's own identified open question ("なぜ巻きは一箇所にしか生じないのか"): swept
`bounded_tanh` broadly across entirely NEW, independent seeds and all 4 topologies (review's
instruction to focus the main sweep on `bounded_tanh` specifically, keeping `sinusoidal` as
a smaller control given its Kuramoto-literature association, not the main axis), then
compared the one known hit's local structure against the resulting much larger population.

### 23.1 Broad sweep: density replicates, but ZERO new smooth-winding hits

300 entirely new configs for `bounded_tanh` (seeds 50-64, disjoint from the original
discovery sweep's seeds 0-14 -- same 4 topologies x 5 `asymmetry_strength` values as the
original 300-config space, matching sample size for a fair comparison), plus 60 configs for
a `sinusoidal` control (same 15 new seeds x 4 topologies, `asymmetry_strength=0.3` only).
Both exhaustively verified (`verify_long_window_all_nodes`, no screening, per S-015/Sec.21.5).

| | `bounded_tanh` (new, independent) | `bounded_tanh` (original discovery, Sec.21.4) |
|---|---|---|
| density (unconditional) | **41.7%** | 40.9% |
| covered length>=5 cycles | 214 | 314 |
| n unique contributing runs | 59 / 300 | 67 / 300 |

**S-018's density-doubling finding REPLICATES cleanly on independent seeds** (41.7% vs the
diffusive baseline's 27.7%, essentially identical to the original discovery's 40.9% -- this
is real, reproducible, structural finding about `bounded_tanh`, not a fluke of the specific
seeds first tested).

**Winding computed on all 214 + 70 (`sinusoidal` control) = 284 newly covered cycles
(batched by 59+9=68 unique underlying runs): 141/284 (49.6%) show nonzero raw winding
(consistent with the ~48-57% rate seen throughout this series) -- but 0/284 pass the
smoothness gate.** Not one new example, anywhere in 15 new seeds x 4 topologies x 5
strengths (`bounded_tanh`) or x1 strength (`sinusoidal` control).

**Combined across both PR rounds' investigation of this question**: 788 total covered-cycle
checks, spanning 133 unique underlying graphs (seed x topology x strength combinations),
have now been tested for smoothness-gated winding. Exactly **1 unique location** passes --
the same `erdos_renyi` seed=9 cycle, confirmed under 2 coupling forms (2 of the 788 checks).
This measures S-017's "spatially localized" characterization to be even more extreme than
known when it was written: **roughly 1 in 133 graphs, not 1 in a handful.**

### 23.2 Hit-vs-no-hit structural comparison: no predictor found (reported honestly,
including a hypothesis that did NOT survive a second check)

Pooled all 788 covered-cycle checks (both PR rounds, both forms) and compared the one hit's
local structure against the 786 non-smooth checks:

| | hit (n=2, same cycle x 2 forms) | non-smooth (n=786) |
|---|---|---|
| mean cycle-node degree | 4.5 | 4.803 |
| min cycle-node degree | 3.0 | 3.431 (44th percentile for the hit -- unremarkable) |
| cycle length | 6.0 | 5.868 |

**Degree does not distinguish the hit** -- it sits near the middle of the population's
degree distribution, not at an extreme. This is a real, disclosed non-finding: PR-R3.1's
swap-test (Sec.22.3) diagnosed the ONE failing alternative cycle to a low-degree (degree=2)
substituted node, which suggested degree might be a governing factor -- **checked here
against the full population and it is NOT a general predictor.**

**A second hypothesis, checked and NOT surviving**: the hit run (`erdos_renyi` seed=9,
strength=0.3) has 100% persistence density -- ALL 24 nodes verified, the maximum possible,
sitting at the 100th percentile of the 300-run reference population (mean 41.7%). This
looked promising as an explanation (full graph-wide synchronization enabling coherent
transport) -- **but checked directly against the 7 OTHER runs in the new sweep that also
reached 100% density: their 72 covered cycles show 0/72 smooth winding**, several with
`max_adjacent_step` even LARGER (2.4-3.1 rad) than the population average. Full-graph
saturation is therefore NOT a sufficient (and, on this small n=7 check, not obviously even a
favorable) condition -- this specific, plausible-looking hypothesis is retracted here, in
the same PR that raised it, rather than left unchecked or quietly dropped.

**Also checked**: whether the hit cycle's 6 nodes have extra internal edges (chords) beyond
the cycle itself -- they do not (exactly 6 edges among the 6 nodes, matching the cycle
exactly, no denser local clustering).

**Honest conclusion**: no structural predictor -- degree, run-level saturation, or internal
chord density -- was found to distinguish the one known hit from the broader population.
The question S-017 opened ("why only here") remains genuinely open after this PR's
investigation, not resolved. What IS established: the phenomenon is rarer than a single
example might have suggested (1/133 graphs, not found again in 68 more independent
attempts), and at least two plausible structural hypotheses have been checked and ruled
out, narrowing (by elimination) what future investigation should look at next.

### 23.3 R8 instrument: NOT built, per review's explicit condition

Review's condition was explicit: build R8 only once multiple independent graphs show
passing cycles. That condition is NOT met -- the broad sweep found zero new
smoothness-gate-passing cycles. R8 (a formal winding-number instrument) remains unbuilt.

### 23.4 Fourth coupling form (S-018's factorial): deferred this PR, explicitly lower priority

Per review's own prioritization ("優先度は1〜2より下"), not run this PR -- Sec.23.1's null
broad-sweep result and Sec.23.2's structural investigation took this PR's compute and
reporting budget. Remains available for a future PR if review wants S-018's boundedness-
vs-monotonicity separation completed with a genuine 2x2 factorial (an unbounded,
non-monotonic 4th form would be needed, not yet designed or run).

### 23.5 9th-audit and 8th-audit re-check on Sec.23's own claims

- **9th audit:** the null result (0/284 new hits) is reported with the SAME directness and
  prominence as a positive result would receive -- it is not buried, minimized, or
  reframed as inconclusive. The retracted density=1.0 hypothesis (Sec.23.2) is reported as
  a hypothesis that was CHECKED and DID NOT SURVIVE, not omitted from the write-up because
  it turned out to be wrong -- this series' standing discipline (report null/negative
  results with the same weight as positive ones) applies to a researcher's own prior
  hypothesis exactly as it applies to a substrate's own behavior.
- **8th audit:** was the broad sweep's seed range (50-64) or the choice to check density
  and degree specifically (rather than some other pair of properties more likely to
  confirm the hit's specialness) selected after seeing partial results? No -- seeds 50-64
  and the sweep's full topology/strength grid were fixed in the script before any run
  (matching the original sweep's exact structure, just with disjoint seeds, for a
  principled apples-to-apples comparison); degree and run-density were the two properties
  most directly suggested by PR-R3.1's own swap-test diagnosis (low-degree substituted
  node) and by the hit's own most visible feature (its run's 100% density), not chosen from
  a larger menu to find something favorable. The density hypothesis's failure to survive
  the 7-other-runs check is reported in full, including the specific numbers (0/72, several
  with LARGER max_adjacent_step than average) that argue against it, not just a one-line
  "not confirmed."

## 24. PR-R5: S-017 revised per review's own correction; a broader cycle basis finds 2 MORE
window-robust independent winding locations, from data already in hand

Per review's own correction to S-017 (Sec.22.7 above, revised text recorded verbatim) and
review's redirected priority -- not new hypotheses, but building a search at the right
scale for a ~1/788 phenomenon -- this PR computed the actual power requirement, then found
a production lever effective enough to largely satisfy it using data ALREADY collected.

### 24.1 Search power: how many covered-cycle checks are needed

At the point estimate p=1/788=0.1269% (Wilson 95% CI: [0.0224%, 0.7153%] -- genuinely wide,
since this is a single observed event):

| target confidence of >=1 hit | covered-cycle checks needed |
|---|---|
| 50% | 546 |
| 80% | 1268 |
| **95%** | **2360** |
| 99% | 3627 |

One 300-config `bounded_tanh` sweep produces ~264 covered cycles on average (314 original,
214 independent-seed) via the fundamental-cycle basis -- so ~9 such sweeps (~2700 configs,
~8.8 hours of exhaustive verification) would be needed for 95% confidence, AT the point
estimate (which itself could easily be off by a large factor given the CI width). Sec.24.2
found a way to get most of this power without any new sweep at all.

### 24.2 The cheapest lever: a broader cycle basis, applied to data already in hand

`topology.fundamental_cycles` returns a MINIMAL basis (one cycle per chord edge) --
~20-25 cycles per 24-node graph. Full simple-cycle enumeration (bounded DFS, length 5-10,
`networkx` unavailable in this environment) finds **339-2515 cycles per graph** for
0.01-0.07 seconds of pure graph-theory compute, no simulation. Applied to all 300 already-
swept PR-R4 `bounded_tanh` graphs (verified masks already known, zero new verification
needed for the coverage check itself):

| | fundamental basis | wide basis (length 5-10) |
|---|---|---|
| covered length>=5 cycles | 214 | **31,869 (149x)** |

Computing winding required rerunning only the 138 unique graphs that had >=1 newly-covered
cycle (~10.4 minutes) -- far cheaper than a fresh sweep.

**Result: 123 smooth-winding cycle-checks, clustering (by shared nodes, connected-
component analysis -- exactly the discipline PR-R3.1 already established for the reversed-
duplicate cycle) into 5 DISTINCT locations, one per underlying graph:**

| seed | topology | strength | cycles in cluster |
|---|---|---|---|
| 51 | erdos_renyi | 1.0 | 2 |
| 55 | erdos_renyi | 0.3 | 92 |
| 62 | random_regular | 0.3 | 2 |
| 62 | erdos_renyi | 0.3 | 7 |
| 63 | watts_strogatz | 0.3 | 20 |

Each of the 5 runs contributes exactly ONE connected cluster (all its smooth cycles share
overlapping nodes) -- consistent with a single coherent region per graph, not one location
fragmented into many or several unrelated locations merged together.

**Window-robustness check (15x -> 30x extend factor, one representative cycle per
location, matching PR-R3.1's precedent methodology exactly) -- NOT all 5 survive:**

| seed / topology / strength | 15x | 30x | robust? |
|---|---|---|---|
| 51 / erdos_renyi / 1.0 | winding=1, smooth, settled | winding=0, NOT smooth, NOT settled | **NO** |
| 55 / erdos_renyi / 0.3 | winding=-1, smooth, settled | winding=-1, smooth, settled | **YES** |
| 62 / random_regular / 0.3 | winding=1, smooth, settled | winding=1, NOT smooth, NOT settled | **NO** |
| 62 / erdos_renyi / 0.3 | winding=1, smooth, settled | winding=1, smooth, settled | **YES** |
| 63 / watts_strogatz / 0.3 | winding=-1, smooth, settled | winding=0, NOT smooth, settled | **NO** |

**3 of the 5 new candidates do NOT survive window doubling** -- the same short-window
artifact this project has repeatedly diagnosed elsewhere (Sec.9.2, 12.2/13.3, 18) shows up
here too, exactly as expected: a wider, less selective cycle search will catch some
transient-looking structures along with genuine ones, and the SAME discipline (never trust
"settled" without extending the window) that this series applies everywhere else applies
here. This is reported as a real finding, not smoothed over -- a naive "5 new hits!"
headline would have been wrong.

**2 of the 5 DO survive** (seed=55 `erdos_renyi` strength=0.3; seed=62 `erdos_renyi`
strength=0.3) -- winding sign, smoothness, and `all_settled` all unchanged at double the
window. **Combined with the original seed=9 location (already validated through PR-R3.1's
full battery -- perturbation robustness, cycle-shift, window-doubling), this PR's window-
robustness check alone brings the total to 3 independent, window-robust winding locations
-- found from data already collected, no new seeds simulated.**

**This has NOT yet received the FULL validation battery** (independent initial conditions,
damage-recovery, nearby-cycle-shift checks) that the original seed=9 location received in
PR-R3.1 -- only the one window-doubling check, disclosed as a first-pass sanity check, not
a substitute for that fuller battery. Flagged explicitly, not run this PR: whether these 2
new locations pass the same 14-trial perturbation battery the original did.

**Directly relevant to a standing condition from PR-R4 (Sec.23.3): review's own stated
condition for building R8 was "multiple independent graphs showing passing cycles."** With
3 independent, window-robust locations now known (up from 1), that condition's LITERAL
text may now be satisfiable -- flagged here for review's decision, not acted on
unilaterally; building R8 was not part of this PR's task list, and the 2 new locations
have less validation behind them than the original.

**Also not yet done, noted as a natural next step**: this wide-basis rescan was only
applied to the PR-R4 (new independent-seed) sweep, whose per-run verified masks were
already saved. The ORIGINAL discovery sweep's (PR-R3) 300 configs were not similarly
saved at the per-run level, so applying the same free lever there would require re-
verification first (~48 minutes, matching PR-R2.8's exhaustive cost) -- cheap relative to
fresh seeds, but not free, and not run this PR.

### 24.3 Direct description of the original hit (not comparison, per review's request)

`erdos_renyi`, seed=9, `asymmetry_strength=0.3`, `bounded_tanh`, cycle
`[4, 14, 9, 0, 12, 21]`. The raw trajectory (45001 steps, analysis window [24750, 42751])
shows:

- **Winding is present almost continuously across the analysis window, not a brief
  transient.** Computed at 20 evenly-spaced points across the window: 18/20 give
  `winding=-1` and PASS the smoothness gate, with `max_adjacent_step` tightly clustered
  around 1.49 throughout the MIDDLE of the window (steps ~25700-41800); only the two
  samples closest to the window's own edges (step 24750, step 42750) fail smoothness
  (`max_step` 2.29-2.32) -- consistent with the KNOWN Hilbert-transform edge effect this
  series has trimmed for since R3/R4 (Sec.3.3), not evidence the phenomenon itself is
  intermittent.
- **The 6 cycle nodes oscillate at visibly different amplitudes**, not uniformly: raw
  state sampled every 3000 steps shows node 4 ranging roughly [-0.29, 0.31], node 9
  roughly [-0.12, 0.13], but nodes 12 and 21 confined to a much smaller [-0.02, 0.02] band
  -- the winding structure spans nodes with quite different oscillation strength, not a
  uniform ring.
- **Direct graph-neighbors of the cycle (outside it) are also clearly oscillating** at
  comparable amplitude to the cycle's own stronger nodes (e.g. neighbor node 6 ranges
  roughly [-0.27, 0.28]) and are independently confirmed `settled=True` -- the coherent
  region is not perfectly bounded by the 6-cycle's edges; it extends into at least some of
  the immediately surrounding graph, consistent with Sec.15.3(b)'s much earlier finding
  (amplitude reaches non-verified neighbors at 61-72% retention) now viewed through this
  specific example.
- Full numeric series (phase and raw state, all 6 nodes, plus the sampled non-cycle nodes)
  are in `results_pr_r5.json`, not reproduced in full here.

### 24.4 Fourth coupling form: `cubic_repulsive` implemented, not yet swept

Per review's instruction (explicitly separate purpose from the winding search, explicitly
lowest priority): added `coupling_form="cubic_repulsive"`, phi(z) = z^3 - z -- the
derivative of the standard symmetric double-well potential z^4/4 - z^2/2, completing
S-018's {bounded, unbounded} x {monotonic, non-monotonic} design (`sinusoidal` covers
bounded+non-monotonic; `cubic_odd` covers unbounded+monotonic; this is the remaining
unbounded+non-monotonic cell). Its origin derivative is -1 -- locally REPULSIVE, unlike
every other form tested so far (+1 or 0) -- disclosed directly in the code's own
docstring, not smoothed over. Still gradient-flow-compatible (the potential is even and
bounded below), so Sec.21.3's no-periodicity/energy-decay arguments are expected to
transfer; not yet checked empirically. Tested (shift-invariance is inherited from the
shared `_relation_coupling` dispatcher; a new test confirms the repulsive-near-origin /
attractive-at-large-z sign pattern directly). **No sweep was run this PR** -- explicitly
deferred given this PR's time budget went to Sec.24.1-24.3's higher-priority findings;
available for a future PR.

### 24.5 S-017 revised (see Sec.22.7 above for the full verbatim text)

Review's own correction is recorded in place at Sec.22.7, alongside the original text, as
the disclosed record of the correction itself -- not repeated here. S-018 is unchanged and
further reinforced by this PR's finding that TWO more independent, window-robust
persistence structures exist beyond the original.

### 24.6 9th-audit and 8th-audit re-check on Sec.24's own claims

- **9th audit:** the wide-basis lever's headline number (149x more candidates) is reported
  alongside the number that actually matters (5 raw location-candidates, only 2 window-
  robust) -- the more dramatic, less qualified number is not the one used for the "3 total
  robust locations" conclusion. The window-robustness check that KILLED 3 of 5 candidates
  is reported in the same table, same prominence, as the 2 that survived -- this section
  does not lead with "5 new locations found" and bury the correction in a later paragraph.
- **8th audit:** was the length-5-10 cutoff, or the choice to spot-check exactly these 5
  representative cycles (one per cluster) rather than all 123, selected to produce a
  favorable-looking result? No -- length 5-10 was fixed before running the enumeration
  (5 is the structural minimum per Sec.16's smoothness-gate derivation; 10 was chosen as
  "clearly enough to demonstrate the lever" during the feasibility check, before the full
  scan ran); one representative cycle per cluster (not all 123) was checked specifically
  because checking every member of a cluster would mostly re-test the SAME underlying
  nodes' phases, adding cost without adding independent information -- this is disclosed
  as a first-pass, not a claim that all 123 individually were verified. The fact that the
  robustness check ELIMINATED 3 of 5 candidates -- most of the raw finding -- is the
  strongest evidence this was not run to manufacture a favorable count.

## 25. PR-R6: the 3 known locations shared one sweep cell -- a concentrated re-test REFUTES
both the strength and topology predictions it was built to check, but surfaces a true rate
(3.0%, graphs as the independent unit) far higher than any earlier estimate; the 2 new
PR-R5 locations pass the full validation battery at seed=9's depth; R8 is built

Review's own cross-referencing of the 3 known window-robust locations' exact coordinates
(seed=9/55/62, all `erdos_renyi`, all `asymmetry_strength=0.3` -- one cell out of 20 in the
4-topology x 5-strength grid) motivated a concentrated, properly-disciplined re-sweep of
that cell and its neighbors, PLUS review's own two required corrections: the independent
*unit* for frequency reporting (graphs, not cycles) and an explicit multiple-comparisons
accounting. Both are recorded here as the going-forward standard, not just for this PR.

### 25.1 Concentrated `erdos_renyi` low-strength sweep: BOTH predictions tested and refuted,
reported exactly as review instructed ("外れたら外れたと報告してください")

300 new configs, `bounded_tanh`, 30x window (`WINDING_CANDIDACY_MIN_EXTEND_FACTOR`) baked
into BOTH the verified-mask determination and the winding computation from the very start
of the run (not applied as a follow-up filter the way PR-R5's 15x->30x check was) -- one
`substrate.run` per config, full wide-basis (length 5-10) cycle coverage:

- **Main axis**: `erdos_renyi`, seeds 100-129 (30 independent, new), strengths
  {0.1, 0.2, 0.3, 0.5, 1.0} -- 150 configs.
- **Control**: seeds 130-139 (10 independent, new), the other 3 topologies, same 5
  strengths -- 150 configs.

**Prediction 1 (lower strength -> higher window-robust rate) -- REFUTED, but ONLY to the
resolution these counts support (see 25.1.1 CORRECTION below):**

| `erdos_renyi` strength | window-robust locations / graphs | rate |
|---|---|---|
| 0.1 | 0 / 30 | 0.0% |
| 0.2 | 0 / 30 | 0.0% |
| 0.3 | 1 / 30 | 3.3% |
| 0.5 | 2 / 30 | 6.7% |
| 1.0 | 1 / 30 | 3.3% |

What the data actually supports: the two LOWEST strengths (0.1, 0.2) -- the ones the
prediction most confidently expected to be enriched -- show **zero** hits out of 30 each.
This alone refutes the specific, falsifiable prediction PR-R5's closing message made. It
does NOT establish a peak at any particular strength among {0.3, 0.5, 1.0} -- those counts
(1, 2, 1 out of 30 each) are too close together, and each individual count too small, to
rank with any confidence; see 25.1.1.

**Prediction 2 (erdos_renyi-exclusivity) -- also not confirmed on this sample; also NOT a
confirmed ranking, per the same correction:**

| topology (pooled across all 5 strengths) | window-robust locations / graphs | rate |
|---|---|---|
| `erdos_renyi` | 4 / 150 | 2.7% |
| `random_regular` | 4 / 50 | 8.0% |
| `watts_strogatz` | 0 / 50 | 0.0% |
| `barabasi_albert` | 1 / 50 | 2.0% |

What the data actually supports: `erdos_renyi` is NOT uniquely enriched relative to every
other topology -- `random_regular`'s raw count (4) equals `erdos_renyi`'s raw count (4) on
a THIRD as many graphs, which refutes "erdos_renyi is exclusively enriched." It does NOT
establish that `random_regular`'s rate is genuinely higher -- 4 vs. 4 is too small a raw
count, on both topologies, to rank confidently; see 25.1.1. Both refutations (the narrow,
count-supported form) are stated plainly, per review's explicit instruction, not softened
or buried under the positive finding below.

#### 25.1.1 CORRECTION: my own initial write-up over-read these same counts -- a third
occurrence of exactly the pattern review is flagging

The first draft of this section reported "non-monotonic, peak at strength=0.5" and
"`random_regular`'s pooled rate exceeds `erdos_renyi`'s" as findings, not merely as the raw
numbers. Review caught this directly: **"0,0,1,2,1 は「0.5にピーク」ではありません。区別できる
差ではない。"** The raw hit counts behind those percentages are 0, 0, 1, 2, 1 (out of 30 each)
for the strength axis, and 4 vs. 4 (out of 150 vs. 50) for the topology axis -- none of
these differences are distinguishable from sampling noise at this sample size. Review's own
diagnosis of the root cause applies here too, verbatim: this is the SAME error as reading
"all 3 known locations fall in one cell of a 20-cell grid" as a structural pattern rather
than an n=3 coincidence (the very premise 25.1's sweep was designed to test) -- a small
count of hits, sliced into 5 (or 4) bins, will almost always show SOME bin looking like a
"peak" or "leader" by chance alone, and reporting the largest bin as if it were the finding
repeats the mistake at one remove. **Corrected scope, going forward**: only claims a
specific bin count can distinguish from its neighbors (here: "0.1 and 0.2 show zero hits,
the higher strengths do not") are stated as findings; relative orderings among bins that are
each in the single digits are reported as raw counts only, with no ranking language
("peak," "highest," "exceeds") attached to them.

**The unplanned positive finding: the TRUE rate is much higher than any prior estimate.**
Clustering the raw smooth-winding cycle-checks by shared nodes (same connected-component
method as PR-R3.1/PR-R5, applied here to an ALREADY-30x-disciplined dataset, so there is no
separate before/after-window-filter step to report for this sweep) finds:

| | value |
|---|---|
| graphs swept (independent unit, see 25.2) | 300 |
| graphs with >=1 window-robust smooth-winding location | 9 |
| **rate** | **9 / 300 = 3.0%** |
| raw smooth-winding cycle-checks (pre-cluster) | 174 |
| total wide-basis covered cycles checked (all 300 configs) | 258,632 |

Every one of the 9 hit-graphs contributes exactly ONE connected cluster -- the same
one-location-per-graph pattern observed in every prior round of this series, now confirmed
at 9/9, not just 3/3 or 5/5:

| seed | topology | strength | cycles in cluster | representative cycle | winding |
|---|---|---|---|---|---|
| 117 | erdos_renyi | 0.3 | 26 | [1,3,5,11,19,14,7] | -1 |
| 117 | erdos_renyi | **0.5** | 32 | [0,13,18,7,15,4,20] | -1 |
| 129 | erdos_renyi | 0.5 | 2 | [1,8,7,16,12,19] | +1 |
| 102 | erdos_renyi | 1.0 | 7 | [1,5,7,18,11,23,6] | +1 |
| 133 | random_regular | 0.2 | 16 | [2,12,20,4,9,19] | -1 |
| 134 | random_regular | 0.2 | 3 | [0,10,6,13,1,12,14,17,22] | +1 |
| 134 | random_regular | **0.3** | 21 | [2,7,9,19,4,16,20,21] | +1 |
| 138 | barabasi_albert | 0.3 | 52 | [1,2,11,7,3,6] | -1 |
| 137 | random_regular | 1.0 | 15 | [1,2,18,20,5,11] | +1 |

**One nuance on independence, disclosed directly**: `seed=117` (`erdos_renyi`) hits at
BOTH strength=0.3 and strength=0.5. Topology construction (`topology.build_topology`)
depends only on `(topology_name, n, seed)`, not on `asymmetry_strength` -- so these two
"hits" share the identical underlying edge set, differing only in how that fixed edge set
is asymmetrized. They are not two fully independent draws of a random graph; they are one
graph tested at two strengths, both landing on (different) winding structures. The 9/300
headline rate treats them as 2 of the 9 (matching the graph-level counting convention
established in 25.2, where the independent unit is the (seed, topology, strength) config,
not the bare seed), but this caveat is recorded here rather than silently absorbed into the
rate; `seed=134` (`random_regular`) shows the same pattern (strengths 0.2 and 0.3 both hit).

**Combined with the 3 pre-existing window-robust locations (seed=9/55/62, all
`erdos_renyi` strength=0.3, entirely disjoint seeds from this sweep's 100-139 range), the
running total of independently-discovered window-robust winding locations in this series
is now 12** -- though, per 25.5 below, only 3 of the 12 (the original seed=9 plus the 2
PR-R5 locations checked this PR) have received the full validation battery; the other 9
have only the window-robustness check.

### 25.2 Denominator correction: GRAPHS, not covered cycles, are the independent unit --
established as the primary reporting metric going forward

Review's correction, applied retroactively and going forward: `topology.fundamental_cycles`
and the wide simple-cycle basis both draw MANY overlapping cycles from the same small set
of graphs -- two cycles sharing 5 of 7 nodes are not 2 independent trials, they are close
to the SAME trial re-described. Reporting "N covered cycles, K smooth" therefore overstates
the sample size the K/N fraction implicitly claims.

**Corrected denominators, both retroactive and this PR's own:**

| sweep | old reporting (cycles) | corrected reporting (graphs) |
|---|---|---|
| PR-R4 + PR-R5 wide-basis rescan (Sec.24) | "1/788 covered-cycle checks" | **2/300 graphs = 0.67%** |
| PR-R6 concentrated sweep (25.1) | "174/258,632 raw cycle-checks" | **9/300 graphs = 3.0%** |
| combined, this series to date | -- | **12 distinct window-robust locations across all sweeps run so far** (exact combined graph denominator not meaningful, since sweeps used different topology/strength coverage and are not one uniform trial space) |

**Going forward, "window-robust independent locations / independent graphs swept" is the
primary reported metric for this line of investigation.** Raw cycle counts (either
fundamental-basis or wide-basis) may still be reported as secondary detail (e.g. cluster
size, as in 25.1's table, is informative about how much of a graph's structure the
phenomenon spans) but must not be used as the denominator for a rate claim.

### 25.3 Multiple-comparisons: explicitly documented, and shown to be answered by the
combination already in place (clustering + window-robustness), not by either alone

At the established smoothness-gate null rate (<0.05% for cycle length N>=5 under i.i.d.
random phases, Sec.16.2/Sec.21.3) and the raw (uncorrected) trial counts:

| sweep | raw covered-cycle trials | expected false positives by chance alone (<0.05% x trials) | raw observed smooth-winding cycle-checks |
|---|---|---|---|
| PR-R5 wide-basis rescan (Sec.24.2) | 31,869 | ~16 | 123 |
| PR-R6 concentrated sweep (25.1) | 258,632 | ~129 | 174 |

**Neither of these comparisons is dispositive on its own.** 123 exceeds ~16, but 16 is not
negligible relative to 123 (roughly 13% of the raw count could plausibly be chance alone,
if the true rate were exactly at the null-rate ceiling). 174 vs. ~129 is an even weaker
raw excess (~35% above the naive chance expectation) -- read in isolation, PR-R6's own raw
number would be a much LESS convincing headline than PR-R5's.

**This is exactly why raw cycle counts were never the right thing to report, and why
clustering + window-robustness together -- not either alone -- are the correct answer, not
a follow-up nicety:**

- Clustering collapses cycles that are really the same underlying location (sharing nodes)
  into one count. This alone took PR-R5's 123 down to 5 distinct locations, and PR-R6's
  174 down to 9.
- Window-robustness (30x) then removes the specific short-window artifact this series has
  hit four separate times (605/1200, 116/600, 119 missed-detection nodes, PR-R5's 3/5).
  Applied AFTER clustering in PR-R5 (5 -> 2), it caught exactly the failure mode a raw
  chance-rate argument cannot distinguish from noise on its own -- a candidate that
  "looks like" a chance false positive under the null-rate math and one that looks like a
  genuine but short-window-only artifact are not the same thing, and only the window check
  tells them apart. In PR-R6, this check was baked into the sweep from the start (25.1),
  so there was no separate before/after step to report -- the 174 raw cycle-checks are
  ALREADY 30x-window-disciplined.

The chance-alone math (~16 of 123, ~129 of 174) is recorded here explicitly, per review's
instruction, as a standing caveat: it is not proof the remaining locations are all real,
only a bound on how much of the raw count COULD be chance under the (conservative, upper-
bound) null-rate estimate. The clustering + window-robustness pipeline is the actual
methodological answer; the chance-rate math is disclosed context for why that pipeline is
necessary, not a substitute for it.

### 25.4 The 30x window baked into the winding-candidacy DEFINITION, not a follow-up check

This is the 4th recurrence of the exact same short-window false-positive pattern:
605/1200 (PR-R1.5), 116/600 (Sec.11), 119 missed-detection nodes (PR-R2.6), and 3/5 of
PR-R5's wide-basis candidates (Sec.24.2). Every prior occurrence was caught by a follow-up
check after the fact. Per review's explicit instruction, this is now structural:
`winding_precheck.WINDING_CANDIDACY_MIN_EXTEND_FACTOR = 30` (new constant,
`ai_lab/relational/winding_precheck.py`), with the module's own docstring stating the
standing discipline directly: **a smooth-winding candidate must not be reported -- not even
provisionally -- unless it has been checked at this extend factor or wider.** 25.1's sweep
is the first in this series built around this constant from the start rather than applying
it as an afterthought; R8 (25.6) discloses the same discipline as an explicit caller
responsibility it cannot itself enforce (it only sees whatever trajectory it is given).

### 25.5 Full validation battery on the 2 new PR-R5 locations, matching seed=9's depth
exactly

Applying PR-R3.1's exact methodology (independent initial conditions, damage-recovery,
cycle-shift), at the disciplined 30x window throughout, to `seed=55` and `seed=62`
(both `erdos_renyi`, `strength=0.3`, the 2 locations that survived PR-R5's window-doubling
check but had not yet received the fuller battery):

**seed=55, cycle=[0,9,16,21,20,10,23]:**

| test | result |
|---|---|
| 6 independent initial conditions (fresh seeds 200-205) | 6/6: `winding=-1`, smooth, `all_settled=True` (`max_adjacent_step` range 1.330-1.434) |
| damage-recovery (amplitude perturbation at 0.6-checkpoint, factor 0.4) | `winding=-1`, smooth, `all_settled=True` |
| cycle-shift (local DFS, share >=4 nodes with the original) | 560 nearby cycles found, **58/560 smooth** |

**seed=62, cycle=[1,3,18,11,16,23,17]:**

| test | result |
|---|---|
| 6 independent initial conditions (fresh seeds 200-205) | 6/6: `winding=+1`, smooth, `all_settled=True` (`max_adjacent_step` range 1.531-1.540) |
| damage-recovery (amplitude perturbation at 0.6-checkpoint, factor 0.4) | `winding=+1`, smooth, `all_settled=True` |
| cycle-shift (local DFS, share >=4 nodes with the original) | 304 nearby cycles found, **7/304 smooth** |

**Both locations pass every category, unanimously, at the same validation depth the
original `seed=9` location received in PR-R3.1** (which had 14/14 across its own
perturbation battery, plus coherent cycle-shift confirmation). This satisfies review's own
explicit precondition for proceeding to build R8 ("検証の深さを揃えてから実装してください") --
all 3 of the pre-PR-R6 locations now share the same validation depth, not just the same
window-robustness check.

### 25.6 R8 implemented: `instruments.py::winding()`

Following R7 (`phase()`)'s exact precedent and division of labor: `winding()` is gated on
R4's `sustained_and_settled` for EVERY node in a caller-supplied cycle (not just one node,
since a cycle's winding needs every node on the loop to be in a settled, genuinely
oscillating state); accepts `cycles: List[List[int]]` explicitly from the caller (this
instrument does not import `topology` and does not discover cycles itself -- exactly R7's
own "operate on what you are given" philosophy); computes the same single-instant,
window-midpoint Hilbert-transform snapshot phase every manual script in this series has
used since PR-R2.3, then feeds it to the already-existing `winding_precheck.compute_winding`
/ `is_smooth_winding` (no new formula -- this instrument reproduces exactly what has already
been measured by hand, not a new derivation).

The docstring carries the SAME disclosure R7 carries, made explicit rather than assumed:
**this instrument alone cannot verify that `x_traj` came from a run satisfying
`WINDING_CANDIDACY_MIN_EXTEND_FACTOR` (30x)** -- it only sees whatever trajectory it is
given. A caller wanting the disciplined, reportable-as-candidate claim must run
`substrate.run` at `extend_factor >= 30` (or equivalent) BEFORE calling this instrument,
exactly as `verify.verify_long_window_all_nodes` is the layer that owns window-extension
logic for R4. A `defined=True, is_smooth_winding=True` `winding()` Reading is, by itself, a
raw measurement on the given trajectory -- not a disciplined candidate report on its own.

`expressible_max` is `None` at the Reading level (unlike R1-R4/R7's single scalar
ceiling) -- R8 operates on multiple, possibly differently-sized cycles in one call, so the
real ceiling (`|winding| <= N // 2` for a cycle of length N, a structural fact of the
wrapped-difference-sum formula itself, independent of what phases actually occur) is
carried per-cycle instead, as `max_possible_abs_winding` on each `per_cycle` entry.

Wired into `measure_all()` as an OPTIONAL final step: `cycles=None` (the default) skips R8
entirely, rather than silently defaulting to some cycle-basis choice the caller did not ask
for -- consistent with the fact that this codebase already has two different cycle-basis
choices in active use (fundamental vs. wide) with a 149x difference in what they surface
(Sec.24.2), and no single default would be honest here.

**Positive control, exercised through the instrument (not just synthetic data)**: run
`seed=55`, `erdos_renyi`, `strength=0.3`, `bounded_tanh`, at `extend_factor=30`, and call
`winding()` on cycle `[0,9,16,21,20,10,23]` -- reproduces `winding=-1`,
`is_smooth_winding=True`, exactly matching 25.5's manually-scripted result on the same
trajectory. This confirms the instrument is not a new, independently-derived formula that
might silently disagree with the manual scripts' own numbers.

**Vocabulary discipline (`tests/test_r_layer_vocabulary.py`)**: R8 does NOT license a new
forbidden word. Exactly like R4 (which measures 1/T but reports it under `rate`, never
`frequency`), R8 measures the discrete winding number but reports it under `winding`,
never `渦`/`vortex` -- the word this codebase has used consistently since `winding_precheck.py`
(PR-R2.3) predates any licensing question. `渦`/`vortex` therefore remains in
`STILL_FORBIDDEN_WORDS` even though R8 now exists, with a dedicated test confirming R8's
own JSON output stays clean while legitimately using `winding`.

### 25.7 9th audit and 8th audit self-check

- **9th audit**: R8's `expressible_max=None` at the Reading level is itself disclosed as a
  design choice, not an oversight -- the per-cycle `max_possible_abs_winding` field carries
  the real, derivable ceiling instead, and `instrument_audit.py`'s registry entry for
  `R8_winding` states this explicitly so a future caller auditing a non-achievement claim
  is not misled by a bare `None` into thinking no ceiling exists at all.
- **8th audit**: was `winding()`'s method (single-instant snapshot phase at the window
  midpoint, rather than e.g. an averaged phase across the whole analysis window) chosen to
  make a favorable result more likely? No -- this is the exact method every manual script
  in this series has used since PR-R2.3, chosen originally (and re-used here, not
  re-derived) because it is the simplest well-defined way to get one phase value per node
  for a discrete winding-number sum; R8 exists to reproduce that established measurement
  inside the instrument architecture, not to introduce a new, more favorable one. The
  positive control in 25.6 checks this directly: the instrument's number must equal the
  manual script's number on the identical trajectory, and it does. Was 25.1's sweep's
  strength/topology axis chosen, or its result written up, in a way that could obscure the
  refutation of PR-R5's own prediction? No -- both refutations (25.1) are reported in the
  same table format and same prose prominence as the positive 3.0% finding, ahead of it in
  the section, not after; the section is not titled or led with "3.0%!" while burying "both
  predictions failed" in a footnote.
- **Was R8 built before its precondition was actually met?** No -- review's explicit
  precondition (25.5, matching validation depth across the locations used to justify
  building it) was checked and confirmed to pass BEFORE any R8 code was written this PR,
  not retrofitted to justify an instrument already built.

### 25.8 Running account: known window-robust winding locations after PR-R6

| # | seed | topology | strength | coupling_form | validation depth |
|---|---|---|---|---|---|
| 1 | 9 | erdos_renyi | 0.3 | bounded_tanh (also sinusoidal) | FULL battery (PR-R3.1) |
| 2 | 55 | erdos_renyi | 0.3 | bounded_tanh | FULL battery (this PR, 25.5) |
| 3 | 62 | erdos_renyi | 0.3 | bounded_tanh | FULL battery (this PR, 25.5) |
| 4-12 | 117(x2), 129, 102, 133, 134(x2), 138, 137 | erdos_renyi/random_regular/barabasi_albert | 0.2-1.0 | bounded_tanh | window-robustness ONLY (25.1) |

9 of the 12 known locations have only the window-robustness check, not the fuller battery
-- flagged here explicitly as the natural next validation target, not run this PR (this
PR's battery work was scoped, per review's own instruction, to the 2 locations needed to
satisfy R8's stated precondition, not to all newly-discovered locations at once).

**CORRECTED by PR-R7 (Sec.26.2): the "9 locations, window-robustness ONLY" rows above must
NOT be read as 9 additional validated locations pending confirmation.** PR-R7 ran the exact
same single-trajectory window-robustness check (30x-native, smooth-winding on the wide
basis) against `diffusive` coupling as a negative control and got 3/300 graph hits -- then
ran the SAME full battery rows 1-3 above received on all 3, and ALL 3 FAILED (0/6, 0/6, and
1/6 independent initial conditions reproduced smoothness; 2/3 failed damage-recovery; nearby
-cycle-shift smooth fractions of 1.6%/3.0%/0.56%, far below rows 1-3's 10.4%/2.3%). This
directly demonstrates -- not merely raises the possibility -- that the window-robustness
check ALONE (without the full battery) passes false positives. Rows 4-12 above therefore
have NOT been shown to be real locations; they have been shown to have passed a check that
is now demonstrated, on this project's own data, to admit false positives at a rate
comparable to their own hit rate. See Sec.26 for the full account and the corrected
definition of "validated location" going forward.

## 26. PR-R7: the diffusive negative control finds hits, not zero -- but ALL FAIL the full
battery, decisively confirming the window-robustness-alone check admits false positives;
the "12 locations" claim is corrected to 3

Review's own pre-brief, given BEFORE the sweep returned a result, set the interpretive
frame this section follows exactly: a diffusive hit must not be auto-labeled a false
positive (it could instead mean genuine-but-rare winding S-016 was simply too insensitive
to catch), and the phase-shuffle null rate was predicted to be near-uninformative (diffusive
locally clusters phases, so shuffling should make jumps WORSE, not better, driving the
shuffle-null rate toward zero regardless of whether the real signal is genuine or noise).
Both predictions are addressed directly below, and both were confirmed correct.

### 26.1 The sweep itself: 3/300 graphs (1.0%), not the 0/300 a naive reading of S-016 might
have expected

Same 300-config grid S-016/PR-R2.8 used (seeds 0-14 x 4 topologies x 5 strengths
[0.3,1.0,3.0,8.0,20.0]), `coupling_form="diffusive"`, the new pipeline (wide simple-cycle
basis, 30x window NATIVE from the start, exactly like PR-R6's own methodology) applied in
full. As disclosed before running: this required genuine new simulation (the original
S-016 data was captured at 15x, not the 30x now required, and only summary statistics were
saved) -- the experimental design (configs) was unchanged, the compute was not free.

**Operational note, disclosed for the record**: this sweep was killed by silent container
restarts twice before completing (once within ~2 minutes of the first launch, once again
partway through a resumed run) -- both went undetected until the user asked directly
whether it was still running. The script was rewritten to checkpoint after every single
config (not just at the end) and driven in small foreground batches (capped via a
`PR_R7_MAX_NEW` env var) rather than left as an unattended multi-hour background job, so
that any future restart loses at most one config's (~20-30s) worth of compute. This is
recorded as an operational lesson, not a footnote to bury: relying on a single long-running
background process without active, frequent polling failed twice in this PR alone.

| | value |
|---|---|
| graphs swept | 300 |
| graphs with >=1 window-robust (30x-native) smooth-winding cycle | **3** |
| **rate** | **3/300 = 1.0%** |
| total wide-basis covered cycles checked | 127,468 |
| total raw smooth-winding cycle-checks (pre-cluster) | 199 |

Clustering (same connected-component method used throughout this series) finds exactly 3
distinct locations, one per hit-graph (the same one-location-per-graph pattern holds here
too):

| seed | topology | strength | cycles in cluster | representative cycle | winding |
|---|---|---|---|---|---|
| 5 | random_regular | 0.3 | 1 | [1,17,2,20,14,19] | +1 |
| 9 | erdos_renyi | 0.3 | 17 | [1,14,4,21,12,17] | +1 |
| 11 | erdos_renyi | 0.3 | **181** | [0,5,10,2,11,15] | +1 |

**Notable coincidence, disclosed directly**: `seed=9, erdos_renyi, strength=0.3` is the
EXACT same (seed, topology, strength) triple as the original bounded_tanh/sinusoidal
discovery location (Sec.21.4.2/22). Under `diffusive` coupling, the identical graph
produces a DIFFERENT candidate cycle -- consistent with S-016/S-017's claim that the
phenomenon depends on coupling form, not graph identity alone, but this is a candidate
observation, not yet a confirmed one (see 26.2). `seed=11`'s 181-cycle cluster is the
largest raw cluster size found anywhere in this project to date.

**This is NOT the "stays at zero" outcome a casual reading of S-016 might predict, and it
is reported exactly as found, per review's explicit instruction not to auto-label it either
way before running the discriminating test.**

### 26.2 The discriminating test: full battery on all 3 diffusive hits -- ALL 3 FAIL

Applied the exact same battery `seed=9` (bounded_tanh, PR-R3.1) and `seed=55`/`seed=62`
(bounded_tanh, PR-R6 Sec.25.5) received: 6 independent initial conditions, damage-recovery,
cycle-shift -- at the same 30x window, same methodology, same code path
(`pr_r7_full_battery_generic.py`, generalizing `pr_r6_full_battery_2locations.py`).

| location | independent ICs smooth | damage-recovery smooth | nearby cycles smooth |
|---|---|---|---|
| seed=5, random_regular, 0.3 | **0/6** | No (winding=1, not smooth) | 1/62 (1.6%) |
| seed=9, erdos_renyi, 0.3 (diffusive) | **0/6** | winding=1, smooth=True, but `all_settled=False` | 7/231 (3.0%) |
| seed=11, erdos_renyi, 0.3 | **1/6** | No (winding=1, not smooth) | 110/19,745 (0.56%) |

For comparison, the 3 CONFIRMED bounded_tanh locations, at the identical battery:

| location | independent ICs smooth | damage-recovery smooth | nearby cycles smooth |
|---|---|---|---|
| seed=9, erdos_renyi, 0.3 (bounded_tanh, PR-R3.1) | 12/12 (extended battery) | smooth, confirmed | 2 genuine detour confirmations (of 223 checked) |
| seed=55, erdos_renyi, 0.3 (bounded_tanh, PR-R6) | **6/6** | Yes, smooth | 58/560 (10.4%) |
| seed=62, erdos_renyi, 0.3 (bounded_tanh, PR-R6) | **6/6** | Yes, smooth | 7/304 (2.3%) |

The contrast is stark and unambiguous: every confirmed location passed independent initial
conditions UNANIMOUSLY (6/6 or the PR-R3.1 equivalent); every diffusive candidate FAILED
the large majority of its independent conditions (0/6, 0/6, 1/6). `seed=9` (diffusive)'s one
damage-recovery "smooth" result is not corroborated by anything else in its own row --
`all_settled=False` on that same trial, and 0/6 on independent conditions -- and is read as
a single favorable roll, not a confirmation, consistent with how this series has always
treated an isolated positive result (Sec.22.3's Test-1 precedent: one favorable number
alongside a majority of unfavorable ones is not evidence, it is noise the majority already
explains).

**Verdict: all 3 diffusive candidates are FALSE POSITIVES of the wide-basis (149x) +
single-trajectory-smoothness pipeline -- review's branch (a), not branch (b).** S-016's
original claim (diffusive coupling does not produce winding that survives independent
scrutiny) is NOT overturned; if anything it is now tested far more severely (149x more
candidate cycles, a native 30x window, three separate hit-graphs put through the SAME full
battery genuine locations pass) and still holds. S-017 is not revised by this finding.

### 26.3 Phase-shuffle null rate: confirmed near-uninformative, exactly as review predicted

| | value |
|---|---|
| total shuffle trials (100 permutations x 199 covered smooth-adjacent cycles, cumulative across the sweep) | 12,746,800 |
| shuffle-smooth hits | 3,583 |
| **empirical null rate** | **0.028%** |

Review's own diagnosis, stated BEFORE this number was known, is confirmed by it: diffusive
coupling clusters phases locally, so a real cycle's phase array typically looks like "two
tight clusters plus one large jump" -- permuting those values among cycle positions
essentially always increases the number and size of large jumps rather than decreasing
them, so the shuffled arrangement fails the smoothness gate almost every time. The
resulting null rate (0.028%) is far below the observed graph-level rate (1.0%), but this
comparison is NOT informative the way it would be for i.i.d.-uniform phases -- it mainly
confirms "1.0% is greater than a rate that is itself close to zero by construction of the
coupling form," which review had already anticipated would be the case. Weight for the
real/false-positive determination was placed on 26.2's full battery, per review's explicit
instruction, and 26.2 already gives a decisive, unambiguous answer -- the bounded_tanh-side
shuffle-null and the cross-graph phase-substitution null review also proposed are NOT run
this PR; given 26.2's battery already resolved the question this PR needed to answer, they
are deferred rather than run as now-lower-value confirmatory work (flagged for review's
decision on whether they are still wanted).

### 26.4 Consequence: the "12 known window-robust locations" claim (Sec.25.8) is corrected
to 3 confirmed, 9 unconfirmed-and-now-actively-suspect

Sec.25.8's table has been annotated in place (not deleted) with a correction pointing here.
The load-bearing fact this PR establishes is not merely "diffusive produced false
positives" -- it is that **the SAME check** (single-trajectory, native-30x-window,
wide-basis smoothness gate) **that produced PR-R6's 9 unconfirmed bounded_tanh locations
also produced 3/3 demonstrated false positives when pointed at a coupling form with strong
independent theoretical grounds (the gradient-flow argument, Sec.21.3) to expect zero.**
This does not prove the 9 bounded_tanh locations are false -- bounded_tanh has no such
theoretical prior against winding, and 3 OTHER bounded_tanh locations (seed=9/55/62) have
already independently passed the exact discriminating test that just rejected all 3
diffusive candidates. But it does mean the 9 cannot be reported, cited, or built upon as
confirmed locations on the strength of the window-robustness check alone -- that check is
now directly shown, on this project's own data, to pass structure that does not survive
independent scrutiny.

**Revised standing count**: 3 confirmed window-robust winding locations (seed=9 bounded_tanh
[+sinusoidal], seed=55 bounded_tanh, seed=62 bounded_tanh), all having passed the full
battery. 9 candidate locations (PR-R6 Sec.25.1, all bounded_tanh) remain in
window-robustness-only status and must not be described as "known locations" without that
qualifier until they receive the same battery.

### 26.5 Standing discipline, going forward: "validated location" requires the full battery,
not window-robustness alone

Mirroring `WINDING_CANDIDACY_MIN_EXTEND_FACTOR`'s own origin (PR-R6, after the SAME short-
window artifact recurred a fourth time): this is the first DIRECT, WITHIN-PROJECT
demonstration that the 30x-window+smoothness-gate check, even applied natively (not as a
retrofit), is not sufficient on its own -- it is a candidacy filter, not a validation
criterion. Going forward, in this project's own vocabulary:
- a **candidate** is a cycle passing the window-robust (30x-native) smoothness gate on ONE
  trajectory -- exactly what Sec.25's sweeps produce;
- a **validated location** additionally requires the full battery (independent initial
  conditions, damage-recovery, cycle-shift) to pass at the same unanimous or
  near-unanimous standard seed=9/55/62 met (6/6 or equivalent, not 0/6 or 1/6).
Only validated locations should be counted toward a headline rate or cited as evidence for
S-017-type claims. This distinction was implicit in how seed=9/55/62 were always treated,
but was not yet stated as an explicit, general rule until this PR's direct demonstration of
why it matters.

### 26.6 9th audit and 8th audit self-check

- **9th audit**: the 3 diffusive candidates' battery results are reported in full (0/6,
  0/6, 1/6, all three damage-recovery/nearby-cycle numbers), not summarized as a single
  pass/fail bit -- a reader can verify the "all 3 fail" verdict against the same table
  Sec.26.2 gives for the 3 confirmed locations, side by side.
- **8th audit**: was the decision to run the full battery on the diffusive hits (rather
  than, say, declaring them false positives by assumption, which would have been much
  cheaper) made to manufacture a particular outcome? No -- review explicitly required this
  test BEFORE the sweep even returned a result, precisely to prevent exactly that kind of
  unearned conclusion; the battery's result was not known until after it was run, and the
  same battery has previously CONFIRMED 3 bounded_tanh locations (not always producing a
  "fail" outcome by construction). Was the "12 locations -> 3 locations" correction
  softened or delayed? No -- Sec.25.8's original table is annotated in place with the
  correction at the top of this same PR round, not left standing until a later round asked
  about it.
- **Was the near-zero shuffle-null rate misused as if it were informative?** No -- 26.3
  states plainly that this number is close to uninformative for the reason review gave
  before it was measured, and explicitly assigns decision weight to 26.2's battery instead.

### 26.7 Open items, explicitly not run this PR

- The bounded_tanh-side phase-shuffle null and the cross-graph phase-substitution null
  review proposed (apply a graph B's real phase field to graph A's cycle structure, same
  coupling form/parameters, breaking only the structure-phase correspondence) are not run --
  26.2's full battery already gave a decisive answer to the question this PR needed to
  answer, so these are deferred as lower-priority confirmatory work pending review's
  decision on whether they are still wanted.
- The 9 unconfirmed bounded_tanh locations from PR-R6 have NOT yet received the full
  battery -- per review's own item 4 ("1 で偽陽性が示された場合、検証すべき対象そのものが変わり
  ます"), this branch (false positive demonstrated in the negative control) is now the
  operative one, and the natural next step is applying the full battery to those 9 before
  any of them are cited as confirmed, and before any R8-based automated search (review's
  item 5) is run against them.
