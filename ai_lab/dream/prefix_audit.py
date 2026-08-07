"""Trajectory-prefix integrity helpers for long-horizon follow-up.

A long run is only comparable to an earlier short run when its early trajectory is the same
trajectory.  We therefore store a stable digest of the ordinary observation endpoint and compare it
with an independent replay before interpreting later-time events.

The digest is deliberately quantized before hashing.  It is strict enough to catch a different
trajectory/start/solver path while avoiding false mismatches from irrelevant last-bit floating point
differences across runners.  This is an integrity check, not a physical observable.
"""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

_ALGORITHM = "sha256-round12-v1"
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
    same_shape = expected.get("shape") == actual.get("shape")
    same_value = expected.get("value") == actual.get("value")
    match = bool(same_algorithm and same_shape and same_value)
    return {
        "status": "MATCH" if match else "MISMATCH",
        "match": match,
        "same_algorithm": same_algorithm,
        "same_shape": same_shape,
        "same_value": same_value,
        "scientific_usable_from_hash": match,
        "expected": expected,
        "actual": actual,
    }


def replay_g001_endpoint(candidate: dict[str, Any], *, quick: bool = True) -> dict[str, Any] | None:
    """Independently replay only the ordinary g001 observation prefix and digest its endpoint.

    This replay does not inspect a triangle or any later outcome.  It uses only the recorded t=0
    family/knobs/seed, so attaching this digest to a frontier candidate does not seed a target shape.
    """
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
        "source": "independent-t0-endpoint-replay",
    })
    return digest


def install_geometry_digest_wrapper(hourly_module: Any, strict_module: Any) -> None:
    """Attach prefix digests only to naturally observed F4+ probes and their frontier summaries.

    The strict geometry probe itself is intentionally left untouched.  A second endpoint-only replay
    is performed for the small number of F4+ candidates, keeping the broad geometry lane simple and
    making the provenance of the integrity digest explicit.
    """
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
            probe["prefix_state_digest"] = replay_g001_endpoint(probe, quick=quick)
            probe["prefix_identity_digest_is_target_seed"] = False
        return probes

    def geometry_summary_with_digest(probes: list[dict[str, Any]]):
        summary = original_summary(probes)
        by_key = {
            (p.get("trial_index"), p.get("seed")): p.get("prefix_state_digest")
            for p in probes if p.get("prefix_state_digest")
        }
        for item in summary.get("frontier_candidates") or []:
            digest = by_key.get((item.get("trial_index"), item.get("seed")))
            if digest:
                item["prefix_state_digest"] = digest
        best = summary.get("best_frontier_candidate")
        if best:
            digest = by_key.get((best.get("trial_index"), best.get("seed")))
            if digest:
                best["prefix_state_digest"] = digest
        summary["prefix_identity_digest_attached_to_F4_plus"] = True
        return summary

    run_geometry_probes_with_digest._prefix_digest_wrapper = True
    geometry_summary_with_digest._prefix_digest_wrapper = True
    hourly_module.run_geometry_probes = run_geometry_probes_with_digest
    hourly_module.geometry_summary = geometry_summary_with_digest
