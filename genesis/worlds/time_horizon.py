"""World-relative long-horizon policy.

A fixed number of solver steps is not comparable across laws.  Deep Time is expressed in multiples of
a declared reference time tau_ref.  The policy is observational and does not decide success.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HorizonPlan:
    tau_ref: float
    multipliers: tuple[float, ...] = (1.0, 4.0, 16.0, 64.0)

    def physical_times(self) -> tuple[float, ...]:
        if self.tau_ref <= 0:
            raise ValueError("tau_ref must be positive")
        return tuple(self.tau_ref * x for x in self.multipliers)


def default_tau_ref(world_id: str, params: dict | None = None) -> float:
    """Conservative first reference times.  Each value states a timescale, not a fitted target."""
    p = params or {}
    if world_id in {"g001-tdgl", "o3-vector", "q2-nematic"}:
        return max(float(p.get("quench_duration", 8.0)), 1e-9)
    if world_id == "g003-model-h":
        # Diffusive unit estimate over the interfacial scale sqrt(kappa): tau ~ kappa/M in code units.
        return max(float(p.get("kappa", 1.0)) / max(float(p.get("M", 1.0)), 1e-12), 1e-9)
    return 1.0


def next_horizon_multiplier(completed_multiplier: float) -> float | None:
    """Escalate only along the predeclared 1,4,16,64 tau ladder."""
    ladder = (1.0, 4.0, 16.0, 64.0)
    for x in ladder:
        if x > completed_multiplier + 1e-12:
            return x
    return None
