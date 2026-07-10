#!/usr/bin/env python3
"""Dimension Transfer Harness (DIMENSION_POLICY.md §2): don't extrapolate a 2D success to 3D.

Before a 2D candidate is promoted to full 3D, this harness MEASURES the 3D-specific risks on the
reference field law (genesis/models):

  A. dimension_risk registry (a-priori for the model class: vortex topology codimension changes 2D->3D,
     out-of-plane escape, vortex reconnection).
  B. THIN 3D SLAB test: take a 2D-ordered state, stack it into a thin slab of nz layers, add a small
     OUT-OF-PLANE perturbation, evolve in 3D, and MEASURE whether structure escapes out of plane
     (z-variance growth), whether the pattern is maintained, and whether new z-modes grow.
  C. a linear proxy: out-of-plane mode growth rate = d/dt log(z-variance).

The harness writes a dimension-transfer.yaml (schemas/dimension-transfer.schema.json). It is a RISK
REPORT, not a pass/fail gate: a high measured out-of-plane growth means "must run full 3D before
claiming a 3D result" (which PR6 does), not "rejected".
"""

import argparse
import json
import os
import sys

import numpy as np
import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import ginzburg_landau as gl  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402


def _order_2d(edge, steps, seed, p):
    rng = np.random.default_rng(seed)
    psi = gl.make_initial((edge, edge), p["noise_amplitude"], rng)
    for t in range(steps):
        psi = gl.step(psi, t * p["dt"], p)
    return psi, rng


def _z_variance(psi3d):
    """Mean over (x,y) of the variance of |psi| ALONG z -- how much structure varies out of plane."""
    amp = np.abs(psi3d)
    return float(np.mean(np.var(amp, axis=2)))


def slab_test(edge=64, nz=10, order_steps=300, slab_steps=200, oop_noise=1e-3, seed=0, quick=False):
    """Stack a 2D-ordered state into a thin nz-slab, perturb out of plane, evolve in 3D, measure escape.

    edge >= 48 is needed so residual vortices survive to be slabbed (a smaller box annihilates them all,
    making the out-of-plane test degenerate). We probe whether those 2D vortices, extended into 3D vortex
    LINES, stay coherent (low z-variance growth) or escape/reconnect out of plane.
    """
    if quick:
        edge, nz, order_steps, slab_steps = 48, 8, 240, 140
    p = dict(gl.DEFAULTS)
    psi2d, rng = _order_2d(edge, order_steps, seed, p)
    # thin slab: replicate the 2D ordered field across z, add a small out-of-plane perturbation
    slab = np.repeat(psi2d[:, :, None], nz, axis=2).astype(np.complex128)
    slab = slab + oop_noise * (rng.standard_normal(slab.shape) + 1j * rng.standard_normal(slab.shape))
    # keep eps at its ordered value (post-quench) so we probe stability, not the quench
    pq = dict(p); pq["quench_duration"] = 0.0
    z0 = _z_variance(slab)
    zt = [z0]
    defect0 = measures.winding_defect_count(slab[:, :, 0])
    for t in range(slab_steps):
        slab = gl.step(slab, 100.0, pq)   # t past quench -> eps = +eps_final
        if t % max(1, slab_steps // 10) == 0:
            zt.append(_z_variance(slab))
    zN = _z_variance(slab)
    defectN = measures.winding_defect_count(slab[:, :, 0])
    growth = float(zN / (z0 + 1e-30))
    # linear proxy: mean per-step log growth of z-variance over the run
    logs = np.log(np.array(zt) + 1e-30)
    oop_rate = float((logs[-1] - logs[0]) / max(1, slab_steps))
    structure_maintained = bool(abs(defectN - defect0) <= max(2, 0.5 * defect0))
    return {
        "edge": edge, "nz": nz, "slab_steps": slab_steps,
        "z_variance_initial": round(z0, 8), "z_variance_final": round(zN, 8),
        "out_of_plane_growth": round(growth, 3), "out_of_plane_log_rate": round(oop_rate, 6),
        "defects_2d_initial": defect0, "defects_2d_final": defectN,
        "structure_maintained": structure_maintained,
        "escaped_out_of_plane": bool(growth > 5.0),
    }


def report(quick=False, seed=0):
    st = slab_test(quick=quick, seed=seed)
    # A. a-priori risk for the complex-GL / vortex model class (topology codimension changes 2D->3D).
    doc = {
        "dimension_risk": {
            "topology_codimension_change": "high",     # 2D point vortex -> 3D vortex LINE
            "inverse_cascade_dependency": False,
            "out_of_plane_escape": "high" if st["escaped_out_of_plane"] else "medium",
            "vortex_reconnection": "high",
            "curvature_instability": "medium",
            "area_vs_volume_conservation_confusion": False,
            "expected_transferability": "medium",
        },
        "two_d_specific_mechanisms": [
            "2D point vortices become 3D vortex LINES (codimension change) -- 2D winding is not a 3D invariant",
        ],
        "linear_analysis": {"out_of_plane_growth_rate": st["out_of_plane_log_rate"]},
        "dimensionless_matched": ["Du/dx^2 (diffusion length)", "quench_duration (correlation length)"],
        "slab_test": {
            "escaped_out_of_plane": st["escaped_out_of_plane"],
            "vortex_cut": bool(st["defects_2d_final"] < st["defects_2d_initial"]),
            "new_unstable_mode": bool(st["out_of_plane_log_rate"] > 0.0),
            "structure_maintained": st["structure_maintained"],
        },
        "status": "audit_passed",
    }
    return doc, st


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dimension Transfer Harness (thin-slab out-of-plane probe)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    doc, st = report(quick=args.quick)
    print("=== Dimension Transfer Harness (2D -> thin 3D slab, out-of-plane probe) ===")
    print("  slab: edge=%s nz=%s steps=%s" % (st["edge"], st["nz"], st["slab_steps"]))
    print("  z-variance: %.3e -> %.3e (growth %.2fx, log-rate %.4g)"
          % (st["z_variance_initial"], st["z_variance_final"], st["out_of_plane_growth"],
             st["out_of_plane_log_rate"]))
    print("  defects(2D slice): %s -> %s ; structure_maintained=%s ; escaped_out_of_plane=%s"
          % (st["defects_2d_initial"], st["defects_2d_final"],
             doc["slab_test"]["structure_maintained"], doc["slab_test"]["escaped_out_of_plane"]))
    print("  RISK: out_of_plane_escape=%s vortex_reconnection=%s expected_transferability=%s"
          % (doc["dimension_risk"]["out_of_plane_escape"], doc["dimension_risk"]["vortex_reconnection"],
             doc["dimension_risk"]["expected_transferability"]))
    print("  => 2D success is a CANDIDATE; full 3D (PR6) is required before any 3D claim.")
    if not args.no_write:
        out = args.out or os.path.join(_REPO, "genesis", "dimension", "_demo_transfer.yaml")
        with open(out, "w") as f:
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
        print("  wrote %s" % os.path.relpath(out, _REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
