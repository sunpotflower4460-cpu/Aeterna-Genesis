"""Track dense regions by periodic overlap and persistent material identities."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import gzip
from pathlib import Path
import zipfile

import numpy as np
from scipy.ndimage import uniform_filter

from measure import periodic_partition
from simulate import HERE, read_json, sha256
from run import json_text

DOMAIN_PLAN = HERE / "DOMAINS_REGISTRATION.json"


@dataclass(frozen=True)
class RegionFrame:
    labels: np.ndarray
    by_molecule: np.ndarray
    volumes: np.ndarray
    populations: np.ndarray


def region_frame(density, positions, threshold, minimum):
    cut_labels, join, volumes = periodic_partition(density > threshold)
    volumes = np.concatenate(([0], volumes))
    eligible = volumes >= minimum
    labels = join[cut_labels]
    labels = np.where(eligible[labels], labels, 0)
    by_molecule = labels.ravel(order="F")[positions]
    populations = np.bincount(by_molecule, minlength=len(volumes))
    return RegionFrame(labels, by_molecule, volumes, populations)


def overlap_counts(old, new, stride):
    a, b = old.ravel(), new.ravel()
    overlap = (a > 0) & (b > 0)
    encoded, counts = np.unique(a[overlap] * stride + b[overlap], return_counts=True)
    return {divmod(int(code), stride): int(count) for code, count in zip(encoded, counts, strict=True)}


def classify_transition(before, after, plan):
    stride = len(after.volumes)
    spatial = overlap_counts(before.labels, after.labels, stride)
    material = overlap_counts(before.by_molecule, after.by_molecule, stride)
    graph = defaultdict(list)
    links = []
    for (source, target), shared in sorted(material.items()):
        region_overlap = spatial.get((source, target), 0)
        if shared < plan["minimum_shared_material_identities"]:
            continue
        if shared < plan["minimum_shared_fraction_of_each_group"] * max(
            before.populations[source], after.populations[target]
        ):
            continue
        if region_overlap < plan["minimum_geometric_overlap_of_smaller_region"] * min(
            before.volumes[source], after.volumes[target]
        ):
            continue
        links.append({"source": source, "target": target, "shared_molecules": shared, "shared_voxels": region_overlap})
        graph[source].append(-target)
        graph[-target].append(source)

    events = []
    visited = set()
    for root in sorted(graph):
        if root in visited:
            continue
        queue = [root]
        visited.add(root)
        for node in queue:
            for adjacent in graph[node]:
                if adjacent not in visited:
                    queue.append(adjacent)
                    visited.add(adjacent)
        sources = sorted(node for node in queue if node > 0)
        targets = sorted(-node for node in queue if node < 0)
        kind = ("one" if len(sources) == 1 else "many") + "-to-" + ("one" if len(targets) == 1 else "many")
        events.append({
            "kind": kind,
            "sources": [{"label": i, "sites": int(before.volumes[i]), "material": int(before.populations[i])}
                        for i in sources],
            "targets": [{"label": i, "sites": int(after.volumes[i]), "material": int(after.populations[i])}
                        for i in targets],
        })
    minimum = plan["minimum_region_sites"]
    before_count = int((before.volumes >= minimum).sum())
    after_count = int((after.volumes >= minimum).sum())
    return {
        "events": events, "links": links,
        "before_regions": before_count, "after_regions": after_count,
        "unlinked_before": before_count - sum(node > 0 for node in graph),
        "unlinked_after": after_count - sum(node < 0 for node in graph),
    }


def track(item):
    evidence, record, plan = item
    path = evidence / record["archive"]
    if sha256(path) != record["archive_sha256"]:
        raise ValueError(f"Archived history does not match audited source: {path}")
    recipe = record["recipe"]
    n = recipe["N"]
    thresholds = plan["thresholds"]
    steps = {str(threshold): [] for threshold in thresholds}
    previous = {}
    with zipfile.ZipFile(path) as archive:
        for time in range(plan["first_time"], int(recipe["T"]) + 1, plan["interval"]):
            sample = time // 10
            cells = np.frombuffer(archive.read(f"state-{sample}-cells.bin"), dtype=np.uint8)
            cells = cells.reshape((n,)*3, order="F")
            positions = np.frombuffer(archive.read(f"state-{sample}-positions.bin"), dtype="<i4")
            density = uniform_filter(((cells == 1) | (cells == 2)).astype(float), size=4, mode="wrap")
            for threshold in thresholds:
                observed = region_frame(density, positions, threshold, plan["minimum_region_sites"])
                if threshold in previous:
                    reading = classify_transition(previous[threshold], observed, plan)
                    reading["end"] = time
                    steps[str(threshold)].append(reading)
                previous[threshold] = observed
    return record["archive"], {
        "N": n, "T": recipe["T"], "seed": recipe["seed"], "case": recipe["case"]["id"],
        "summary_by_threshold": {key: summarize(transitions) for key, transitions in steps.items()},
    }, steps


def summarize(transitions):
    kinds = Counter(event["kind"] for row in transitions for event in row["events"])
    return {
        "intervals": len(transitions), "event_counts": dict(kinds),
        "unlinked_before": sum(row["unlinked_before"] for row in transitions),
        "unlinked_after": sum(row["unlinked_after"] for row in transitions),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--measurements", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    plan = read_json(DOMAIN_PLAN)
    data = read_json(args.measurements)
    chosen = [row for row in data["archives"] if row["recipe"]["case"]["id"] in ("uniform_minus", "reversible_df0.2")
              or row["phase"] in ("clock", "supply")]
    if len(chosen) != 27:
        raise ValueError("Incomplete registered tracking matrix")
    reports, histories = {}, {}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for key, report, steps in pool.map(track, [(args.evidence, row, plan) for row in chosen]):
            reports[key] = report
            histories[key] = steps
    args.out.mkdir(parents=True, exist_ok=False)
    result = {"registration_sha256": sha256(DOMAIN_PLAN), "records": reports}
    (args.out / "results.json").write_text(json_text(result), encoding="utf-8")
    (args.out / "events.json.gz").write_bytes(gzip.compress(json_text(histories).encode(), mtime=0))
    print(f"Tracked {len(reports)} histories at both density thresholds.", flush=True)


if __name__ == "__main__":
    main()
