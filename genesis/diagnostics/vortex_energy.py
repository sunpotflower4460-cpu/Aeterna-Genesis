"""Observation-only local energy diagnostics around naturally occurring vortex relations.

This module never changes dynamics, places vortices, seeds pairs/triads, or changes any science gate.
It measures the instantaneous Ginzburg-Landau free-energy landscape *after* a relation is observed.

For g001 TDGL the instantaneous density is

    f = -eps(t)|psi|^2/2 + |psi|^4/4 + Du |grad psi|^2/2

using the same forward-difference gradient convention as ``ginzburg_landau.free_energy``.  We also
retain the quench-independent density used by the legacy whole-field diagnostic.

Regions are defined only from measured vortex positions:
- each vortex core: fixed radius in reference coherence-length units;
- pair bridge: a capsule around the measured shortest periodic segment;
- triad interior: the measured periodic triangle interior;
- triad edges: capsules around the three measured sides;
- local envelope and an outer annulus around the measured group centroid.

All outputs are descriptive observations.  In particular, an energy minimum/contrast/asymmetry is not
called a binding energy, force, causal mechanism, or universal law without separate perturbation and
numerical-integrity tests.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from genesis.models import ginzburg_landau as gl


def instantaneous_energy_density(psi: np.ndarray, t: float, p: dict[str, Any]) -> dict[str, np.ndarray]:
    """Return local GL energy-density components for the instantaneous TDGL parameters."""
    if psi.ndim != 2:
        raise ValueError("local vortex-energy diagnostics currently require a 2D complex field")
    amp2 = np.abs(psi) ** 2
    quartic = 0.25 * amp2 * amp2
    eps = float(gl.eps_of_t(float(t), p))
    quadratic = -0.5 * eps * amp2
    grad2 = np.zeros_like(amp2, dtype=float)
    for ax in range(psi.ndim):
        d = np.roll(psi, -1, axis=ax) - psi
        grad2 += np.abs(d) ** 2
    gradient = 0.5 * float(p["Du"]) * grad2
    total = quadratic + quartic + gradient
    quench_independent = quartic + gradient
    return {
        "quadratic": np.asarray(quadratic, dtype=float),
        "quartic": np.asarray(quartic, dtype=float),
        "gradient": np.asarray(gradient, dtype=float),
        "total": np.asarray(total, dtype=float),
        "quench_independent": np.asarray(quench_independent, dtype=float),
    }


def reference_coherence_length(p: dict[str, Any]) -> float:
    """Predeclared reference length sqrt(Du/eps_final), not fitted to an observed relation."""
    return float(math.sqrt(max(float(p["Du"]), 1e-12) / max(abs(float(p["eps_final"])), 1e-12)))


def _periodic_signed_delta(values: np.ndarray, centre: float, size: int) -> np.ndarray:
    return (values - float(centre) + 0.5 * float(size)) % float(size) - 0.5 * float(size)


def _grid_relative_to(centre: dict[str, float], shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.indices(shape, dtype=float)
    # Vortices are reported at plaquette centres (n + 0.5), so sample cell centres consistently.
    yy += 0.5
    xx += 0.5
    return (
        _periodic_signed_delta(yy, float(centre["y"]), shape[0]),
        _periodic_signed_delta(xx, float(centre["x"]), shape[1]),
    )


def _disk_mask(centre: dict[str, float], radius: float, shape: tuple[int, int]) -> np.ndarray:
    dy, dx = _grid_relative_to(centre, shape)
    return dy * dy + dx * dx <= float(radius) ** 2


def _annulus_mask(centre: dict[str, float], r0: float, r1: float, shape: tuple[int, int]) -> np.ndarray:
    dy, dx = _grid_relative_to(centre, shape)
    r2 = dy * dy + dx * dx
    return (r2 >= float(r0) ** 2) & (r2 <= float(r1) ** 2)


def _unwrap_point(point: dict[str, float], ref: dict[str, float], shape: tuple[int, int]) -> np.ndarray:
    dy = ((float(point["y"]) - float(ref["y"]) + 0.5 * shape[0]) % shape[0]) - 0.5 * shape[0]
    dx = ((float(point["x"]) - float(ref["x"]) + 0.5 * shape[1]) % shape[1]) - 0.5 * shape[1]
    return np.asarray([dy, dx], dtype=float)


def _segment_capsule_mask(
    a: dict[str, float], b: dict[str, float], *, width: float, shape: tuple[int, int]
) -> np.ndarray:
    """Mask cells within ``width`` of the shortest periodic a->b segment."""
    dy, dx = _grid_relative_to(a, shape)
    qy, qx = _unwrap_point(b, a, shape)
    denom = qy * qy + qx * qx
    if denom <= 1e-18:
        return dy * dy + dx * dx <= float(width) ** 2
    u = np.clip((dy * qy + dx * qx) / denom, 0.0, 1.0)
    py = u * qy
    px = u * qx
    d2 = (dy - py) ** 2 + (dx - px) ** 2
    return d2 <= float(width) ** 2


def _triangle_mask(vertices: list[dict[str, float]], shape: tuple[int, int]) -> np.ndarray:
    if len(vertices) != 3:
        raise ValueError("triangle mask requires exactly three vertices")
    ref = vertices[0]
    a = np.asarray([0.0, 0.0])
    b = _unwrap_point(vertices[1], ref, shape)
    c = _unwrap_point(vertices[2], ref, shape)
    dy, dx = _grid_relative_to(ref, shape)
    p = np.stack([dy, dx], axis=-1)
    v0 = b - a
    v1 = c - a
    den = float(v0[0] * v1[1] - v1[0] * v0[1])
    if abs(den) <= 1e-12:
        return np.zeros(shape, dtype=bool)
    rel = p - a
    # Solve p = u*v0 + v*v1; tolerate half-cell boundary noise.
    u = (rel[..., 0] * v1[1] - v1[0] * rel[..., 1]) / den
    v = (v0[0] * rel[..., 1] - rel[..., 0] * v0[1]) / den
    tol = 1e-9
    return (u >= -tol) & (v >= -tol) & (u + v <= 1.0 + tol)


def _masked_stats(field: np.ndarray, mask: np.ndarray) -> dict[str, float | int | None]:
    n = int(np.count_nonzero(mask))
    if n == 0:
        return {"cells": 0, "mean": None, "sum": None, "std": None}
    values = np.asarray(field[mask], dtype=float)
    return {
        "cells": n,
        "mean": float(np.mean(values)),
        "sum": float(np.sum(values)),
        "std": float(np.std(values)),
    }


def _region_components(density: dict[str, np.ndarray], mask: np.ndarray) -> dict[str, Any]:
    return {name: _masked_stats(values, mask) for name, values in density.items()}


def _asymmetry(values: Iterable[float | None]) -> dict[str, float | None]:
    a = np.asarray([float(x) for x in values if x is not None and math.isfinite(float(x))], dtype=float)
    if len(a) < 2:
        return {"std": None, "range": None, "normalized_range": None, "cv_abs": None}
    mean_abs = float(np.mean(np.abs(a)))
    return {
        "std": float(np.std(a)),
        "range": float(np.max(a) - np.min(a)),
        "normalized_range": float((np.max(a) - np.min(a)) / max(mean_abs, 1e-12)),
        "cv_abs": float(np.std(a) / max(mean_abs, 1e-12)),
    }


def _mean_of(region: dict[str, Any], component: str = "total") -> float | None:
    return region.get(component, {}).get("mean")


def _contrast(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return float(a - b)


def relation_energy_landscape(
    psi: np.ndarray,
    *,
    t: float,
    p: dict[str, Any],
    points: list[dict[str, Any]],
    relation: dict[str, Any],
    shape: tuple[int, int],
) -> dict[str, Any] | None:
    """Measure local energy around an observed 2- or 3-vortex relation.

    ``relation`` must contain measured ``indices`` pointing into ``points``.  No relation is inferred
    from energy, preventing an energy diagnostic from feeding back into relation selection.
    """
    ids = [int(i) for i in relation.get("indices") or []]
    if len(ids) not in {2, 3} or any(i < 0 or i >= len(points) for i in ids):
        return None
    vertices = [points[i] for i in ids]
    density = instantaneous_energy_density(psi, t, p)
    xi = reference_coherence_length(p)
    core_radius = max(1.25, 2.0 * xi)
    # Relation geometry determines only the observation window, never the dynamics.
    sides = []
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            d = _unwrap_point(vertices[j], vertices[i], shape)
            sides.append(float(np.linalg.norm(d)))
    max_side = max(sides) if sides else core_radius
    centroid = relation.get("centroid")
    if not centroid:
        # Pairs use a periodic midpoint; triads should already carry a measured centroid.
        ref = vertices[0]
        offsets = [_unwrap_point(v, ref, shape) for v in vertices]
        mean = np.mean(np.stack(offsets, axis=0), axis=0)
        centroid = {
            "y": float((float(ref["y"]) + mean[0]) % shape[0]),
            "x": float((float(ref["x"]) + mean[1]) % shape[1]),
        }

    envelope_radius = max(2.5 * core_radius, 0.80 * max_side + core_radius)
    outer0 = envelope_radius
    outer1 = min(0.45 * min(shape), envelope_radius + max(2.0 * core_radius, 0.45 * max_side))
    if outer1 <= outer0 + 0.5:
        outer1 = outer0 + 1.0

    core_masks = [_disk_mask(v, core_radius, shape) for v in vertices]
    core_regions = [_region_components(density, m) for m in core_masks]
    envelope_mask = _disk_mask(centroid, envelope_radius, shape)
    outer_mask = _annulus_mask(centroid, outer0, outer1, shape)
    envelope = _region_components(density, envelope_mask)
    outer = _region_components(density, outer_mask)

    total_core_means = [_mean_of(x, "total") for x in core_regions]
    gradient_core_means = [_mean_of(x, "gradient") for x in core_regions]
    charge_pattern = "".join("+" if int(v.get("charge", 0)) > 0 else "-" for v in vertices)

    result: dict[str, Any] = {
        "version": 1,
        "relation_size": len(vertices),
        "relation_kind": relation.get("kind") or ("pair" if len(vertices) == 2 else "triad"),
        "charge_pattern_ordered": charge_pattern,
        "reference_coherence_length": xi,
        "core_radius": core_radius,
        "max_side": max_side,
        "centroid": centroid,
        "instantaneous_eps": float(gl.eps_of_t(float(t), p)),
        "physical_time": float(t),
        "cores": core_regions,
        "envelope": envelope,
        "outer_ring": outer,
        "vertex_total_energy_asymmetry": _asymmetry(total_core_means),
        "vertex_gradient_energy_asymmetry": _asymmetry(gradient_core_means),
        "envelope_minus_outer_total_mean": _contrast(_mean_of(envelope), _mean_of(outer)),
        "measurement_only": True,
        "binding_energy_claim": False,
        "force_claim": False,
    }

    if len(vertices) == 2:
        bridge_width = max(1.25, 1.5 * xi)
        bridge_mask = _segment_capsule_mask(vertices[0], vertices[1], width=bridge_width, shape=shape)
        # Exclude the two core disks so the bridge describes the field between the vortices.
        bridge_only = bridge_mask & ~core_masks[0] & ~core_masks[1]
        bridge = _region_components(density, bridge_only)
        result.update({
            "pair_separation": sides[0] if sides else 0.0,
            "bridge_width": bridge_width,
            "bridge": bridge,
            "bridge_minus_outer_total_mean": _contrast(_mean_of(bridge), _mean_of(outer)),
            "bridge_minus_outer_gradient_mean": _contrast(_mean_of(bridge, "gradient"), _mean_of(outer, "gradient")),
        })
    else:
        interior_mask = _triangle_mask(vertices, shape)
        # Keep a true interior statistic separate from vortex cores.
        for cm in core_masks:
            interior_mask &= ~cm
        edge_width = max(1.0, 1.25 * xi)
        edge_mask = np.zeros(shape, dtype=bool)
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edge_mask |= _segment_capsule_mask(vertices[i], vertices[j], width=edge_width, shape=shape)
        for cm in core_masks:
            edge_mask &= ~cm
        interior = _region_components(density, interior_mask)
        edges = _region_components(density, edge_mask)
        result.update({
            "interior": interior,
            "edges": edges,
            "edge_width": edge_width,
            "interior_minus_outer_total_mean": _contrast(_mean_of(interior), _mean_of(outer)),
            "interior_minus_outer_gradient_mean": _contrast(_mean_of(interior, "gradient"), _mean_of(outer, "gradient")),
            "edges_minus_outer_total_mean": _contrast(_mean_of(edges), _mean_of(outer)),
            "edges_minus_outer_gradient_mean": _contrast(_mean_of(edges, "gradient"), _mean_of(outer, "gradient")),
        })
    return result


def compact_energy_features(landscape: dict[str, Any] | None) -> dict[str, Any]:
    """Small JSON-friendly feature set for time-series reports and open-ended later analysis."""
    if not landscape:
        return {}
    asym = landscape.get("vertex_total_energy_asymmetry") or {}
    gasym = landscape.get("vertex_gradient_energy_asymmetry") or {}
    out = {
        "relation_size": landscape.get("relation_size"),
        "energy_charge_pattern": landscape.get("charge_pattern_ordered"),
        "energy_vertex_asymmetry": asym.get("normalized_range"),
        "gradient_vertex_asymmetry": gasym.get("normalized_range"),
        "energy_envelope_minus_outer": landscape.get("envelope_minus_outer_total_mean"),
    }
    if int(landscape.get("relation_size") or 0) == 2:
        out.update({
            "energy_bridge_minus_outer": landscape.get("bridge_minus_outer_total_mean"),
            "gradient_bridge_minus_outer": landscape.get("bridge_minus_outer_gradient_mean"),
        })
    elif int(landscape.get("relation_size") or 0) == 3:
        out.update({
            "energy_interior_minus_outer": landscape.get("interior_minus_outer_total_mean"),
            "gradient_interior_minus_outer": landscape.get("interior_minus_outer_gradient_mean"),
            "energy_edges_minus_outer": landscape.get("edges_minus_outer_total_mean"),
            "gradient_edges_minus_outer": landscape.get("edges_minus_outer_gradient_mean"),
        })
    return out
