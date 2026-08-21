"""Relation-only geometry, identity-continuity and lineage diagnostics.

These instruments operate *after* a relation state exists.  They do not add positions, directions,
objects, bodies or target morphologies to the dynamics.  The primary Pure Genesis use consumes only an
anonymous symmetric relation matrix and derives a threshold relation graph from relation magnitudes.

Three questions are kept deliberately separate:

* metric-from-relations: does the relation graph support a reproducible metric-like organization that
  survives anonymous-label permutation and differs from relation-destroying rewires?
* identity-continuity: do non-trivial relation-defined components remain structurally trackable through
  time under a predeclared, label-free association rule?
* lineage-accounting: when one persistent relation-defined component is followed by two persistent
  components, can their coarse relational accounting plausibly inherit from the parent better than
  unrelated alternatives?

Positive outputs are measurement candidates only.  They are not claims of physical spacetime,
fundamental dimension, organism/self/cell/life, biological division, reproduction or heredity.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from typing import Any, Iterable

import numpy as np

INSTRUMENT_VERSION = 1


def _edge_key(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _compact_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def make_graph(
    node_count: int,
    edges: Iterable[tuple[int, int] | tuple[int, int, float]],
    *,
    source: str = "explicit-relation-graph",
    coordinate_input_used: bool = False,
) -> dict[str, Any]:
    """Build a small undirected relation graph used by the pure diagnostic functions."""
    n = max(0, int(node_count))
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for raw in edges:
        a, b = int(raw[0]), int(raw[1])
        if a == b or a < 0 or b < 0 or a >= n or b >= n:
            continue
        weight = float(raw[2]) if len(raw) >= 3 else 1.0  # type: ignore[arg-type]
        if not math.isfinite(weight):
            continue
        key = _edge_key(a, b)
        rows[key] = {
            "a": key[0],
            "b": key[1],
            "weight": abs(weight),
            "signed_weight": weight,
            "sign": 1 if weight >= 0 else -1,
        }
    return {
        "version": INSTRUMENT_VERSION,
        "nodes": list(range(n)),
        "edges": [rows[key] for key in sorted(rows)],
        "source": source,
        "coordinate_input_used": bool(coordinate_input_used),
        "target_geometry_used": False,
    }


def graph_from_relation_matrix(matrix: np.ndarray, *, edge_quantile: float = 0.80) -> dict[str, Any]:
    """Derive adjacency only from anonymous relation magnitudes.

    ``edge_quantile`` is an observation regulator, not a physical law.  Ties at the threshold are kept
    rather than broken by node labels, preserving permutation invariance at the cost of variable density.
    """
    r = np.asarray(matrix, dtype=float)
    if r.ndim != 2 or r.shape[0] != r.shape[1]:
        raise ValueError("relation matrix must be square")
    if not np.all(np.isfinite(r)):
        return {
            **make_graph(r.shape[0], [], source="relation-matrix-quantile", coordinate_input_used=False),
            "finite": False,
            "edge_quantile": float(edge_quantile),
            "threshold": None,
            "threshold_tie_fraction": None,
        }
    n = int(r.shape[0])
    pairs = [(i, j, float(r[i, j])) for i in range(n) for j in range(i + 1, n)]
    mags = np.asarray([abs(x[2]) for x in pairs], dtype=float)
    q = max(0.0, min(1.0, float(edge_quantile)))
    threshold = float(np.quantile(mags, q)) if mags.size else math.inf
    tol = max(1e-14, abs(threshold) * 1e-12) if math.isfinite(threshold) else 1e-14
    selected = [(i, j, w) for i, j, w in pairs if abs(w) + tol >= threshold and abs(w) > 1e-15]
    ties = int(np.count_nonzero(np.abs(mags - threshold) <= tol)) if mags.size and math.isfinite(threshold) else 0
    graph = make_graph(n, selected, source="relation-matrix-quantile", coordinate_input_used=False)
    graph.update({
        "finite": True,
        "edge_quantile": q,
        "threshold": None if not math.isfinite(threshold) else threshold,
        "threshold_tie_fraction": 0.0 if not mags.size else ties / len(mags),
        "relation_matrix_labels_have_physical_identity": False,
        "threshold_is_physical_law": False,
    })
    return graph


def _adjacency(graph: dict[str, Any]) -> dict[int, set[int]]:
    nodes = [int(x) for x in graph.get("nodes") or []]
    adj = {i: set() for i in nodes}
    for e in graph.get("edges") or []:
        a, b = int(e["a"]), int(e["b"])
        if a in adj and b in adj and a != b:
            adj[a].add(b)
            adj[b].add(a)
    return adj


def components(graph: dict[str, Any]) -> list[list[int]]:
    adj = _adjacency(graph)
    unseen = set(adj)
    out: list[list[int]] = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        stack = [root]
        comp: list[int] = []
        while stack:
            i = stack.pop()
            comp.append(i)
            for j in sorted(adj[i]):
                if j in unseen:
                    unseen.remove(j)
                    stack.append(j)
        out.append(sorted(comp))
    out.sort(key=lambda c: (-len(c), c))
    return out


def _subgraph_edges(graph: dict[str, Any], nodes: set[int]) -> list[dict[str, Any]]:
    return [e for e in (graph.get("edges") or []) if int(e["a"]) in nodes and int(e["b"]) in nodes]


def _triangle_count(adj: dict[int, set[int]], nodes: Iterable[int]) -> int:
    ids = sorted(nodes)
    count = 0
    for a, b, c in itertools.combinations(ids, 3):
        if b in adj[a] and c in adj[a] and c in adj[b]:
            count += 1
    return count


def component_signature(graph: dict[str, Any], component: Iterable[int]) -> dict[str, Any]:
    """Label-free structural signature. Node IDs never enter the signature itself."""
    ids = set(int(x) for x in component)
    adj = _adjacency(graph)
    edges = _subgraph_edges(graph, ids)
    degrees = sorted(len(adj[i] & ids) for i in ids)
    weights = [float(e.get("weight", 0.0)) for e in edges]
    signs = [int(e.get("sign", 1)) for e in edges]
    n, m = len(ids), len(edges)
    cycle_rank = max(0, m - n + (1 if n else 0))
    possible = max(1, n * (n - 1) // 2)
    return {
        "node_count": n,
        "edge_count": m,
        "edge_density": m / possible if n >= 2 else 0.0,
        "degree_sequence": degrees,
        "mean_degree": 0.0 if not degrees else float(np.mean(degrees)),
        "degree_std": 0.0 if not degrees else float(np.std(degrees)),
        "cycle_rank": cycle_rank,
        "triangle_count": _triangle_count(adj, ids),
        "weight_mean": 0.0 if not weights else float(np.mean(weights)),
        "weight_std": 0.0 if not weights else float(np.std(weights)),
        "positive_edges": sum(x >= 0 for x in signs),
        "negative_edges": sum(x < 0 for x in signs),
    }


def _canonical_graph_signature(graph: dict[str, Any]) -> dict[str, Any]:
    sigs = [component_signature(graph, c) for c in components(graph)]
    compact = [
        {
            "n": s["node_count"], "m": s["edge_count"], "deg": s["degree_sequence"],
            "cycle": s["cycle_rank"], "tri": s["triangle_count"],
            "pos": s["positive_edges"], "neg": s["negative_edges"],
        }
        for s in sigs
    ]
    compact.sort(key=lambda s: (s["n"], s["m"], s["deg"], s["cycle"], s["tri"], s["pos"], s["neg"]))
    return {"components": compact, "digest": _compact_hash(compact)}


def _bfs_distances(adj: dict[int, set[int]], source: int, allowed: set[int]) -> dict[int, int]:
    dist = {source: 0}
    queue = [source]
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        for j in adj[i]:
            if j not in allowed or j in dist:
                continue
            dist[j] = dist[i] + 1
            queue.append(j)
    return dist


def _linear_fit(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    if len(xs) < 2 or len(xs) != len(ys):
        return None, None
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if float(np.std(x)) <= 1e-12:
        return None, None
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    denom = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 if denom <= 1e-15 else max(0.0, 1.0 - float(np.sum((y - pred) ** 2)) / denom)
    return float(slope), float(r2)


def _ball_growth(adj: dict[int, set[int]], comp: list[int]) -> dict[str, Any]:
    allowed = set(comp)
    if len(comp) < 4:
        return {"dimension_candidate": None, "fit_r2": None, "local_dimension_mean": None, "local_dimension_cv": None}
    dists = {i: _bfs_distances(adj, i, allowed) for i in comp}
    finite = [d for row in dists.values() for d in row.values()]
    diameter = max(finite) if finite else 0
    xs, ys = [], []
    profile = []
    for radius in range(1, max(1, diameter) + 1):
        counts = [sum(1 for j, d in dists[i].items() if j != i and d <= radius) for i in comp]
        mean_count = float(np.mean(counts)) if counts else 0.0
        profile.append({"radius": radius, "mean_nodes_within": mean_count})
        if mean_count > 0.0 and mean_count < 0.90 * (len(comp) - 1):
            xs.append(math.log(float(radius)))
            ys.append(math.log(mean_count))
    slope, r2 = _linear_fit(xs, ys)

    local_slopes: list[float] = []
    for i in comp:
        lx, ly = [], []
        for radius in range(1, max(1, diameter) + 1):
            count = sum(1 for j, d in dists[i].items() if j != i and d <= radius)
            if count > 0 and count < 0.90 * (len(comp) - 1):
                lx.append(math.log(float(radius)))
                ly.append(math.log(float(count)))
        ls, _ = _linear_fit(lx, ly)
        if ls is not None and math.isfinite(ls):
            local_slopes.append(ls)
    local_mean = None if not local_slopes else float(np.mean(local_slopes))
    local_std = None if not local_slopes else float(np.std(local_slopes))
    local_cv = None if local_mean is None or abs(local_mean) <= 1e-12 else abs(float(local_std or 0.0) / local_mean)
    return {
        "dimension_candidate": slope,
        "fit_r2": r2,
        "diameter": diameter,
        "ball_growth_profile": profile,
        "local_dimension_mean": local_mean,
        "local_dimension_std": local_std,
        "local_dimension_cv": local_cv,
        "physical_dimension_claim": False,
    }


def _core_metrics(graph: dict[str, Any]) -> dict[str, Any]:
    comps = components(graph)
    adj = _adjacency(graph)
    largest = comps[0] if comps else []
    degrees = [len(adj[i]) for i in adj]
    path_values: list[int] = []
    if largest:
        allowed = set(largest)
        for i in largest:
            row = _bfs_distances(adj, i, allowed)
            path_values.extend(d for j, d in row.items() if j > i)
    growth = _ball_growth(adj, largest)
    n = len(adj)
    m = len(graph.get("edges") or [])
    canonical = _canonical_graph_signature(graph)
    return {
        "node_count": n,
        "edge_count": m,
        "component_count": len(comps),
        "component_sizes": sorted((len(c) for c in comps), reverse=True),
        "largest_component_fraction": 0.0 if n <= 0 else len(largest) / n,
        "mean_degree": 0.0 if not degrees else float(np.mean(degrees)),
        "mean_graph_distance": None if not path_values else float(np.mean(path_values)),
        "graph_diameter": None if not path_values else int(max(path_values)),
        "canonical_signature_digest": canonical["digest"],
        **growth,
    }


def permute_graph_labels(graph: dict[str, Any], *, seed: int = 0) -> dict[str, Any]:
    nodes = [int(x) for x in graph.get("nodes") or []]
    shuffled = list(nodes)
    random.Random(seed).shuffle(shuffled)
    mapping = dict(zip(nodes, shuffled))
    edges = [
        (mapping[int(e["a"])], mapping[int(e["b"])], float(e.get("signed_weight", e.get("weight", 1.0))))
        for e in graph.get("edges") or []
    ]
    return make_graph(len(nodes), edges, source="anonymous-label-permutation-control", coordinate_input_used=False)


def degree_preserving_rewire(graph: dict[str, Any], *, seed: int = 0, swaps: int | None = None) -> dict[str, Any]:
    """Destroy specific relation pairing while approximately preserving node degrees and edge count."""
    edges = [
        (_edge_key(int(e["a"]), int(e["b"])), float(e.get("signed_weight", e.get("weight", 1.0))))
        for e in graph.get("edges") or []
    ]
    if len(edges) < 2:
        return make_graph(len(graph.get("nodes") or []), [(a, b, w) for (a, b), w in edges], source="rewire-control")
    rng = random.Random(seed)
    target = max(1, int(swaps if swaps is not None else len(edges) * 4))
    mapping = {key: weight for key, weight in edges}
    keys = list(mapping)
    changed = 0
    for _ in range(target * 12):
        if len(keys) < 2 or changed >= target:
            break
        e1, e2 = rng.sample(keys, 2)
        a, b = e1
        c, d = e2
        if len({a, b, c, d}) < 4:
            continue
        proposals = [(_edge_key(a, d), _edge_key(c, b)), (_edge_key(a, c), _edge_key(b, d))]
        p1, p2 = proposals[rng.randrange(len(proposals))]
        if p1 == p2 or p1 in mapping or p2 in mapping or p1[0] == p1[1] or p2[0] == p2[1]:
            continue
        w1, w2 = mapping.pop(e1), mapping.pop(e2)
        mapping[p1], mapping[p2] = w1, w2
        keys = list(mapping)
        changed += 1
    out = make_graph(
        len(graph.get("nodes") or []),
        [(a, b, w) for (a, b), w in mapping.items()],
        source="degree-preserving-relation-destroying-control",
        coordinate_input_used=False,
    )
    out["rewire_swaps_completed"] = changed
    return out


def _holdout_check(graph: dict[str, Any], *, seed: int = 0) -> dict[str, Any]:
    edges = list(graph.get("edges") or [])
    nodes = [int(x) for x in graph.get("nodes") or []]
    if len(edges) < 4 or len(nodes) < 4:
        return {"available": False, "reason": "too-few-relations"}
    scored = sorted(
        edges,
        key=lambda e: hashlib.sha256(f"{seed}:{min(int(e['a']), int(e['b']))}:{max(int(e['a']), int(e['b']))}".encode()).hexdigest(),
    )
    k = max(1, min(len(edges) // 4, len(edges) - 2))
    holdout = scored[:k]
    held_keys = {_edge_key(int(e["a"]), int(e["b"])) for e in holdout}
    train_edges = [
        (int(e["a"]), int(e["b"]), float(e.get("signed_weight", e.get("weight", 1.0))))
        for e in edges if _edge_key(int(e["a"]), int(e["b"])) not in held_keys
    ]
    train = make_graph(len(nodes), train_edges, source="temporal-free-edge-holdout-train")
    adj = _adjacency(train)
    original_keys = {_edge_key(int(e["a"]), int(e["b"])) for e in edges}
    nonedges = [p for p in itertools.combinations(nodes, 2) if _edge_key(*p) not in original_keys]
    if not nonedges:
        return {"available": False, "reason": "no-nonedge-control"}
    rng = random.Random(seed ^ 0xA517)
    rng.shuffle(nonedges)
    controls = nonedges[:k]

    def distance(pair: tuple[int, int]) -> float:
        row = _bfs_distances(adj, pair[0], set(nodes))
        return float(row.get(pair[1], math.inf))

    held_dist = [distance(_edge_key(int(e["a"]), int(e["b"]))) for e in holdout]
    ctrl_dist = [distance(_edge_key(*p)) for p in controls]
    wins = []
    for h, c in zip(held_dist, ctrl_dist):
        if h < c:
            wins.append(1.0)
        elif h == c:
            wins.append(0.5)
        else:
            wins.append(0.0)
    finite_held = [x for x in held_dist if math.isfinite(x)]
    finite_ctrl = [x for x in ctrl_dist if math.isfinite(x)]
    return {
        "available": True,
        "heldout_edges": len(holdout),
        "matched_nonedge_controls": len(controls),
        "heldout_reachable_fraction": len(finite_held) / len(held_dist),
        "holdout_vs_nonedge_advantage": float(np.mean(wins)) if wins else None,
        "heldout_mean_graph_distance": None if not finite_held else float(np.mean(finite_held)),
        "control_mean_graph_distance": None if not finite_ctrl else float(np.mean(finite_ctrl)),
        "future_or_target_labels_used": False,
    }


def metric_with_controls(graph: dict[str, Any], *, seed: int = 0, rewire_replicates: int = 3) -> dict[str, Any]:
    core = _core_metrics(graph)
    perm = _core_metrics(permute_graph_labels(graph, seed=seed ^ 0x19))
    permutation_pass = (
        core.get("canonical_signature_digest") == perm.get("canonical_signature_digest")
        and core.get("component_sizes") == perm.get("component_sizes")
    )
    holdout = _holdout_check(graph, seed=seed)
    rewired = []
    for i in range(max(0, int(rewire_replicates))):
        g = degree_preserving_rewire(graph, seed=seed + 101 * (i + 1))
        m = _core_metrics(g)
        m["rewire_swaps_completed"] = g.get("rewire_swaps_completed", 0)
        rewired.append(m)

    def structure_score(m: dict[str, Any]) -> float | None:
        r2 = m.get("fit_r2")
        cv = m.get("local_dimension_cv")
        if r2 is None or cv is None or not _finite(r2) or not _finite(cv):
            return None
        return float(r2) / (1.0 + max(0.0, float(cv)))

    observed_score = structure_score(core)
    null_scores = [x for x in (structure_score(m) for m in rewired) if x is not None]
    null_mean = None if not null_scores else float(np.mean(null_scores))
    null_delta = None if observed_score is None or null_mean is None else observed_score - null_mean
    holdout_adv = holdout.get("holdout_vs_nonedge_advantage") if holdout.get("available") else None
    candidate = bool(
        permutation_pass
        and core.get("dimension_candidate") is not None
        and float(core.get("fit_r2") or 0.0) >= 0.75
        and core.get("local_dimension_cv") is not None
        and float(core.get("local_dimension_cv") or 99.0) <= 0.60
        and holdout_adv is not None and float(holdout_adv) >= 0.65
        and null_delta is not None and float(null_delta) >= 0.08
    )
    return {
        **core,
        "instrument": "metric-from-relations",
        "instrument_version": INSTRUMENT_VERSION,
        "status": "RELATIONAL_METRIC_STRUCTURE_CANDIDATE" if candidate else "MEASURED_NO_METRIC_LEAD",
        "permutation_control_passed": permutation_pass,
        "holdout": holdout,
        "relation_destroying_controls": rewired,
        "structure_score": observed_score,
        "rewire_structure_score_mean": null_mean,
        "structure_score_excess_vs_rewire": null_delta,
        "coordinate_input_used": bool(graph.get("coordinate_input_used", False)),
        "target_geometry_used": False,
        "physical_space_claim": False,
        "fundamental_dimension_claim": False,
        "gravity_claim": False,
    }


def _signature_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    def rel(x: float, y: float, floor: float = 1.0) -> float:
        return min(1.0, abs(x - y) / max(floor, abs(x), abs(y)))

    return min(1.0,
        0.28 * rel(float(a["node_count"]), float(b["node_count"]))
        + 0.16 * abs(float(a["edge_density"]) - float(b["edge_density"]))
        + 0.12 * rel(float(a["mean_degree"]), float(b["mean_degree"]))
        + 0.10 * rel(float(a["degree_std"]), float(b["degree_std"]))
        + 0.10 * rel(float(a["cycle_rank"]), float(b["cycle_rank"]))
        + 0.08 * rel(float(a["triangle_count"]), float(b["triangle_count"]))
        + 0.10 * rel(float(a["weight_mean"]), float(b["weight_mean"]), floor=1e-6)
        + 0.06 * rel(float(a["weight_std"]), float(b["weight_std"]), floor=1e-6)
    )


def _candidate_components(graph: dict[str, Any]) -> list[dict[str, Any]]:
    n = len(graph.get("nodes") or [])
    out = []
    for c in components(graph):
        # The whole universe-as-one-component is not counted as an individual candidate.
        if len(c) < 2 or len(c) >= n:
            continue
        out.append({"nodes": c, "signature": component_signature(graph, c)})
    return out


def _track_core(graphs: list[dict[str, Any]]) -> dict[str, Any]:
    frames = [_candidate_components(g) for g in graphs]
    tracks: dict[int, dict[str, Any]] = {}
    previous: list[dict[str, Any]] = []
    next_id = 1
    ambiguity_events = 0
    associations = 0
    births = 0
    deaths = 0
    frame_track_ids: list[list[int]] = []

    for frame_index, current in enumerate(frames):
        if not previous:
            ids = []
            for c in current:
                tid = next_id
                next_id += 1
                tracks[tid] = {"track_id": tid, "frames": [frame_index], "signatures": [c["signature"]], "ambiguity_count": 0}
                c["track_id"] = tid
                ids.append(tid)
                births += 1
            previous = current
            frame_track_ids.append(ids)
            continue

        proposals: list[tuple[float, int, int]] = []
        for pi, p in enumerate(previous):
            for ci, c in enumerate(current):
                proposals.append((_signature_distance(p["signature"], c["signature"]), pi, ci))
        proposals.sort()
        used_prev: set[int] = set()
        used_curr: set[int] = set()
        for cost, pi, ci in proposals:
            if cost > 0.34 or pi in used_prev or ci in used_curr:
                continue
            # Explicit ambiguity: another available current candidate is nearly as good for this parent.
            alternatives = [
                x[0] for x in proposals
                if x[1] == pi and x[2] != ci and x[2] not in used_curr and x[0] <= 0.34
            ]
            ambiguous = bool(alternatives and abs(min(alternatives) - cost) <= 0.04)
            tid = int(previous[pi]["track_id"])
            current[ci]["track_id"] = tid
            tracks[tid]["frames"].append(frame_index)
            tracks[tid]["signatures"].append(current[ci]["signature"])
            tracks[tid]["ambiguity_count"] += int(ambiguous)
            ambiguity_events += int(ambiguous)
            associations += 1
            used_prev.add(pi)
            used_curr.add(ci)
        deaths += len(previous) - len(used_prev)
        for ci, c in enumerate(current):
            if ci in used_curr:
                continue
            tid = next_id
            next_id += 1
            c["track_id"] = tid
            tracks[tid] = {"track_id": tid, "frames": [frame_index], "signatures": [c["signature"]], "ambiguity_count": 0}
            births += 1
        previous = current
        frame_track_ids.append([int(c["track_id"]) for c in current])

    deaths += len(previous)
    lengths = [len(t["frames"]) for t in tracks.values()]
    normalized = [x / max(1, len(graphs)) for x in lengths]
    return {
        "tracks": list(tracks.values()),
        "frame_track_ids": frame_track_ids,
        "track_count": len(tracks),
        "persistent_tracks_3plus": sum(x >= 3 for x in lengths),
        "longest_track_frames": max(lengths, default=0),
        "mean_normalized_persistence": 0.0 if not normalized else float(np.mean(normalized)),
        "association_count": associations,
        "ambiguity_events": ambiguity_events,
        "ambiguity_rate": 0.0 if associations <= 0 else ambiguity_events / associations,
        "birth_events": births,
        "death_events": deaths,
    }


def identity_continuity(graphs: list[dict[str, Any]], *, seed: int = 0) -> dict[str, Any]:
    observed = _track_core(graphs)
    order = list(range(len(graphs)))
    random.Random(seed ^ 0x1D37).shuffle(order)
    shuffled_graphs = [graphs[i] for i in order]
    shuffled = _track_core(shuffled_graphs) if len(graphs) >= 2 else observed
    excess = float(observed["mean_normalized_persistence"]) - float(shuffled["mean_normalized_persistence"])
    candidate = bool(
        int(observed["persistent_tracks_3plus"]) > 0
        and float(observed["ambiguity_rate"]) <= 0.25
        and excess >= 0.15
    )
    return {
        "instrument": "identity-continuity",
        "instrument_version": INSTRUMENT_VERSION,
        "status": "IDENTITY_CONTINUITY_CANDIDATE" if candidate else "MEASURED_NO_IDENTITY_LEAD",
        "observed": observed,
        "shuffled_time_control": {
            "frame_order": order,
            "mean_normalized_persistence": shuffled["mean_normalized_persistence"],
            "persistent_tracks_3plus": shuffled["persistent_tracks_3plus"],
        },
        "persistence_excess_vs_shuffled_time": excess,
        "association_rule_uses_node_labels": False,
        "target_body_shape_used": False,
        "organism_claim": False,
        "self_claim": False,
        "cell_claim": False,
        "life_claim": False,
    }


def _best_signature_match(target: dict[str, Any], candidates: list[dict[str, Any]]) -> float | None:
    if not candidates:
        return None
    return min(_signature_distance(target, c["signature"]) for c in candidates)


def _inheritance_score(parent: dict[str, Any], a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    pn = max(1.0, float(parent["node_count"]))
    size_error = abs(float(a["node_count"] + b["node_count"] - parent["node_count"])) / pn
    pdeg = max(1e-6, float(parent["mean_degree"]))
    daughter_degree = (
        float(a["mean_degree"]) * float(a["node_count"]) + float(b["mean_degree"]) * float(b["node_count"])
    ) / max(1.0, float(a["node_count"] + b["node_count"]))
    degree_error = min(1.0, abs(daughter_degree - pdeg) / max(1.0, abs(pdeg)))
    pw = max(1e-6, abs(float(parent["weight_mean"])))
    daughter_weight = 0.5 * (float(a["weight_mean"]) + float(b["weight_mean"]))
    weight_error = min(1.0, abs(daughter_weight - float(parent["weight_mean"])) / pw)
    score = max(0.0, 1.0 - 0.50 * min(1.0, size_error) - 0.30 * degree_error - 0.20 * weight_error)
    return {
        "score": score,
        "node_count_error": size_error,
        "mean_degree_error": degree_error,
        "mean_weight_error": weight_error,
    }


def lineage_accounting(graphs: list[dict[str, Any]]) -> dict[str, Any]:
    frames = [_candidate_components(g) for g in graphs]
    candidates: list[dict[str, Any]] = []
    if len(frames) >= 4:
        for t in range(1, len(frames) - 2):
            prev, parents, daughters, after = frames[t - 1], frames[t], frames[t + 1], frames[t + 2]
            for p in parents:
                psig = p["signature"]
                if int(psig["node_count"]) < 4:
                    continue
                parent_persistence = _best_signature_match(psig, prev)
                if parent_persistence is None or parent_persistence > 0.24:
                    continue
                pair_rows = []
                for da, db in itertools.combinations(daughters, 2):
                    accounting = _inheritance_score(psig, da["signature"], db["signature"])
                    da_next = _best_signature_match(da["signature"], after)
                    db_next = _best_signature_match(db["signature"], after)
                    daughters_persist = bool(
                        da_next is not None and db_next is not None and da_next <= 0.24 and db_next <= 0.24
                    )
                    pair_rows.append({
                        "daughter_a": da,
                        "daughter_b": db,
                        "accounting": accounting,
                        "daughters_persist": daughters_persist,
                        "daughter_a_next_cost": da_next,
                        "daughter_b_next_cost": db_next,
                    })
                if not pair_rows:
                    continue
                pair_rows.sort(key=lambda x: float(x["accounting"]["score"]), reverse=True)
                best = pair_rows[0]
                alternatives = [float(x["accounting"]["score"]) for x in pair_rows[1:]]
                control = None if not alternatives else float(np.median(alternatives))
                delta = None if control is None else float(best["accounting"]["score"]) - control
                controlled = bool(
                    best["daughters_persist"]
                    and float(best["accounting"]["score"]) >= 0.75
                    and delta is not None and delta >= 0.15
                )
                candidates.append({
                    "parent_frame": t,
                    "daughter_frame": t + 1,
                    "parent_signature": psig,
                    "parent_persistence_cost": parent_persistence,
                    "daughter_a_signature": best["daughter_a"]["signature"],
                    "daughter_b_signature": best["daughter_b"]["signature"],
                    "daughters_persist": best["daughters_persist"],
                    "inheritance_accounting": best["accounting"],
                    "unrelated_pair_control_score": control,
                    "score_excess_vs_unrelated_pair": delta,
                    "controlled_lineage_candidate": controlled,
                })
    controlled_count = sum(bool(x.get("controlled_lineage_candidate")) for x in candidates)
    return {
        "instrument": "lineage-accounting",
        "instrument_version": INSTRUMENT_VERSION,
        "status": "CONTROLLED_LINEAGE_ACCOUNTING_CANDIDATE" if controlled_count else "MEASURED_NO_LINEAGE_LEAD",
        "candidate_events": candidates,
        "candidate_event_count": len(candidates),
        "controlled_candidate_count": controlled_count,
        "persistent_parent_required": True,
        "persistent_daughters_required": True,
        "node_labels_used_as_parent_daughter_identity": False,
        "biological_cell_division_claim": False,
        "reproduction_claim": False,
        "heredity_claim": False,
        "life_claim": False,
    }


def _even_sample(values: list[Any], max_items: int) -> list[Any]:
    if len(values) <= max_items:
        return list(values)
    if max_items <= 1:
        return [values[-1]]
    idx = sorted({round(i * (len(values) - 1) / (max_items - 1)) for i in range(max_items)})
    return [values[int(i)] for i in idx]


def analyze_graph_series(graphs: list[dict[str, Any]], *, seed: int = 0, max_frames: int = 8) -> dict[str, Any]:
    sampled = _even_sample(graphs, max(2, int(max_frames))) if graphs else []
    metrics = [metric_with_controls(g, seed=seed + i * 7919) for i, g in enumerate(sampled)]
    metric_candidates = [m for m in metrics if m.get("status") == "RELATIONAL_METRIC_STRUCTURE_CANDIDATE"]
    identity = identity_continuity(sampled, seed=seed) if sampled else {
        "instrument": "identity-continuity", "status": "NOT_MEASURED", "observed": {"track_count": 0}
    }
    lineage = lineage_accounting(sampled) if sampled else {
        "instrument": "lineage-accounting", "status": "NOT_MEASURED", "candidate_event_count": 0,
        "controlled_candidate_count": 0,
    }
    metric_series_lead = bool(len(metric_candidates) >= 3 and len(metric_candidates) >= math.ceil(0.5 * len(metrics)))
    return {
        "version": INSTRUMENT_VERSION,
        "mode": "relation-only-structure-instruments",
        "frames_available": len(graphs),
        "frames_measured": len(sampled),
        "metric": {
            "instrument": "metric-from-relations",
            "status": "RELATIONAL_METRIC_SERIES_CANDIDATE" if metric_series_lead else "MEASURED_NO_SERIES_LEAD",
            "candidate_frames": len(metric_candidates),
            "measured_frames": len(metrics),
            "frames": metrics,
        },
        "identity": identity,
        "lineage": lineage,
        "integrity": {
            "coordinate_input_used": any(bool(g.get("coordinate_input_used")) for g in sampled),
            "anonymous_label_permutation_control": True,
            "relation_destroying_control": True,
            "holdout_control": True,
            "target_morphology_seeded": False,
            "changes_dynamics": False,
            "changes_truth_gate": False,
            "promotes_room_or_level": False,
            "physical_space_claim": False,
            "fundamental_dimension_claim": False,
            "organism_or_life_claim": False,
            "biological_cell_division_claim": False,
        },
    }


def analyze_relation_matrix_series(
    matrices: list[np.ndarray], *, seed: int = 0, max_frames: int = 8, edge_quantile: float = 0.80,
) -> dict[str, Any]:
    sampled = _even_sample(matrices, max(2, int(max_frames))) if matrices else []
    graphs = [graph_from_relation_matrix(r, edge_quantile=edge_quantile) for r in sampled]
    out = analyze_graph_series(graphs, seed=seed, max_frames=max(2, len(graphs)))
    out["source"] = "anonymous-relation-matrix"
    out["edge_quantile"] = float(edge_quantile)
    out["integrity"]["coordinate_input_used"] = False
    out["integrity"]["relation_matrix_node_labels_are_physical_identity"] = False
    out["integrity"]["threshold_is_physical_law"] = False
    return out
