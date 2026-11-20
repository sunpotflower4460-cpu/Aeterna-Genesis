"""Run the preregistered six long, unstructured 3D histories."""
from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "20261120-length-selection"
PLAN = HERE / "PRE_REGISTRATION.json"
sys.path.insert(0, str(PREVIOUS))

from simulate import PLAN as PREVIOUS_PLAN, trials_for as previous_trials
from run import FUEL, Trial, read_json, run_phase, sha256


def trials_for(plan):
    if sha256(PREVIOUS_PLAN) != plan["solver"]["baseline_registration_sha256"]:
        raise ValueError("The frozen baseline registration has changed")
    if sha256(FUEL / "local_kmc_sparse.cpp") != plan["solver"]["sha256"]:
        raise ValueError("The original solver has changed")

    base_plan = read_json(PREVIOUS_PLAN)
    base_case = next(trial.case for trial in previous_trials(base_plan, "extent")
                     if trial.n == 56 and trial.case["id"] == plan["solver"]["case"])
    matrix = plan["matrix"]
    if matrix["seeds"] != base_plan["seeds"]:
        raise ValueError("The two panels must use the registered matched seeds")
    jobs = [
        Trial(matrix["phase"], "sparse", n, matrix["T"], seed,
              {**base_case, "kex": n * plan["solver"]["exchange_per_site"]})
        for n, seed in product(matrix["edges"], matrix["seeds"])
    ]
    if len(jobs) != matrix["histories"] or len({job.key for job in jobs}) != len(jobs):
        raise ValueError("Contradictory registration")
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    args.evidence.mkdir(parents=True, exist_ok=True)
    args.scratch.mkdir(parents=True, exist_ok=True)
    plan = read_json(PLAN)
    phase = plan["matrix"]["phase"]
    run_phase(phase, {phase: trials_for(plan)}, args.evidence.resolve(), args.scratch.resolve(),
              args.jobs, registration_path=PLAN)


if __name__ == "__main__":
    main()
