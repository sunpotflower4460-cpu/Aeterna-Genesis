"""Render figure panels from validated measurements and actual 3D snapshots."""
from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import uniform_filter

from simulate import HERE, read_json, sha256

SIZE_STYLES = {32: ("#23667b", "o"), 48: ("#a34a2c", "s"), 56: ("#59743b", "^")}
DENSITY_NAMES = ("dilute", "intermediate", "dense")


def clean(axis):
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#e2ecef", linewidth=0.8)


def save(figure, output, filename):
    figure.savefig(output / filename, dpi=160, facecolor="white")
    plt.close(figure)


def snapshots(results, evidence, output):
    baseline = {row["recipe"]["N"]: row for row in results["archives"]
                if row["recipe"]["case"]["id"] == "uniform_minus" and row["recipe"]["seed"] == 4111}
    fig, axes = plt.subplots(3, 3, figsize=(8.5, 8.0), layout="constrained")
    for row, (n, record) in zip(axes, sorted(baseline.items()), strict=True):
        archive = evidence / record["archive"]
        if sha256(archive) != record["archive_sha256"]:
            raise ValueError("Snapshot archive digest differs")
        with zipfile.ZipFile(archive) as bundle:
            for col, (axis, time) in enumerate(zip(row, (0, 1200, 2400), strict=True)):
                cells = np.frombuffer(bundle.read(f"state-{time // 10}-cells.bin"), dtype=np.uint8)
                cells = cells.reshape((n,)*3, order="F")
                density = uniform_filter(((cells == 1) | (cells == 2)).astype(float), size=4, mode="wrap")
                im = axis.imshow(density[:, :, n // 2].T, origin="lower", extent=(0, n, 0, n),
                                 cmap="viridis", vmin=0, vmax=1, interpolation="nearest")
                if n == min(baseline):
                    axis.set_title(f"Time {time}")
                axis.set_xticks([0, n // 2, n])
                axis.set_yticks([0, n // 2, n])
                if col == 0:
                    axis.set_ylabel(f"{n}³ box\ny (sites)")
                else:
                    axis.set_yticklabels([])
    fig.supxlabel("x (sites) · midplane of the 3D box · seed 4111", fontsize=9)
    fig.colorbar(im, ax=axes, label="Material fraction in a 4³ neighborhood", shrink=0.88)
    save(fig, output, "volume-snapshots.png")


def growth_plot(data, output):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), layout="constrained")
    fields = ("spectral_length", "half_correlation", "first_shell_fraction")
    titles = ("Spectral length", "Half-correlation distance", "Power in the first shell")
    for n, (color, marker) in SIZE_STYLES.items():
        rows = [row for row in data["extent"] if row["N"] == n]
        t = [row["end"] for row in rows]
        for axis, field in zip(axes, fields, strict=True):
            by_seed = np.asarray([row["measurements"][field]["by_seed"] for row in rows], dtype=float)
            axis.plot(t, by_seed, color=color, linewidth=0.6, alpha=0.23)
            y = [row["measurements"][field]["mean"] for row in rows]
            axis.plot(t, y, color=color, marker=marker, markersize=4, label=f"{n}³ · 3 seeds")
    axes[-1].axhline(0.5, linestyle=":", color="#64757b", linewidth=1)
    for axis, title in zip(axes, titles, strict=True):
        axis.set_title(title)
        axis.set_xlabel("End of averaging window")
        clean(axis)
    axes[0].set_ylabel("Length (sites)")
    axes[1].set_ylabel("Distance (sites)")
    axes[2].set_ylabel("Fraction of total power")
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, output, "length-and-age.png")


def factorial_plot(data, output):
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.6), layout="constrained")
    clock_rows = data["clock_comparisons"]
    fields = ("spectral_length", "B_fraction", "work_rate")
    for axis, field, ylabel in zip(axes, fields, ("Spectral length (sites)", "Fraction in state B",
                                              "Chemical work per molecule and time"), strict=True):
        for supply, color, marker in ((1, "#23667b", "o"), (4, "#a34a2c", "s")):
            ys = [[row["arms"][f"r{reaction}_k{supply}"][field] for row in data["supply_comparisons"]]
                  for reaction in (1, 4)]
            xs = [1, 4]
            if supply == 1:
                xs = [0.25, *xs]
                ys = [[row["driven"][field] for row in clock_rows if row["case"] == "clock_0.25"], *ys]
            axis.plot(xs, np.asarray(ys, dtype=float), color=color, linewidth=0.7, alpha=0.24)
            axis.plot(xs, [mean(y) for y in ys], color=color, marker=marker, markersize=5, label=f"Supply ×{supply}")
        axis.set(xscale="log", xticks=[0.25, 1, 4], xticklabels=["¼", "1", "4"],
                 xlabel="Multiplier of both reaction paths", ylabel=ylabel)
        axis.minorticks_off()
        clean(axis)
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, output, "reaction-and-replenishment.png")


def locality_plot(event_table, old, current, output):
    records = event_table["records"]
    fig, (group, density) = plt.subplots(1, 2, figsize=(11.2, 4.1), layout="constrained")
    histograms = []
    for row in records:
        events = np.asarray(row["window"]["accepted_counts_by_density"])
        net = events[3] - events[2]
        histograms.append(net / net.sum())
        density.step(np.arange(65)/64, histograms[-1], where="mid", linewidth=1, color="#23667b", alpha=0.26)
    density.step(np.arange(65)/64, np.mean(histograms, axis=0), where="mid", color="#23667b", linewidth=1.7)
    for threshold in (0.3, 0.7):
        density.axvline(threshold, linestyle=":", color="#64757b", linewidth=0.9)
    density.set(xlabel="Local fraction of material at reaction site",
                ylabel="Fraction of net fuel-linked events per bin", title="Every accepted event · archived replays")
    exact = [mean(r["window"]["bins"][name]["fraction_of_net_linked"] for r in records) for name in DENSITY_NAMES]
    archives = {(r["recipe"]["N"], r["recipe"]["seed"]): r for r in old["archives"]
                if r["recipe"]["case"]["id"] == "uniform_minus"}
    references = [archives[r["N"], r["seed"]]["windows"]["1200"]["density_bins"] for r in records]
    fresh = [r["windows"]["2400"]["density_bins"] for r in current["archives"]
             if r["recipe"]["N"] == 56 and r["recipe"]["case"]["id"] == "uniform_minus"]

    def work_share(cases, name):
        return mean(group[name]["linked_work_per_box_site"]
                    / sum(group[key]["linked_work_per_box_site"] for key in DENSITY_NAMES) for group in cases)

    values = (
        (exact, "Accepted events, replay", "#23667b"),
        ([work_share(references, key) for key in DENSITY_NAMES], "Snapshot rates, same histories", "#a34a2c"),
        ([work_share(fresh, key) for key in DENSITY_NAMES], "Snapshot rates, fresh 56³", "#59743b"),
    )
    x = np.arange(3)
    for (y, name, color), offset in zip(values, (-0.24, 0, 0.24), strict=True):
        group.bar(x + offset, y, width=0.22, color=color, label=name)
    group.set(xticks=x, xticklabels=["Dilute", "Intermediate", "Dense"],
              ylabel="Share of net fuel-linked conversion", title="Where fuel conversion occurs")
    group.legend(frameon=False, fontsize=8)
    for ax in (group, density):
        clean(ax)
    save(fig, output, "where-reactions-occur.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--figures", type=Path, required=True)
    args = parser.parse_args()
    data = read_json(HERE / "measurements/results.json")
    old = read_json(HERE / "previous-measurements/results.json")
    events = read_json(HERE / "event-measurements/results.json")
    args.figures.mkdir(parents=True, exist_ok=True)
    snapshots(data, args.evidence, args.figures)
    growth_plot(data, args.figures)
    factorial_plot(data, args.figures)
    locality_plot(events, old, data, args.figures)


if __name__ == "__main__":
    main()
