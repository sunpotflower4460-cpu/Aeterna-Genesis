"""Render audited physical snapshots and stationary results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import uniform_filter

HERE = Path(__file__).resolve().parent
ACTIVE = "#146581"
CONTROL = "#a35427"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean(axis):
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#dfebee", linewidth=0.8)
    axis.set_axisbelow(True)


def save(fig, output, name):
    fig.savefig(output / name, dpi=170, facecolor="white")
    plt.close(fig)


def stationary_figure(output):
    rows = read(HERE / "stationary-results.json")["rows"]
    saddle = read(HERE / "saddle-results.json")["rows"]
    fig, (shift, cycles) = plt.subplots(1, 2, figsize=(10.7, 4.2), layout="constrained")
    for label, model, color in (("Implicit reservoir", rows[0]["model"], ACTIVE),
                                ("Fast-exchange fuel", saddle[0]["model"], CONTROL)):
        for diffusivity, marker, style in ((1.0, "o", "-"), (100.0, "s", "--")):
            series = sorted((row for row in rows if row["case"] == "both_driven"
                             and row["model"] == model and row["D_I"] == diffusivity),
                            key=lambda row: row["n"])
            shift.plot([row["n"] for row in series],
                       [100 * row["relative_contact_shift"] for row in series],
                       color=color, marker=marker, linestyle=style,
                       label=f"{label}, I diffusion {diffusivity:g}")
    shift.axhline(0, linewidth=0.8, color="#67747d")
    shift.set(xlabel="Periodic box edge (sites)", ylabel="Relative contact change given both B (%)",
              xticks=[4, 6, 8], title="Exact two-particle stationary contact")
    shift.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(0.012, 0.17))

    example = sorted((row for row in saddle if row["D_I"] == 1 and row["n"] == 8),
                     key=lambda row: row["saddle"])
    theta = [row["saddle"] for row in example]
    cycles.axhline(0, linewidth=0.8, color="#67747d")
    cycles.axvline(next(row["saddle"] for row in example if row["analytic_point"]),
                   linewidth=1.0, linestyle=":", color="#67747d")
    cycles.plot(theta, [row["cycle_log_ratio"] for row in example], "o-", color=ACTIVE,
                label="Neighbor in state B")
    cycles.plot(theta, [row["cycle_log_ratio_I_neighbor"] for row in example], "s--", color=CONTROL,
                label="Neighbor in state I")
    cycles.set(xlabel="Driven barrier sensitivity", ylabel="Log of forward/reverse cycle rate product",
               title="One cycle closes while the other persists")
    cycles.legend(frameon=False, fontsize=8)
    for axis in (shift, cycles):
        clean(axis)
    save(fig, output, "stationary-contact.png")


def finite_pair_figure(output):
    reports = [read(HERE / name)["comparisons"]
               for name in ("finite-pair-results.json", "slow-b-results.json")]
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(9.2, 4.1), layout="constrained")
    for axis, report in zip(axes, reports, strict=True):
        rows = [row for row in report["windows"] if row["window"] == [1200, 6000]]
        x = [row["exchange_per_site"] for row in rows]
        y = [100 * row["driven_minus_reversible"] for row in rows]
        lower, upper = np.asarray([row["paired_seed_bootstrap_interval"] for row in rows]).T * 100
        exact = report["fast_limit"]
        offset = 100 * (exact["conditional_contact"] - exact["canonical_conditional_contact"])
        axis.axhline(0, linewidth=0.8, color="#67747d")
        axis.axhline(offset, linewidth=1.1, color=CONTROL, linestyle="--", label="Exact fast-exchange limit")
        axis.vlines(x, lower, upper, color=ACTIVE, linewidth=1.1,
                    label="95% paired seed bootstrap interval")
        axis.scatter(x, y, color=ACTIVE, zorder=3)
        axis.set(xscale="log", xticks=x, xticklabels=[f"{value:g}" for value in x],
                 xlabel="Uniform fuel exchange per site",
                 title=f"B diffusion {report['D_B']:g} · I diffusion {report['D_I']:g}")
        axis.minorticks_off()
        clean(axis)
    axes[0].set_ylabel("Driven minus reversible contact (percentage points)")
    axes[1].legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle("Both-B contact at finite exchange in the original simulator", fontsize=14)
    save(fig, output, "finite-pair-comparisons.png")


def field_figure(results, evidence, output):
    n, seed = 40, 2017
    rows = {row["recipe"]["case"]["id"]: row for row in results["archives"]
            if row["recipe"]["N"] == n and row["recipe"]["seed"] == seed}
    fig, axes = plt.subplots(2, 3, figsize=(9.0, 6.5), layout="constrained")
    fig.suptitle("Material density on the same slice of a 40³ periodic box", fontsize=15)
    for row, case, label in zip(axes, ("uniform_minus", "reversible_df0.2"),
                                ("Driven", "Reversible control"), strict=True):
        archive = rows[case]
        path = evidence / archive["archive"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != archive["archive_sha256"]:
            raise ValueError(f"Archived snapshot failed SHA-256: {path}")
        with zipfile.ZipFile(path) as bundle:
            for column, (axis, time) in enumerate(zip(row, (0, 600, 1200), strict=True)):
                cells = np.frombuffer(bundle.read(f"state-{time // 10}-cells.bin"), np.uint8)
                cells = cells.reshape((n, n, n), order="F")
                density = uniform_filter(((cells == 1) | (cells == 2)).astype(float), size=4, mode="wrap")
                image = axis.imshow(density[:, :, n // 2].T, origin="lower", vmin=0, vmax=1,
                                    cmap="viridis", interpolation="nearest", extent=(0, n, 0, n))
                axis.set_title(f"Time {time}")
                axis.set_xticks([0, 20, 40])
                axis.set_yticks([0, 20, 40])
                if column == 0:
                    axis.set_ylabel(label + "\ny (sites)")
                else:
                    axis.set_yticklabels([])
    fig.supxlabel("x (sites)  ·  z = 20  ·  seed 2017", fontsize=9)
    fig.colorbar(image, ax=axes, shrink=0.83, aspect=32, location="right",
                 label="Local fraction of I or B particles in 4³ sites")
    save(fig, output, "field-snapshots.png")


def difference_figure(results, output):
    pairs = results["comparisons"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), layout="constrained")
    for n, color, marker in ((32, ACTIVE, "o"), (40, CONTROL, "s")):
        seeds = sorted({row["seed"] for row in pairs if row["N"] == n})
        for index, seed in enumerate(seeds):
            series = [row for row in pairs if row["N"] == n and row["seed"] == seed]
            times = [row["window"]["end"] for row in series]
            for axis, measure in zip(axes, ("variance_4", "gross_turnover", "wavelength_sites"), strict=True):
                values = []
                for row in series:
                    comparison = row["measures"][measure]
                    if not comparison["bracket_available"]:
                        values.append(np.nan)
                        continue
                    baseline = (row["driven_gross_turnover"] if measure == "gross_turnover"
                                else comparison["interpolated_variance"])
                    values.append(100 * comparison["signed_residual"] / baseline)
                axis.plot(times, values, color=color, marker=marker, markersize=4,
                          linestyle="-", linewidth=0.9, alpha=0.7,
                          label=f"{n}³ box" if index == 0 else None)
    for bound in (-10, 10):
        axes[1].axhline(bound, color="#67747d", linewidth=0.9, linestyle=":")
    for axis, label in zip(axes, ("Material density variance", "Gross reaction turnover",
                                  "Density wavelength (sites)"), strict=True):
        axis.axhline(0, color="#67747d", linewidth=0.8)
        axis.set(xlabel="End of averaging window", xticks=[600, 900, 1200],
                 ylabel="Driven vs composition-matched control (%)", title=label)
        clean(axis)
    axes[1].set_ylabel("Driven minus control (% of driven turnover)")
    axes[0].legend(frameon=False, loc="best")
    save(fig, output, "finite-time-comparisons.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--finite-pair", action="store_true")
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    stationary_figure(args.figures)
    if args.finite_pair:
        finite_pair_figure(args.figures)
    if args.evidence:
        results = read(HERE / "measurements" / "results.json")
        field_figure(results, args.evidence, args.figures)
        difference_figure(results, args.figures)


if __name__ == "__main__":
    main()
