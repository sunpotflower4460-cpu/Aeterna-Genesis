"""Diagnose failed tracking with lifted paths on the periodic voxel grid.

Exploratory follow-up to the registered readout. Uses the same density mask
and inspects the anchor and the first failed frame, without extending tracks.
"""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from measure import PLAN, geometry, load_binary
from tools.study_record import check_record, load_plan, read_object

spec = spec_from_file_location("lattice_geometry", PLAN.parent.parent / "20261119-transport-and-composition/observe.py")
topology = module_from_spec(spec)
spec.loader.exec_module(topology)


def inspect_frame(positions, length, protocol):
    n = round(length)
    dx = length / n
    indices = ((2 * positions.astype(np.int32) + 1) * n) // 131072
    flat = np.ravel_multi_index(indices.T, (n,) * 3)
    raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
    field = ndimage.gaussian_filter(raw, protocol["smooth_sigma"] / dx, mode="wrap")
    threshold, depth, _stride = geometry.SCHEMES["main"]
    dense, _, _, bounded, second = geometry.separate(
        field, protocol["minimum_component_volume"], dx, threshold, depth)
    volume = float(dense.sum() * dx**3)
    vacant = [
        n - int(np.count_nonzero(np.any(dense, axis=tuple(i for i in range(3) if i != axis))))
        for axis in range(3)
    ]
    components = topology.periodic_components(dense)
    if components["count"] != bool(dense.any()):
        raise ValueError("expected the density mask to be connected across the periodic seams")
    winding = components["largest_winding_axes"]
    if any(planes and wraps for planes, wraps in zip(vacant, winding)):
        raise ValueError("a winding path cannot bypass a vacant plane")
    return {
        "component_volume": volume,
        "second_component_volume": second,
        "vacant_planes_xyz": vacant,
        "winding_axes": [axis for axis, wraps in zip("xyz", winding) if wraps],
        "above_minimum_volume": volume >= protocol["minimum_component_volume"],
        "bounded_in_registered_analysis": bool(bounded),
    }


def measure(evidence, result):
    plan = load_plan(PLAN)
    protocol = plan["protocol"]
    path = evidence / "record.json"
    check_record(PLAN, path)
    record = read_object(path)
    forks, failures = {}, {}
    for name, output in result["cases"].items():
        case = plan["cases"][name]
        group = case["group"]
        positions, ledger, _species, _initial = load_binary(evidence, name, record["cases"][name][-1])
        p = output["main"]
        if group not in forks:
            first = np.flatnonzero(ledger[:, 1] == protocol["fork"]).item()
            forks[group] = inspect_frame(positions[first], case["length"], protocol)
        end = p["track_through_tau"]
        if end is not None and not p["track_complete"]:
            after = np.flatnonzero(ledger[:, 1] == end).item() + 1
            failures[name] = {"time_tau": float(ledger[after, 1]),
                              **inspect_frame(positions[after], case["length"], protocol)}
    return {"analysis_role": "exploratory_after_primary_result", "forks": forks, "first_tracking_losses": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = measure(args.evidence.resolve(), read_object(args.results))
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
