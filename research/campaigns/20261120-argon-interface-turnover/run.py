"""Execute the registered molecular dynamics, keeping the common history and both continuations."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from threading import Lock

import numpy as np

from tools.study_record import load_plan, sha256, verify_registration

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PLAN.json"


def atomic_json(path, data):
    scratch = path.with_suffix(".tmp")
    scratch.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    scratch.replace(path)


def assemble(raw, out, arm, case, protocol, start, end, common_state=None):
    with (raw / (arm + ".csv")).open() as stream:
        rows = csv.reader(stream)
        columns = next(rows)
        ledger = np.array([[float(v) for v in row] for row in rows], dtype="<f8")
    steps = np.arange(round(start / case["dt"]), round(end / case["dt"]) + 1,
                      round(protocol["sample"] / case["dt"]))
    if not np.isfinite(ledger).all() or not np.array_equal(steps, ledger[:, 0]):
        raise ValueError(f"incomplete or nonfinite {arm} ledger")
    atoms = 4 * case["cells"]**3
    positions = np.fromfile(raw / (arm + ".u16"), dtype="<u2").reshape(len(steps), atoms, 3)
    packed = {
        "ledger": ledger, "columns": columns, "positions": positions,
        "box_length": case["length"],
    }
    if common_state is not None:
        packed["common_state"] = np.fromfile(common_state, dtype="<f8").reshape(2, atoms, 3)
    np.savez_compressed(out, **packed)


def run_group(executable, names, cases, protocol, output, scratch):
    raw = scratch / cases[names[0]]["group"]
    raw.mkdir()
    setup = cases[names[0]]
    paired = setup["mode"] != "warm"
    kind = "paired" if paired else "warm"
    arguments = [
        str(executable), str(raw), str(setup["cells"]), str(setup["length"]), str(setup["dt"]),
        str(setup["cutoff"]), str(setup["seed"]), str(protocol["quench"]), str(protocol["fork"]),
        str(protocol["end"]), str(protocol["sample"]), str(protocol["collision_rate"]), kind,
    ]
    with (raw / "solver.log").open("w") as log:
        subprocess.run(arguments, stdout=log, stderr=subprocess.STDOUT, check=True)
    prefix = None
    digests = {}
    if paired:
        states = [raw / (name + ".state") for name in ("prefix", "bath", "isolated")]
        digests = {path.stem: sha256(path) for path in states}
        if len(set(digests.values())) != 1:
            raise ValueError("the saved phase-space states differ at the intervention")
        prefix = output / (setup["group"] + "-prefix.npz")
        assemble(raw, prefix, "prefix", setup, protocol, 0, protocol["fork"], states[0])
    results = {}
    for name in names:
        mode = cases[name]["mode"]
        file = output / (name + ".npz")
        start = protocol["fork"] if paired else 0
        assemble(raw, file, mode, cases[name], protocol, start, protocol["end"])
        sources = [file] if prefix is None else [file, prefix]
        results[name] = {
            "status": "completed",
            "artifacts": {artifact.name: sha256(artifact) for artifact in sources},
        }
        if paired:
            results[name].update(prefix=prefix.name, checkpoint_sha256=digests[mode])
    return results


def run(evidence, scratch, registration, jobs, cxx):
    plan = load_plan(PLAN)
    verify_registration(PLAN, plan, registration)
    evidence.mkdir(parents=True, exist_ok=False)
    scratch.mkdir(parents=True, exist_ok=False)
    flags = ["-std=c++17", "-O3", "-ffp-contract=off"]
    program = scratch / "fluid"
    record = {
        "registration_commit": registration,
        "environment": {
            "platform": platform.platform(), "python": sys.version.split()[0], "numpy": np.__version__,
            "compiler": subprocess.check_output([cxx, "--version"], text=True).splitlines()[0],
            "compiler_flags": flags,
            "native_byte_order": sys.byteorder,
        },
        "cases": {name: [{"status": "not_run", "reason": "not started"}] for name in plan["cases"]},
    }
    atomic_json(evidence / "record.json", record)
    if sys.byteorder != "little":
        raise RuntimeError("the recorded file format requires a little-endian host")
    subprocess.run([cxx, *flags, str(HERE / "fluid.cpp"), "-o", str(program)], check=True)
    record["environment"]["solver_sha256"] = sha256(program)
    atomic_json(evidence / "record.json", record)
    lock = Lock()

    def write(results):
        with lock:
            for name, attempt in results.items():
                record["cases"][name][-1] = attempt
            atomic_json(evidence / "record.json", record)

    def measure(names):
        write({n: {"status": "running", "reason": "common trajectory or control started"} for n in names})
        try:
            completed = run_group(program, names, plan["cases"], plan["protocol"], evidence, scratch)
        except Exception as error:
            artifacts = {}
            group = plan["cases"][names[0]]["group"]
            for raw in sorted((scratch / group).glob("*")):
                if raw.is_file():
                    destination = evidence / f"{group}-partial-{raw.name}.gz"
                    with raw.open("rb") as stream, destination.open("wb") as sink:
                        with gzip.GzipFile(fileobj=sink, mode="wb", mtime=0) as compressed:
                            shutil.copyfileobj(stream, compressed)
                    artifacts[destination.name] = sha256(destination)
            write({n: {"status": "failed", "reason": f"{type(error).__name__}: {error}", "artifacts": artifacts}
                   for n in names})
            print(" ".join(names), "failed", str(error), flush=True)
            return False
        write(completed)
        print(" ".join(names), "completed", flush=True)
        return True

    groups = defaultdict(list)
    for name, config in plan["cases"].items():
        groups[config["group"]].append(name)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(measure, names) for names in groups.values()]
        results = [item.result() for item in as_completed(futures)]
    return int(not all(results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registered-at", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--cxx", default=os.environ.get("CXX", "c++"))
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()
    return run(args.out.resolve(), args.scratch.resolve(), args.registered_at, args.jobs, args.cxx)


if __name__ == "__main__":
    raise SystemExit(main())
