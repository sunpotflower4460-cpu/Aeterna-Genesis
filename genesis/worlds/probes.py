"""Small common-format probes for registered Worlds.

These probes are deliberately observational: they never assign an official Emergence Level, never
promote a Room, and never compare unlike observables as a single success score.  Their purpose is to
make heterogeneous law classes inspectable by one research director while retaining each law's own
physics and integrity quantities.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from genesis.diagnostics import measures
from genesis.models import ginzburg_landau as gl
from genesis.models import model_h
from genesis.models import q_tensor_nematic as q2
from genesis.models import vector_o3 as o3
from .registry import get_world
from .zero_registry import get_zero


def _correlated_noise(shape: tuple[int, ...], rng: np.random.Generator, corr: float, *, complex_: bool) -> np.ndarray:
    base = rng.standard_normal(shape)
    if complex_:
        base = base + 1j * rng.standard_normal(shape)
    f = np.fft.fftn(base)
    ks = [np.fft.fftfreq(n) * n for n in shape]
    grids = np.meshgrid(*ks, indexing="ij")
    k2 = sum(g * g for g in grids)
    f *= np.exp(-0.5 * corr * corr * (2.0 * np.pi / max(shape)) ** 2 * k2)
    out = np.fft.ifftn(f)
    if not complex_:
        out = np.real(out)
    return out / (np.std(out) + 1e-30)


def _base_result(world_id: str, zero_id: str, seed: int) -> dict[str, Any]:
    world = get_world(world_id)
    zero = get_zero(zero_id)
    return {
        "world_id": world_id,
        "world_label": world.label,
        "zero_id": zero_id,
        "zero_purity_class": zero.purity_class,
        "seed": int(seed),
        "role": world.role,
        "causal_closure": world.causal_closure,
        "official_emergence_level": None,
        "promotion_effect": False,
        "claim_tier": "observed",
        "target_encoded": False,
    }


def _probe_g001(zero_id: str, seed: int, quick: bool) -> dict[str, Any]:
    if zero_id not in {"Z-A", "Z-B"}:
        raise ValueError("g001 shadow probe currently supports Z-A/Z-B")
    shape = (40, 40) if quick else (80, 80)
    steps = 180 if quick else 480
    p = dict(gl.DEFAULTS)
    rng = np.random.default_rng(seed)
    if zero_id == "Z-A":
        psi = gl.make_initial(shape, p["noise_amplitude"], rng)
    else:
        psi = (p["noise_amplitude"] * _correlated_noise(shape, rng, 4.0, complex_=True)).astype(np.complex128)
    initial_amp = measures.mean_amplitude(psi)
    initial_energy = gl.free_energy(psi, p)
    for i in range(steps):
        psi = gl.step(psi, i * p["dt"], p)
        if not np.isfinite(psi).all():
            return {**_base_result("g001-tdgl", zero_id, seed), "finite": False, "metrics": {}, "events": []}
    _, prom = measures.structure_factor_peak(psi)
    final_amp = measures.mean_amplitude(psi)
    defects = measures.winding_defect_count(psi)
    return {
        **_base_result("g001-tdgl", zero_id, seed),
        "finite": True,
        "physical_time": steps * p["dt"],
        "metrics": {
            "mean_amplitude_initial": initial_amp,
            "mean_amplitude_final": final_amp,
            "mean_amplitude_growth": final_amp / (initial_amp + 1e-30),
            "structure_factor_prominence": prom,
            "winding_defect_count": defects,
            "quench_independent_energy_initial": initial_energy,
            "quench_independent_energy_final": gl.free_energy(psi, p),
        },
        "events": [
            x for x, yes in (
                ("symmetry_breaking_signal", final_amp > 5.0 * initial_amp),
                ("winding_defects_present", defects > 0),
            ) if yes
        ],
        "integrity": {"boundary": "periodic", "dt": p["dt"], "dx": 1.0, "resolution": list(shape)},
    }


def _probe_g003(zero_id: str, seed: int, quick: bool) -> dict[str, Any]:
    if zero_id != "Z-A":
        raise ValueError("g003 shadow probe currently supports Z-A")
    N = 40 if quick else 80
    steps = 220 if quick else 700
    dt = model_h.DEFAULTS["dt"]
    r = model_h.run(N, steps, dt=dt, seed=seed, coupling=1.0, snapshots=6)
    tr = r["traj"]
    base = _base_result("g003-model-h", zero_id, seed)
    if not r["finite"] or len(tr) < 2:
        return {**base, "finite": False, "metrics": {}, "events": []}
    first, last = tr[0], tr[-1]
    mass_drift = abs(float(last["mass"]) - float(first["mass"]))
    return {
        **base,
        "finite": True,
        "physical_time": steps * dt,
        "metrics": {
            "phase_amplitude_initial": first["amp"],
            "phase_amplitude_final": last["amp"],
            "structure_scale_initial": first["scale"],
            "structure_scale_final": last["scale"],
            "kinetic_energy_final": last["ke"],
            "mass_drift": mass_drift,
            "free_energy_initial": first["F"],
            "free_energy_final": last["F"],
        },
        "events": [
            x for x, yes in (
                ("phase_separation_signal", float(last["amp"]) > 3.0 * max(float(first["amp"]), 1e-12)),
                ("flow_generated", float(last["ke"]) > 1e-10),
            ) if yes
        ],
        "integrity": {
            "boundary": "bi-periodic",
            "dt": dt,
            "resolution": [N, N],
            "mass_conservation_error": mass_drift,
            "free_energy_nonincreasing_endpoints": bool(float(last["F"]) <= float(first["F"]) + 1e-8),
        },
    }


def _probe_o3(zero_id: str, seed: int, quick: bool) -> dict[str, Any]:
    if zero_id not in {"Z-A", "Z-B"}:
        raise ValueError("O(3) probe currently supports Z-A/Z-B")
    shape = (40, 40) if quick else (80, 80)
    p = dict(o3.DEFAULTS)
    steps = 200 if quick else 520
    rng = np.random.default_rng(seed)
    if zero_id == "Z-A":
        phi = o3.make_initial(shape, p["noise_amplitude"], rng)
    else:
        comps = [_correlated_noise(shape, rng, 4.0, complex_=False) for _ in range(3)]
        phi = (p["noise_amplitude"] * np.stack(comps, axis=-1)).astype(np.float64)
    first = o3.metrics(phi)
    for i in range(steps):
        phi = o3.step(phi, i * p["dt"], p)
        if not np.isfinite(phi).all():
            return {**_base_result("o3-vector", zero_id, seed), "finite": False, "metrics": {}, "events": []}
    last = o3.metrics(phi)
    return {
        **_base_result("o3-vector", zero_id, seed),
        "finite": True,
        "physical_time": steps * p["dt"],
        "metrics": {**{f"initial_{k}": v for k, v in first.items()}, **{f"final_{k}": v for k, v in last.items()}},
        "events": ["vector_order_amplitude_grew"] if last["mean_magnitude"] > 5.0 * first["mean_magnitude"] else [],
        "integrity": {"boundary": "periodic", "dt": p["dt"], "dx": 1.0, "resolution": list(shape)},
    }


def _probe_q2(zero_id: str, seed: int, quick: bool) -> dict[str, Any]:
    if zero_id not in {"Z-A", "Z-B"}:
        raise ValueError("Q2 probe currently supports Z-A/Z-B")
    shape = (40, 40) if quick else (80, 80)
    p = dict(q2.DEFAULTS)
    steps = 220 if quick else 560
    rng = np.random.default_rng(seed)
    if zero_id == "Z-A":
        q = q2.make_initial(shape, p["noise_amplitude"], rng)
    else:
        comps = [_correlated_noise(shape, rng, 4.0, complex_=False) for _ in range(2)]
        q = (p["noise_amplitude"] * np.stack(comps, axis=-1)).astype(np.float64)
    first = q2.metrics(q)
    for i in range(steps):
        q = q2.step(q, i * p["dt"], p)
        if not np.isfinite(q).all():
            return {**_base_result("q2-nematic", zero_id, seed), "finite": False, "metrics": {}, "events": []}
    last = q2.metrics(q)
    return {
        **_base_result("q2-nematic", zero_id, seed),
        "finite": True,
        "physical_time": steps * p["dt"],
        "metrics": {**{f"initial_{k}": v for k, v in first.items()}, **{f"final_{k}": v for k, v in last.items()}},
        "events": ["nematic_tensor_amplitude_grew"] if last["mean_tensor_amplitude"] > 5.0 * first["mean_tensor_amplitude"] else [],
        "integrity": {
            "boundary": "periodic",
            "dt": p["dt"],
            "dx": 1.0,
            "resolution": list(shape),
            **q2.tensor_invariants(q),
        },
    }


_PROBES = {"g001": _probe_g001, "g003": _probe_g003, "o3": _probe_o3, "q2": _probe_q2}


def probe_world(world_id: str, *, zero_id: str | None = None, seed: int = 0, quick: bool = True) -> dict[str, Any]:
    world = get_world(world_id)
    if not world.runnable_probe:
        raise ValueError(f"world {world_id} has no validated shadow probe adapter yet")
    chosen_zero = zero_id or world.zero_ids[0]
    if chosen_zero not in world.zero_ids:
        raise ValueError(f"zero {chosen_zero} is not declared for world {world_id}")
    return _PROBES[world.runnable_probe](chosen_zero, int(seed), bool(quick))
