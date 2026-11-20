"""Repeat the stop test in the early wake with a norm-preserving split step."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from pathlib import Path
import platform
import sys
from threading import Lock

import numpy as np
import scipy
from scipy.fft import fftn, ifftn

from tools.study_record import load_plan, sha256, verify_registration

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261120-vortex-drive-stop"))
from analyze import phase_crossings
from run import initial_field, put_json

PLAN = HERE / "PLAN.json"


def boundary(t, mode, protocol):
    height, rise, start, speed = 5.0, 0.0, 30.0, 0.68
    split = protocol["brake_start"]
    brake = protocol["brake_end"] - split
    if t < 16:
        q = np.pi * t / 16
        return start, 0.0, height * (1 - np.cos(q)) / 2, height * np.pi * np.sin(q) / 32
    if t < 40:
        q = np.pi * (t - 16) / 24
        return start + speed * ((t - 16) - 24 / np.pi * np.sin(q)) / 2, speed * (1 - np.cos(q)) / 2, height, rise
    if mode == "continue" or t < split:
        return start + speed * (t - 28), speed, height, rise
    used = min(t - split, brake)
    q = np.pi * used / brake
    center = start + speed * (split - 28 + (used + brake / np.pi * np.sin(q)) / 2)
    velocity = speed * (1 + np.cos(q)) / 2
    if mode == "release" and t >= protocol["brake_end"]:
        fade = protocol["release_end"] - protocol["brake_end"]
        q = np.pi * min(t - protocol["brake_end"], fade) / fade
        height = 2.5 * (1 + np.cos(q))
        rise = 0.0 if t >= protocol["release_end"] else -2.5 * np.pi / fade * np.sin(q)
    return center, velocity, height, rise


class Obstacle:
    def __init__(self, shape, dx, mode, protocol):
        nx, ny, nz = shape
        x = self.profile(dx * (np.arange(nx) - nx // 2), dx * nx)[0]
        y = self.profile(dx * (np.arange(ny) - ny // 2), dx * ny)[0]
        self.xy = np.multiply.outer(x, y)
        self.z = dx * np.arange(nz)
        self.length = dx * nz
        self.mode = mode
        self.protocol = protocol

    @staticmethod
    def profile(separation, period):
        offsets = (separation + period / 2) % period - period / 2
        offsets = offsets[:, None] + period * np.arange(-1, 2)
        contributions = np.exp(-0.5 * (offsets / 2.5)**2)
        return contributions.sum(axis=1), (offsets * contributions).sum(axis=1) / 2.5**2

    def sample(self, t):
        center, speed, height, rise = motion = boundary(t, self.mode, self.protocol)
        profile, shifted = self.profile(self.z - center, self.length)
        return motion, height * profile, rise * profile + height * speed * shifted


def digest(psi):
    return hashlib.sha256(psi.astype("<c16", copy=False).tobytes()).hexdigest()


def kinetic_phase(shape, dx, dt):
    # The three eigenvalues of -D_jj/2 sum to the discrete stencil energy.
    axes = [2 * (np.sin(np.pi * np.fft.fftfreq(n)) / dx)**2 for n in shape]
    total = axes[0][:, None, None] + axes[1][None, :, None] + axes[2][None, None, :]
    return np.exp(-1j * dt * total)


def evolve(case, protocol, out):
    shape, dx, dt = case["shape"], case["dx"], case["dt"]
    psi = initial_field(case)
    obstacle = Obstacle(shape, dx, case["mode"], protocol)
    multiplier = kinetic_phase(shape, dx, dt)
    steps = round(protocol["duration"] / dt)
    stride = round(protocol["interval"] / dt)
    cuts, faces, records, states = [], [], [], {}
    hashes = {"initial_sha256": digest(psi)}
    work = 0.0
    density = np.abs(psi)**2
    volume = dx**3

    def power(n, height_rate):
        if not height_rate.any():
            return 0.0
        return float(volume * np.einsum("ij,ijk,k->", obstacle.xy, n, height_rate))

    motion, axial, height_rate = obstacle.sample(0)
    previous_power = power(density, height_rate)
    for step in range(steps + 1):
        t = step * dt
        if t in protocol["cuts"]:
            cuts.append(density[shape[0] // 2].astype("<f4"))
        if t in (protocol["brake_start"], protocol["brake_end"]):
            hashes[f"state_t{t:.0f}_sha256"] = digest(psi)
        if case["seed"] == 92301 and case["variant"] == "base" and case["mode"] == "release" and t in (58, 160):
            states[f"t{t:.0f}"] = psi.copy()
        if step % stride == 0:
            grad = sum(float(np.square(np.abs(np.roll(psi, -1, ax) - psi)).sum()) for ax in range(3))
            contact = float(0.5 * np.square(density - 1).sum())
            external = float(np.einsum("ij,ijk,k->", obstacle.xy, density, axial))
            value = volume * (0.5 * grad / dx**2 + contact + external)
            current_mass = float(volume * density.sum())
            if not np.isfinite([work, value, current_mass]).all():
                raise ValueError(f"nonfinite state at t={t}")
            records.append((t, *motion[:3], work, 0.0, value, current_mass, previous_power))
            faces.extend((step // stride, *face) for face in phase_crossings(psi))
        if step == steps:
            break
        middle_axial = obstacle.sample(t + dt / 2)[1]
        half = (-0.5j * dt)
        potential = obstacle.xy[:, :, None] * middle_axial if middle_axial.any() else 0.0
        field = psi * np.exp(half * (density - 1 + potential))
        field = ifftn(multiplier * fftn(field, workers=1), workers=1, overwrite_x=True)
        density = np.abs(field)**2
        psi = field * np.exp(half * (density - 1 + potential))
        motion, axial, height_rate = obstacle.sample((step + 1) * dt)
        next_power = power(density, height_rate)
        work += dt / 2 * (previous_power + next_power)
        previous_power = next_power

    np.savez_compressed(
        out, shape=shape, dx=dx, dt=dt, cut_times=protocol["cuts"], cuts=np.array(cuts),
        faces=np.array(faces, dtype=np.int32).reshape(-1, 6),
        ledger_columns=["t", "obstacle_z", "speed", "height", "work", "heat", "energy", "mass", "power"],
        ledger=np.array(records),
    )
    artifacts = [out]
    if states:
        volume_file = out.with_stem(out.stem + "-volumes")
        np.savez_compressed(volume_file, **states)
        artifacts.append(volume_file)
    return hashes | {"artifacts": {p.name: sha256(p) for p in artifacts}}


def run(out, registration, jobs):
    plan = load_plan(PLAN)
    verify_registration(PLAN, plan, registration)
    out.mkdir(parents=True, exist_ok=False)
    record = {
        "registration_commit": registration,
        "environment": {
            "platform": platform.platform(), "python": sys.version.split()[0],
            "numpy": np.__version__, "scipy": scipy.__version__,
        },
        "cases": {name: [{"status": "not_run", "reason": "not started"}] for name in plan["cases"]},
    }
    lock = Lock()

    def save(name, result):
        with lock:
            record["cases"][name][-1] = result
            put_json(out / "record.json", record)

    put_json(out / "record.json", record)

    def measure(name, case):
        save(name, {"status": "running", "reason": "started; no final outcome written yet"})
        output = out / f"{name}.npz"
        try:
            result = {"status": "completed", **evolve(case, plan["protocol"], output)}
        except Exception as exc:
            result = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}",
                      "artifacts": {output.name: sha256(output)} if output.is_file() else {}}
        save(name, result)
        print(name, result["status"], result.get("reason", ""), flush=True)
        return result["status"]

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(measure, name, case) for name, case in plan["cases"].items()]
        results = [f.result() for f in as_completed(futures)]
    return int(any(status != "completed" for status in results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registered-at", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    return run(args.out.resolve(), args.registered_at, args.jobs)


if __name__ == "__main__":
    raise SystemExit(main())
