"""Geometry and encounter measurements for periodic molecular lattices."""
from __future__ import annotations

from collections import defaultdict
from math import fsum

import numpy as np
from scipy.ndimage import generate_binary_structure, label, uniform_filter

from genesis.diagnostics.topology3d import three_d_authenticity

THRESHOLDS = (0.3, 0.5, 0.7)
FACE_NEIGHBORS = generate_binary_structure(3, 1)


def periodic_components(mask):
    """Label six-neighbor components on a torus and detect lifted winding cycles."""
    if mask.ndim != 3:
        raise ValueError("Expected one three-dimensional lattice")
    labels, count = label(mask, structure=FACE_NEIGHBORS)
    volumes = np.bincount(labels.ravel(), minlength=count + 1)
    edges = defaultdict(list)
    for axis in range(3):
        near = np.take(labels, 0, axis=axis).ravel()
        far = np.take(labels, -1, axis=axis).ravel()
        occupied = (near != 0) & (far != 0)
        connections = np.column_stack((far[occupied], near[occupied]))
        step = tuple(int(coordinate == axis) for coordinate in range(3))
        for source, target in np.unique(connections, axis=0):
            edges[source].append((target, step))
            edges[target].append((source, tuple(-value for value in step)))

    components = []
    lifts = {}
    for root in range(1, count + 1):
        if root in lifts:
            continue
        lifts[root] = (0, 0, 0)
        queue = [root]
        volume = 0
        winding = [False] * 3
        for source in queue:
            volume += int(volumes[source])
            for target, step in edges[source]:
                implied = tuple(a + b for a, b in zip(lifts[source], step))
                if target not in lifts:
                    lifts[target] = implied
                    queue.append(target)
                else:
                    winding = [flag or a != b for flag, a, b in zip(winding, implied, lifts[target])]
        components.append((volume, winding))

    components.sort(reverse=True)
    return {
        "count": len(components),
        "largest_volumes": [volume for volume, _ in components[:8]],
        "cut_open_count": count,
        "cut_open_largest": int(max(volumes[1:], default=0)),
        "winding_component_count": sum(any(winding) for _, winding in components),
        "winding_axes_any": [any(winding[axis] for _, winding in components) for axis in range(3)],
        "largest_winding_axes": components[0][1] if components else [False] * 3,
        "volume_fraction": float(np.mean(mask)),
    }


def neighbor_sum(field):
    """Sum values over the six periodic face neighbors."""
    result = np.zeros(field.shape, dtype=np.result_type(field.dtype, np.int8))
    for axis in range(3):
        result += np.roll(field, 1, axis=axis)
        result += np.roll(field, -1, axis=axis)
    return result


def encounter_rates(cells, parameters):
    """Observe propensities and two composition-preserving mixing references."""
    nonmacro = (cells != 1) & (cells != 2)
    eligible = neighbor_sum(nonmacro)
    eligible_x = nonmacro.sum(axis=(1, 2))
    n_b = neighbor_sum(cells == 2)
    eps_ts = 0.5 * parameters["epsilon"]
    b_counts = np.arange(7)
    weights = [
        parameters["eta"] * np.exp(parameters["df"] + (parameters["epsilon"] - eps_ts) * b_counts) / 6,
        parameters["eta"] * np.exp(-eps_ts * b_counts) / 6,
    ]
    result = {}
    for name, macro_code, resource_code, weight in zip(
        ("B_to_I", "I_to_B"), (2, 1), (3, 4), weights,
    ):
        macro = cells == macro_code
        resource = cells == resource_code
        resource_x = resource.sum(axis=(1, 2))
        constant = int(resource_x.sum()) / max(1, int(eligible_x.sum()))
        same_x = np.divide(resource_x, eligible_x, where=eligible_x > 0, out=np.zeros_like(resource_x, dtype=float))
        directed_contacts = {
            "observed": neighbor_sum(resource),
            "well_mixed": eligible * constant,
            "same_x_mixed": neighbor_sum(nonmacro * same_x[:, None, None]),
        }
        bins = n_b[macro]
        contacts = {
            key: np.bincount(bins, weights=values[macro], minlength=7)
            for key, values in directed_contacts.items()
        }
        result[name] = {
            "contacts_by_B_neighbors": {key: values.tolist() for key, values in contacts.items()},
            "propensities": {key: float(weight @ values) for key, values in contacts.items()},
        }
    return result


def measure_frame(cells, parameters, explicit_fuel):
    """Read the state without feeding geometric or chemical labels into its dynamics."""
    macro = (cells == 1) | (cells == 2)
    rho2 = uniform_filter(macro.astype(float), size=2, mode="wrap")
    rho4 = uniform_filter(macro.astype(float), size=4, mode="wrap")
    x_profile = rho4.mean(axis=(1, 2))
    observations = {
        "variance_2": float(rho2.var()),
        "variance_4": float(rho4.var()),
        "variance_4_x_only": float(x_profile.var()),
        "variance_4_transverse": float(np.mean((rho4 - x_profile[:, None, None]) ** 2)),
        "density_regions": {
            str(threshold): periodic_components(rho4 > threshold) for threshold in THRESHOLDS
        },
        "three_d_authenticity": three_d_authenticity(rho4),
    }
    if explicit_fuel:
        n = cells.shape[0]
        observations["profiles"] = {
            key: ((cells == code).sum(axis=(1, 2)) / n**2).tolist()
            for key, code in (("I", 1), ("B", 2), ("F", 3), ("W", 4))
        }
        observations["encounters"] = encounter_rates(cells, parameters)
    return observations


def time_mean(times, values, start, end):
    """Average a piecewise linear reconstruction over the exact registered window."""
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)
    if (
        times.ndim != 1 or values.ndim != 1 or times.shape != values.shape
        or times.size < 2 or np.any(np.diff(times) <= 0)
        or not times[0] <= start < end <= times[-1]
    ):
        raise ValueError("Samples must be increasing and bracket the complete window")
    inner = times[(start < times) & (times < end)]
    points = np.concatenate(([start], inner, [end]))
    interpolated = np.interp(points, times, values)
    trapezoids = np.diff(points) * (interpolated[:-1] + interpolated[1:]) / 2
    return fsum(trapezoids) / (end - start)
