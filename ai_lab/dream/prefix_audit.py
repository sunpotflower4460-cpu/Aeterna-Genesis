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
