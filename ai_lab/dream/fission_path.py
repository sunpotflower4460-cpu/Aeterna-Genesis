"""Observation-only F0->F7 relation-fission research path for Genesis Dream.

This is NOT a replacement for docs/EMERGENCE_LEVELS.md and it never changes scientific truth gates.
The F prefix is mandatory in reports so these stages cannot be confused with official Emergence Levels.
It answers a narrower research question: in one uninterrupted run that starts without object-like
structures, how far does the following relation-fission path arise on its own?

F0 almost-uniform/random start
F1 difference emerges
F2 local defects/vortices emerge
F3 local structures form a persistent relation
F4 a persistent balanced triangle appears (one possible measured route, never required by physics)
F5 that balance visibly breaks while the local group is still one group
F6 the one local group remains connected but becomes an instability candidate
F7 the relation network persistently separates into 2+ groups after that instability

F7 is deliberately called a relation-network fission candidate, NOT biological cell division and NOT
official Emergence Level 7. A future morphology/body detector is required before making a stronger
individual-division claim.
"""
from __future__ import annotations

from typing import Any

PATH_PREFIX = "F"
STAGES = {
    0: "ほぼ何もない揺らぎから開始",
    1: "違いが生まれる",
    2: "渦などの局所構造が生まれる",
    3: "局所構造どうしが持続する関係を作る",
    4: "三角形などの一時的な安定配置になる",
    5: "その配置のバランスが崩れる",
    6: "1つの関係網のまま不安定化する",
    7: "関係網が2つ以上へ持続的に分かれる",
}

# Strict path claims exclude object-like amplitude scaffolds. Correlated/random spectra are allowed
# because they place no discrete object, vortex, division site, or target geometry.  They are however
# explicitly weaker zero-purity than white noise because they impose a correlation/scale structure.
MINIMAL_RANDOM_FAMILIES = {
    "white",
    "white_lowk",
    "white_highk",
    "spectral_powerlaw",
    "bandpass",
}


def stage_code(stage: int) -> str:
    return f"{PATH_PREFIX}{stage}"


def start_purity(family: str | None) -> str:
    if family == "white":
        return "Z-A:minimal-white"
    if family in MINIMAL_RANDOM_FAMILIES:
        return "Z-B:random-field-no-objects-with-declared-scale"
    return "scaffolded-start"


def strict_zero_eligible(family: str | None) -> bool:
    return family in MINIMAL_RANDOM_FAMILIES


def assess_probe(probe: dict[str, Any]) -> dict[str, Any]:
    """Return the deepest CONTIGUOUS F-stage reached by one run."""
    family = probe.get("family")
    level = int(probe.get("reached_level") or 0)
    eligible = strict_zero_eligible(family)
    flags = {
        0: bool(eligible),
        1: bool(eligible and level >= 1),
        2: bool(eligible and level >= 2),
        3: bool(eligible and level >= 2 and probe.get("persistent_relation_seen")),
        4: bool(eligible and level >= 2 and probe.get("triangle_seen")),
        5: bool(eligible and probe.get("balance_collapse_seen")),
        6: bool(eligible and probe.get("pre_split_instability_candidate")),
        7: bool(eligible and probe.get("network_fission_candidate")),
    }
    depth = -1
    for stage in range(8):
        if flags[stage]:
            depth = stage
        else:
            break
    next_stage = min(7, depth + 1) if depth >= 0 else 0
    return {
        "path_id": "relation-fission-F",
        "path_stage_prefix": PATH_PREFIX,
        "strict_zero_eligible": eligible,
        "start_purity": start_purity(family),
        "depth": depth,
        "depth_code": stage_code(depth) if depth >= 0 else None,
        "next_stage": next_stage,
        "next_stage_code": stage_code(next_stage),
        "flags": {str(k): bool(v) for k, v in flags.items()},
        "stage_label": STAGES.get(depth),
        "next_stage_label": STAGES.get(next_stage),
        "network_fission_is_biological_cell_division": False,
        "changes_official_emergence_level": False,
    }


def _frontier_item(item: dict[str, Any]) -> dict[str, Any]:
    depth = int(item["path"]["depth"])
    next_stage = min(7, depth + 1)
    return {
        "trial_index": item.get("trial_index"),
        "family": item.get("family"),
        "knobs": item.get("knobs") or {},
        "seed": item.get("seed"),
        "depth": depth,
        "depth_code": stage_code(depth),
        "stage_label": STAGES.get(depth),
        "next_stage": next_stage,
        "next_stage_code": stage_code(next_stage),
        "next_stage_label": STAGES.get(next_stage),
        "source": "relation-fission-F-path",
    }


def summarize(probes: list[dict[str, Any]]) -> dict[str, Any]:
    assessed: list[dict[str, Any]] = []
    for p in probes:
        path = p.get("zero_to_fission") or assess_probe(p)
        if int(path.get("depth", -1)) < 0:
            continue
        assessed.append({
            "path": path,
            "trial_index": p.get("trial_index"),
            "family": p.get("family"),
            "knobs": p.get("knobs") or {},
            "seed": p.get("seed"),
            "triangle_seen": bool(p.get("triangle_seen")),
            "balance_collapse_seen": bool(p.get("balance_collapse_seen")),
            "network_fission_candidate": bool(p.get("network_fission_candidate")),
        })

    counts = {str(i): 0 for i in range(8)}
    for item in assessed:
        depth = int(item["path"]["depth"])
        for i in range(depth + 1):
            counts[str(i)] += 1

    assessed.sort(key=lambda x: int(x["path"]["depth"]), reverse=True)
    deepest = int(assessed[0]["path"]["depth"]) if assessed else -1
    frontier_candidates = [_frontier_item(x) for x in assessed[:6]]
    best_frontier = frontier_candidates[0] if frontier_candidates else None

    return {
        "version": 2,
        "path_id": "relation-fission-F",
        "path_stage_prefix": PATH_PREFIX,
        "goal": "同じrunで、0の未分化状態から関係網の分離候補まで自然に連続して進む経路を見つける",
        "stages": {stage_code(k): v for k, v in STAGES.items()},
        "strict_zero_eligible_probes": len(assessed),
        "stage_reached_counts": {stage_code(int(k)): v for k, v in counts.items()},
        "deepest_contiguous_stage": deepest,
        "deepest_code": stage_code(deepest) if deepest >= 0 else None,
        "deepest_label": STAGES.get(deepest),
        "best_frontier_candidate": best_frontier,
        "frontier_candidates": frontier_candidates,
        "triangle_is_required": False,
        "triangle_is_one_hypothesis_route": True,
        "network_fission_is_biological_cell_division": False,
        "official_emergence_levels_unchanged": True,
        "note": (
            "F0〜F7は公式Emergence Levelではない。三角形を初期条件に置いたり、分裂位置・時刻を与えたりしない。"
            "深さは同じrun内で前段を飛ばさず連続到達した場合だけ数える。"
        ),
    }
