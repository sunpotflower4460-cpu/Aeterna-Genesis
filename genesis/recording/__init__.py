"""Field-recording for the Observatory (Phase 0).

Additive-only: records DOWNSAMPLED snapshots of fields the simulation ALREADY computes, so the UI can
replay the REAL measured fields over time (no decorative/fake particles). Never changes physics,
solver, initial conditions, conservation, emergence level, audits, or the final-field checksum.
"""
from .recorder import FieldRecorder, downsample  # noqa: F401
