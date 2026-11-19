"""Audit each archived history and assemble seed-paired comparisons."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import sys
import zipfile

import numpy as np

from run import HERE, REGISTRATION, json_text, plan, read_json, sha256, valid_archive

sys.path.insert(0, str(HERE.parents[2]))
from observe import measure_frame, neighbor_sum, time_mean

METRICS = (
    "variance_4", "variance_2", "variance_4_x_only", "variance_4_transverse",
    "largest_fraction_0.5", "B_fraction", "work_rate", "driven_net_B_to_I",
    "passive_net_B_to_I",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_ledger(rows, recipe, explicit_fuel):
    parameters = recipe["parameters"]
    times = np.array([float(row["time"]) for row in rows])
    b = np.array([int(row["B"]) for row in rows])
    pairs = np.array([int(row["pairs"]) for row in rows])
    counts = np.array([[sum(int(row[f"rxn_{kind}_{n}"]) for n in range(7))
                        for kind in range(4)] for row in rows])
    passive = counts[:, 0] - counts[:, 1]
    driven = counts[:, 2] - counts[:, 3]
    h = np.array([float(row["H"]) for row in rows])
    work = np.array([float(row["work"]) for row in rows])
    medium = np.array([float(row["heat"]) for row in rows])
    scale = np.maximum.reduce((np.ones_like(work), np.abs(work), np.abs(h - h[0])))
    error = np.abs(medium - (work - (h - h[0]))) / scale
    require(np.array_equal(times, np.arange(0, recipe["T"] + 1, 10)), "Incomplete sample clock")
    require(np.isfinite(error).all() and error.max() <= 1e-10, "Medium entropy budget")
    require(b[0] == recipe["initial_B_count"], "Initial B count")
    require(np.array_equal(b, b[0] - passive - driven), "Independent B reaction ledger")
    require(np.allclose(h, parameters["df"] * b + parameters["epsilon"] * pairs, rtol=1e-14, atol=1e-12),
            "Independent Hamiltonian ledger")
    require(all(int(row["molecules"]) == recipe["molecules"] for row in rows), "Macro count ledger")

    result = {
        "time": times, "B_fraction": b / recipe["molecules"], "work": work,
        "passive": passive, "driven": driven, "B": b,
        "passive_activity": counts[:, 0] + counts[:, 1],
        "driven_activity": counts[:, 2] + counts[:, 3],
        "max_relative_medium_error": float(error.max()),
    }
    if explicit_fuel:
        f = np.array([int(row["F"]) for row in rows])
        w = np.array([int(row["W"]) for row in rows])
        f_net = np.array([int(row["F_in"]) - int(row["F_out"]) for row in rows])
        w_net = np.array([int(row["W_in"]) - int(row["W_out"]) for row in rows])
        require(np.array_equal(f, f[0] + f_net - driven), "Independent fuel ledger")
        require(np.array_equal(w, w[0] + w_net + driven), "Independent waste ledger")
        mu = parameters["mu"]
        log_f = np.log(parameters["z_total"]) - np.logaddexp(0.0, -mu)
        log_w = np.log(parameters["z_total"]) - np.logaddexp(0.0, mu)
        require(np.all(np.abs(work - (log_f * f_net + log_w * w_net)) <= 1e-10 * scale),
                "Independent reservoir work ledger")
        if parameters["source"] == "closed":
            require(not np.any(f_net) and not np.any(w_net) and not np.any(work), "Closed-world work")
        result.update(F=f, W=w, F_net=f_net, W_net=w_net,
                      log_f=float(log_f), log_w=float(log_w))
    return result


def read_frame(bundle, frame, recipe, row, initial_positions, explicit_fuel):
    n = recipe["N"]
    size = (n,) * 3
    sample = frame["sample"]
    physical = {}
    for kind in ("cells", "positions", "conformers", "displacements"):
        name = f"state-{sample}-{kind}.bin"
        physical[kind] = bundle.read(name)
        require(hashlib.sha256(physical[kind]).hexdigest() == frame["files"][name], f"SHA mismatch for {name}")
    cells = np.frombuffer(physical["cells"], dtype=np.uint8).reshape(size, order="F")
    positions = np.frombuffer(physical["positions"], dtype="<i4")
    conformers = np.frombuffer(physical["conformers"], dtype=np.uint8)
    displacement = np.frombuffer(physical["displacements"], dtype="<i8").reshape(-1, 3)
    require(np.all((positions >= 0) & (positions < n**3)), "Position outside the lattice")
    require(np.unique(positions).size == len(positions) == recipe["molecules"], "Macro site identities")
    require(np.array_equal(cells.ravel(order="F")[positions], conformers + 1), "Macro conformation map")

    coordinates = initial_positions + displacement
    wrapped = np.ravel_multi_index(coordinates.T, size, mode="wrap", order="F")
    require(np.array_equal(wrapped, positions), "Lagrangian displacements and occupied sites disagree")
    b = cells == 2
    require(int(b.sum()) == int(row["B"]), "B snapshot count")
    require(int(neighbor_sum(b)[b].sum()) == 2 * int(row["pairs"]), "Snapshot bond count")
    require(int(((cells == 1) | b).sum()) == recipe["molecules"], "Macro snapshot count")

    measures = measure_frame(cells, recipe["parameters"], explicit_fuel)
    for width in (2, 4):
        require(abs(measures[f"variance_{width}"] - frame["density_variances"][str(width)]["material"]) < 1e-12,
                "Independent density variance disagrees with the parent observer")
    if explicit_fuel:
        for code, species in enumerate(("I", "B", "F", "W"), 1):
            measured = np.rint(n**2 * np.asarray(measures["profiles"][species])).astype(int)
            recorded = [int(row[f"profile_{code}_{x}"]) for x in range(n)]
            require(np.array_equal(measured, recorded), "Independent profile count")
        require(np.count_nonzero(cells == 3) == int(row["F"])
                and np.count_nonzero(cells == 4) == int(row["W"]), "Fuel or waste snapshot count")
    return {"time": frame["time"], **measures}


def window_metrics(frames, ledger, recipe, window):
    start, end = window["start"], window["end"]
    frame_times = [frame["time"] for frame in frames]

    def average(values, times=frame_times):
        return time_mean(times, values, start, end)

    i, j = np.searchsorted(ledger["time"], [start, end])
    require(ledger["time"][i] == start and ledger["time"][j] == end, "Window is off the ledger clock")
    exposure = (end - start) * recipe["molecules"]

    def flux(key):
        return float((ledger[key][j] - ledger[key][i]) / exposure)

    metrics = {
        key: average([frame[key] for frame in frames])
        for key in ("variance_4", "variance_2", "variance_4_x_only", "variance_4_transverse")
    }
    for threshold in ("0.3", "0.5", "0.7"):
        volume = [next(iter(frame["density_regions"][threshold]["largest_volumes"]), 0)
                  for frame in frames]
        metrics[f"largest_fraction_{threshold}"] = average(volume) / recipe["N"]**3
    metrics.update(
        B_fraction=average(ledger["B_fraction"], ledger["time"]),
        work_rate=flux("work"), passive_net_B_to_I=flux("passive"), driven_net_B_to_I=flux("driven"),
        B_population_drift_rate=flux("B"), passive_gross_rate=flux("passive_activity"),
        driven_gross_rate=flux("driven_activity"),
    )
    if "F" in ledger:
        metrics["F_reservoir_net"] = flux("F_net")
        metrics["W_reservoir_net"] = flux("W_net")
        metrics["conversion_work_rate"] = recipe["parameters"]["mu"] * metrics["driven_net_B_to_I"]
        metrics["inventory_work_rate"] = ledger["log_f"] * flux("F") + ledger["log_w"] * flux("W")
        require(abs(metrics["work_rate"] - metrics["conversion_work_rate"]
                    - metrics["inventory_work_rate"]) < 1e-10, "Window work decomposition")
        metrics["F_site_fraction"] = average(ledger["F"] / recipe["N"]**3, ledger["time"])
        metrics["W_site_fraction"] = average(ledger["W"] / recipe["N"]**3, ledger["time"])
        metrics["encounter_propensities_per_macro"] = {
            direction: {
                key: average([frame["encounters"][direction]["propensities"][key] for frame in frames])
                / recipe["molecules"]
                for key in ("observed", "well_mixed", "same_x_mixed")
            }
            for direction in ("B_to_I", "I_to_B")
        }
    return metrics


def inspect_history(path, trial, registration):
    require(valid_archive(path, trial, sha256(REGISTRATION)), f"Missing {path}")
    explicit_fuel = trial.engine != "lattice"
    with zipfile.ZipFile(path) as bundle:
        recipe = json.loads(bundle.read("recipe.json"))
        summary = json.loads(bundle.read("summary.json"))
        execution = json.loads(bundle.read("execution.json"))
        rows = list(csv.DictReader(io.StringIO(bundle.read("series.csv").decode())))
        ledger = read_ledger(rows, recipe, explicit_fuel)
        states = summary["frames"]
        require(states[0]["time"] == 0 and states[-1]["time"] == recipe["T"], "Missing initial or final state")
        shape = (recipe["N"],) * 3
        initial = np.frombuffer(bundle.read("state-0-positions.bin"), dtype="<i4")
        initial_coordinates = np.column_stack(np.unravel_index(initial, shape, order="F"))
        frames = [read_frame(bundle, frame, recipe, rows[frame["sample"]], initial_coordinates, explicit_fuel)
                  for frame in states]
    windows = {
        str(window["end"]): window_metrics(frames, ledger, recipe, window)
        for window in registration["observations"]["windows"] if window["end"] <= recipe["T"]
    }
    return {
        "archive": trial.relative_archive.as_posix(), "archive_sha256": sha256(path),
        "phase": trial.phase, "engine": trial.engine, "recipe": recipe, "execution": execution,
        "initial_hashes": states[0]["files"], "windows": windows, "frames": frames,
        "max_relative_medium_error": ledger["max_relative_medium_error"],
    }


def check_initial_matching(histories):
    fuel = {}
    lattice = {}
    for record in histories:
        recipe = record["recipe"]
        hashes = record["initial_hashes"]
        key = recipe["N"], recipe["seed"]
        if record["engine"] == "lattice":
            positions = hashes["state-0-positions.bin"]
            require(lattice.setdefault(key, positions) == positions, "Lattice initial macro positions differ")
        else:
            key += (recipe["parameters"]["mu"],)
            require(fuel.setdefault(key, hashes) == hashes, "Fuel initial states differ within a paired group")
    return {"fuel_groups": len(fuel), "lattice_position_groups": len(lattice)}


def describe(values):
    return {
        "mean": float(np.mean(values)), "median": float(np.median(values)),
        "min": min(values), "max": max(values),
        "positive": sum(value > 0 for value in values), "negative": sum(value < 0 for value in values),
    }


def contrasts(pairs):
    differences = []
    for seed, left, right in pairs:
        differences.append({"seed": seed, **{key: left[key] - right[key] for key in METRICS}})
    return {"differences": differences, "summary": {
        key: describe([pair[key] for pair in differences]) for key in METRICS
    }}


def compare_histories(records, slots, registration):
    index = {
        (r["phase"], r["recipe"]["N"], r["recipe"]["seed"], r["recipe"]["case"]["id"]): r
        for r in records
    }
    by_archive = {r["archive"]: r for r in records}
    holdout = registration["phases"]["fuel_holdout"]
    pairs = (
        ("fed_minus_fast", "closed_minus"), ("fed_minus_fast", "fed_minus_slow"),
        ("uniform_minus", "fed_minus_fast"), ("fed_minus_fast", "fed_minus_no_passive"),
        ("uniform_minus", "uniform_minus_no_passive"),
    )

    def window(phase, n, seed, case, end):
        return index[phase, n, seed, case]["windows"][str(end)]

    holdout_pairs = {}
    for n, end, (left, right) in itertools.product(holdout["N"], (300, 600), pairs):
        if n == 24 and right.endswith("no_passive"):
            continue
        holdout_pairs[f"N{n}T{end}:{left}-{right}"] = contrasts([
            (seed, window("fuel_holdout", n, seed, left, end), window("fuel_holdout", n, seed, right, end))
            for seed in holdout["seeds"]
        ])
    volume = {
        case: contrasts([
            (seed, window("fuel_holdout", 32, seed, case, 600), window("fuel_holdout", 24, seed, case, 600))
            for seed in holdout["seeds"]
        ])
        for case in holdout["cases_both_volumes"]
    }
    time = {
        f"N{n}:{case}": contrasts([
            (seed, window("fuel_holdout", n, seed, case, 600), window("fuel_holdout", n, seed, case, 300))
            for seed in holdout["seeds"]
        ])
        for n in holdout["N"]
        for case in holdout["cases_both_volumes"] + (holdout["cases_N32_only"] if n == 32 else [])
    }

    lattice_seeds = registration["phases"]["lattice_matched"]["seeds"]
    lattice_pairs = {
        f"{left}-{right}": contrasts([
            (seed, window("lattice_matched", 32, seed, left, 3000),
             window("lattice_matched", 32, seed, right, 3000))
            for seed in lattice_seeds
        ])
        for left, right in (
            ("dynamic_high_df", "dynamic_low_df"), ("I_slow_high_df", "I_slow_low_df"),
            ("dynamic_high_df", "I_slow_high_df"), ("dynamic_low_df", "I_slow_low_df"),
        )
    }
    brackets = []
    for seed, (case, mobility) in itertools.product(
        lattice_seeds, (("dynamic_high_df", 100), ("I_slow_high_df", 1)),
    ):
        active = window("lattice_matched", 32, seed, case, 3000)
        nulls = sorted(
            (r["windows"]["3000"]["B_fraction"], r["windows"]["3000"]["variance_4"])
            for r in records if r["phase"] == "lattice_brackets" and r["recipe"]["seed"] == seed
            and r["recipe"]["parameters"]["D_I"] == mobility
        )
        x, y = np.array(nulls).T
        target = active["B_fraction"]
        found = bool(x[0] <= target <= x[-1])
        row = {"seed": seed, "case": case, "I_mobility": mobility, "active_B": target,
               "active_variance": active["variance_4"], "nulls_B_variance": nulls,
               "bracket_available": found}
        if found:
            upper = min(max(1, int(np.searchsorted(x, target, side="right"))), len(x) - 1)
            prediction = float(np.interp(target, x, y))
            lo, hi = float(y[upper - 1]), float(y[upper])
            row.update(
                bracket_B=[float(x[upper - 1]), float(x[upper])], bracket_variance=[lo, hi],
                interpolated_variance=prediction, signed_residual=active["variance_4"] - prediction,
                strictly_above_both=active["variance_4"] > max(lo, hi),
                strictly_below_both=active["variance_4"] < min(lo, hi),
            )
        brackets.append(row)

    grid = []
    for slot in slots:
        record = by_archive[slot["archive"]]
        grid.append({
            **slot, "archive_sha256": record["archive_sha256"], "engine": record["engine"],
            **{key: record["windows"]["300"][key] for key in METRICS},
        })
    return {
        "fuel_holdout_paired": holdout_pairs, "fuel_holdout_volume_N32_minus_N24": volume,
        "fuel_holdout_late_minus_early": time, "lattice_paired": lattice_pairs,
        "lattice_composition_matches": brackets, "fuel_grid_slots": grid,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reg = read_json(REGISTRATION)
    trials, slots = plan()
    records = []
    for phase, jobs in trials.items():
        for trial in jobs:
            try:
                records.append(inspect_history(args.evidence / trial.relative_archive, trial, reg))
            except Exception as error:
                raise RuntimeError(f"Audit failed for {trial.relative_archive}") from error
        print(f"Validated {phase}: {len(jobs)} histories", flush=True)
    comparisons = compare_histories(records, slots, reg)
    validation = check_initial_matching(records)
    summary = {
        "registration_sha256": sha256(REGISTRATION),
        "counts": {phase: len(jobs) for phase, jobs in trials.items()},
        "initial_condition_checks": validation,
        "maximum_relative_medium_error": max(r["max_relative_medium_error"] for r in records),
        "failures_retained": [
            {"path": str(path.relative_to(args.evidence)), "sha256": sha256(path)}
            for path in sorted((args.evidence / "failures").rglob("*.zip"))
        ],
        **comparisons,
        "archives": [
            {key: record[key] for key in ("archive", "archive_sha256", "phase", "engine", "windows")}
            for record in records
        ],
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "results.json").write_text(json_text(summary), encoding="utf-8")
    (args.out / "observations.json.gz").write_bytes(gzip.compress(json_text(records).encode(), mtime=0))
    print(f"Audited and retained {len(records)} histories", flush=True)


if __name__ == "__main__":
    main()
