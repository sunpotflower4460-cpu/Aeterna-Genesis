"""Reconstruct oriented vortex loops from raw nonzero plaquette circulations."""
from __future__ import annotations

from collections import defaultdict
import math

import numpy as np


def minimum_image(displacement, period):
    return (displacement + period / 2) % period - period / 2


def potential_at_crossings(faces, shape, dx, obstacle_z, height):
    if not len(faces):
        return np.empty(0)
    period = np.array(shape) * dx
    coords = faces[:, 1:4].astype(float) + 0.5
    coords[np.arange(len(faces)), faces[:, 0]] -= 0.5
    separation = minimum_image(coords * dx - [period[0] / 2, period[1] / 2, obstacle_z], period)
    return height * np.exp(-0.5 * ((separation[:, :, None] + period[:, None] *
                                  np.arange(-1, 2)) / 2.5)**2).sum(axis=2).prod(axis=1)


def decode(faces, shape, dx, obstacle_z, height):
    """Faces contain (normal, x, y, z, integer charge) in cyclic (yz,zx,xy) orientation."""
    box = np.array(shape)
    period = box * dx
    incident = defaultdict(list)
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    potential = potential_at_crossings(faces, box, dx, obstacle_z, height)
    for index, (normal, x, y, z, charge) in enumerate(faces):
        b = np.array([x, y, z])
        a = b.copy()
        a[normal] = (a[normal] - 1) % box[normal]
        source, sink = (tuple(a), tuple(b)) if charge > 0 else (tuple(b), tuple(a))
        for _ in range(abs(charge)):
            outgoing[source].append((sink, index))
            incoming[sink].append(source)
            incident[source].append(sink)
            incident[sink].append(source)
    visited = set()
    components = []
    for start in sorted(incident):
        if start in visited:
            continue
        queue = [start]
        visited.add(start)
        for site in queue:
            for other in incident[site]:
                if other not in visited:
                    visited.add(other)
                    queue.append(other)
        if any(len(outgoing[site]) != 1 or len(incoming[site]) != 1 for site in queue):
            components.append({"status": "unresolved", "edges": sum(len(outgoing[p]) for p in queue)})
            continue
        p = start
        path = [np.array(p)]
        indices = []
        for _ in queue:
            q, edge = outgoing[p][0]
            path.append(path[-1] + minimum_image(np.subtract(q, p), box).astype(int))
            indices.append(edge)
            p = q
        if p != start or not np.array_equal(path[-1], path[0]):
            components.append({"status": "wraps", "edges": len(indices)})
            continue
        nodes = (np.array(path) + 0.5) * dx
        center = nodes[:-1].mean(axis=0)
        relative = nodes - center
        area = np.cross(relative[:-1], relative[1:]).sum(axis=0) / 2
        radius = math.sqrt(np.square(relative[:-1]).sum(axis=1).mean())
        components.append({
            "status": "closed",
            "edges": len(indices),
            "center": (center % period).tolist(),
            "radius": radius,
            "area_vector": area.tolist(),
            "max_v": float(potential[indices].max()),
            "nodes": nodes,
        })
    return components


def frames(data):
    """Decode every saved time, including frames with zero pierced faces."""
    shape, dx = data["shape"], float(data["dx"])
    ledger = data["ledger"]
    face_groups = np.split(data["faces"][:, 1:], np.searchsorted(data["faces"][:, 0], np.arange(1, len(ledger))))
    return [
        decode(faces, shape, dx, row[1], row[3])
        for row, faces in zip(ledger, face_groups)
    ]


def follow(components, times, box, v_cutoff=0.5):
    tracks = []
    previous = []
    counts = []
    for time, pieces in zip(times, components):
        current = [
            {k: v for k, v in piece.items() if k != "nodes"}
            for piece in pieces
            if piece["status"] == "closed" and piece["radius"] >= 2.0 and piece["max_v"] <= v_cutoff
        ]
        near_prior = defaultdict(list)
        near_next = defaultdict(list)
        for j, loop in enumerate(current):
            for i in previous:
                old = tracks[i][-1]
                distance = np.linalg.norm(minimum_image(np.subtract(loop["center"], old["center"]), box))
                radius_ratio = loop["radius"] / old["radius"]
                if distance <= 1.5 * (time - old["t"]) and 2 / 3 <= radius_ratio <= 1.5:
                    near_prior[j].append(i)
                    near_next[i].append(j)
        previous = []
        ambiguous = 0
        for j, loop in enumerate(current):
            if len(near_prior[j]) == 1 and len(near_next[near_prior[j][0]]) == 1:
                i = near_prior[j][0]
            else:
                ambiguous += bool(near_prior[j])
                i = len(tracks)
                tracks.append([])
            tracks[i].append({"t": float(time), **loop})
            previous.append(i)
        counts.append({
            "t": float(time),
            "resolved": len(current),
            "all_closed": sum(p["status"] == "closed" for p in pieces),
            "unresolved": sum(p["status"] == "unresolved" for p in pieces),
            "wraps": sum(p["status"] == "wraps" for p in pieces),
            "ambiguous_associations": ambiguous,
        })
    return counts, tracks


def summarize(tracks):
    cohort = [track for track in tracks if track[0]["t"] <= 116 and track[-1]["t"] >= 120]
    entry = [track for track in tracks if track[0]["t"] > 132 and len(track) >= 3]
    return {
        "cohort": len(cohort),
        "cohort_still_linked": {str(t): sum(tr[-1]["t"] >= t for tr in cohort) for t in (132, 176, 224)},
        "cohort_last_times": [track[-1]["t"] for track in cohort],
        "cohort_radius_at_120": [next(row["radius"] for row in tr if row["t"] == 120) for tr in cohort],
        "cohort_radius_at_224": [tr[-1]["radius"] for tr in cohort if tr[-1]["t"] == 224],
        "later_track_starts": [tr[0]["t"] for tr in entry],
    }
