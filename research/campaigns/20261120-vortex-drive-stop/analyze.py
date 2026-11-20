"""Read the frozen plan and phase crossings to make a paired measurement ledger."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from cylinder import material
from genesis.diagnostics import vortex_rings
from loops import follow, frames, summarize, minimum_image
from tools.study_record import check_record, load_plan, read_object

HERE = Path(__file__).resolve().parent


def work_and_heat(data):
    times, _, _, _, work, heat, energy, mass, power = data["ledger"].T
    stop = int(np.flatnonzero(times == 132)[0])
    return {
        "work_0_to_120": float(work[times == 120].item()),
        "work_braking_window": float(work[stop] - work[times == 120].item()),
        "work_after_132": float(work[-1] - work[stop]),
        "heat_after_132": float(heat[-1] - heat[stop]),
        "energy_change_after_132": float(energy[-1] - energy[stop]),
        "post_132_max_absolute_power": float(np.abs(power[stop:]).max()),
        "max_absolute_balance_residual": float(np.abs(energy - energy[0] - work + heat).max()),
        "relative_final_mass_change": float(mass[-1] / mass[0] - 1),
        "max_energy": float(energy.max()),
    }


def observe(data):
    components = frames(data)
    times = data["ledger"][:, 0]
    period = data["shape"] * data["dx"]
    summary, histories = {}, {}
    for name, v_cutoff, stride in (("main", 0.5, 1), ("mask-025", 0.25, 1),
                                    ("mask-100", 1.0, 1), ("every-four", 0.5, 2)):
        counts, tracks = follow(components[::stride], times[::stride], period, v_cutoff)
        summary[name] = summarize(tracks)
        summary[name]["cohort_terminal_axial_travel"] = [
            float(sum(minimum_image(np.subtract(b["center"], a["center"]), period)[2]
                      for a, b in zip(segment[:-1], segment[1:])))
            for tr in tracks if tr[0]["t"] <= 116 and tr[-1]["t"] == 224
            for segment in [[row for row in tr if row["t"] >= 132]]
        ]
        histories[name] = {"counts": counts, "tracks": tracks}
    return summary | {"budget": work_and_heat(data)}, histories


def phase_crossings(field):
    windings = vortex_rings.plaquette_windings(field)
    expected = [windings[(1, 2)], -windings[(0, 2)], windings[(0, 1)]]
    items = []
    for normal, values in enumerate(expected):
        for x, y, z in np.argwhere(values):
            items.append((normal, int(x), int(y), int(z), int(values[x, y, z])))
    return sorted(items)


def read_witness(evidence, plan, record):
    case = plan["cases"]["base-g0-92101-continue"]
    audits = {}
    for mode in ("continue", "brake"):
        name = "base-g0-92101-" + mode
        with np.load(evidence / (name + ".npz")) as data, np.load(evidence / (name + "-volumes.npz")) as fields:
            for field_key in fields.files:
                time = 120 if field_key == "at_split" else plan["protocol"]["duration"]
                index = np.flatnonzero(data["ledger"][:, 0] == time).item()
                logged = sorted(map(tuple, data["faces"][data["faces"][:, 0] == index, 1:].tolist()))
                volume = fields[field_key]
                measured = phase_crossings(volume)
                if logged != measured:
                    raise ValueError(f"independent phase detector disagreed for {name} {field_key}")
                mid = volume[volume.shape[0] // 2]
                observed_slice = data["cuts"][data["cut_times"] == time][0]
                maximum = float(np.max(np.abs((np.abs(mid)**2).astype("<f4") - observed_slice)))
                if field_key == "at_split":
                    digest = hashlib.sha256(volume.astype("<c16", copy=False).tobytes()).hexdigest()
                    for arm in ("continue", "brake"):
                        if record["cases"]["base-g0-92101-" + arm][-1]["prefix_sha256"] != digest:
                            raise ValueError("independent volume digest disagrees with a split-time hash")
                if maximum > 1e-6 or volume.shape != tuple(case["shape"]):
                    raise ValueError(f"independent slice readback disagreed for {name} {field_key}")
                audits[name + "-" + field_key] = {"signed_faces_equal": len(measured), "slice_max_error": maximum}
    return audits


def compare_pairs(evidence, plan, record, flow):
    pairs = {}
    for name, case in plan["cases"].items():
        if case.get("mode") != "continue" or name not in flow:
            continue
        other = name.removesuffix("-continue") + "-brake"
        if other not in flow:
            pairs[name] = {"comparison": "missing brake arm"}
            continue
        continued, braked = [record["cases"][candidate][-1] for candidate in (name, other)]
        with np.load(evidence / (name + ".npz")) as a, np.load(evidence / (other + ".npz")) as b:
            index = np.flatnonzero(a["ledger"][:, 0] == 120).item()
            same_frames = np.array_equal(a["ledger"][:index + 1], b["ledger"][:index + 1])
            same_faces = np.array_equal(a["faces"][a["faces"][:, 0] <= index],
                                        b["faces"][b["faces"][:, 0] <= index])
        same_state = all(continued[k] == braked[k] for k in ("initial_sha256", "prefix_sha256"))
        if not (same_state and same_frames and same_faces):
            raise ValueError(f"mismatched treatment prefix: {name}")
        pairs[name] = {"verified_prefix": True}
    return pairs


def analyze(evidence, out):
    plan = load_plan(HERE / "PLAN.json")
    record = read_object(evidence / "record.json")
    manifest = check_record(HERE / "PLAN.json", evidence / "record.json")
    flow, chamber, histories = {}, {}, {}
    for name, case in plan["cases"].items():
        attempt = record["cases"][name][-1]
        if attempt["status"] != "completed":
            continue
        if case["kind"] == "flow":
            with np.load(evidence / (name + ".npz")) as saved:
                flow[name], histories[name] = observe(saved)
        else:
            d = read_object(evidence / (name + ".json"))
            pct = 100 * (d["fine"]["hz"] / d["observed_hz"] - 1)
            d["fine_error_pct"] = pct
            chamber[name] = d
    pairs = compare_pairs(evidence, plan, record, flow)
    witness = read_witness(evidence, plan, record) if all("base-g0-92101-" + arm in flow
                                                         for arm in ("continue", "brake")) else {}
    out.mkdir(parents=True, exist_ok=True)
    results = {
        "manifest": manifest,
        "physical_scales": material(plan["reference"]),
        "pairs": pairs,
        "witness_readback": witness,
        "flows": flow,
        "cylinders": chamber,
    }
    (out / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "tracking.json.gz").write_bytes(gzip.compress(json.dumps(histories, separators=(",", ":"), allow_nan=False)
                                                         .encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
