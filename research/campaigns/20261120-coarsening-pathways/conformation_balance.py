"""Close independent B and I balances on the fixed observed component masks."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np

from coarsening_runs import HERE, PLAN, PREVIOUS, read_json, sha256
from audit_transport import HOP_PLAN
from run import json_text
from survey import ledgers, read_snapshots, write_gzip
from track_domains import region_frame

REGISTRATION = HERE / "CONVERSION_REGISTRATION.json"
CIRCULATION_PLAN = HERE / "CIRCULATION_NOTE.json"
FIELDS = ("delta_I", "delta_B", "net_I_hops", "net_B_hops", "net_I_to_B")


def conformation_balance(delta_i, delta_b, in_i, out_i, in_b, out_b):
    net_i, net_b = in_i - out_i, in_b - out_b
    conversion = delta_b - net_b
    if conversion != net_i - delta_i:
        raise ValueError("I and B independently inferred different conversion counts")
    return dict(zip(FIELDS, (delta_i, delta_b, net_i, net_b, conversion), strict=True))


def counts_by_label(mask, lattice, length):
    return [np.bincount(mask[lattice == code], minlength=length) for code in (1, 2)]


def verified_rows(record, traces, previous, plan):
    observed = traces / record["trace"]
    if sha256(observed) != record["trace_sha256"]:
        raise ValueError("Boundary hop trace digest changed")
    path = previous / record["archive"]
    if sha256(path) != record["archive_sha256"]:
        raise ValueError("Physical archive digest changed")
    times = range(plan["first_time"], plan["T"] + 1, plan["cadence"])
    with ZipFile(path) as zipfile:
        recipe = json.loads(zipfile.read("recipe.json"))
        ledger = ledgers(zipfile, recipe)
        snapshots = list(read_snapshots(zipfile, recipe, [{"time": t} for t in times]))
        cells = {t: np.frombuffer(zipfile.read(f"state-{t//10}-cells.bin"), dtype=np.uint8) for t in times}
    minimum = read_json(PLAN)["domains"]["minimum_region_sites"]
    lookup = {}
    for threshold_index, threshold in enumerate(plan["thresholds"]):
        frames = {s.time: region_frame(s.density_count, s.positions, threshold * 64, minimum) for s in snapshots}
        for start, end in zip(times, times[1:]):
            for endpoint, time in enumerate((start, end)):
                mask = frames[time].labels.ravel(order="F")
                maximum = int(mask.max()) + 1
                before_i, before_b = counts_by_label(mask, cells[start], maximum)
                after_i, after_b = counts_by_label(mask, cells[end], maximum)
                delta_i, delta_b = after_i - before_i, after_b - before_b
                for label in range(1, maximum):
                    lookup[start, threshold_index, endpoint, label] = int(delta_i[label]), int(delta_b[label])
    rows = []
    with gzip.open(observed, "rt", newline="") as f:
        for entry in csv.DictReader(f):
            row = {key: int(value) for key, value in entry.items()}
            key = tuple(row[k] for k in ("start", "threshold_index", "endpoint", "label"))
            delta = lookup.pop(key)
            balance = conformation_balance(*delta, row["in_I"], row["out_I"], row["in_B"], row["out_B"])
            rows.append({"start": row["start"], "end": row["end"], "label": row["label"],
                         "threshold": plan["thresholds"][row["threshold_index"]],
                         "endpoint": row["endpoint"], **balance})
    if lookup or len(rows) != record["verified_fixed_region_tallies"]:
        raise ValueError("The conversion budget does not cover the archived hop tallies")
    global_changes = {(start, end): int(ledger["B"][end//10] - ledger["B"][start//10])
                      for start, end in zip(times, times[1:])}
    return rows, global_changes


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["threshold"], row["endpoint"]].append(row)
    result = []
    for (threshold, endpoint), matches in sorted(groups.items()):
        values = {key: [r[key] for r in matches] for key in FIELDS}
        result.append({"threshold": threshold, "endpoint": endpoint, "labels": len(matches),
                       "totals": {k: sum(nums) for k, nums in values.items()},
                       "positive_terms": {k: sum(num > 0 for num in nums) for k, nums in values.items()},
                       "negative_terms": {k: sum(num < 0 for num in nums) for k, nums in values.items()}})
    return result



def circulation(rows, global_changes, settings):
    """Close the signed reaction conversion in the dense union and its complement."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["start"], row["end"], row["threshold"], row["endpoint"]].append(row)
    steps = []
    for threshold in settings["thresholds"]:
        for endpoint in (0, 1):
            for (start, end), delta in global_changes.items():
                matched = groups[start, end, threshold, endpoint]
                inside = sum(row["net_I_to_B"] for row in matched)
                net_i = sum(row["net_I_hops"] for row in matched)
                net_b = sum(row["net_B_hops"] for row in matched)
                steps.append({"start": start, "end": end, "threshold": threshold, "endpoint": endpoint,
                              "net_I_hops": net_i, "net_B_hops": net_b, "global_B_change": delta,
                              "net_I_to_B_inside": inside, "net_I_to_B_outside": delta - inside})
    return steps


def summarize_circulation(steps):
    groups = defaultdict(list)
    for row in steps:
        groups[row["threshold"], row["endpoint"]].append(row)
    fields = ("net_I_hops", "net_B_hops", "net_I_to_B_inside", "net_I_to_B_outside", "global_B_change")

    def direction(r):
        return (r["net_I_hops"] > 0 and r["net_B_hops"] < 0
                and r["net_I_to_B_inside"] > 0 and r["net_I_to_B_outside"] < 0)

    summaries = []
    for (threshold, endpoint), group in sorted(groups.items()):
        sums = {f: sum(r[f] for r in group) for f in fields}
        summaries.append({"threshold": threshold, "endpoint": endpoint, **sums,
                          "signed_circulation_for_total": direction(sums),
                          "intervals_with_signed_circulation": sum(direction(r) for r in group),
                          "intervals": len(group)})
    return summaries


def symmetric_circulation(steps):
    endpoints = defaultdict(dict)
    for rec in steps:
        endpoints[rec["threshold"], rec["start"], rec["end"]][rec["endpoint"]] = rec
    combined = []
    for (threshold, start, end), pair in sorted(endpoints.items()):
        if set(pair) != {0, 1}:
            raise ValueError("Both masks are needed for the time-symmetric readout")
        fields = ("net_I_hops", "net_B_hops", "net_I_to_B_inside", "net_I_to_B_outside", "global_B_change")
        combined.append({"threshold": threshold, "start": start, "end": end, "endpoint": -1,
                         **{key: pair[0][key] + pair[1][key] for key in fields}})
    return summarize_circulation(combined)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", type=Path, required=True)
    parser.add_argument("--previous", type=Path, default=PREVIOUS / "evidence")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = read_json(args.transport / "results.json")
    if evidence["registration_sha256"] != sha256(HOP_PLAN):
        raise ValueError("Different transport registration")
    plan = read_json(HOP_PLAN)
    rows, flow, totals = {}, {}, []
    for record in evidence["records"]:
        data, global_changes = verified_rows(record, args.transport, args.previous, plan)
        steps = circulation(data, global_changes, plan)
        flow[record["archive"]] = steps
        rows[record["archive"]] = data
        totals.append({"N": record["N"], "case": record["case"], "seed": record["seed"],
                       "archive": record["archive"], "balances": aggregate(data),
                       "circulation": summarize_circulation(steps),
                       "circulation_twice_symmetric": symmetric_circulation(steps)})
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "results.json").write_text(json_text({"registration_sha256": sha256(REGISTRATION),
        "circulation_registration_sha256": sha256(CIRCULATION_PLAN),
        "transport_sha256": sha256(args.transport / "results.json"), "records": totals}))
    write_gzip(args.out / "fixed_mask_balances.json.gz", rows)
    write_gzip(args.out / "circulation_intervals.json.gz", flow)


if __name__ == "__main__":
    main()
