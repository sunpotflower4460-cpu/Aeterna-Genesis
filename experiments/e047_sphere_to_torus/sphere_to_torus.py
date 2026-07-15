#!/usr/bin/env python3
"""e047 sphere-to-torus (P06 / F1) -- V0 + V1 ONLY.  role V (validation), NOT emergence.

This is the F1 rung of docs/frontier/F0_P06_sphere_to_torus.md. It does two, and only two, things:

  V0  Confirm the Topology Instrument v1 (genesis/diagnostics/topology_betti.betti3d) reads the material
      VOLUME topology of fixed shapes correctly -- solid ball (b1=0, genus 0), solid torus (b1=1, genus 1),
      double torus (b1=2, genus 2) -- from the SAME diffuse-interface level sets phi>phi_c used in V1, and
      show it is stable to the threshold phi_c and to resolution. We keep the C03 distinction explicit:
      the reported number is the VOLUME first Betti number b1(Omega); the boundary SURFACE genus equals it
      only for a cavity-free handlebody, and surface b1 = 2*genus is a different count.

  V1  Evaluate the FULL nematic droplet free energy on FIXED shapes (the shape phi never moves -- no hole
      opens here) and reproduce the sphere->torus free-energy crossing. Driver: planar-degenerate anchoring
      forces surface defects that a sphere cannot avoid (Poincare-Hopf: tangent index +2 on S^2) but a torus
      can (index 0). Sweeping the elastic/capillary ratio K/(sigma*R), F(torus) crosses below F(ball) at K*.
      Mechanism control (F0 section 5): with anchoring OFF the forced defects vanish and the crossing
      vanishes. Companion: the FULL Q-tensor functional (which lets defect cores melt/escape into 3D) does
      NOT cross at this resolution -- that escape is exactly the ingredient F2's dynamic hole-opening needs
      and V1 does not; we record it honestly.

DISCIPLINE (F0 / AGENTS.md):
- We STOP at F1. No S1/E2 (no dynamic hole, no genus transition). phi is fixed throughout.
- Nondimensionalisation/coefficients/grid/dt are frozen in genesis.models.nematic_qtensor.FROZEN and in
  CONFIG below; --quick only subsamples (coarser grid/fewer steps), never changes the physics constants.
- V0 is V (a measurement-tool check), not E. The fixed-shape energy crossing is V, not "a hole grew".
  We make no interpretive claim ("the difference wanted a hole", life/mind/universe) -- only measured
  Betti/genus and free energies.
- target_encoded = false: F contains no hole/handle/genus term and no target shape; the only anisotropy is
  standard L2 elasticity + planar-degenerate anchoring. The seed director ensemble is shape-blind (identical
  recipe for every shape); the functional, not the seed, selects the lower-energy shape.

CLAIM TIER: measured (Betti/genus, free energies) / established (Koizumi 2307.00632, Lin-Wang 2009.11487).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from genesis.diagnostics import topology_betti as tb          # noqa: E402
from genesis.models import nematic_qtensor as nq              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- frozen run protocol (physics constants live in nq.FROZEN; these set grid/geometry/sweep) ----
CONFIG_FULL = dict(N=36, Rb=8.0, aspect=2.5, steps=450, seeds=(0, 1),
                   Ks=[0.02, 0.08, 0.16, 0.30, 0.45, 0.65], W=nq.FROZEN["W_planar"],
                   phi_cs=[-0.3, -0.15, 0.0, 0.15, 0.3], q_N=24, q_steps=200, q_Ws=[0.5, 2.0])
CONFIG_QUICK = dict(N=24, Rb=6.0, aspect=2.5, steps=200, seeds=(0,),
                    Ks=[0.02, 0.16, 0.35, 0.60], W=nq.FROZEN["W_planar"],
                    phi_cs=[-0.2, 0.0, 0.2], q_N=20, q_steps=140, q_Ws=[2.0])


# =============================================================== V0
def run_v0(cfg):
    """Topology Instrument reads volume b0/b1/b2/genus of fixed shapes; stable to phi_c and resolution."""
    p = nq.FROZEN
    R, a = nq.torus_from_ball(cfg["Rb"], cfg["aspect"])
    # (a) canonical analytic controls (the instrument's own GREEN set) -- ball / torus / double-torus
    shapes = [("solid_ball", tb.ball(), dict(b1=0, genus=0)),
              ("solid_torus", tb.solid_torus(), dict(b1=1, genus=1)),
              ("double_torus", tb.double_torus(), dict(b1=2, genus=2))]
    controls = []
    for name, mask, exp in shapes:
        got = tb.betti3d(mask)
        controls.append(dict(name=name, **got, expect=exp,
                             ok=bool(got["b1"] == exp["b1"] and got["genus"] == exp["genus"])))
    # (b) the SAME diffuse-interface level sets used by V1 (phi>0) must read ball b1=0, torus b1=1
    pb = nq.phi_ball(cfg["N"], cfg["Rb"], p["eps"])
    pt = nq.phi_torus(cfg["N"], R, a, p["eps"])
    diffuse = [dict(name="diffuse_ball", **tb.betti3d(pb > 0.0), expect_b1=0),
               dict(name="diffuse_torus", **tb.betti3d(pt > 0.0), expect_b1=1)]
    diffuse_ok = bool(diffuse[0]["b1"] == 0 and diffuse[1]["b1"] == 1 and diffuse[1]["genus"] == 1)
    # (c) threshold phi_c robustness (torus b1 stays 1 as phi_c moves inside the interface)
    phic_b1 = {float(c): int(tb.betti3d(pt > c)["b1"]) for c in cfg["phi_cs"]}
    phic_ok = all(v == 1 for v in phic_b1.values())
    # (d) resolution robustness (torus b1=1 at a second, coarser N)
    N2 = max(20, cfg["N"] - 8)
    R2, a2 = nq.torus_from_ball(cfg["Rb"] * N2 / cfg["N"], cfg["aspect"])
    res_b1 = int(tb.betti3d(nq.phi_torus(N2, R2, a2, p["eps"]) > 0.0)["b1"])
    res_ok = res_b1 == 1
    return dict(controls=controls, diffuse=diffuse, diffuse_ok=diffuse_ok,
                phic_b1=phic_b1, phic_ok=phic_ok, res_N=N2, res_b1=res_b1, res_ok=res_ok,
                c03_note="reported = VOLUME b1(Omega); boundary SURFACE genus equals it for a cavity-free "
                         "handlebody; surface b1 = 2*genus is a distinct count (conflict register C03)",
                all_ok=bool(all(c["ok"] for c in controls) and diffuse_ok and phic_ok and res_ok))


# =============================================================== V1
def run_v1(cfg):
    """Frank-director free-energy crossing vs elastic/capillary ratio, its anchoring-off control, and the
    Q-tensor companion (escape -> no crossing)."""
    p = nq.FROZEN
    # (a) crossing with planar anchoring ON
    on = nq.sphere_torus_crossing_frank(cfg["N"], cfg["Rb"], cfg["Ks"], W=cfg["W"], p=p,
                                        steps=cfg["steps"], seeds=cfg["seeds"], aspect=cfg["aspect"])
    dF = [r["dF"] for r in on["rows"]]
    crossing_ok = bool(on["K_star"] is not None and dF[0] > 0.0 and dF[-1] < 0.0)
    # (b) mechanism control: anchoring OFF -> no forced defects -> no crossing (ball always lower)
    off = nq.sphere_torus_crossing_frank(cfg["N"], cfg["Rb"], cfg["Ks"], W=0.0, p=p,
                                        steps=cfg["steps"], seeds=cfg["seeds"], aspect=cfg["aspect"])
    control_ok = bool(off["K_star"] is None and all(r["dF"] > 0.0 for r in off["rows"]))
    # (c) Q-tensor companion: full escape-allowing functional does NOT cross here (recorded, not a gate)
    q_rows = []
    R, a = nq.torus_from_ball(cfg["Rb"] * cfg["q_N"] / cfg["N"], cfg["aspect"])
    qb = nq.phi_ball(cfg["q_N"], cfg["Rb"] * cfg["q_N"] / cfg["N"], p["eps"])
    qt = nq.phi_torus(cfg["q_N"], R, a, p["eps"])
    for W in cfg["q_Ws"]:
        _q1, _h1, tball = nq.relax(qb, W, p, cfg["q_steps"], seed=0, kind="azimuthal")
        _q2, _h2, ttor = nq.relax(qt, W, p, cfg["q_steps"], seed=0, kind="azimuthal")
        q_rows.append(dict(W=float(W), F_ball=tball["total"], F_torus=ttor["total"],
                           dF=ttor["total"] - tball["total"]))
    qtensor_no_cross = bool(all(r["dF"] > 0.0 for r in q_rows))   # torus stays higher (escape cheapens sphere)
    return dict(anchoring_on=on, crossing_ok=crossing_ok, K_star=on["K_star"],
                area_penalty=on["area_penalty"], anchoring_off=off, control_ok=control_ok,
                qtensor_companion=dict(rows=q_rows, no_crossing=qtensor_no_cross,
                    note="full Q-tensor lets defect cores melt/escape (xi=sqrt(L1/|A|) sub-cell) so the "
                         "sphere satisfies planar anchoring cheaply and F_torus stays > F_ball; that escape "
                         "is the F2 (dynamic hole) ingredient, absent by design in V1"),
                all_ok=bool(crossing_ok and control_ok))


def evaluate(v0, v1):
    checks = {
        "V0 instrument reads ball/torus/double-torus b1=0/1/2 & genus 0/1/2": all(c["ok"] for c in v0["controls"]),
        "V0 diffuse level sets (phi>0) read ball b1=0, torus b1=1 genus=1": v0["diffuse_ok"],
        "V0 threshold phi_c robust (torus b1==1 across phi_c)": v0["phic_ok"],
        "V0 resolution robust (torus b1==1 at coarser N)": v0["res_ok"],
        "V1 sphere->torus free-energy crossing exists (small K ball, large K torus)": v1["crossing_ok"],
        "V1 mechanism control: anchoring OFF -> no crossing": v1["control_ok"],
    }
    return all(checks.values()), checks


# =============================================================== render + io
def _chart(on, off, path):
    """Dependency-free PNG: F_ball & F_torus vs K (anchoring on), with the crossing marked."""
    from tools.snapshot import write_png
    H, Wd = 300, 460
    img = np.full((H, Wd, 3), 12, np.uint8)
    rows = on["rows"]
    Ks = [r["K"] for r in rows]
    fb = [r["F_ball"] for r in rows]
    ft = [r["F_torus"] for r in rows]
    allv = fb + ft
    lo, hi = min(allv), max(allv)
    x0, x1, y0, y1 = 40, Wd - 12, 20, H - 28

    def px(k):
        return int(x0 + (k - Ks[0]) / (Ks[-1] - Ks[0] + 1e-9) * (x1 - x0))

    def py(v):
        return int(y1 - (v - lo) / (hi - lo + 1e-9) * (y1 - y0))

    def line(p0, p1, col):
        (xa, ya), (xb, yb) = p0, p1
        n = max(abs(xb - xa), abs(yb - ya), 1)
        for t in range(n + 1):
            x = int(xa + (xb - xa) * t / n); y = int(ya + (yb - ya) * t / n)
            if 0 <= x < Wd and 0 <= y < H:
                img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = col
    for i in range(len(Ks) - 1):
        line((px(Ks[i]), py(fb[i])), (px(Ks[i + 1]), py(fb[i + 1])), (110, 170, 255))   # ball = blue
        line((px(Ks[i]), py(ft[i])), (px(Ks[i + 1]), py(ft[i + 1])), (255, 150, 90))    # torus = orange
    if on["K_star"] is not None:
        xk = px(on["K_star"])
        img[y0:y1, max(0, xk - 1):xk + 1] = (90, 230, 160)                              # crossing = green
    write_png(img, path)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="e047 sphere-to-torus F1 (V0 topology check + V1 free-energy crossing)")
    ap.add_argument("--quick", action="store_true", help="coarse grid / fewer steps (physics constants unchanged)")
    ap.add_argument("--no-write", action="store_true", help="run everything but do not write results/*.json or PNG")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args(argv)
    cfg = CONFIG_QUICK if args.quick else CONFIG_FULL

    print("=== e047 sphere-to-torus -- P06 / F1 (V0 topology + V1 fixed-shape free-energy crossing) role V ===")
    v0 = run_v0(cfg)
    print("-- V0: Topology Instrument on fixed shapes (VOLUME b1; genus = surface genus of a handlebody) --")
    for c in v0["controls"]:
        print("   [%s] %-13s b0=%d b1=%d b2=%d chi=%d genus=%s"
              % ("PASS" if c["ok"] else "FAIL", c["name"], c["b0"], c["b1"], c["b2"], c["chi"], c["genus"]))
    print("   diffuse phi>0: ball b1=%d, torus b1=%d genus=%s | phi_c-robust=%s | resolution(N=%d) b1=%d"
          % (v0["diffuse"][0]["b1"], v0["diffuse"][1]["b1"], v0["diffuse"][1]["genus"],
             v0["phic_ok"], v0["res_N"], v0["res_b1"]))
    v1 = run_v1(cfg)
    print("-- V1: full free energy on FIXED shapes; sweep elastic/capillary K (planar anchoring W=%.2f) --" % cfg["W"])
    print("   area penalty (torus-ball interface) = %.2f" % v1["area_penalty"])
    print("     K       F_ball     F_torus      dF(=T-B)")
    for r in v1["anchoring_on"]["rows"]:
        print("   %6.3f  %9.2f  %9.2f   %9.2f" % (r["K"], r["F_ball"], r["F_torus"], r["dF"]))
    print("   crossing K* = %s  (ball wins at small K, torus at large K)" % v1["K_star"])
    print("   control (anchoring OFF): crossing absent = %s" % v1["control_ok"])
    print("   Q-tensor companion (escape allowed) rows:", [(r["W"], round(r["dF"], 1)) for r in v1["qtensor_companion"]["rows"]],
          "-> no crossing =", v1["qtensor_companion"]["no_crossing"])

    passed, checks = evaluate(v0, v1)
    for k, ok in checks.items():
        print("   [%s] %s" % ("PASS" if ok else "FAIL", k))
    print("STATUS:", "GREEN" if passed else "RED", "(role V: shapes are PLACED; we validate the instrument "
          "and reproduce the fixed-shape energy crossing -- NOT a claim that a hole opened by itself)")

    result = dict(experiment="e047_sphere_to_torus", rung="F1", role="V", status="GREEN" if passed else "RED",
                  frozen_constants=nq.FROZEN, config={k: v for k, v in cfg.items() if k != "seeds"},
                  v0=v0, v1={k: v for k, v in v1.items()}, checks=checks,
                  references=["Koizumi et al. arXiv:2307.00632", "Lin & Wang arXiv:2009.11487"])
    if not args.no_write:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "sphere_to_torus.json"), "w") as f:
            json.dump(result, f, indent=2, default=lambda o: list(o) if isinstance(o, tuple) else o)
        try:
            _chart(v1["anchoring_on"], v1["anchoring_off"], os.path.join(args.out, "crossing.png"))
        except Exception as e:  # PNG is a report aid, never a gate
            print("   (chart skipped:", e, ")")
        print("wrote", os.path.join(args.out, "sphere_to_torus.json"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
