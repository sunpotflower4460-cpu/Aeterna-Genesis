"""Measures for replicator spots and their containers (P17). A spot belongs to at most ONE container: the one holding
more than half of its voxels. protocell.containers (P15) counts a spot for every container it touches; these
measures do not, so a spot straddling a wall or clipping a neighbour is counted once. The measure knows nothing of
the result (it only labels and counts)."""
from __future__ import annotations

import numpy as np


def inside_shares(spots, box):
    """For each labelled spot, the share of its voxels inside any container (box). Outside: share <= 0.5."""
    vox = np.bincount(spots.ravel())
    inside = np.bincount(spots[box].ravel(), minlength=vox.size)[1:] / np.maximum(vox[1:], 1)
    return inside[vox[1:] > 0]


def assignment(spots, lab):
    """{spot id: container id or 0}: the container holding more than half of the spot's voxels, else 0."""
    n_c = int(lab.max())
    s_ids, s_inv = np.unique(spots.ravel(), return_inverse=True)
    size = np.bincount(s_inv)
    pair = np.bincount(s_inv * (n_c + 1) + lab.ravel(), minlength=s_ids.size * (n_c + 1)).reshape(s_ids.size, n_c + 1)
    out = {}
    for j, sid in enumerate(s_ids):
        if sid == 0:
            continue
        row = pair[j].copy()
        row[0] = 0
        best = int(np.argmax(row))
        out[int(sid)] = best if row[best] * 2 > size[j] else 0
    return out


def assign_spots(spots, lab):
    """(per-container number of assigned spots for every container id in lab, number of unassigned spots)."""
    a = assignment(spots, lab)
    per = {int(i): 0 for i in np.unique(lab) if i}
    for c in a.values():
        if c:
            per[c] += 1
    return per, sum(1 for c in a.values() if c == 0)


def spot_kinds(spots, lab, V1, V):
    """{container id: share of kind 1 over the whole spots assigned to it} for containers with >= 1 assigned spot.
    The kind is read from the spots themselves (all their voxels), not from what happens to lie inside the wall."""
    a = assignment(spots, lab)
    s1 = np.bincount(spots.ravel(), V1.ravel())
    sv = np.bincount(spots.ravel(), V.ravel())
    k1: dict = {}
    kv: dict = {}
    for sid, c in a.items():
        if c:
            k1[c] = k1.get(c, 0.0) + s1[sid]
            kv[c] = kv.get(c, 0.0) + sv[sid]
    return {c: float(k1[c] / max(kv[c], 1e-12)) for c in k1}
