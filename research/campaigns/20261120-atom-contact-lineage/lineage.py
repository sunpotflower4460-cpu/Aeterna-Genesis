"""Measure atom transfers among all substantial contact components."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Transition:
    shared: np.ndarray
    forward: dict[int, int]
    backward: dict[int, int]
    merges: dict[int, list[int]]
    splits: dict[int, list[int]]


def transition(before, after, rule):
    present = (before.labels >= 0) & (after.labels >= 0)
    n, m = len(before.sizes), len(after.sizes)
    pairs = before.labels[present].astype(int) * m + after.labels[present]
    shared = np.bincount(pairs, minlength=n*m).reshape(n, m)
    parent_size = before.sizes[:, None]
    child_size = after.sizes[None, :]
    support = shared >= rule["minimum_shared_atoms"]
    branch = rule["branch_fraction"]
    majority = rule["branch_majority"]
    coverage = rule["branch_coverage"]
    contributing = support & (shared >= majority * parent_size) & (shared >= branch * child_size)
    receiving = support & (shared >= branch * parent_size) & (shared >= majority * child_size)
    merges = {
        child: np.flatnonzero(contributing[:, child]).tolist()
        for child in range(m) if contributing[:, child].sum() >= 2
        and shared[contributing[:, child], child].sum() >= coverage * after.sizes[child]
    }
    splits = {
        parent: np.flatnonzero(receiving[parent]).tolist()
        for parent in range(n) if receiving[parent].sum() >= 2
        and shared[parent, receiving[parent]].sum() >= coverage * before.sizes[parent]
    }
    ambiguous_parents = set(splits) | {i for indices in merges.values() for i in indices}
    ambiguous_children = set(merges) | {i for indices in splits.values() for i in indices}
    threshold = rule["reciprocal_majority"]
    matching = (shared > threshold * parent_size) & (shared > threshold * child_size)
    forward = {int(i): int(j) for i, j in np.argwhere(matching)
               if i not in ambiguous_parents and j not in ambiguous_children}
    return Transition(shared, forward, {j: i for i, j in forward.items()}, merges, splits)


def affiliation(frame, grid_atoms):
    labels = frame.labels[grid_atoms]
    counts = np.bincount(labels[labels >= 0], minlength=len(frame.sizes))
    leading = np.flatnonzero(counts == counts.max()) if len(counts) else []
    match = None
    n = int(grid_atoms.sum())
    if len(leading) == 1:
        rank = int(leading[0])
        if 2 * counts[rank] > max(n, frame.sizes[rank]):
            match = rank
    return {"grid_atoms": n, "overlaps_with_contact_components": counts.tolist(), "match": match}


def classify(change, i, j):
    """Describe the contact relation between the grid-affiliated components."""
    if i is None or j is None:
        return "unresolved_affiliation"
    merged = i in change.merges.get(j, ())
    split = j in change.splits.get(i, ())
    if merged and split:
        return "merge_and_split"
    if merged:
        return "merge"
    if split:
        return "split"
    if change.forward.get(i) == j:
        return "same_component"
    if i in change.forward and j in change.backward:
        return "different_continuing_components"
    return "unresolved_material_transfer"


def survives(indices, transitions, reverse=False):
    current = list(indices)
    for change in transitions:
        link = change.backward if reverse else change.forward
        if any(i not in link for i in current):
            return False
        current = [link[i] for i in current]
    return True


def events(data, times, transitions, loss, width, persistence):
    span = round(persistence / (times[1] - times[0]))
    collected = []
    for k, change in enumerate(transitions):
        if not (loss - width <= times[k + 1] <= loss + width):
            continue
        previous = transitions[max(0, k-span):k]
        subsequent = transitions[k+1:k+1+span]
        for kind, branches in (("merge", change.merges), ("split", change.splits)):
            for singleton, multiples in branches.items():
                parent, child = (multiples, [singleton]) if kind == "merge" else ([singleton], multiples)
                persistent = None
                if len(previous) == len(subsequent) == span:
                    persistent = bool(survives(parent, reversed(previous), reverse=True)
                                      and survives(child, subsequent))
                collected.append({
                    "kind": kind, "before_tau": float(times[k]), "after_tau": float(times[k+1]),
                    "parent_components": parent, "child_components": child,
                    "parent_sizes": data[k].sizes[parent].tolist(),
                    "child_sizes": data[k+1].sizes[child].tolist(),
                    "shared_ids": change.shared[np.ix_(parent, child)].tolist(),
                    "parent_winding_axes": [data[k].winding_axes[i] for i in parent],
                    "child_winding_axes": [data[k+1].winding_axes[j] for j in child],
                    "persistent": persistent,
                })
    return collected


def follow(data, times, transitions, grid_at_anchor, anchor):
    index = np.flatnonzero(times == anchor).item()
    start = affiliation(data[index], grid_at_anchor)
    component = start["match"]
    trace = []
    stop = None
    if component is None:
        stop = {"time_tau": float(times[index]), "reason": "unresolved_affiliation"}
    else:
        origin = data[index].labels == component
        for i in range(index, len(data)):
            flags = data[i].labels == component
            trace.append({
                "time_tau": float(times[i]), "component": component,
                "atoms": int(flags.sum()), "origin_atoms_still_present": int((flags & origin).sum()),
                "winding_axes": data[i].winding_axes[component],
            })
            if i == len(transitions):
                break
            change = transitions[i]
            following = change.forward.get(component)
            if following is None:
                split = component in change.splits
                merge = any(component in parents for parents in change.merges.values())
                reason = ("merge_and_split" if split and merge else "merge" if merge
                          else "split" if split else "no_reciprocal_majority")
                stop = {"time_tau": float(times[i+1]), "reason": reason}
                break
            component = following
    first_winding = next((row["time_tau"] for row in trace if row["winding_axes"]), None)
    last = trace[-1] if trace else None
    return {
        "anchor_affiliation": start, "first_winding_tau": first_winding,
        "last_followed": last, "first_loss": stop, "initial_atoms": trace[0]["atoms"] if trace else None,
        "rank_switches_along_track": sum(x["component"] != y["component"] for x, y in zip(trace, trace[1:])),
    }, trace
