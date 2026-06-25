#!/usr/bin/env python3
"""Aeterna-Genesis experiment e004 -- octave hierarchy / folding / holography.

================================ AUDIT HEADER ================================
MODULE:      e004_octave_holography
QUESTION:    Does a pure octave (factor-2) coarse-graining hierarchy carry a
             hyperbolic (AdS/MERA-like) "radial" geometry, and does a spiral =
             repetition + small asymmetry (0!=nothing / 51:49) progress instead
             of closing -- with one spiral turn = one octave = one fold-layer?
PUT IN:      (A) a 1D ring of L0 nodes (highest-frequency band) + binary
             coarse-graining: layer l has L0/2^l nodes, intra-layer ring edges,
             and inter-layer edges parent i -> children {2i, 2i+1}. NO curvature,
             NO "hyperbolic" instruction.
             (B) a rotation-with-bias map z -> z*exp(i 2pi/N)*(1+eps). eps is
             HAND-SET (the 51:49 asymmetry is an input, not an emergence).
EMERGED:     (measured) exponential ball growth + diameter ~ log(N) + boundary
             distance ~ log(separation) (geodesics dip into the bulk) =
             hyperbolic/holographic signatures; spiral closes at eps=0 and
             advances linearly in log-radius at eps>0, with one turn = one
             octave when (1+eps)^N = 2.
CLAIM TIER:  measured (the graph/spiral numbers) ; interpretive/analogy (the
             AdS-CFT / MERA / RG / Ryu-Takayanagi reading) ; speculative (the
             cosmological "spacetime from octaves" picture).
KNOWN MATCH: MERA tensor networks & AdS/CFT (the tree is the canonical discrete
             hyperbolic bulk); renormalization (each layer halves the dof);
             small-world/hyperbolic graphs (diameter ~ log N).
AUDIT (7):   see AUDIT.md. HONEST VERDICT: YELLOW, not GREEN.
             1 rules name the result? No (local ring+tree edges only).
             2 faithful physics?      PARTIAL -- this is a faithful RG/MERA
               *structure*, not a dynamical field law (unlike e001/e002 GPE).
             3 result in the inputs?  PARTIAL/NO -- a binary hierarchy is
               *inherently* hyperbolic, so the geometry is largely encoded by
               the construction. This is the main reason it is not GREEN.
             4 un-asked things?       Mild (local ~2D then global hyperbolic).
             5 agrees by number?      Yes, with MERA/AdS expectations.
             6 robust?                Yes, across L0 in {256..2048} and eps.
             7 code discovers?        Yes (BFS measurement, not hardcoded).
STATUS:      YELLOW -- the signatures are measured and robust, but the geometry
             is built into the hand-made hierarchy and the model is structural
             (RG/MERA), not a faithful dynamical emergence. Reported as a
             measured-structural result / suggestion, NOT a success/GREEN.
A_OR_B:      Intended (A) faithful emergence, but honestly this sits between a
             faithful construction and an analogy: the folding hierarchy and the
             asymmetry eps are hand inputs. Deriving the hierarchy/eps from
             0!=nothing is the deeper (B) floor, NOT attempted here.
=============================================================================

Honest floors (LAW.md), stated up front and never hidden:
  * The octave hierarchy is HAND-BUILT; binary trees are inherently hyperbolic,
    so "hyperbolic geometry emerged" is really "we built a hierarchy whose
    geometry is hyperbolic and measured it". Re-derivation, not surprise.
  * eps (the 51:49 spiral asymmetry) is HAND-SET: we measure "asymmetry ->
    spiral -> progress", not the emergence of the asymmetry itself.
  * This reproduces MERA / AdS-CFT structure; it is NOT new physics (analogy).
  * Flat real space (the 3D we live in) does NOT come out of folding alone --
    that needs a 2-cell / "third" (known floor). The folded direction is the
    holographic RADIAL handle, not a flat-space handle.

Run with no args for the full result + result.json. --quick for a short run.
"""

import argparse
import json
import os
import sys
from collections import deque

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# --------------------------------------------------------------------------
# graph construction + measurement primitives (self-contained: this is a
# graph/RG modality, not the field core used by e001/e002)
# --------------------------------------------------------------------------
def build_octave_hierarchy(L0):
    """Build the folding hierarchy graph. Returns (adjacency, layer_sizes).

    Node = (layer, index). Highest-frequency band = layer 0 ring of L0 nodes.
    Each layer halves; intra-layer ring edges encode "nearness in that band";
    inter-layer edges (the fold / spiral step) connect parent i in layer l to
    children {2i, 2i+1} in layer l-1.
    """
    sizes = []
    s = L0
    while s >= 1:
        sizes.append(s)
        if s == 1:
            break
        s //= 2
    adj = {(l, i): set() for l, sz in enumerate(sizes) for i in range(sz)}
    for l, sz in enumerate(sizes):
        if sz >= 3:                                   # ring within the band
            for i in range(sz):
                j = (i + 1) % sz
                adj[(l, i)].add((l, j))
                adj[(l, j)].add((l, i))
        elif sz == 2:
            adj[(l, 0)].add((l, 1))
            adj[(l, 1)].add((l, 0))
        if l >= 1:                                    # fold to the band below
            child_sz = sizes[l - 1]
            for i in range(sz):
                for c in (2 * i, 2 * i + 1):
                    if c < child_sz:
                        adj[(l, i)].add((l - 1, c))
                        adj[(l - 1, c)].add((l, i))
    return adj, sizes


def bfs_distances(adj, src):
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def _fit_r2(x, y):
    """Least-squares linear fit; return R^2 (coefficient of determination)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.size < 3:
        return float("nan")
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


# --------------------------------------------------------------------------
# Part A -- is the octave/fold hierarchy hyperbolic?
# --------------------------------------------------------------------------
def part_a(L0, scaling_L0):
    adj, sizes = build_octave_hierarchy(L0)
    N = len(adj)
    dist = bfs_distances(adj, (0, 0))
    maxd = max(dist.values())
    ball = np.array([sum(1 for d in dist.values() if d <= r)
                     for r in range(maxd + 1)], dtype=float)
    rs = np.arange(maxd + 1)
    sel = (rs >= 1) & (ball < 0.6 * N)               # unsaturated regime
    r2_exp = _fit_r2(rs[sel], np.log(ball[sel]))         # log(ball) vs r
    r2_pow = _fit_r2(np.log(rs[sel]), np.log(ball[sel]))  # log(ball) vs log(r)

    # diameter scaling across sizes (double-sweep estimate)
    diam_rows = []
    for L in scaling_L0:
        a, _ = build_octave_hierarchy(L)
        far = max(bfs_distances(a, (0, 0)).items(), key=lambda kv: kv[1])[0]
        diam = max(bfs_distances(a, far).values())
        diam_rows.append({"L0": L, "N": len(a), "diameter": int(diam)})
    Ns = [r["N"] for r in diam_rows]
    Ds = [r["diameter"] for r in diam_rows]
    r2_diam_log = _fit_r2(np.log(Ns), Ds)                # diam ~ log N (hyperbolic)
    r2_diam_pow = _fit_r2(np.log(Ns), np.log(Ds))        # log diam ~ log N (power)

    # radial distance to the same position 0 across octaves (dream point 3)
    radial = [int(dist[(l, 0)]) for l in range(len(sizes))]

    return {
        "L0": L0, "N": N, "n_layers": len(sizes), "max_distance": int(maxd),
        "ball_growth": ball.tolist(),
        "r2_ball_exponential": r2_exp, "r2_ball_power": r2_pow,
        "hyperbolic_wins": bool(r2_exp > r2_pow),
        "diameter_scaling": diam_rows,
        "r2_diameter_vs_logN": r2_diam_log,
        "r2_logdiameter_vs_logN": r2_diam_pow,
        "diameter_is_logN": bool(r2_diam_log > r2_diam_pow and r2_diam_log > 0.99),
        "radial_distance_per_octave": radial,
        "radial_increases_with_octave": bool(all(
            radial[l + 1] > radial[l] for l in range(len(radial) - 1))),
    }


# --------------------------------------------------------------------------
# Part B -- spiral = repetition + small asymmetry (0 != nothing)
# --------------------------------------------------------------------------
def _spiral(N, eps, turns):
    rot = np.exp(1j * 2 * np.pi / N) * (1.0 + eps)
    z = 1.0 + 0j
    pts = [z]
    for _ in range(int(round(turns * N))):
        z = z * rot
        pts.append(z)
    return np.array(pts)

def part_b(N, eps, turns):
    # symmetric: closes (circle)
    z0 = _spiral(N, 0.0, 1)
    closure = float(abs(z0[-1] - z0[0]))
    radius_spread_sym = float(np.abs(z0).max() - np.abs(z0).min())

    # asymmetric: progresses (spiral)
    z = _spiral(N, eps, turns)
    logr = np.log(np.abs(z))
    step = np.arange(len(z))
    A = np.vstack([step, np.ones_like(step)]).T
    slope = float(np.linalg.lstsq(A, logr, rcond=None)[0][0])
    per_turn = [float(logr[k * N]) for k in range(turns + 1)]
    advances = list(np.diff(per_turn))
    advance_constant = float(np.std(advances) / (abs(np.mean(advances)) + 1e-30))

    # octave bridge: choose eps so one turn doubles the radius -> one octave/turn
    eps_oct = 2.0 ** (1.0 / N) - 1.0
    zo = _spiral(N, eps_oct, 5)
    log2r_turns = [float(np.log2(abs(zo[k * N]))) for k in range(6)]
    octave_increments = list(np.diff(log2r_turns))

    return {
        "N": N, "eps": eps, "turns": turns,
        "symmetric_closure_displacement": closure,
        "symmetric_radius_spread": radius_spread_sym,
        "closes_when_symmetric": bool(closure < 1e-9),
        "logradius_slope": slope,
        "logradius_slope_expected": float(np.log(1.0 + eps)),
        "progresses_when_asymmetric": bool(slope > 0
                                           and abs(slope - np.log(1 + eps)) < 1e-6),
        "per_turn_logradius_advance": advances,
        "advance_constant_relstd": advance_constant,
        "eps_for_one_octave_per_turn": eps_oct,
        "log2radius_per_turn": log2r_turns,
        "octave_increments_per_turn": octave_increments,
        "one_octave_per_turn": bool(np.allclose(octave_increments, 1.0, atol=1e-9)),
    }


# --------------------------------------------------------------------------
# Part C -- bundle all bands into one geometry (holographic layering)
# --------------------------------------------------------------------------
def part_c(L0):
    adj, sizes = build_octave_hierarchy(L0)
    N = len(adj)
    dist = bfs_distances(adj, (0, 0))
    connected = bool(len(dist) == N)

    # boundary(0,0) -> boundary(0,j): full-graph distance vs ring separation j.
    # ring alone would give ~ j; log(j) means geodesics dip into the bulk (RT).
    js = [j for j in (1, 2, 4, 8, 16, 32, 64, 128, 256) if j < sizes[0]]
    bdist = [int(dist[(0, j)]) for j in js]
    r2_boundary_log = _fit_r2(np.log(js), bdist)
    r2_boundary_lin = _fit_r2(js, bdist)

    radial = [int(dist[(l, 0)]) for l in range(len(sizes))]
    return {
        "L0": L0, "N": N, "connected": connected,
        "layer_sizes_radial": sizes,
        "boundary_separations": js,
        "boundary_distance": bdist,
        "r2_boundary_vs_log_separation": r2_boundary_log,
        "r2_boundary_vs_linear_separation": r2_boundary_lin,
        "boundary_distance_is_logarithmic":
            bool(r2_boundary_log > r2_boundary_lin),
        "radial_distance_per_octave": radial,
    }


# --------------------------------------------------------------------------
# Part D -- RG x holography structural correspondence (interpretive only)
# --------------------------------------------------------------------------
def part_d(a_result, c_result):
    # purely a structural consistency statement -- no fabricated numbers.
    return {
        "rg_halving_matches_radial": bool(
            c_result["layer_sizes_radial"][0]
            // c_result["layer_sizes_radial"][-1] == 2 ** (a_result["n_layers"] - 1)),
        "note": (
            "Each fold layer halves the dof (RG step) and is one radial shell of "
            "the measured hyperbolic geometry; boundary distance ~ log(separation) "
            "is structurally the Ryu-Takayanagi behaviour (geodesic through the "
            "bulk). This is a STRUCTURAL correspondence (interpretive/speculative), "
            "not a quantitative proof, and flat real space still needs a 2-cell."),
        "claim_tier": "interpretive/speculative",
    }


def simulate(quick=False):
    if quick:
        L0, scaling = 256, [128, 256, 512]
        N_spiral, turns = 32, 6
    else:
        L0, scaling = 512, [256, 512, 1024, 2048]
        N_spiral, turns = 64, 8
    a = part_a(L0, scaling)
    b = part_b(N_spiral, eps=0.02, turns=turns)
    c = part_c(L0)
    d = part_d(a, c)
    return {"part_a": a, "part_b": b, "part_c": c, "part_d": d}


def evaluate(result):
    """Booleans for the measured signatures (signal present?). NOTE: these say
    the measured signatures are present -- they do NOT upgrade the honest 7-audit
    verdict, which is YELLOW (see AUDIT.md): the geometry is built into the
    hand-made hierarchy, so this is measured-structural, not faithful emergence.
    """
    a, b, c = result["part_a"], result["part_b"], result["part_c"]
    checks = {
        "A_ball_exponential_beats_power": a["hyperbolic_wins"],
        "A_diameter_scales_as_logN": a["diameter_is_logN"],
        "A_radial_grows_with_octave": a["radial_increases_with_octave"],
        "B_symmetric_circle_closes": b["closes_when_symmetric"],
        "B_asymmetric_spiral_progresses": b["progresses_when_asymmetric"],
        "B_one_octave_per_turn": b["one_octave_per_turn"],
        "C_bundle_connected": c["connected"],
        "C_boundary_distance_logarithmic": c["boundary_distance_is_logarithmic"],
    }
    return all(checks.values()), checks


def _print_report(result):
    print(__doc__)
    a, b, c, d = (result["part_a"], result["part_b"],
                  result["part_c"], result["part_d"])
    print("------------------------------ MEASUREMENTS ------------------------------")
    print("[Part A] octave/fold hierarchy geometry  (L0=%d, N=%d, layers=%d)"
          % (a["L0"], a["N"], a["n_layers"]))
    print("  ball growth: R^2 exponential=%.4f  vs  power=%.4f  -> hyperbolic wins: %s"
          % (a["r2_ball_exponential"], a["r2_ball_power"], a["hyperbolic_wins"]))
    print("  diameter vs log(N): R^2=%.4f  (log diam vs log N: R^2=%.4f) -> log(N): %s"
          % (a["r2_diameter_vs_logN"], a["r2_logdiameter_vs_logN"],
             a["diameter_is_logN"]))
    print("    " + "  ".join("L0=%d:diam=%d" % (r["L0"], r["diameter"])
                             for r in a["diameter_scaling"]))
    print("  radial distance to (layer l, pos 0): %s -> grows with octave: %s"
          % (a["radial_distance_per_octave"], a["radial_increases_with_octave"]))
    print("[Part B] spiral = repetition + asymmetry  (N=%d, eps=%.3f)"
          % (b["N"], b["eps"]))
    print("  symmetric (eps=0): closure displacement=%.2e -> circle closes: %s"
          % (b["symmetric_closure_displacement"], b["closes_when_symmetric"]))
    print("  asymmetric: d(log r)/dstep=%.6f (expect %.6f) -> progresses: %s"
          % (b["logradius_slope"], b["logradius_slope_expected"],
             b["progresses_when_asymmetric"]))
    print("  octave bridge: log2(radius) per turn=%s -> one octave/turn: %s"
          % ([round(x, 3) for x in b["log2radius_per_turn"]],
             b["one_octave_per_turn"]))
    print("[Part C] bundle all bands  (N=%d)" % c["N"])
    print("  connected: %s | radial layer sizes: %s"
          % (c["connected"], c["layer_sizes_radial"]))
    print("  boundary dist vs separation: %s for j=%s"
          % (c["boundary_distance"], c["boundary_separations"]))
    print("    R^2 vs log(sep)=%.4f  vs  linear(sep)=%.4f -> logarithmic (RT-like): %s"
          % (c["r2_boundary_vs_log_separation"],
             c["r2_boundary_vs_linear_separation"],
             c["boundary_distance_is_logarithmic"]))
    print("[Part D] RG x holography (structural, interpretive):")
    print("  " + d["note"])
    _, checks = evaluate(result)
    print("--------------------------- MEASURED SIGNATURES --------------------------")
    for k, v in checks.items():
        print("  [%s] %s" % ("yes" if v else "NO", k))
    allsig, _ = evaluate(result)
    print("ALL MEASURED SIGNATURES PRESENT: %s" % allsig)
    print("HONEST 7-AUDIT VERDICT: YELLOW (measured-structural, not GREEN) -- the")
    print("geometry is built into the hand-made hierarchy and eps is hand-set; this")
    print("reproduces MERA/AdS structure (analogy), it is not faithful emergence.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="octave hierarchy / holography (e004)")
    ap.add_argument("--quick", action="store_true", help="short run for CI/tests")
    ap.add_argument("--no-write", action="store_true", help="do not write result.json")
    args = ap.parse_args(argv)

    result = simulate(quick=args.quick)
    _print_report(result)

    if not args.no_write and not args.quick:
        out_path = os.path.join(os.path.dirname(__file__), "result.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print("\nwrote %s" % out_path)

    # exit 0 if the measured signatures are present (NOT a GREEN claim).
    allsig, _ = evaluate(result)
    return 0 if allsig else 1


if __name__ == "__main__":
    sys.exit(main())
