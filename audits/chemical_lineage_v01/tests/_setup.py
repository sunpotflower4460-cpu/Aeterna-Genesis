"""Shared import path for this audit's tests (no test logic)."""
import os
import sys

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
