"""Read archived positions, rederive the numerical and published comparisons, and optionally plot."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tools.study_record import check_record, load_plan, read_object


def analyze(evidence, output, figure=False):
    plan_path = HERE / "PLAN.json"
    record_path = evidence / "record.json"
    check_record(plan_path, record_path)
    attempts = read_object(record_path)["cases"]
    plan = load_plan(plan_path)
    p = plan["protocol"]
    temps = p["fit_temperatures_C"]
    fit_d = [plan["cases"][f"water-{t}"]["reference_D"] * p["reference_unit_m2_s"] for t in temps]
    # Independent two-equation fit for ln D = intercept + slope/T.
    fit_matrix = np.column_stack((np.ones(len(temps)), 1 / (273.15 + np.array(temps))))
    intercept, slope = np.linalg.solve(fit_matrix, np.log(fit_d))
    times = np.arange(p["intervals"] + 1) * p["interval_s"]
    per_seed, summary = [], []
    for name, case in plan["cases"].items():
        t_c = case["temperature_C"]
        predicted = 0.0 if t_c is None else float(np.exp(intercept + slope / (273.15 + t_c)))
        trial, = attempts[name]  # This published reference used one attempt per condition.
        if trial["status"] != "completed" or f"{name}.npz" not in trial.get("artifacts", {}):
            raise ValueError(f"{name}: no registered displacement file for this condition")
        with np.load(evidence / f"{name}.npz", allow_pickle=False) as archive:
            xyz = archive["displacement_steps"]
        expected_shape = (len(p["seeds"]), len(times), p["tracers"], 3)
        if xyz.shape != expected_shape or not np.issubdtype(xyz.dtype, np.integer) or np.any(xyz[:, 0]):
            raise ValueError(f"{name}: invalid positions or nonzero displacement at time zero")
        if t_c is None and np.any(xyz):
            raise ValueError("the zero-rate control moved")
        msd = (xyz.astype(float) ** 2).sum(axis=-1).mean(axis=-1) * p["spacing_m"] ** 2
        for seed, series in zip(p["seeds"], msd):
            per_seed.extend({"case": name, "seed": seed, "time_s": t, "msd_m2": value,
                             "analytic_msd_m2": 6 * predicted * t} for t, value in zip(times, series))
        estimate = msd[:, -1].mean() / (6 * times[-1])
        reference = case.get("reference_D", 0.0) * p["reference_unit_m2_s"]
        n = p["tracers"] * len(p["seeds"])
        sampling_se = np.sqrt((2 * predicted ** 2 / 3 + p["spacing_m"] ** 2 * predicted / (6 * times[-1])) / n)
        summary.append({"case": name, "temperature_C": t_c,
                        "role": "static" if t_c is None else "fit" if t_c in temps else "comparison",
                        "D_reference_m2_s": reference if t_c is not None else None, "D_model_m2_s": predicted,
                        "D_sampled_m2_s": estimate, "MC_standard_error_m2_s": sampling_se,
                        "model_minus_reference_pct": 100 * (predicted / reference - 1) if reference else None})
    output.mkdir(parents=True, exist_ok=True)
    for filename, rows in (("per-seed.csv", per_seed), ("temperatures.csv", summary)):
        with (output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    if figure:
        draw(evidence, output, p, summary)


def draw(evidence, output, protocol, summary):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.colors import LogNorm

    with np.load(evidence / "water-25.npz", allow_pickle=False) as archive:
        xyz = archive["displacement_steps"][0] * (protocol["spacing_m"] * 1e6)
    width = int(np.ceil(np.abs(xyz[..., :2]).max()))
    edges = np.arange(-width - 0.5, width + 1.5)
    fig = plt.figure(figsize=(9.5, 7), layout="constrained")
    grid = fig.add_gridspec(2, 4, height_ratios=[1.1, 1], width_ratios=[1, 1, 1, 0.055])
    for i, frame in enumerate((0, 1, protocol["intervals"])):
        ax = fig.add_subplot(grid[0, i])
        counts, _, _ = np.histogram2d(xyz[frame, :, 0], xyz[frame, :, 1], bins=(edges, edges))
        mesh = ax.pcolormesh(edges, edges, np.ma.masked_equal(counts.T, 0), cmap="viridis",
                             norm=LogNorm(vmin=1, vmax=protocol["tracers"]))
        ax.set(aspect="equal", title=f"{frame * protocol['interval_s'] * 1000:g} ms",
               xlabel="x displacement (µm)", ylabel="y displacement (µm)" if i == 0 else "")
    bar = fig.colorbar(mesh, cax=fig.add_subplot(grid[0, 3]))
    bar.set_label("Tracers per projected bin")
    ax = fig.add_subplot(grid[1, :3])
    ax.axhline(0, color="0.65", linewidth=1)
    for role, marker, color, label in (("fit", "s", "#aa5125", "Used in fit"),
                                       ("comparison", "o", "#20598a", "Outside fit, already published")):
        group = [r for r in summary if r["role"] == role]
        ax.scatter([r["temperature_C"] for r in group], [r["model_minus_reference_pct"] for r in group],
                   marker=marker, color=color, s=50, label=label)
    ax.set(xlabel="Temperature (°C)", ylabel="Model minus reference (%)",
           title="Temperature law checked against Mills (1973), Table III")
    ax.legend(frameon=False, loc="best")
    fig.suptitle(f"3D tracer displacements projected onto x–y at 25 °C   |   seed {protocol['seeds'][0]}")
    fig.savefig(output / "transport-reference.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--figure", action="store_true", help="also render the measured positions (matplotlib)")
    args = parser.parse_args()
    analyze(args.evidence, args.out, args.figure)
