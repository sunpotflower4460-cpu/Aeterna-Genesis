"""Track localized lumps of a (time-averaged) density field on a periodic grid, in 2D or 3D.

A measuring instrument only: it does not know what a lump "should" do.

    detect(field, thr, max_extent)  connected regions above `thr` (periodic, n-D). A region whose extent along
                                    any axis exceeds `max_extent` (a wall / membrane spanning the box) is
                                    reported separately as extended, not as a lump.
    link(prev, cur, dt, c=1, margin) nearest-neighbour matching that respects a speed limit: a lump can only be
                                    matched to one within c·dt + margin cells (nothing is linked faster than light)
    Tracker                         accumulates frames into tracks: positions, content, birth / death / split /
                                    merge counts, lifetime, net displacement and mean speed per track.

Positions are circular means per axis (so a lump sitting on the periodic edge is not torn in two), distances
are minimum-image distances.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import ndimage


def _merge_periodic(lab: np.ndarray) -> np.ndarray:
    """Join labels that touch across periodic faces (union–find on face pairs)."""
    n = int(lab.max())
    parent = list(range(n + 1))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for ax in range(lab.ndim):
        a = np.take(lab, 0, axis=ax).ravel()
        b = np.take(lab, -1, axis=ax).ravel()
        both = (a > 0) & (b > 0)
        for i, j in zip(a[both], b[both]):
            ri, rj = find(int(i)), find(int(j))
            if ri != rj:
                parent[ri] = rj
    roots = np.array([find(i) for i in range(n + 1)])
    return roots[lab]


def _circ_mean(idx: np.ndarray, n: int, w: np.ndarray) -> float:
    ang = 2 * np.pi * idx / n
    return float((np.arctan2((w * np.sin(ang)).sum(), (w * np.cos(ang)).sum()) % (2 * np.pi)) * n / (2 * np.pi))


def _extent(idx: np.ndarray, n: int) -> int:
    """Smallest periodic arc (in cells) covering the occupied indices along one axis."""
    occ = np.zeros(n, bool)
    occ[np.unique(idx)] = True
    if occ.all():
        return n
    # longest run of empty cells (periodic) -> extent = n - that run
    free = ~occ
    best = run = 0
    for v in np.concatenate([free, free]):
        run = run + 1 if v else 0
        best = max(best, min(run, n))
    return n - best


def detect(f: np.ndarray, thr: float, max_extent: int, min_size: int = 3) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (lumps, extended). Each item: pos (tuple), size (cells), content (sum of f), peak, extent."""
    lab, n = ndimage.label(f > thr)
    if n == 0:
        return [], []
    lab = _merge_periodic(lab)
    lumps, extended = [], []
    coords = np.nonzero(lab)
    labels = lab[coords]
    for r in np.unique(labels):
        sel = labels == r
        if sel.sum() < min_size:
            continue
        pts = [c[sel] for c in coords]
        w = f[tuple(pts)]
        ext = [_extent(pts[a], f.shape[a]) for a in range(f.ndim)]
        item = {"pos": tuple(_circ_mean(pts[a], f.shape[a], w) for a in range(f.ndim)), "size": int(sel.sum()),
                "content": float(w.sum()), "peak": float(w.max()), "extent": ext}
        (extended if max(ext) > max_extent else lumps).append(item)
    return lumps, extended


def pdist(a: tuple[float, ...], b: tuple[float, ...], shape: tuple[int, ...]) -> float:
    return math.sqrt(sum(min(abs(x - y), n - abs(x - y)) ** 2 for x, y, n in zip(a, b, shape)))


@dataclass
class Track:
    id: int
    t: list[float] = field(default_factory=list)
    pos: list[tuple[float, ...]] = field(default_factory=list)
    content: list[float] = field(default_factory=list)
    size: list[int] = field(default_factory=list)
    end: str = "alive"               # alive | death | merge

    def summary(self, shape: tuple[int, ...]) -> dict[str, Any]:
        life = self.t[-1] - self.t[0]
        steps = [pdist(a, b, shape) for a, b in zip(self.pos, self.pos[1:])]
        path = float(sum(steps))
        # net displacement along the path, unwrapped step by step (minimum image each step)
        disp = np.zeros(len(shape))
        for a, b in zip(self.pos, self.pos[1:]):
            d = np.array([((y - x + n / 2) % n) - n / 2 for x, y, n in zip(a, b, shape)])
            disp += d
        return {"id": self.id, "born": self.t[0], "last": self.t[-1], "lifetime": round(life, 3), "end": self.end,
                "frames": len(self.t), "path": round(path, 3), "net_displacement": round(float(np.linalg.norm(disp)), 3),
                "mean_speed": round(path / life, 4) if life > 0 else 0.0,
                "content_first": round(self.content[0], 4), "content_last": round(self.content[-1], 4),
                "mean_size": round(float(np.mean(self.size)), 2), "last_pos": [round(x, 2) for x in self.pos[-1]]}


class Tracker:
    """Link lumps frame by frame. A match must lie within c·dt + margin (speed limit c)."""

    def __init__(self, shape: tuple[int, ...], c: float = 1.0, margin: float = 2.0):
        self.shape, self.c, self.margin = tuple(shape), c, margin
        self.tracks: list[Track] = []
        self.alive: list[Track] = []
        self.events = {"birth": 0, "death": 0, "split": 0, "merge": 0}
        self._t: float | None = None

    def add(self, t: float, lumps: list[dict[str, Any]]) -> None:
        if self._t is None:
            for L in lumps:
                self._new(t, L)
            self._t = t
            return
        r = self.c * (t - self._t) + self.margin
        self._t = t
        prev = self.alive
        pairs = sorted((pdist(p.pos[-1], L["pos"], self.shape), i, j)
                       for i, p in enumerate(prev) for j, L in enumerate(lumps))
        used_p, used_c, nxt = set(), set(), []
        claims = {j: 0 for j in range(len(lumps))}
        for d, i, j in pairs:
            if d > r:
                break
            claims[j] += 1
            if i in used_p or j in used_c:
                continue
            used_p.add(i)
            used_c.add(j)
            p, L = prev[i], lumps[j]
            p.t.append(t), p.pos.append(L["pos"]), p.content.append(L["content"]), p.size.append(L["size"])
            nxt.append(p)
        # a previous lump within reach of an already-claimed current lump merged into it; otherwise it died
        for i, p in enumerate(prev):
            if i in used_p:
                continue
            near = any(pdist(p.pos[-1], lumps[j]["pos"], self.shape) <= r for j in used_c)
            p.end = "merge" if near else "death"
            self.events["merge" if near else "death"] += 1
        for j, L in enumerate(lumps):
            if j in used_c:
                continue
            near = any(pdist(prev[i].pos[-2] if len(prev[i].pos) > 1 else prev[i].pos[-1], L["pos"], self.shape) <= r
                       for i in used_p)
            self.events["split" if near else "birth"] += 1
            nxt.append(self._new(t, L))
        self.alive = nxt

    def _new(self, t: float, L: dict[str, Any]) -> Track:
        tr = Track(len(self.tracks), [t], [L["pos"]], [L["content"]], [L["size"]])
        self.tracks.append(tr)
        if self._t is None:
            self.alive.append(tr)
        return tr

    def summary(self) -> dict[str, Any]:
        return {"events": dict(self.events), "tracks": [tr.summary(self.shape) for tr in self.tracks]}
