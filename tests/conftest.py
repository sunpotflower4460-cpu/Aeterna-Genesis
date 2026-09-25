"""Make the repository root importable so `core` resolves during tests, and mark measured-slow tests."""

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_SLOW_LIST = os.path.join(os.path.dirname(__file__), "slow_tests.txt")


def _slow_ids():
    try:
        with open(_SLOW_LIST, encoding="utf-8") as fh:
            return {line.strip() for line in fh if line.strip() and not line.startswith("#")}
    except OSError:
        return set()


def pytest_collection_modifyitems(config, items):
    """Tag tests listed in tests/slow_tests.txt (measured >5 s) so `pytest -m "not slow"` stays quick."""
    slow = _slow_ids()
    for item in items:
        if item.nodeid in slow:
            item.add_marker(pytest.mark.slow)
