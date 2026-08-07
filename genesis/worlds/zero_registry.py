"""Registry of physically distinct meanings of 'zero'.

Zero does not mean numeric zeros.  It means a maximally uncommitted state for the law under study,
with every imposed scale/direction/topology/object declared.  The registry lets Genesis compare how
far a result was causally prepared without pretending all random starts are equivalent.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ZeroSpec:
    zero_id: str
    label: str
    description: str
    purity_class: str
    generation: str
    correlated: bool
    imposed_length_scale: bool = False
    imposed_direction: bool = False
    imposed_object_count: bool = False
    imposed_topology: bool = False
    imposed_phase_structure: bool = False
    imposed_boundary_structure: bool = False
    strict_zero_candidate: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ZERO_REGISTRY: dict[str, ZeroSpec] = {
    "Z-A": ZeroSpec(
        zero_id="Z-A",
        label="minimal-white",
        description="Maximally symmetric/uniform state plus unbiased, spatially uncorrelated microscopic noise.",
        purity_class="A",
        generation="uniform_plus_white_noise",
        correlated=False,
        strict_zero_candidate=True,
    ),
    "Z-B": ZeroSpec(
        zero_id="Z-B",
        label="correlated-random",
        description="No objects/topology are placed, but the random field carries a declared correlation scale.",
        purity_class="B",
        generation="uniform_plus_correlated_random_field",
        correlated=True,
        imposed_length_scale=True,
        strict_zero_candidate=True,
        notes="Honest zero-like start, but weaker than Z-A for claims of scale-free origin.",
    ),
    "Z-C": ZeroSpec(
        zero_id="Z-C",
        label="ensemble-prepared",
        description="A state sampled from a stated equilibrium/statistical ensemble rather than hand-shaped.",
        purity_class="C",
        generation="statistical_ensemble",
        correlated=True,
        strict_zero_candidate=True,
        notes="The ensemble law and its correlation scales are part of the preparation and must be disclosed.",
    ),
    "Z-D": ZeroSpec(
        zero_id="Z-D",
        label="process-prepared",
        description="Initial state produced by an upstream physical preparation protocol or parent World.",
        purity_class="D",
        generation="upstream_physical_process",
        correlated=True,
        strict_zero_candidate=False,
        notes="Candidate route toward causal-closure C2/C3; provenance of the preparation is mandatory.",
    ),
    "Z-R": ZeroSpec(
        zero_id="Z-R",
        label="relational",
        description="No fixed metric/coordinate lattice is primary; only relations are primitive.",
        purity_class="R",
        generation="relational_substrate",
        correlated=False,
        strict_zero_candidate=False,
        notes="C4 frontier. Registering this class is not evidence that relational spacetime has emerged.",
    ),
}


def get_zero(zero_id: str) -> ZeroSpec:
    return ZERO_REGISTRY[zero_id]


def list_zeros() -> list[ZeroSpec]:
    return [ZERO_REGISTRY[k] for k in sorted(ZERO_REGISTRY)]
