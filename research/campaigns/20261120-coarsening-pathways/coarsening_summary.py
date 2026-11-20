"""Summarize all paired histories while keeping particle paths and controls traceable."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
import math
from pathlib import Path
from zipfile import ZipFile

from coarsening_runs import HERE, PLAN, PREVIOUS, read_json, sha256
from analyse import check_initial_matching, composition_residual
from mobility import MOBILITY_PLAN
from pathways import BUDGET_KEYS, KINDS
from survey import MECHANISM_PLAN, REGION_FIELDS, SCALES, check_prefix, write_gzip
from run import json_text


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def cube(row):
    recipe = row["recipe"]
    return recipe["N"], recipe["seed"], recipe["case"]["id"]


def read_surveys(sources, plan):
    expected = (sha256(PLAN), sha256(MECHANISM_PLAN), sha256(MOBILITY_PLAN))
    roster, frames, events = [], {}, {}
    for source in sources:
        report = read_json(source / "results.json")
        hashes = tuple(report[k] for k in ("registration_sha256", "mechanism_registration_sha256",
                                             "mobility_registration_sha256"))
        if hashes != expected:
            raise ValueError(f"Registration mismatch in {source}")
        overlap = {r["archive"] for r in roster} & {r["archive"] for r in report["archives"]}
        if overlap:
            raise ValueError(f"Duplicate histories: {sorted(overlap)}")
        roster.extend(report["archives"])
        frames.update(read_gzip(source / "frames.json.gz"))
        events.update(read_gzip(source / "transitions.json.gz"))
    keys = {r["archive"] for r in roster}
    if keys != set(frames) or keys != set(events):
        raise ValueError("The tables and the histories do not agree")
    by_phase = defaultdict(list)
    for row in roster:
        by_phase[row["phase"]].append(row)
    old = by_phase["extent"]
    historical = read_json(PREVIOUS / "measurements" / "results.json")
    expected_old = {row["archive"]: row for row in historical["archives"] if row["phase"] == "extent"}
    if len(old) != len(expected_old) or set(expected_old) != {r["archive"] for r in old}:
        raise ValueError("The archived comparison panel is incomplete")
    for row in old:
        parent = expected_old[row["archive"]]
        if row["archive_sha256"] != parent["archive_sha256"]:
            raise ValueError(f"Archived control changed: {row['archive']}")
        for time, outcome in row["windows"].items():
            if any(abs(outcome[key] - parent["windows"][time][key]) > 1e-12 for key in SCALES):
                raise ValueError(f"Inherited length measurement changed: {row['archive']} at {time}")

    new_phase = plan["matrix"]["phase"]
    phase_totals = {new_phase: plan["matrix"]["histories"], "mobility": read_json(MOBILITY_PLAN)["histories"]}
    for phase, count in phase_totals.items():
        if len(by_phase[phase]) not in (0, count):
            raise ValueError(f"Incomplete panel {phase}")
    return roster, frames, events, by_phase


def means(values):
    return {"by_seed": values, "mean": math.fsum(values) / len(values) if None not in values else None}


def active_histories(roster, plan):
    driven = plan["solver"]["case"]
    old_n56 = any(row["phase"] == plan["matrix"]["phase"] for row in roster)
    result = [row for row in roster if cube(row)[2] == driven
              and not (old_n56 and row["phase"] == "extent" and row["recipe"]["N"] == 56)]
    return sorted(result, key=cube)


def size_windows(rows, thresholds):
    groups = defaultdict(list)
    for row in rows:
        n, seed, _ = cube(row)
        for time, observation in row["windows"].items():
            groups[n, int(time)].append((seed, observation))
    result = []
    for (n, time), group in sorted(groups.items()):
        seeds, windows = zip(*group, strict=True)
        measures = {key: means([window[key] for window in windows]) for key in (*SCALES, "B_fraction", "gross_turnover")}
        measures["regions"] = {
            key: {field: means([w["regions"][key][field] for w in windows]) for field in REGION_FIELDS}
            for key in thresholds
        }
        result.append({"N": n, "seeds": list(seeds), "end": time, **measures})
    return result


def late_tests(windows):
    n_values = (56, 64)
    time_values = (3600, 4200, 4800)
    lookup = {(row["N"], row["end"]): row for row in windows}
    if any((n, t) not in lookup for n in n_values for t in time_values):
        return None
    lengths = SCALES[:2]

    def change(ref, new, field):
        old, late = lookup[ref][field], lookup[new][field]
        def relative(x, y):
            return y / x - 1 if x and y is not None else None

        return {"of_means": relative(old["mean"], late["mean"]),
                "by_seed": [relative(x, y) for x, y in zip(old["by_seed"], late["by_seed"], strict=True)]}

    time_steps = {
        f"{n}/{begin}-{end}": {field: change((n, begin), (n, end), field) for field in lengths}
        for n in n_values for begin, end in zip(time_values, time_values[1:])
    }
    size_step = {field: change((56, 4800), (64, 4800), field) for field in lengths}
    shell = {str(n): lookup[n, 4800]["first_shell_fraction"] for n in n_values}
    def bounded(value, tolerance):
        return value is not None and abs(value) <= tolerance

    evidence = {
        "temporal_each_size_each_step_within_5pct": all(bounded(val["of_means"], 0.05)
                                                        for p in time_steps.values() for val in p.values()),
        "size_difference_within_10pct": all(bounded(val["of_means"], 0.10) for val in size_step.values()),
        "last_first_shell_not_majority": all(bounded(val["mean"], 0.5) for val in shell.values()),
    }
    return {"changes_over_time": time_steps, "changes_across_size": size_step, "last_first_shell": shell,
            "criteria": evidence, "all_pass": all(evidence.values())}


def pathways_by_group(roster, thresholds, cadences):
    groups = defaultdict(list)
    for row in roster:
        n, seed, case = cube(row)
        groups[row["phase"], n, case].append(row)
    result = []
    for (phase, n, case), records in sorted(groups.items()):
        durations = sorted(set(r["recipe"]["T"] for r in records))
        for threshold in thresholds:
            for cadence in cadences:
                rollup = [row["region_budget"][threshold][cadence] for row in records]
                history_count = len(rollup)
                totaled = {key: sum(r["number_budget"][key] for r in rollup) for key in BUDGET_KEYS}
                counts = {kind: sum(r["event_counts"][kind] for r in rollup) for kind in KINDS}
                first = sum(r["first_count"] for r in rollup)
                last = sum(r["last_count"] for r in rollup)
                end_single = sum(bool(row["sustained_single_region"][threshold])
                                 and not row["sustained_single_region"][threshold][-1]["observed_reversal"]
                                 for row in records)
                result.append({
                    "phase": phase, "N": n, "case": case, "threshold": threshold, "cadence": int(cadence),
                    "durations": durations, "histories": history_count, "first_count": first, "last_count": last,
                    "net_number_budget": totaled, "observed_events": counts,
                    "sustained_single_at_end": end_single,
                    "strict_separated_losses": sum(r["loss_statuses"].get("strict_separated_loss", 0) for r in rollup),
                    "strict_losses_with_witnessed_routes": sum(r["strict_losses_with_witnessed_routes"] for r in rollup),
                    "witnessed_routes": sum(r["witnessed_same_id_routes"] for r in rollup),
                    "time_exposure": sum(r["time_exposure"] for r in rollup),
                    "region_time_exposure": sum(r["region_time_exposure"] for r in rollup),
                    "material_budgets": {key: sum(r["material_budgets"][key] for r in rollup)
                                         for key in rollup[0]["material_budgets"]},
                    "paired_extremes": {key: sum(r["paired_extremes"][key] for r in rollup)
                                        for key in rollup[0]["paired_extremes"]},
                })
    return result


def paired_controls(old, plan):
    groups = defaultdict(list)
    for row in old:
        n, seed, _ = cube(row)
        if n in (32, 48):
            groups[n, seed].append(row)
    result = []
    for (n, seed), group in sorted(groups.items()):
        active = next(row for row in group if cube(row)[2] == plan["solver"]["case"])
        controls = sorted((row for row in group if row is not active),
                          key=lambda row: row["full_tracking_exposure"]["B_fraction"])
        if len(controls) != 3:
            raise ValueError("Each archived condition must have three actual reversible controls")
        active_exposure = active["full_tracking_exposure"]
        fractions = [row["full_tracking_exposure"]["B_fraction"] for row in controls]
        turnover_control = [row["full_tracking_exposure"]["gross_turnover"] for row in controls]
        active_fraction = active_exposure["B_fraction"]
        active_rate = active_exposure["gross_turnover"]
        rate = composition_residual(active_fraction, active_rate, list(zip(fractions, turnover_control, strict=True)))
        mismatch = abs(rate["signed_residual"] / active_rate) if rate["bracket_available"] else None
        demography = {}
        for threshold, sampling in active["region_budget"].items():
            for cadence, window in sampling.items():
                other = [row["region_budget"][threshold][cadence] for row in controls]
                if any(row["time_exposure"] != window["time_exposure"] for row in other):
                    raise ValueError("Comparison exposure differs across cases")
                measure = "region_losses_per_1000_time"
                defined = composition_residual(active_fraction, window[measure],
                                               list(zip(fractions, [o[measure] for o in other], strict=True)))
                if defined["bracket_available"]:
                    defined["bracket_loss_rates"] = defined.pop("bracket_variance")
                    defined["interpolated_loss_rate"] = defined.pop("interpolated_variance")
                demography[f"{threshold}/{cadence}"] = {
                    "observed_loss_rate": window[measure],
                    "control_loss_rates": [o[measure] for o in other],
                    "controls_interpolated_at_same_B": defined,
                }
        result.append({"N": n, "seed": seed, "window": [plan["domains"]["first_time"], active["recipe"]["T"]],
                       "active_B_fraction": active_fraction, "active_gross": active_rate,
                       "controls": [{"case": cube(row)[2], **row["full_tracking_exposure"]} for row in controls],
                       "B_bracket_available": rate["bracket_available"], "relative_gross_error": mismatch,
                       "joint_match": mismatch is not None and mismatch <= 0.1, "demography": demography})
    return result


def mobility_pairs(rows, previous):
    register = read_json(MOBILITY_PLAN)
    n, case_id = register["N"], register["reference"]["id"]
    refs = {cube(r)[1]: r for r in previous if cube(r)[0] == n and cube(r)[2] == case_id}
    result = []
    for row in rows:
        _, seed, mobility = cube(row)
        base = refs[seed]
        params, before = row["recipe"]["parameters"], base["recipe"]["parameters"]
        changed = {key for key, value in params.items() if before[key] != value}
        if changed != {"D_" + mobility[-1]} or row["initial_hashes"] != base["initial_hashes"]:
            raise ValueError("The mobility intervention or the shared initial configuration changed")
        for start, end in register["windows"]:
            reference = base["windows"][str(end)]
            changed = row["windows"][str(end)]
            fields = (*SCALES, "B_fraction", "work", "gross_turnover", "passive", "driven")
            delta = {f: changed[f] - reference[f] for f in fields}
            delta["regions"] = {key: changed["regions"][key]["count"] - reference["regions"][key]["count"]
                                for key in reference["regions"]}
            result.append({
                "N": n, "seed": seed, "case": mobility, "window": [start, end], "delta": delta,
                "reference": reference, "measured": changed,
                "B_fraction_difference_within_2_points": abs(delta["B_fraction"]) <= 0.02,
            })
    return result


def choose_transfer_event(active, events):
    candidates = []
    for row in active:
        n, seed, _ = cube(row)
        for threshold, by_interval in events[row["archive"]].items():
            for cadence, transitions in by_interval.items():
                for step in transitions:
                    for loss in step["losses"]:
                        count = loss.get("witnessed_same_id_routes", 0)
                        if count:
                            preference = (-n, not (threshold == "0.5" and cadence == "50"), -count,
                                          seed, step["end"], float(threshold), int(cadence), loss["source"])
                            candidates.append((preference, row["archive"], threshold, int(cadence), loss))
    if not candidates:
        return None
    _, archive, threshold, cadence, loss = min(candidates)
    return {"archive": archive, "threshold": threshold, "cadence": cadence, **loss}



def reference_prefix_checks(evidence, archives, completed):
    """Verify the archived stock-solver prefixes against full specialized histories."""
    known = {row["recipe"]["seed"]: row for row in completed if row["recipe"]["N"] == 64}
    results = []
    for archive in sorted(archives):
        with ZipFile(evidence / archive) as stock:
            meta = json.loads(stock.read("reference-stop.json"))
            recipe = json.loads(stock.read("recipe.json"))
            execution = json.loads(stock.read("execution.json"))
        match = known[recipe["seed"]]
        if recipe != match["recipe"]:
            raise ValueError(f"Reference run parameters differ: {archive}")
        if execution["binary_sha256"] == match["execution"]["binary_sha256"]:
            raise ValueError(f"Expected independently compiled stock and specialized binaries: {archive}")
        with ZipFile(evidence / match["archive"]) as active:
            validation = check_prefix(active, evidence / archive)
        if (validation["byte_identical_states"] != meta["checkpoints"]
                or validation["byte_identical_ledger_rows"] != meta["ledger_rows"]):
            raise ValueError(f"Reference observation count differs: {archive}")
        results.append({"seed": recipe["seed"], "stock_prefix": archive, "completed_history": match["archive"],
                        "stock_binary_sha256": execution["binary_sha256"],
                        "specialized_binary_sha256": match["execution"]["binary_sha256"], **validation})
    return results


def summarize(sources, evidence):
    plan = read_json(PLAN)
    roster, frames, events, by_phase = read_surveys(sources, plan)
    thresholds = list(map(str, plan["domains"]["thresholds"]))
    cadences = list(map(str, plan["domains"]["cadences"]))
    active = active_histories(roster, plan)
    scales = size_windows(active, thresholds)
    new = by_phase[plan["matrix"]["phase"]] + by_phase["mobility"]
    new_keys = {row["archive"] for row in new}
    expected = set(new_keys)
    evidence_archives = {p.relative_to(evidence).as_posix(): p for p in evidence.rglob("*.zip")}
    missing = new_keys - set(evidence_archives)
    if missing:
        raise ValueError(f"Missing physical data: {sorted(missing)}")
    for row in new:
        path = evidence_archives[row["archive"]]
        if sha256(path) != row["archive_sha256"]:
            raise ValueError(f"The completed archive changed: {row['archive']}")
        with ZipFile(path) as bundle:
            if bundle.testzip() is not None:
                raise ValueError(f"Invalid archive CRC: {row['archive']}")
    attempts, stock_prefixes = [], []
    for key, archive in sorted(evidence_archives.items()):
        if key.startswith("reference-prefixes/"):
            stock_prefixes.append(key)
        if key.startswith(("failures/", "reference-prefixes/")):
            attempts.append({"path": key, "sha256": sha256(archive)})
            expected.add(key)
    if set(evidence_archives) != expected:
        raise ValueError("Evidence directory has unexpected trial archives")

    return {
        "registration_sha256": sha256(PLAN),
        "mechanism_registration_sha256": sha256(MECHANISM_PLAN),
        "mobility_registration_sha256": sha256(MOBILITY_PLAN),
        "archives": new, "reused_archives": by_phase["extent"], "partial_attempts": attempts,
        "validated_stock_solver_prefixes": reference_prefix_checks(evidence, stock_prefixes, new),
        "matched_initial_groups": check_initial_matching(roster),
        "maximum_relative_medium_error": max(row["max_relative_medium_error"] for row in roster),
        "active_scale_windows": scales, "finite_window_length_test": late_tests(scales),
        "region_budget_panels": pathways_by_group(roster, thresholds, cadences),
        "paired_archive_controls": paired_controls(by_phase["extent"], plan),
        "mobility_contrasts": mobility_pairs(by_phase["mobility"], by_phase["extent"]),
        "witnessed_transport_example": choose_transfer_event(active, events),
    }, frames, events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("surveys", type=Path, nargs="+")
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result, frames, events = summarize(args.surveys, args.evidence)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "results.json").write_text(json_text(result))
    write_gzip(args.out / "frames.json.gz", frames)
    write_gzip(args.out / "transitions.json.gz", events)


if __name__ == "__main__":
    main()
