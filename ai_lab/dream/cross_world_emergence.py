"""Cross-World Emergence Comparator for Multi-World Genesis.

The comparator searches for similarly shaped *observable transitions* across independently defined
Worlds.  A shared fingerprint is only a research-navigation lead: it never means identical physics,
universality, a higher Emergence Level, or Room promotion.

Important integrity rule: start purity is part of the evidence.  A scaffolded g001 X-pattern that
resembles a strict Z-A run elsewhere remains SIGNATURE_OVERLAP_ONLY.  Only a g001 pattern actually
seen from Z-A may become a CROSS_WORLD_ZERO_ALIGNED_LEAD, and even that is not a universality claim.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from genesis.models import ginzburg_landau as gl
from genesis.models import model_h
from genesis.models import q_tensor_nematic as q2
from genesis.models import vector_o3 as o3
from genesis.worlds.zero_registry import get_zero

_REPO = Path(__file__).resolve().parents[2]
_G001_LEDGER = _REPO / "ai_lab" / "discoveries" / "emergence_graph.json"
_LEDGER = _REPO / "ai_lab" / "discoveries" / "cross_world_emergence.json"
_REPORT = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"


def _storage_path(path: Path, *, for_write: bool = False) -> Path:
    """Honor the process dry-run root explicitly for comparator persistence.

    The generic dry-run I/O redirect remains the broad safety net, but this comparator owns two
    durable files and therefore resolves them explicitly as a second integrity barrier.
    """
    root = os.environ.get("AETERNA_DRY_RUN_ROOT")
    if not root:
        return path
    try:
        relative = path.resolve().relative_to(_REPO)
    except (OSError, ValueError):
        return path
    twin = Path(root) / relative
    if for_write:
        twin.parent.mkdir(parents=True, exist_ok=True)
        return twin
    return twin if twin.exists() else path


OBSERVABLE_DEFINITION_VERSION = 2
COMMON_FEATURES = (
    "order_mean",
    "order_std",
    "global_alignment",
    "spectral_entropy",
    "spectral_k_rms",
    "spectral_anisotropy",
    "spatial_gradient",
    "high_order_fraction",
)
_G001_TO_COMMON = {
    "mean_amp": "order_mean",
    "amp_std": "order_std",
    "phase_coherence": "global_alignment",
    "spectral_entropy": "spectral_entropy",
    "spectral_k_rms": "spectral_k_rms",
    "spectral_anisotropy": "spectral_anisotropy",
    "gradient_rms": "spatial_gradient",
    "high_amp_fraction": "high_order_fraction",
}


def _correlated_noise(shape: tuple[int, int], rng: np.random.Generator, corr: float, *, complex_: bool) -> np.ndarray:
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


def _magnitude(field: np.ndarray, kind: str) -> np.ndarray:
    arr = np.asarray(field)
    if kind in {"complex", "scalar"}:
        return np.abs(arr)
    if kind in {"vector", "nematic"}:
        return np.linalg.norm(arr, axis=-1)
    raise ValueError(f"unsupported common observable kind: {kind}")


def _alignment(field: np.ndarray, mag: np.ndarray, kind: str) -> float:
    """Amplitude-weighted global alignment, matching g001 phase_coherence semantics.

    complex/scalar: |mean(field)| / mean(|field|)
    vector/nematic: ||mean(component vector)|| / mean(component magnitude)
    """
    denom = float(np.mean(mag))
    if denom <= 1e-30:
        return 0.0
    arr = np.asarray(field)
    if kind in {"complex", "scalar"}:
        return float(abs(np.mean(arr)) / denom)
    axes = tuple(range(arr.ndim - 1))
    return float(np.linalg.norm(np.mean(arr, axis=axes)) / denom)


def _spectral_features(mag: np.ndarray) -> tuple[float, float, float]:
    """Spectrum of order magnitude, matching g001 open-ended spectral features."""
    field = np.asarray(mag, dtype=float) - float(np.mean(mag))
    power = np.abs(np.fft.fftn(field)) ** 2
    if power.size:
        power.flat[0] = 0.0
    total = float(power.sum())
    if not math.isfinite(total) or total <= 1e-30:
        return 0.0, 0.0, 0.0
    p = (power / total).ravel()
    nz = p[p > 0]
    entropy = float(-(nz * np.log(nz)).sum() / max(math.log(len(p)), 1.0))
    ky = np.fft.fftfreq(field.shape[0])[:, None]
    kx = np.fft.fftfreq(field.shape[1])[None, :]
    k2 = kx * kx + ky * ky
    k_rms = float(math.sqrt(max(0.0, float((power * k2).sum() / total))))
    denom = float((power * k2).sum())
    anis = 0.0 if denom <= 1e-30 else float(abs((power * (kx * kx - ky * ky)).sum()) / denom)
    return entropy, k_rms, anis


def _field_gradient(field: np.ndarray, kind: str) -> float:
    """RMS spatial gradient of the actual order field, not only of its magnitude.

    This is chosen so g001 exactly follows its existing gradient_rms definition.  For vector/tensor
    fields, component-wise differences are summed before the spatial mean.
    """
    arr = np.asarray(field)
    gy = np.roll(arr, -1, axis=0) - arr
    gx = np.roll(arr, -1, axis=1) - arr
    if kind in {"complex", "scalar"}:
        local = np.abs(gx) ** 2 + np.abs(gy) ** 2
    else:
        local = np.sum(gx * gx + gy * gy, axis=-1)
    return float(np.sqrt(np.mean(local)))


def _snapshot(field: np.ndarray, *, kind: str, physical_time: float) -> dict[str, float]:
    mag = _magnitude(field, kind)
    mean = float(np.mean(mag))
    std = float(np.std(mag))
    entropy, k_rms, anis = _spectral_features(mag)
    return {
        "physical_time": float(physical_time),
        "order_mean": mean,
        "order_std": std,
        "global_alignment": _alignment(field, mag, kind),
        "spectral_entropy": entropy,
        "spectral_k_rms": k_rms,
        "spectral_anisotropy": anis,
        "spatial_gradient": _field_gradient(field, kind),
        "high_order_fraction": float(np.mean(mag > mean + std)),
    }


def _recorded_run(*, world_id: str, zero_id: str, seed: int, quick: bool) -> dict[str, Any]:
    if world_id == "g001-tdgl":
        shape, steps = ((40, 40), 180) if quick else ((80, 80), 480)
        p = dict(gl.DEFAULTS)
        rng = np.random.default_rng(seed)
        if zero_id == "Z-A":
            field = gl.make_initial(shape, p["noise_amplitude"], rng)
        elif zero_id == "Z-B":
            field = (p["noise_amplitude"] * _correlated_noise(shape, rng, 4.0, complex_=True)).astype(np.complex128)
        else:
            raise ValueError("g001 common probe supports Z-A/Z-B")
        snaps = [_snapshot(field, kind="complex", physical_time=0.0)]
        every = max(1, steps // 18)
        for i in range(1, steps + 1):
            field = gl.step(field, (i - 1) * p["dt"], p)
            if not np.isfinite(field).all():
                return {"finite": False, "snapshots": snaps}
            if i % every == 0 or i == steps:
                snaps.append(_snapshot(field, kind="complex", physical_time=i * p["dt"]))
        analysis_start = max(float(p.get("quench_duration", 0.0)), steps * p["dt"] * 0.2)

    elif world_id == "g003-model-h":
        if zero_id != "Z-A":
            raise ValueError("Model H common probe supports Z-A")
        N, steps = (40, 220) if quick else (80, 700)
        dt = float(model_h.DEFAULTS["dt"])
        solver = model_h.ModelH(N, seed=seed, coupling=1.0)
        snaps = [_snapshot(solver.phi(), kind="scalar", physical_time=0.0)]
        every = max(1, steps // 18)
        for i in range(1, steps + 1):
            solver.step(dt)
            if not solver.finite():
                return {"finite": False, "snapshots": snaps}
            if i % every == 0 or i == steps:
                snaps.append(_snapshot(solver.phi(), kind="scalar", physical_time=i * dt))
        # No externally imposed time-dependent quench in this Model H implementation.
        analysis_start = steps * dt * 0.1

    elif world_id == "o3-vector":
        shape, steps = ((40, 40), 200) if quick else ((80, 80), 520)
        p = dict(o3.DEFAULTS)
        rng = np.random.default_rng(seed)
        if zero_id == "Z-A":
            field = o3.make_initial(shape, p["noise_amplitude"], rng)
        elif zero_id == "Z-B":
            comps = [_correlated_noise(shape, rng, 4.0, complex_=False) for _ in range(3)]
            field = (p["noise_amplitude"] * np.stack(comps, axis=-1)).astype(np.float64)
        else:
            raise ValueError("O(3) common probe supports Z-A/Z-B")
        snaps = [_snapshot(field, kind="vector", physical_time=0.0)]
        every = max(1, steps // 18)
        for i in range(1, steps + 1):
            field = o3.step(field, (i - 1) * p["dt"], p)
            if not np.isfinite(field).all():
                return {"finite": False, "snapshots": snaps}
            if i % every == 0 or i == steps:
                snaps.append(_snapshot(field, kind="vector", physical_time=i * p["dt"]))
        analysis_start = max(float(p.get("quench_duration", 0.0)), steps * p["dt"] * 0.2)

    elif world_id == "q2-nematic":
        shape, steps = ((40, 40), 220) if quick else ((80, 80), 560)
        p = dict(q2.DEFAULTS)
        rng = np.random.default_rng(seed)
        if zero_id == "Z-A":
            field = q2.make_initial(shape, p["noise_amplitude"], rng)
        elif zero_id == "Z-B":
            comps = [_correlated_noise(shape, rng, 4.0, complex_=False) for _ in range(2)]
            field = (p["noise_amplitude"] * np.stack(comps, axis=-1)).astype(np.float64)
        else:
            raise ValueError("Q2 common probe supports Z-A/Z-B")
        snaps = [_snapshot(field, kind="nematic", physical_time=0.0)]
        every = max(1, steps // 18)
        for i in range(1, steps + 1):
            field = q2.step(field, (i - 1) * p["dt"], p)
            if not np.isfinite(field).all():
                return {"finite": False, "snapshots": snaps}
            if i % every == 0 or i == steps:
                snaps.append(_snapshot(field, kind="nematic", physical_time=i * p["dt"]))
        analysis_start = max(float(p.get("quench_duration", 0.0)), steps * p["dt"] * 0.2)

    else:
        raise ValueError(f"world {world_id} has no common-observable probe")

    return {"finite": True, "analysis_start_time": float(analysis_start), "snapshots": snaps}


def common_probe(world_id: str, *, zero_id: str, seed: int, quick: bool = True) -> dict[str, Any]:
    out = _recorded_run(world_id=world_id, zero_id=zero_id, seed=int(seed), quick=bool(quick))
    zero = get_zero(zero_id)
    return {
        "world_id": world_id,
        "zero_id": zero_id,
        "seed": int(seed),
        "zero_purity_class": zero.purity_class,
        "strict_zero_candidate": bool(zero.strict_zero_candidate),
        "imposed_length_scale": bool(zero.imposed_length_scale),
        "observable_definition_version": OBSERVABLE_DEFINITION_VERSION,
        **out,
    }


def _robust_scales(matrix: np.ndarray) -> np.ndarray:
    q10 = np.nanpercentile(matrix, 10.0, axis=0)
    q90 = np.nanpercentile(matrix, 90.0, axis=0)
    span = q90 - q10
    fallback = np.nanmax(np.abs(matrix), axis=0)
    return np.maximum(span, np.maximum(fallback * 1e-6, 1e-9))


def _bucket(x: float) -> str:
    return "S" if x < 0.35 else ("M" if x < 0.8 else "L")


def _fingerprint(delta: np.ndarray) -> str | None:
    ranked = sorted(range(len(COMMON_FEATURES)), key=lambda i: abs(float(delta[i])), reverse=True)
    parts: list[str] = []
    for i in ranked:
        value = float(delta[i])
        if abs(value) < 0.15:
            continue
        parts.append(f"{COMMON_FEATURES[i]}:{'+' if value > 0 else '-'}{_bucket(abs(value))}")
        if len(parts) >= 5:
            break
    return "|".join(sorted(parts)) if parts else None


def detect_common_episodes(probe: dict[str, Any], *, max_episodes: int = 3) -> list[dict[str, Any]]:
    snaps = probe.get("snapshots") or []
    if len(snaps) < 4 or max_episodes <= 0:
        return []
    matrix = np.asarray([[float(s[k]) for k in COMMON_FEATURES] for s in snaps], dtype=float)
    if not np.isfinite(matrix).all():
        return []
    delta = np.diff(matrix, axis=0) / _robust_scales(matrix)
    scores = np.sqrt(np.mean(np.clip(delta, -5.0, 5.0) ** 2, axis=1))
    eligible = [
        i for i in range(len(scores))
        if float(snaps[i + 1]["physical_time"]) >= float(probe.get("analysis_start_time", 0.0))
    ]
    if not eligible:
        return []
    vals = np.asarray([scores[i] for i in eligible])
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med)))
    threshold = max(0.18, med + 2.5 * max(mad, 1e-6))
    chosen: list[int] = []
    for i in sorted(eligible, key=lambda j: float(scores[j]), reverse=True):
        if float(scores[i]) < threshold or any(abs(i - j) <= 1 for j in chosen):
            continue
        chosen.append(i)
        if len(chosen) >= max_episodes:
            break
    episodes: list[dict[str, Any]] = []
    for i in sorted(chosen):
        fp = _fingerprint(delta[i])
        if not fp:
            continue
        episodes.append({
            "pattern_id": "CWX-" + hashlib.sha256(fp.encode()).hexdigest()[:10],
            "fingerprint": fp,
            "change_score": round(float(scores[i]), 6),
            "physical_time": float(snaps[i + 1]["physical_time"]),
            "world_id": probe.get("world_id"),
            "zero_id": probe.get("zero_id"),
            "seed": probe.get("seed"),
            "zero_purity_class": probe.get("zero_purity_class"),
            "strict_zero_candidate": bool(probe.get("strict_zero_candidate")),
            "imposed_length_scale": bool(probe.get("imposed_length_scale")),
        })
    return episodes


def project_g001_fingerprint(fingerprint: str | None) -> dict[str, Any]:
    raw = [p for p in str(fingerprint or "").split("|") if p]
    mapped: list[str] = []
    dropped: list[str] = []
    for part in raw:
        if ":" not in part:
            dropped.append(part)
            continue
        name, suffix = part.split(":", 1)
        common = _G001_TO_COMMON.get(name)
        if common:
            mapped.append(f"{common}:{suffix}")
        else:
            dropped.append(part)
    mapped = sorted(set(mapped))
    return {
        "fingerprint": "|".join(mapped) if mapped else None,
        "coverage": 0.0 if not raw else len(mapped) / len(raw),
        "mapped_parts": mapped,
        "dropped_parts": dropped,
    }


def _load_json(path: Path, fallback: Any) -> Any:
    path = _storage_path(path, for_write=False)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return fallback


def _g001_purities(ledger: dict[str, Any], pattern_id: str, pattern: dict[str, Any]) -> list[str]:
    values = [
        str(e.get("zero_purity")) for e in ledger.get("recent_episodes") or []
        if e.get("pattern_id") == pattern_id and e.get("zero_purity")
    ]
    rep = pattern.get("representative") or {}
    if rep.get("zero_purity"):
        values.append(str(rep["zero_purity"]))
    return list(dict.fromkeys(values))


def _strict_alignment(source_purities: list[str], targets: list[dict[str, Any]]) -> bool:
    source_za = any(x.startswith("Z-A:") for x in source_purities)
    target_za = any(e.get("zero_id") == "Z-A" and e.get("strict_zero_candidate") for e in targets)
    return bool(source_za and target_za)


def _update_cross_ledger(*, burst_id: str, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = _load_json(_LEDGER, {"version": 1, "patterns": []})
    patterns = {p["pattern_id"]: p for p in ledger.get("patterns") or []}
    for e in episodes:
        p = patterns.setdefault(e["pattern_id"], {
            "pattern_id": e["pattern_id"], "fingerprint": e["fingerprint"], "observations": 0,
            "worlds": [], "zeros": [], "seeds": [], "first_burst": burst_id,
        })
        p["last_burst"] = burst_id
        p["observations"] = int(p.get("observations", 0)) + 1
        p["worlds"] = list(dict.fromkeys([*(p.get("worlds") or []), e.get("world_id")]))[-16:]
        p["zeros"] = list(dict.fromkeys([*(p.get("zeros") or []), f"{e.get('world_id')}@{e.get('zero_id')}"]))[-32:]
        p["seeds"] = list(dict.fromkeys([*(p.get("seeds") or []), int(e.get("seed") or 0)]))[-64:]
        nw = len(p["worlds"])
        p["status"] = "MULTI_WORLD_RECURRENT_SIGNATURE" if nw >= 3 else (
            "CROSS_WORLD_RECURRENT_SIGNATURE" if nw >= 2 else "SINGLE_WORLD_SIGNATURE"
        )
    ledger.update({
        "patterns": sorted(
            patterns.values(),
            key=lambda p: (len(p.get("worlds") or []), len(p.get("seeds") or []), int(p.get("observations", 0))),
            reverse=True,
        )[:256],
        "last_burst": burst_id,
        "observable_definition_version": OBSERVABLE_DEFINITION_VERSION,
        "note": "Shared common-observable fingerprints are research leads, not universality or identical-physics claims.",
    })
    ledger_path = _storage_path(_LEDGER, for_write=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    return ledger


def compare_g001_patterns(*, episodes: list[dict[str, Any]], g001_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    by_fp: dict[str, list[dict[str, Any]]] = {}
    for e in episodes:
        if e.get("world_id") != "g001-tdgl":
            by_fp.setdefault(str(e.get("fingerprint")), []).append(e)
    matches: list[dict[str, Any]] = []
    allowed = {"REPEATED", "CROSS_CONDITION_RECURRENT", "ROBUST_RECURRENT_CANDIDATE", "CROSS_WORLD_CANDIDATE"}
    for pattern in g001_ledger.get("patterns") or []:
        if pattern.get("status") not in allowed:
            continue
        projection = project_g001_fingerprint(pattern.get("fingerprint"))
        fp = projection.get("fingerprint")
        if not fp or fp not in by_fp:
            continue
        targets = by_fp[fp]
        purities = _g001_purities(g001_ledger, str(pattern["pattern_id"]), pattern)
        aligned = _strict_alignment(purities, targets)
        coverage = float(projection.get("coverage", 0.0))
        status = "CROSS_WORLD_ZERO_ALIGNED_LEAD" if aligned and coverage >= 0.999 else "SIGNATURE_OVERLAP_ONLY"
        matches.append({
            "g001_pattern_id": pattern["pattern_id"],
            "g001_fingerprint": pattern.get("fingerprint"),
            "common_fingerprint": fp,
            "projection_coverage": round(coverage, 4),
            "dropped_g001_features": projection.get("dropped_parts") or [],
            "g001_start_purities": purities,
            "matched_worlds": sorted({str(e.get("world_id")) for e in targets}),
            "matched_world_zero_pairs": sorted({f"{e.get('world_id')}@{e.get('zero_id')}" for e in targets}),
            "matched_observations_this_burst": len(targets),
            "strict_ZA_alignment": aligned,
            "status": status,
            "universality_claim": False,
            "identical_physics_claim": False,
        })
    matches.sort(
        key=lambda x: (x["strict_ZA_alignment"], len(x["matched_worlds"]), x["matched_observations_this_burst"]),
        reverse=True,
    )
    return matches


def analyze_shadow_report(report: dict[str, Any], *, quick: bool = True, max_episodes_per_probe: int = 3) -> dict[str, Any]:
    probes: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for obs in report.get("observations") or []:
        try:
            probes.append(common_probe(
                str(obs["world_id"]), zero_id=str(obs["zero_id"]), seed=int(obs["seed"]), quick=quick
            ))
        except Exception as exc:
            errors.append({
                "world_id": str(obs.get("world_id")), "zero_id": str(obs.get("zero_id")),
                "error": f"{type(exc).__name__}: {exc}",
            })
    episodes: list[dict[str, Any]] = []
    for probe in probes:
        if probe.get("finite"):
            episodes.extend(detect_common_episodes(probe, max_episodes=max_episodes_per_probe))

    burst_id = str(report.get("burst_id") or report.get("generated_at") or "multiworld-shadow")
    cross_ledger = _update_cross_ledger(burst_id=burst_id, episodes=episodes)
    g001_ledger = _load_json(_G001_LEDGER, {"patterns": [], "recent_episodes": []})
    matches = compare_g001_patterns(episodes=episodes, g001_ledger=g001_ledger)
    recurrent = [p for p in cross_ledger.get("patterns") or [] if len(p.get("worlds") or []) >= 2]
    summary = {
        "version": 1,
        "mode": "cross-world-open-ended-shadow",
        "observable_definition_version": OBSERVABLE_DEFINITION_VERSION,
        "common_features": list(COMMON_FEATURES),
        "probes": len(probes),
        "finite_probes": sum(bool(p.get("finite")) for p in probes),
        "episodes": len(episodes),
        "errors": errors,
        "recurrent_common_signatures": recurrent[:12],
        "g001_pattern_matches": matches[:12],
        "strict_zero_aligned_matches": sum(m.get("status") == "CROSS_WORLD_ZERO_ALIGNED_LEAD" for m in matches),
        "signature_overlap_only_matches": sum(m.get("status") == "SIGNATURE_OVERLAP_ONLY" for m in matches),
        "same_fingerprint_means_same_physics": False,
        "universality_claim": False,
        "official_level_effect": False,
        "promotion_effect": False,
        "hypothesis_confidence_effect": False,
        "changes_world_dynamics": False,
        "note": (
            "Common fingerprints compare normalized directions of observable changes. They do not equate order parameters, "
            "defect physics, conserved quantities, microscopic laws, or claim universality."
        ),
    }
    report_path = _storage_path(_REPORT, for_write=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
