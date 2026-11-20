"""Run the corrective early-stop comparison from a single exact checkpoint per fork."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
import importlib.util
from pathlib import Path
import platform
import sys
from threading import Lock

import numpy as np
import scipy

from tools.study_record import load_plan, sha256, verify_registration

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PAIRED_PLAN.json"
spec = importlib.util.spec_from_file_location("early_split_step", HERE / "run.py")
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)


@dataclass
class Checkpoint:
    psi: np.ndarray
    n: np.ndarray
    work: float = 0.0
    power: float = 0.0
    step: int = 0
    records: list = field(default_factory=list)
    cuts: list = field(default_factory=list)
    faces: list = field(default_factory=list)

    def fork(self):
        # Arrays from the parent are read-only here. Each advance allocates a new field.
        return replace(self, records=self.records.copy(), cuts=self.cuts.copy(), faces=self.faces.copy())


def advance(state, case, mode, protocol, stop, kinetic):
    shape, dx, dt = case["shape"], case["dx"], case["dt"]
    obstacle = solver.Obstacle(shape, dx, mode, protocol)
    stride = round(protocol["interval"] / dt)
    end = round(stop / dt)
    volume = dx**3
    motion, axial, rate = obstacle.sample(state.step * dt)

    def project(density, axial_weights):
        if not axial_weights.any():
            return 0.0
        return float(np.einsum("ij,ijk,k->", obstacle.xy, density, axial_weights))

    def record():
        t = state.step * dt
        psi, n = state.psi, state.n
        if t in protocol["cuts"]:
            state.cuts.append(n[shape[0] // 2].astype("<f4"))
        if state.step % stride:
            return
        gradient = sum(float(np.square(np.abs(np.roll(psi, -1, ax) - psi)).sum()) for ax in range(3))
        contact = float(0.5 * np.square(n - 1).sum())
        energy = volume * (0.5 * gradient / dx**2 + contact + project(n, axial))
        mass = float(volume * n.sum())
        if not np.isfinite([energy, mass, state.work]).all():
            raise ValueError(f"nonfinite state at t={t}")
        state.records.append((t, *motion[:3], state.work, 0.0, energy, mass, state.power))
        state.faces.extend((state.step // stride, *point) for point in solver.phase_crossings(psi))

    if not state.records:
        state.power = volume * project(state.n, rate)
        record()
    for step in range(state.step, end):
        multiplier = -0.5j * dt
        midpoint = obstacle.sample((step + 0.5) * dt)[1]
        potential = obstacle.xy[:, :, None] * midpoint if midpoint.any() else 0.0
        phase = np.exp(multiplier * (state.n - 1 + potential))
        psi_k = solver.fftn(state.psi * phase, workers=1)
        psi = solver.ifftn(kinetic * psi_k, workers=1, overwrite_x=True)
        state.n = np.abs(psi)**2
        state.psi = psi * np.exp(multiplier * (state.n - 1 + potential))
        motion, axial, rate = obstacle.sample((step + 1) * dt)
        next_power = volume * project(state.n, rate)
        state.work += dt / 2 * (state.power + next_power)
        state.power = next_power
        state.step = step + 1
        record()
    return state


def save_arrays(path, case, protocol, s):
    np.savez_compressed(
        path, shape=case["shape"], dx=case["dx"], dt=case["dt"],
        cut_times=protocol["cuts"], cuts=np.array(s.cuts),
        faces=np.array(s.faces, dtype=np.int32).reshape(-1, 6),
        ledger_columns=["t", "obstacle_z", "speed", "height", "work", "heat", "energy", "mass", "power"],
        ledger=np.array(s.records),
    )


def run(out, registration, jobs):
    plan = load_plan(PLAN)
    verify_registration(PLAN, plan, registration)
    out.mkdir(parents=True, exist_ok=False)
    table = {
        "registration_commit": registration,
        "environment": {"platform": platform.platform(), "python": sys.version.split()[0],
                        "numpy": np.__version__, "scipy": scipy.__version__},
        "cases": {name: [{"status": "not_run", "reason": "not started"}] for name in plan["cases"]},
    }
    lock = Lock()

    def note(name, record):
        with lock:
            table["cases"][name][-1] = record
            solver.put_json(out / "record.json", table)

    def fail(name, cause):
        note(name, {"status": "failed", "reason": f"{type(cause).__name__}: {cause}"})
        print(name, "failed", str(cause), flush=True)

    def measure_group(names):
        case = plan["cases"][names[0]]
        p = plan["protocol"]
        for name in names:
            note(name, {"status": "running", "reason": "common t=0 preparation started"})
        try:
            psi = solver.initial_field(case)
            init = solver.digest(psi)
            kinetic = solver.kinetic_phase(case["shape"], case["dx"], case["dt"])
            split = advance(Checkpoint(psi, np.abs(psi)**2), case, "continue", p, p["brake_start"], kinetic)
            split_hash = solver.digest(split.psi)
            brake = advance(split.fork(), case, "hold", p, p["brake_end"], kinetic)
            stopped_hash = solver.digest(brake.psi)
        except Exception as exc:
            for name in names:
                fail(name, exc)
            return False

        finished = True
        for name in names:
            try:
                mode = plan["cases"][name]["mode"]
                parent = split if mode == "continue" else brake
                result = advance(parent.fork(), case, mode, p, p["duration"], kinetic)
                files = [out / f"{name}.npz"]
                save_arrays(files[0], case, p, result)
                if name == "base-92301-release":
                    files.append(out / f"{name}-volumes.npz")
                    np.savez_compressed(files[-1], t58=split.psi, t70=brake.psi, t160=result.psi)
                metadata = {"status": "completed", "initial_sha256": init, "state_t58_sha256": split_hash,
                            "state_t70_sha256": stopped_hash if mode != "continue" else None,
                            "artifacts": {file.name: sha256(file) for file in files}}
                note(name, metadata)
                print(name, "completed", flush=True)
            except Exception as exc:
                fail(name, exc)
                finished = False
        return finished

    solver.put_json(out / "record.json", table)
    groups = defaultdict(list)
    for name, case in plan["cases"].items():
        groups[(case["variant"], case["seed"])].append(name)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        pending = [pool.submit(measure_group, names) for names in groups.values()]
        outcomes = [job.result() for job in as_completed(pending)]
    return int(not all(outcomes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registered-at", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--jobs", default=6, type=int)
    args = parser.parse_args()
    return run(args.out.resolve(), args.registered_at, args.jobs)


if __name__ == "__main__":
    raise SystemExit(main())
