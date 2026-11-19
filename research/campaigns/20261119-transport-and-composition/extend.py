"""Run and analyse the registered explicit-fuel composition and capacity controls."""
from __future__ import annotations

import argparse
from functools import lru_cache
import gzip
import itertools
from pathlib import Path
import zipfile

import numpy as np

from analyse import composition_residual, contrasts, inspect_history
from run import FUEL, HERE, REGISTRATION, Trial, json_text, read_json, run_phase, sha256

SUPPLEMENT = HERE / "SUPPLEMENTAL_REGISTRATION.json"
COMPOSITION = "fuel_composition"
CAPACITY = "fuel_capacity"


def jobs_for(registration):
    n, duration, seeds = registration["n"], registration["T"], registration["seeds"]
    cases = {case["id"]: case for case in read_json(FUEL / "PRE_REGISTRATION.json")["cases"]}
    comp = registration["explicit_fuel_composition"]
    capacity = registration["exchange_capacity"]
    external = capacity["reference_kex"] * n / capacity["reference_n"]
    jobs = {
        COMPOSITION: [
            Trial(COMPOSITION, "sparse", n, duration, seed, {
                **cases[parent], **comp["parameters"], "id": f"{parent}_B{fraction:g}",
                "initial_B_fraction": fraction,
            })
            for seed, (parent, fractions) in itertools.product(seeds, comp["parent_cases"].items())
            for fraction in fractions
        ],
        CAPACITY: [
            Trial(CAPACITY, "sparse", n, duration, seed, {
                **cases[parent], "id": f"{parent}_capacity_matched", "kex": external,
            })
            for seed, parent in itertools.product(seeds, capacity["cases"])
        ],
    }
    if len(jobs[COMPOSITION]) != comp["histories"] or len(jobs[CAPACITY]) != capacity["histories"]:
        raise ValueError("Supplemental history count differs from registration")
    return jobs


@lru_cache
def initial_state(path):
    with zipfile.ZipFile(path) as bundle:
        return tuple(bundle.read(f"state-0-{field}.bin")
                     for field in ("cells", "positions", "conformers", "displacements"))


def analyse(registration, jobs, evidence, primary_results, output):
    primary = read_json(REGISTRATION)
    records = [
        inspect_history(evidence / job.relative_archive, job, primary, registration_path=SUPPLEMENT)
        for group in jobs.values() for job in group
    ]
    index = {row["archive"]: row for row in read_json(primary_results)["archives"]}
    n, duration = registration["n"], registration["T"]
    window = str(duration)

    def parent(case, seed, size):
        return f"fuel_holdout/{case}-d3-n{size}-T{duration:g}-s{seed}.zip"

    brackets = []
    for seed, case in itertools.product(registration["seeds"], registration["explicit_fuel_composition"]["parent_cases"]):
        main = parent(case, seed, n)
        old_cells, old_positions, *_ = initial_state(evidence / main)
        baseline_fuel = np.frombuffer(old_cells, np.uint8)
        baseline_fuel = np.where(baseline_fuel >= 3, baseline_fuel, 0)
        frozen = []
        for record in records:
            recipe = record["recipe"]
            if record["phase"] != COMPOSITION or recipe["seed"] != seed or not recipe["case"]["id"].startswith(case + "_B"):
                continue
            trial_cells, trial_positions, *_ = initial_state(evidence / record["archive"])
            trial_fuel = np.frombuffer(trial_cells, np.uint8)
            if old_positions != trial_positions or not np.array_equal(baseline_fuel, np.where(trial_fuel >= 3, trial_fuel, 0)):
                raise ValueError("Composition control changed initial macro locations or fuel/waste")
            frozen.append(record["windows"][window])
        active = index[main]["windows"][window]
        reads = {}
        for field in ("variance_4", "variance_4_x_only", "variance_4_transverse"):
            nulls = sorted((value["B_fraction"], value[field]) for value in frozen)
            reads[field] = {
                "active": active[field], "nulls": nulls,
                **composition_residual(active["B_fraction"], active[field], nulls),
            }
        brackets.append({"seed": seed, "case": case, "active_B": active["B_fraction"], "readouts": reads})

    sizes = registration["exchange_capacity"]
    capacity = {}
    for case in sizes["cases"]:
        baseline_at_size, baseline_at_small_size = [], []
        for seed in registration["seeds"]:
            main = parent(case, seed, n)
            small = parent(case, seed, sizes["reference_n"])
            scaled = next(row for row in records if row["phase"] == CAPACITY and row["recipe"]["seed"] == seed
                          and row["recipe"]["case"]["id"] == case + "_capacity_matched")
            if initial_state(evidence / main) != initial_state(evidence / scaled["archive"]):
                raise ValueError("Capacity control changed the parent initial state")
            baseline_at_size.append((seed, scaled["windows"][window], index[main]["windows"][window]))
            baseline_at_small_size.append((seed, scaled["windows"][window], index[small]["windows"][window]))
        capacity[case] = {
            "scaled_N32_minus_N32": contrasts(baseline_at_size),
            "scaled_N32_minus_N24": contrasts(baseline_at_small_size),
        }
    summary = {
        "registration_sha256": sha256(SUPPLEMENT), "primary_results_sha256": sha256(primary_results),
        "counts": {phase: len(group) for phase, group in jobs.items()},
        "maximum_relative_medium_error": max(record["max_relative_medium_error"] for record in records),
        "composition": brackets, "capacity": capacity,
        "archives": [
            {key: record[key] for key in ("archive", "archive_sha256", "windows")}
            for record in records
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "results.json").write_text(json_text(summary), encoding="utf-8")
    (output / "observations.json.gz").write_bytes(gzip.compress(json_text(records).encode(), mtime=0))
    print(f"Audited {len(records)} supplemental histories", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    modes = parser.add_subparsers(dest="mode", required=True)
    simulate = modes.add_parser("simulate")
    simulate.add_argument("--scratch", type=Path, required=True)
    simulate.add_argument("--jobs", type=int, default=4)
    simulate.add_argument("--phase", choices=("all", COMPOSITION, CAPACITY), default="all")
    simulate.add_argument("--seed", type=int, action="append", help="Run only these registered seeds")
    report = modes.add_parser("analyse")
    report.add_argument("--primary-results", type=Path, required=True)
    report.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reg = read_json(SUPPLEMENT)
    jobs = jobs_for(reg)
    if args.mode == "simulate":
        if args.jobs < 1:
            parser.error("--jobs must be positive")
        evidence, scratch = args.evidence.resolve(), args.scratch.resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        evidence.mkdir(parents=True, exist_ok=True)
        if args.seed and set(args.seed) - set(reg["seeds"]):
            parser.error(f"Requested seeds must be registered: {reg['seeds']}")
        selected = {phase: [job for job in group if not args.seed or job.seed in args.seed]
                    for phase, group in jobs.items()}
        for phase in jobs if args.phase == "all" else [args.phase]:
            run_phase(phase, selected, evidence, scratch, args.jobs, registration_path=SUPPLEMENT)
    else:
        analyse(reg, jobs, args.evidence, args.primary_results, args.out)


if __name__ == "__main__":
    main()
