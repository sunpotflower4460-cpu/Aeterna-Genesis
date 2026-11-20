"""Count fixed-mask hops by particle conformation on byte-matched archived replays."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

import numpy as np

from coarsening_runs import FUEL, HERE, PLAN, PREVIOUS, PREVIOUS_PLAN, read_json, previous_trials, sha256
from pathways import endpoints
from run import json_text
from survey import read_snapshots
from track_domains import region_frame

HOP_PLAN = HERE / "TRANSPORT_REGISTRATION.json"
SOURCE = FUEL / "local_kmc_sparse.cpp"
HEADER = HERE / "fixed_boundary_observer.hpp"
COUNT_FIELDS = ("in_I", "out_I", "in_B", "out_B")
PARAMETERS = ("epsilon", "df", "passive_rate", "eta", "D_B", "D_I", "D_F", "D_W",
              "kex", "source", "mu", "z_total", "initial_B_fraction")


def instrument(original):
    insertions = [
        ("int main(int argc,char**argv)", '#include "fixed_boundary_observer.hpp"\n\n', True),
        ("  auto measure=[&](int sample){", "  FixedBoundaryObserver transport(out,V);\n", True),
        ("    obs<<'\\n';obs.flush();", "\n    transport.sample(sample*10);", False),
        ("      const int mid=macro_at[x];", "      transport.hop(type,x,y);\n", True),
    ]
    for anchor, observer, before in insertions:
        if original.count(anchor) != 1:
            raise ValueError("Unexpected source anchor for the read-only observer")
        original = original.replace(anchor, observer + anchor if before else anchor + observer)
    return original


def compile_observer(scratch, plan):
    if sha256(SOURCE) != plan["solver_source_sha256"]:
        raise ValueError("Solver source digest changed")
    work = scratch / "transport.cpp"
    work.write_text(instrument(SOURCE.read_text()))
    binary = scratch / "transport"
    subprocess.run(["g++", "-O3", "-std=c++17", "-I", str(HEADER.parent),
                    str(work), "-o", str(binary)], check=True)
    return binary, sha256(work)


def mask_input(bundle, recipe, plan, destination):
    times = range(plan["first_time"], plan["T"] + 1, plan["cadence"])
    snapshots = list(read_snapshots(bundle, recipe, [{"time": t} for t in times]))
    minimum = read_json(PLAN)["domains"]["minimum_region_sites"]
    masks = [[region_frame(s.density_count, s.positions, 64 * threshold, minimum).labels.ravel(order="F")
              for s in snapshots] for threshold in plan["thresholds"]]
    expected, endpoints_by_interval = {}, {}
    with destination.open("xb") as stream:
        for i, (a, b) in enumerate(zip(snapshots, snapshots[1:])):
            endpoints_by_interval[a.time] = b.time
            for threshold, lattice_masks in enumerate(masks):
                for endpoint, labels in enumerate(lattice_masks[i:i+2]):
                    stream.write(labels.astype("<i4").tobytes())
                    left, right = labels[a.positions], labels[b.positions]
                    for label in range(1, int(labels.max()) + 1):
                        expected[a.time, threshold, endpoint, label] = endpoints(left == label, right == label)
    return expected, endpoints_by_interval


def verify_physical_prefix(work, old, end):
    ledger = (work / "series.csv").read_bytes().splitlines()
    if len(ledger) != end // 10 + 2 or ledger != old.read("series.csv").splitlines()[:len(ledger)]:
        raise ValueError("Instrumented physical ledger is not the archived prefix")
    members = sorted(p for p in work.glob("state-*.bin"))
    target = {f"state-{t//10}-{kind}.bin" for t in range(0, end + 1, 50)
              for kind in ("cells", "conformers", "positions", "displacements")}
    if {p.name for p in members} != target or any(p.read_bytes() != old.read(p.name) for p in members):
        raise ValueError("Instrumented physical checkpoints are not the archived prefix")
    return len(ledger) - 1, len(members) // 4


def summarize_events(raw, expected, endpoints_by_interval, thresholds):
    totals = defaultdict(lambda: dict.fromkeys(COUNT_FIELDS, 0))
    checked = set()
    for row in csv.DictReader(io.StringIO(raw.decode())):
        start, end, threshold, endpoint, label = (int(row[field]) for field in
                                                  ("start", "end", "threshold_index", "endpoint", "label"))
        key = start, threshold, endpoint, label
        if key not in expected or key in checked or end != endpoints_by_interval[start]:
            raise ValueError("Unexpected time or fixed observation mask")
        checked.add(key)
        n = {field: int(row[field]) for field in COUNT_FIELDS}
        incoming, outgoing = n["in_I"] + n["in_B"], n["out_I"] + n["out_B"]
        reference = expected[key]
        if (incoming - outgoing != reference["net"]
                or incoming < reference["unique_outside_to_inside"]
                or outgoing < reference["unique_inside_to_outside"]
                or min(n.values()) < 0):
            raise ValueError("An accepted-event tally disagrees with exact endpoint conservation")
        for field, value in n.items():
            totals[threshold, endpoint][field] += value
    if checked != set(expected):
        raise ValueError("Observer missed a fixed region tally")
    records = []
    for (threshold, endpoint), n in sorted(totals.items()):
        gross = sum(n.values())
        records.append({"threshold": thresholds[threshold], "endpoint": endpoint, **n,
                        "gross_fraction_I": (n["in_I"] + n["out_I"]) / gross if gross else None,
                        "net_I": n["in_I"] - n["out_I"], "net_B": n["in_B"] - n["out_B"]})
    return records, len(checked)


def replay(task):
    test, reference, plan, scratch, output, binary, observer_sha = task
    archive = reference / test.relative_archive
    work = Path(tempfile.mkdtemp(prefix=f"{test.key}-", dir=scratch))
    with ZipFile(archive) as old:
        recipe = json.loads(old.read("recipe.json"))
        expected, clock = mask_input(old, recipe, plan, work / "observer-masks.bin")
        args = [str(x) for x in (binary, test.n, 3, recipe["molecules"], plan["T"], test.seed,
                                  *(recipe["parameters"][k] for k in PARAMETERS), work)]
        with (work / "solver.log").open("wb") as log:
            subprocess.run(args, check=True, stdout=log, stderr=log)
        ledger_rows, snapshots = verify_physical_prefix(work, old, plan["T"])
    raw = (work / "boundary-hops.csv").read_bytes()
    totals, tally_count = summarize_events(raw, expected, clock, plan["thresholds"])
    trace = output / f'{test.key}-through{plan["T"]}.csv.gz'
    with trace.open("xb") as f:
        f.write(gzip.compress(raw, mtime=0))
    report = {"archive": test.relative_archive.as_posix(), "archive_sha256": sha256(archive),
              "seed": test.seed, "N": test.n, "case": test.case["id"],
              "physical_ledger_rows": ledger_rows, "byte_identical_checkpoints": snapshots,
              "verified_fixed_region_tallies": tally_count, "totals": totals,
              "trace": trace.name, "trace_sha256": sha256(trace), "observer_source_sha256": observer_sha}
    shutil.rmtree(work)
    print(f"Audited {tally_count} fixed masks in {test.key}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=PREVIOUS / "evidence")
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    plan = read_json(HOP_PLAN)
    if (plan["first_time"], plan["T"], plan["cadence"], len(plan["thresholds"])) != (1200, 1800, 50, 2):
        raise ValueError("Observer schedule and registration disagree")
    trials = [t for t in previous_trials(read_json(PREVIOUS_PLAN), "extent")
              if t.n == plan["N"] and t.seed in plan["seeds"] and t.case["id"] in plan["cases"]]
    if len(trials) != len(plan["cases"]) * len(plan["seeds"]):
        raise ValueError("Incomplete exact-hop replay matrix")
    args.scratch.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=False)
    binary, source = compile_observer(args.scratch.resolve(), plan)
    tasks = [(t, args.reference.resolve(), plan, args.scratch.resolve(), args.out.resolve(), binary, source)
             for t in trials]
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        records = list(executor.map(replay, tasks))
    (args.out / "results.json").write_text(json_text({"registration_sha256": sha256(HOP_PLAN),
                                                      "observer_header_sha256": sha256(HEADER), "records": records}))


if __name__ == "__main__":
    main()
