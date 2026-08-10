"""Trajectory-prefix integrity helpers for long-horizon follow-up.

A long run is only comparable to an earlier short run when its early trajectory is the same
trajectory.  Two complementary checks are used:

1. an observation digest made directly from the ORIGINAL geometry probe's compact time series; and
2. a quantized endpoint-field digest from an independent t=0 reconstruction.

The first check proves that the replay reproduces the actually recorded detector history.  The second
is a stricter reconstruction-stability signal for new candidates.  Neither is a physical observable
or a target-shape seed.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

_ALGORITHM = "sha256-round12-v1"
_OBSERVATION_ALGORITHM = "sha256-observation-round10-v1"
_DECIMALS = 12


def field_digest(field: np.ndarray, *, decimals: int = _DECIMALS) -> dict[str, Any]:
    """Return a compact, reproducible digest for a real or complex field."""
    arr = np.asarray(field)
    if np.iscomplexobj(arr):
        payload_arr = np.stack(
            [np.round(arr.real, decimals=decimals), np.round(arr.imag, decimals=decimals)],
            axis=-1,
        ).astype("<f8", copy=False)
        kind = "complex"
    else:
        payload_arr = np.round(arr, decimals=decimals).astype("<f8", copy=False)
        kind = "real"
    payload = np.ascontiguousarray(payload_arr).tobytes(order="C")
    return {
        "algorithm": _ALGORITHM if decimals == _DECIMALS else f"sha256-round{decimals}-v1",
        "value": hashlib.sha256(payload).hexdigest(),
        "shape": list(arr.shape),
        "kind": kind,
        "finite": bool(np.all(np.isfinite(arr))),
    }


def observation_digest(series: list[dict[str, Any]] | None, *, decimals: int = 10) -> dict[str, Any] | None:
    """Digest the compact detector history that came from the actual ordinary geometry run."""
    if series is None:
        return None

    def normalize(value: Any) -> Any:
        if isinstance(value, float):
            if not np.isfinite(value):
                return str(value)
            return round(value, decimals)
        if isinstance(value, dict):
            return {str(k): normalize(v) for k, v in sorted(value.items())}
        if isinstance(value, (list, tuple)):
            return [normalize(v) for v in value]
        return value

    normalized = normalize(series)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {
        "algorithm": _OBSERVATION_ALGORITHM if decimals == 10 else f"sha256-observation-round{decimals}-v1",
        "value": hashlib.sha256(payload).hexdigest(),
        "snapshots": len(series),
        "source": "actual-ordinary-geometry-observation-series",
    }


def compare_digest(expected: dict[str, Any] | None, actual: dict[str, Any] | None) -> dict[str, Any]:
    """Compare two stored digests without pretending missing legacy evidence is a match."""
    if not expected:
        return {
            "status": "LEGACY_NO_BASELINE_DIGEST",
            "match": None,
            "scientific_usable_from_hash": None,
        }
    if not actual:
        return {
            "status": "REPLAY_DIGEST_MISSING",
            "match": False,
            "scientific_usable_from_hash": False,
        }
    same_algorithm = expected.get("algorithm") == actual.get("algorithm")
    same_shape = expected.get("shape") == actual.get("shape") if "shape" in expected or "shape" in actual else True
    same_count = expected.get("snapshots") == actual.get("snapshots") if "snapshots" in expected or "snapshots" in actual else True
    same_value = expected.get("value") == actual.get("value")
    match = bool(same_algorithm and same_shape and same_count and same_value)
    return {
        "status": "MATCH" if match else "MISMATCH",
        "match": match,
        "same_algorithm": same_algorithm,
        "same_shape": same_shape,
        "same_count": same_count,
        "same_value": same_value,
        "scientific_usable_from_hash": match,
        "expected": expected,
        "actual": actual,
    }


def replay_g001_endpoint(candidate: dict[str, Any], *, quick: bool = True) -> dict[str, Any] | None:
    """Independently replay only the ordinary g001 observation prefix and digest its endpoint."""
    from ai_lab import lab
    from genesis.models import ginzburg_landau as gl

    edge, macro_steps, _ = lab.STEPS_2D[bool(quick)]
    shape = (edge, edge)
    knobs = dict(candidate.get("knobs") or {})
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    total = macro_steps * nsub
    rng = np.random.default_rng(int(candidate["seed"]))
    psi = lab.make_ic(
        str(candidate["family"]), shape, float(p["noise_amplitude"]), rng,
        corr_len=float(knobs.get("correlation_length", 1.0)),
    )
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            return None
    digest = field_digest(psi)
    digest.update({
        "ordinary_macro_steps": int(macro_steps),
        "ordinary_internal_steps": int(total),
        "ordinary_physical_time": float(macro_steps * base_dt),
        "quick": bool(quick),
        "source": "independent-t0-endpoint-reconstruction",
    })
    return digest


def install_geometry_digest_wrapper(hourly_module: Any, strict_module: Any) -> None:
    """Attach integrity digests only to naturally observed F4+ probes and frontier summaries."""
    current = hourly_module.run_geometry_probes
    if getattr(current, "_prefix_digest_wrapper", False):
        return
    original_run = current
    original_summary = hourly_module.geometry_summary

    def run_geometry_probes_with_digest(*args: Any, **kwargs: Any):
        probes = original_run(*args, **kwargs)
        quick = bool(kwargs.get("quick", True))
        for probe in probes:
            path = probe.get("zero_to_fission") or {}
            if int(path.get("depth", -1)) < 4:
                continue
            # This digest is made from the actual ordinary probe output, not from a later replay.
            probe["prefix_observation_digest"] = observation_digest(probe.get("series"))
            # This complementary field digest is an independent reconstruction and is labelled as such.
            probe["prefix_state_digest"] = replay_g001_endpoint(probe, quick=quick)
            probe["prefix_identity_digest_is_target_seed"] = False
        return probes

    def geometry_summary_with_digest(probes: list[dict[str, Any]]):
        summary = original_summary(probes)
        by_key = {
            (p.get("trial_index"), p.get("seed")): {
                "prefix_observation_digest": p.get("prefix_observation_digest"),
                "prefix_state_digest": p.get("prefix_state_digest"),
            }
            for p in probes if p.get("prefix_observation_digest") or p.get("prefix_state_digest")
        }
        path = summary.get("zero_to_fission_path") or {}
        for item in path.get("frontier_candidates") or []:
            digests = by_key.get((item.get("trial_index"), item.get("seed"))) or {}
            item.update({k: v for k, v in digests.items() if v})
        best = path.get("best_frontier_candidate")
        if best:
            digests = by_key.get((best.get("trial_index"), best.get("seed"))) or {}
            best.update({k: v for k, v in digests.items() if v})
        path["prefix_identity_digest_attached_to_F4_plus"] = True
        path["actual_observation_history_digest_attached"] = True
        summary["zero_to_fission_path"] = path
        summary["prefix_identity_digest_attached_to_F4_plus"] = True
        return summary

    run_geometry_probes_with_digest._prefix_digest_wrapper = True
    geometry_summary_with_digest._prefix_digest_wrapper = True
    hourly_module.run_geometry_probes = run_geometry_probes_with_digest
    hourly_module.geometry_summary = geometry_summary_with_digest
