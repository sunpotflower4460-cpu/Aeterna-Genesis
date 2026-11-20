"""Show recorded atom positions and the actual overlaps of their IDs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np

from analyze import binary
from contact_graph import histories
from study import PLAN
from tools.study_record import load_plan, read_object

BG = "#111c25"
PANEL = "#1b2a36"
WHITE = "#edf3f5"
TEXT = "#b6c9d3"
PALETTE = ["#f5b66b", "#60cfb7", "#a99dec", "#74b8ef"]
UNASSIGNED = "#6c8190"


def panels(ax, q, labels, length, title):
    xyz = (q.astype(float) + .5) * (length / 65536)
    outside = labels < 0
    ax.scatter(*xyz[outside].T, s=2.1, alpha=.14, color=UNASSIGNED, linewidths=0, depthshade=False)
    for rank in np.unique(labels[~outside]):
        ax.scatter(*xyz[labels == rank].T, s=5.5, alpha=.80, color=PALETTE[rank % len(PALETTE)],
                   linewidths=0, depthshade=False)
    ax.view_init(elev=22, azim=-56)
    ax.set(xlim=(0, length), ylim=(0, length), zlim=(0, length),
           xticks=[], yticks=[], zticks=[], box_aspect=(1, 1, 1))
    ax.set_title(title, fontsize=11, pad=1)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor(to_rgba(PANEL, .4))
        axis.pane.set_edgecolor("#536b7a")


def draw(original, replay, analysis, output):
    plan = load_plan(PLAN)
    stored = read_object(analysis / "results.json")
    mapped = read_object(analysis / "grid-contact-map.json")["cases"]
    old = read_object(original / "record.json")["cases"]
    new = read_object(replay / "record.json")["cases"]
    main = plan["contact_schemes"]["main"]

    def read(name):
        folder, ledger = (replay, new) if stored["replay_checks"][name]["verified"] else (original, old)
        return binary.load_binary(folder, name, ledger[name][-1])

    plt.rcParams.update({
        "text.color": WHITE, "axes.titlecolor": WHITE, "font.size": 10,
        "axes.edgecolor": "#536b7a", "savefig.facecolor": BG,
    })
    fig = plt.figure(figsize=(13.2, 10.25), facecolor=BG)
    grid = fig.add_gridspec(4, 4, height_ratios=(.56, 1, 1, 1), width_ratios=(.95, 1.25, 1.25, 1.15),
                           top=.86, bottom=.06, left=.06, right=.955, hspace=.28, wspace=.13)
    fig.text(.06, .95, "Following the same atoms through a tracking loss", fontsize=23, weight="bold")
    fig.text(.06, .914, "3D argon–krypton trajectories  ·  two standard-density seeds  ·  periodic boxes",
             fontsize=12, color=TEXT)

    first = next(iter(plan["targets"]))
    q, _ledger, species, _initial = read(first)
    L = plan["cases"][first]["length"]
    points = (q[0].astype(float) + .5) * (L / 65536)
    slab = np.abs(points[:, 2] - L/2) < 1.2
    ax = fig.add_subplot(grid[0, 0], facecolor=PANEL)
    for data, color in ((species == 0, PALETTE[3]), (species == 1, PALETTE[0])):
        ax.scatter(*points[slab & data, :2].T, s=8, color=color, linewidths=0)
    ax.set(xlim=(0, L), ylim=(0, L), aspect="equal", xticks=[], yticks=[])
    ax.set_title("Uniform start at 0 τ", fontsize=10)
    notes = fig.add_subplot(grid[0, 1:])
    notes.set_axis_off()
    notes.text(0, .82, "Around each tracking loss", fontsize=13, weight="bold")
    notes.text(0, .56, "Colors follow the atoms in each earlier contact group into the later frame.", color=TEXT)
    notes.text(0, .34, "Opposite faces of each box are connected.", color=TEXT)
    notes.text(0, .13, "The tables count shared IDs. Margins show the total atoms in each contact group.", color=TEXT)
    names = ["94201  ·  bath continued", "94201  ·  isolated", "94207  ·  isolated"]
    for row, ((name, loss), title) in enumerate(zip(plan["targets"].items(), names), start=1):
        data, ledger, _species, _initial = read(name)
        length = plan["cases"][name]["length"]
        pair = stored["cases"][name]["main"]["native"]["loss_pair"]
        times = (pair["from_tau"], loss)
        chosen = data[[np.flatnonzero(ledger[:, 1] == t).item() for t in times]]
        before, after = histories(chosen, length, {"main": main}, plan["lineage"]["minimum_component_atoms"])["main"]

        label = fig.add_subplot(grid[row, 0])
        label.set_axis_off()
        label.text(0, .71, title, fontsize=12, weight="bold")
        label.text(0, .49, f"Grid overlap {pair['voxel_jaccard']:.3f}", color=TEXT)
        label.text(0, .31, f"Stopped at {loss:g} τ", color=TEXT)
        join = mapped[name]["merger_contacts"]
        if join:
            label.text(0, .09, f"Groups joined at {join['accepted_at_tau']:g} τ", color=PALETTE[1], fontsize=11)
        for j, t in enumerate(times):
            ax = fig.add_subplot(grid[row, j+1], projection="3d", facecolor=BG)
            labels = before.labels if j == 0 else np.where(after.labels >= 0, before.labels, -1)
            panels(ax, chosen[j], labels, length, f"{'Earlier' if j == 0 else 'Later'}  |  {t:g} τ")
        ax = fig.add_subplot(grid[row, 3])
        ax.set_axis_off()
        ax.set_title("Atoms in both groups", fontsize=10.5, pad=7)
        matrix = np.array(pair["shared_ids"])
        if not matrix.size:
            ax.text(.5, .51, "No contact groups to compare", ha="center", color=TEXT)
            continue
        before_sizes = pair["before"]["contact_sizes"]
        after_sizes = pair["after"]["contact_sizes"]
        table = ax.table(
            cellText=[[str(n) if n else "·" for n in line] for line in matrix],
            rowLabels=[str(n) for n in before_sizes], colLabels=[str(n) for n in after_sizes],
            cellLoc="center", rowLoc="center", loc="center", bbox=[.16, .19, .84, .63],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9.5)
        for (i, j), cell in table.get_celld().items():
            cell.set_edgecolor("#455967")
            cell.set_linewidth(.65)
            cell.set_facecolor(PANEL)
            cell.get_text().set_color(TEXT if i == 0 else WHITE)
            if i > 0 and j == -1:
                cell.get_text().set_color(PALETTE[(i-1) % len(PALETTE)])
            if i > 0 and j >= 0 and matrix[i-1,j]:
                cell.set_facecolor(to_rgba(PALETTE[(i-1) % len(PALETTE)], .26))
    fig.savefig(output, dpi=154)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    draw(args.original, args.replay, args.analysis, args.out)


if __name__ == "__main__":
    main()
