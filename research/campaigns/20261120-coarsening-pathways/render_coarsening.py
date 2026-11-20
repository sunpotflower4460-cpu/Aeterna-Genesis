"""Render scientific figures from the sealed output, using fixed figure selection."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from coarsening_runs import HERE, PLAN, PREVIOUS, read_json
from coarsening_summary import read_gzip
from pathways import one_to_one
from survey import read_snapshots
from track_domains import region_frame

SIZE_COLORS = {32: "#7890a2", 48: "#2b8492", 56: "#31598e", 64: "#813c7a"}
INK = "#1b2938"
GRID = "#e4eaef"
ORANGE = "#b44c24"
TEAL = "#207b87"
PURPLE = "#714397"


def configure():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
                         "axes.labelcolor": INK, "axes.titlesize": 13, "axes.titleweight": "bold",
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#a0afba", "xtick.color": INK, "ytick.color": INK,
                         "figure.dpi": 145, "savefig.facecolor": "white"})


def age_figure(result, output):
    panels = [
        ("Spectral scale", "Lattice spacings", lambda w: w["spectral_length"]),
        ("Half-correlation distance", "Lattice spacings", lambda w: w["half_correlation"]),
        ("Resolved dense regions", "Regions per box", lambda w: w["regions"]["0.5"]["count"]),
        ("Largest region’s share", "Share of dense material", lambda w: w["regions"]["0.5"]["largest_material_share"]),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(10.8, 7.1), sharex=True, layout="constrained")
    table = result["active_scale_windows"]
    widths = sorted({row["N"] for row in table})
    for axis, (name, unit, field) in zip(axes.flat, panels, strict=True):
        for n in widths:
            points = [row for row in table if row["N"] == n]
            ages = [row["end"] for row in points]
            values = [field(row) for row in points]
            for trajectory in zip(*(x["by_seed"] for x in values), strict=True):
                axis.plot(ages, trajectory, alpha=0.18, linewidth=1, color=SIZE_COLORS[n])
            axis.plot(ages, [x["mean"] for x in values], "o-", markersize=4.5, color=SIZE_COLORS[n],
                      label=f"{n}³")
        axis.set_title(name, loc="left")
        axis.set_ylabel(unit)
        axis.grid(axis="y", color=GRID)
        axis.axvline(2400, linewidth=0.9, color="#687785", linestyle=":")
    axes[0, 0].legend(title="Box size", frameon=False, ncols=2)
    for axis in axes[-1]:
        axis.set_xlabel("End time of 360-unit average")
    axes[1, 1].set_ylim(0, 1.06)
    figure.suptitle("Age and physical box size", fontsize=19, fontweight="bold")
    figure.savefig(output / "age-and-box-size.png")
    plt.close(figure)


def budget_figure(result, output):
    fields = [
        ("many-to-one", "Many to one", PURPLE),
        ("one-to-many", "One to many", "#358477"),
        ("many-to-many", "Many to many", "#856483"),
        ("unmatched_appearance", "Unmatched appearance", "#6ea7ae"),
        ("unmatched_loss", "Unmatched loss", ORANGE),
    ]
    figure, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), sharey=True)
    figure.subplots_adjust(left=.14, right=.97, top=.76, bottom=.23, wspace=.18)
    for axis, cadence in zip(axes, (50, 100), strict=True):
        subset = [r for r in result["region_budget_panels"] if r["case"] == "uniform_minus"
                  and r["threshold"] == "0.5" and r["cadence"] == cadence]
        selected = {row["N"]: row for row in sorted(subset, key=lambda r: r["durations"])}
        panels = [selected[n] for n in sorted(selected)]
        y = np.arange(len(panels))
        positive = np.zeros(len(y), dtype=int)
        negative = positive.copy()
        for key, _, color in fields:
            values = np.array([row["net_number_budget"][key] for row in panels])
            axis.barh(y, values, left=np.where(values > 0, positive, negative), height=.57, color=color)
            positive += np.maximum(values, 0)
            negative += np.minimum(values, 0)
        net = [row["last_count"] - row["first_count"] for row in panels]
        axis.scatter(net, y, marker="D", color=INK, edgecolor="white", linewidth=.7, s=37, zorder=5)
        axis.axvline(0, color=INK, alpha=.45)
        axis.set_yticks(y, [f'{row["N"]}³  {row["first_count"]} → {row["last_count"]}' for row in panels])
        axis.set_title(f"{cadence}-time-unit sampling")
        axis.set_xlabel("Contributions to region-count change")
        axis.grid(axis="x", color=GRID)
    axes[0].invert_yaxis()
    legend = [Line2D([], [], marker="s", linestyle="none", markersize=8, color=color, label=name)
              for _, name, color in fields]
    legend.append(Line2D([], [], marker="D", linestyle="none", markersize=6, color=INK, label="Net change"))
    figure.legend(handles=legend, loc="lower center", bbox_to_anchor=(.54, .015), frameon=False, ncols=3)
    figure.suptitle("Where resolved dense regions were lost or gained", fontsize=18, fontweight="bold")
    figure.text(.55, .84, "Three runs per box size · material density above 0.5 · from time 1200", ha="center")
    figure.savefig(output / "region-count-budget.png")
    plt.close(figure)


def mobility_figure(result, output):
    rows = [row for row in result["mobility_contrasts"] if row["window"][1] == 1800]
    if not rows:
        return
    figure, axes = plt.subplots(1, 3, figsize=(10.9, 4.25), layout="constrained")
    fields = [("spectral_length", "Spectral scale", "Difference (%)"),
              ("half_correlation", "Half-correlation distance", "Difference (%)"),
              ("B_fraction", "Material in state B", "Difference (points)")]
    for axis, (key, title, unit) in zip(axes, fields, strict=True):
        for j, (case, color) in enumerate((("slow_I", ORANGE), ("slow_B", PURPLE))):
            group = [row for row in rows if row["case"] == case]
            values = [100 * row["delta"][key] / (row["reference"][key] if key != "B_fraction" else 1)
                      for row in group]
            axis.scatter(j + np.linspace(-.14, .14, len(values)), values, color=color, s=42, zorder=3)
            axis.plot([j - .23, j + .23], [np.mean(values)]*2, color=color, linewidth=2.5)
        axis.axhline(0, color="#687785", linewidth=1)
        axis.grid(axis="y", color=GRID)
        axis.set_xticks([0, 1], ["Slower I", "Slower B"])
        axis.set_ylabel(unit)
        axis.set_title(title, loc="left")
        axis.set_xlim(-.43, 1.43)
    figure.suptitle("Changing the mobility of one material state", fontsize=18, fontweight="bold")
    figure.supxlabel("Paired against the original rates · 48³ · t = 1440–1800")
    figure.savefig(output / "mobility-response.png")
    plt.close(figure)


def route_geometry(example, result, transitions, evidence, old_evidence):
    key = example["archive"]
    row = next(r for r in result["archives"] + result["reused_archives"] if r["archive"] == key)
    root = old_evidence if row["phase"] == "extent" else evidence
    times = [example[k] for k in ("anchor", "start", "dilute_time", "recipient_time")]
    settings = read_json(PLAN)["domains"]
    with ZipFile(root / key) as archive:
        snapshots = list(read_snapshots(archive, row["recipe"], [{"time": time} for time in times]))
    threshold = float(example["threshold"])
    regions = [region_frame(s.density_count, s.positions, threshold * 64, settings["minimum_region_sites"])
               for s in snapshots]
    before = example["labels_before_loss"]
    donor = [before[0], before[-1], None, None]
    paths = transitions[key][example["threshold"]][str(example["cadence"])]
    successors = {edge["start"]: one_to_one(edge) for edge in paths}
    recipients = set(r["initial_label"] for r in example["recipients"])
    recipients_by_time = {}
    for time in range(times[0], times[-1] + 1, example["cadence"]):
        recipients_by_time[time] = recipients
        if time < times[-1]:
            recipients = {successors[time][identifier] for identifier in recipients}
    diagrams = []
    for time, frame, parent in zip(times, regions, donor, strict=True):
        receiver = np.isin(frame.labels, sorted(recipients_by_time[time]))
        source = frame.labels == parent if parent is not None else np.zeros_like(receiver)
        context = (frame.labels > 0) & ~(receiver | source)
        diagrams.append((source, receiver, context))
    cohort = regions[0].by_molecule == donor[0]
    dilute = snapshots[2].density_count.ravel(order="F")[snapshots[2].positions] < 64 * settings["separated_loss"]["dilute_below"]
    entered = np.isin(regions[-1].by_molecule, sorted(recipients))
    witnessed = cohort & dilute & entered
    if int(witnessed.sum()) != example["witnessed_same_id_routes"]:
        raise ValueError("The illustrated particle identities do not match the reported count")
    size = row["recipe"]["N"]
    coords = [np.column_stack(np.unravel_index(s.positions[witnessed], (size,)*3, order="F")) for s in snapshots]
    return size, row["recipe"]["seed"], times, diagrams, coords


def boundary(mask):
    interior = mask.copy()
    for axis in range(3):
        interior &= np.roll(mask, 1, axis=axis) & np.roll(mask, -1, axis=axis)
    return np.argwhere(mask & ~interior)


def transport_figure(result, raw_transitions, evidence, old_evidence, output):
    example = result["witnessed_transport_example"]
    if example is None:
        return
    size, seed, times, diagrams, trace = route_geometry(example, result, raw_transitions, evidence, old_evidence)
    composite = sum((s | r).astype(int) for s, r, _ in diagrams)
    cut = np.array([np.argmin(composite.sum(axis=tuple(k for k in range(3) if k != a))) for a in range(3)])

    figure = plt.figure(figsize=(10.8, 8.8))
    figure.subplots_adjust(left=.02, right=.98, top=.84, bottom=.12, wspace=.06, hspace=.06)
    titles = ["Marked in a dense region", "The source region shrinks",
              "The same particles are dilute", "The same particles enter other regions"]
    for i, (t, (source, receivers, context), points, title) in enumerate(zip(times, diagrams, trace, titles, strict=True), 1):
        axis = figure.add_subplot(2, 2, i, projection="3d", box_aspect=(1, 1, 1))
        for mask, color, alpha in ((context, "#b0b8bd", .12), (receivers, TEAL, .22), (source, "#c89b50", .42)):
            xyz = (boundary(mask)[::2] - cut) % size
            if xyz.size:
                axis.scatter(*xyz.T, c=color, s=2.7, alpha=alpha, depthshade=False, linewidths=0)
        marked = (points - cut) % size
        axis.scatter(*marked.T, c=ORANGE, s=8.5, depthshade=False, alpha=.84, linewidths=0)
        axis.set(xlim=(0, size), ylim=(0, size), zlim=(0, size))
        axis.view_init(elev=23, azim=-55)
        for set_ticks in (axis.set_xticks, axis.set_yticks, axis.set_zticks):
            set_ticks([0, size // 2, size])
        axis.tick_params(labelsize=8, pad=0)
        axis.set_title(f"t = {t}  ·  {title}", fontsize=11, y=.98)
        axis.set_proj_type("ortho")
    labels = [(ORANGE, f"{len(trace[0])} identical particle IDs"),
              ("#c89b50", "Shrinking source region"), (TEAL, "Persistent recipient regions")]
    handles = [Line2D([], [], marker="o", linestyle="none", color=color, label=label, markersize=7)
               for color, label in labels]
    figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .053), frameon=False, ncols=3)
    figure.suptitle("Material transfer between separate regions", y=.965, fontsize=20, fontweight="bold")
    figure.text(.5, .909, f"Selected {size}³ history · seed {seed} · periodic coordinates held fixed",
                ha="center", fontsize=11)
    figure.text(.5, .041, f'Surfaces show measured density above {example["threshold"]}. The panels are sampled states.',
                ha="center", color="#536474", fontsize=9.5)
    figure.savefig(output / "tracked-material-transfer.png")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    parser.add_argument("--previous", type=Path, default=PREVIOUS / "evidence")
    parser.add_argument("--figures", type=Path, required=True)
    args = parser.parse_args()
    configure()
    result = read_json(args.measurements / "results.json")
    args.figures.mkdir(parents=True, exist_ok=True)
    age_figure(result, args.figures)
    budget_figure(result, args.figures)
    mobility_figure(result, args.figures)
    transport_figure(result, read_gzip(args.measurements / "transitions.json.gz"),
                     args.evidence, args.previous, args.figures)


if __name__ == "__main__":
    main()
