"""Vortex rings (tori) in a 3D complex field, periodic box (P11). The measure does not know whether a ring is
expected; it reports every connected vortex tangle piece and its topology.

1. `plaquette_windings(psi)`: the phase winding through every plaquette of the three planes, WITH the periodic
   wrap (unlike `plaquette_ledger`, whose arrays stop at the seam) -- where vortex lines pierce.
2. `line_mask(psi, dilate)`: the voxels at the corners of pierced plaquettes, thickened by `dilate` cells
   (periodic). A closed vortex loop becomes a solid torus, a line around the box a solid cylinder.
3. `components(mask)`: connected pieces on the torus, each walked voxel by voxel and laid out in unwrapped
   coordinates; a piece that meets itself again one box length away goes around the box (`wraps`).
4. `ring_stats(coords, L)`: topology of the unwrapped piece (`topology_betti.betti3d`: genus 1 = solid torus),
   whether it wraps the box, the centroid (mod L), principal axes (the smallest is the ring's axis n),
   flatness = smallest / largest spread, radius R = mean distance from the axis through the centroid,
   roundness = spread of that distance / R.
A piece counts as a RING if: genus 1, it does not wrap the box, flatness < 0.45, roundness < 0.35, R ≥ 2.
"""
from __future__ import annotations

import numpy as np
from collections import deque

from genesis.diagnostics.topology_betti import betti3d


def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def plaquette_windings(psi: np.ndarray) -> dict[tuple[int, int], np.ndarray]:
    ph = np.angle(psi)
    d = [_wrap(np.roll(ph, -1, ax) - ph) for ax in range(3)]
    out = {}
    for i, j in ((0, 1), (1, 2), (0, 2)):
        loop = d[i] + np.roll(d[j], -1, i) - np.roll(d[i], -1, j) - d[j]
        out[(i, j)] = np.rint(loop / (2 * np.pi)).astype(int)
    return out


def line_mask(psi: np.ndarray, dilate: int = 1, exclude: np.ndarray | None = None) -> np.ndarray:
    """exclude (optional): voxels where the phase means nothing (e.g. inside an impenetrable obstacle, where
    |ψ| ≈ 0); plaquettes touching them are ignored. None = every plaquette counts."""
    m = np.zeros(psi.shape, bool)
    for (i, j), w in plaquette_windings(psi).items():
        p = w != 0
        if exclude is not None:
            touch = exclude | np.roll(exclude, -1, i) | np.roll(exclude, -1, j) | np.roll(np.roll(exclude, -1, i), -1, j)
            p = p & ~touch
        m |= p | np.roll(p, 1, i) | np.roll(p, 1, j) | np.roll(np.roll(p, 1, i), 1, j)
    for _ in range(dilate):
        m = m | np.any([np.roll(m, s, ax) for ax in range(3) for s in (1, -1)], axis=0)
    return m


def components(mask: np.ndarray) -> list[tuple[np.ndarray, bool]]:
    """Connected pieces on the periodic box, each walked from one voxel through its 6 neighbours and laid out
    in unwrapped coordinates. `wraps` is True when the walk reaches a voxel again by a route that differs by a
    whole box length -- the piece goes around the torus (exact, whatever its size)."""
    L = np.array(mask.shape)
    todo = {tuple(int(v) for v in x) for x in np.argwhere(mask)}
    steps = [np.array(s) for s in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    out = []
    while todo:
        start = todo.pop()
        pos = {start: np.array(start)}
        queue, wraps = deque([start]), False
        while queue:
            cur = queue.popleft()
            for st in steps:
                un = pos[cur] + st
                nb = tuple(int(v) for v in un % L)
                if nb in pos:
                    if not wraps and np.any(pos[nb] != un):
                        wraps = True
                elif nb in todo:
                    todo.discard(nb)
                    pos[nb] = un
                    queue.append(nb)
        out.append((np.array(list(pos.values()), float), wraps))
    return out


def ring_stats(c: np.ndarray, L, wraps: bool = False) -> dict:
    L = np.array(L, float)
    lo = np.floor(c.min(0)).astype(int)
    shape = np.floor(c.max(0)).astype(int) - lo + 1
    local = np.zeros(tuple(shape), bool)
    local[tuple((np.floor(c).astype(int) - lo).T)] = True
    b = betti3d(local)
    cen = c.mean(0)
    X = c - cen
    ev, evec = np.linalg.eigh(X.T @ X / len(X))
    n = evec[:, 0]
    rperp = np.linalg.norm(X - np.outer(X @ n, n), axis=1)
    R = float(rperp.mean())
    stats = {"voxels": int(len(c)), "genus": b["genus"], "b1": b["b1"], "wraps": wraps,
             "centroid": [float(v) for v in cen % L], "axis": [float(v) for v in n],
             "flatness": float(np.sqrt(max(ev[0], 0) / max(ev[2], 1e-12))), "radius": R,
             "roundness": float(rperp.std() / max(R, 1e-12))}
    stats["ring"] = bool(stats["genus"] == 1 and not wraps and stats["flatness"] < 0.45
                         and stats["roundness"] < 0.35 and R >= 2.0)
    return stats


def rings(psi: np.ndarray, dilate: int = 1, exclude: np.ndarray | None = None) -> list[dict]:
    return [ring_stats(c, psi.shape, w) for c, w in components(line_mask(psi, dilate, exclude))]
