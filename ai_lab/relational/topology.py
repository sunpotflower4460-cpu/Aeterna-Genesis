"""ai_lab/relational/topology.py -- relation-graph generators for the R-layer (spec Sec.4.4).

Produces the weighted adjacency matrix W (w_ij >= 0, symmetric, zero diagonal) that is the
`G` input of substrate.py. Nodes carry no coordinates -- only integer indices 0..N-1. Every
generator here builds a graph from a *generation rule* (a hand-set input, disclosed in
A_OR_B), never from a target structure ("make it look like X").

Hard constraint (spec Sec.4.4): a regular grid/lattice must NOT be the default topology,
because a grid hands the system distance, dimension and isotropy for free -- those are
things R9 (a later PR) is supposed to *measure*, not something PR-R1 may assume. `grid()`
exists here only as a comparison control; any caller that selects it must set
`geometry_was_given: True` in its result (substrate.run() does this automatically when
`topology="grid"`).

No external graph library (networkx) is used -- these are minimal from-scratch generators
so the R-layer has no new third-party dependency beyond numpy/scipy, which the rest of the
repo already requires.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

# Topologies selectable via the `topology` ingredient axis (spec Sec.4.3). "grid" is
# deliberately listed but excluded from DEFAULT_TOPOLOGY / this is the honesty list, not
# the default-selection list.
AVAILABLE_TOPOLOGIES = (
    "random_regular",
    "erdos_renyi",
    "watts_strogatz",
    "barabasi_albert",
    "grid",
)

# The minimal-side default per spec Sec.4.3 table. Must never be "grid".
DEFAULT_TOPOLOGY = "random_regular"

# Topologies that hand the system geometry (distance/dimension/isotropy) for free and must
# therefore raise geometry_was_given=True whenever selected (spec Sec.4.4).
GEOMETRY_GIVING_TOPOLOGIES = ("grid",)


def _symmetrize_binary(n: int, edges) -> np.ndarray:
    """Build a symmetric 0/1 adjacency matrix (zero diagonal) from an edge-index iterable."""
    w = np.zeros((n, n), dtype=float)
    for i, j in edges:
        if i == j:
            continue
        w[i, j] = 1.0
        w[j, i] = 1.0
    return w


def random_regular(n: int, degree: int, seed: Optional[int] = None) -> np.ndarray:
    """A random d-regular graph on n nodes (pairing/configuration model with rejection).

    Every node ends up with exactly `degree` neighbours (no self-loops, no multi-edges).
    This is a generation *rule* (pair random stubs), not a placed structure.
    """
    if degree < 0 or degree >= n:
        raise ValueError("random_regular: need 0 <= degree < n")
    if (n * degree) % 2 != 0:
        raise ValueError("random_regular: n * degree must be even")
    rng = np.random.default_rng(seed)
    max_attempts = 2000
    for _ in range(max_attempts):
        stubs = np.repeat(np.arange(n), degree)
        rng.shuffle(stubs)
        pairs = stubs.reshape(-1, 2)
        edge_set = set()
        ok = True
        for a, b in pairs:
            a, b = int(a), int(b)
            if a == b or (a, b) in edge_set or (b, a) in edge_set:
                ok = False
                break
            edge_set.add((a, b))
        if ok:
            return _symmetrize_binary(n, edge_set)
    raise RuntimeError(
        "random_regular: failed to build a simple d-regular graph after %d attempts "
        "(try a smaller degree or different seed)" % max_attempts
    )


def erdos_renyi(n: int, p: float, seed: Optional[int] = None) -> np.ndarray:
    """G(n, p): each of the n*(n-1)/2 possible undirected edges present independently with prob p."""
    if not (0.0 <= p <= 1.0):
        raise ValueError("erdos_renyi: p must be in [0, 1]")
    rng = np.random.default_rng(seed)
    w = np.zeros((n, n), dtype=float)
    iu = np.triu_indices(n, k=1)
    mask = rng.random(len(iu[0])) < p
    w[iu[0][mask], iu[1][mask]] = 1.0
    w[iu[1][mask], iu[0][mask]] = 1.0
    return w


def watts_strogatz(n: int, k: int, beta: float, seed: Optional[int] = None) -> np.ndarray:
    """Watts-Strogatz small-world: ring lattice (k nearest neighbours, k even) + rewiring.

    NOTE: the *construction* uses a ring as scaffolding for the generation rule, but the
    resulting graph carries no coordinates once built -- only w_ij. Node index adjacency in
    the ring is a generator detail, not a state the substrate can see (the substrate only
    ever sees W).
    """
    if k % 2 != 0 or k <= 0 or k >= n:
        raise ValueError("watts_strogatz: need 0 < k < n and k even")
    if not (0.0 <= beta <= 1.0):
        raise ValueError("watts_strogatz: beta must be in [0, 1]")
    rng = np.random.default_rng(seed)
    edge_set = set()
    for i in range(n):
        for offset in range(1, k // 2 + 1):
            j = (i + offset) % n
            a, b = (i, j) if i < j else (j, i)
            edge_set.add((a, b))
    edges = list(edge_set)
    rewired = set()
    for (a, b) in edges:
        if rng.random() < beta:
            # rewire endpoint b to a new random target != a, avoiding an existing edge
            attempts = 0
            new_b = b
            while attempts < 50:
                cand = int(rng.integers(0, n))
                key = (a, cand) if a < cand else (cand, a)
                if cand != a and key not in rewired and key not in edge_set:
                    new_b = cand
                    break
                attempts += 1
            key = (a, new_b) if a < new_b else (new_b, a)
            rewired.add(key)
        else:
            rewired.add((a, b))
    return _symmetrize_binary(n, rewired)


def barabasi_albert(n: int, m: int, seed: Optional[int] = None) -> np.ndarray:
    """Barabasi-Albert preferential attachment: start from an m-clique, grow to n nodes."""
    if m < 1 or m >= n:
        raise ValueError("barabasi_albert: need 1 <= m < n")
    rng = np.random.default_rng(seed)
    edge_set = set()
    degree = np.zeros(n, dtype=float)
    # seed clique on the first m+1 nodes
    seed_nodes = list(range(m + 1))
    for a in range(len(seed_nodes)):
        for b in range(a + 1, len(seed_nodes)):
            edge_set.add((seed_nodes[a], seed_nodes[b]))
            degree[seed_nodes[a]] += 1
            degree[seed_nodes[b]] += 1
    for new_node in range(m + 1, n):
        existing = np.arange(new_node)
        weights = degree[existing] + 1e-9
        probs = weights / weights.sum()
        targets = rng.choice(existing, size=min(m, new_node), replace=False, p=probs)
        for t in targets:
            t = int(t)
            edge_set.add((min(new_node, t), max(new_node, t)))
            degree[new_node] += 1
            degree[t] += 1
    return _symmetrize_binary(n, edge_set)


def grid(n: int, dim: int = 1, periodic: bool = False, seed: Optional[int] = None) -> np.ndarray:
    """A regular lattice -- comparison control ONLY. NOT the default (spec Sec.4.4).

    Hands the system distance/dimension/isotropy for free. Any caller selecting this must
    record geometry_was_given=True. `seed` is accepted for a uniform generator signature
    but unused (the grid is deterministic given n, dim, periodic).
    """
    del seed
    if dim == 1:
        side = n
        w = np.zeros((n, n), dtype=float)
        for i in range(n):
            j = i + 1
            if j < n:
                w[i, j] = w[j, i] = 1.0
            elif periodic and n > 2:
                w[i, 0] = w[0, i] = 1.0
        return w
    if dim == 2:
        side = int(round(np.sqrt(n)))
        if side * side != n:
            raise ValueError("grid: n must be a perfect square for dim=2")
        w = np.zeros((n, n), dtype=float)

        def idx(r, c):
            return r * side + c

        for r in range(side):
            for c in range(side):
                i = idx(r, c)
                neighbours = []
                if c + 1 < side:
                    neighbours.append(idx(r, c + 1))
                elif periodic and side > 2:
                    neighbours.append(idx(r, 0))
                if r + 1 < side:
                    neighbours.append(idx(r + 1, c))
                elif periodic and side > 2:
                    neighbours.append(idx(0, c))
                for j in neighbours:
                    w[i, j] = w[j, i] = 1.0
        return w
    raise ValueError("grid: only dim in (1, 2) implemented")


_GENERATORS = {
    "random_regular": random_regular,
    "erdos_renyi": erdos_renyi,
    "watts_strogatz": watts_strogatz,
    "barabasi_albert": barabasi_albert,
    "grid": grid,
}


def build_topology(name: str, n: int, seed: Optional[int] = None, **kwargs) -> np.ndarray:
    """Dispatch to one of the named generators. `name` must be in AVAILABLE_TOPOLOGIES."""
    if name not in _GENERATORS:
        raise ValueError(
            "unknown topology %r; available: %s" % (name, ", ".join(AVAILABLE_TOPOLOGIES))
        )
    fn = _GENERATORS[name]
    return fn(n, seed=seed, **kwargs)


def geometry_was_given(name: str) -> bool:
    """True iff selecting this topology hands the system geometry for free (spec Sec.4.4)."""
    return name in GEOMETRY_GIVING_TOPOLOGIES
