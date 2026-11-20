"""Render the fixed early-wake witness from the measured density and trajectory."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261120-vortex-drive-stop"))
from cylinder import material
from tools.study_record import load_plan

COLORS = {"continue": "#3b6cc4", "hold": "#a94d24", "release": "#13796c"}
LABELS = {"continue": "Keep moving", "hold": "Brake and hold", "release": "Brake and remove"}


def render(evidence, analysis):
    reference = load_plan(HERE.parent / "20261120-vortex-drive-stop" / "PLAN.json")["reference"]
    scales = material(reference)
    ms = 1e3 * scales["tau_s"]
    um = 1e6 * scales["ell_m"]
    with gzip.open(analysis / "tracking.json.gz", "rt") as stream:
        all_tracks = json.load(stream)
    snapshot_labels = ["Start", "Common state", "Obstacle at rest",
                         "Potential removed", "Free evolution", "Final observation"]
    names = {arm: "base-92301-" + arm for arm in COLORS}
    fig = plt.figure(figsize=(12, 8), layout="constrained")
    grid = fig.add_gridspec(3, 6, height_ratios=[0.84, 0.84, 1.35])
    axs = [fig.add_subplot(grid[i // 3, 2 * (i % 3):2 * (i % 3) + 2]) for i in range(6)]
    with np.load(evidence / (names["release"] + ".npz")) as source:
        times = source["cut_times"]
        cuts = source["cuts"]
        dy = source["dx"].item() * um
        ymax, zmax = cuts.shape[1:]
    extent = (-dy / 2, (zmax - 0.5) * dy, -(ymax / 2 + 0.5) * dy, (ymax / 2 - 0.5) * dy)
    for ax, cut, time, label in zip(axs, cuts, times, snapshot_labels):
        im = ax.imshow(cut, origin="lower", extent=extent, aspect="auto", interpolation="nearest",
                       cmap="viridis", vmin=0, vmax=cuts.max())
        ax.set_title(f"{time * ms:.0f} ms  |  {label}", loc="left", fontsize=10)
        ax.set_xlabel("Axial position (µm)")
        ax.set_ylabel("y (µm)")
    fig.colorbar(im, ax=axs, shrink=0.9, label="Density / starting density")
    radius_ax = fig.add_subplot(grid[2, :3])
    work_ax = fig.add_subplot(grid[2, 3:])
    for arm, name in names.items():
        with np.load(evidence / (name + ".npz")) as source:
            ledger = source["ledger"]
        after = ledger[:, 0] >= 58
        t, _, _, _, work, *_ = ledger[after].T
        work_ax.plot(t * ms, work - work[0], color=COLORS[arm], label=LABELS[arm], linewidth=2)
        tracks = all_tracks[name]["main"]["tracks"]
        cohort = [tr for tr in tracks if tr[0]["t"] <= 54 and tr[-1]["t"] >= 58]
        for track in cohort:
            pts = [p for p in track if p["t"] >= 58]
            radius_ax.plot([p["t"] * ms for p in pts], [p["radius"] * um for p in pts],
                           color=COLORS[arm], marker=".", markersize=3.3, linewidth=1.35, alpha=0.8)
        if arm == "release":
            late = [tr for tr in tracks if tr[0]["t"] > 82 and len(tr) >= 3]
            for index, track in enumerate(late):
                radius_ax.plot([p["t"] * ms for p in track], [p["radius"] * um for p in track],
                               color=COLORS[arm], linestyle="--", linewidth=1.9,
                               label="First detected after removal" if index == 0 else None)
            if late:
                radius_ax.legend(frameon=False, loc="best", fontsize=8)
    for ax in (radius_ax, work_ax):
        ax.axvspan(58 * ms, 70 * ms, color="#c4cbd4", alpha=0.4, linewidth=0)
        ax.axvspan(70 * ms, 82 * ms, color="#b3ded8", alpha=0.4, linewidth=0)
        ax.set_xlabel("Time since start (ms)")
        ax.set_xlim(58 * ms, 160 * ms)
        ax.grid(axis="y", alpha=0.23)
    radius_ax.set_title("Loops tracked across the intervention", loc="left")
    radius_ax.set_ylabel("RMS radius (µm)")
    work_ax.set_title("Mechanical work since the split", loc="left")
    work_ax.set_ylabel("Work / (µ n₀ ℓ³)")
    work_ax.legend(frameon=False, loc="best")
    fig.suptitle("Early wake | density slices for the obstacle-removal history", fontsize=15, fontweight="bold")
    fig.savefig(analysis / "early-stop.png", dpi=145)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    args = parser.parse_args()
    render(args.evidence, args.analysis)


if __name__ == "__main__":
    raise SystemExit(main())
