"""Apply the archived argon solver and observer to the fixed force-range replication."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261120-argon-interface-turnover"))
import analyze
import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    calculate = commands.add_parser("run", help="run the registered trajectories")
    calculate.add_argument("--registered-at", required=True)
    calculate.add_argument("--scratch", required=True, type=Path)
    calculate.add_argument("--out", required=True, type=Path)
    calculate.add_argument("--jobs", type=int, default=6)
    calculate.add_argument("--cxx", default=os.environ.get("CXX", "c++"))
    measure = commands.add_parser("analyze", help="read the registered trajectories")
    measure.add_argument("--evidence", required=True, type=Path)
    measure.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    # These modules also serve the frozen first registration. Redirect only the new plan.
    run.PLAN = HERE / "PLAN.json"
    analyze.HERE = HERE
    if args.command == "run":
        return run.run(args.out.resolve(), args.scratch.resolve(), args.registered_at, args.jobs, args.cxx)
    analyze.analyze(args.evidence.resolve(), args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
