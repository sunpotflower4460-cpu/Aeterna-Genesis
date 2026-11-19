"""Run and audit longer 3D fluid histories at matched reservoir capacity and turnover."""
from __future__ import annotations

import argparse
from functools import lru_cache
import gzip
from itertools import product
import math
from pathlib import Path
import sys
import zipfile

import numpy as np
from scipy.ndimage import uniform_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261119-transport-and-composition"))

from analyse import check_initial_matching, composition_residual, inspect_history
from observe import time_mean
from run import FUEL, Trial, json_text, read_json, run_phase, sha256

PLAN = HERE / "PRE_REGISTRATION.json"
PHASE = "matched_longtime"


def trials_for(plan):
    calibration = plan["calibration"]
    if sha256(HERE.parent / calibration["path"]) != calibration["sha256"]:
        raise ValueError("Changed calibration data")
    fuel = read_json(FUEL / "PRE_REGISTRATION.json")
    parent = next(case for case in fuel["cases"] if case["id"] == plan["parent_case"])
    cases = [parent] + [
        {
            **parent, "id": f"reversible_df{item['df']:g}", "eta": 0.0,
            "df": item["df"], "passive_rate": item["passive_rate"],
        } for item in calibration["by_df"]
    ]
    jobs = [
        Trial(PHASE, "sparse", n, plan["duration"], seed, {**case, "kex": n * plan["kex_per_site"]})
        for n, seed, case in product(reversed(plan["sizes"]), plan["seeds"], cases)
    ]
    if len(jobs) != plan["count"] or len({job.key for job in jobs}) != len(jobs):
        raise ValueError("Registration does not enumerate the full matrix")
    return jobs


@lru_cache
def wave_numbers(n):
    modes = np.fft.fftfreq(n) * n
    squared = modes**2
    return np.sqrt(squared[:, None, None] + squared[None, :, None] + squared[None, None, :])


def density_wavelength(cells):
    """Power-weighted inverse wave number and Parseval validation for width-4 density."""
    macro = (cells == 1) | (cells == 2)
    coarse = uniform_filter(macro.astype(float), size=4, mode="wrap")
    return wavelength_from_density(coarse)


def wavelength_from_density(density):
    modes = np.fft.fftn(density - density.mean())
    power = modes.real**2 + modes.imag**2
    power[0, 0, 0] = 0.0
    total = math.fsum(power.flat)
    if total == 0.0:
        return None, 0.0
    n = density.shape[0]
    mean_mode = math.fsum((power * wave_numbers(n)).flat) / total
    return n / mean_mode, total / density.size**2


def add_spectra(path, record, plan):
    n = record["recipe"]["N"]
    with zipfile.ZipFile(path) as bundle:
        for frame in record["frames"]:
            sample = int(frame["time"] // 10)
            raw = bundle.read(f"state-{sample}-cells.bin")
            cells = np.frombuffer(raw, np.uint8).reshape((n,) * 3, order="F")
            wavelength, variance = density_wavelength(cells)
            if not np.isclose(variance, frame["variance_4"], rtol=0, atol=1e-12):
                raise ValueError(f"Parseval check failed for {path.name} at {frame['time']}")
            frame["wavelength_sites"] = wavelength
    times = [f["time"] for f in record["frames"]]
    values = [f["wavelength_sites"] for f in record["frames"]]
    for window in plan["windows"]:
        stats = record["windows"][str(window["end"])]
        wavelength = None if any(v is None for v in values) else time_mean(
            times, values, window["start"], window["end"],
        )
        stats["wavelength_sites"] = wavelength
        stats["wavelength_over_box"] = wavelength / n if wavelength is not None else None
        stats["gross_turnover"] = stats["passive_gross_rate"] + stats["driven_gross_rate"]


def compare(histories, plan):
    index = {(r["recipe"]["N"], r["recipe"]["seed"]): [] for r in histories}
    for record in histories:
        recipe = record["recipe"]
        index[recipe["N"], recipe["seed"]].append(record)
    output = []
    for (n, seed), group in sorted(index.items()):
        active = next(r for r in group if r["recipe"]["case"]["id"] == plan["parent_case"])
        controls = [r for r in group if r is not active]
        for window in plan["windows"]:
            end = str(window["end"])
            reference = active["windows"][end]
            b = reference["B_fraction"]
            comparisons = {}
            for field in ("variance_4", "variance_2", "gross_turnover", "wavelength_sites", "wavelength_over_box"):
                if reference[field] is None:
                    continue
                points = sorted((r["windows"][end]["B_fraction"], r["windows"][end][field])
                                for r in controls if r["windows"][end][field] is not None)
                if len(points) >= 2:
                    comparison = composition_residual(b, reference[field], points)
                    if comparison["bracket_available"]:
                        comparison["bracket_control_values"] = comparison.pop("bracket_variance")
                        comparison["interpolated_control"] = comparison.pop("interpolated_variance")
                    comparisons[field] = comparison
            turnover = comparisons["gross_turnover"]
            fractional_error = (abs(turnover["signed_residual"]) / reference["gross_turnover"]
                                if turnover["bracket_available"] else None)
            output.append({
                "N": n, "seed": seed, "window": window, "driven_B": b,
                "driven_gross_turnover": reference["gross_turnover"],
                "gross_fractional_error": fractional_error,
                "gross_within_10_percent": fractional_error is not None and fractional_error <= .10,
                "measures": comparisons,
                "controls_B": [r["windows"][end]["B_fraction"] for r in controls],
            })
    return output


def audit(jobs, plan, evidence, output):
    observation = {"observations": {"windows": plan["windows"]}}
    histories = []
    for number, trial in enumerate(jobs, 1):
        path = evidence / trial.relative_archive
        record = inspect_history(path, trial, observation, registration_path=PLAN)
        add_spectra(path, record, plan)
        histories.append(record)
        if number % 8 == 0:
            print(f"{number}/{len(jobs)} histories independently audited.", flush=True)
    by_seed = check_initial_matching(histories)
    report = {
        "registration_sha256": sha256(PLAN), "count": len(histories), "matched_initial_groups": by_seed,
        "maximum_relative_medium_error": max(r["max_relative_medium_error"] for r in histories),
        "comparisons": compare(histories, plan),
        "archives": [{
            key: r[key] for key in ("archive", "archive_sha256", "recipe", "windows")
        } for r in histories],
        "partial_attempts": [{"path": p.relative_to(evidence).as_posix(), "sha256": sha256(p)}
                             for p in sorted((evidence / "failures").rglob("*.zip"))],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "results.json").write_text(json_text(report), encoding="utf-8")
    (output / "observations.json.gz").write_bytes(gzip.compress(json_text(histories).encode(), mtime=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    simulate = subparsers.add_parser("simulate")
    simulate.add_argument("--scratch", type=Path, required=True)
    simulate.add_argument("--jobs", type=int, default=4)
    simulate.add_argument("--size", type=int)
    analyse = subparsers.add_parser("analyse")
    analyse.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plan = read_json(PLAN)["explicit"]
    jobs = trials_for(plan)
    evidence = args.evidence.resolve()
    if args.command == "simulate":
        if args.jobs < 1 or (args.size is not None and args.size not in plan["sizes"]):
            parser.error("Use a positive job count and a registered size")
        scratch = args.scratch.resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        evidence.mkdir(parents=True, exist_ok=True)
        selected = [job for job in jobs if args.size is None or job.n == args.size]
        run_phase(PHASE, {PHASE: selected}, evidence, scratch, args.jobs, registration_path=PLAN)
    else:
        audit(jobs, plan, evidence, args.out)


if __name__ == "__main__":
    main()
