"""Aeterna Dream Loop — bounded autonomous research bursts for AI Genesis Lab.

The Dream Loop never changes success thresholds and never writes official Rooms.  It
orchestrates existing experimenters, turns measured outcomes into machine-readable
research events, and prepares human-facing reports / observation presets.
"""

from .events import classify_search_candidate, events_from_autopilot, novelty_score
from .presets import make_view_preset
from .report import build_report

__all__ = [
    "build_report",
    "classify_search_candidate",
    "events_from_autopilot",
    "make_view_preset",
    "novelty_score",
]
