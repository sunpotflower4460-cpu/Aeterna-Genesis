"""Causal sets: order-only spacetime measures (LAW.md audit 5/7).

A causal set is a locally finite partial order. Everything here is read from the
ORDER alone -- no metric is put back in. Coordinates (when present) only
*generate* a non-trivial order via the Minkowski light cone; the measured
quantities (rank = time, interval dimension, Benincasa-Dowker action) use only
the relation matrix.

    sprinkle(N, dim, region, seed)      Poisson points in a box or causal diamond
    causal_relation(coords)             Minkowski order  R[a,b] = a precedes b
    transitive_percolation(N, p, seed)  random DAG, transitive closure via bitmask
    rank(relation)                      longest chain ending at each element (time)
    interval_dimension(relation)        Myrheim-Meyer dimension from ordering fraction
    bd_action_2d(relation)              Benincasa-Dowker 2D causal action
    ds_molecules(u, v)                  Dou-Sorkin horizon molecules (2D null coords)

THE TRAP (designer hit it, we avoid it): the transitive closure is built with a
Python-int BITMASK (each element's future set as set bits), not a repeated
boolean matrix multiply -- the bitmask is exact and cheap and cannot leave a
missed transitive edge. Sprinkling is Poisson (fluctuating count), not a fixed
grid. The Myrheim-Meyer ordering fraction uses UNORDERED pairs C(N,2), for which
the 2D expected fraction is exactly r*(2D) = 1/2 (diamond).

Floors: bd_action_2d here is the discrete BD sum up to the standard overall
factor of 2 (chosen so a chain and an antichain both give S = N); the physical
action is 2x this. The Dou-Sorkin 3D coefficient is a known DS d>2 pathology and
is a FLOOR (frontier) -- it is never a GREEN gate. "Time" for rank is analogy
for the order height, not a clock.
"""

import numpy as np
from scipy.special import gammaln
from scipy.optimize import brentq


def sprinkle(N, dim=2, region="diamond", seed=0):
    """N Poisson points; first coordinate is time.

    region='box'     : uniform in the unit box [0,1]^dim.
    region='diamond' : uniform in the unit causal interval (Alexandrov set)
                       between the origin and the apex (1, 0, ...).
    """
    rng = np.random.default_rng(seed)
    if region == "box":
        return rng.random((N, dim))
    if region != "diamond":
        raise ValueError("region must be 'box' or 'diamond'")
    out = []
    while len(out) < N:
        m = (N - len(out)) * 4 + 16
        t = rng.uniform(0.0, 1.0, m)
        if dim > 1:
            xs = rng.uniform(-0.5, 0.5, (m, dim - 1))
            rx = np.sqrt((xs ** 2).sum(1))
        else:
            xs = np.zeros((m, 0))
            rx = np.zeros(m)
        keep = (t > rx) & ((1.0 - t) > rx)               # inside future(0) AND past(apex)
        for ti, xi in zip(t[keep], xs[keep]):
            out.append(np.concatenate([[ti], xi]))
            if len(out) >= N:
                break
    return np.array(out)


def causal_relation(coords):
    """Strict Minkowski order R[a,b]: b in the open forward light cone of a."""
    t = coords[:, 0]
    x = coords[:, 1:]
    dt = t[None, :] - t[:, None]
    if x.shape[1] > 0:
        dx2 = ((x[None, :, :] - x[:, None, :]) ** 2).sum(2)
    else:
        dx2 = np.zeros_like(dt)
    R = (dt > 0) & (dt ** 2 > dx2)
    np.fill_diagonal(R, False)
    return R


def transitive_percolation(N, p, seed=0):
    """Transitive percolation DAG on N labelled elements (0..N-1 is a time order).

    Each pair i<j is linked with probability p; the transitive closure is built
    with a per-element bitmask future set (exact, no missed edge). Returns the
    boolean relation (already transitively closed).
    """
    rng = np.random.default_rng(seed)
    future = [0] * N                                     # bitmask of descendants
    for i in range(N - 1, -1, -1):
        f = 0
        for j in range(i + 1, N):
            if rng.random() < p:
                f |= (1 << j) | future[j]                 # j and everything after j
        future[i] = f
    R = np.zeros((N, N), bool)
    for i in range(N):
        f = future[i]
        j = 0
        while f:
            if f & 1:
                R[i, j] = True
            f >>= 1
            j += 1
    return R


def rank(relation):
    """Longest chain ending at each element (order height = emergent time).

    Elements are processed in a valid topological order: in a transitively
    closed relation a<b implies ancestors(a) subset ancestors(b), so ascending
    ancestor count is a linear extension.
    """
    N = relation.shape[0]
    order = np.argsort(relation.sum(0))                  # fewest ancestors first
    r = np.zeros(N, int)
    for b in order:
        preds = np.where(relation[:, b])[0]
        r[b] = 0 if preds.size == 0 else 1 + int(r[preds].max())
    return r


def _mm_fraction_theory(d):
    """Myrheim-Meyer expected related-pair fraction in a d-dim interval (denom 2)."""
    return float(np.exp(gammaln(d + 1) + gammaln(d / 2.0)
                        - np.log(2.0) - gammaln(3.0 * d / 2.0)))


def interval_dimension(relation):
    """Myrheim-Meyer dimension from the unordered ordering fraction.

    r = (# related pairs) / C(N,2); invert r(d). For a 2D causal diamond the
    theory value is r*(2D) = 1/2, so a 2D sprinkling returns ~2.
    """
    N = relation.shape[0]
    if N < 2:
        return float("nan")
    r = int(relation.sum()) / (N * (N - 1) / 2.0)
    try:
        return float(brentq(lambda d: _mm_fraction_theory(d) - r, 1.0, 9.0))
    except ValueError:
        return float("nan")


def bd_action_2d(relation):
    """Benincasa-Dowker 2D causal action (up to the standard overall factor 2).

    S = N - 2 n0 + 4 n1 - 2 n2, where n_k is the number of related pairs with
    exactly k elements strictly between them (the interval cardinality
    (R @ R)[i, j]). Exact special cases: chain S = N, antichain S = N,
    complete bilayer S = N - N^2 / 2.
    """
    N = relation.shape[0]
    Rf = relation.astype(np.int64)
    between = Rf @ Rf                                     # between[i,j] = |{k: i<k<j}|
    m = between[relation]                                 # only over related pairs
    n0 = int(np.count_nonzero(m == 0))
    n1 = int(np.count_nonzero(m == 1))
    n2 = int(np.count_nonzero(m == 2))
    return N - 2 * n0 + 4 * n1 - 2 * n2


def ds_molecules(u, v):
    """Dou-Sorkin horizon molecules from 2D null coordinates (u, v).

    A molecule is a maximal element just above the horizon (v>0) whose past
    below the horizon (u<0, v<0) has a single minimal partner -- the discrete
    analogue of the horizon-crossing links that meter the area. Returns the
    molecule count. (The 3D coefficient is a DS d>2 pathology = FLOOR.)
    """
    P = np.where(v > 0)[0]
    if P.size == 0:
        return 0
    order = P[np.argsort(u[P])]
    ymin, run = [], np.inf
    for i in order:
        if v[i] < run:
            ymin.append(i)
            run = v[i]
    c = 0
    for yi in ymin:
        if u[yi] <= 0:
            continue
        S = np.where((u < u[yi]) & (v < v[yi]))[0]
        if S.size == 0:
            continue
        order2 = S[np.argsort(-u[S])]
        rm = -np.inf
        for xi in order2:
            if v[xi] > rm:
                if u[xi] < 0 and v[xi] < 0:
                    c += 1
                rm = v[xi]
    return c
