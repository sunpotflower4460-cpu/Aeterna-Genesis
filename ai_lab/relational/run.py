#!/usr/bin/env python3
"""ai_lab/relational/run.py -- CLI for the R-layer substrate + first four instruments
(PR-R1 + PR-R1.5 + PR-R1.75 + PR-R1.9 + PR-R2.1).

MODULE:      relational_r1 (ai_lab/relational, PR-R1 through PR-R2.1 addenda)
QUESTION:    Starting from only node indices, a relation graph, and a real-valued per-node
             state (no coordinates, no complex numbers, no phase, no S^1): does repetition
             (R3/R4) emerge, and if so, under exactly which combination of ingredients, with
             what mechanism, and is it a genuine self-sustaining structure or an artifact of
             the observation window? PR-R1 through PR-R1.9 established: memory=off never
             sustains, for any W (Gershgorin, saturation-independent); memory=on with
             symmetric W never sustains, for any damping>0 (energy/Lyapunov, also
             saturation-independent); memory=on x asymmetry=on IS linearly unstable exactly
             when q^2 > p*gamma^2 for some eigenvalue mu=p+iq of the graph Laplacian L
             (Gershgorin guarantees p>=0) -- all of this is PROVEN and UNAFFECTED by what
             follows (AUDIT.md Sec.13.1 separates this explicitly). PR-R2.1 answers the
             question those proofs leave open -- does linear instability actually produce a
             genuine, self-sustaining bounded oscillation, and under which further
             conditions -- and finds: only with an explicit nonlinear cap
             (saturation="cubic"; saturation="none" cannot ever sustain, it is an exactly
             linear ODE that must diverge given any Re(lambda)>0, AUDIT.md Sec.12.2) AND
             linear dissipation (damping>0; damping=0.0's capped oscillation is mostly a
             conservative orbit family, not an attractor, AUDIT.md Sec.13.7) AND a
             re-verification at a much longer window than the one it was first detected in
             (AUDIT.md Sec.13.3 -- the third time this PR series has had to correct a
             short-window false positive, now prevented structurally by
             ai_lab/relational/verify.py rather than caught after the fact each time).
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
             inhomogeneity epsilon (no shape, no pattern, v(0)=0 identically when memory=on);
             a finite node count N. PR-R2.1 adds no new PHYSICS ingredient axis (saturation
             and damping both already existed as axes; PR-R2.1 only re-sweeps a combination
             of existing axes that PR-R1.75/11 had not properly explored) -- it adds two
             TOOLING utilities to substrate.run() (x0_override/v0_override, for continuing a
             trajectory from a checkpoint -- documented in substrate.py as numerical/tooling
             knobs, not disclosed physics inputs, matching how `dt` is already treated) and
             one analysis-only hand-set choice (the fundamental-cycle-basis construction for
             counting "the graph's cycles," AUDIT.md Sec.11.2/13.8, a standard parameter-free
             graph-theory choice, not tuned to any outcome).
EMERGED:     See AUDIT.md Sec.3-11 for the full derivation history (all proofs and negative
             results below are saturation-independent and unaffected by PR-R2.1):
             memory=off, any W (symmetric or asymmetric, any strength): PROVEN zero
             sustained periods (Gershgorin, Sec.10.2), matched by 5760+8640 node-checks.
             memory=on, symmetric W, any damping>0: PROVEN zero sustained periods
             (energy/Lyapunov + LaSalle, Sec.10.1), matched by 0/1200 sustained (the
             original "605/1200 periodic" headline was a decaying-transient artifact,
             corrected in PR-R1.5, Sec.9.2 -- the FIRST instance of the window/artifact
             mistake PR-R2.1's verify.py now prevents structurally).
             memory=on x asymmetry=on: PROVEN linearly unstable exactly when
             q^2 > p*gamma^2 for some eigenvalue of L (Sec.10.3), matching a direct
             eigenvalue cross-check in 11/12 configurations. Whether that instability
             produces a genuine SUSTAINED oscillation depends entirely on what happens next:
             - saturation="none": CANNOT sustain, ever (Sec.12.2) -- an exactly linear ODE,
               no capping mechanism exists. PR-R1.75/PR-R1.9's "133/600" and "116/600"
               positive headlines under this setting are RETRACTED: direct 20x-window
               re-integration confirmed 10/11 spot-checked damping=0.05 flags diverge
               unboundedly (one grows from max|x|=0.2 to 1.6e9); the 11th decays. This is
               the SECOND instance of the window/artifact mistake.
             - saturation="cubic" (PR-R2.1, AUDIT.md Sec.13): genuinely sustains. Re-swept
               the full 600-config grid; screened 363/600 candidates; applying
               `verify.verify_long_window` (a MANDATORY 15x-window re-check, not optional --
               Sec.13.3 documents why this specific window-length-robust form was needed,
               a THIRD near-instance of the same mistake caught before it became a fourth
               retraction) leaves **240/600 runs, 663/1153 node-checks VERIFIED** -- the
               R-layer's first robust positive sustained-oscillation count.
             - damage-recovery (PR-R2.1, `verify.check_attractor_recovery`, AUDIT.md
               Sec.13.4/13.7): perturbing a verified trajectory's entire state by rescaling
               60% of its amplitude away at a checkpoint and checking whether it returns.
               On a disclosed 16-run sample (2 per topology x damping cell): **damping=0.05
               recovers in 8/8 sampled cases (within a few percent); damping=0.0 recovers in
               only 2/8** (the 6 failures sit near 55-60% relative difference -- essentially
               the perturbed amplitude itself, no return at all). This is a genuine
               attracting limit cycle (self-sustaining) only at damping=0.05, matching the
               physical prediction that damping=0.0 lacks the dissipation needed to select a
               unique amplitude rather than a conservative orbit family.
             - cycle-clustering (AUDIT.md Sec.11.2, redone in Sec.13.8 on the corrected
               data): 39/5711 (0.68%) of fundamental cycles are fully covered by
               verified-sustained nodes, ~18.7x an independence-null baseline -- but
               `random_regular` (no hubs) now shows ZERO covered cycles while
               `barabasi_albert`/`erdos_renyi` (degree-heterogeneous) show strong enrichment
               (14.9x/29.7x). This REVERSES the earlier (`saturation="none"`-based)
               conclusion that the clustering was "not a hub artifact" -- that claim is
               retracted; degree heterogeneity may in fact be relevant, though
               `random_regular`'s sample is flagged as statistically underpowered to be
               fully conclusive (Sec.13.8).
CLAIM TIER:  proven (memory=off any-W any-strength: Gershgorin; memory=on symmetric-W any
             damping>0: energy/Lyapunov+LaSalle; memory=on x asymmetry=on linear
             instability threshold q^2>p*gamma^2 -- all saturation-independent, Sec.13.1) ;
             measured+verified+mechanism-confirmed (memory=on x asymmetry=on x
             saturation="cubic" x damping=0.05: 240/600 runs survive 15x-window
             re-verification AND 8/8 sampled cases are interventionally confirmed
             self-sustaining attractors -- the R-layer's first claim at this tier, not just
             "observed") ; retracted (memory=on x asymmetry=on x saturation="none": PR-R1.75/
             PR-R1.9's positive counts were pre-blowup transients, Sec.12.2) ; interpretive
             (whether damping=0.0's capped-but-mostly-non-recovering oscillation is EVER a
             genuine attractor under some other configuration -- only 2/8 sampled, not
             exhaustively ruled out; whether cycle-clustering is genuinely hub-dependent or
             `random_regular` was merely underpowered -- Sec.13.8, open).
KNOWN MATCH: N/A -- first measurement of the R-layer. The linear-regime results
             (Gershgorin, energy/Lyapunov) are qualitatively consistent with textbook
             dynamical-systems facts (gradient/relaxation flows admit no limit cycles;
             damped linear systems with no forcing converge to equilibria). PR-R2.1's
             two-stage structure -- linear instability (inertia+asymmetry) sets the
             oscillation, a nonlinear cap (saturation) sets the amplitude, linear
             dissipation (damping) selects a unique attracting amplitude rather than a
             conservative family -- is the standard shape of a Hopf bifurcation with
             dissipation; not claimed as a new mathematical result, only newly measured and
             derived in this graph-relational form (AUDIT.md Sec.13.1/13.9).
AUDIT (7):   1. Rule names the result?                 No -- the update rule, the asymmetry
                construction, and the saturation/damping terms are all disclosed and fixed
                before any classification; the q^2>p*gamma^2 threshold and the Hopf/
                dissipation framing (Sec.13.1) are both derived algebraically from these same
                equations after the fact, never built to hit a target ratio.
             2. Faithful/reasonable local dynamics?      Yes -- graph-Laplacian diffusion,
                standard second-order extension, standard cubic saturation, standard non-
                reciprocal-coupling construction; PR-R2.1 adds no new dynamics, only sweeps
                an existing axis (saturation) more completely and adds continuation tooling
                (x0_override/v0_override) that replays the SAME equations from a different
                starting state.
             3. Result already in the initial condition? No -- x_i(0) is i.i.d. Gaussian
                noise; v(0)=0 for memory=on; asymmetry's chi_ij is a disjoint RNG stream.
                The damage-recovery checkpoint state (Sec.13.4) is itself GENERATED by the
                same equations (not hand-placed), and the perturbation is a disclosed,
                fixed-factor rescaling, not tuned per case.
             4. Untargeted companion phenomena appear?   Partial -- only R1-R4 exist. PR-R2.1
                narrows the load-bearing gap to R5-R7 (period diversity, phase) against the
                damping=0.05/saturation="cubic"/verify_long_window-confirmed subset
                specifically, and reopens (rather than resolves) the cycle-clustering
                question (Sec.13.8) as a companion phenomenon still under-characterized.
             5. Matches reality with real numbers?        Yes for all three proven cells
                (exact analytic guarantees, matched exactly by their sweeps). For the
                positive saturation="cubic" result: "measured" the 240/600 verified count,
                and independently "confirmed" (not just measured) the damage-recovery split
                via a disclosed sample -- two different lines of evidence agreeing, not one
                number reported twice.
             6. Robust to changing IC/parameters?         Yes -- the full PR-R1 through
                PR-R2.1 sweep history (AUDIT.md Sec.3-13) spans thousands of seed/topology/
                strength/damping/saturation combinations; PR-R2.1 specifically re-swept the
                full 600-config grid under saturation="cubic" and sampled the
                damage-recovery check across all 4 topologies x both damping values.
             7. Code asserts or discovers the conclusion? Discovers -- run.py/verify.py
                report `sustained`, `settled`, `sustained_and_settled`, `verified_sustained`,
                and `achieved` (damage-recovery) as separate, explicit fields; nothing
                upgrades a weaker verdict into a stronger-sounding one. PR-R2.1's own
                retraction of Sec.10.4/11's saturation="none" headline, and its reversal of
                Sec.12.3's "not a hub artifact" claim, were both written into AUDIT.md with
                the same weight as the positive saturation="cubic" finding -- corrections,
                not omissions.
STATUS:      YELLOW, upgraded in substance though not in color: the positive claim is now at
             the "measured, 15x-window-verified, AND interventionally attractor-confirmed"
             tier for the first time in this PR series (damping=0.05, saturation="cubic"),
             rather than "observed." Not GREEN: R5-R7 still do not exist to characterize the
             confirmed regime; the cycle-clustering question was reopened, not closed, by
             the corrected data (Sec.13.8); the damage-recovery sample is n=16, not
             exhaustive; and the q^2>p*gamma^2 cross-validation is still limited to one
             topology/seed pair (Sec.10.5, unchanged by PR-R2.1).
A_OR_B:      (B)-leaning, but not (B). Still hand-set: the existence of the node set / the
             relation-graph generation rule / the update rule's functional form / the
             timestep / the initial small inhomogeneity / the finite node count / the
             asymmetry perturbation's distribution (PR-R1.5) / the fundamental-cycle-basis
             construction (PR-R1.9, unchanged in PR-R2.1) / (PR-R2.1) the damage-recovery
             instrument's fixed constants: `perturb_factor=0.4`, `RECOVERY_TOL=0.20`,
             `checkpoint_frac=0.6`, `LONG_WINDOW_EXTEND_FACTOR=15` (all in verify.py, chosen
             once before sampling, not tuned per result -- Sec.13.10).

CLI only. NOT wired into any hourly loop, multiworld registration, or report pipeline in
this PR (that is a future PR's scope). --no-record is intended to call
ai_lab.dream.dry_run.activate() per the spec's repo-wide convention. NOTE (found while
editing this header for PR-R2.1, not investigated further -- out of this PR's scope):
ai_lab/dream/ now EXISTS in this checkout (including dry_run.py and ceiling_ladder.py),
contradicting PR-R1's original "does not exist" finding (AUDIT.md Sec.0) -- most likely
introduced by a later merge into this branch, not by this PR. The try/except below still
guards the import defensively, so behavior is unaffected either way, but the Sec.8.1
ceiling_ladder.py integration and this --no-record wiring should be revisited in a future
PR now that the module is actually present, rather than assumed absent.
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
