#!/usr/bin/env python3
"""ai_lab/relational/run.py -- CLI for the R-layer substrate + first four instruments (PR-R1).

MODULE:      relational_r1 (ai_lab/relational, PR-R1)
QUESTION:    Starting from only node indices, a relation graph, and a real-valued per-node
             state (no coordinates, no complex numbers, no phase, no S^1), is inertia
             (second-order/"memory" dynamics) the minimum ingredient needed for reversal
             (R3) and period (R4) to appear, while pure first-order relaxation ("memory
             off") genuinely fails to produce them?
PUT IN:      node count N; a relation graph G (w_ij >= 0) from a disclosed generator rule
             (random_regular / erdos_renyi / watts_strogatz / barabasi_albert -- never a
             grid by default); real per-node state x_i in R^m (default m=1, no complex
             numbers/angles/phase); the local update rule (Sec.4.2 of the spec: difference-
             only diffusion Sum_j w_ij(x_j - x_i), plus optionally a per-node cubic
             saturation term and/or second-order/inertial dynamics with linear damping, plus
             optionally an explicit sum-conserving projection and/or difference-only weight
             plasticity -- every one of these is an explicit, disclosed, switchable
             ingredient axis, OFF by default); a fixed timestep dt (a numerical regulator,
             not a physical input); a small i.i.d. random initial inhomogeneity epsilon (no
             shape, no pattern, v(0)=0 identically when memory=on); a finite node count N.
EMERGED:     (measured) memory=off (pure first-order relaxation) produces zero genuine,
             sustained periods across a broad sweep (30 seeds x 4 topologies x 2 saturation
             settings = 240 runs x 24 nodes = 5760 node-checks, 0 R4-defined). An earlier
             instrument version DID show a small number of short-lag false positives (4/5760,
             traced to a multi-modal-transient artifact and a moving-average edge-padding
             bug) before two independently-motivated bugfixes removed them -- see AUDIT.md
             Sec.3.3 for the full investigation, reported rather than hidden. memory=on
             (second-order, damped) produced a defined R4 period in 50/50 swept (seed,
             damping) runs, on 605/1200 (50.4%) of nodes overall. Neither the specific period
             values, the damping dependence, nor the false-positive locations were put in --
             they are measured outputs of instruments.py applied to substrate.py's
             trajectories.
CLAIM TIER:  measured (the memory=off vs memory=on contrast on R3/R4, and the fact that
             memory=off is a provable gradient flow -- see AUDIT.md's Lyapunov argument) ;
             observed (the specific period/damping relationship for memory=on -- no external
             reference value exists to check it against) ; interpretive (framing this as
             "periodicity requires inertia in a difference-only relational system").
KNOWN MATCH: N/A -- first measurement of the R-layer. Qualitatively consistent with the
             textbook dynamical-systems fact that gradient/relaxation flows admit no limit
             cycles (a strictly decreasing Lyapunov function forbids periodic orbits) while
             damped second-order systems generically show decaying oscillatory transients --
             not a new mathematical result, but not previously measured in this graph-
             relational, coordinate-free form in this repository.
AUDIT (7):   1. Rule names the result?                 No  -- the update rule is Sum_j
                w_ij(x_j-x_i) [+ optional a*g(x_i)] [+ optional -gamma*v]; nothing in it
                references "period", "reversal", or any instrument's output.
             2. Faithful/reasonable local dynamics?      Yes -- graph-Laplacian diffusion
                (textbook consensus/heat-equation form) plus, when enabled, a standard
                damped second-order extension and a standard cubic saturation nonlinearity;
                none of these were built or tuned to manufacture periodicity.
             3. Result already in the initial condition? No -- x_i(0) is i.i.d. Gaussian
                noise (scale epsilon only, no shape); v(0)=0 identically for memory=on.
             4. Untargeted companion phenomena appear?   Partial/not fully assessed -- only
                R1-R4 exist in this PR, so the fuller phenomenology (R5-R11: diversity,
                ratio-locking, derived phase, winding, dimension, coherence, history) cannot
                be checked yet. What IS visible: memory=on shows oscillation on most/all
                nodes (not one contrived target node), and topology-dependent period values
                -- an untargeted spread, not a single planted number.
             5. Matches reality with real numbers?        Yes for memory=off -- 0/5760 node-
                checks defined across the full sweep, matching an EXACT analytic guarantee
                (the update is dx/dt = -grad V(x) for V = (1/2) x^T L x + (a/4) Sum x_i^4, a
                provable gradient flow with no limit cycles; see AUDIT.md). Only "observed"
                for memory=on's specific period/damping numbers -- a first measurement with
                no external theory value to check them against.
             6. Robust to changing IC/parameters?         Yes -- swept 30 seeds x 4 topologies
                x 2 saturation settings (memory=off, 240 runs, 0/5760 false positives in the
                final instrument version) and 10 seeds x 5 damping values (memory=on, 50/50
                runs periodic, 605/1200 nodes); an earlier instrument version's small residual
                false-positive rate (4/5760, 0.07%) was investigated and fixed via two
                independently-motivated bugfixes -- see AUDIT.md Sec.3.3.
             7. Code asserts or discovers the conclusion? Discovers -- run.py calls
                instruments.measure_all() and reports whatever comes back. The now-fixed
                false positives were reported and investigated in AUDIT.md rather than
                silently patched over; the fixes themselves were validated on a plain
                monotone-series unit test unrelated to the memory question, and a threshold
                choice validated against memory=off's own known-zero ground truth -- not by
                tuning until the memory=off/on contrast looked better.
STATUS:      YELLOW. Not RED: the core contrast is real, reproducible, and has an exact
             analytic backing for the memory=off side, now matched exactly (0/5760) rather
             than approximately. Not GREEN: item 4 is not fully assessable with only R1-R4
             built, and this is a first PR standing up new instruments (which needed two
             bugfixes during its own test-writing) rather than a robustness-hardened result.
A_OR_B:      (B)-leaning, but not (B). Still hand-set: the existence of the node set / the
             relation-graph generation rule / the update rule's functional form / the
             timestep / the initial small inhomogeneity / the finite node count.

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
    )
    readings = instruments.measure_all(sub.x_traj, sub.W_initial, sub.dt)
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
