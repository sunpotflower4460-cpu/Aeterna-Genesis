"""Aeterna Genesis Autopilot.

A deterministic campaign queue around the repository's existing physics runners.
AI may author campaign YAML, but the worker only executes schema-validated,
allow-listed start-condition changes and never writes official rooms.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
