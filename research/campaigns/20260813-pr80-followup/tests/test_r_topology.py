"""Tests for ai_lab/relational/topology.py's fundamental_cycles (PR-R1.9)."""

import numpy as np
import pytest

from ai_lab.relational import topology


def _assert_valid_cycle(W, cycle):
    m = len(cycle)
    assert m >= 3
    for k in range(m):
        a, b = cycle[k], cycle[(k + 1) % m]
        assert W[a, b] > 0, "cycle edge (%d, %d) does not exist in W" % (a, b)


def test_tree_has_no_cycles():
    n = 6
    W = np.zeros((n, n))
    for i, j in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        W[i, j] = W[j, i] = 1.0
    assert topology.fundamental_cycles(W) == []


def test_single_cycle_graph_returns_exactly_one_cycle():
    n = 5
    W = np.zeros((n, n))
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    for i, j in edges:
        W[i, j] = W[j, i] = 1.0
    cycles = topology.fundamental_cycles(W)
    assert len(cycles) == 1
    assert set(cycles[0]) == set(range(n))
    _assert_valid_cycle(W, cycles[0])


def test_cycle_space_dimension_matches_e_minus_n_plus_components():
    rng = np.random.default_rng(3)
    for _ in range(20):
        n = int(rng.integers(4, 12))
        W = (rng.random((n, n)) < 0.35).astype(float)
        W = np.triu(W, k=1)
        W = W + W.T
        cycles = topology.fundamental_cycles(W)
        n_edges = int((W > 0).sum() // 2)
        # connected components via union-find on the edge set
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        iu, ju = np.triu_indices(n, k=1)
        for i, j in zip(iu, ju):
            if W[i, j] > 0:
                ri, rj = find(int(i)), find(int(j))
                if ri != rj:
                    parent[ri] = rj
        n_components = len({find(x) for x in range(n)})
        expected_dim = n_edges - n + n_components
        assert len(cycles) == expected_dim
        for c in cycles:
            _assert_valid_cycle(W, c)


def test_fundamental_cycles_unaffected_by_asymmetrization():
    """Asymmetry (PR-R1.5) only splits a per-edge weight; it must never add or remove an
    edge, so the fundamental cycle basis of W and of its asymmetrized version must match
    (as edge sets) exactly -- this is the property AUDIT.md Sec.11's analysis relies on to
    reuse the same cycle basis for the pre- and post-asymmetrization graph."""
    from ai_lab.relational import substrate

    W0 = topology.build_topology("erdos_renyi", n=14, p=0.3, seed=5)
    Wa = substrate._asymmetrize(W0, strength=2.0, seed=5)
    c0 = topology.fundamental_cycles(W0)
    ca = topology.fundamental_cycles(Wa)
    edges0 = {frozenset((c[k], c[(k + 1) % len(c)])) for c in c0 for k in range(len(c))}
    edgesa = {frozenset((c[k], c[(k + 1) % len(c)])) for c in ca for k in range(len(c))}
    assert len(c0) == len(ca)


def test_disconnected_graph_gives_one_forest_per_component():
    n = 6
    W = np.zeros((n, n))
    # component A: a 3-cycle on {0,1,2}; component B: a tree on {3,4,5}
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        W[i, j] = W[j, i] = 1.0
    for i, j in [(3, 4), (4, 5)]:
        W[i, j] = W[j, i] = 1.0
    cycles = topology.fundamental_cycles(W)
    assert len(cycles) == 1
    assert set(cycles[0]) == {0, 1, 2}
