"""Render snapshots and composition readouts from evidence without changing the physics."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
from scipy import ndimage

from measure import PLAN, load_binary
from tools.study_record import load_plan, read_object

AR = "#54b9ef"
KR = "#ffb778"
INK = "#e8edf0"
MUTED = "#aec0ce"
BG = "#131c25"
PANEL = "#1c2935"


def atoms_in_slice(encoded, species, length, elapsed):
    n = round(length)
    points = (encoded.astype(float) + 0.5) * length / 65536
    centre = np.full(3, length / 2)
    if elapsed:
        dx = length / n
        indices = (points / dx).astype(int)
        counts = np.bincount(np.ravel_multi_index(indices.T, (n,) * 3), minlength=n**3).reshape((n,) * 3)
        density = ndimage.gaussian_filter(counts.astype(float), 1 / dx, mode="wrap")
        centre = (np.asarray(np.unravel_index(density.argmax(), density.shape)) + 0.5) * dx
    relative = (points - centre + length / 2) % length - length / 2
    shown = np.abs(relative[:, 2]) <= 1.2
    return relative[shown], species[shown]


def draw(args):
    plan = load_plan(PLAN)
    p = plan["protocol"]
    name = p["illustration_case"]
    attempt = read_object(args.evidence / "record.json")["cases"][name][-1]
    case = plan["cases"][name]
    positions, ledger, species, _ = load_binary(args.evidence, name, attempt)
    result = read_object(args.analysis / "results.json")
    with gzip.open(args.analysis / "measurements.json.gz", "rt") as layers:
        data = json.load(layers)[name]["main"]
    times = ledger[:, 1]

    plt.rcParams.update({"font.size": 10.5, "text.color": INK, "axes.facecolor": PANEL,
                         "axes.labelcolor": MUTED, "axes.edgecolor": "#415465",
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK})
    fig = plt.figure(figsize=(12.3, 8.3), facecolor=BG)
    grid = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1], height_ratios=[1.15, 1],
                           left=.075, right=.965, bottom=.135, top=.825, hspace=.50, wspace=.36)
    fig.text(.075, .95, "Composition and atom exchange at a 3D interface", fontsize=23, weight="bold")
    fig.text(.075, .905, f"Argon and krypton · seed {case['seed']} · {len(species):,} atoms in a periodic cube",
             color=MUTED, fontsize=12)
    fig.text(.765, .905, "● Argon", color=AR, fontsize=12)
    fig.text(.868, .905, "● Krypton", color=KR, fontsize=12)
    titles = ("Start", "Heat bath removed", "End of isolated history")
    for i, (t, title) in enumerate(zip((0, p["fork"], p["end"]), titles)):
        ax = fig.add_subplot(grid[0, i])
        pts, types = atoms_in_slice(positions[np.flatnonzero(times == t).item()], species, case["length"], t)
        for kind, colour in enumerate((AR, KR)):
            x, y = pts[types == kind, :2].T
            ax.scatter(x, y, s=12, c=colour, alpha=.88, linewidths=0)
        radius = case["length"] / 2
        ax.set(xlim=(-radius, radius), ylim=(-radius, radius), aspect="equal", xticks=[], yticks=[])
        ax.set_title(f"{title}  |  {t} τ", fontsize=11, pad=10)

    curve = fig.add_subplot(grid[1, :2])
    rows = data["frames"]
    summary = result["cases"][name]["main"]
    end = summary["track_through_tau"]
    valid = np.array([end is not None and p["fork"] <= r["t"] <= end
                      and min(r["liquid_count"], r["vapor_count"]) >= p["minimum_core_count"] for r in rows])
    curve.axvspan(p["comparison_start"], p["end"], color="#263f50", alpha=.55)
    curve.axvline(p["fork"], color=MUTED, lw=1, ls="--", alpha=.8)
    for phase, label, colour in (("liquid", "Dense core", KR), ("vapor", "Vapor core", AR)):
        ratio = np.full(len(rows), np.nan)
        for i in np.flatnonzero(valid):
            row = rows[i]
            ratio[i] = row[phase + "_kr_count"] / row[phase + "_count"]
        curve.plot(times, ratio, color=colour, linewidth=1.4, label=label)
    curve.set(xlim=(0, p["end"]), ylim=(0, 1), xlabel="Time (τ)", ylabel="Krypton fraction")
    curve.yaxis.set_major_formatter(PercentFormatter(1))
    curve.legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=9)
    curve.grid(axis="y", color="#415465", alpha=.4)

    contrast = fig.add_subplot(grid[1, 2])
    seeds = [c["seed"] for group, c in plan["cases"].items() if group.startswith("binary-") and c["mode"] == "isolated"]
    for group, label, colour, d in (("binary", "Ar–Kr", KR, -.09),
                                    ("equal-interactions", "Equal forces", MUTED, .09)):
        y = []
        for seed in seeds:
            scheme = result["cases"].get(f"{group}-{seed}-isolated", {}).get("main", {})
            y.append(scheme["window_composition"]["delta_kr"] if scheme.get("window_complete") else np.nan)
        contrast.scatter(np.arange(len(seeds)) + d, y, label=label, s=46, color=colour, zorder=3)
    contrast.axhline(0, color="#adbfc9", lw=1)
    contrast.grid(axis="y", color="#415465", alpha=.4)
    contrast.set(xlim=(-.5, len(seeds) - .5), ylim=(-.2, .65), xticks=range(len(seeds)),
                 xticklabels=seeds, xlabel="Seed", ylabel="Dense minus vapor (pp)")
    contrast.yaxis.set_major_formatter(PercentFormatter(1, symbol=""))
    contrast.legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=8)
    counts = summary["transits"]
    if counts:
        phrases = [f"{label} {counts[key]['liquid_to_vapor']['distinct_ids']} out / "
                   f"{counts[key]['vapor_to_liquid']['distinct_ids']} in"
                   for key, label in (("ar", "Ar"), ("kr", "Kr"))]
        fig.text(.075, .063, "Distinct IDs crossing in the selected window · " + "  |  ".join(phrases),
                 color=INK, fontsize=11)
    fig.text(.075, .032, "Top views show a 2.4 σ slice, recentered at a density peak after t=0. "
             "Bottom right plots complete isolated histories only.", color=MUTED, fontsize=9)
    fig.savefig(args.out, dpi=155, facecolor=BG)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    draw(parser.parse_args())


if __name__ == "__main__":
    main()
