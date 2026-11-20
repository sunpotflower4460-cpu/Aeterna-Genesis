"""Cross-check the periodic graph, the archived observer and one isolated interval."""
from __future__ import annotations

import argparse
from collections import deque
import gzip
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from readouts import binary, core_footprint, geometry, read_mask, topology
from study import PLAN
from tools.study_record import check_record, load_plan, read_object
import validate as integrator


def direct_winding(mask):
    """Follow unit moves on the lifted lattice, without compressing interior regions."""
    start = tuple(map(int, np.argwhere(mask)[0]))
    lifts = {start: (0, 0, 0)}
    queue = deque([start])
    winding = [False] * 3
    while queue:
        site = queue.popleft()
        for axis, size in enumerate(mask.shape):
            for step in (-1, 1):
                neighbor = list(site)
                neighbor[axis] = (site[axis] + step) % size
                neighbor = tuple(neighbor)
                if not mask[neighbor]:
                    continue
                position = list(lifts[site])
                position[axis] += step
                position = tuple(position)
                if neighbor not in lifts:
                    lifts[neighbor] = position
                    queue.append(neighbor)
                else:
                    for i, (a, b) in enumerate(zip(position, lifts[neighbor])):
                        if (a - b) % mask.shape[i]:
                            raise ValueError("inconsistent lifted lattice positions")
                        winding[i] |= a != b
    if len(lifts) != int(mask.sum()):
        raise ValueError("a single component is required")
    return [axis for axis, wraps in zip("xyz", winding) if wraps]


def verify_fixtures():
    tube = np.zeros((8, 8, 8), dtype=bool)
    tube[:, 2, 2] = True
    seam = np.zeros_like(tube)
    seam[[7, 0, 1], 2, 2] = True
    staircase = np.zeros_like(tube)
    staircase[:4, 2, 2] = True
    staircase[3:, 3, 2] = True
    # One connected group winds in two axes.
    cross = tube.copy()
    cross[4, :, 2] = True
    cases = [
        ("periodic tube", tube, ["x"], False),
        ("finite seam crossing", seam, [], True),
        ("finite staircase across all x planes", staircase, [], False),
        ("two winding axes", cross, ["x", "y"], False),
    ]
    for name, mask, expected, vacancy in cases:
        for shift in ((0, 0, 0), (2, 5, 1)):
            moved = np.roll(mask, shift, axis=(0, 1, 2))
            _, _, _, frame = read_mask(moved.astype(float), 1., .5, 1., 1., core_footprint(1., 1.))
            flags = topology.periodic_components(moved)["largest_winding_axes"]
            assert [a for a, b in zip("xyz", flags) if b] == direct_winding(moved) == expected, name
            assert frame["vacant"] == vacancy, name
            assert frame["finite"] == (not expected), name
    return [name for name, _mask, _axes, _vacancy in cases]


def recorded_component(positions, length, protocol, threshold):
    n = round(length)
    dx = length / n
    ids = ((2 * positions.astype(np.int32) + 1) * n) // 131072
    flat = np.ravel_multi_index(ids.T, (n, n, n))
    raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
    field = ndimage.gaussian_filter(raw, protocol["smooth_sigma"] / dx, mode="wrap")
    mask, *_ = geometry.separate(field, protocol["minimum_component_volume"], dx, threshold, protocol["core_depth"])
    return mask


def verify(evidence, analysis):
    plan = load_plan(PLAN)
    protocol = plan["protocol"]
    check_record(PLAN, evidence / "record.json")
    record = read_object(evidence / "record.json")
    result = read_object(analysis / "results.json")["cases"]
    with gzip.open(analysis / "readouts.json.gz", "rt") as stream:
        details = json.load(stream)

    legacy_names = plan["validation"]["legacy_cases"]
    frames_checked = []
    for name, case in plan["cases"].items():
        if name not in result:
            continue
        positions, ledger, species, _initial = binary.load_binary(evidence, name, record["cases"][name][-1])
        clock = ledger[:, 1]
        if name in legacy_names:
            old, _ = binary.read_geometry(positions, clock, species, case["length"], protocol, "main")
            here = result[name]["main"]["vacant"]
            for key, prior in (("track_to_tau", "track_through_tau"), ("composition_frames", "window_valid_frames"),
                               ("complete", "window_complete"), ("composition", "window_composition"),
                               ("transits", "transits")):
                assert here[key] == old[prior], (name, key)
        rows = [r for r in details[name]["main"]["frames"] if r["t"] >= protocol["fork"]]
        for label, matching in (
                ("finite_without_vacant_plane", (r for r in rows if r["finite"] and not r["vacant"])),
                ("winding", (r for r in rows if r["winding_axes"]))):
            first = next(matching, None)
            if first is None:
                continue
            idx = np.flatnonzero(clock == first["t"]).item()
            mask = recorded_component(positions[idx], case["length"], protocol, plan["schemes"]["main"]["threshold"])
            axes = direct_winding(mask)
            assert axes == first["winding_axes"], (name, first["t"], axes)
            frames_checked.append({"case": name, "time_tau": first["t"], "category": label, "axes": axes})
    integrator.PLAN = PLAN
    independent = integrator.verify(evidence, plan["validation"]["integrator_case"])
    return {"synthetic_masks": verify_fixtures(), "legacy_cases": legacy_names,
            "direct_winding_snapshots": frames_checked, "periodic_tree_integrator": independent}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.evidence.resolve(), args.analysis.resolve())
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Direct winding verified for {len(report['direct_winding_snapshots'])} saved snapshots.")


if __name__ == "__main__":
    main()
