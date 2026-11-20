"""Run conformation-selective mobility comparisons."""
from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

from extend import HERE, PLAN, read_json, run_phase, trials_for as extent_trials
from run import Trial

MOBILITY_PLAN = HERE / "MOBILITY_REGISTRATION.json"


def trials_for(plan):
    previous = extent_trials(read_json(PLAN))[0]
    n = plan["N"]
    base = {**previous.case, "kex": n * read_json(PLAN)["solver"]["exchange_per_site"]}
    jobs = [Trial(plan["phase"], "sparse", n, plan["T"], seed, {**base, **case})
            for case, seed in product(plan["cases"], plan["seeds"])]
    if len(jobs) != plan["histories"] or len({job.key for job in jobs}) != len(jobs):
        raise ValueError("Contradictory mobility registration")
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    args.evidence.mkdir(parents=True, exist_ok=True)
    args.scratch.mkdir(parents=True, exist_ok=True)
    plan = read_json(MOBILITY_PLAN)
    phase = plan["phase"]
    run_phase(phase, {phase: trials_for(plan)}, args.evidence.resolve(), args.scratch.resolve(),
              args.jobs, registration_path=MOBILITY_PLAN)


if __name__ == "__main__":
    main()
