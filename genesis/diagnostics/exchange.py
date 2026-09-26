"""Energy exchange between an observed interior and an unobserved outside (a border / bath).

A measuring instrument only. Feed it the interior energy at successive times; it keeps the two directions
apart: `inflow` sums every increase (energy that came in from the outside), `outflow` every decrease (energy
that left). A one-way border shows outflow only; a border that also kicks back (a heat bath) shows both, and in
a steady state the two balance (net ≈ 0) while each keeps growing -- a circulation, not a standstill.

The interior is closed except through its edge (the dynamics inside conserve energy), so a change of interior
energy is energy that crossed the edge -- up to the integrator's bounded O(dt²) wobble, which shows up in both
columns and is reported by comparing with a closed box.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExchangeMeter:
    inflow: float = 0.0
    outflow: float = 0.0
    last: float | None = None
    series: list[dict[str, Any]] = field(default_factory=list)

    def add(self, t: float, interior_energy: float, keep: bool = False) -> None:
        if self.last is not None:
            d = interior_energy - self.last
            if d > 0:
                self.inflow += d
            else:
                self.outflow -= d
        self.last = interior_energy
        if keep:
            self.series.append({"t": t, "E_in": interior_energy, "inflow": self.inflow, "outflow": self.outflow})

    def summary(self) -> dict[str, Any]:
        tot = self.inflow + self.outflow
        return {"inflow": round(self.inflow, 4), "outflow": round(self.outflow, 4),
                "net": round(self.inflow - self.outflow, 4),
                "two_way": round(min(self.inflow, self.outflow) / (0.5 * tot), 4) if tot > 0 else 0.0}
