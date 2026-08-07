"""Typed, audit-friendly contract for a Genesis World.

The contract deliberately separates what is *put in* (field types, equations, substrate, boundary and
zero-state family) from what is later *observed*.  No success criterion or target morphology belongs
in a WorldSpec.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    name: str
    rank: int
    components: int
    scalar_type: str = "real"  # real | complex
    symmetry: str = "none"
    conserved: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorldSpec:
    world_id: str
    label: str
    model_module: str
    fields: tuple[FieldSpec, ...]
    zero_ids: tuple[str, ...]
    dimensions: tuple[int, ...]
    substrate: str = "fixed_euclidean_lattice"
    boundary: str = "periodic"
    drive_class: str = "autonomous"
    role: str = "F"  # E/V/S/N/F/Q vocabulary from PHYSICS_INTEGRITY.md
    causal_closure: str = "C1"
    runnable_probe: str | None = None
    characteristic_time: str = "model_declared"
    invariants: tuple[str, ...] = field(default_factory=tuple)
    symmetries: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fields"] = [x.to_dict() for x in self.fields]
        return d


def validate_world_spec(spec: WorldSpec) -> list[str]:
    """Return contract errors.  This is structural validation, never a scientific success gate."""
    errors: list[str] = []
    if not spec.world_id:
        errors.append("world_id is required")
    if not spec.model_module:
        errors.append("model_module is required")
    if not spec.fields:
        errors.append("at least one field is required")
    if not spec.zero_ids:
        errors.append("at least one zero-state family is required")
    if not spec.dimensions or any(d <= 0 for d in spec.dimensions):
        errors.append("dimensions must contain positive integers")
    if spec.role not in {"E", "V", "S", "N", "F", "Q"}:
        errors.append("role must be one of E/V/S/N/F/Q")
    if spec.causal_closure not in {"C0", "C1", "C2", "C3", "C4"}:
        errors.append("causal_closure must be C0..C4")
    for f in spec.fields:
        if f.rank < 0:
            errors.append(f"field {f.name}: rank must be >=0")
        if f.components <= 0:
            errors.append(f"field {f.name}: components must be >0")
        if f.scalar_type not in {"real", "complex"}:
            errors.append(f"field {f.name}: scalar_type must be real or complex")
    return errors
