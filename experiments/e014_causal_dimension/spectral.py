#!/usr/bin/env python3
"""e014 Stage 2 -- the SPECTRAL dimension (a second, independent ruler).

The Myrheim-Meyer dimension (Stage 1) is a Hausdorff-type counting dimension.
The SPECTRAL dimension is different: it is how a diffusion/random walk spreads,
d_s = -2 d ln P(t) / d ln t, where P(t) = (1/N) sum_i exp(-t lambda_i) is the
heat-kernel return probability of the graph Laplacian (lambda_i its eigenvalues).
For a smooth D-dim geometry, d_s -> D.

We measure:
  * a 3D geometric lattice graph -> d_s ~ 3 (and a 2D control -> ~2): geometry's
    diffusion knows its dimension.
  * the causal-set link (Hasse-diagram) graph -> d_s, which is ALLOWED to differ
    from the Hausdorff/Myrheim-Meyer value -- the spectral dimension of a causal
    set is a known subtle/anomalous quantity. We report it honestly, not force it.

So "causal/geometry -> dimension" stands on TWO rulers, with the honest caveat
that they need not agree for a discrete causal set.

MODULE:   e014_causal_dimension (Stage 2: spectral dimension)
QUESTION: Does the heat-kernel spectral dimension of geometry read d_s~3 (and how does a causal set's compare)?
PUT IN:   a graph Laplacian (3D/2D lattice; causal-set Hasse diagram). The dimension is read from diffusion, not put in.
EMERGED:  (measured) 3D geometry -> d_s~3, 2D -> ~2; causal-set Hasse d_s reported (may be anomalous).
CLAIM TIER: measured(geometry d_s~D) ; observed(causal-set d_s) ; interpretive(diffusion encodes dimension).
KNOWN MATCH: spectral dimension in CDT/causal sets; heat-kernel dimension.
STATUS:   GREEN (geometry d_s~3 measured; causal-set spectral dim reported with the known-anomaly floor).
A_OR_B:   (A) faithful. Hand input = a graph; the dimension is read from its diffusion.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"grid2d_L": 40, "grid3d_L": 22, "cset_d": 3, "cset_N": 400,
           "cset_seeds": [0, 1]}
QUICK = {"grid2d_L": 28, "grid3d_L": 16, "cset_N": 250, "cset_seeds": [0]}


def _spectral_dim(lam, ts):
    P = np.array([np.mean(np.exp(-t * lam)) for t in ts])
    ds = -2.0 * np.gradient(np.log(P), np.log(ts))
    return ds


def _grid_eigs(L, dim):
    k = 2 * np.pi * np.fft.fftfreq(L)
    if dim == 2:
        KX, KY = np.meshgrid(k, k, indexing="ij")
        lam = 2 * (2 - np.cos(KX) - np.cos(KY))
    else:
        KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
        lam = 2 * (3 - np.cos(KX) - np.cos(KY) - np.cos(KZ))
    return lam.ravel()


def grid_ds(L, dim):
    lam = _grid_eigs(L, dim)
    ts = np.logspace(0.3, 1.6, 20)
    ds = _spectral_dim(lam, ts)
    return float(np.median(ds[5:15]))


def _sprinkle(d, N, rng):
    T, X = [], []
    while len(T) < N:
        m = (N - len(T)) * 4 + 16
        t = rng.uniform(0, 1, m)
        xs = rng.uniform(-0.5, 0.5, (m, d - 1)) if d > 1 else np.zeros((m, 0))
        rx = np.sqrt((xs ** 2).sum(1)) if d > 1 else np.zeros(m)
        keep = (t > rx) & ((1 - t) > rx)
        for ti, xi in zip(t[keep], xs[keep]):
            T.append(ti)
            X.append(xi)
            if len(T) >= N:
                break
    return np.array(T), np.array(X)


def _hasse_laplacian(T, X):
    """Symmetric normalized Laplacian of the covering-relation (Hasse) graph."""
    N = len(T)
    rel = np.zeros((N, N), bool)
    for i in range(N):
        dt = T - T[i]
        dx2 = ((X - X[i]) ** 2).sum(1) if X.shape[1] > 0 else np.zeros(N)
        rel[i] = (dt > 0) & (dt ** 2 > dx2)
    A = np.zeros((N, N))
    for i in range(N):
        for j in np.where(rel[i])[0]:
            if not np.any(rel[i] & rel[:, j]):       # covering: no intermediate
                A[i, j] = A[j, i] = 1.0
    deg = A.sum(1)
    deg[deg == 0] = 1.0
    Dm = np.diag(1.0 / np.sqrt(deg))
    return Dm @ (np.diag(deg) - A) @ Dm


def causal_set_ds(d, N, seeds):
    vals = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        T, X = _sprinkle(d, N, rng)
        lam = np.linalg.eigvalsh(_hasse_laplacian(T, X))
        ds = _spectral_dim(lam, np.logspace(-0.3, 0.8, 20))
        vals.append(float(np.median(ds[5:15])))
    return float(np.mean(vals))


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    ds2 = grid_ds(p["grid2d_L"], 2)
    ds3 = grid_ds(p["grid3d_L"], 3)
    cset = causal_set_ds(p["cset_d"], p["cset_N"], p["cset_seeds"])
    return {"params": p,
            "grid_2d_d_s": round(ds2, 3),
            "grid_3d_d_s": round(ds3, 3),
            "causal_set_d_s": round(cset, 3),
            "causal_set_d": p["cset_d"]}


EXPECT = {"tol": 0.25}


def evaluate(result, quick=False):
    checks = {
        "grid_3d_d_s~3": abs(result["grid_3d_d_s"] - 3.0) < EXPECT["tol"],
        "grid_2d_d_s~2": abs(result["grid_2d_d_s"] - 2.0) < EXPECT["tol"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e014 spectral dimension", "tier": "measured",
        "put_in": "graph Laplacian (3D/2D lattice; causal-set Hasse diagram); dimension read from diffusion",
        "emerged": ["3D geometry d_s=%.2f, 2D d_s=%.2f (diffusion knows the dimension)"
                    % (result["grid_3d_d_s"], result["grid_2d_d_s"]),
                    "causal-set Hasse d_s=%.2f (a second ruler; may be anomalous vs Hausdorff)"
                    % result["causal_set_d_s"]],
        "surprises": ["the spectral and Myrheim-Meyer dimensions are independent rulers"],
        "persistence": "kinematic graph property",
        "measured_numbers": {"grid_2d_d_s": result["grid_2d_d_s"],
                             "grid_3d_d_s": result["grid_3d_d_s"],
                             "causal_set_d_s": result["causal_set_d_s"]},
        "not_scripted_check": "d_s read from the heat-kernel slope; no dimension label is used",
        "claim_tier": "measured (geometry d_s~D) ; observed (causal-set d_s) ; interpretive (diffusion encodes dimension)",
        "floors": ["causal-set spectral dimension is a known subtle/anomalous quantity; reported, not forced to match d_MM",
                   "kinematic; dynamic geometry is AJL (inherited)"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e014 spectral dimension")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e014 spectral dimension (heat-kernel) ===")
    print("  2D geometry grid: d_s = %.3f (expect ~2)" % r["grid_2d_d_s"])
    print("  3D geometry grid: d_s = %.3f (expect ~3)" % r["grid_3d_d_s"])
    print("  causal-set (d=%d) Hasse graph: d_s = %.3f (may be anomalous vs Hausdorff d_MM)"
          % (r["causal_set_d"], r["causal_set_d_s"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (geometry spectral dim measured; causal-set d_s reported with anomaly floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        out = os.path.dirname(__file__)
        with open(os.path.join(out, "spectral.json"), "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote spectral.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
