"""Measure periodic scales and local currents on sealed trajectory archives."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
from functools import lru_cache
import gzip
import io
import math
from pathlib import Path
import zipfile

import numpy as np
from scipy.ndimage import label, uniform_filter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from simulate import PLAN, SUPPLY_PLAN, read_json, sha256, supply_trials, trials_for
from analyse import check_initial_matching, composition_residual, inspect_history, read_ledger
from longtime import PLAN as OLD_PLAN, trials_for as old_trials
from observe import FACE_NEIGHBORS, THRESHOLDS, neighbor_sum, time_mean
from run import json_text

GROWTH_FIELDS = ("spectral_length", "half_correlation", "first_shell_fraction")
MATCH_FIELDS = ("variance_4", "variance_2", "gross_turnover", *GROWTH_FIELDS)
DENSITY_BINS = ("dilute", "intermediate", "dense")


@lru_cache(maxsize=4)
def mode_norms(n):
    axes = np.rint(np.fft.fftfreq(n) * n).astype(int)
    squared = axes**2
    norm_squared = squared[:, None, None] + squared[None, :, None] + squared[None, None, :]
    return np.sqrt(norm_squared), norm_squared == 1


def spectral_length(density):
    n = density.shape[0]
    amps = np.fft.fftn(density - density.mean())
    power = amps.real**2 + amps.imag**2
    power[0, 0, 0] = 0.0
    total = math.fsum(power.flat)
    if total == 0.0:
        return None, None, 0.0
    norms, first_shell = mode_norms(n)
    return (
        n * total / math.fsum((power * norms).flat),
        math.fsum(power[first_shell]) / total,
        total / density.size**2,
    )


def half_correlation(counts):
    """Axial covariance crossing, exact integer contractions before interpolation."""
    volume = counts.size
    squared_sum = int((counts * counts).sum(dtype=np.int64))
    total_squared = int(counts.sum(dtype=np.int64)) ** 2
    denominator = 3 * (volume * squared_sum - total_squared)
    if denominator == 0:
        return None
    previous = 1.0
    for step in range(1, counts.shape[0] // 2 + 1):
        overlap = sum(int((counts * np.roll(counts, step, axis=axis)).sum(dtype=np.int64))
                      for axis in range(3))
        value = (volume * overlap - 3 * total_squared) / denominator
        if value <= 0.5:
            return step - 1 + (previous - 0.5) / (previous - value)
        previous = value
    return None


def periodic_partition(mask):
    """Stitch open six-neighbor labels across the three periodic cuts."""
    labels, count = label(mask, structure=FACE_NEIGHBORS)
    if count == 0:
        return labels, np.zeros(1, dtype=int), np.empty(0, dtype=np.int64)
    pairs = []
    for axis in range(3):
        left, right = np.take(labels, 0, axis=axis), np.take(labels, -1, axis=axis)
        touches = (left > 0) & (right > 0)
        pairs.append(np.column_stack((left[touches], right[touches])) - 1)
    a, b = np.concatenate(pairs).T
    graph = coo_matrix((np.ones(len(a)), (a, b)), shape=(count, count)).tocsr()
    groups, membership = connected_components(graph, directed=False)
    open_sizes = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    sizes = np.zeros(groups, dtype=np.int64)
    np.add.at(sizes, membership, open_sizes)
    return labels, np.concatenate(([0], membership + 1)), sizes


def component_sizes(mask):
    return np.sort(periodic_partition(mask)[2])[::-1]


def reaction_fields(cells, parameters):
    """Forward I→B and backward B→I rates per material site, in each path."""
    i, b = cells == 1, cells == 2
    adjacent_b = neighbor_sum(b)
    df, eps = parameters["df"], parameters["epsilon"]
    p, eta = parameters["passive_rate"], parameters["eta"]
    k = range(7)
    passive_reverse = np.asarray([p * math.exp(df + eps * n) for n in k])
    linked_forward = np.asarray([eta * math.exp(-0.5 * eps * n) / 6 for n in k])
    linked_reverse = np.asarray([eta * math.exp(df + 0.5 * eps * n) / 6 for n in k])
    return (
        p * i,
        b * passive_reverse[adjacent_b],
        i * linked_forward[adjacent_b] * neighbor_sum(cells == 4),
        b * linked_reverse[adjacent_b] * neighbor_sum(cells == 3),
    )


def material_hop_derivative(cells, parameters):
    i, b, empty = cells == 1, cells == 2, cells == 0
    escape = np.asarray([parameters["D_B"] * math.exp(parameters["epsilon"] * n) for n in range(7)])
    departure = (parameters["D_I"] * i + b * escape[neighbor_sum(b)]) / 6
    derivative = np.zeros(cells.shape)
    for axis in range(3):
        for step in (-1, 1):
            outgoing = departure * np.roll(empty, -step, axis=axis)
            derivative += np.roll(outgoing, step, axis=axis) - outgoing
    return derivative


def density_currents(cells, density, parameters, inherited):
    occup = (cells == 1) | (cells == 2)
    bands = np.searchsorted((0.3, 0.7), density, side="right").ravel()
    p_f, p_r, d_f, d_r = reaction_fields(cells, parameters)
    expected = {
        "I_to_B": float(d_f.sum()),
        "B_to_I": float(d_r.sum()),
    }
    if not all(math.isclose(value, inherited[direction]["propensities"]["observed"],
                            rel_tol=1e-12, abs_tol=1e-10) for direction, value in expected.items()):
        raise ValueError("Independent encounter propensity disagrees")
    hop_derivative = material_hop_derivative(cells, parameters)
    if abs(math.fsum(hop_derivative.flat)) > cells.size * 1e-12:
        raise ValueError("Material hopping does not sum to zero")
    channels = {
        "volume_sites": None,
        "material_sites": occup,
        "B_sites": cells == 2,
        "passive_net_B": p_f - p_r,
        "linked_net_B": d_f - d_r,
        "gross_flip_rate": p_f + p_r + d_f + d_r,
        "material_hop_derivative": hop_derivative,
    }
    totals = {
        field: np.bincount(bands, weights=None if values is None else values.ravel(), minlength=3)
        for field, values in channels.items()
    }
    result = {name: {field: float(value[index]) for field, value in totals.items()}
              for index, name in enumerate(DENSITY_BINS)}
    if sum(x["volume_sites"] for x in result.values()) != cells.size:
        raise ValueError("Density bins do not cover the box")
    return result


def frame_readouts(cells, frame, parameters):
    density = uniform_filter(((cells == 1) | (cells == 2)).astype(float), size=4, mode="wrap")
    length, first_shell, variance = spectral_length(density)
    if not math.isclose(variance, frame["variance_4"], rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("Width-4 Parseval and archived variance disagree")
    counts = np.rint(density * 4**3).astype(np.int16)
    correlation = half_correlation(counts)
    morphology = {}
    for threshold in THRESHOLDS:
        key = str(threshold)
        prior = frame["density_regions"][key]
        sizes = component_sizes(density > threshold)
        if len(sizes) != prior["count"] or sizes[:8].tolist() != prior["largest_volumes"]:
            raise ValueError("Independent periodic component volumes disagree")
        morphology[key] = {
            "largest_fraction": prior["largest_volumes"][0] / cells.size if len(sizes) else 0.0,
            "component_count": len(sizes),
            "components_at_least_64": int(np.count_nonzero(sizes >= 64)),
            "winding_component_count": prior["winding_component_count"],
            "largest_winding_axes": prior["largest_winding_axes"],
        }
    return {
        "time": frame["time"],
        "variance_4": frame["variance_4"],
        "variance_2": frame["variance_2"],
        "spectral_length": length,
        "half_correlation": correlation,
        "first_shell_fraction": first_shell,
        "domains": morphology,
        "density_bins": density_currents(cells, density, parameters, frame["encounters"]),
    }


def summarize_window(frames, ledger, recipe, start, end):
    times = [frame["time"] for frame in frames]

    def snapshot_mean(values):
        if any(value is None for value in values):
            segment = range(max(0, np.searchsorted(times, start, side="right") - 1),
                            np.searchsorted(times, end, side="left") + 1)
            if any(values[i] is None for i in segment):
                return None
            values = [0.0 if value is None else value for value in values]
        return time_mean(times, values, start, end)

    result = {field: snapshot_mean([frame[field] for frame in frames])
              for field in ("variance_4", "variance_2", *GROWTH_FIELDS)}
    result["spectral_over_box"] = result["spectral_length"] / recipe["N"] if result["spectral_length"] else None
    result["domains"] = {
        str(threshold): {
            field: snapshot_mean([frame["domains"][str(threshold)][field] for frame in frames])
            for field in ("largest_fraction", "component_count", "components_at_least_64", "winding_component_count")
        }
        for threshold in THRESHOLDS
    }
    bins = {}
    exposure = recipe["molecules"]
    volume = recipe["N"]**3
    for name in DENSITY_BINS:
        totals = {key: snapshot_mean([frame["density_bins"][name][key] for frame in frames])
                  for key in frames[0]["density_bins"][name]}
        material = totals["material_sites"]
        bins[name] = {
            "volume_fraction": totals["volume_sites"] / volume,
            "material_fraction": material / exposure,
            "B_fraction": totals["B_sites"] / material if material else None,
            "linked_work_per_box_site": -recipe["parameters"]["mu"] * totals["linked_net_B"] / volume,
            "currents_per_material": {
                key: totals[key] / material if material else None
                for key in ("passive_net_B", "linked_net_B", "gross_flip_rate", "material_hop_derivative")
            },
        }
    i, j = np.searchsorted(ledger["time"], [start, end])
    if [int(ledger["time"][i]), int(ledger["time"][j])] != [start, end]:
        raise ValueError("Window endpoints are absent from the reaction ledger")

    def per_material(key):
        return float(ledger[key][j] - ledger[key][i]) / ((end - start) * exposure)

    result.update({
        "window": [start, end],
        "B_fraction": time_mean(ledger["time"], ledger["B_fraction"], start, end),
        "gross_turnover": per_material("passive_activity") + per_material("driven_activity"),
        "ledger_passive_net_B": -per_material("passive"),
        "ledger_linked_net_B": -per_material("driven"),
        "B_change_per_material_time": per_material("B"),
        "work_rate": per_material("work"),
        "F_net": per_material("F_net"),
        "W_net": per_material("W_net"),
        "density_bins": bins,
    })
    return result


def measure_trial(item):
    trial, evidence, registration, windows = item
    path = evidence / trial.relative_archive
    prior = inspect_history(path, trial, {"observations": {"windows": []}}, registration_path=registration)
    recipe = prior["recipe"]
    with zipfile.ZipFile(path) as bundle:
        ledger = read_ledger(list(csv.DictReader(io.StringIO(bundle.read("series.csv").decode()))), recipe, True)
        frames = []
        for frame in prior["frames"]:
            sample = int(frame["time"] // 10)
            cells = np.frombuffer(bundle.read(f"state-{sample}-cells.bin"), np.uint8).reshape((recipe["N"],)*3, order="F")
            frames.append(frame_readouts(cells, frame, recipe["parameters"]))
    record = {k: prior[k] for k in ("archive", "archive_sha256", "recipe", "phase", "engine", "initial_hashes", "max_relative_medium_error")}
    record["windows"] = {str(end): summarize_window(frames, ledger, recipe, start, end)
                         for start, end in windows if end <= trial.duration}
    return record, frames


def matched_controls(records, active_case):
    groups = defaultdict(list)
    for row in records:
        recipe = row["recipe"]
        if row["windows"] and row["phase"] in ("extent", "matched_longtime"):
            groups[recipe["N"], recipe["seed"]].append(row)
    matched = []
    for (n, seed), group in sorted(groups.items()):
        if len(group) == 1:
            continue
        active = next(row for row in group if row["recipe"]["case"]["id"] == active_case)
        controls = [row for row in group if row is not active]
        for end, actual in active["windows"].items():
            reference = {}
            for field in MATCH_FIELDS:
                if actual[field] is None:
                    continue
                points = sorted((row["windows"][end]["B_fraction"], row["windows"][end][field])
                                for row in controls if row["windows"][end][field] is not None)
                if len(points) < 2:
                    continue
                comparison = composition_residual(actual["B_fraction"], actual[field], points)
                if comparison["bracket_available"]:
                    comparison["bracket_control_values"] = comparison.pop("bracket_variance")
                    comparison["interpolated_control"] = comparison.pop("interpolated_variance")
                reference[field] = comparison
            difference = reference["gross_turnover"].get("signed_residual")
            rate_error = abs(difference) / actual["gross_turnover"] if difference is not None else None
            matched.append({"N": n, "seed": seed, "window": actual["window"],
                            "active_B": actual["B_fraction"], "active_rate": actual["gross_turnover"],
                            "gross_fractional_error": rate_error,
                            "gross_within_10_percent": rate_error is not None and rate_error <= 0.1,
                            "comparisons": reference})
    return matched


def extent_readouts(records, active_case):
    active = [row for row in records if row["recipe"]["case"]["id"] == active_case]
    groups = defaultdict(list)
    for row in active:
        for end, window in row["windows"].items():
            groups[row["recipe"]["N"], int(end)].append((row["recipe"]["seed"], window))
    summaries = []
    for (n, end), pairs in sorted(groups.items()):
        measurements = {}
        for field in (*GROWTH_FIELDS, "spectral_over_box", "variance_4", "B_fraction", "gross_turnover", "work_rate"):
            nums = [window[field] for _, window in pairs]
            measurements[field] = {"by_seed": nums, "mean": math.fsum(nums) / len(nums) if None not in nums else None}
        summaries.append({"N": n, "end": end, "seeds": [seed for seed, _ in pairs], "measurements": measurements})
    return summaries


def plateau_diagnostic(summaries):
    means = {(row["N"], row["end"]): {name: data["mean"] for name, data in row["measurements"].items()}
             for row in summaries}
    earlier, late = 1800, 2400

    def relative_change(a, b):
        return a / b - 1 if a is not None and b else None

    temporal = {
        str(n): {f: relative_change(means[n, late][f], means[n, earlier][f]) for f in GROWTH_FIELDS[:2]}
        for n in (48, 56)
    }
    extent = {f: relative_change(means[56, late][f], means[48, late][f]) for f in GROWTH_FIELDS[:2]}
    first_shell = {str(n): means[n, late]["first_shell_fraction"] for n in (48, 56)}
    passes = {
        "temporal_within_5_percent": all(value is not None and abs(value) <= 0.05
                                         for fields in temporal.values() for value in fields.values()),
        "size_within_10_percent": all(value is not None and abs(value) <= 0.1 for value in extent.values()),
        "first_shell_below_majority": all(value is not None and value <= 0.5 for value in first_shell.values()),
    }
    return {"temporal_change": temporal, "size_change": extent, "first_shell_fraction": first_shell,
            "passes": passes, "all_pass": all(passes.values())}


def clock_readouts(records, active_case):
    baseline = {row["recipe"]["seed"]: row for row in records
                if row["recipe"]["N"] == 32 and row["recipe"]["case"]["id"] == active_case}
    return [
        {"seed": row["recipe"]["seed"], "case": row["recipe"]["case"]["id"],
         "driven": row["windows"]["2400"], "intermediate_clock": baseline[row["recipe"]["seed"]]["windows"]["2400"]}
        for row in records if row["phase"] == "clock"
    ]


def supply_readouts(records, active_case):
    fields = ("B_fraction", "gross_turnover", "work_rate", "variance_4", *GROWTH_FIELDS)
    groups = defaultdict(dict)
    names = {
        active_case: "r1_k1", "clock_4": "r4_k1",
        "supply_clock_1": "r1_k4", "supply_clock_4": "r4_k4",
    }
    for row in records:
        recipe = row["recipe"]
        case = recipe["case"]["id"]
        if recipe["N"] == 32 and case in names:
            groups[recipe["seed"]][names[case]] = row["windows"]["2400"]
    results = []
    for seed, arms in sorted(groups.items()):
        effects = {}
        for name, a, b in (
            ("reaction_at_k1", "r4_k1", "r1_k1"), ("reaction_at_k4", "r4_k4", "r1_k4"),
            ("supply_at_r1", "r1_k4", "r1_k1"), ("supply_at_r4", "r4_k4", "r4_k1"),
        ):
            effects[name] = {f: arms[a][f] - arms[b][f] if None not in (arms[a][f], arms[b][f]) else None
                             for f in fields}
            effects[name]["B_within_0.02"] = abs(effects[name]["B_fraction"]) <= 0.02
        low, high = effects["reaction_at_k1"], effects["reaction_at_k4"]
        interaction = {f: high[f] - low[f] if None not in (high[f], low[f]) else None for f in fields}
        results.append({"seed": seed, "arms": {name: {f: w[f] for f in fields} for name, w in arms.items()},
                        "effects": effects, "difference_of_differences": interaction})
    return results


def audit(evidence, output, jobs, previous):
    plan = read_json(PLAN)
    windows = plan["windows"]
    if previous:
        trials = old_trials(read_json(OLD_PLAN)["explicit"])
        sources = [(trial, evidence, OLD_PLAN, windows) for trial in trials]
    else:
        trials = [*trials_for(plan, "extent"), *trials_for(plan, "clock")]
        supplied = supply_trials(plan, read_json(SUPPLY_PLAN))
        sources = [(trial, evidence, PLAN, windows) for trial in trials]
        sources += [(trial, evidence, SUPPLY_PLAN, windows) for trial in supplied]
    records, frames = [], {}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for index, (record, checkpoints) in enumerate(pool.map(measure_trial, sources), 1):
            records.append(record)
            frames[record["archive"]] = checkpoints
            print(f"Audited {index}/{len(sources)} {record['archive']}", flush=True)
    active_case = plan["solver"]["parent_case"]
    result = {
        "registration_sha256": sha256(OLD_PLAN if previous else PLAN),
        "count": len(records),
        "matched_initial_groups": check_initial_matching(records),
        "maximum_relative_medium_error": max(row["max_relative_medium_error"] for row in records),
        "archives": records,
        "matched_controls": matched_controls(records, active_case),
        "extent": extent_readouts(records, active_case),
    }
    if not previous:
        result["supply_registration_sha256"] = sha256(SUPPLY_PLAN)
        result["plateau"] = plateau_diagnostic(result["extent"])
        result["clock_comparisons"] = clock_readouts(records, active_case)
        result["supply_comparisons"] = supply_readouts(records, active_case)
        result["partial_attempts"] = [{"path": p.relative_to(evidence).as_posix(), "sha256": sha256(p)}
                                      for p in sorted((evidence / "failures").rglob("*.zip"))]
    output.mkdir(parents=True, exist_ok=False)
    (output / "results.json").write_text(json_text(result), encoding="utf-8")
    (output / "frames.json.gz").write_bytes(gzip.compress(json_text(frames).encode(), mtime=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--previous", action="store_true", help="Re-analyze the previous 32 verified trajectories.")
    args = parser.parse_args()
    audit(args.evidence, args.out, args.jobs, args.previous)


if __name__ == "__main__":
    main()
