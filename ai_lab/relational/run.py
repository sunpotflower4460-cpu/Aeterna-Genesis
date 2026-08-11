#!/usr/bin/env python3
"""ai_lab/relational/run.py -- CLI for the R-layer substrate + first four instruments
(PR-R1 + PR-R1.5 + PR-R1.75 + PR-R1.9).

MODULE:      relational_r1 (ai_lab/relational, PR-R1 + PR-R1.5 + PR-R1.75 + PR-R1.9 addenda)
QUESTION:    Starting from only node indices, a relation graph, and a real-valued per-node
             state (no coordinates, no complex numbers, no phase, no S^1): (a) does pure
             first-order relaxation ("memory off") with a SYMMETRIC relation (w_ij == w_ji)
             genuinely fail to produce sustained reversal (R3) / period (R4)? (b) does
             breaking that symmetry (asymmetry=True, w_ij != w_ji, PR-R1.5) change the
             answer, since the symmetric case's proof no longer applies? (c) when a period
             IS detected (memory=on, or asymmetry=on), is it SUSTAINED oscillation or a
             decaying transient relaxing to a fixed point (PR-R1.5's envelope instrument)?
             (d) does memory=on, symmetric W, ALSO provably fail to sustain for any damping
             gamma>0 (not just fail to be observed), and does the one combination PR-R1.5
             left untested -- memory=on x asymmetry=on -- actually produce sustained
             oscillation, and if so, exactly which analytic condition on L's eigenvalues
             predicts it (PR-R1.75)? (e) of the nodes found "sustained," how many have
             actually SETTLED into a plateaued amplitude rather than still climbing toward it
             (PR-R1.9's stricter envelope check), and do settled nodes cover entire closed
             loops in the relation graph -- R8's (future) precondition (PR-R1.9)? PR-R1
             originally asked only a version of (a)/naive-(b) without the symmetry
             precondition or the sustained/decaying distinction; PR-R1.5 corrected the scope;
             PR-R1.75 supplies the missing proof for (c)'s memory=on side and answers (d);
             PR-R1.9 answers (e) and, per its own result, does NOT proceed to build R8 this
             PR -- see AUDIT.md Sec.9-11.
PUT IN:      node count N; a relation graph G (w_ij >= 0) from a disclosed generator rule
             (random_regular / erdos_renyi / watts_strogatz / barabasi_albert -- never a
             grid by default); real per-node state x_i in R^m (default m=1, no complex
             numbers/angles/phase); the local update rule (Sec.4.2 of the spec: difference-
             only diffusion Sum_j w_ij(x_j - x_i), plus optionally a per-node cubic
             saturation term and/or second-order/inertial dynamics with linear damping, plus
             optionally an explicit sum-conserving projection, difference-only weight
             plasticity, and/or a per-edge magnitude-only asymmetry split (PR-R1.5,
             average-preserving, direction not placed) -- every one of these is an explicit,
             disclosed, switchable ingredient axis, OFF by default); a fixed timestep dt (a
             numerical regulator, not a physical input); a small i.i.d. random initial
             inhomogeneity epsilon (no shape, no pattern, v(0)=0 identically when
             memory=on); a finite node count N. PR-R1.75 adds no new ingredient axis -- it
             only combines the two that already existed (memory=on, asymmetry=on together)
             and adds analysis (proofs, an eigenvalue threshold) of the existing equations.
EMERGED:     (measured) memory=off, W symmetric, produces zero genuine, sustained periods
             across a broad sweep (30 seeds x 4 topologies x 2 saturation settings = 240
             runs x 24 nodes = 5760 node-checks, 0 R4-defined; see AUDIT.md Sec.3.3 for two
             independently-motivated instrument bugfixes found and fixed along the way, not
             hidden). PR-R1.5: memory=off, W asymmetric (360 runs / 8640 node-checks, 3
             asymmetry strengths x 4 topologies x 30 seeds) ALSO produced zero periods.
             PR-R1.75 (Sec.10.2) proves this is not a range-of-strengths artifact: by the
             Gershgorin circle theorem, the graph Laplacian's row-sum construction forces
             every eigenvalue of L to have Re >= 0 for ANY non-negative W, symmetric or
             asymmetric, at ANY strength -- so no finite asymmetry can ever destabilize
             memory=off under this construction; verified numerically out to strengths of
             100 (300 stress-test cases, worst min(Re(eigenvalue)) = -7.8e-14, i.e. zero up
             to floating-point noise). Separately, PR-R1.5's sustained/decaying instrument,
             re-applied to PR-R1's original memory=on sweep (10 seeds x 5 damping values),
             found 0/1200 of the previously-"periodic" node-checks are actually sustained --
             every one is a decaying transient. PR-R1.75 (Sec.10.1) proves this is not an
             artifact either: for memory=on with symmetric W, the mechanical energy
             E = (1/2)|v|^2 + (1/2)x^T L x + (a/4)Sum x_i^4 satisfies dE/dt = -gamma|v|^2 <=
             0 exactly (derived from substrate.py's actual deriv2, not assumed), so by
             LaSalle's invariance principle every trajectory converges to a fixed point --
             sustained oscillation is impossible whenever gamma>0 and W=W^T, matching the
             empirical 0/1200 exactly. PR-R1.75 then measured the one combination left
             untested by PR-R1.5: memory=on x asymmetry=on (damping in {0.0, 0.05}, 4
             topologies, asymmetry strength in {0.3,1.0,3.0,8.0,20.0}, 15 seeds, n=24,
             steps=3000 -- 600 runs / 14400 node-checks). Result: 373/600 runs any period
             defined, and **133/600 runs (708/14400 node-checks) SUSTAINED** -- the
             R-layer's first genuine sustained-oscillation result. Sec.10.3 derives exactly
             why: writing an eigenvalue of L as mu = p + iq (Gershgorin guarantees p >= 0),
             the second-order characteristic equation lambda^2 + gamma*lambda + mu = 0 gives
             Re(lambda) > 0 (linear instability, later capped by the cubic/bounded-degree
             nonlinearity into a limit cycle) exactly when q^2 > p*gamma^2 -- inertia
             converts a Gershgorin-marginal (p~0) rotational mode, which the first-order
             system can only carry forever at constant amplitude, into genuine exponential
             growth. This derived sign was checked against direct eigenvalue computation and
             matched in 11/12 configurations (1 floating-point boundary tie). Net: sustained
             oscillation requires BOTH memory (inertia) AND asymmetry together; neither alone
             produces it in any configuration measured across PR-R1, PR-R1.5, or PR-R1.75,
             and this is now proven, not just unobserved, for both single-ingredient cases.
             PR-R1.9 (AUDIT.md Sec.11) added `settled` -- a trailing-quarter-only envelope
             check, distinct from `sustained`'s whole-window halves check, catching a node
             that is still climbing toward its eventual limit-cycle amplitude but happens to
             average out as "roughly flat" over the whole window. Re-running PR-R1.75's exact
             600-config sweep (same kw+seed, an exact recheck): `any_sustained` reproduced
             133/600 (708/14400 node-checks) identically, but **sustained-AND-settled is
             116/600 runs (396/14400 node-checks)** -- 17 runs' sustained signal was entirely
             still-growing, and 44% of the originally-sustained node-checks were caught
             mid-ramp. The headline is not overturned (a genuine plateaued-oscillation regime
             still exists, memory+asymmetry are still both required) but its true size is
             116/600, not 133/600. Separately, PR-R1.9 measured R8's (future) spatial
             precondition directly: building each settled run's relation graph's
             **fundamental cycle basis** (topology.fundamental_cycles, spanning-tree+chords,
             not an exhaustive simple-cycle enumeration) and checking whether every node on a
             cycle is sustained-and-settled found only **41/2660 (1.5%) of fundamental cycles
             fully covered** -- ~20x the rate an independent-node null predicts (settled
             nodes DO cluster, more than chance), but every fully-covered cycle has length
             <=5 (no long loop was found covered). Per review's own instruction, this PR
             stopped at R7 scope and did NOT build R8 -- 1.5%, concentrated on short local
             loops, is too close to zero to be structurally meaningful yet.
CLAIM TIER:  proven (memory=off, any W built by this construction, any strength: Gershgorin,
             Sec.10.2; memory=on, symmetric W, any gamma>0: energy/Lyapunov + LaSalle,
             Sec.10.1) ; measured (memory=off/symmetric-W: 0/5760, matches the proof exactly;
             memory=off/asymmetric-W: 0/8640, matches the Gershgorin proof exactly;
             memory=on/symmetric-W's ORIGINAL "period found" numbers, now understood to be
             decaying transients: 0/1200 sustained, matches the energy proof exactly;
             memory=on x asymmetry=on: 116/600 runs sustained-AND-settled, PR-R1.9's
             corrected version of PR-R1.75's 133/600, a genuine positive result; 1.5% of
             fundamental cycles fully settled-sustained, ~20x an independence-null baseline
             but concentrated on cycles of length <=5) ; observed (the specific
             period/damping relationship for decaying transients -- no external reference
             value exists) ; interpretive (the q^2 > p*gamma^2 threshold's generality beyond
             the one topology/seed pair it was directly cross-validated against -- 11/12 sign
             matches is supportive, not yet a held-out-sweep confirmation, AUDIT.md Sec.10.5;
             and why the settled regime clusters locally instead of propagating along the
             graph -- open, not attempted, AUDIT.md Sec.11.2).
KNOWN MATCH: N/A -- first measurement of the R-layer. The symmetric-W memory=off/on
             no-period results are qualitatively consistent with the textbook facts that
             gradient flows admit no limit cycles and that damped second-order systems with
             no forcing converge to equilibria; the memory=on x asymmetry=on
             sustained-oscillation mechanism (inertia turning a Gershgorin-marginal complex
             eigenvalue into genuine growth) is a first measurement in this graph-relational
             form, though it is a specific instance of the general dynamical-systems fact
             that adding inertia to a non-normal (non-symmetric) linear operator can
             destabilize modes the first-order operator alone cannot -- not claimed as a new
             mathematical result in general, only newly measured and derived here.
AUDIT (7):   1. Rule names the result?                 No  -- the update rule is Sum_j
                w_ij(x_j-x_i) [+ optional a*g(x_i)] [+ optional -gamma*v]; nothing in it,
                nor the asymmetry construction (a per-edge magnitude-only split, average
                preserved), references "period", "reversal", "sustained", or any
                instrument's output. The q^2 > p*gamma^2 threshold (PR-R1.75) is derived
                algebraically from this same rule's characteristic equation after the fact,
                not built to hit a target ratio.
             2. Faithful/reasonable local dynamics?      Yes -- graph-Laplacian diffusion
                (textbook consensus/heat-equation form) plus, when enabled, a standard
                damped second-order extension, a standard cubic saturation nonlinearity, and
                a standard non-reciprocal-coupling construction (splits each edge's coupling
                asymmetrically while preserving its average); none of these were built or
                tuned to manufacture periodicity. Both PR-R1.75 proofs (Sec.10.1 energy,
                Sec.10.2 Gershgorin) are derived from these same, already-disclosed
                equations -- no new dynamics were introduced to make the proofs work.
             3. Result already in the initial condition? No -- x_i(0) is i.i.d. Gaussian
                noise (scale epsilon only, no shape); v(0)=0 identically for memory=on; the
                asymmetry perturbation chi_ij is drawn from a disjoint RNG stream so it does
                not correlate with x_i(0) for a given seed (verified).
             4. Untargeted companion phenomena appear?   Partial/not fully assessed -- only
                R1-R4 exist, so the fuller phenomenology (R5-R11) cannot be checked yet.
                PR-R1.9 measured, rather than assumed, whether R8's precondition (settled
                nodes spanning entire closed loops) is met: only 1.5% of fundamental cycles
                qualify, so PR-R1.9 deliberately stopped at R7 scope and left R8 unbuilt --
                the load-bearing open item is now R5-R7 (period diversity, phase), plus the
                new question PR-R1.9 raised: why does the settled regime cluster locally
                (20x above chance) instead of propagating along the graph.
             5. Matches reality with real numbers?        Yes for memory=off/symmetric-W --
                0/5760 matching an exact analytic guarantee (Sec.3.1/10.1). Yes for
                memory=off/asymmetric-W -- 0/8640 matching the Gershgorin proof exactly
                (Sec.10.2, not merely "observed" as PR-R1.5 first reported it). Yes for
                memory=on/symmetric-W's decaying-transient numbers -- 0/1200 sustained
                matching the energy/Lyapunov proof exactly (Sec.10.1). "Measured" (not yet
                matched to an independent external formula) for memory=on x asymmetry=on's
                116/600 sustained-AND-settled count (PR-R1.9's correction of PR-R1.75's
                133/600), though the derived q^2>p*gamma^2 sign was cross-checked against
                direct eigenvalue computation (11/12 match). "Measured" for the 1.5%
                fundamental-cycle coverage figure, cross-checked against a pre-specified
                independence-null baseline (predicted 0.077%, observed 20x higher).
             6. Robust to changing IC/parameters?         Yes -- swept 30 seeds x 4
                topologies x 2 saturation settings (memory=off/symmetric, 0/5760), 30 seeds
                x 4 topologies x 3 asymmetry strengths (memory=off/asymmetric, 0/8640,
                PR-R1.5; plus 300 additional stress-test cases at strengths up to 100,
                PR-R1.75), 10 seeds x 5 damping values (memory=on/symmetric, 605/1200
                defined but 0/1200 sustained), (PR-R1.75) 15 seeds x 4 topologies x 5
                asymmetry strengths x 2 damping values (memory=on x asymmetry=on, 373/600
                defined, 133/600 sustained), and (PR-R1.9) the identical 600-config sweep
                rechecked with the settled instrument (116/600 sustained-AND-settled) plus
                2660 fundamental cycles examined across all 4 topologies for the spatial
                coverage figure.
             7. Code asserts or discovers the conclusion? Discovers -- run.py calls
                instruments.measure_all() and reports whatever comes back, including
                `sustained` alongside `defined`, and (PR-R1.9) `settled` and
                `sustained_and_settled` alongside `sustained`, so a caller cannot read
                "period found" as "structure found," nor "sustained by the whole-window
                check" as "actually plateaued," without seeing every verdict explicitly.
                PR-R1.5's correction of PR-R1's own memory=on headline, PR-R1.75's positive
                133/600 sustained result, and PR-R1.9's own downward correction of that
                figure to 116/600 (plus the near-zero 1.5% cycle-coverage finding) were all
                written into AUDIT.md with the same weight as each other -- PR-R1.9
                deliberately did not build R8 despite review's hypothesis being directionally
                right (settled nodes DO cluster above chance), because the measured coverage
                did not support it structurally.
STATUS:      YELLOW. Not RED: three of the four cells now have exact analytic proofs
             (memory=off any-W: Gershgorin, Sec.10.2; memory=on symmetric-W: energy/
             Lyapunov, Sec.10.1) matched exactly by the sweeps (0/5760, 0/8640, 0/1200), the
             fourth cell's positive result (memory=on x asymmetry=on, now 116/600
             sustained-AND-settled after PR-R1.9's correction) has both a derived mechanism
             (q^2>p*gamma^2) and empirical support, and PR-R1.9's own claims (settled
             regression tests, the fundamental-cycle-coverage figure) were checked against
             synthetic positive/negative controls and an independence-null baseline rather
             than asserted. Not GREEN: item 4 is still the binding constraint -- R5-R7 do
             not exist yet to characterize the sustained-and-settled regime, R8 was
             deliberately not built pending a better understanding of WHY the regime
             clusters locally instead of propagating (AUDIT.md Sec.11.2's open question),
             and the q^2>p*gamma^2 threshold's cross-validation (11/12 sign matches) is
             still limited to one topology/seed pair.
A_OR_B:      (B)-leaning, but not (B). Still hand-set: the existence of the node set / the
             relation-graph generation rule / the update rule's functional form / the
             timestep / the initial small inhomogeneity / the finite node count / (PR-R1.5)
             the asymmetry perturbation's distribution (Uniform(-1,1) per edge) when
             asymmetry=True. PR-R1.75 added no new hand-set input -- only proofs and a sweep
             over the existing (memory, asymmetry) combination. PR-R1.9 added one: the
             fundamental-cycle-basis construction (spanning-tree-plus-chords) used to define
             "the graph's cycles" for the R8-precondition check -- a standard, disclosed,
             parameter-free graph-theory choice (AUDIT.md Sec.11.2), not tuned to the
             coverage figure it produced.

CLI only. NOT wired into any hourly loop, multiworld registration, or report pipeline in
this PR (that is PR-R4's scope). --no-record is intended to call
ai_lab.dream.dry_run.activate() per the spec's repo-wide convention; ai_lab/dream/ does not
exist in this checkout (see instrument_audit.py's header for the verification), so this is
currently a documented no-op -- see the try/except below. Regardless of that import's
availability, --no-record always suppresses writing the result to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from ai_lab.relational import instrument_audit, instruments, substrate, topology


def _activate_dry_run_if_available() -> bool:
    """Best-effort call into ai_lab.dream.dry_run.activate(), per repo convention.

    Returns True if the call was made, False if the module isn't present (documented,
    not silently swallowed -- see module docstring above).
    """
    try:
        from ai_lab.dream import dry_run  # type: ignore
    except ImportError:
        print(
            "note: ai_lab.dream.dry_run is not present in this checkout; --no-record still "
            "suppresses writing output to disk, but the repo-wide dry-run registry was not "
            "activated (nothing to activate).",
            file=sys.stderr,
        )
        return False
    dry_run.activate()
    return True


def build_result(args: argparse.Namespace) -> Dict[str, Any]:
    sub = substrate.run(
        n=args.n,
        steps=args.steps,
        dt=args.dt,
        seed=args.seed,
        epsilon=args.epsilon,
        topology=args.topology,
        memory=args.memory,
        saturation=args.saturation,
        saturation_strength=args.saturation_strength,
        conservation=args.conservation,
        plasticity=args.plasticity,
        plasticity_rate=args.plasticity_rate,
        m=args.m,
        damping=args.damping,
        asymmetry=args.asymmetry,
        asymmetry_strength=args.asymmetry_strength,
    )
    # W_final, not W_initial: with plasticity or asymmetry on, this is the coupling the
    # recorded trajectory actually evolved under (W_initial == W_final whenever both are off).
    readings = instruments.measure_all(sub.x_traj, sub.W_final, sub.dt)
    audits = instrument_audit.audit_readings(readings)

    result: Dict[str, Any] = sub.to_dict(include_trajectory=args.include_trajectory)
    result["instruments"] = {name: r.to_dict() for name, r in readings.items()}
    result["instrument_audit"] = {name: v.to_dict() for name, v in audits.items()}
    # 9th-audit machine-checkable flag (spec Sec.8): true iff ANY instrument in this result
    # is instrument-limited for the (absent, in PR-R1) claimed-target check -- CI/tests can
    # grep this key directly.
    result["instrument_limited"] = any(v.instrument_limited for v in audits.values())
    return result


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="R-layer (PR-R1): difference-and-relation substrate + R1-R4 instruments."
    )
    p.add_argument("--n", type=int, default=40, help="node count")
    p.add_argument("--steps", type=int, default=2000, help="integration steps")
    p.add_argument("--dt", type=float, default=0.05, help="timestep (numerical regulator)")
    p.add_argument("--seed", type=int, default=None, help="RNG seed")
    p.add_argument("--epsilon", type=float, default=0.1, help="initial inhomogeneity scale")
    p.add_argument("--topology", choices=topology.AVAILABLE_TOPOLOGIES, default=substrate.DEFAULT_TOPOLOGY)
    p.add_argument("--memory", choices=("off", "on"), default=substrate.DEFAULT_MEMORY)
    p.add_argument("--saturation", choices=("none", "cubic"), default=substrate.DEFAULT_SATURATION)
    p.add_argument("--saturation-strength", type=float, default=0.1)
    p.add_argument("--conservation", action="store_true", default=substrate.DEFAULT_CONSERVATION)
    p.add_argument("--plasticity", action="store_true", default=substrate.DEFAULT_PLASTICITY)
    p.add_argument("--plasticity-rate", type=float, default=0.02)
    p.add_argument("--m", type=int, default=substrate.DEFAULT_M, help="real state dimension per node")
    p.add_argument("--damping", type=float, default=0.08, help="gamma, used only when memory=on")
    p.add_argument("--asymmetry", action="store_true", default=substrate.DEFAULT_ASYMMETRY,
                   help="allow w_ij != w_ji (PR-R1.5); see AUDIT.md Sec.9 for why this changes "
                        "which question memory=off answers")
    p.add_argument("--asymmetry-strength", type=float, default=substrate.DEFAULT_ASYMMETRY_STRENGTH)
    p.add_argument("--include-trajectory", action="store_true",
                   help="include the full x/v trajectory arrays in the JSON output (large)")
    p.add_argument("--output", type=str, default=None, help="write result JSON to this path")
    p.add_argument("--no-record", action="store_true",
                   help="activate the repo-wide dry-run registry (if present) and never write to disk")
    return p


def main(argv: Optional[list] = None) -> int:
    args = _parser().parse_args(argv)
    no_record = args.no_record
    if no_record:
        _activate_dry_run_if_available()

    result = build_result(args)
    text = json.dumps(result, indent=2, sort_keys=True)

    if args.output and not no_record:
        with open(args.output, "w") as f:
            f.write(text)
        print("wrote %s" % args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
