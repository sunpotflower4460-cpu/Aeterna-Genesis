"""Parallel law/field registry for Multi-World Genesis.

The registry is descriptive.  A registered world may be Validation or Frontier and is never promoted
merely by appearing here.  Existing official Rooms keep their existing gates.
"""
from __future__ import annotations

from .spec import FieldSpec, WorldSpec, validate_world_spec
from .zero_registry import ZERO_REGISTRY


WORLD_REGISTRY: dict[str, WorldSpec] = {
    "g001-tdgl": WorldSpec(
        world_id="g001-tdgl",
        label="Complex TDGL quench",
        model_module="genesis.models.ginzburg_landau",
        fields=(FieldSpec("psi", rank=0, components=1, scalar_type="complex", symmetry="global U(1)"),),
        zero_ids=("Z-A", "Z-B"),
        dimensions=(2, 3),
        drive_class="time_programmed_environment",
        role="V",
        causal_closure="C1",
        runnable_probe="g001",
        symmetries=("global_U1", "translation", "rotation_discrete_lattice"),
        notes="Reference defect-formation world; quench is imposed and therefore excluded from spontaneous claims.",
    ),
    "g002-boussinesq": WorldSpec(
        world_id="g002-boussinesq",
        label="Boussinesq convection",
        model_module="genesis.models.boussinesq_rb",
        fields=(
            FieldSpec("temperature", rank=0, components=1, conserved=False),
            FieldSpec("velocity", rank=1, components=2, conserved=False, notes="incompressible flow"),
        ),
        zero_ids=("Z-A", "Z-D"),
        dimensions=(2, 3),
        boundary="walls_or_declared_variant",
        drive_class="externally_driven",
        role="V",
        causal_closure="C1",
        runnable_probe=None,
        invariants=("incompressibility",),
        notes="Registered now; execution adapter remains separate from the current shadow probe set.",
    ),
    "g003-model-h": WorldSpec(
        world_id="g003-model-h",
        label="Model H phase-field + flow",
        model_module="genesis.models.model_h",
        fields=(
            FieldSpec("phi", rank=0, components=1, conserved=True, notes="composition/order parameter"),
            FieldSpec("velocity", rank=1, components=2, conserved=False, notes="incompressible flow"),
        ),
        zero_ids=("Z-A", "Z-B", "Z-D"),
        dimensions=(2,),
        drive_class="autonomous",
        role="V",
        causal_closure="C1",
        runnable_probe="g003",
        invariants=("phi_mass", "incompressibility"),
        notes="Strong candidate for process-prepared C2 work because no external drive is required after t=0.",
    ),
    "cgl": WorldSpec(
        world_id="cgl",
        label="Complex Ginzburg-Landau",
        model_module="genesis.models.complex_ginzburg_landau",
        fields=(FieldSpec("psi", rank=0, components=1, scalar_type="complex", symmetry="global U(1)"),),
        zero_ids=("Z-A", "Z-B"),
        dimensions=(2,),
        drive_class="autonomous_or_declared_drive",
        role="V",
        causal_closure="C1",
        runnable_probe=None,
        notes="Non-variational/dissipative-wave family; adapter to be validated before autonomous use.",
    ),
    "gray-scott": WorldSpec(
        world_id="gray-scott",
        label="Gray-Scott reaction diffusion",
        model_module="genesis.models.gray_scott",
        fields=(
            FieldSpec("U", rank=0, components=1),
            FieldSpec("V", rank=0, components=1),
        ),
        zero_ids=("Z-D",),
        dimensions=(2,),
        drive_class="open_reaction_system",
        role="V",
        causal_closure="C1",
        runnable_probe=None,
        notes="Existing spot-division validation uses founder seeds; it must not be presented as strict Z-A emergence.",
    ),
    "o3-vector": WorldSpec(
        world_id="o3-vector",
        label="O(3) vector order parameter",
        model_module="genesis.models.vector_o3",
        fields=(FieldSpec("phi", rank=1, components=3, symmetry="O(3)"),),
        zero_ids=("Z-A", "Z-B"),
        dimensions=(2, 3),
        drive_class="time_programmed_environment",
        role="F",
        causal_closure="C1",
        runnable_probe="o3",
        symmetries=("O3_internal", "translation"),
        notes="Minimal vector-field frontier. No defect/individuality claim is attached at registration time.",
    ),
    "q2-nematic": WorldSpec(
        world_id="q2-nematic",
        label="2D symmetric-traceless Q tensor",
        model_module="genesis.models.q_tensor_nematic",
        fields=(FieldSpec("Q", rank=2, components=2, symmetry="nematic Q=-director equivalence"),),
        zero_ids=("Z-A", "Z-B"),
        dimensions=(2,),
        drive_class="time_programmed_environment",
        role="F",
        causal_closure="C1",
        runnable_probe="q2",
        symmetries=("nematic_head_tail", "translation"),
        notes="Reduced 2D nematic tensor field. It is not a spacetime metric and carries no gravity claim.",
    ),
    "relational-c4": WorldSpec(
        world_id="relational-c4",
        label="Relational substrate frontier",
        model_module="frontier.not_implemented",
        fields=(FieldSpec("relations", rank=2, components=1, notes="abstract relational adjacency/weight"),),
        zero_ids=("Z-R",),
        dimensions=(1,),
        substrate="relational_no_fixed_metric",
        boundary="not_applicable",
        drive_class="frontier",
        role="F",
        causal_closure="C4",
        runnable_probe=None,
        notes="Registry placeholder only. Must begin with validation of known relational-geometry models before Genesis claims.",
    ),
}


def _validate_registry() -> None:
    for world_id, spec in WORLD_REGISTRY.items():
        errors = validate_world_spec(spec)
        unknown = [z for z in spec.zero_ids if z not in ZERO_REGISTRY]
        if unknown:
            errors.append(f"unknown zero ids: {unknown}")
        if world_id != spec.world_id:
            errors.append("registry key must equal world_id")
        if errors:
            raise ValueError(f"invalid WorldSpec {world_id}: {'; '.join(errors)}")


_validate_registry()


def get_world(world_id: str) -> WorldSpec:
    return WORLD_REGISTRY[world_id]


def list_worlds(*, runnable_only: bool = False) -> list[WorldSpec]:
    worlds = [WORLD_REGISTRY[k] for k in sorted(WORLD_REGISTRY)]
    if runnable_only:
        worlds = [w for w in worlds if w.runnable_probe]
    return worlds
