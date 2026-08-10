"""Open-ended emergence discovery for Genesis Dream.

This lane intentionally does NOT ask whether a run followed the relation-fission F-path.  It samples
current g001 search results across score strata, records a neutral set of time-series observables,
finds post-drive change points, fingerprints state transitions, and remembers fingerprints that
repeat across independent seeds/conditions.

The output is research navigation only.  It cannot assign official Emergence Levels, promote Rooms,
change success thresholds, or claim a newly named physical law.  Human/physics interpretation comes
after a recurrent transition has survived independent checks.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from ai_lab.dream import fission_path
from genesis.diagnostics import geometry_events as geom
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "emergence_graph.json"
_REPORT = _REPO / "ai_lab" / "reports" / "emergence" / "latest.json"
_CAPTURED_MASS: list[dict[str, Any]] = []

_FEATURES = (
    "mean_amp",
    "amp_std",
    "phase_coherence",
    "spectral_entropy",
    "spectral_k_rms",
    "spectral_anisotropy",
    "gradient_rms",
    "defect_count",
    "net_topological_charge",
    "high_amp_fraction",
)


def install_mass_capture(adaptive_module: Any) -> None:
    """Capture this burst's mass results without changing how the mass search itself behaves."""
    current = adaptive_module.run_mass_2d
    if getattr(current, "_open_ended_capture", False):
        return
    original = current

    def wrapped(*args: Any, **kwargs: Any):
        result = original(*args, **kwargs)
        global _CAPTURED_MASS
        _CAPTURED_MASS = [dict(x) for x in (result.get("results") or [])]
        return result

    wrapped._open_ended_capture = True
    adaptive_module.run_mass_2d = wrapped


def consume_captured_mass() -> list[dict[str, Any]]:
    global _CAPTURED_MASS
    out = _CAPTURED_MASS
    _CAPTURED_MASS = []
    return out


def _condition_signature(rec: dict[str, Any]) -> str:
    k = rec.get("knobs") or {}
    d = max(float(k.get("diffusion_ratio", 1.0)), 1e-12)
    dlog = round(math.log10(d) * 2.0) / 2.0
    drive = int(math.floor(float(k.get("drive_strength", 0.0))))
    quench = int(math.floor(float(k.get("quench_duration", 0.0)) / 5.0))
    return f"{rec.get('family')}|logD={dlog:+.1f}|drive={drive}|q5={quench}"


def select_diverse_candidates(
    results: list[dict[str, Any]], *, n: int = 24, seed: int = 0,
) -> list[dict[str, Any]]:
    """Sample across the score distribution instead of only replaying the current winners."""
    stable = [x for x in results if x.get("score") is not None]
    if not stable or n <= 0:
        return []
    stable.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    rng = random.Random(seed ^ 0x0EED5EED)
    n = min(int(n), len(stable))
    quartiles: list[list[dict[str, Any]]] = []
    for q in range(4):
        lo = (q * len(stable)) // 4
        hi = ((q + 1) * len(stable)) // 4
        bucket = stable[lo:hi]
        rng.shuffle(bucket)
        quartiles.append(bucket)
    chosen: list[dict[str, Any]] = []
    cursor = [0, 0, 0, 0]
    while len(chosen) < n:
        progressed = False
        for q in range(4):
            if cursor[q] < len(quartiles[q]) and len(chosen) < n:
                chosen.append(quartiles[q][cursor[q]])
                cursor[q] += 1
                progressed = True
        if not progressed:
            break
    return chosen


def _spectral_features(psi: np.ndarray) -> tuple[float, float, float]:
    field = np.abs(psi)
    field = field - float(field.mean())
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


def _snapshot_features(psi: np.ndarray, *, physical_time: float, shape: tuple[int, int]) -> dict[str, Any]:
    amp = np.abs(psi)
    mean_amp = float(amp.mean())
    amp_std = float(amp.std())
    weight = float(amp.sum())
    unit = psi / np.maximum(amp, 1e-15)
    phase_coherence = 0.0 if weight <= 1e-30 else float(abs((amp * unit).sum()) / weight)
    entropy, k_rms, anis = _spectral_features(psi)
    gy = np.roll(psi, -1, axis=0) - psi
    gx = np.roll(psi, -1, axis=1) - psi
    gradient_rms = float(np.sqrt(np.mean(np.abs(gx) ** 2 + np.abs(gy) ** 2)))
    points = geom.vortex_points_2d(psi)
    net_charge = int(sum(int(p.get("charge", 0)) for p in points))
    threshold = mean_amp + amp_std
    high_fraction = float(np.mean(amp > threshold))
    triad = geom.best_mutual_triad(points, shape)
    triangle = geom.best_triangle(points, shape)
    return {
        "physical_time": float(physical_time),
        "mean_amp": mean_amp,
        "amp_std": amp_std,
        "phase_coherence": phase_coherence,
        "spectral_entropy": entropy,
        "spectral_k_rms": k_rms,
        "spectral_anisotropy": anis,
        "gradient_rms": gradient_rms,
        "defect_count": float(len(points)),
        "net_topological_charge": float(net_charge),
        "high_amp_fraction": high_fraction,
        "relation_present": bool(triad),
        "triangle_present": bool(triangle),
    }


def _probe(rec: dict[str, Any]) -> dict[str, Any]:
    quick = bool(rec.get("quick", True))
    edge, macro_steps, nsnap = lab.STEPS_2D[quick]
    shape = (edge, edge)
    knobs = dict(rec.get("knobs") or {})
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    total = macro_steps * nsub
    rng = np.random.default_rng(int(rec["seed"]))
    psi = lab.make_ic(
        str(rec["family"]), shape, float(p["noise_amplitude"]), rng,
        corr_len=float(knobs.get("correlation_length", 1.0)),
    )
    snap_every = max(1, total // max(16, nsnap * 3))
    snapshots: list[dict[str, Any]] = []
    finite = True
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            finite = False
            break
        if t % snap_every != 0 and t != total - 1:
            continue
        snapshots.append(_snapshot_features(psi, physical_time=(t + 1) * p["dt"], shape=shape))
    base_physical_time = macro_steps * base_dt
    analysis_start = min(base_physical_time * 0.8, max(float(knobs.get("quench_duration", 0.0)), base_physical_time * 0.2))
    return {
        "trial_index": rec.get("trial_index"),
        "family": rec.get("family"),
        "knobs": knobs,
        "seed": rec.get("seed"),
        "score": rec.get("score"),
        "world_id": "g001-tdgl",
        "zero_purity": fission_path.start_purity(rec.get("family")),
        "condition_id": _condition_signature(rec),
        "finite": finite,
        "analysis_start_time": analysis_start,
        "base_physical_time": base_physical_time,
        "snapshots": snapshots,
    }


def _robust_scales(matrix: np.ndarray) -> np.ndarray:
    q10 = np.nanpercentile(matrix, 10.0, axis=0)
    q90 = np.nanpercentile(matrix, 90.0, axis=0)
    scale = q90 - q10
    fallback = np.nanmax(np.abs(matrix), axis=0)
    return np.maximum(scale, np.maximum(fallback * 1e-6, 1e-9))


def _magnitude_bucket(x: float) -> str:
    if x < 0.35:
        return "S"
    if x < 0.8:
        return "M"
    return "L"


def _episode_fingerprint(delta_norm: np.ndarray) -> str | None:
    ranked = sorted(range(len(_FEATURES)), key=lambda i: abs(float(delta_norm[i])), reverse=True)
    pieces: list[str] = []
    for i in ranked:
        v = float(delta_norm[i])
        if abs(v) < 0.15:
            continue
        sign = "+" if v > 0 else "-"
        pieces.append(f"{_FEATURES[i]}:{sign}{_magnitude_bucket(abs(v))}")
        if len(pieces) >= 5:
            break
    return "|".join(sorted(pieces)) if pieces else None


def _state_fingerprint(row: np.ndarray, matrix: np.ndarray) -> str:
    keys = ("mean_amp", "phase_coherence", "spectral_entropy", "gradient_rms", "defect_count")
    pieces = []
    for key in keys:
        i = _FEATURES.index(key)
        val = float(row[i])
        if key == "defect_count":
            state = "0" if val < 0.5 else ("1-2" if val < 2.5 else "3+")
        else:
            q33, q67 = np.nanpercentile(matrix[:, i], [33.0, 67.0])
            state = "L" if val < q33 else ("H" if val > q67 else "M")
        pieces.append(f"{key}={state}")
    return ";".join(pieces)


def _known_context(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if before.get("defect_count", 0.0) < 0.5 <= after.get("defect_count", 0.0):
        tags.append("vortices_appear")
    if before.get("defect_count", 0.0) >= 0.5 > after.get("defect_count", 0.0):
        tags.append("vortices_disappear")
    if bool(before.get("relation_present")) != bool(after.get("relation_present")):
        tags.append("relation_presence_changes")
    if bool(before.get("triangle_present")) != bool(after.get("triangle_present")):
        tags.append("triangle_presence_changes")
    return tags


def detect_episodes(probe: dict[str, Any], *, max_episodes: int = 3) -> list[dict[str, Any]]:
    snaps = probe.get("snapshots") or []
    if len(snaps) < 4 or max_episodes <= 0:
        return []
    matrix = np.asarray([[float(s[k]) for k in _FEATURES] for s in snaps], dtype=float)
    if not np.all(np.isfinite(matrix)):
        return []
    scales = _robust_scales(matrix)
    delta_norm = np.diff(matrix, axis=0) / scales
    clipped = np.clip(delta_norm, -5.0, 5.0)
    scores = np.sqrt(np.mean(clipped * clipped, axis=1))
    eligible = [
        i for i in range(len(scores))
        if float(snaps[i + 1]["physical_time"]) >= float(probe.get("analysis_start_time", 0.0))
    ]
    if not eligible:
        return []
    vals = np.asarray([scores[i] for i in eligible], dtype=float)
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med)))
    threshold = max(0.18, med + 2.5 * max(mad, 1e-6))
    ranked = sorted(eligible, key=lambda i: float(scores[i]), reverse=True)
    chosen: list[int] = []
    for i in ranked:
        if float(scores[i]) < threshold:
            continue
        if any(abs(i - j) <= 1 for j in chosen):
            continue
        chosen.append(i)
        if len(chosen) >= max_episodes:
            break
    episodes: list[dict[str, Any]] = []
    for i in sorted(chosen):
        fp = _episode_fingerprint(delta_norm[i])
        if not fp:
            continue
        before, after = snaps[i], snaps[i + 1]
        state_before = _state_fingerprint(matrix[i], matrix)
        state_after = _state_fingerprint(matrix[i + 1], matrix)
        pid = "X-" + hashlib.sha256(fp.encode()).hexdigest()[:10]
        episodes.append({
            "pattern_id": pid,
            "fingerprint": fp,
            "change_score": round(float(scores[i]), 6),
            "physical_time": float(after["physical_time"]),
            "before_state": state_before,
            "after_state": state_after,
            "known_context": _known_context(before, after),
            "unlabeled_transition": not bool(_known_context(before, after)),
            "trial_index": probe.get("trial_index"),
            "family": probe.get("family"),
            "seed": probe.get("seed"),
            "condition_id": probe.get("condition_id"),
            "zero_purity": probe.get("zero_purity"),
            "world_id": probe.get("world_id"),
        })
    return episodes


def _load_ledger() -> dict[str, Any]:
    if _LEDGER.exists():
        try:
            return json.loads(_LEDGER.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "version": 1,
        "note": "Open-ended transition fingerprints. Pattern status is research navigation, not scientific truth.",
        "patterns": [],
        "transitions": [],
        "recent_episodes": [],
    }


def _pattern_status(*, unique_seeds: int, unique_conditions: int, unique_worlds: int) -> str:
    if unique_worlds >= 2 and unique_seeds >= 4:
        return "CROSS_WORLD_CANDIDATE"
    if unique_seeds >= 5 and unique_conditions >= 3:
        return "ROBUST_RECURRENT_CANDIDATE"
    if unique_seeds >= 3 and unique_conditions >= 2:
        return "CROSS_CONDITION_RECURRENT"
    if unique_seeds >= 2:
        return "REPEATED"
    return "NEW"


def _update_ledger(ledger: dict[str, Any], *, burst_id: str, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = {p["pattern_id"]: p for p in (ledger.get("patterns") or [])}
    transitions = {t["transition_id"]: t for t in (ledger.get("transitions") or [])}
    new_ids: set[str] = set()
    for e in episodes:
        pid = str(e["pattern_id"])
        p = patterns.get(pid)
        if p is None:
            p = {
                "pattern_id": pid,
                "fingerprint": e["fingerprint"],
                "first_burst": burst_id,
                "last_burst": burst_id,
                "observations": 0,
                "seeds": [],
                "conditions": [],
                "worlds": [],
                "unlabeled_observations": 0,
                "known_context_counts": {},
                "representative": e,
                "status": "NEW",
            }
            patterns[pid] = p
            new_ids.add(pid)
        p["last_burst"] = burst_id
        p["observations"] = int(p.get("observations", 0)) + 1
        seed = int(e.get("seed") or 0)
        condition = str(e.get("condition_id"))
        world = str(e.get("world_id"))
        p["seeds"] = list(dict.fromkeys([*(p.get("seeds") or []), seed]))[-64:]
        p["conditions"] = list(dict.fromkeys([*(p.get("conditions") or []), condition]))[-64:]
        p["worlds"] = list(dict.fromkeys([*(p.get("worlds") or []), world]))[-16:]
        if e.get("unlabeled_transition"):
            p["unlabeled_observations"] = int(p.get("unlabeled_observations", 0)) + 1
        kc = p.setdefault("known_context_counts", {})
        for tag in e.get("known_context") or []:
            kc[tag] = int(kc.get(tag, 0)) + 1
        p["status"] = _pattern_status(
            unique_seeds=len(p["seeds"]), unique_conditions=len(p["conditions"]), unique_worlds=len(p["worlds"])
        )

        edge_raw = f"{e['before_state']}->{e['after_state']}"
        edge_id = "T-" + hashlib.sha256(edge_raw.encode()).hexdigest()[:10]
        t = transitions.get(edge_id)
        if t is None:
            t = {
                "transition_id": edge_id,
                "before_state": e["before_state"],
                "after_state": e["after_state"],
                "count": 0,
                "pattern_ids": [],
                "first_burst": burst_id,
            }
            transitions[edge_id] = t
        t["count"] = int(t.get("count", 0)) + 1
        t["last_burst"] = burst_id
        t["pattern_ids"] = list(dict.fromkeys([*(t.get("pattern_ids") or []), pid]))[-32:]

    ordered_patterns = sorted(
        patterns.values(),
        key=lambda p: (len(p.get("seeds") or []), len(p.get("conditions") or []), int(p.get("observations", 0))),
        reverse=True,
    )[:256]
    ordered_transitions = sorted(transitions.values(), key=lambda t: int(t.get("count", 0)), reverse=True)[:256]
    recent = [*(ledger.get("recent_episodes") or []), *episodes][-256:]
    ledger.update({
        "patterns": ordered_patterns,
        "transitions": ordered_transitions,
        "recent_episodes": recent,
        "last_burst": burst_id,
    })
    return {"new_pattern_ids": sorted(new_ids), "ledger": ledger}


def _plain_pattern(p: dict[str, Any]) -> str:
    fp = str(p.get("fingerprint") or "")
    parts = [x.replace(":+", " が増える(").replace(":-", " が減る(") + ")" for x in fp.split("|") if x]
    return "、".join(parts[:4]) if parts else "まだ名前のない状態変化"


def run_open_ended(
    *, burst_id: str, mass_results: list[dict[str, Any]], seed: int, quick: bool = True,
    probes: int = 24, workers: int = 4, max_episodes_per_probe: int = 3,
) -> dict[str, Any]:
    chosen = select_diverse_candidates(mass_results, n=max(0, int(probes)), seed=seed)
    payload = [{**x, "quick": bool(quick)} for x in chosen]
    if workers <= 1:
        raw = [_probe(x) for x in payload]
    else:
        with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
            raw = list(pool.map(_probe, payload))
    episodes: list[dict[str, Any]] = []
    for p in raw:
        if p.get("finite"):
            episodes.extend(detect_episodes(p, max_episodes=max(0, int(max_episodes_per_probe))))

    ledger = _load_ledger()
    update = _update_ledger(ledger, burst_id=burst_id, episodes=episodes)
    ledger = update["ledger"]
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))

    recurrent = [
        p for p in ledger.get("patterns") or []
        if p.get("status") in {"CROSS_CONDITION_RECURRENT", "ROBUST_RECURRENT_CANDIDATE", "CROSS_WORLD_CANDIDATE"}
    ]
    recurrent_unlabeled = [p for p in recurrent if int(p.get("unlabeled_observations", 0)) > 0]
    top = recurrent_unlabeled[:5] or recurrent[:5]
    if top:
        highlight = (
            f"{top[0]['pattern_id']} が {len(top[0].get('seeds') or [])} 個の独立seed、"
            f"{len(top[0].get('conditions') or [])} 種類の条件で反復。特徴は {_plain_pattern(top[0])}。"
        )
    elif episodes:
        strongest = max(episodes, key=lambda e: float(e.get("change_score", 0.0)))
        highlight = f"新しい未整理の変化 {strongest['pattern_id']} を記録。まだ反復確認前です。"
    else:
        highlight = "今回の観測窓では、基準を超える新しい変化点候補はありませんでした。"

    summary = {
        "version": 1,
        "mode": "open-ended-shadow",
        "burst_id": burst_id,
        "world_id": "g001-tdgl",
        "probes": len(raw),
        "finite_probes": sum(bool(x.get("finite")) for x in raw),
        "episodes": len(episodes),
        "new_patterns": len(update["new_pattern_ids"]),
        "recurrent_patterns": len(recurrent),
        "recurrent_unlabeled_patterns": len(recurrent_unlabeled),
        "highlight": highlight,
        "top_recurrent": top,
        "sampled_score_strata": 4,
        "selection_is_top_only": False,
        "analysis_begins_after_imposed_drive_phase": True,
        "known_F_path_is_one_reference_only": True,
        "changes_success_gate": False,
        "changes_official_level": False,
        "promotion_effect": False,
        "new_concept_names_are_scientific_claims": False,
        "note": (
            "Fingerprints describe repeated observable transitions before interpretation. A repeated X-pattern is a research lead, "
            "not proof of a new law, organism, route, or higher Emergence Level."
        ),
    }
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
