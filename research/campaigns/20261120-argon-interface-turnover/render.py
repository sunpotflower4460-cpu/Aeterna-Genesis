"""Draw the archived density, boundary track, and confirmed identity exchanges."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from analyze import load_trajectory, separate
from tools.study_record import load_plan, read_object

COLORS = {"bath": "#aa5029", "isolated": "#176f88"}
LABELS = {"bath": "Bath kept", "isolated": "Isolated after split"}


def centred_density(points, length, protocol):
    size = round(length)
    dx = length / size
    indices = ((2 * points.astype(np.int32) + 1) * size) // 131072
    ids = np.ravel_multi_index(indices.T, (size,) * 3)
    density = np.bincount(ids, minlength=size**3).reshape((size,) * 3) / dx**3
    smooth = ndimage.gaussian_filter(density, protocol["smooth_sigma"] / dx, mode="wrap")
    component = separate(smooth, protocol["minimum_component_volume"], dx, 0.35, 2)[0]
    if component.any():
        center = []
        coords = np.argwhere(component)
        for axis in range(3):
            circle = np.exp(2j * np.pi * coords[:, axis] / size)
            phase = np.angle(circle.mean()) % (2 * np.pi)
            center.append(round(size * phase / (2 * np.pi)) % size)
        shift = tuple(size // 2 - p for p in center)
        smooth = np.roll(smooth, shift, axis=(0, 1, 2))
    return smooth[:, :, size // 2]


def figure(plan_path, evidence, analysis, group):
    plan = load_plan(plan_path)
    p = plan["protocol"]
    record = read_object(evidence / "record.json")
    result = read_object(analysis / "results.json")
    with gzip.open(analysis / "measurements.json.gz", "rt") as compressed:
        history = json.load(compressed)
    names = {k: f"{group}-{k}" for k in COLORS}
    cubes = {k: load_trajectory(evidence, name, record["cases"][name][-1]) for k, name in names.items()}
    length = plan["cases"][names["bath"]]["length"]
    tau_ps = result["physical_scales"]["tau_ps"]
    sigma_nm = 1e9 * plan["material"]["sigma_m"]
    wanted = [(0, "bath", "Initial uniform arrangement"),
              (p["quench"], "bath", "Before cooling"),
              (100, "bath", "During cooling"),
              (p["fork"], "bath", "Common state"),
              (p["end"], "bath", "Bath kept"), (p["end"], "isolated", "Bath removed")]
    slices = []
    for t, mode, title in wanted:
        coords, ledger = cubes[mode]
        i = np.flatnonzero(ledger[:, 1] == t).item()
        slices.append((centred_density(coords[i], length, p), t, title))
    ceiling = max(float(image.max()) for image, _, _ in slices)
    fig = plt.figure(figsize=(12, 9), layout="constrained")
    grid = fig.add_gridspec(3, 6, height_ratios=(1.15, 1.15, 1.05))
    axes = []
    extent = length * sigma_nm / 2
    for i, (image, t, title) in enumerate(slices):
        ax = fig.add_subplot(grid[i // 3, 2 * (i % 3):2 * (i % 3) + 2])
        axes.append(ax)
        artist = ax.imshow(image.T, origin="lower", extent=(-extent, extent, -extent, extent),
                           cmap="viridis", vmin=0, vmax=ceiling, interpolation="nearest")
        if image.min() < 0.35 < image.max():
            ax.contour(image.T, levels=[0.35], colors=["white"], alpha=0.6, origin="lower",
                       extent=(-extent, extent, -extent, extent), linewidths=0.7)
        ax.set_title(f"{t * tau_ps:,.0f} ps  |  {title}", loc="left", fontsize=10)
        ax.set_xlabel("x, centred (nm)")
        ax.set_ylabel("y, centred (nm)")
    fig.colorbar(artist, ax=axes, shrink=0.94, label="Smoothed number density (σ⁻³)")

    volume_ax, exchange_ax = fig.add_subplot(grid[2, :3]), fig.add_subplot(grid[2, 3:])
    showed_exchange = False
    for mode, name in names.items():
        frame = history[name]["main"]
        status = result["cases"][name]["main"]
        times = np.array([x["t"] for x in frame["frames"]])
        values = np.array([x["component_volume"] if x["bounded"] else np.nan for x in frame["frames"]])
        before = times <= p["fork"]
        after = ~before
        if mode == "bath":
            volume_ax.plot(times[before] * tau_ps, values[before] * sigma_nm**3, color="#6f7b83")
        if status["track_through"] is not None:
            showed_exchange = True
            retained = (times >= p["fork"]) & (times <= status["track_through"])
            volume_ax.plot(times[retained] * tau_ps, values[retained] * sigma_nm**3, label=LABELS[mode],
                           color=COLORS[mode], lw=2)
            unlinked = after & ~retained
            if np.any(unlinked):
                volume_ax.plot(times[unlinked] * tau_ps, values[unlinked] * sigma_nm**3, color=COLORS[mode],
                               lw=1.1, alpha=0.5, linestyle=":")
            subclock = times[retained]
            for direction, line in (("vapor_to_liquid", "-"), ("liquid_to_vapor", "--")):
                event_t = sorted(x["to_t"] for x in frame["events"]
                                 if x["moves_between_cores"] and x["direction"] == direction)
                totals = np.searchsorted(event_t, subclock, side="right")
                exchange_ax.step(subclock * tau_ps, totals, where="post", color=COLORS[mode],
                                 linestyle=line, linewidth=1.8)
        else:
            volume_ax.plot(times[after] * tau_ps, values[after] * sigma_nm**3, color=COLORS[mode],
                           lw=1.1, alpha=0.55, linestyle=":", label=LABELS[mode])
    volume_ax.set_title("Volume of the largest bounded liquid region", loc="left")
    volume_ax.set_ylabel("Volume (nm³)")
    volume_ax.set_xlim(0, p["end"] * tau_ps)
    volume_ax.axvline(p["fork"] * tau_ps, color="#8b949b", lw=1, linestyle="--")
    if volume_ax.get_legend_handles_labels()[0]:
        volume_ax.legend(frameon=False, fontsize=8)
    exchange_ax.set_title("Same-atom transfers between bulk phases", loc="left")
    exchange_ax.set_ylabel("Cumulative confirmed transfers")
    exchange_ax.set_xlim(p["fork"] * tau_ps, p["end"] * tau_ps)
    if showed_exchange:
        exchange_ax.plot([], [], color="#475569", label="Into liquid")
        exchange_ax.plot([], [], color="#475569", linestyle="--", label="Into vapor")
        exchange_ax.legend(frameon=False, fontsize=8)
    else:
        exchange_ax.text(0.5, 0.54, "No bounded component at the split",
                         transform=exchange_ax.transAxes, ha="center", color="#475569")
        exchange_ax.set_yticks([])
    for ax in (volume_ax, exchange_ax):
        ax.set_xlabel("Time since start (ps)")
        ax.grid(axis="y", alpha=0.24)
    seed = plan["cases"][names["bath"]]["seed"]
    fig.suptitle(f"Argon-scale 3D fluid  |  {length * sigma_nm:.2f} nm cube, seed {seed}",
                 fontweight="bold", fontsize=15)
    fig.savefig(analysis / "droplet-exchange.png", dpi=145)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--group", required=True)
    args = parser.parse_args()
    figure(args.plan, args.evidence, args.analysis, args.group)


if __name__ == "__main__":
    main()
