"""Observation-only geometry diagnostics for spontaneous vortex arrangements.

These diagnostics NEVER change emergence Levels or success thresholds. They ask a separate
question: when an isolated local group of three naturally formed vortices persists in a balanced
triangle, is a later split of that local group more common than after a non-triangular three-vortex
control arrangement?

The triangle is never seeded. "Fission-like" is field geometry, not biological cell division.
"""
from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np


def vortex_points_2d(psi: np.ndarray) -> list[dict[str, Any]]:
    """Return measured 2D vortex plaquette centres and winding charges (+1/-1)."""
    if psi.ndim != 2:
        raise ValueError("vortex_points_2d expects a 2D complex field")
    # A purely real field has phase only 0/pi and cannot carry a true 2*pi vortex. Exclude the known
    # domain-wall winding artifact from geometry research instead of turning it into a false discovery.
    if float(np.max(np.abs(psi.imag))) <= 1e-14:
        return []
    theta = np.angle(psi)
    amp = np.abs(psi)
    thr = 0.25 * float(amp.max()) if amp.size else 0.0

    def wrap(x):
        return (x + np.pi) % (2 * np.pi) - np.pi

    a = theta
    b = np.roll(theta, -1, 0)
    c = np.roll(np.roll(theta, -1, 0), -1, 1)
    d = np.roll(theta, -1, 1)
    circ = wrap(b - a) + wrap(c - b) + wrap(d - c) + wrap(a - d)
    winding = np.round(circ / (2 * np.pi)).astype(int)
    mean4 = 0.25 * (
        amp + np.roll(amp, -1, 0)
        + np.roll(np.roll(amp, -1, 0), -1, 1)
        + np.roll(amp, -1, 1)
    )
    mask = (winding != 0) & (mean4 > thr)
    return [
        {"y": float(y) + 0.5, "x": float(x) + 0.5, "charge": int(winding[y, x])}
        for y, x in np.argwhere(mask)
    ]


def _periodic_delta(a: float, b: float, size: float) -> float:
    d = abs(float(a) - float(b))
    return min(d, size - d)


def periodic_distance(a: dict[str, Any], b: dict[str, Any], shape: tuple[int, int]) -> float:
    return float(math.hypot(
        _periodic_delta(a["y"], b["y"], float(shape[0])),
        _periodic_delta(a["x"], b["x"], float(shape[1])),
    ))


def _nearest_ids(points: list[dict[str, Any]], i: int, shape: tuple[int, int], k: int = 2) -> list[int]:
    return [
        j for _, j in sorted(
            ((periodic_distance(points[i], q, shape), j) for j, q in enumerate(points) if j != i),
            key=lambda x: x[0],
        )[:k]
    ]


def _mutual_nearest_triad(points: list[dict[str, Any]], ids: tuple[int, int, int], shape: tuple[int, int]) -> bool:
    """Require each member's two nearest vortices to be the other two members.

    This prevents a dense cloud with dozens of vortices from producing an "interesting triangle"
    merely because some arbitrary combination of three happens to look equilateral.
    """
    target = set(ids)
    return all(set(_nearest_ids(points, i, shape, 2)) == (target - {i}) for i in ids)


def _centroid(points: list[dict[str, Any]], ids: tuple[int, int, int], shape: tuple[int, int]) -> dict[str, float]:
    ref = points[ids[0]]
    ys, xs = [float(ref["y"])], [float(ref["x"])]
    for idx in ids[1:]:
        p = points[idx]
        for key, vals, size in (("y", ys, shape[0]), ("x", xs, shape[1])):
            raw = float(p[key])
            base = vals[0]
            vals.append(min((raw - size, raw, raw + size), key=lambda v: abs(v - base)))
    return {"y": round(float(np.mean(ys)) % shape[0], 4), "x": round(float(np.mean(xs)) % shape[1], 4)}


def _triad_metrics(points: list[dict[str, Any]], ids: tuple[int, int, int], shape: tuple[int, int]) -> dict[str, Any]:
    p = [points[i] for i in ids]
    sides = sorted([
        periodic_distance(p[0], p[1], shape),
        periodic_distance(p[1], p[2], shape),
        periodic_distance(p[2], p[0], shape),
    ])
    a, b, c = sides
    s = 0.5 * (a + b + c)
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    regularity = a / max(c, 1e-9)
    area_ratio = area / max(c * c, 1e-9)
    charges = [int(x["charge"]) for x in p]
    score = regularity * min(1.0, area_ratio / 0.35)
    return {
        "indices": list(ids),
        "side_lengths": [round(x, 4) for x in sides],
        "regularity": round(regularity, 4),
        "area": round(area, 4),
        "area_ratio": round(area_ratio, 4),
        "charge_pattern": "".join("+" if q > 0 else "-" for q in sorted(charges, reverse=True)),
        "max_side": round(c, 4),
        "triangle_score": round(score, 4),
        "mutual_nearest": True,
        "centroid": _centroid(points, ids, shape),
    }


def _mutual_triad_candidates(points: list[dict[str, Any]], shape: tuple[int, int]) -> list[dict[str, Any]]:
    if len(points) < 3:
        return []
    ids_seen: set[tuple[int, int, int]] = set()
    out: list[dict[str, Any]] = []
    for i in range(len(points)):
        nearest = _nearest_ids(points, i, shape, 2)
        if len(nearest) < 2:
            continue
        ids = tuple(sorted((i, nearest[0], nearest[1])))
        if ids in ids_seen:
            continue
        ids_seen.add(ids)
        if not _mutual_nearest_triad(points, ids, shape):
            continue
        m = _triad_metrics(points, ids, shape)
        if float(m["max_side"]) <= 0.35 * min(shape):
            out.append(m)
    return out


def best_mutual_triad(points: list[dict[str, Any]], shape: tuple[int, int]) -> dict[str, Any] | None:
    """Return the strongest local mutual-nearest triad without deciding that it is a triangle.

    This is useful for observing a relation continuously while its geometry changes.  It deliberately
    has no triangle/control threshold and therefore cannot by itself support either hypothesis.
    """
    candidates = _mutual_triad_candidates(points, shape)
    if not candidates:
        return None
    best = max(candidates, key=lambda m: float(m["triangle_score"]))
    return {**best, "qualified": True, "kind": "mutual"}


def best_triangle(points: list[dict[str, Any]], shape: tuple[int, int]) -> dict[str, Any] | None:
    """Return the best isolated/mutual local three-vortex triangle, if one exists."""
    candidates = _mutual_triad_candidates(points, shape)
    qualified = [
        m for m in candidates
        if float(m["regularity"]) >= 0.72 and float(m["area_ratio"]) >= 0.25
    ]
    if not qualified:
        return None
    best = max(qualified, key=lambda m: float(m["triangle_score"]))
    return {**best, "qualified": True, "kind": "triangle"}


def best_control_triad(points: list[dict[str, Any]], shape: tuple[int, int]) -> dict[str, Any] | None:
    """Return an isolated/mutual three-vortex arrangement that is clearly NOT triangle-like.

    This gives the triangle hypothesis a matched geometry control rather than treating every
    triangle-followed split as support by itself.
    """
    candidates = _mutual_triad_candidates(points, shape)
    controls = [
        m for m in candidates
        if float(m["regularity"]) <= 0.55 or float(m["area_ratio"]) <= 0.16
    ]
    if not controls:
        return None
    # Pick the most clearly non-triangular local triad.
    best = min(controls, key=lambda m: float(m["triangle_score"]))
    return {**best, "qualified": True, "kind": "control"}


def same_local_triad(a: dict[str, Any], b: dict[str, Any], shape: tuple[int, int]) -> bool:
    """Loose persistence match for triads in consecutive snapshots."""
    if not a or not b or a.get("kind") != b.get("kind"):
        return False
    max_side = max(float(a.get("max_side") or 1.0), float(b.get("max_side") or 1.0))
    return periodic_distance(a["centroid"], b["centroid"], shape) <= max(2.0, 0.60 * max_side)


def local_cluster_count(
    points: list[dict[str, Any]], *, centre: dict[str, float], shape: tuple[int, int],
    neighbourhood_radius: float, link_radius: float,
) -> dict[str, int]:
    """Count connected vortex groups near a remembered triad centre."""
    local = [p for p in points if periodic_distance(p, centre, shape) <= neighbourhood_radius]
    n = len(local)
    if n == 0:
        return {"local_vortices": 0, "clusters": 0}
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if periodic_distance(local[i], local[j], shape) <= link_radius:
                union(i, j)
    return {"local_vortices": n, "clusters": len({find(i) for i in range(n)})}
