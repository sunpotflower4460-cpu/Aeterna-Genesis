"""Run the registered 3D interventions and static-cylinder reference calculations."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from threading import Lock

import numpy as np
import scipy

from cylinder import calculate
from tools.study_record import load_plan, sha256, verify_registration

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PLAN.json"


def initial_field(case):
    nx, ny, nz = case["shape"]
    dx = case["dx"]
    x, y, z = np.ogrid[:nx, :ny, :nz]
    modes = [(1, 1, 1), (2, -1, 1), (1, 2, -2), (2, 1, 3), (1, -2, 3)]
    rng = np.random.Generator(np.random.PCG64(case["seed"]))
    phase = np.zeros((nx, ny, nz))
    for (kx, ky, kz), (a, b) in zip(modes, rng.standard_normal((len(modes), 2))):
        angle = 2 * np.pi * dx * (kx * (x - nx // 2) / 12 + ky * (y - ny // 2) / 12 + kz * z / 48)
        phase += a * np.cos(angle) + b * np.sin(angle)
    return np.exp(1j * phase * (0.005 / np.sqrt(len(modes))))


def read_evolution(scratch, case, protocol):
    with (scratch / "ledger.csv").open() as stream:
        rows = csv.reader(stream)
        columns = next(rows)
        ledger = np.array([[float(v) for v in row] for row in rows])
    expected_times = np.arange(0, protocol["duration"] + protocol["interval"], protocol["interval"])
    if not np.array_equal(ledger[:, 0], expected_times) or not np.isfinite(ledger).all():
        raise ValueError("missing frames or nonfinite ledger")
    time_index = dict(zip(ledger[:, 0], range(len(ledger))))
    with (scratch / "faces.csv").open() as stream:
        rows = csv.reader(stream)
        next(rows)
        faces = np.array([[time_index[float(t)], *(int(v) for v in data)] for t, *data in rows],
                         dtype=np.int32).reshape(-1, 6)
    cuts = np.fromfile(scratch / "cuts.f32", dtype="<f4").reshape(len(protocol["cuts"]), *case["shape"][1:])
    if not np.isfinite(cuts).all():
        raise ValueError("nonfinite density sections")
    return {
        "shape": case["shape"], "dx": case["dx"], "dt": case["dt"],
        "cut_times": protocol["cuts"], "cuts": cuts, "faces": faces,
        "ledger_columns": columns, "ledger": ledger,
    }


def run_flow(executable, out, scratch, name, case, protocol):
    field = initial_field(case)
    initial = scratch / "initial.c128"
    field.astype("<c16", copy=False).tofile(initial)
    command = [
        str(executable), str(scratch), *map(str, case["shape"]), str(case["dx"]), str(case["dt"]),
        str(case["gamma"]), case["mode"], str(protocol["duration"]), str(protocol["interval"]),
        str(int(case["witness"])), str(initial),
    ]
    with (scratch / "solver.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    data = read_evolution(scratch, case, protocol)
    prefix = scratch / "prefix.c128"
    if prefix.stat().st_size != field.nbytes:
        raise ValueError("incomplete split-time checkpoint")
    details = {"initial_sha256": sha256(initial), "prefix_sha256": sha256(prefix)}
    main = out / (name + ".npz")
    np.savez_compressed(main, **data)
    artifacts = [main]
    if case["witness"]:
        path = out / (name + "-volumes.npz")
        # The common prefix is archived once. Both arms record its digest.
        volumes = {"final": np.fromfile(scratch / "final.c128", dtype="<c16").reshape(case["shape"])}
        if case["mode"] == "continue":
            volumes["at_split"] = np.fromfile(prefix, dtype="<c16").reshape(case["shape"])
        np.savez_compressed(path, **volumes)
        artifacts.append(path)
    return details | {"artifacts": {p.name: sha256(p) for p in artifacts}}


def put_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(out, scratch, registration, jobs, cxx):
    plan = load_plan(PLAN)
    verify_registration(PLAN, plan, registration)
    out.mkdir(parents=True, exist_ok=False)
    scratch.mkdir(parents=True, exist_ok=False)
    record = {
        "registration_commit": registration,
        "environment": {
            "platform": platform.platform(), "python": sys.version.split()[0],
            "numpy": np.__version__, "scipy": scipy.__version__,
        },
        "cases": {name: [{"status": "not_run", "reason": "not started"}] for name in plan["cases"]},
    }
    lock = Lock()

    def save(name, outcome):
        with lock:
            record["cases"][name][-1] = outcome
            put_json(out / "record.json", record)

    put_json(out / "record.json", record)
    executable = scratch / "evolve"
    flags = ["-std=c++17", "-O3", "-ffp-contract=off"]
    record["environment"]["compiler"] = subprocess.check_output([cxx, "--version"], text=True).splitlines()[0]
    record["environment"]["compiler_flags"] = flags
    subprocess.run([cxx, *flags, str(HERE / "evolve.cpp"), "-o", str(executable)], check=True)
    record["environment"]["solver_sha256"] = sha256(executable)
    put_json(out / "record.json", record)

    def measure_case(name, case):
        directory = scratch / name
        directory.mkdir()
        save(name, {"status": "running", "reason": "started; no final outcome written yet"})
        try:
            if case["kind"] == "flow":
                details = run_flow(executable, out, directory, name, case, plan["protocol"])
            else:
                file = out / (name + ".json")
                put_json(file, calculate(plan["reference"], case))
                details = {"artifacts": {file.name: sha256(file)}}
            outcome = {"status": "completed", **details}
        except Exception as exc:
            outcome = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}", "artifacts": {}}
            for partial in ("solver.log", "ledger.csv", "faces.csv", "cuts.f32"):
                if (directory / partial).is_file():
                    artifact = out / f"{name}-{partial}.gz"
                    artifact.write_bytes(gzip.compress((directory / partial).read_bytes(), mtime=0))
                    outcome["artifacts"][artifact.name] = sha256(artifact)
        save(name, outcome)
        print(name, outcome["status"], outcome.get("reason", ""), flush=True)
        return outcome["status"]

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(measure_case, name, case) for name, case in plan["cases"].items()]
        outcomes = [f.result() for f in as_completed(futures)]
    return int(any(status != "completed" for status in outcomes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registered-at", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--jobs", default=4, type=int)
    parser.add_argument("--cxx", default=os.environ.get("CXX", "c++"))
    args = parser.parse_args()
    return run(args.out.resolve(), args.scratch.resolve(), args.registered_at, args.jobs, args.cxx)


if __name__ == "__main__":
    raise SystemExit(main())
