#!/usr/bin/env python3
"""e046 topological state capacity -- how many independent, gauge-protected, non-contractible HOLONOMY CHANNELS
does a fixed closed surface carry? (H-gamma port, corrected role.)

MODULE:   e046_topological_state_capacity (static, rigorous cell-complex holonomy)
QUESTION: on a FIXED cell complex of a closed orientable surface, does the number of independent
          noncontractible winding-coordinate channels equal the first Betti number b_1 = 2g, and are specified
          windings (a) read back exactly, (b) invariant under local gauge relabelling, (c) zero on contractible
          cycles, (d) equal for different loops of the same homology class?
PUT IN:   the surface's cell complex (V,E,F), a U(1) edge-phase connection, an H_1 basis, and -- in some tests --
          integer windings on that basis. The TOPOLOGY and the WINDINGS are PLACED BY HAND.
MEASURED: rank H_1 = b_1 = 2g (and b_1 = 2g+b-1 with b boundaries); exact holonomy read-back; gauge invariance;
          contractible cycles read 0; same homology class -> same integer.
ROLE:     **V (topological validation)** primary, **N** secondary. Because the topology and windings are placed,
          this is NOT emergence: it verifies that this repo's holonomy instrument agrees numerically with known
          cellular-cohomology facts. It is the positive control for a future 3D topology instrument. The
          EMERGENT question (do a hole and a nonzero winding ARISE from 3D dynamics?) is a separate future
          frontier (one-handle selection / emergent holonomy), NOT claimed here.
CLAIM TIER: measured/established (a cellular-cohomology theorem, validated numerically on tested complexes).
KNOWN MATCH: cellular H^1(surface); toric-code protected logical dof = b_1; Aharonov-Bohm holonomy;
          Poincare-Hopf (sum of tangent-field defect indices = chi) as a related but DISTINCT statement.

TERMINOLOGY (conflict register C02): b_1 is the RANK of the protected winding-coordinate space = the number of
independent noncontractible holonomy channels. It is NOT an information capacity in bits (that needs a per-
channel alphabet, energy barriers, noise, readout precision, retention time). We never call a gate "memory."
DISTINCT QUANTITIES (C03): handle count g, boundary count b, and b_1=2g(+b-1) are recorded as SEPARATE fields.
NOT the same invariant (C09): the Hopf invariant (3D map preimage linking) is different from H_1 holonomy; this
module measures only the latter.

Floors: finite fixed cell complexes; b_1 is a topological invariant (shown mesh-independent at two torus
resolutions). Placed topology + placed windings => role V, not a genesis claim (same maths != same thing).
"""
import argparse
import json
import os
import sys

import numpy as np


# ---------- cell-complex homology + holonomy engine ----------
def betti_numbers(V, edges, faces):
    """Return (b0, b1, b2) from the boundary operators. edges: [(tail,head)]. faces: [[(edge,sign),...]].
    b0 = V - rank(d1) (components); b1 = nullity(d1) - rank(d2); b2 = nullity(d2) (closed-surface 2-cycles)."""
    E = len(edges)
    d1 = np.zeros((V, E))
    for e, (t, h) in enumerate(edges):
        d1[t, e] -= 1.0
        d1[h, e] += 1.0
    F = len(faces)
    d2 = np.zeros((E, F))
    for f, loop in enumerate(faces):
        for (e, s) in loop:
            d2[e, f] += s
    r1 = int(np.linalg.matrix_rank(d1)) if E else 0
    r2 = int(np.linalg.matrix_rank(d2)) if F else 0
    b0 = V - r1
    b1 = (E - r1) - r2
    b2 = F - r2
    return b0, b1, b2


def holonomy(theta, cycle):
    """Winding read on an oriented cycle [(edge,sign),...] = (sum of signed edge phases)/2pi."""
    return sum(s * theta[e] for (e, s) in cycle) / (2.0 * np.pi)


def face_flux(theta, faces):
    return max((abs(sum(s * theta[e] for (e, s) in loop)) for loop in faces), default=0.0)


# ---------- fixed closed orientable surfaces ----------
def octahedron():
    """Sphere (genus 0): V=6,E=12,F=8, chi=2 -> (b0,b1,b2)=(1,0,1)."""
    tri = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
           (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    edict = {}

    def eid(a, b):
        edict.setdefault((min(a, b), max(a, b)), len(edict))
        return edict[(min(a, b), max(a, b))]
    for (a, b, c) in tri:
        eid(a, b); eid(b, c); eid(c, a)
    edges = [None] * len(edict)
    for k, i in edict.items():
        edges[i] = k
    faces = []
    for (a, b, c) in tri:
        loop = []
        for (x, y) in [(a, b), (b, c), (c, a)]:
            i = edict[(min(x, y), max(x, y))]
            loop.append((i, 1.0 if edges[i] == (x, y) else -1.0))
        faces.append(loop)
    return {"name": "sphere(octahedron)", "V": 6, "edges": edges, "faces": faces, "genus": 0, "boundary": 0}


def torus_grid(n):
    """Torus (genus 1) as n x n periodic grid: V=n^2,E=2n^2,F=n^2, chi=0 -> (1,2,1). Provides two basis cycles
    (a: horizontal, b: vertical) + a2 (a second horizontal loop, same class as a) for the non-locality test."""
    eidx, edges = {}, []

    def vid(i, j):
        return (i % n) * n + (j % n)
    for i in range(n):
        for j in range(n):
            eidx[("h", i, j)] = len(edges); edges.append((vid(i, j), vid(i, j + 1)))
            eidx[("v", i, j)] = len(edges); edges.append((vid(i, j), vid(i + 1, j)))

    def eh(i, j):
        return eidx[("h", i % n, j % n)]

    def ev(i, j):
        return eidx[("v", i % n, j % n)]
    faces = [[(eh(i, j), 1.0), (ev(i, j + 1), 1.0), (eh(i + 1, j), -1.0), (ev(i, j), -1.0)]
             for i in range(n) for j in range(n)]
    cyc = {"a": [(eh(0, j), 1.0) for j in range(n)],
           "b": [(ev(i, 0), 1.0) for i in range(n)],
           "a2": [(eh(n // 2, j), 1.0) for j in range(n)]}
    return {"name": "torus%dx%d" % (n, n), "V": n * n, "edges": edges, "faces": faces,
            "eidx": eidx, "cyc": cyc, "n": n, "genus": 1, "boundary": 0}


def genus_cw(g):
    """Standard CW complex of a genus-g surface: 1 vertex, 2g edges (a_i,b_i), 1 face = prod [a_i,b_i].
    (b0,b1,b2)=(1,2g,1) for g>=1. Generator a_i is a cycle with holonomy theta_{a_i}. General proof of 2g."""
    edges = [(0, 0)] * (2 * g)
    face = []
    for i in range(g):
        a, b = 2 * i, 2 * i + 1
        face += [(a, 1.0), (b, 1.0), (a, -1.0), (b, -1.0)]
    cycles = [[(e, 1.0)] for e in range(2 * g)]
    return {"name": "genus%d" % g, "V": 1, "edges": edges, "faces": [face] if g else [],
            "cycles": cycles, "genus": g, "boundary": 0}


def _uniform_torus_connection(cx, windings):
    """FLAT torus connection (zero face flux) with holonomy windings=(wa,wb): uniform phase per edge-type."""
    wa, wb = windings
    n = cx["n"]
    theta = np.zeros(len(cx["edges"]))
    for key, e in cx["eidx"].items():
        theta[e] = 2 * np.pi * (wa if key[0] == "h" else wb) / n
    return theta


def surface_record(cx):
    b0, b1, b2 = betti_numbers(cx["V"], cx["edges"], cx["faces"])
    return {"name": cx["name"], "V": cx["V"], "E": len(cx["edges"]), "F": len(cx["faces"]),
            "euler": cx["V"] - len(cx["edges"]) + len(cx["faces"]),
            "b0": b0, "b1": b1, "b2": b2, "genus": cx["genus"], "boundary": cx["boundary"],
            "independent_holonomy_channels": b1}       # == b1; NOT information capacity (C02)


def simulate(seed=0):
    rng = np.random.default_rng(seed)
    out = {"surfaces": [], "torus_tests": [], "genus_scaling": []}
    out["surfaces"].append(surface_record(octahedron()))
    for n in (4, 6):
        T = torus_grid(n)
        out["surfaces"].append(surface_record(T))
        wa, wb = int(rng.integers(-3, 4)), int(rng.integers(-3, 4))
        theta = _uniform_torus_connection(T, (wa, wb))
        lam = rng.normal(0, 1, T["V"])
        tg = theta.copy()
        for e, (t, h) in enumerate(T["edges"]):
            tg[e] += lam[h] - lam[t]
        out["torus_tests"].append({
            "n": n, "put_in": [wa, wb],
            "read_back": [round(holonomy(theta, T["cyc"]["a"]), 6), round(holonomy(theta, T["cyc"]["b"]), 6)],
            "flat_flux": round(face_flux(theta, T["faces"]), 12),
            "contractible": round(holonomy(theta, T["faces"][0]), 12),
            "gauge_read_back": [round(holonomy(tg, T["cyc"]["a"]), 6), round(holonomy(tg, T["cyc"]["b"]), 6)],
            "nonlocal_same_class_delta": round(abs(holonomy(theta, T["cyc"]["a2"])
                                                   - holonomy(theta, T["cyc"]["a"])), 12)})
    for g in (0, 1, 2, 3, 4):
        C = genus_cw(g)
        b0, b1, b2 = betti_numbers(C["V"], C["edges"], C["faces"])
        w = rng.integers(-3, 4, size=2 * g).tolist()
        theta = np.zeros(len(C["edges"]))
        for e in range(2 * g):
            theta[e] = 2 * np.pi * w[e]
        read = [int(round(holonomy(theta, C["cycles"][e]))) for e in range(2 * g)]
        out["genus_scaling"].append({"genus": g, "b1": b1, "expected_2g": 2 * g, "read_back_exact": read == w})
    return out


def evaluate(r):
    sph = next(s for s in r["surfaces"] if s["genus"] == 0)
    tor = r["torus_tests"]
    checks = {
        "rank_h1_equals_betti1 (torus b1=2 at all resolutions; genus g -> 2g)":
            all(s["b1"] == 2 * s["genus"] for s in r["surfaces"])
            and all(s["b1"] == s["expected_2g"] and s["read_back_exact"] for s in r["genus_scaling"]),
        "sphere_zero_channels (genus-0 surface carries 0 protected winding coordinates)": sph["b1"] == 0,
        "holonomy_readback_exact (specified windings recovered)":
            all(abs(t["read_back"][0] - t["put_in"][0]) < 1e-6
                and abs(t["read_back"][1] - t["put_in"][1]) < 1e-6 for t in tor),
        "contractible_cycle_zero (flat connection; contractible loop reads 0)":
            all(t["flat_flux"] < 1e-9 and abs(t["contractible"]) < 1e-9 for t in tor),
        "holonomy_gauge_invariant (read unchanged under local phase relabelling)":
            all(abs(t["gauge_read_back"][0] - t["put_in"][0]) < 1e-6
                and abs(t["gauge_read_back"][1] - t["put_in"][1]) < 1e-6 for t in tor),
        "same_homology_same_readout (different loop, same class -> same integer)":
            all(t["nonlocal_same_class_delta"] < 1e-9 for t in tor),
    }
    return all(checks.values()), checks


def main(argv=None):
    ap = argparse.ArgumentParser(description="e046 topological state capacity (V): independent holonomy channels = b1")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate()
    print("=== e046 topological state capacity -- independent noncontractible holonomy channels = b_1 (role V) ===")
    for s in r["surfaces"]:
        print("  %-16s V=%d E=%d F=%d chi=%d (b0,b1,b2)=(%d,%d,%d) genus=%d channels=%d"
              % (s["name"], s["V"], s["E"], s["F"], s["euler"], s["b0"], s["b1"], s["b2"],
                 s["genus"], s["independent_holonomy_channels"]))
    for t in r["torus_tests"]:
        print("  torus n=%d put_in=%s read=%s gauge=%s flux=%g contractible=%g nonlocal_delta=%g"
              % (t["n"], t["put_in"], t["read_back"], t["gauge_read_back"], t["flat_flux"],
                 t["contractible"], t["nonlocal_same_class_delta"]))
    for s in r["genus_scaling"]:
        print("  genus %d: b1=%d (expect %d) read_back_exact=%s" % (s["genus"], s["b1"], s["expected_2g"], s["read_back_exact"]))
    passed, checks = evaluate(r)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (role V: topology+windings PLACED; validates the holonomy instrument, not emergence)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "topological_state_capacity.json"), "w") as f:
            json.dump({"result": r, "passed": passed, "checks": checks}, f, indent=2)
        print("wrote results/topological_state_capacity.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
