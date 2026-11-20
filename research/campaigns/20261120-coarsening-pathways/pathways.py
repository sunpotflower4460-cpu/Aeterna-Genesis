"""Conserved-particle and region-number budgets on observed components."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from coarsening_runs import PREVIOUS  # Load the inherited measurement modules before using them.
from track_domains import RegionFrame, classify_transition


KINDS = ("one-to-one", "many-to-one", "one-to-many", "many-to-many")
BUDGET_KEYS = (*KINDS, "unmatched_appearance", "unmatched_loss")


@dataclass(frozen=True)
class Snapshot:
    time: int
    positions: np.ndarray
    density_count: np.ndarray


def number_budget(transition):
    """Signed contributions to the observed change in the number of regions."""
    terms = dict.fromkeys(BUDGET_KEYS, 0)
    for event in transition["events"]:
        terms[event["kind"]] += len(event["targets"]) - len(event["sources"])
    terms["unmatched_appearance"] = transition["unlinked_after"]
    terms["unmatched_loss"] = -transition["unlinked_before"]
    if sum(terms.values()) != transition["after_regions"] - transition["before_regions"]:
        raise ValueError("Region census fails to close")
    return terms


def endpoints(inside_at_start, inside_at_end):
    """Infer the exact signed crossings of a fixed mask from conservation."""
    incoming = int(np.count_nonzero(inside_at_end & ~inside_at_start))
    outgoing = int(np.count_nonzero(inside_at_start & ~inside_at_end))
    start, end = int(inside_at_start.sum()), int(inside_at_end.sum())
    if end - start != incoming - outgoing:
        raise ValueError("Fixed-mask material budget fails to close")
    return {"at_start": start, "at_end": end, "net": end - start,
            "unique_outside_to_inside": incoming, "unique_inside_to_outside": outgoing}


def material_budget(a: RegionFrame, b: RegionFrame, old_sites, new_sites, source, target):
    """Partition inventory change symmetrically over the start and end masks."""
    old_at_start = a.by_molecule == source
    new_at_end = b.by_molecule == target
    old_at_end = a.labels.ravel(order="F")[new_sites] == source
    new_at_start = b.labels.ravel(order="F")[old_sites] == target
    fixed_a = endpoints(old_at_start, old_at_end)
    fixed_b = endpoints(new_at_start, new_at_end)
    delta = fixed_b["at_end"] - fixed_a["at_start"]
    hop_twice = fixed_a["net"] + fixed_b["net"]
    boundary_twice = ((fixed_b["at_start"] - fixed_a["at_start"])
                      + (fixed_b["at_end"] - fixed_a["at_end"]))
    if hop_twice + boundary_twice != 2 * delta:
        raise ValueError("Symmetric material budget fails to close")
    return {"source": source, "target": target, "inventory_delta": delta,
            "fixed_start_mask": fixed_a, "fixed_end_mask": fixed_b,
            "twice_symmetric_hop_flux": hop_twice,
            "twice_symmetric_boundary_term": boundary_twice}


def region_gap_at_least(labels, region, gap):
    """Check periodic Manhattan distance to another resolved region."""
    reached = labels == region
    other = (labels > 0) & ~reached
    for _ in range(1, gap):
        expanded = reached.copy()
        for axis in range(3):
            expanded |= np.roll(reached, 1, axis=axis)
            expanded |= np.roll(reached, -1, axis=axis)
        if np.any(expanded & other):
            return False
        reached = expanded
    return True


def one_to_one(transition):
    return {event["sources"][0]["label"]: event["targets"][0]["label"]
            for event in transition["events"] if event["kind"] == "one-to-one"}


def lost_labels(before, transition, minimum):
    linked = {link["source"] for link in transition["links"]}
    return sorted(set(int(i) for i in np.flatnonzero(before.volumes >= minimum)) - linked)


def shrinking_path(frames, links, index, label, settings):
    """Identify a series with decreasing population and volume before loss."""
    steps = settings["prior_one_to_one_steps"]
    if index < steps:
        return {"status": "left_censored"}
    labels = [label]
    for edge in links[index - steps:index][::-1]:
        parent = next((source for source, target in edge.items() if target == labels[-1]), None)
        if parent is None:
            return {"status": "no_unambiguous_ancestors"}
        labels.append(parent)
    labels.reverse()
    cut = frames[index - steps:index + 1]
    sites = [int(frame.volumes[k]) for frame, k in zip(cut, labels, strict=True)]
    material = [int(frame.populations[k]) for frame, k in zip(cut, labels, strict=True)]
    decline = settings["minimum_relative_decline"]
    trace = {"labels_before_loss": labels, "sites_before_loss": sites,
             "material_before_loss": material}

    def decreasing(values):
        return all(x > y for x, y in zip(values, values[1:])) and values[-1] <= (1 - decline) * values[0]

    if not decreasing(sites) or not decreasing(material):
        return {**trace, "status": "decline_criterion_unmet"}
    gaps = [region_gap_at_least(frame.labels, k, settings["minimum_periodic_manhattan_gap"])
            for frame, k in zip(cut, labels, strict=True)]
    if not all(gaps):
        return {**trace, "gap_checks": gaps, "status": "separation_criterion_unmet"}
    return {**trace, "gap_checks": gaps, "status": "strict_separated_loss"}


def persistent_recipients(frames, links, anchor, last, initial_donor, minimum):
    """Trace distinct regions that already existed when the cohort was marked."""
    current = {int(k): int(k) for k in np.flatnonzero(frames[anchor].volumes >= minimum)
               if k != initial_donor}
    for follow in links[anchor:last]:
        current = {first: follow[k] for first, k in current.items() if k in follow}
    return current


def classify_loss(snapshots, frames, links, index, label, plan):
    settings = plan["separated_loss"]
    s0, s1 = snapshots[index:index + 2]
    result = {"start": s0.time, "end": s1.time, "source": label,
              **shrinking_path(frames, links, index, label, settings)}
    if result["status"] != "strict_separated_loss":
        return result

    anchor = index - settings["prior_one_to_one_steps"]
    initial_donor = result["labels_before_loss"][0]
    cohort = frames[anchor].by_molecule == initial_donor
    below = s1.density_count.ravel(order="F")[s1.positions] < 64 * settings["dilute_below"]
    cohort_below = cohort & below
    result.update(anchor=snapshots[anchor].time, dilute_time=s1.time,
                  initial_cohort=int(cohort.sum()),
                  cohort_outside_resolved_at_loss=int(np.count_nonzero(cohort & (frames[index + 1].by_molecule == 0))),
                  cohort_dilute_at_loss=int(cohort_below.sum()), all_dilute_at_loss=int(below.sum()))
    last = index + 1 + settings["later_steps_at_cadence"]
    if last >= len(frames):
        return {**result, "transport_censored": True}

    recipients = persistent_recipients(frames, links, anchor, last, initial_donor,
                                       plan["minimum_region_sites"])
    picked = frames[last].by_molecule
    destinations = [
        {"initial_label": k, "last_label": v,
         "cohort_count": int(np.count_nonzero(cohort & (picked == v))),
         "same_dilute_cohort_count": int(np.count_nonzero(cohort_below & (picked == v))),
         "all_dilute_count": int(np.count_nonzero(below & (picked == v)))}
        for k, v in sorted(recipients.items())
    ]
    routes = sum(row["same_dilute_cohort_count"] for row in destinations)
    background = sum(row["all_dilute_count"] for row in destinations)
    dilute_pool = result["all_dilute_at_loss"]
    return {**result, "transport_censored": False, "recipient_time": snapshots[last].time,
            "recipients": destinations, "witnessed_same_id_routes": routes,
            "expected_routes_uniform_dilute_cohort": (result["cohort_dilute_at_loss"] * background / dilute_pool
                                                      if dilute_pool else 0.0)}


def paired_extremes(terms, before):
    if len(terms) < 2:
        return None
    ordered = sorted(terms, key=lambda row: before.populations[row["source"]])
    small, large = ordered[0], ordered[-1]
    small_n, large_n = (int(before.populations[row["source"]]) for row in (small, large))
    if (small_n == before.populations[ordered[1]["source"]]
            or large_n == before.populations[ordered[-2]["source"]]):
        return None
    return {"material_small": small_n, "material_large": large_n,
            "delta_small": small["inventory_delta"], "delta_large": large["inventory_delta"],
            "twice_hop_small": small["twice_symmetric_hop_flux"],
            "twice_hop_large": large["twice_symmetric_hop_flux"]}


def observe_transitions(snapshots, frames, plan):
    """Classify full adjacent observations and keep censored and unmatched cases."""
    rows = []
    for a, b, sa, sb in zip(frames[:-1], frames[1:], snapshots[:-1], snapshots[1:], strict=True):
        transition = classify_transition(a, b, plan)
        links = one_to_one(transition)
        transfers = [material_budget(a, b, sa.positions, sb.positions, source, target)
                     for source, target in links.items()]
        absent = lost_labels(a, transition, plan["minimum_region_sites"])
        if len(absent) != transition["unlinked_before"]:
            raise ValueError("Unmatched label count disagrees with the component census")
        rows.append({"start": sa.time, "end": sb.time, **transition,
                     "number_budget": number_budget(transition), "material_budgets": transfers,
                     "lost_labels": absent, "paired_extremes": paired_extremes(transfers, a)})
    if not rows:
        raise ValueError("No complete tracking intervals")

    graph = [one_to_one(row) for row in rows]
    for index, row in enumerate(rows):
        row["losses"] = [classify_loss(snapshots, frames, graph, index, label, plan)
                         for label in row["lost_labels"]]
    return rows


def summarize_transitions(rows):
    duration = sum(row["end"] - row["start"] for row in rows)
    exposure = sum(row["before_regions"] * (row["end"] - row["start"]) for row in rows)
    sums = {key: sum(row["number_budget"][key] for row in rows) for key in BUDGET_KEYS}
    first, last = rows[0]["before_regions"], rows[-1]["after_regions"]
    if sum(sums.values()) != last - first:
        raise ValueError("Region census fails to close over the entire history")

    budgets = [budget for row in rows for budget in row["material_budgets"]]
    losses = [loss for row in rows for loss in row["losses"]]
    counts = {key: sum(event["kind"] == key for row in rows for event in row["events"]) for key in KINDS}
    ranked = [row["paired_extremes"] for row in rows if row["paired_extremes"] is not None]
    return {"first_count": first, "last_count": last, "time_exposure": duration,
            "region_time_exposure": exposure, "intervals": len(rows), "number_budget": sums,
            "region_losses_per_1000_time": (first - last) * 1000 / duration,
            "event_counts": counts, "loss_statuses": dict(Counter(loss["status"] for loss in losses)),
            "strict_losses_with_witnessed_routes": sum(loss.get("witnessed_same_id_routes", 0) > 0 for loss in losses),
            "strict_losses_transport_censored": sum(loss.get("transport_censored", False) for loss in losses),
            "witnessed_same_id_routes": sum(loss.get("witnessed_same_id_routes", 0) for loss in losses),
            "material_budgets": {
                "one_to_one_transitions": len(budgets),
                "abs_inventory_change": sum(abs(row["inventory_delta"]) for row in budgets),
                "twice_abs_hop_flux": sum(abs(row["twice_symmetric_hop_flux"]) for row in budgets),
                "twice_abs_boundary_term": sum(abs(row["twice_symmetric_boundary_term"]) for row in budgets),
                "matching_flux_sign_nonzero_change": sum(row["inventory_delta"] * row["twice_symmetric_hop_flux"] > 0
                                                          for row in budgets),
                "opposing_flux_sign_nonzero_change": sum(row["inventory_delta"] * row["twice_symmetric_hop_flux"] < 0
                                                          for row in budgets),
            },
            "paired_extremes": {"intervals": len(ranked),
                                "larger_gains_more": sum(r["delta_large"] > r["delta_small"] for r in ranked),
                                "larger_hop_flux_more": sum(r["twice_hop_large"] > r["twice_hop_small"] for r in ranked)}}
