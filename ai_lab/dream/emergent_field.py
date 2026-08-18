"""Uniform-field frontier search for spontaneous morphology under an existing local law.

This lane is deliberately NOT a network/brain generator.  It reuses the existing Gray-Scott
reaction-diffusion law and changes only shape-free start conditions + ordinary law parameters:

    spatially uniform U/V background + small iid noise, periodic boundary, t=0 restart.

No spot, node, edge, branch, path, graph, neuron, target image, split site or desired morphology is
seeded.  The dynamics never see the morphology observer.  After the run, an independent observer
measures generic localization/connectivity summaries.  Those summaries are evidence descriptors only:
they do not change official Emergence Levels, Room promotion, truth gates, or the next state update.

The purpose is to let Adaptive Dream occasionally ask a simple frontier question:

    Can an already-allowed local field law, started without founder spots, amplify homogeneous noise
    into persistent differentiated structure?

If the answer is no, that negative result is useful.  If differentiated structure appears, stronger
interpretations require separate controls and later law-variant audits.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy import ndimage

from genesis.models import gray_scott as gs

_REPO = Path(__file__).resolve().parents[2]
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "emergent_field_latest.json"
_REGISTRY = _REPO / "genesis" / "registry" / "param_ranges.yaml"
_PRIMES = (2, 3, 5, 7, 11, 13)


def _load_space() -> dict[str, tuple[float, float]]:
    """Registry is the single source of truth for every automatically varied physical/start parameter."""
    raw = yaml.safe_load(_REGISTRY.read_text())
    spec = raw["search_space"]["model_specific"]["gray_scott_uniform_noise"]
    keys = ("Du", "Dv", "F", "k", "v_background", "noise_amplitude")
    return {key: (float(spec[key]["min"]), float(spec[key]["max"])) for key in keys}


SPACE = _load_space()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _vdc(index: int, base: int) -> float:
    n = max(1, int(index))
    denom = 1.0
    out = 0.0
    while n:
        n, rem = divmod(n, base)
        denom *= base
        out += rem / denom
    return out


def _halton(index: int) -> list[float]:
    return [_vdc(index + 1, p) for p in _PRIMES]


def _lin(u: float, lo: float, hi: float) -> float:
    return float(lo + (hi - lo) * min(1.0, max(0.0, u)))


def _log(u: float, lo: float, hi: float) -> float:
    return float(10 ** _lin(u, math.log10(lo), math.log10(hi)))


def trial_parameters(index: int, *, seed: int) -> dict[str, float]:
    """Deterministic low-discrepancy parameter sample; no outcome feedback is used."""
    u = _halton(int(index) + int(seed) * 17)
    return {
        "Du": _lin(u[0], *SPACE["Du"]),
        "Dv": _lin(u[1], *SPACE["Dv"]),
        "F": _lin(u[2], *SPACE["F"]),
        "k": _lin(u[3], *SPACE["k"]),
        "v_background": _lin(u[4], *SPACE["v_background"]),
        "noise_amplitude": _log(u[5], *SPACE["noise_amplitude"]),
    }


def make_uniform_noise_initial(
    shape: tuple[int, int], *, v_background: float, noise_amplitude: float, rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Shape-free IC: uniform chemistry plus iid noise; there are no hand-placed founder spots."""
    v0 = float(min(0.20, max(0.0, v_background)))
    amp = float(max(0.0, noise_amplitude))
    noise = rng.standard_normal(shape)
    # The pre-clipping perturbation is zero-mean and translation-unbiased.  Clipping only enforces
    # concentration bounds; it never steers a location toward a target morphology.
    V = np.clip(v0 + amp * noise, 0.0, 1.0)
    U = np.clip(1.0 - v0 - amp * noise, 0.0, 1.0)
    return U.astype(float), V.astype(float)


def _component_sizes(mask: np.ndarray) -> tuple[np.ndarray, dict[int, int]]:
    """4-neighbour connected components with periodic wrap, matching the physical boundary."""
    labels, n = ndimage.label(mask)
    if n == 0:
        return labels, {}

    parent = list(range(n + 1))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        if not a or not b:
            return
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for i in range(mask.shape[0]):
        union(int(labels[i, 0]), int(labels[i, -1]))
    for j in range(mask.shape[1]):
        union(int(labels[0, j]), int(labels[-1, j]))

    roots = np.zeros_like(labels)
    sizes: dict[int, int] = {}
    for lab in range(1, n + 1):
        root = find(lab)
        pixels = labels == lab
        roots[pixels] = root
        sizes[root] = sizes.get(root, 0) + int(np.count_nonzero(pixels))
    return roots, sizes


def observe_morphology(initial_v: np.ndarray, final_v: np.ndarray, previous_v: np.ndarray | None = None) -> dict[str, Any]:
    """Outcome-agnostic morphology observer, completely separated from the dynamics.

    Thresholds are fixed relative to the INITIAL fluctuation scale, so every final field is not forced to
    contain a percentile-defined feature.  We threshold absolute departure from the homogeneous initial
    mean so both positive and negative differentiation are visible.  A corridor candidate is merely an
    active periodic component containing >=2 separate strict cores.  It is NOT called an edge/network.
    """
    init = np.asarray(initial_v, dtype=float)
    final = np.asarray(final_v, dtype=float)
    base_mean = float(np.mean(init))
    sigma0 = max(float(np.std(init)), 1.0e-12)
    active_threshold = 4.0 * sigma0
    core_threshold = 8.0 * sigma0
    departure = np.abs(final - base_mean)
    active = departure > active_threshold
    cores = departure > core_threshold
    active_labels, active_sizes_all = _component_sizes(active)
    core_labels, core_sizes_all = _component_sizes(cores)

    # A near-global phase/background shift is not a localized object.  Keep it in active_fraction but do
    # not count a component occupying most of the domain as a localized region/core.
    domain_area = int(final.size)
    max_local_area = max(1, int(0.50 * domain_area))
    active_sizes = {k: v for k, v in active_sizes_all.items() if v <= max_local_area}
    core_sizes = {k: v for k, v in core_sizes_all.items() if v <= max_local_area}

    corridor_candidates = 0
    valid_core_ids = set(core_sizes)
    for aid in active_sizes:
        core_ids = {int(x) for x in np.unique(core_labels[active_labels == aid]) if int(x) > 0}
        if len(core_ids & valid_core_ids) >= 2:
            corridor_candidates += 1

    boundary = np.logical_xor(active, np.roll(active, 1, 0)) | np.logical_xor(active, np.roll(active, 1, 1))
    active_area = int(np.count_nonzero(active))
    perimeter_proxy = int(np.count_nonzero(boundary))
    filamentarity_proxy = float(perimeter_proxy / max(1.0, math.sqrt(max(active_area, 1))))

    persistence = None
    if previous_v is not None:
        a = np.asarray(previous_v, dtype=float).ravel()
        b = final.ravel()
        a = a - a.mean()
        b = b - b.mean()
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        persistence = float(np.dot(a, b) / denom) if denom > 1.0e-15 else 0.0

    return {
        "initial_mean_v": base_mean,
        "initial_sigma_v": sigma0,
        "final_mean_v": float(np.mean(final)),
        "final_sigma_v": float(np.std(final)),
        "fluctuation_gain": float(np.std(final) / sigma0),
        "active_departure_threshold": active_threshold,
        "core_departure_threshold": core_threshold,
        "active_fraction": float(np.mean(active)),
        "localized_region_count": len(active_sizes),
        "strong_core_count": len(core_sizes),
        "largest_region_area": max(active_sizes.values(), default=0),
        "corridor_candidate_count": int(corridor_candidates),
        "filamentarity_proxy": filamentarity_proxy,
        "late_field_persistence": persistence,
        "periodic_component_merging": True,
        "global_components_excluded_from_localized_count": True,
        "observer_semantics": {
            "localized_region": "periodic connected region whose absolute departure exceeds a fixed initial-noise-relative threshold and covers <=50% of the domain",
            "corridor_candidate": "one localized active region containing two or more separate stricter localized cores",
            "network_claim": False,
            "node_claim": False,
            "edge_claim": False,
        },
    }


def _observation_priority(obs: dict[str, Any]) -> float:
    """Reader-attention ranking only; never a scientific success gate or feedback controller."""
    gain = min(3.0, math.log10(max(1.0, float(obs.get("fluctuation_gain") or 1.0)))) / 3.0
    occupied = min(1.0, float(obs.get("active_fraction") or 0.0) * 8.0)
    diversity = min(1.0, math.log1p(int(obs.get("localized_region_count") or 0)) / math.log(12.0))
    persistence = max(0.0, float(obs.get("late_field_persistence") or 0.0))
    return round(0.40 * gain + 0.20 * occupied + 0.20 * diversity + 0.20 * persistence, 6)


def run_trial(index: int, *, master_seed: int, shape: tuple[int, int] = (64, 64), steps: int = 320) -> dict[str, Any]:
    params = trial_parameters(index, seed=master_seed)
    trial_seed = int(hashlib.sha256(f"emergent-field|{master_seed}|{index}".encode()).hexdigest()[:12], 16) % 1_000_000
    rng = np.random.default_rng(trial_seed)
    U, V = make_uniform_noise_initial(
        shape, v_background=params["v_background"], noise_amplitude=params["noise_amplitude"], rng=rng,
    )
    initial_v = V.copy()
    p = {"Du": params["Du"], "Dv": params["Dv"], "F": params["F"], "k": params["k"], "dt": 1.0}
    previous_v = None
    finite = True
    total_steps = max(1, int(steps))
    for t in range(total_steps):
        U, V = gs.step(U, V, p)
        if not np.all(np.isfinite(U)) or not np.all(np.isfinite(V)):
            finite = False
            break
        if t == total_steps - 9:
            previous_v = V.copy()
    if not finite:
        return {
            "trial_index": int(index), "seed": trial_seed, "parameters": params,
            "status": "numerically_unstable", "observations": None, "observation_priority": None,
        }
    obs = observe_morphology(initial_v, V, previous_v=previous_v)
    checksum = hashlib.sha256(np.ascontiguousarray(V).tobytes()).hexdigest()[:16]
    return {
        "trial_index": int(index),
        "seed": trial_seed,
        "parameters": params,
        "status": "observed",
        "observations": obs,
        "observation_priority": _observation_priority(obs),
        "checksum": checksum,
    }


def run_emergent_field_research(
    *, burst_id: str, trials: int = 12, seed: int = 0, quick: bool = False, persist: bool = True,
) -> dict[str, Any]:
    """Run a bounded non-feedback search from homogeneous/noisy starts.

    Every trial is chosen before outcomes are known.  Results are sorted only for human inspection after
    all runs complete; the ordering cannot alter the parameter plan or the physical dynamics.
    """
    n = max(0, int(trials))
    shape = (48, 48) if quick else (64, 64)
    steps = 120 if quick else 320
    rows = [run_trial(i, master_seed=int(seed), shape=shape, steps=steps) for i in range(n)]
    stable = [r for r in rows if r.get("status") == "observed"]
    ranked = sorted(stable, key=lambda r: float(r.get("observation_priority") or 0.0), reverse=True)
    report = {
        "version": 1,
        "mode": "uniform-noise-existing-law-frontier",
        "burst_id": str(burst_id),
        "research_question": "Can a homogeneous Gray-Scott field plus small unstructured noise amplify into persistent differentiated morphology without founder spots?",
        "trials": n,
        "shape": list(shape),
        "steps": steps,
        "search_policy": {
            "parameter_selection": "deterministic_halton_before_outcomes",
            "parameter_bounds_source": "genesis/registry/param_ranges.yaml::search_space.model_specific.gray_scott_uniform_noise",
            "feedback_from_morphology_to_dynamics": False,
            "target_image_or_graph_objective": False,
            "official_level_gate_changed": False,
            "room_promotion_changed": False,
        },
        "initial_condition": {
            "spatial_pattern": "uniform_background_plus_unstructured_gaussian_perturbation",
            "founder_spots": 0,
            "seeded_nodes": 0,
            "seeded_edges": 0,
            "seeded_branches": 0,
            "target_morphology_seeded": False,
        },
        "law": {
            "model": gs.MODEL_ID,
            "law_variant": False,
            "note": "Uses the existing Gray-Scott equations; this lane does not add Hebbian/plastic/network rules.",
        },
        "results": rows,
        "top_observations": ranked[:5],
        "counts": {
            "stable": len(stable),
            "unstable": n - len(stable),
            "with_localized_regions": sum(int((r.get("observations") or {}).get("localized_region_count") or 0) > 0 for r in stable),
            "with_corridor_candidates": sum(int((r.get("observations") or {}).get("corridor_candidate_count") or 0) > 0 for r in stable),
        },
        "not_claimed": [
            "network", "node", "edge", "neuron", "brain", "learning", "memory", "plasticity", "life",
        ],
        "honesty": {
            "observer_is_separate_from_physics": True,
            "observer_metrics_are_success_criteria": False,
            "observation_priority_is_scientific_score": False,
            "negative_results_are_retained": True,
            "this_is_pure_genesis_R0_proof": False,
            "existing_spatial_law_contains_geometry_as_a_given": True,
            "periodic_physics_uses_periodic_component_observer": True,
            "next_step_local_plasticity_requires_separate_law_variant_audit": True,
        },
    }
    if persist:
        _write(_REPORT, report)
    return report
