"""Read long, mobility, and archived controls with the same periodic measurements."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import io
from itertools import groupby
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.ndimage import uniform_filter

from coarsening_runs import HERE, PLAN, PREVIOUS, PREVIOUS_PLAN, previous_trials, trials_for
from mobility import MOBILITY_PLAN, trials_for as mobility_trials
from analyse import check_initial_matching, inspect_history, read_ledger
from measure import half_correlation, spectral_length
from observe import time_mean
from pathways import Snapshot, observe_transitions, summarize_transitions
from run import json_text, read_json, sha256
from track_domains import region_frame

MECHANISM_PLAN = HERE / "MECHANISM_REGISTRATION.json"
SCALES = ("spectral_length", "half_correlation", "first_shell_fraction", "variance_4")
REGION_FIELDS = ("count", "total_material", "largest_material_share", "volume_weighted_sites")


def ledgers(bundle, recipe):
    rows = list(csv.DictReader(io.StringIO(bundle.read("series.csv").decode())))
    return read_ledger(rows, recipe, True)


def read_snapshots(bundle, recipe, frames):
    n = recipe["N"]
    for frame in frames:
        sample = frame["time"] // 10
        cells = np.frombuffer(bundle.read(f"state-{sample}-cells.bin"), dtype=np.uint8)
        material = ((cells == 1) | (cells == 2)).reshape((n,)*3, order="F")
        counts = np.rint(64 * uniform_filter(material.astype(float), size=4, mode="wrap")).astype(np.uint8)
        positions = np.frombuffer(bundle.read(f"state-{sample}-positions.bin"), dtype="<i4")
        yield Snapshot(frame["time"], positions, counts)


def scale_readout(snapshot, reference):
    density = snapshot.density_count / 64
    length, first_shell, variance = spectral_length(density)
    if abs(variance - reference["density_variances"]["4"]["material"]) >= 1e-12:
        raise ValueError("Spectral variance disagrees with the independent physical readout")
    geometry = reference["three_d_authenticity"]
    if not geometry["genuinely_3d"]:
        raise ValueError("No resolved out-of-plane variation")
    return {"time": snapshot.time, "spectral_length": length, "first_shell_fraction": first_shell,
            "half_correlation": half_correlation(snapshot.density_count.astype(np.int32)),
            "variance_4": variance, "three_d": geometry}


def region_readout(frame, minimum):
    eligible = frame.volumes >= minimum
    size = frame.volumes[eligible]
    population = frame.populations[eligible]
    total_material = int(population.sum())
    return {"count": len(size), "total_material": total_material,
            "largest_material_share": int(population.max()) / total_material if total_material else None,
            "volume_weighted_sites": int(np.dot(size, size)) / int(size.sum()) if size.size else None}


def one_region_periods(snapshots, regions, first_time):
    sampled = [(snapshot.time, reading["count"]) for snapshot, reading in zip(snapshots, regions, strict=True)
               if snapshot.time >= first_time and snapshot.time % 50 == 0]
    sustained = []
    for count, group in groupby(sampled, key=lambda row: row[1]):
        run = list(group)
        if count == 1 and len(run) >= 6:
            sustained.append({"start": run[0][0], "end": run[-1][0], "frames": len(run),
                              "observed_reversal": run[-1][0] < sampled[-1][0]})
    return sustained


def chemistry_window(ledger, recipe, start, end):
    times = ledger["time"]
    first, last = np.searchsorted(times, [start, end])
    if times[first] != start or times[last] != end:
        raise ValueError("Requested window does not match the exact sample clock")
    scale = (end - start) * recipe["molecules"]
    values = {key: float((ledger[key][last] - ledger[key][first]) / scale)
              for key in ("passive", "driven", "work", "passive_activity", "driven_activity")}
    values["B_fraction"] = time_mean(times, ledger["B_fraction"], start, end)
    values["gross_turnover"] = values["passive_activity"] + values["driven_activity"]
    return values


def observed_mean(times, values, start, end):
    left = bisect_right(times, start) - 1
    right = bisect_left(times, end) + 1
    selected = values[left:right]
    return time_mean(times[left:right], selected, start, end) if None not in selected else None


def window_readouts(readings, ledger, recipe, windows):
    times = [frame["time"] for frame in readings]
    result = {}
    for start, end in windows:
        if end > recipe["T"]:
            continue
        measured = {key: observed_mean(times, [f[key] for f in readings], start, end) for key in SCALES}
        measured["regions"] = {
            rho: {key: observed_mean(times, [f["regions"][rho][key] for f in readings], start, end)
                  for key in REGION_FIELDS}
            for rho in readings[0]["regions"]
        }
        result[str(end)] = {"window": [start, end], **measured, **chemistry_window(ledger, recipe, start, end)}
    return result


def check_prefix(new_bundle, old_path):
    """Verify every original physical checkpoint and the complete old event ledger."""
    with ZipFile(old_path) as old:
        members = sorted(name for name in old.namelist() if name.startswith("state-") and name.endswith(".bin"))
        for name in members:
            if old.read(name) != new_bundle.read(name):
                raise ValueError(f"Divergent physical trajectory at {old_path.name}/{name}")
        old_rows = old.read("series.csv").splitlines()
        new_rows = new_bundle.read("series.csv").splitlines()
        if old_rows != new_rows[:len(old_rows)]:
            raise ValueError(f"Divergent ledger for {old_path.name}")
        if not members or len(members) % 4:
            raise ValueError(f"Invalid reference archive {old_path}")
    return {"previous_archive": old_path.name, "previous_sha256": sha256(old_path),
            "byte_identical_states": len(members) // 4, "byte_identical_ledger_rows": len(old_rows) - 1}


def track_snapshot_regions(snapshots, settings, readings):
    histories, summaries, periods = {}, {}, {}
    minimum = settings["minimum_region_sites"]
    for threshold in settings["thresholds"]:
        key = str(threshold)
        region_frames = []
        region_reads = []
        for sample, metrics in zip(snapshots, readings, strict=True):
            # The integer field ranges from 0 to 64. Scaling the threshold is exact for these masks.
            frame = region_frame(sample.density_count, sample.positions, threshold * 64, minimum)
            reading = region_readout(frame, minimum)
            metrics["regions"][key] = reading
            region_reads.append(reading)
            region_frames.append(frame)
        histories[key], summaries[key] = {}, {}
        periods[key] = one_region_periods(snapshots, region_reads, settings["first_time"])
        for cadence in settings["cadences"]:
            indexes = [i for i, s in enumerate(snapshots)
                       if s.time >= settings["first_time"] and s.time % cadence == 0]
            aligned = [snapshots[i] for i in indexes]
            regions = [region_frames[i] for i in indexes]
            rows = observe_transitions(aligned, regions, settings)
            histories[key][str(cadence)] = rows
            summaries[key][str(cadence)] = summarize_transitions(rows)
    return histories, summaries, periods


def inspect(task):
    trial, evidence, registration, old_path, settings = task
    path = evidence / trial.relative_archive
    result = inspect_history(path, trial, {"observations": {"windows": []}}, registration_path=registration)
    recipe = result["recipe"]
    with ZipFile(path) as bundle:
        parent_frames = json.loads(bundle.read("summary.json"))["frames"]
        ledger = ledgers(bundle, recipe)
        snapshots = list(read_snapshots(bundle, recipe, result["frames"]))
        prefix = check_prefix(bundle, old_path) if old_path else None

    readings = [{**scale_readout(snapshot, frame), "regions": {}}
                for snapshot, frame in zip(snapshots, parent_frames, strict=True)]
    events, summaries, periods = track_snapshot_regions(snapshots, settings["domains"], readings)
    result.pop("frames")
    result.pop("two_time_identity_retention")
    result.update(
        windows=window_readouts(readings, ledger, recipe, settings["comparison_windows"]),
        full_tracking_exposure=chemistry_window(ledger, recipe, settings["domains"]["first_time"], recipe["T"]),
        prefix=prefix, region_budget=summaries, sustained_single_region=periods,
    )
    return result, readings, events


def tasks(panels, settings, evidence, previous_evidence):
    if sha256(PREVIOUS_PLAN) != settings["solver"]["baseline_registration_sha256"]:
        raise ValueError("The previous targeting matrix has changed")
    old = previous_trials(read_json(PREVIOUS_PLAN), "extent")
    previous_prefixes = {job.seed: previous_evidence / job.relative_archive for job in old if job.n == 56}
    jobs = []
    if "previous" in panels:
        jobs.extend((job, previous_evidence, PREVIOUS_PLAN, None, settings) for job in old)
    if "extent" in panels:
        jobs.extend((job, evidence, PLAN, previous_prefixes.get(job.seed) if job.n == 56 else None, settings)
                    for job in trials_for(settings))
    if "mobility" in panels:
        jobs.extend((job, evidence, MOBILITY_PLAN, None, settings)
                    for job in mobility_trials(read_json(MOBILITY_PLAN)))
    return jobs


def write_gzip(path, data):
    path.write_bytes(gzip.compress(json_text(data).encode(), compresslevel=6, mtime=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", choices=("all", "previous", "extent", "mobility"), default="all")
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    parser.add_argument("--previous", type=Path, default=PREVIOUS / "evidence")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    panels = ("previous", "extent", "mobility") if args.panel == "all" else (args.panel,)
    settings = read_json(PLAN)
    items = tasks(panels, settings, args.evidence, args.previous)
    records, frames, events = [], {}, {}
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        for record, readings, transitions in executor.map(inspect, items):
            key = record["archive"]
            records.append(record)
            frames[key], events[key] = readings, transitions
            print(f"{len(records)}/{len(items)} measured {key}", flush=True)
    result = {
        "registration_sha256": sha256(PLAN),
        "mechanism_registration_sha256": sha256(MECHANISM_PLAN),
        "mobility_registration_sha256": sha256(MOBILITY_PLAN),
        "archives": records,
        "matched_initial_groups": check_initial_matching(records),
        "max_relative_medium_error": max(row["max_relative_medium_error"] for row in records),
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "results.json").write_text(json_text(result))
    write_gzip(args.out / "frames.json.gz", frames)
    write_gzip(args.out / "transitions.json.gz", events)


if __name__ == "__main__":
    main()
