"""Replay both binary-fluid branches with the registered observation interval."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "20261120-periodic-boundary-confirmation"
BINARY = HERE.parent / "20261120-binary-boundary-exchange"
PLAN = HERE / "PLAN.json"
sys.path.insert(0, str(BINARY))
import run as binary_run


if __name__ == "__main__":
    binary_run.PLAN = PLAN
    raise SystemExit(binary_run.main())
