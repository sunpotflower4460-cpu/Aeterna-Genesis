"""Plot the registered views of the archived binary-fluid experiment."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import numpy as np

from readouts import binary
from render import atoms_in_slice
from study import PLAN
from tools.study_record import load_plan, read_object
from verify import recorded_component

BACKGROUND = "#111b24"
PANEL = "#1b2935"
FOREGROUND = "#ecf4f7"
SECONDARY = "#aec2cd"
FINITE = "#50bda8"
MISSED = "#f7bd64"
WINDING = "#a99bea"
SPARSE = "#334753"
AR = "#71bfec"
KR = "#f5a767"


def draw(evidence, analysis, output):
    plan = load_plan(PLAN)
    p = plan["protocol"]
    record = read_object(evidence / "record.json")
    with gzip.open(analysis / "readouts.json.gz", "rt") as stream:
        results = json.load(stream)

    def trajectory(name):
        return binary.load_binary(evidence, name, record["cases"][name][-1])

    small = "small-94201-isolated"
    large = "large-94201-isolated"
    histories = {name: trajectory(name) for name in (small, large)}
    plt.rcParams.update({
        "font.size": 10, "text.color": FOREGROUND, "axes.facecolor": PANEL, "axes.titlecolor": FOREGROUND,
        "axes.edgecolor": "#495c69", "axes.labelcolor": SECONDARY, "xtick.color": SECONDARY,
        "ytick.color": SECONDARY, "savefig.facecolor": BACKGROUND,
    })
    fig = plt.figure(figsize=(13.2, 9.3), facecolor=BACKGROUND)
    grid = fig.add_gridspec(3, 5, height_ratios=(1, 1.3, .45),
                           left=.075, right=.96, bottom=.115, top=.84, wspace=.28, hspace=.41)
    fig.text(.075, .951, "Finite domains and periodic winding", fontsize=23, weight="bold")
    fig.text(.075, .908, "Argon–krypton molecular dynamics  ·  seed 94201  ·  two box sizes at the same density",
             color=SECONDARY, fontsize=11.7)
    labels = ((small, 0, "Start"), (small, p["fork"], "Small box"), (small, p["end"], "Small box"),
              (large, p["fork"], "Large box"), (large, p["end"], "Large box"))
    for i, (name, t, title) in enumerate(labels):
        coordinates, ledger, species, _initial = histories[name]
        length = plan["cases"][name]["length"]
        points, types = atoms_in_slice(coordinates[np.flatnonzero(ledger[:, 1] == t).item()], species, length, t)
        ax = fig.add_subplot(grid[0, i])
        for element, colour in enumerate((AR, KR)):
            x, y = points[types == element, :2].T
            ax.scatter(x, y, s=11, color=colour, alpha=.86, linewidths=0)
        limit = length / 2
        ax.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect="equal", xticks=[], yticks=[])
        ax.set_title(f"{title}  |  {t} τ", fontsize=11, pad=7)

    examples = (
        ("Finite with a full projection", lambda row: row["finite"] and not row["vacant"], MISSED),
        ("Component with a winding path", lambda row: bool(row["winding_axes"]), WINDING),
    )
    for j, (title, criterion, colour) in enumerate(examples):
        ax = fig.add_subplot(grid[1, 2*j:2*j + 2], projection="3d", facecolor=BACKGROUND)
        ax.set_title(title, fontsize=11.5, pad=3)
        selected = next(((name, row) for name in plan["cases"] if name in results
                         for row in results[name]["main"]["frames"] if row["t"] >= p["fork"] and criterion(row)),
                        None)
        if selected is None:
            ax.text2D(.5, .5, "No such snapshot", transform=ax.transAxes, ha="center", color=SECONDARY)
            ax.set_axis_off()
            continue
        name, row = selected
        positions, ledger, _species, _initial = histories[name] if name in histories else trajectory(name)
        i = np.flatnonzero(ledger[:, 1] == row["t"]).item()
        mask = recorded_component(positions[i], plan["cases"][name]["length"], p, .35)
        ax.voxels(mask, facecolors=colour, edgecolor="#344651", linewidth=.12)
        ax.set(xlim=(0, mask.shape[0]), ylim=(0, mask.shape[1]), zlim=(0, mask.shape[2]),
               xticklabels=[], yticklabels=[], zticklabels=[], xlabel="x", ylabel="y", zlabel="z")
        ax.view_init(elev=25, azim=-52)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.set_facecolor((.10, .16, .22, .30))
            axis.pane.set_edgecolor("#8295a3")
        ax.text2D(.5, -.09, f"{name} at {row['t']:g} τ", transform=ax.transAxes, ha="center",
                  fontsize=9, color=SECONDARY)

    notes = fig.add_subplot(grid[1, 4])
    notes.set_axis_off()
    notes.text(.0, .94, "● Argon", fontsize=10, color=AR)
    notes.text(.0, .83, "● Krypton", fontsize=10, color=KR)
    notes.text(.0, .65, "Top row\n2.4 σ slices,\ncentered on a density\npeak after t=0.", color=SECONDARY,
               fontsize=9, linespacing=1.25, va="top")
    notes.text(.0, .28, "Middle row\nLargest 3D component.\nOpposite box faces\nare joined.", color=SECONDARY,
               fontsize=9, linespacing=1.25, va="top")

    timeline = fig.add_subplot(grid[2, :])
    cmap = ListedColormap((SPARSE, FINITE, MISSED, WINDING))
    for i, name in enumerate((small, large)):
        rows = results[name]["main"]["frames"]
        tags = [3 if r["winding_axes"] else 1 if r["vacant"] else 2 if r["finite"] else 0 for r in rows]
        timeline.imshow([tags], aspect="auto", cmap=cmap, vmin=0, vmax=3, interpolation="nearest",
                        extent=(-p["sample"]/2, p["end"] + p["sample"]/2, i-.36, i+.36))
    timeline.axvline(p["fork"], color="white", linestyle="--", lw=.9)
    timeline.axvline(p["comparison_start"], color="white", linestyle=":", lw=.9)
    timeline.set_title("Geometric classification per frame", loc="left", fontsize=10.5, pad=7)
    timeline.set(xlim=(0, p["end"]), ylim=(1.5, -.5), yticks=(0, 1), yticklabels=("Small", "Large"),
                 xlabel="Time (τ)   ·   dashed: bath removed   ·   dotted: composition window starts")
    fig.legend(handles=[Patch(facecolor=c, label=label) for c, label in (
        (SPARSE, "Below volume threshold"), (FINITE, "Both tests accept"),
        (MISSED, "Finite, old test misses"), (WINDING, "Wraps around box")
    )], loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(.5, .025), labelcolor=FOREGROUND)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    draw(args.evidence, args.analysis, args.out)


if __name__ == "__main__":
    main()
