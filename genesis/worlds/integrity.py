"""Reusable physics-integrity audit plans for heterogeneous Worlds.

This module creates *tests to run*, not conclusions.  A surprising result should survive independent
seed, time-step, spatial-resolution, box-size and (where available) solver checks before a strong claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AuditVariant:
    kind: str
    factor: float
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_AUDIT_VARIANTS = (
    AuditVariant("dt", 0.5, "time-step convergence"),
    AuditVariant("dx", 0.5, "spatial-resolution convergence at fixed physical size"),
    AuditVariant("box_size", 2.0, "finite-size dependence"),
    AuditVariant("seed", 1.0, "independent stochastic replication"),
)


def audit_plan(*, solver_alternative_available: bool = False) -> dict[str, Any]:
    variants = [x.to_dict() for x in DEFAULT_AUDIT_VARIANTS]
    if solver_alternative_available:
        variants.append(AuditVariant("solver", 1.0, "independent numerical-method agreement").to_dict())
    return {
        "version": 1,
        "variants": variants,
        "rule": "A physics claim may be weakened or quarantined if the qualitative event disappears under convergence checks.",
        "changes_success_thresholds": False,
        "promotion_effect": False,
    }


def classify_audit(observations: list[dict[str, Any]], event_name: str) -> str:
    """Small helper for later automation. Missing evidence remains UNTESTED rather than negative."""
    relevant = [o for o in observations if o.get("audit_kind") in {"dt", "dx", "box_size", "seed", "solver"}]
    if not relevant:
        return "UNTESTED"
    finite = [o for o in relevant if o.get("finite")]
    if len(finite) != len(relevant):
        return "NUMERICALLY_UNSTABLE"
    hits = [event_name in (o.get("events") or []) for o in finite]
    if hits and all(hits):
        return "ROBUST_ACROSS_TESTED_VARIANTS"
    if hits and any(hits):
        return "DEPENDENT_ON_NUMERICS_OR_SCALE"
    return "NOT_REPRODUCED_IN_AUDIT"
