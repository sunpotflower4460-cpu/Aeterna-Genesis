"""Corroboration for the one-chemistry protocell (P17): are the containers a property of the law, or of the local
finite-difference stencil?

The same law and the same t = 0 are run with two independent discretisations of ∇² -- the LOCAL nearest-neighbour
stencil (the main line) and a SPECTRAL (FFT) Laplacian with a smaller time step (its ∇⁴ has larger eigenvalues) --
and scale-robust observables are compared (all in the verdict): the number of containers, how many hold a replicator spot, the share of
the box inside containers, the mean replicator density and the inside/outside ratio. Same pattern of layout under
both => not a discretisation artefact. The measure (genesis.models.protocell.containers) is shared and unchanged.
"""
from __future__ import annotations

import numpy as np

KEYS = ("containers", "occupied", "box_share", "replicators", "in_out")


def observables(c, V1, V2):
    from genesis.diagnostics.protocell_measures import assign_spots
    from genesis.models import protocell as pc
    lab, cs = pc.containers(c, V1, V2)
    box = lab > 0
    V = V1 + V2
    per, _ = assign_spots(pc.labels(V, pc.THRESH_V), lab)             # a spot counts for one container only
    v_out = float(V[~box].mean()) if (~box).any() else 0.0
    return {"containers": len(cs), "occupied": sum(1 for v in per.values() if v > 0),
            "box_share": float(box.mean()), "replicators": float(V.mean()),
            "in_out": float(V[box].mean() / max(v_out, 1e-9)) if box.any() else 0.0}


def agree(a, b, tol=0.2, keys=KEYS):
    rel = {k: abs(a[k] - b[k]) / (abs(a[k]) + abs(b[k]) + 1e-9) for k in keys}
    return bool(all(v <= tol for v in rel.values())), {k: round(v, 4) for k, v in rel.items()}


def corroborate_local_vs_spectral(shape, T, seed=1, params=None, refine=8, tol=0.2):
    """Run genesis.models.protocell_one from one t = 0 with the local stencil (dt) and with the spectral Laplacian
    (dt / refine) to time T; compare observables. Returns a verdict dict."""
    from genesis.models import protocell_one as po
    p = dict(po.DEFAULTS if len(shape) == 3 else po.DEFAULTS_2D, **(params or {}))
    s0 = po.make_initial(shape, np.random.default_rng(seed), p)
    a = tuple(x.copy() for x in s0)
    for _ in range(int(round(T / p["dt"]))):
        a = po.step(*a, p)
    ps = dict(p, dt=p["dt"] / refine)
    lap = po.spectral_laplacian(shape, p.get("dx", 1.0))              # the same physical grid as the local run
    b = tuple(x.copy() for x in s0)
    for _ in range(int(round(T / ps["dt"]))):
        b = po.step(*b, ps, lap=lap)
    oa, ob = observables(*(a[0], a[2], a[3])), observables(*(b[0], b[2], b[3]))
    ok, rel = agree(oa, ob, tol=tol)
    return {"corroborated": ok, "tol": tol, "rel_diff": rel, "local": oa, "spectral": ob,
            "method_a": "local_stencil", "method_b": "spectral_fft", "shape": tuple(shape), "T": T,
            "dt": [p["dt"], ps["dt"]]}
