"""Generate free-tracer displacements from the registered local jump law."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tools.study_record import load_plan, sha256, verify_registration


def diffusivity(plan, temperature):
    if temperature is None:
        return 0.0
    protocol = plan["protocol"]
    low, high = protocol["fit_temperatures_C"]
    first = plan["cases"][f"water-{low}"]["reference_D"] * protocol["reference_unit_m2_s"]
    last = plan["cases"][f"water-{high}"]["reference_D"] * protocol["reference_unit_m2_s"]
    weight = (1 / (temperature + 273.15) - 1 / (low + 273.15)) / (1 / (high + 273.15) - 1 / (low + 273.15))
    return first * math.exp(weight * math.log(last / first))


def displacements(protocol, temperature, coefficient):
    """Exact unwrapped positions at sampling times for independent, constant-rate jumps."""
    mean = coefficient * protocol["interval_s"] / protocol["spacing_m"] ** 2
    shape = (len(protocol["seeds"]), protocol["intervals"] + 1, protocol["tracers"], 3)
    positions = np.zeros(shape, dtype=np.int64)
    for index, seed in enumerate(protocol["seeds"]):
        rng = np.random.Generator(np.random.PCG64([seed, 0 if temperature is None else temperature]))
        for frame in range(1, shape[1]):
            plus = rng.poisson(mean, size=shape[2:])
            minus = rng.poisson(mean, size=shape[2:])
            positions[index, frame] = positions[index, frame - 1] + plus - minus
    return positions


def run(out, commit):
    path = HERE / "PLAN.json"
    plan = load_plan(path)
    verify_registration(path, plan, commit)
    out.mkdir(parents=True, exist_ok=False)
    record = {"registration_commit": commit,
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "rng": "PCG64"},
              "cases": {key: [{"status": "not_run", "reason": "waiting"}] for key in plan["cases"]}}

    def save():
        temp = out / "record.tmp"
        temp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(out / "record.json")

    save()
    for key, case in plan["cases"].items():
        attempt = record["cases"][key][0]
        attempt.update(status="running", reason="started; completion not yet recorded")
        save()
        try:
            temperature = case["temperature_C"]
            positions = displacements(plan["protocol"], temperature, diffusivity(plan, temperature))
            artifact = out / f"{key}.npz"
            np.savez_compressed(artifact, displacement_steps=positions)
            attempt.update(status="completed", artifacts={artifact.name: sha256(artifact)})
            del attempt["reason"]
        except (Exception, KeyboardInterrupt) as exc:
            attempt.update(status="stopped" if isinstance(exc, KeyboardInterrupt) else "failed",
                           reason=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="a new output directory")
    parser.add_argument("--registered-at", required=True, help="full Git ID of the registered plan and code")
    args = parser.parse_args()
    run(args.out, args.registered_at)
