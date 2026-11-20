"""Explore why the grid stopped after opening the registered contact results."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from analyze import binary, geometry
from contact_graph import components, cutoff_squared, neighbors
from lineage import transition
from study import PLAN
from tools.study_record import load_plan, read_object


def grid_groups(encoded, length, p, cutoff):
    n = round(length)
    dx = length / n
    ids = ((2 * encoded.astype(np.int32) + 1) * n) // 131072
    flat = np.ravel_multi_index(ids.T, (n,) * 3)
    raw = np.bincount(flat, minlength=n**3).reshape((n,) * 3) / dx**3
    smooth = ndimage.gaussian_filter(raw, p["smooth_sigma"] / dx, mode="wrap")
    labels = geometry.periodic_labels(smooth >= cutoff)
    sizes = np.bincount(labels.ravel())
    labels_by_atom = geometry.phase_at(labels, ids)
    qualifying = [int(k) for k in np.argsort(-sizes, kind="stable")
                  if k != 0 and sizes[k] * dx**3 >= p["minimum_component_volume"]]
    return [labels_by_atom == k for k in qualifying]


def intersections(a, b):
    return [[int((x & y).sum()) for y in b] for x in a]


def inspect(original, replay, analysis):
    plan = load_plan(PLAN)
    summary = read_object(analysis / "results.json")
    old = read_object(original / "record.json")["cases"]
    new = read_object(replay / "record.json")["cases"]
    original_plan = load_plan(Path(plan["previous_archive"]) / "PLAN.json")
    cutoff = original_plan["schemes"]["main"]["threshold"]
    scheme = plan["contact_schemes"]["main"]
    minimum = plan["lineage"]["minimum_component_atoms"]
    with gzip.open(analysis / "lineages.json.gz", "rt") as stream:
        details = json.load(stream)

    cases = {}
    for name, loss in plan["targets"].items():
        folder, rec = (replay, new) if summary["replay_checks"][name]["verified"] else (original, old)
        q, ledger, _, _ = binary.load_binary(folder, name, rec[name][-1])
        times = ledger[:, 1]
        length = plan["cases"][name]["length"]

        def read_frame(t):
            snapshot = q[np.flatnonzero(times == t).item()]
            near = neighbors(snapshot, length, scheme["radius"])
            graph = components(len(snapshot), near, scheme, length, minimum)
            return snapshot, graph, near

        matched_grid = []
        matched_contact = []
        for t in (loss-2, loss):
            snapshot, graph, _near = read_frame(t)
            matched_grid.append(grid_groups(snapshot, length, plan["protocol"], cutoff))
            matched_contact.append([graph.labels == k for k in range(len(graph.sizes))])
        result = {
            "comparison_times_tau": [loss-2, loss],
            "grid_sizes_before_after": [[int(g.sum()) for g in state] for state in matched_grid],
            "grid_to_contact_before_after": [intersections(grid, contact)
                                             for grid, contact in zip(matched_grid, matched_contact)],
            "grid_shared_ids_between_frames": intersections(*matched_grid),
            "merger_contacts": None,
        }
        eligible = [row for row in details[name]["main"]["native"]["adjacent_events"]
                    if row["kind"] == "merge" and row["after_tau"] <= loss
                    and row["parent_components"] == [0, 1] and row["child_components"] == [0]]
        if eligible:
            event = eligible[-1]
            _q, parents, _near = read_frame(event["before_tau"])
            A, B = parents.labels == 0, parents.labels == 1
            stats = []
            for t in sorted({loss, event["after_tau"]-0.5, event["after_tau"],
                             event["after_tau"]+1, event["after_tau"]+2, event["after_tau"]+4}):
                if t not in times:
                    continue
                _snapshot, groups, near = read_frame(t)
                edges = near[0][near[2] <= cutoff_squared(scheme["radius"], length)]
                i, j = edges.T
                cross = (A[i] & B[j]) | (B[i] & A[j])
                same_component = (groups.labels[i] >= 0) & (groups.labels[i] == groups.labels[j])
                links = edges[cross & same_component]
                stats.append({
                    "time_tau": t, "cross_parent_contact_edges_in_same_dense_component": len(links),
                    "unique_atoms_on_those_edges": len(np.unique(links)),
                    "largest_contact_component_atoms": int(groups.sizes[0]) if len(groups.sizes) else None,
                    "largest_winding_axes": groups.winding_axes[0] if len(groups.sizes) else (),
                })
            descendants = []
            previous = None
            component = event["child_components"][0]
            last_clock = times[(times >= event["after_tau"]) & (times <= loss + plan["lineage"]["window_tau"])]
            for t in last_clock:
                _snapshot, groups, _near = read_frame(t)
                if previous is not None:
                    change = transition(previous, groups, plan["lineage"])
                    component = change.forward.get(component)
                    if component is None:
                        break
                descendants.append({"time_tau": float(t), "component_atoms": int(groups.sizes[component]),
                                    "winding_axes": groups.winding_axes[component]})
                previous = groups
            result["merger_contacts"] = {"accepted_at_tau": event["after_tau"],
                                         "source_tau": event["before_tau"], "measurements": stats,
                                         "local_descendant": descendants}
        cases[name] = result
    return {"analysis_role": "exploratory_after_registered_readout", "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    data = inspect(args.original, args.replay, args.analysis)
    args.out.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
