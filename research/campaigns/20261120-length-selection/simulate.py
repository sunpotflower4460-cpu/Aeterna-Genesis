"""Run the registered long histories with the unchanged explicit-fuel solver."""
from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "20261119-long-time-and-stationary"
sys.path.insert(0, str(OLD))

from longtime import trials_for as parent_trials
from run import FUEL, Trial, read_json, run_phase, sha256

PLAN = HERE / "PRE_REGISTRATION.json"
SUPPLY_PLAN = HERE / "SUPPLY_REGISTRATION.json"


def trials_for(plan, panel):
    parent_file = OLD / "PRE_REGISTRATION.json"
    if sha256(parent_file) != plan["solver"]["parent_plan_sha256"]:
        raise ValueError("The matched control calibration is not the registered one")
    if sha256(FUEL / "local_kmc_sparse.cpp") != plan["solver"]["sha256"]:
        raise ValueError("The local solver has changed")
    parent = read_json(parent_file)["explicit"]
    calibrated = [dict(trial.case) for trial in parent_trials(parent)[:4]]
    active = next(case for case in calibrated if case["id"] == plan["solver"]["parent_case"])
    jobs = []
    for spec in plan["panels"][panel]:
        n, duration = spec["N"], spec["T"]
        if panel == "clock":
            defaults = read_json(FUEL / "PRE_REGISTRATION.json")["defaults"]
            values = defaults | active
            cases = [
                {**active, "id": f"clock_{factor:g}",
                 "passive_rate": factor * values["passive_rate"], "eta": factor * values["eta"]}
                for factor in spec["multipliers"]
            ]
        else:
            cases = calibrated if spec["cases"] == "matched" else [active]
        for seed, case in product(plan["seeds"], cases):
            jobs.append(Trial(panel, "sparse", n, duration, seed,
                              {**case, "kex": n * plan["solver"]["exchange_per_site"]}))
    if len(jobs) != plan["case_count"][panel] or len({job.key for job in jobs}) != len(jobs):
        raise ValueError("Incomplete trial matrix")
    return jobs


def supply_trials(plan, supplement):
    n = supplement["N"]
    base = next(trial for trial in trials_for(plan, "extent")
                if trial.case["id"] == plan["solver"]["parent_case"] and trial.n == n)
    defaults = read_json(FUEL / "PRE_REGISTRATION.json")["defaults"] | base.case
    cases = [
        {**base.case, "id": f"supply_clock_{factor:g}",
         "kex": base.case["kex"] * supplement["exchange_multiplier"],
         "passive_rate": defaults["passive_rate"] * factor, "eta": defaults["eta"] * factor}
        for factor in supplement["reaction_multipliers"]
    ]
    jobs = [Trial("supply", "sparse", n, supplement["T"], seed, case)
            for seed, case in product(supplement["seeds"], cases)]
    if len(jobs) != supplement["new_histories"]:
        raise ValueError("Incomplete reaction and replenishment matrix")
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", choices=("extent", "clock", "supply"))
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    args.scratch.mkdir(parents=True, exist_ok=True)
    args.evidence.mkdir(parents=True, exist_ok=True)
    plan = read_json(PLAN)
    registration = SUPPLY_PLAN if args.panel == "supply" else PLAN
    jobs = supply_trials(plan, read_json(SUPPLY_PLAN)) if args.panel == "supply" else trials_for(plan, args.panel)
    run_phase(args.panel, {args.panel: jobs}, args.evidence.resolve(), args.scratch.resolve(),
              args.jobs, registration_path=registration)


if __name__ == "__main__":
    main()
