"""Common contracts for parallel Genesis worlds.

A World is a physically explicit combination of fields, laws, substrate, zero-state families,
solver capabilities and integrity obligations.  Registering a World does not make it official and
does not imply any Emergence Level.
"""

from .spec import FieldSpec, WorldSpec, validate_world_spec
from .zero_registry import ZeroSpec, get_zero, list_zeros
from .registry import get_world, list_worlds

__all__ = [
    "FieldSpec",
    "WorldSpec",
    "ZeroSpec",
    "get_world",
    "list_worlds",
    "get_zero",
    "list_zeros",
    "validate_world_spec",
]
