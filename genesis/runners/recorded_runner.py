"""Recorded adapter for the common Genesis Runner.

It uses the exact model steppers, mode sizes and diagnostic functions from `runner.py`,
while adding read-only display snapshots through FieldRecorder. Recording never feeds
back into the simulation and therefore cannot change the final checksum.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

from genesis.diagnostics import measures
from genesis.recording.recorder import FieldRecorder
from genesis.runners import runner


def run_recorded(
    genesis: dict[str, Any],
    *,
    mode: str = "2d-screen",
    quick: bool = False,
    target: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    if mode not in runner.MODES:
        raise ValueError(f"unknown runner mode {mode!r}")
    model = runner.MODELS[genesis["model"]]
    dim, edge, steps, nsnap = (runner.QUICK_MODES if quick else runner.MODES)[mode]
    shape = tuple([edge] * dim)
    p = dict(model.DEFAULTS)
    ist = genesis.get("initial_state", {})
    if "noise_amplitude" in ist:
        p["noise_amplitude"] = ist["noise_amplitude"]
    proto = (genesis.get("protocol") or {}).get("quench")
    if proto:
        p["quench_start"] = proto.get("start", p["quench_start"])
        p["quench_duration"] = proto.get("duration", p["quench_duration"])

    rng = np.random.default_rng(genesis.get("seed", 0))
    psi = model.make_initial(shape, p["noise_amplitude"], rng)
    display_target = target or ((48, 48) if dim == 2 else (28, 28, 28))
    recorder = (
        FieldRecorder(dim, display_target)
        .declare("phase", "arg(psi)", "rad", cyclic=True)
        .declare("density", "abs(psi)^2", "n")
    )

    traj: list[dict[str, Any]] = []
    snap_every = max(1, steps // nsnap)
    f0 = model.free_energy(psi, p)
    for step in range(steps):
        psi = model.step(psi, step * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            raise FloatingPointError(f"non-finite field at step {step} ({mode})")
        if step % snap_every == 0 or step == steps - 1:
            _, skprom = measures.structure_factor_peak(psi)
            traj.append(
                {
                    "step": step,
                    "mean_amp": measures.mean_amplitude(psi),
                    "var": measures.amplitude_variance(psi),
                    "sk_prom": skprom,
                    "defects": measures.winding_defect_count(psi),
                }
            )
            recorder.add(step * p["dt"], {"phase": np.angle(psi), "density": np.abs(psi) ** 2})
    f1 = model.free_energy(psi, p)

    reached, detected, measured_by = measures.assess_level(traj)
    genesis_for_record = copy.deepcopy(genesis)
    genesis_for_record["dimension"] = dim
    genesis_for_record.setdefault("domain", {})["size"] = list(shape)
    manifest = {
        "run_id": "%s-%s-seed%04d" % (genesis["model"], mode, genesis.get("seed", 0)),
        "room_id": genesis.get("room_id", "room-scratch"),
        "seed": int(genesis.get("seed", 0)),
        "dimension": dim,
        "mode": mode,
        "manifest": {
            "genesis": runner._genesis_checksum(genesis_for_record),
            "solver": genesis["model"],
            "steps": steps,
            "dt": p["dt"],
            "grid": list(shape),
            "code_version": runner.CODE_VERSION,
        },
        "summary": {
            "reached_level": reached,
            "conservation_drift": round(float(f1 - f0), 6),
            "final_mean_amplitude": round(traj[-1]["mean_amp"], 6),
        },
        "checksum": {"final_field_sha256": runner._checksum(psi)},
    }
    emergence = {
        "reached_level": reached,
        "candidate_level": min(reached + 1, 8),
        "uninterrupted_from_zero": True,
        "level_detected_by_measurement": True,
        "detected": detected,
        "measured_by": {
            key: float(value) if isinstance(value, np.floating) else value
            for key, value in measured_by.items()
        },
        "purity": {"per_object_labels": False, "external_optimum": False, "role": "E" if reached >= 1 else "F"},
        "natural_emergence": {
            "started_from_time_zero": True,
            "target_shape_seeded": False,
            "runtime_interventions": 0,
            "target_dependent_rules": False,
            "target_dependent_stopping": False,
            "target_dependent_clipping": False,
            "level_detected_by_measurement": True,
        },
    }
    return {
        "manifest": manifest,
        "emergence": emergence,
        "traj": traj,
        "recorder": recorder,
        "genesis": genesis_for_record,
    }
