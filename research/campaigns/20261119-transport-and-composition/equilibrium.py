"""Compare the driven uniform fluid with a reversible, composition-bracketed fluid."""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path

from analyse import check_initial_matching, composition_residual, inspect_history
from run import FUEL, HERE, REGISTRATION, Trial, json_text, read_json, run_phase, sha256

PLAN = HERE / "EQUILIBRIUM_REGISTRATION.json"
PHASE = "fuel_equilibrium"


def planned(reg):
    fuel = read_json(FUEL / "PRE_REGISTRATION.json")
    parent = next(case for case in fuel["cases"] if case["id"] == reg["parent_case"])
    passive = reg["passive_control"]
    cases = [parent] + [
        {**parent, "id": f"reversible_df{df:g}", "df": df,
         "eta": passive["eta"], "passive_rate": passive["passive_rate"]}
        for df in passive["df"]
    ]
    jobs = [
        Trial(PHASE, "sparse", reg["N"], reg["T"], seed, case)
        for seed in reg["seeds"] for case in cases
    ]
    if len(jobs) != reg["histories"]:
        raise ValueError("Unexpected number of reversible histories")
    return jobs


def analyse(registration, jobs, evidence, out):
    observer_registration = read_json(REGISTRATION)
    records = [inspect_history(evidence / job.relative_archive, job, observer_registration,
                               registration_path=PLAN) for job in jobs]
    matching = check_initial_matching(records)
    t = str(registration["T"])
    comparisons = []
    for seed in registration["seeds"]:
        seed_group = [record for record in records if record["recipe"]["seed"] == seed]
        active = next(r["windows"][t] for r in seed_group
                      if r["recipe"]["case"]["id"] == registration["parent_case"])
        passive = [r["windows"][t] | {"df": r["recipe"]["parameters"]["df"]} for r in seed_group
                   if r["recipe"]["case"]["id"] != registration["parent_case"]]
        measurements = {}
        for field in ("variance_4", "variance_4_x_only", "variance_4_transverse"):
            points = sorted((record["B_fraction"], record[field]) for record in passive)
            measurements[field] = {
                "active": active[field], "nulls": points,
                **composition_residual(active["B_fraction"], active[field], points),
            }
        comparisons.append({"seed": seed, "active_B": active["B_fraction"],
                            "active": active, "reversible": passive, "readouts": measurements})
    report = {
        "registration_sha256": sha256(PLAN), "history_count": len(records),
        "initial_condition_checks": matching,
        "maximum_relative_medium_error": max(record["max_relative_medium_error"] for record in records),
        "comparisons": comparisons,
        "archives": [{key: row[key] for key in ("archive", "archive_sha256", "windows")} for row in records],
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "results.json").write_text(json_text(report), encoding="utf-8")
    (out / "observations.json.gz").write_bytes(gzip.compress(json_text(records).encode(), mtime=0))
    print(f"Audited {len(records)} reversible comparison histories.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    simulate = subparsers.add_parser("simulate")
    simulate.add_argument("--scratch", type=Path, required=True)
    simulate.add_argument("--jobs", type=int, default=4)
    observe = subparsers.add_parser("analyse")
    observe.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    registration = read_json(PLAN)
    jobs = planned(registration)
    evidence = args.evidence.resolve()
    if args.mode == "simulate":
        if args.jobs < 1:
            parser.error("--jobs must be positive")
        scratch = args.scratch.resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        evidence.mkdir(parents=True, exist_ok=True)
        run_phase(PHASE, {PHASE: jobs}, evidence, scratch, args.jobs, registration_path=PLAN)
    else:
        analyse(registration, jobs, evidence, args.out)


if __name__ == "__main__":
    main()
