"""Independent full contact traversal and set-based ancestry checks."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from analyze import binary
from contact_graph import Components, components, cutoff_squared, neighbors
from lineage import classify, transition
from study import PLAN
from tools.study_record import check_record, load_plan, read_object


def traverse(encoded, length, scheme, minimum_atoms):
    """Check each atom edge directly, without contracting interior components."""
    edges, jumps, squared = neighbors(encoded, length, scheme["radius"])
    select = squared <= cutoff_squared(scheme["radius"], length)
    edges, jumps = edges[select], jumps[select]
    active = np.bincount(edges.ravel(), minlength=len(encoded)) >= scheme["coordination"]
    graph = defaultdict(list)
    for (i, j), move in zip(edges[np.all(active[edges], axis=1)], jumps[np.all(active[edges], axis=1)]):
        graph[int(i)].append((int(j), tuple(move)))
        graph[int(j)].append((int(i), tuple(-move)))
    found = set()
    groups = []
    for i in np.flatnonzero(active).tolist():
        if i in found:
            continue
        queue = [i]
        lift = {i: (0, 0, 0)}
        wraps = [False] * 3
        for source in queue:
            for target, step in graph[source]:
                implied = tuple(a + b for a, b in zip(lift[source], step))
                if target not in lift:
                    lift[target] = implied
                    queue.append(target)
                else:
                    wraps = [flag or a != b for flag, a, b in zip(wraps, implied, lift[target])]
        found.update(queue)
        if len(queue) >= minimum_atoms:
            groups.append((set(queue), tuple(axis for axis, flag in zip("xyz", wraps) if flag)))
    return sorted(groups, key=lambda group: (-len(group[0]), min(group[0])))


def sets(frame):
    return [set(np.flatnonzero(frame.labels == i).tolist()) for i in range(len(frame.sizes))]


def verify_frame(encoded, length, scheme, minimum_atoms):
    fast = components(len(encoded), neighbors(encoded, length, scheme["radius"]), scheme, length,
                      minimum_atoms)
    assert list(zip(sets(fast), fast.winding_axes)) == traverse(encoded, length, scheme, minimum_atoms)
    return fast


def fixture(labels):
    ids = np.array(labels)
    sizes = np.bincount(ids[ids >= 0])
    return Components(ids, sizes, ((),) * len(sizes))


def checks():
    plan = load_plan(PLAN)
    rule = plan["lineage"]
    # An exact-threshold edge and a finite pair that crosses the periodic seam.
    at_cut = np.array([[0, 0, 0], [4096, 0, 0], [24576, 0, 0]], dtype=np.uint16)
    near = {"radius": 1.8, "coordination": 1}
    expected = verify_frame(at_cut, 28.8, near, 2)
    assert sets(expected) == [{0, 1}]
    seam = np.array([[256, 0, 0], [65280, 0, 0]], dtype=np.uint16)
    assert verify_frame(seam, 8., near, 2).winding_axes == ((),)
    tube = np.array([[8192*i+512, 100, 100] for i in range(8)], dtype=np.uint16)
    assert verify_frame(tube, 8., near, 2).winding_axes == (("x",),)
    shifted = ((tube.astype(int) + np.array([7812, 29031, 12414])) % 65536).astype(np.uint16)
    assert verify_frame(shifted, 8., near, 2).winding_axes == (("x",),)

    a = fixture([0]*60 + [1]*55 + [-1]*10)
    b = fixture([1]*60 + [0]*65)
    replacement = transition(a, b, rule)
    assert replacement.forward == {0: 1, 1: 0}
    assert classify(replacement, 0, 0) == "different_continuing_components"
    assert classify(replacement, 0, 1) == "same_component"
    c = fixture([0]*125)
    merger = transition(a, c, rule)
    assert merger.merges == {0: [0, 1]} and not merger.forward
    assert classify(merger, 0, 0) == "merge"
    division = transition(c, a, rule)
    assert division.splits == {0: [0, 1]} and not division.forward
    assert classify(division, 0, 0) == "split"
    tied = transition(fixture([0]*48 + [1]*48), fixture(([0]*24+[1]*24)*2), rule)
    assert not tied.forward
    return ["exact cutoff", "seam without winding", "periodic tube and translated tube",
            "rank swap", "same lineage after rank swap", "merge", "split", "no reciprocal tie"]


def evidence_check(original, replay, result):
    plan = load_plan(PLAN)
    previous = Path(plan["previous_archive"])
    check_record(previous / "PLAN.json", original / "record.json")
    check_record(PLAN, replay / "record.json")
    previous_results = read_object(previous / "analysis" / "results.json")["cases"]
    old = read_object(original / "record.json")
    fine = read_object(replay / "record.json")
    summaries = read_object(result / "results.json")
    scheme = plan["contact_schemes"]["main"]
    minimum = plan["lineage"]["minimum_component_atoms"]
    verified = []
    for name, loss in plan["targets"].items():
        config = plan["cases"][name]
        length = config["length"]
        if summaries["replay_checks"][name]["verified"]:
            positions, ledger, _species, _initial = binary.load_binary(replay, name, fine["cases"][name][-1])
        else:
            positions, ledger, _species, _initial = binary.load_binary(original, name, old["cases"][name][-1])
        out = summaries["cases"][name]["main"]["native"]
        assert previous_results[name]["main"]["finite"]["stopped_at"] == {"time_tau": loss, "reason": "overlap"}
        assert out["loss_pair"]["voxel_jaccard"] < .5
        a, b = [verify_frame(positions[np.flatnonzero(ledger[:, 1] == t).item()], length, scheme, minimum)
                for t in (out["loss_pair"]["from_tau"], loss)]
        matrix = [[len(x & y) for y in sets(b)] for x in sets(a)]
        assert matrix == out["loss_pair"]["shared_ids"]
        verified.append({"case": name, "time_tau": loss, "contact_membership_and_shared_ids_verified": True})
    return {"fixtures": checks(), "target_pairs": verified}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-only", action="store_true")
    parser.add_argument("--original", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--analysis", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.fixtures_only:
        print(json.dumps(checks()))
        return
    if None in (args.original, args.replay, args.analysis, args.out):
        parser.error("provide --original, --replay, --analysis, and --out")
    report = evidence_check(args.original, args.replay, args.analysis)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
