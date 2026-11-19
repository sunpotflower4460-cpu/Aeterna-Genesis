"""Render measured fields and the registered control comparisons."""
from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from scipy.ndimage import uniform_filter

from run import REGISTRATION, read_json

CASES = {
    "closed_minus": ("Closed box", "#535e6d"),
    "fed_minus_fast": ("Plane, fast fuel", "#176b99"),
    "fed_minus_slow": ("Plane, slow fuel", "#b66400"),
    "uniform_minus": ("Uniform, fast fuel", "#13836d"),
    "fed_minus_no_passive": ("Plane, driven path only", "#a14885"),
    "uniform_minus_no_passive": ("Uniform, driven path only", "#aa4232"),
}
CONTRASTS = (
    ("fed_minus_fast-closed_minus", "Plane fast − closed"),
    ("fed_minus_fast-fed_minus_slow", "Plane fast − slow"),
    ("uniform_minus-fed_minus_fast", "Uniform − plane fast"),
    ("fed_minus_fast-fed_minus_no_passive", "Plane both paths − driven only"),
    ("uniform_minus-uniform_minus_no_passive", "Uniform both paths − driven only"),
)


def field_slices(evidence: Path, out: Path):
    seed = read_json(REGISTRATION)["phases"]["fuel_holdout"]["seeds"][0]
    n = 32
    cases = ("closed_minus", "fed_minus_fast", "fed_minus_slow", "uniform_minus")
    times = (0, 300, 600)
    figure, axes = plt.subplots(len(cases), len(times), figsize=(8.5, 8.15), layout="constrained")
    for row, case in enumerate(cases):
        archive = evidence / "fuel_holdout" / f"{case}-d3-n{n}-T600-s{seed}.zip"
        with zipfile.ZipFile(archive) as bundle:
            for column, time in enumerate(times):
                file = f"state-{time // 10}-cells.bin"
                cells = np.frombuffer(bundle.read(file), dtype=np.uint8).reshape((n,) * 3, order="F")
                macro = ((cells == 1) | (cells == 2)).astype(float)
                density = uniform_filter(macro, size=4, mode="wrap")
                ax = axes[row, column]
                image = ax.imshow(density[:, :, n // 2].T, origin="lower", cmap="cividis",
                                  vmin=0, vmax=1, interpolation="nearest")
                if case.startswith("fed_"):
                    ax.axvline(0, color="#fff", linewidth=1, linestyle="--", alpha=.8)
                ax.set_xticks([0, 15, 31] if row == len(cases) - 1 else [])
                ax.set_yticks([0, 15, 31] if column == 0 else [])
                if row == 0:
                    ax.set_title(f"t = {time}", fontweight="bold")
                if column == 0:
                    ax.set_ylabel(CASES[case][0], color=CASES[case][1], fontweight="bold")
    figure.colorbar(image, ax=axes, label="Macromolecule occupancy, averaged over 4³ sites", shrink=.82)
    figure.suptitle(f"Material density from an unstructured start\n32³ sites, seed {seed}, fixed z = {n // 2} slice",
                    fontweight="bold")
    figure.supxlabel("x (dashed line marks the plane reservoir at x = 0)")
    figure.savefig(out / "field-evolution.png", dpi=170)
    plt.close(figure)


def controls(results, out: Path):
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
    rows = [row for row in results["archives"] if row["phase"] == "fuel_holdout" and "-n32-" in row["archive"]]
    for key, (label, color) in CASES.items():
        windows = [row["windows"]["600"] for row in rows if Path(row["archive"]).name.startswith(key + "-d3-")]
        axes[0, 0].scatter([w["work_rate"] for w in windows], [w["variance_4"] for w in windows],
                           s=27, color=color, alpha=.8, label=label)
        rates = [w["encounter_propensities_per_macro"]["I_to_B"] for w in windows]
        ratios = [r["observed"] / r["same_x_mixed"] for r in rates if r["same_x_mixed"] > 0]
        axes[1, 1].scatter(ratios, [list(CASES).index(key)] * len(ratios), s=24, color=color, alpha=.78)
    axes[0, 0].set_title("Chemical work and material concentration")
    axes[0, 0].set_xlabel("Reservoir work / (macromolecule × time)")
    axes[0, 0].set_ylabel("Late width-4 density variance")
    axes[0, 0].legend(fontsize=8, ncol=2, loc="best")
    axes[1, 1].set_title("W encounters after accounting for x profiles")
    axes[1, 1].axvline(1, color="#6d7783", linewidth=1, linestyle="--")
    axes[1, 1].set_yticks(range(len(CASES)), [label for label, _ in CASES.values()])
    axes[1, 1].invert_yaxis()
    axes[1, 1].set_xlabel("Observed I→B propensity / within-plane mixing expectation")

    ax = axes[0, 1]
    for index, (key, _) in enumerate(CONTRASTS):
        for n, offset, color in ((24, -.09, "#696c80"), (32, .09, "#176b99")):
            comparison = results["fuel_holdout_paired"].get(f"N{n}T600:{key}")
            if comparison is None:
                continue
            values = [row["variance_4"] for row in comparison["differences"]]
            y = index + offset
            ax.scatter(values, [y] * len(values), color=color, s=23, alpha=.65,
                       label=f"N={n}" if index == 0 else None)
            ax.plot(comparison["summary"]["variance_4"]["median"], y, "|", markersize=13,
                    color=color, markeredgewidth=2)
    ax.axvline(0, color="#6d7783", linewidth=1, linestyle="--")
    ax.set_yticks(range(len(CONTRASTS)), [label for _, label in CONTRASTS])
    ax.invert_yaxis()
    ax.set_xlabel("Paired difference in late width-4 variance")
    ax.set_title("Matched fuel controls")
    ax.legend(fontsize=8, loc="best")

    ax = axes[1, 0]
    matches = results["lattice_composition_matches"]
    for mobility, color in ((1, "#b66400"), (100, "#176b99")):
        group = [entry for entry in matches if entry["I_mobility"] == mobility]
        for entry in group:
            x, y = np.array(entry["nulls_B_variance"]).T
            ax.plot(x, y, color=color, alpha=.27, linewidth=1.2)
        values = np.asarray([entry["nulls_B_variance"] for entry in group])
        ax.plot(values[0, :, 0], values[:, :, 1].mean(axis=0), "-o", color=color,
                linewidth=1.6, markersize=4, label=f"Frozen, Dᵢ = {mobility}")
        ax.scatter([entry["active_B"] for entry in group], [entry["active_variance"] for entry in group],
                   marker="D", s=38, color=color, edgecolor="white", linewidth=.4, label=f"Reactive, Dᵢ = {mobility}")
    ax.set_xlabel("Late fraction in bonding conformation")
    ax.set_ylabel("Late width-4 density variance")
    ax.set_title("Composition brackets at the same I mobility")
    ax.legend(fontsize=8, ncol=2)
    figure.suptitle("3D exclusion-fluid controls", fontweight="bold", fontsize=15)
    figure.savefig(out / "control-comparisons.png", dpi=160)
    plt.close(figure)


def grid_map(results, out: Path):
    slots = results["fuel_grid_slots"]
    sources = ("plane", "uniform")
    energies = (1.2, 2.4)
    etas = (1, 10, 100)
    mobilities = (1, 100)
    tables = {}
    for source in sources:
        for df in energies:
            table = np.zeros((len(etas), len(mobilities)))
            for i, eta in enumerate(etas):
                for j, mobility in enumerate(mobilities):
                    values = [r["variance_4"] for r in slots if r["case"]["source"] == source
                              and r["case"]["df"] == df and r["case"]["eta"] == eta
                              and r["case"]["D_F"] == mobility]
                    if len(values) != 3:
                        raise ValueError("Missing grid seed")
                    table[i, j] = np.mean(values)
            tables[source, df] = table
    scale = Normalize(vmin=0, vmax=max(table.max() for table in tables.values()))
    figure, axes = plt.subplots(2, 2, figsize=(8, 7), layout="constrained")
    for i, source in enumerate(sources):
        for j, df in enumerate(energies):
            ax = axes[i, j]
            table = tables[source, df]
            image = ax.imshow(table, cmap="cividis", norm=scale, aspect="auto")
            for row, col in np.ndindex(table.shape):
                color = "white" if scale(table[row, col]) < .54 else "#171721"
                ax.text(col, row, f"{table[row, col]:.4f}", ha="center", va="center", color=color)
            ax.set_title(f"{source.capitalize()} reservoir, df = {df:g}", fontweight="bold")
            ax.set_xticks(range(len(mobilities)), mobilities)
            ax.set_yticks(range(len(etas)), etas)
            if i == 1:
                ax.set_xlabel("Fuel and waste diffusivity")
            if j == 0:
                ax.set_ylabel("Encounter prefactor η")
    figure.colorbar(image, ax=axes, label="Mean late width-4 variance, 3 seeds", shrink=.85)
    figure.suptitle("Reaction and transport conditions across 72 slots", fontweight="bold")
    figure.savefig(out / "transport-grid.png", dpi=160)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    results = read_json(args.results)
    field_slices(args.evidence, args.out)
    controls(results, args.out)
    grid_map(results, args.out)


if __name__ == "__main__":
    main()
