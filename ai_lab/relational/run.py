#!/usr/bin/env python3
"""ai_lab/relational/run.py -- CLI for the R-layer substrate + first four instruments
(PR-R1 + PR-R1.5).

MODULE:      relational_r1 (ai_lab/relational, PR-R1 + PR-R1.5 addendum)
QUESTION:    Starting from only node indices, a relation graph, and a real-valued per-node
             state (no coordinates, no complex numbers, no phase, no S^1): (a) does pure
             first-order relaxation ("memory off") with a SYMMETRIC relation (w_ij == w_ji)
             genuinely fail to produce sustained reversal (R3) / period (R4)? (b) does
             breaking that symmetry (asymmetry=True, w_ij != w_ji, PR-R1.5) change the
             answer, since the symmetric case's proof no longer applies? (c) when a period
             IS detected (memory=on, or asymmetry=on), is it SUSTAINED oscillation or a
             decaying transient relaxing to a fixed point (PR-R1.5's envelope instrument)?
             PR-R1 originally asked only a version of (a)/naive-(b) without the symmetry
             precondition or the sustained/decaying distinction; PR-R1.5 corrected the scope
             -- see AUDIT.md Sec.9.
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
             memory=on); a finite node count N.
EMERGED:     (measured) memory=off, W symmetric, produces zero genuine, sustained periods
             across a broad sweep (30 seeds x 4 topologies x 2 saturation settings = 240
             runs x 24 nodes = 5760 node-checks, 0 R4-defined; see AUDIT.md Sec.3.3 for two
             independently-motivated instrument bugfixes found and fixed along the way, not
             hidden). PR-R1.5: memory=off, W asymmetric (360 runs / 8640 node-checks, 3
             asymmetry strengths x 4 topologies x 30 seeds) ALSO produced zero periods --
             this specific construction did not reproduce the review's non-reciprocity
             hypothesis within the range tried (see AUDIT.md Sec.9.1 for what is and is not
             ruled out by that). Separately, PR-R1.5's new sustained/decaying instrument,
             re-applied to PR-R1's original memory=on sweep (10 seeds x 5 damping values),
             found 0/1200 of the previously-"periodic" node-checks are actually sustained --
             every one is a decaying transient (a damped spiral relaxing to the fixed
             point). The instrument's own positive control (memory=on, damping=0.0, a
             genuinely undamped/conservative run) DOES register sustained oscillation on
             20/24 nodes, confirming the instrument detects sustained periods when they are
             actually present rather than always reporting "decaying." Net: no configuration
             tried so far -- memory=off (symmetric or asymmetric) or memory=on with any
             tested nonzero damping -- has been shown to produce sustained oscillation.
CLAIM TIER:  measured (memory=off/symmetric-W: provable gradient flow, matched empirically
             0/5760; memory=off/asymmetric-W: 0/8640, a genuine negative result within the
             tested range; memory=on's ORIGINAL "period found" numbers, now understood to be
             decaying transients: 0/1200 sustained) ; observed (the specific period/damping
             relationship for memory=on's decaying transients -- no external reference value
             exists) ; interpretive (any framing of "what produces sustained oscillation
             here" -- still open, see AUDIT.md Sec.9.3, NOT concluded to be memory, since
             the one sustained case found is an undamped positive control, not a swept
             result).
KNOWN MATCH: N/A -- first measurement of the R-layer. The symmetric-W memory=off result is
             qualitatively consistent with the textbook dynamical-systems fact that
             gradient/relaxation flows admit no limit cycles (a strictly decreasing
             Lyapunov function forbids periodic orbits); the asymmetric-W and memory=on
             sustained-oscillation questions are first measurements with no established
             external match to check against.
AUDIT (7):   1. Rule names the result?                 No  -- the update rule is Sum_j
                w_ij(x_j-x_i) [+ optional a*g(x_i)] [+ optional -gamma*v]; nothing in it,
                nor the asymmetry construction (a per-edge magnitude-only split, average
                preserved), references "period", "reversal", "sustained", or any
                instrument's output.
             2. Faithful/reasonable local dynamics?      Yes -- graph-Laplacian diffusion
                (textbook consensus/heat-equation form) plus, when enabled, a standard
                damped second-order extension, a standard cubic saturation nonlinearity, and
                a standard non-reciprocal-coupling construction (splits each edge's coupling
                asymmetrically while preserving its average); none of these were built or
                tuned to manufacture periodicity.
             3. Result already in the initial condition? No -- x_i(0) is i.i.d. Gaussian
                noise (scale epsilon only, no shape); v(0)=0 identically for memory=on; the
                asymmetry perturbation chi_ij is drawn from a disjoint RNG stream so it does
                not correlate with x_i(0) for a given seed (verified).
             4. Untargeted companion phenomena appear?   Partial/not fully assessed -- only
                R1-R4 exist, so the fuller phenomenology (R5-R11) cannot be checked yet.
             5. Matches reality with real numbers?        Yes for memory=off/symmetric-W --
                0/5760 node-checks defined, matching an EXACT analytic guarantee (dx/dt =
                -grad V(x), V = (1/2) x^T L x + (a/4) Sum x_i^4, a provable gradient flow
                with no limit cycles, valid only for W=W^T; see AUDIT.md Sec.3.1/9.1).
                "Observed" for memory=off/asymmetric-W (0/8640, no external theory value to
                check it against) and for memory=on's decaying-transient numbers.
             6. Robust to changing IC/parameters?         Yes -- swept 30 seeds x 4
                topologies x 2 saturation settings (memory=off/symmetric, 0/5760), 30 seeds
                x 4 topologies x 3 asymmetry strengths (memory=off/asymmetric, 0/8640,
                PR-R1.5), and 10 seeds x 5 damping values (memory=on, 605/1200 defined but
                0/1200 sustained, PR-R1.5's re-check of PR-R1's own sweep).
             7. Code asserts or discovers the conclusion? Discovers -- run.py calls
                instruments.measure_all() and reports whatever comes back, including
                `sustained` alongside `defined` so a caller cannot read "period found" as
                "structure found" without also seeing the decay verdict. PR-R1.5's
                correction of PR-R1's own memory=on headline was written into AUDIT.md
                rather than quietly revised away.
STATUS:      YELLOW. Not RED: the symmetric-W no-period side has an exact analytic proof,
             matched exactly (0/5760) empirically, and the sustained/decaying instrument is
             validated by both synthetic positive controls and a physical (damping=0)
             positive control. Not GREEN: item 4 is not fully assessable with only R1-R4
             built, PR-R1.5 turned "memory=on produces period" into an open question rather
             than a closed one (605/1200 defined, 0/1200 sustained), and the
             non-reciprocity-produces-oscillation hypothesis is narrowed but not resolved.
A_OR_B:      (B)-leaning, but not (B). Still hand-set: the existence of the node set / the
             relation-graph generation rule / the update rule's functional form / the
             timestep / the initial small inhomogeneity / the finite node count / (PR-R1.5)
             the asymmetry perturbation's distribution (Uniform(-1,1) per edge) when
             asymmetry=True.

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
