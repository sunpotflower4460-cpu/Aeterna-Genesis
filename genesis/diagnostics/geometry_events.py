"""Observation-only geometry diagnostics for spontaneous vortex arrangements.

These diagnostics NEVER change emergence Levels or success thresholds.  They only ask a new
question of already-emerging fields: when three naturally formed vortices arrange in a robust
triangle, does the nearby vortex cluster later separate into two or more persistent groups?

The triangle is never seeded.  Calling the later change "fission-like" is deliberately cautious:
it is a field-geometry event, not a claim of biological cell division.
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
        amp
        + np.roll(amp, -1, 0)
        + np.roll(np.roll(amp, -1, 0), -1, 1)
        + np.roll(amp, -1, 1)
    )
    mask = (winding != 0) & (mean4 > thr)
    out: list[dict[str, Any]] = []
    for y, x in np.argwhere(mask):
        out.append({"y": float(y) + 0.5, "x": float(x) + 0.5, "charge": int(winding[y, x])})
    return out


def _periodic_delta(a: float, b: float, size: float) -> float:
    d = abs(float(a) - float(b))
    return min(d, size - d)


def periodic_distance(a: dict[str, Any], b: dict[str, Any], shape: tuple[int, int]) -> float:
    dy = _periodic_delta(a["y"], b["y"], float(shape[0]))
    dx = _periodic_delta(a["x"], b["x"], float(shape[1]))
    return float(math.hypot(dy, dx))


def _triangle_metrics(points: list[dict[str, Any]], ids: tuple[int, int, int], shape: tuple[int, int]) -> dict[str, Any]:
    p = [points[i] for i in ids]
    sides = [periodic_distance(p[0], p[1], shape), periodic_distance(p[1], p[2], shape), periodic_distance(p[2], p[0], shape)]
    sides.sort()
    a, b, c = sides
    s = 0.5 * (a + b + c)
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    regularity = a / max(c, 1e-9)
    area_ratio = area / max(c * c, 1e-9)
    charges = [int(x["charge"]) for x in p]
    return {
        "indices": list(ids),
        "side_lengths": [round(x, 4) for x in sides],
        "regularity": round(regularity, 4),
        "area": round(area, 4),
        "area_ratio": round(area_ratio, 4),
        "charge_pattern": "".join("+" if q > 0 else "-" for q in sorted(charges, reverse=True)),
        "max_side": round(c, 4),
    }


def best_triangle(points: list[dict[str, Any]], shape: tuple[int, int]) -> dict[str, Any] | None:
    """Find a local, non-collinear, roughly balanced three-vortex arrangement.

    Any three points mathematically form a triangle, so the detector intentionally requires a
    meaningful geometry: not almost collinear, not spanning most of the periodic box, and with no
    side dramatically shorter than the others.  This definition is observation metadata only.
    """
    if len(points) < 3:
        return None
    candidate_ids: set[tuple[int, int, int]] = set()
    for i, p in enumerate(points):
        neighbours = sorted(
            ((periodic_distance(p, q, shape), j) for j, q in enumerate(points) if j != i),
            key=lambda x: x[0],
        )[:8]
        ids = [j for _, j in neighbours]
        for j, k in itertools.combinations(ids, 2):
            candidate_ids.add(tuple(sorted((i, j, k))))
    best = None
    best_score = -1.0
    for ids in candidate_ids:
        m = _triangle_metrics(points, ids, shape)
        max_side = float(m["max_side"])
        if max_side > 0.45 * min(shape) or float(m["area_ratio"]) < 0.18:
            continue
        score = float(m["regularity"]) * min(1.0, float(m["area_ratio"]) / 0.35)
        if score > best_score:
            best_score = score
            best = {**m, "triangle_score": round(score, 4)}
    if best is None:
        return None
    best["qualified"] = bool(float(best["regularity"]) >= 0.65 and float(best["area_ratio"]) >= 0.22)
    ids = best["indices"]
    # Circular mean is unnecessary for a local triangle once the max-side bound is applied; use a
    # reference-unwrapped centroid so points near a periodic edge do not average to the box centre.
    ref = points[ids[0]]
    ys, xs = [float(ref["y"])], [float(ref["x"])]
    for idx in ids[1:]:
        p = points[idx]
        for key, vals, size in (("y", ys, shape[0]), ("x", xs, shape[1])):
            raw = float(p[key])
            base = vals[0]
            choices = (raw - size, raw, raw + size)
            vals.append(min(choices, key=lambda v: abs(v - base)))
    best["centroid"] = {"y": round(float(np.mean(ys)) % shape[0], 4), "x": round(float(np.mean(xs)) % shape[1], 4)}
    return best


def local_cluster_count(
    points: list[dict[str, Any]],
    *,
    centre: dict[str, float],
    shape: tuple[int, int],
    neighbourhood_radius: float,
    link_radius: float,
) -> dict[str, int]:
    """Count connected vortex groups near a remembered triangle centre."""
    centre_point = {"y": centre["y"], "x": centre["x"]}
    local = [p for p in points if periodic_distance(p, centre_point, shape) <= neighbourhood_radius]
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
