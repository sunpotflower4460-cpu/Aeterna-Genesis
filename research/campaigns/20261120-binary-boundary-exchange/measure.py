"""Measure both species in the same tracked 3D boundary, with raw event provenance."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import math
from pathlib import Path

import numpy as np

from tools.study_record import check_record, load_plan, read_object

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PLAN.json"
spec = spec_from_file_location("argon_geometry", HERE.parent / "20261120-argon-interface-turnover/analyze.py")
geometry = module_from_spec(spec)
spec.loader.exec_module(geometry)


def saturation(rows, temperature):
    (t0, p0), (t1, p1) = rows
    if not t0 <= temperature <= t1:
        raise ValueError("pure-component saturation pressure is not bracketed")
    a = (1 / temperature - 1 / t0) / (1 / t1 - 1 / t0)
    return math.exp((1 - a) * math.log(p0) + a * math.log(p1))


def scales(plan):
    material = plan["material"]
    ar = material["pairs_ar_ar_ar_kr_kr_kr"][0]
    reference = plan["real_material_reference"]
    temperature = reference["temperature_K"]
    ar_pressure = saturation(reference["ar_saturation_rows_K_MPa"], temperature)
    kr_pressure = saturation(reference["kr_saturation_rows_K_MPa"], temperature)
    return {
        "tau_ps": 1e12 * ar["sigma_m"] * math.sqrt(material["ar_mass_kg"] / ar["epsilon_J"]),
        "kelvin_per_reduced_unit": ar["epsilon_J"] / material["boltzmann_J_per_K"],
        "mpa_per_reduced_unit": 1e-6 * ar["epsilon_J"] / ar["sigma_m"]**3,
        "pure_ar_pressure_MPa": ar_pressure,
        "pure_kr_pressure_MPa": kr_pressure,
        "ideal_relative_volatility_ar_to_kr": ar_pressure / kr_pressure,
    }


def fractions(totals, heavy):
    denominator = totals.sum(axis=0)
    if (denominator == 0).any():
        return None
    x, y = heavy.sum(axis=0) / denominator
    return {"x_kr": float(x), "y_kr": float(y), "delta_kr": float(x - y)}


def count_events(events, species, phase, in_window, interval, displaced):
    tallies = {}
    for identifier, element in ((0, "ar"), (1, "kr")):
        counts = {}
        atom = species == identifier
        for direction, source in (("liquid_to_vapor", 1), ("vapor_to_liquid", 2)):
            ids = [e["atom"] for e in events
                   if e["direction"] == direction and atom[e["atom"]]
                   and (e["moves_between_cores"] or not displaced)]
            exposure = int(np.count_nonzero(phase[in_window][:, atom] == source)) * interval
            counts[direction] = {
                "events": len(ids),
                "distinct_ids": len(set(ids)),
                "sampled_source_atom_tau": exposure,
                "events_per_1000_source_atom_tau": 1000 * len(ids) / exposure if exposure else None,
            }
        tallies[element] = counts
    return tallies


def load_binary(evidence, name, outcome):
    positions, ledger = geometry.load_trajectory(evidence, name, outcome)
    source = outcome.get("prefix", name + ".npz")
    with np.load(evidence / source) as archive:
        species, initial = archive["species"], archive["initial_state"]
        length = archive["box_length"].item()
    if not np.all(np.isfinite(initial)) or not np.array_equal(
            np.floor(initial[0] * (65536 / length)).astype("<u2"), positions[0]):
        raise ValueError(f"initial state and first snapshot differ: {name}")
    return positions, ledger, species, initial


def read_geometry(positions, clock, species, length, protocol, scheme):
    threshold, depth, stride = geometry.SCHEMES[scheme]
    history, times = positions[::stride], clock[::stride]
    phase, frozen_phase, frames = geometry.classify(history, times, length, threshold, depth, protocol)
    fork, last = geometry.mine_track(frames, protocol["fork"], protocol["overlap_min"])
    complete = last == len(times) - 1
    total = np.column_stack([(phase == k).sum(axis=1) for k in (1, 2)])
    heavy = np.column_stack([(phase[:, species == 1] == k).sum(axis=1) for k in (1, 2)])
    for i, row in enumerate(frames):
        row["liquid_kr_count"], row["vapor_kr_count"] = map(int, heavy[i])
    start = protocol["comparison_start"]
    raw_window = (times >= start) & (np.arange(len(times)) <= (last if last is not None else -1))
    core_window = raw_window & (total >= protocol["minimum_core_count"]).all(axis=1)
    detail = {"frames": frames, "events": [], "fixed_atom_null_events": []}
    counts = None
    null_counts = None
    null_moved = None
    if last is not None:
        args = (times, fork, last, protocol["residence_frames"], length, protocol["minimum_displacement"])
        events = geometry.exchange(phase, history, *args)["events"]
        frozen = np.broadcast_to(history[fork], history.shape)
        null_events = geometry.exchange(frozen_phase, frozen, *args)["events"]
        detail.update(events=events, fixed_atom_null_events=null_events)
        interval = float(times[1] - times[0])
        exposure_window = raw_window & (np.arange(len(times)) < last)
        counts = count_events([e for e in events if e["from_t"] >= start], species, phase,
                              exposure_window, interval, displaced=True)
        late_null = [e for e in null_events if e["from_t"] >= start]
        null_counts = count_events(late_null, species, frozen_phase, exposure_window, interval, displaced=False)
        null_moved = sum(e["moves_between_cores"] for e in late_null)
    blocks = []
    edges = protocol["composition_block_edges"]
    for lo, hi in zip(edges, edges[1:]):
        stop = times <= hi if hi == edges[-1] else times < hi
        keep = core_window & (times >= lo) & stop
        blocks.append({"from_tau": lo, "to_tau": hi, "valid_frames": int(keep.sum()),
                       "composition": fractions(total[keep], heavy[keep])})
    all_frames = int(np.count_nonzero(times >= start))
    valid = int(core_window.sum())
    summary = {
        "first_bounded_tau": next((r["t"] for r in frames if r["bounded"]), None),
        "bounded_frames": sum(r["bounded"] for r in frames),
        "track_through_tau": frames[last]["t"] if last is not None else None,
        "track_complete": complete,
        "window_expected_frames": all_frames,
        "window_valid_frames": valid,
        "window_complete": complete and valid == all_frames,
        "window_composition": fractions(total[core_window], heavy[core_window]),
        "blocks": blocks,
        "transits": counts,
        "fixed_atom_null": null_counts,
        "fixed_atom_null_with_displacement": null_moved,
    }
    return summary, detail


def analyze(evidence, out):
    plan = load_plan(PLAN)
    protocol = plan["protocol"]
    path = evidence / "record.json"
    manifest = check_record(PLAN, path)
    record = read_object(path)
    units = scales(plan)
    results, details = {}, {}
    ancestor_states = defaultdict(set)
    initial_states = defaultdict(set)
    for name, config in plan["cases"].items():
        attempt = record["cases"][name][-1]
        if attempt["status"] != "completed":
            continue
        if "prefix" in attempt:
            ancestor_states[config["group"]].add((attempt["prefix"], attempt["checkpoint_sha256"]))
        positions, ledger, species, initial = load_binary(evidence, name, attempt)
        key = (config["seed"], config["cells"], config["length"])
        initial_states[key].add(hashlib.sha256(initial.tobytes() + species.tobytes()).hexdigest())
        t = ledger[:, 1]
        result, detail = {}, {}
        for scheme in protocol["scales"]:
            result[scheme], detail[scheme] = read_geometry(
                positions, t, species, config["length"], protocol, scheme)
        fork = np.flatnonzero(t == protocol["fork"]).item()
        late = t >= protocol["comparison_start"]
        energy = ledger[:, 3] + ledger[:, 4]
        work = ledger[:, 5]
        momentum = ledger[:, 6:9]
        n = len(species)
        result["ledger"] = {
            "late_mean_K": float(ledger[late, 2].mean() * units["kelvin_per_reduced_unit"]),
            "late_whole_box_virial_MPa": float(ledger[late, 9].mean() * units["mpa_per_reduced_unit"]),
            "max_abs_balance_error_per_atom": float(np.abs(energy - energy[0] - work).max() / n),
            "max_energy_change_since_fork_per_atom": float(np.abs(energy[fork:] - energy[fork]).max() / n),
            "max_bath_work_change_since_fork_per_atom": float(np.abs(work[fork:] - work[fork]).max() / n),
            "max_momentum_change_since_fork": float(np.linalg.norm(momentum[fork:] - momentum[fork], axis=1).max()),
        }
        if config["mode"] == "isolated" and result["ledger"]["max_bath_work_change_since_fork_per_atom"] != 0:
            raise ValueError(f"unregistered heat transfer after isolation: {name}")
        core = result["main"]
        if config["mode"] == "bath" and config["model"] == "ar-kr" and core["window_complete"]:
            x, y = (core["window_composition"][value] for value in ("x_kr", "y_kr"))
            alpha = units["ideal_relative_volatility_ar_to_kr"]
            expected = x / (x + alpha * (1 - x))
            result["ideal_reference"] = {
                "at_measured_x_kr": expected, "y_kr_minus_ideal": y - expected,
                "effective_relative_volatility_ar_to_kr": (1 - y) * x / (y * (1 - x)) if 0 < x < 1 and y > 0 else None,
            }
        results[name], details[name] = result, detail
    if any(len(states) != 1 for states in (*ancestor_states.values(), *initial_states.values())):
        raise ValueError("paired cases have inconsistent phase-space histories")
    out.mkdir(parents=True, exist_ok=True)
    content = {"manifest": manifest, "units": units, "cases": results}
    (out / "results.json").write_text(json.dumps(content, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "measurements.json.gz").write_bytes(gzip.compress(
        json.dumps(details, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
