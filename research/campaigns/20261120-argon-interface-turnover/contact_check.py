"""Exploratory check with a contact graph, independent of the density grid."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from analyze import exchange, load_trajectory, mine_track
from tools.study_record import load_plan, read_object


def classify_contacts(encoded, length):
    points = (encoded.astype(float) + 0.5) * (length / 65536)
    edges = cKDTree(points, boxsize=length).query_pairs(1.8, output_type="ndarray")
    coordination = np.bincount(edges.ravel(), minlength=len(points))
    active = coordination >= 8
    mapping = np.cumsum(active) - 1
    contacts = edges[np.all(active[edges], axis=1)]
    clustered = np.zeros(len(points), dtype=bool)
    phase = np.zeros(len(points), dtype=np.uint8)
    if not len(contacts):
        return clustered, phase, False
    endpoints = mapping[contacts]
    graph = sparse.coo_matrix(
        (np.ones(len(contacts)), (endpoints[:, 0], endpoints[:, 1])),
        shape=(int(active.sum()),) * 2,
    ).tocsr()
    _, labels = connected_components(graph, directed=False)
    sizes = np.bincount(labels)
    largest = int(np.argmax(sizes))
    clustered[active] = labels == largest
    inside = points[clustered]
    by_axis = np.sort(inside, axis=0)
    empty_intervals = np.diff(np.vstack((by_axis, by_axis[0] + length)), axis=0).max(axis=0)
    bounded = sizes[largest] >= 48 and bool(np.all(empty_intervals > 1.8))
    if bounded:
        distance, _ = cKDTree(points[active], boxsize=length).query(points)
        phase[clustered & (coordination >= 14)] = 1
        phase[(coordination <= 4) & (distance >= 2)] = 2
    return clustered, phase, bounded


def measure(plan, evidence):
    record = read_object(evidence / "record.json")
    p = plan["protocol"]
    report = {}
    for name, setup in plan["cases"].items():
        entry = record["cases"][name][-1]
        if entry["status"] != "completed":
            continue
        positions, ledger = load_trajectory(evidence, name, entry)
        times = ledger[:, 1]
        start = np.flatnonzero(times == p["fork"]).item() - (p["residence_frames"] - 1)
        positions, times = positions[start:], times[start:]
        previous = np.zeros(positions.shape[1], dtype=bool)
        flags, rows = [], []
        for pts, t in zip(positions, times):
            members, phase, bounded = classify_contacts(pts, setup["length"])
            union = np.count_nonzero(members | previous)
            overlap = float(np.count_nonzero(members & previous) / union) if union else None
            rows.append({"t": float(t), "bounded": bounded, "overlap": overlap})
            flags.append(phase)
            previous = members
        anchor, end = mine_track(rows, p["fork"], p["overlap_min"])
        summary = {"track_through": rows[end]["t"] if end is not None else None}
        if end is not None:
            result = exchange(np.array(flags), positions, times, anchor, end, p["residence_frames"],
                              setup["length"], p["minimum_displacement"])
            summary.update({k: v for k, v in result.items() if k != "events"})
        report[name] = summary
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    values = measure(load_plan(args.plan), args.evidence)
    args.out.write_text(json.dumps(values, indent=2, allow_nan=False) + "\n")
    print(f"contact-graph analysis completed for {len(values)} cases")


if __name__ == "__main__":
    main()
