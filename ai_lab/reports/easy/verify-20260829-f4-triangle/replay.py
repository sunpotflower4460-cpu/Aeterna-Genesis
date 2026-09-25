#!/usr/bin/env python3
"""Independent t=0 replay of cited F4 / X-pattern claims. Observation only.

Does not change physics, thresholds, official rooms, or F-path gates.
Visualization is separated from physics data (AGENTS.md / render honesty).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from ai_lab import lab  # noqa: E402
from ai_lab.dream import fission_path, open_ended, prefix_audit, x_mechanism_discovery  # noqa: E402
from ai_lab.dream import strict_geometry as strict  # noqa: E402
from genesis.diagnostics import geometry_events as geom  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tools import snapshot  # noqa: E402

OUT = Path(__file__).resolve().parent
PNG = OUT / "png"
PNG.mkdir(parents=True, exist_ok=True)

CITED_F4 = {
    "trial_index": 808359,
    "family": "white",
    "seed": 517111,
    "quick": True,
    "knobs": {
        "noise_amplitude": 2.3934591337967174e-05,
        "correlation_length": 8.012905565651579,
        "diffusion_ratio": 0.12867366080783085,
        "drive_strength": 3.1112983463625192,
        "quench_duration": 6.613343130350215,
    },
    "expected_observation_digest": "206d189ecf4eabaed6980707fa347f27fa42ad931b37b6da4ee31bc9ed68a316",
    "expected_state_digest": "b1f69464d8806eb9606ef9ffbcebc2dccab07676c6d268a76eae2aacea25fb44",
}

# Stored follow-up source for the unlabeled amp_std:+L pattern (not the F4 seed).
X_PATTERN = {
    "trial_index": 809780,
    "family": "white_lowk",
    "seed": 366216,  # a white-family seed listed on X-b991d59a4d; knobs below are the stored follow-up source
    "quick": True,
    "pattern_id": "X-b991d59a4d",
    "knobs": {
        "noise_amplitude": 1.0395555252403736e-05,
        "correlation_length": 10.615693081104842,
        "diffusion_ratio": 0.24812678989296233,
        "drive_strength": 4.961717814441295,
        "quench_duration": 8.328079456110377,
    },
    "note": (
        "Knobs are the stored unknown_followups search_focus for X-b991d59a4d "
        "(family=white_lowk, trial 809780). Seed 366216 is a listed white-family "
        "observation seed for the same fingerprint; this is a near-zero replay, "
        "not a reconstruction of unpublished trial-249 single_seed knobs."
    ),
}

# A second listed F4 frontier, only as a robustness check if the cited seed is replayable.
SECOND_F4 = {
    "trial_index": 809020,
    "family": "white",
    "seed": 948530,
    "quick": True,
    "knobs": {
        "noise_amplitude": 1.617119902913215e-05,
        "correlation_length": 5.599384591545325,
        "diffusion_ratio": 0.17015066741583834,
        "drive_strength": 1.7797103175649942,
        "quench_duration": 6.4047135658023375,
    },
}


def _jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else obj
    if isinstance(obj, np.generic):
        return _jsonable(obj.item())
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return str(obj)


def _mark_vortices(rgb: np.ndarray, points: list[dict[str, Any]], edge: int, color: tuple[int, int, int]) -> np.ndarray:
    """Diagnostic overlay only. Does not change the physical field."""
    out = np.array(rgb, copy=True)
    h, w, _ = out.shape
    scale_y = h / float(edge)
    scale_x = w / float(edge)
    r = max(2, int(round(min(h, w) / 48.0)))
    for p in points:
        cy = int(round(float(p["y"]) * scale_y)) % h
        cx = int(round(float(p["x"]) * scale_x)) % w
        y0, y1 = max(0, cy - r), min(h, cy + r + 1)
        x0, x1 = max(0, cx - r), min(w, cx + r + 1)
        out[y0:y1, x0:x1] = color
        # tiny hollow so the marker is visible on both dark and bright fields
        if y1 - y0 > 2 and x1 - x0 > 2:
            out[y0 + 1:y1 - 1, x0 + 1:x1 - 1] = rgb[y0 + 1:y1 - 1, x0 + 1:x1 - 1]
            out[cy:cy + 1, x0:x1] = color
            out[y0:y1, cx:cx + 1] = color
    return out


def _save_fields(prefix: str, psi: np.ndarray, points: list[dict[str, Any]], triangle: dict[str, Any] | None) -> dict[str, str]:
    amp_path = str(PNG / f"{prefix}_amp.png")
    phase_path = str(PNG / f"{prefix}_phase.png")
    overlay_path = str(PNG / f"{prefix}_amp_vortices.png")
    snapshot.render_field(np.abs(psi), amp_path, diverging=False, symmetric=False, px=384)
    snapshot.render_field(np.angle(psi), phase_path, diverging=True, symmetric=True, px=384)
    rgb = snapshot.colormap(
        snapshot._upscale(
            (np.abs(psi) - float(np.abs(psi).min())) / (float(np.abs(psi).max() - np.abs(psi).min()) + 1e-12),
            384,
        ),
        diverging=False,
    )
    marked = _mark_vortices(rgb, points, psi.shape[0], (255, 255, 255))
    if triangle:
        tri_pts = [points[i] for i in triangle.get("indices") or [] if i < len(points)]
        marked = _mark_vortices(marked, tri_pts, psi.shape[0], (220, 40, 40))
    snapshot.write_png(marked, overlay_path)
    return {"amp": amp_path, "phase": phase_path, "overlay": overlay_path}


def _evolve(rec: dict[str, Any], *, save_prefix: str | None, png_times: int = 8) -> dict[str, Any]:
    """Same IC + TDGL stepper as strict_geometry._geometry_probe, plus field screenshots."""
    quick = bool(rec.get("quick", True))
    edge, steps, nsnap = lab.STEPS_2D[quick]
    shape = (edge, edge)
    p = lab._apply_knobs(dict(gl.DEFAULTS), rec["knobs"])
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    total = steps * nsub
    rng = np.random.default_rng(int(rec["seed"]))
    psi0 = lab.make_ic(
        rec["family"], shape, float(p["noise_amplitude"]), rng,
        corr_len=float(rec["knobs"].get("correlation_length", 1.0)),
    )
    psi = np.array(psi0, copy=True)
    snap_every = max(1, total // max(10, nsnap * 2))
    want_png = set()
    if save_prefix:
        want_png = {0, total - 1}
        for k in range(png_times):
            want_png.add(min(total - 1, (k * (total - 1)) // max(1, png_times - 1)))

    series: list[dict[str, Any]] = []
    pngs: dict[str, Any] = {}
    first_vortex_step = None
    first_triangle_step = None
    persistent_triangle_from = None
    prev_triangle = False
    traj = []
    amp0 = float(np.mean(np.abs(psi)))

    def observe(t: int, field: np.ndarray) -> dict[str, Any]:
        points = geom.vortex_points_2d(field)
        pair = geom.best_mutual_pair(points, shape)
        triad = geom.best_mutual_triad(points, shape)
        triangle = geom.best_triangle(points, shape)
        amp = np.abs(field)
        mean_amp = float(amp.mean())
        amp_std = float(amp.std())
        _, prom = measures.structure_factor_peak(field)
        physical_time = (t + 1) * p["dt"] if t >= 0 else 0.0
        return {
            "step": t,
            "physical_time": physical_time,
            "n_vortices": len(points),
            "charges": [int(q["charge"]) for q in points],
            "points": points,
            "pair": bool(pair),
            "relation": bool(triad),
            "triangle": bool(triangle),
            "triangle_metrics": None if triangle is None else {
                "regularity": triangle.get("regularity"),
                "area_ratio": triangle.get("area_ratio"),
                "max_side": triangle.get("max_side"),
                "charge_pattern": triangle.get("charge_pattern"),
                "centroid": triangle.get("centroid"),
                "side_lengths": triangle.get("side_lengths"),
            },
            "mean_amp": mean_amp,
            "amp_std": amp_std,
            "amp_cv": amp_std / max(mean_amp, 1e-15),
            "sk_prom": float(prom),
            "defects_winding": int(measures.winding_defect_count(field)),
        }

    # t=0 (before any step) — the start we actually used
    t0 = observe(-1, psi)
    t0["physical_time"] = 0.0
    t0["step"] = 0
    series.append(t0)
    if save_prefix:
        pngs["t0"] = _save_fields(f"{save_prefix}_t000", psi, t0["points"], None)

    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            break
        take = (t % snap_every == 0) or (t == total - 1) or (save_prefix and t in want_png)
        if not take:
            continue
        row = observe(t, psi)
        series.append(row)
        traj.append({"mean_amp": row["mean_amp"], "sk_prom": row["sk_prom"], "defects": row["defects_winding"]})
        if first_vortex_step is None and row["n_vortices"] > 0:
            first_vortex_step = t
            if save_prefix:
                pngs["first_vortex"] = _save_fields(f"{save_prefix}_first_vortex", psi, row["points"], None)
        if row["triangle"] and not prev_triangle and first_triangle_step is None:
            first_triangle_step = t
            if save_prefix:
                pngs["first_triangle"] = _save_fields(
                    f"{save_prefix}_first_triangle", psi, row["points"],
                    geom.best_triangle(row["points"], shape),
                )
        if row["triangle"] and prev_triangle and persistent_triangle_from is None:
            persistent_triangle_from = series[-2]["step"]
            if save_prefix:
                pngs["persistent_triangle"] = _save_fields(
                    f"{save_prefix}_persistent_triangle", psi, row["points"],
                    geom.best_triangle(row["points"], shape),
                )
        prev_triangle = bool(row["triangle"])
        if save_prefix and t in want_png:
            pngs[f"step_{t:04d}"] = _save_fields(
                f"{save_prefix}_s{t:04d}", psi, row["points"],
                geom.best_triangle(row["points"], shape) if row["triangle"] else None,
            )

    if save_prefix:
        pngs["end"] = _save_fields(
            f"{save_prefix}_end", psi, series[-1]["points"],
            geom.best_triangle(series[-1]["points"], shape) if series[-1]["triangle"] else None,
        )

    level, detected, mb = measures.assess_level(traj) if traj else (0, {}, {})
    digest = prefix_audit.field_digest(psi)
    ampN = float(np.mean(np.abs(psi)))
    return {
        "family": rec["family"],
        "seed": rec["seed"],
        "knobs": rec["knobs"],
        "grid": list(shape),
        "macro_steps": steps,
        "internal_steps": total,
        "nsub": nsub,
        "dt": p["dt"],
        "physical_time": float(steps * base_dt),
        "ic_family_uses_correlation_length": rec["family"] != "white",
        "t0": {
            "mean_amp": t0["mean_amp"],
            "amp_std": t0["amp_std"],
            "amp_cv": t0["amp_cv"],
            "n_vortices": t0["n_vortices"],
            "max_abs": float(np.max(np.abs(psi0))),
        },
        "end": {
            "mean_amp": ampN,
            "amp_std": series[-1]["amp_std"],
            "amp_cv": series[-1]["amp_cv"],
            "n_vortices": series[-1]["n_vortices"],
            "triangle": series[-1]["triangle"],
        },
        "amp_growth": ampN / max(amp0, 1e-30),
        "first_vortex_step": first_vortex_step,
        "first_triangle_step": first_triangle_step,
        "persistent_triangle_from_step": persistent_triangle_from,
        "max_vortices": max(s["n_vortices"] for s in series),
        "any_triangle_snapshot": any(s["triangle"] for s in series),
        "assess_level": {"reached_level": level, "detected": detected, "measured_by": mb},
        "endpoint_digest": digest,
        "series": [{k: v for k, v in s.items() if k != "points"} for s in series],
        "pngs": pngs,
        "honesty": {
            "triangle_was_seeded": False,
            "vortices_were_seeded": False,
            "visualization_separated_from_physics": True,
            "overlay_is_diagnostic_only": True,
        },
    }


def _compact_probe_view(probe: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "trial_index", "family", "seed", "reached_level", "persistent_pair_seen",
        "persistent_pair_only_seen", "persistent_relation_seen", "triangle_seen",
        "control_seen", "fission_like_after_triangle", "fission_like_after_control",
        "balance_collapse_seen", "balance_collapse_step", "pre_split_instability_candidate",
        "persistent_split_seen", "persistent_split_step", "network_fission_candidate",
        "network_fission_is_biological_cell_division", "zero_to_fission", "honesty",
        "triangle", "relation", "pair", "series",
    )
    return {k: probe.get(k) for k in keep}


def replay_f4(rec: dict[str, Any], *, prefix: str) -> dict[str, Any]:
    screen = lab._screen_ic(rec["family"], rec["knobs"], rec["seed"], quick=True)
    probe_in = {**rec, "reached_level": screen.get("reached_level"), "quick": True}
    probe = strict._geometry_probe(probe_in)
    obs = prefix_audit.observation_digest(probe.get("series"))
    state = prefix_audit.replay_g001_endpoint(rec, quick=True)
    expected_obs = {"algorithm": "sha256-observation-round10-v1", "value": rec.get("expected_observation_digest")} if rec.get("expected_observation_digest") else None
    expected_state = {
        "algorithm": "sha256-round12-v1",
        "value": rec.get("expected_state_digest"),
        "shape": [48, 48],
        "kind": "complex",
    } if rec.get("expected_state_digest") else None
    visual = _evolve(rec, save_prefix=prefix)
    path = probe.get("zero_to_fission") or fission_path.assess_probe(probe)
    return {
        "cited": {k: rec[k] for k in ("trial_index", "family", "seed", "knobs") if k in rec},
        "screen": screen,
        "geometry_probe": _compact_probe_view(probe),
        "zero_to_fission": path,
        "observation_digest": obs,
        "state_digest": state,
        "digest_match": {
            "observation": prefix_audit.compare_digest(expected_obs, obs) if expected_obs else None,
            "state": prefix_audit.compare_digest(expected_state, state) if expected_state else None,
        },
        "visual": visual,
        "open_ended": replay_x_on(rec),
    }


def replay_x_on(rec: dict[str, Any]) -> dict[str, Any]:
    probe = open_ended._probe({**rec, "quick": True})
    episodes = open_ended.detect_episodes(probe, max_episodes=5)
    classified = []
    qd = float((rec.get("knobs") or {}).get("quench_duration", 0.0))
    snaps = probe.get("snapshots") or []
    for ep in episodes:
        t = float(ep.get("physical_time", 0.0))
        idx = next((i for i, s in enumerate(snaps) if abs(float(s.get("physical_time", -1.0)) - t) <= 1e-9), None)
        cls = None
        if idx is not None and idx > 0:
            cls = x_mechanism_discovery._classify_event(
                snaps[idx - 1], snaps[idx], event_time=t, quench_duration=qd,
                known_context=list(ep.get("known_context") or []),
            )
        classified.append({"episode": ep, "classification": cls})
    target = [c for c in classified if (c["episode"] or {}).get("pattern_id") == "X-b991d59a4d"]
    defect_never = all(float(s.get("defect_count", 0.0)) < 0.5 for s in snaps)
    defect_any = any(float(s.get("defect_count", 0.0)) >= 0.5 for s in snaps)
    amp_stds = [float(s["amp_std"]) for s in snaps]
    mean_amps = [float(s["mean_amp"]) for s in snaps]
    cvs = [s / max(m, 1e-15) for s, m in zip(amp_stds, mean_amps)]
    return {
        "condition_id": probe.get("condition_id"),
        "zero_purity": probe.get("zero_purity"),
        "finite": probe.get("finite"),
        "n_snapshots": len(snaps),
        "defect_count_never_nonzero": defect_never,
        "defect_count_any_nonzero": defect_any,
        "amp_std_start": amp_stds[0] if amp_stds else None,
        "amp_std_end": amp_stds[-1] if amp_stds else None,
        "amp_std_max": max(amp_stds) if amp_stds else None,
        "mean_amp_start": mean_amps[0] if mean_amps else None,
        "mean_amp_end": mean_amps[-1] if mean_amps else None,
        "amp_cv_start": cvs[0] if cvs else None,
        "amp_cv_end": cvs[-1] if cvs else None,
        "amp_cv_max": max(cvs) if cvs else None,
        "snapshots": [
            {
                "physical_time": s["physical_time"],
                "mean_amp": s["mean_amp"],
                "amp_std": s["amp_std"],
                "amp_cv": float(s["amp_std"]) / max(float(s["mean_amp"]), 1e-15),
                "defect_count": s["defect_count"],
                "triangle_present": s.get("triangle_present"),
                "relation_present": s.get("relation_present"),
            }
            for s in snaps
        ],
        "episodes": classified,
        "x_b991d59a4d_episodes": target,
    }


def main() -> None:
    print("replaying cited F4 candidate (white / seed=517111) from t=0 ...", flush=True)
    f4 = replay_f4(CITED_F4, prefix="f4_517111")
    print(
        "  screen L%s  triangle_seen=%s  depth=%s  obs_match=%s  state_match=%s"
        % (
            f4["screen"].get("reached_level"),
            f4["geometry_probe"].get("triangle_seen"),
            (f4["zero_to_fission"] or {}).get("depth_code"),
            (f4["digest_match"]["observation"] or {}).get("status"),
            (f4["digest_match"]["state"] or {}).get("status"),
        ),
        flush=True,
    )

    print("replaying second F4 frontier (white / seed=948530) ...", flush=True)
    f4b = replay_f4(SECOND_F4, prefix="f4_948530")
    print(
        "  screen L%s  triangle_seen=%s  depth=%s"
        % (
            f4b["screen"].get("reached_level"),
            f4b["geometry_probe"].get("triangle_seen"),
            (f4b["zero_to_fission"] or {}).get("depth_code"),
        ),
        flush=True,
    )

    print("replaying X-b991d59a4d follow-up source (white_lowk) ...", flush=True)
    x_visual = _evolve(X_PATTERN, save_prefix="x_white_lowk")
    x_open = replay_x_on(X_PATTERN)
    x_screen = lab._screen_ic(X_PATTERN["family"], X_PATTERN["knobs"], X_PATTERN["seed"], quick=True)
    print(
        "  screen L%s  defect_never=%s  amp_std %s -> %s  x_hits=%d"
        % (
            x_screen.get("reached_level"),
            x_open["defect_count_never_nonzero"],
            x_open["amp_std_start"],
            x_open["amp_std_end"],
            len(x_open["x_b991d59a4d_episodes"]),
        ),
        flush=True,
    )

    out = {
        "version": 1,
        "burst_cited": "dream-20260829-0520",
        "question": (
            "Did one uninterrupted near-zero run grow a 3-vortex triangle, "
            "and is amp_std:+L the same as a new object being born?"
        ),
        "claim_tier_of_this_file": "measured",
        "dimension": "2d-screen-quick-48",
        "not_official_room": True,
        "not_official_emergence_level_4": True,
        "cited_f4": f4,
        "second_f4": f4b,
        "x_pattern": {
            "pattern_id": "X-b991d59a4d",
            "fingerprint": "amp_std:+L",
            "source_note": X_PATTERN["note"],
            "screen": x_screen,
            "visual": x_visual,
            "open_ended": x_open,
        },
        "verdict_keys": {
            "cited_triangle_seen": bool(f4["geometry_probe"].get("triangle_seen")),
            "cited_balance_collapse_seen": bool(f4["geometry_probe"].get("balance_collapse_seen")),
            "cited_network_fission_candidate": bool(f4["geometry_probe"].get("network_fission_candidate")),
            "cited_depth_code": (f4["zero_to_fission"] or {}).get("depth_code"),
            "cited_reached_level": f4["screen"].get("reached_level"),
            "observation_digest_match": (f4["digest_match"]["observation"] or {}).get("match"),
            "state_digest_match": (f4["digest_match"]["state"] or {}).get("match"),
        },
    }
    path = OUT / "measurements.json"
    path.write_text(json.dumps(_jsonable(out), indent=2, ensure_ascii=False))
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
