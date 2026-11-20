"""Dense components and periodic winding directly from stored particle coordinates."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class Components:
    labels: np.ndarray
    sizes: np.ndarray
    winding_axes: tuple[tuple[str, ...], ...]


def neighbors(encoded, length, radius):
    # Midpoints have a common half-bin offset, which cancels in pair differences.
    # Query a superset, then use squared integer distances for the registered cuts.
    limit = math.sqrt(cutoff_squared(radius, length)) + 1
    edges = cKDTree(encoded, boxsize=65536).query_pairs(limit, output_type="ndarray")
    delta = encoded[edges[:, 1]].astype(np.int32) - encoded[edges[:, 0]]
    jumps = -((delta + 32768) // 65536)
    minimum = delta + 65536 * jumps
    return edges, jumps, np.sum(minimum**2, axis=1, dtype=np.int64)


def cutoff_squared(radius, length):
    bins = 65536 * Fraction(str(radius)) / Fraction(str(length))
    return bins.numerator**2 // bins.denominator**2


def periodic_roots(n_atoms, edges, jumps):
    """Contract non-seam edges, then detect inconsistent lifts on the seam graph."""
    seam = jumps.any(axis=1)
    ordinary = edges[~seam]
    graph = coo_matrix((np.ones(len(ordinary), dtype=np.uint8), ordinary.T),
                       shape=(n_atoms, n_atoms)).tocsr()
    count, open_labels = connected_components(graph, directed=False)
    roots = np.arange(count)
    winding = np.zeros((count, 3), dtype=bool)
    linked = defaultdict(list)
    boundary = np.column_stack((open_labels[edges[seam]], jumps[seam]))
    for source, target, dx, dy, dz in np.unique(boundary, axis=0).tolist():
        linked[source].append((target, (dx, dy, dz)))
        linked[target].append((source, (-dx, -dy, -dz)))

    lift = {}
    for root in linked:
        if root in lift:
            continue
        lift[root] = (0, 0, 0)
        queue = [root]
        for current in queue:
            for target, jump in linked[current]:
                implied = tuple(a + b for a, b in zip(lift[current], jump))
                if target not in lift:
                    lift[target] = implied
                    roots[target] = root
                    queue.append(target)
                else:
                    winding[root] |= [a != b for a, b in zip(lift[target], implied)]
    return roots[open_labels], winding


def components(n_atoms, nearby, scheme, length, minimum_atoms):
    edges, jumps, radius_squared = nearby
    close = radius_squared <= cutoff_squared(scheme["radius"], length)
    edges, jumps = edges[close], jumps[close]
    coordinated = np.bincount(edges.ravel(), minlength=n_atoms) >= scheme["coordination"]
    active = np.flatnonzero(coordinated)
    use = np.all(coordinated[edges], axis=1)
    roots, winding = periodic_roots(n_atoms, edges[use], jumps[use])
    sizes = np.bincount(roots[active], minlength=len(winding))
    selected = np.flatnonzero(sizes >= minimum_atoms)
    # Rank equal-sized components by their smallest immutable atom ID.
    first = np.full(len(sizes), n_atoms, dtype=int)
    np.minimum.at(first, roots[active], active)
    selected = selected[np.lexsort((first[selected], -sizes[selected]))]
    rank = np.full(len(sizes), -1, dtype=np.int16)
    rank[selected] = np.arange(len(selected))
    membership = np.full(n_atoms, -1, dtype=np.int16)
    membership[active] = rank[roots[active]]
    axes = tuple(tuple(axis for axis, wraps in zip("xyz", winding[root]) if wraps) for root in selected)
    return Components(membership, sizes[selected], axes)


def histories(positions, length, schemes, minimum_atoms):
    radius = max(scheme["radius"] for scheme in schemes.values())
    result = {name: [] for name in schemes}
    for snapshot in positions:
        nearby = neighbors(snapshot, length, radius)
        for name, scheme in schemes.items():
            result[name].append(components(len(snapshot), nearby, scheme, length, minimum_atoms))
    return result
