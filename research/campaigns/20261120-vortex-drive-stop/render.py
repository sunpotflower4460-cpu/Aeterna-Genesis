"""Plot the declared witness histories and the no-fit rubidium comparison."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = {"continue": "#3b6cc4", "brake": "#a94d24"}
LABELS = {"continue": "Keep moving", "brake": "Brake, then hold"}
DARK = "#17273a"


def plot_intervention(evidence, analysis, results, histories):
    pair = {arm: "base-g0-92101-" + arm for arm in COLORS}
    scale = results["physical_scales"]
    ms = 1e3 * scale["tau_s"]
    um = 1e6 * scale["ell_m"]
    plt.rcParams.update({"text.color": DARK, "axes.labelcolor": DARK, "axes.titlecolor": DARK, "font.size": 10})
    fig = plt.figure(figsize=(12, 9), layout="constrained")
    grid = fig.add_gridspec(4, 2, height_ratios=[0.9, 0.9, 1.15, 1.0])
    snapshots = [(0, "continue", "Start"), (120, "continue", "Common state before braking"),
                 (224, "continue", LABELS["continue"]), (224, "brake", LABELS["brake"])]
    saved = {}
    for arm, name in pair.items():
        with np.load(evidence / (name + ".npz")) as data:
            saved[arm] = {k: data[k] for k in ("cuts", "cut_times", "shape", "dx", "ledger")}
    vmax = max(float(np.max(data["cuts"])) for data in saved.values())
    slices = []
    for i, (instant, arm, label) in enumerate(snapshots):
        ax = fig.add_subplot(grid[i // 2, i % 2])
        slices.append(ax)
        data = saved[arm]
        index = np.flatnonzero(data["cut_times"] == instant).item()
        cut = data["cuts"][index]
        dy = data["dx"] * um
        displayed = ax.imshow(cut, origin="lower", aspect="auto", interpolation="nearest",
                              extent=(-dy / 2, (cut.shape[1] - 0.5) * dy,
                                      -(cut.shape[0] / 2 + 0.5) * dy, (cut.shape[0] / 2 - 0.5) * dy),
                              vmin=0, vmax=vmax, cmap="viridis")
        ax.set_title(f"{label}  |  {instant * ms:.0f} ms", loc="left", fontsize=10)
        ax.set_xlabel("Axial position (µm)")
        ax.set_ylabel("y (µm)")
    fig.colorbar(displayed, ax=slices, orientation="vertical", shrink=0.95, pad=0.02,
                 label="Density / starting density")
    radius_ax, count_ax = (fig.add_subplot(grid[2, i]) for i in range(2))
    work_ax = fig.add_subplot(grid[3, :])
    for arm, name in pair.items():
        columns = saved[arm]["ledger"].T
        ts = columns[0]
        past = ts >= 120
        work_ax.plot(ts[past] * ms, columns[4][past] - columns[4][ts == 120][0],
                     color=COLORS[arm], label=LABELS[arm], linewidth=2)
        time_series = histories[name]["main"]
        branch_tracks = time_series["tracks"]
        cohort = [track for track in branch_tracks if track[0]["t"] <= 116 and track[-1]["t"] >= 120]
        for i, track in enumerate(cohort):
            times = [row["t"] * ms for row in track if row["t"] >= 120]
            radii = [row["radius"] * um for row in track if row["t"] >= 120]
            radius_ax.plot(times, radii, color=COLORS[arm], label=LABELS[arm] if i == 0 else None,
                           alpha=0.74, linewidth=1.9, marker=".", markersize=3)
        arrivals = results["flows"][name]["main"]["later_track_starts"]
        count_ax.step(ts[past] * ms,
                      np.searchsorted(sorted(arrivals), ts[past], side="right"),
                      where="post", color=COLORS[arm], label=LABELS[arm], linewidth=2)
    for ax in (radius_ax, count_ax, work_ax):
        ax.axvspan(120 * ms, 132 * ms, color="#c4cbd4", alpha=0.4, linewidth=0)
        ax.set_xlim(120 * ms, 224 * ms)
        ax.set_xlabel("Time since start (ms)")
        ax.grid(axis="y", alpha=0.23)
    radius_ax.set_title("Loops tracked from before braking", loc="left")
    radius_ax.set_ylabel("RMS radius (µm)")
    count_ax.set_title("New sustained detections after the stop time", loc="left")
    count_ax.set_ylabel("Cumulative detections")
    count_ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    work_ax.set_title("Mechanical work since the split", loc="left")
    work_ax.set_ylabel("Work / (µ n₀ ℓ³)")
    work_ax.legend(loc="best", frameon=False, ncol=2)
    fig.suptitle("Rubidium-87 bulk model | paired 3D histories, no bath", fontsize=15, fontweight="bold")
    fig.savefig(analysis / "intervention.png", dpi=145)
    plt.close(fig)


def plot_calibration(analysis, results):
    records = sorted(results["cylinders"].values(), key=lambda row: row["atoms"])
    x = np.array([row["atoms"] for row in records])
    obs = np.array([row["observed_hz"] for row in records])
    fine = np.array([row["fine"]["hz"] for row in records])
    variants = np.array([[v["hz"] for v in row["geometry_corners_coarse_mesh"]] for row in records])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), layout="constrained")
    a.fill_between(x, variants.min(axis=1), variants.max(axis=1), color="#dbe9fb",
                   label="Geometry variation (±1 µm)")
    a.semilogx(x, fine, "o-", color=COLORS["continue"], label="Cylinder GPE")
    a.errorbar(x, obs, yerr=np.array([row["raster_readout_relative"] for row in records]) * obs,
               fmt="s", color=DARK, mfc="white", label="Garratt et al., Fig. 2")
    a.set_ylabel("Axial oscillation frequency (Hz)")
    a.legend(frameon=False, loc="upper left")
    b.semilogx(x, 100 * (fine / obs - 1), "o", color=COLORS["brake"])
    b.axhline(0, color=DARK, alpha=0.6, linewidth=1)
    b.set_ylabel("Prediction minus observation (%)")
    for ax in (a, b):
        ax.set_xlabel("Number of atoms")
        ax.set_xlim(x.min() * 0.8, x.max() * 1.25)
        ax.grid(axis="y", alpha=0.23)
    fig.suptitle("Hard-wall cylinder | published frequencies compared without fitting", fontsize=13)
    fig.savefig(analysis / "rubidium-calibration.png", dpi=145)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    args = parser.parse_args()
    results = json.loads((args.analysis / "results.json").read_text())
    with gzip.open(args.analysis / "tracking.json.gz", "rt") as stream:
        histories = json.load(stream)
    plot_intervention(args.evidence, args.analysis, results, histories)
    plot_calibration(args.analysis, results)


if __name__ == "__main__":
    main()
