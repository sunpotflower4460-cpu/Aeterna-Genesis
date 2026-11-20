"""Audit the corrective early-stop run and write its paired observations."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

from tools.study_record import check_record, load_plan, read_object

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("early_stop_measurement", HERE / "analyze.py")
measurement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measurement)


def analyze(evidence, out):
    plan_path = HERE / "PAIRED_PLAN.json"
    plan = load_plan(plan_path)
    record_path = evidence / "record.json"
    manifest = check_record(plan_path, record_path)
    record = read_object(record_path)
    groups = defaultdict(list)
    observations, history, attempts, pairs = {}, {}, {}, {}
    for name, case in plan["cases"].items():
        attempt = record["cases"][name][-1]
        if attempt["status"] != "completed":
            continue
        with np.load(evidence / (name + ".npz")) as data:
            observations[name], history[name] = measurement.measure(data)
            ledger = data["ledger"]
            after = ledger[ledger[:, 0] >= plan["protocol"]["release_end"]]
            if case["mode"] != "continue" and np.any(after[:, -1]):
                raise ValueError(f"nonzero power after the observation starts: {name}")
            if case["mode"] == "release" and np.any(after[:, 3]):
                raise ValueError(f"nonzero potential amplitude after the release: {name}")
        attempts[name] = attempt
        groups[(case["variant"], case["seed"])].append(name)
    for (variant, seed), names in groups.items():
        stopped = [name for name in names if not name.endswith("-continue")]
        pairs[f"{variant}-{seed}"] = {
            "prefix_to_58": measurement.compare(evidence, names, attempts, 58) if len(names) >= 2 else {},
            "prefix_to_70": measurement.compare(evidence, stopped, attempts, 70) if len(stopped) >= 2 else {},
        }
    witness = "base-92301-release"
    if witness in attempts:
        with np.load(evidence / (witness + "-volumes.npz")) as check:
            for time in (58, 70):
                expected = attempts[witness][f"state_t{time}_sha256"]
                actual = hashlib.sha256(check[f"t{time}"].astype("<c16", copy=False).tobytes()).hexdigest()
                if expected != actual:
                    raise ValueError(f"archived common field at t={time} does not match its digest")
    out.mkdir(parents=True, exist_ok=True)
    result = {"manifest": manifest, "prefixes": pairs, "flows": observations}
    (out / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "tracking.json.gz").write_bytes(gzip.compress(json.dumps(history, separators=(",", ":"), allow_nan=False)
                                                         .encode(), mtime=0))
    print(json.dumps(manifest, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    analyze(args.evidence.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
