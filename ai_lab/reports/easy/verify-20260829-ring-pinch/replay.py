#!/usr/bin/env python3
"""Independent 3D check: can one ring-like vortex pinch into two?

Observation only. Does not change physics, thresholds, or official Rooms.
A placed circular-ring seed is a CAPABILITY check and is labeled 置いた.
Grown-from-undifferentiated-IC is the north-star lane and is labeled 育った.

This is NOT cell division, NOT F7 network fission, NOT a new law.
A meridional slice of ONE ring looks like TWO dark dots — that is not two rings.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from core import field as gpe_field  # noqa: E402
from core import measure as gpe_measure  # noqa: E402
from core.fft import k_squared_3d  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402
from genesis.diagnostics.topology3d import three_d_authenticity  # noqa: E402
from genesis.diagnostics.vortex_lines_3d import trace_vortex_lines  # noqa: E402
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tools import snapshot  # noqa: E402

OUT = Path(__file__).resolve().parent
PNG = OUT / "png"
PNG.mkdir(parents=True, exist_ok=True)

# A priori pinch-split criterion (written before looking at this run's pictures).
# Isolated 1 closed bulk loop persists, then 2 closed bulk loops persist.
# Network tangle, 1→0 collapse, and 2D two-core leftovers are NOT a pass.
PINCH_SPLIT_CRITERION = {
    "isolated_one_min_frames": 3,
    "isolated_two_min_frames": 3,
    "max_open_paths_when_isolated": 2,
    "min_loop_n_points": 8,
    "min_loop_length": 8.0,
    "not_a_pass": [
        "many simultaneous loops (KZ tangle / network)",
        "1 closed loop then 0 (shrink / annihilate)",
        "two dark dots on a 2D slice of one ring",
        "opposite-charge pair leftover on a plane",
        "F7 network_fission_candidate",
    ],
}

OFFICIAL_ROOM = {
    "room_id": "room-g001-a",
    "title": "3D Vortex-Line Genesis (TDGL quench)",
    "dimension": "full-3D 64^3",
    "steps_reported": 700,
    "seeds": [0, 1, 2],
    "law": "g001_ginzburg_landau_quench",
    "ic": "uniform_plus_noise mean_amp=0 noise=0.01 (no ring placed)",
    "reached_level": 2,
    "candidate_level": 3,
    "defect_counts": {0: 241, 1: 173, 2: 117},
    "note": (
        "Official diagnostics count xy-plaquette piercings summed over z "
        "(a line-length proxy), not traced closed loops. Candidate L3 "
        "(motion / reconnection) is frontier. Display field.json is a "
        "20^3 uint8 volume lens, interpolated_for_display — not physics."
    ),
}


def _jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else float(obj)
    if isinstance(obj, np.generic):
        return _jsonable(obj.item())
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return str(obj)


def _field_digest(psi: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes())
    h.update(np.ascontiguousarray(psi.imag).tobytes())
    return h.hexdigest()


def _ring_field(n: int, radius: float, charge: int = 1, core_width: float = 1.5,
                center: float | None = None) -> np.ndarray:
    """Circular vortex RING imprint (置いた). Same phase as core.field.vortex_ring_phase."""
    c = (n - 1) / 2.0 if center is None else float(center)
    X, Y, Z = np.meshgrid(np.arange(n, dtype=float), np.arange(n, dtype=float),
                          np.arange(n, dtype=float), indexing="ij")
    rho = np.sqrt((X - c) ** 2 + (Y - c) ** 2)
    phase = charge * np.arctan2(Z - c, rho - radius)
    dist = np.sqrt((rho - radius) ** 2 + (Z - c) ** 2)
    amp = np.tanh(dist / core_width)
    return (amp * np.exp(1j * phase)).astype(np.complex128)


def _compact_loops(trace: dict[str, Any], min_n: int, min_len: float) -> list[dict[str, Any]]:
    out = []
    for i, lp in enumerate(trace.get("loops") or []):
        n_pts = int(lp.get("n_points") or 0)
        length = float(lp.get("length") or 0.0)
        if n_pts < min_n or length < min_len:
            continue
        cx, cy, cz = lp["centroid"]
        out.append({
            "i": i,
            "n_points": n_pts,
            "length": length,
            "effective_radius": float(lp.get("effective_radius") or 0.0),
            "mean_curvature": float(lp.get("mean_curvature") or 0.0),
            "centroid": [float(cx), float(cy), float(cz)],
        })
    return out


def _neck_min_self_distance(loop: dict[str, Any], skip: int = 4) -> float | None:
    """Smallest distance between non-adjacent points on one loop (a waist proxy).

    Observational only — not a success gate. A pinch would make this drop;
    a round ring keeps it near the diameter.
    """
    pts = np.asarray(loop.get("points") or [], dtype=float)
    n = len(pts)
    if n < 2 * skip + 2:
        return None
    best = np.inf
    for i in range(n):
        for j in range(i + skip, n - skip):
            if min(j - i, n - (j - i)) < skip:
                continue
            d = float(np.linalg.norm(pts[i] - pts[j]))
            if d < best:
                best = d
    return None if not math.isfinite(best) else best


def _trace_row(psi: np.ndarray, step: int, dt: float) -> dict[str, Any]:
    tr = trace_vortex_lines(psi)
    compact = _compact_loops(tr, PINCH_SPLIT_CRITERION["min_loop_n_points"],
                             PINCH_SPLIT_CRITERION["min_loop_length"])
    necks = []
    for lp in tr.get("loops") or []:
        if int(lp.get("n_points") or 0) >= PINCH_SPLIT_CRITERION["min_loop_n_points"]:
            necks.append(_neck_min_self_distance(lp))
    amp = np.abs(psi)
    return {
        "step": int(step),
        "physical_time": float(step * dt),
        "mean_amp": float(amp.mean()),
        "amp_std": float(amp.std()),
        "amp_min": float(amp.min()),
        "xy_plaquette_defects": int(measures.winding_defect_count(psi)),
        "n_loops_raw": len(tr.get("loops") or []),
        "n_loops_bulk": len(compact),
        "n_open_paths": len(tr.get("open_paths") or []),
        "n_cubes_pierced": int(tr.get("n_cubes_pierced") or 0),
        "n_cubes_overloaded": int(tr.get("n_cubes_overloaded") or 0),
        "n_healed": int(tr.get("n_healed_connections") or 0),
        "n_unhealed_dangling": int(tr.get("n_unhealed_dangling") or 0),
        "loops": compact,
        "neck_min_self_distance": None if not necks else min(v for v in necks if v is not None) if any(v is not None for v in necks) else None,
        "authenticity": three_d_authenticity(psi),
    }


def _slice_dark_blobs(amp2d: np.ndarray, frac: float = 0.35) -> int:
    """Count connected low-amplitude blobs on a 2D slice (picture-language, not topology)."""
    a = np.asarray(amp2d, float)
    thr = float(a.min()) + frac * (float(a.max()) - float(a.min()) + 1e-15)
    mask = a < thr
    if not mask.any():
        return 0
    # 4-connected flood fill, no scipy required
    seen = np.zeros(mask.shape, dtype=bool)
    n = 0
    h, w = mask.shape
    for i in range(h):
        for j in range(w):
            if not mask[i, j] or seen[i, j]:
                continue
            n += 1
            stack = [(i, j)]
            seen[i, j] = True
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
    return n


def _meridional_two_dot_note(psi: np.ndarray) -> dict[str, Any]:
    """Honesty check: a meridional slice of one ring shows two dark dots."""
    n = psi.shape[0]
    mid = n // 2
    xz = np.abs(psi[:, mid, :])
    yz = np.abs(psi[mid, :, :])
    xy = np.abs(psi[:, :, mid])
    return {
        "xy_mid_dark_blobs": _slice_dark_blobs(xy),
        "xz_mid_dark_blobs": _slice_dark_blobs(xz),
        "yz_mid_dark_blobs": _slice_dark_blobs(yz),
        "note": (
            "Two dark blobs on a meridional (xz/yz) slice can be ONE ring "
            "piercing the plane twice. That is not two rings."
        ),
    }


def _save_slices(prefix: str, psi: np.ndarray, loops: list[dict[str, Any]] | None = None) -> dict[str, str]:
    n = psi.shape[0]
    mid = n // 2
    amp = np.abs(psi)
    phase = np.angle(psi)
    paths: dict[str, str] = {}
    for name, sl, ph in (
        ("xy", amp[:, :, mid], phase[:, :, mid]),
        ("xz", amp[:, mid, :], phase[:, mid, :]),
        ("yz", amp[mid, :, :], phase[mid, :, :]),
    ):
        ap = str(PNG / f"{prefix}_{name}_amp.png")
        pp = str(PNG / f"{prefix}_{name}_phase.png")
        snapshot.render_field(sl, ap, diverging=False, symmetric=False, px=360)
        snapshot.render_field(ph, pp, diverging=True, symmetric=True, px=360)
        paths[f"{name}_amp"] = ap
        paths[f"{name}_phase"] = pp
    # loop projection on xy (diagnostic overlay, not a physical field)
    canvas = np.clip(amp.max(axis=2), 0, None)
    # invert so holes (cores) are bright-ish on viridis after min-max: keep raw amp, overlay later
    proj_path = str(PNG / f"{prefix}_xy_maxamp.png")
    snapshot.render_field(canvas, proj_path, diverging=False, symmetric=False, px=360)
    paths["xy_maxamp"] = proj_path
    hole = canvas.max() - canvas
    hole_path = str(PNG / f"{prefix}_xy_amp_holes.png")
    snapshot.render_field(hole, hole_path, diverging=False, symmetric=False, px=360)
    paths["xy_amp_holes"] = hole_path
    if loops:
        rgb = snapshot.colormap(
            snapshot._upscale(
                (hole - float(hole.min())) / (float(hole.max() - hole.min()) + 1e-12),
                360,
            ),
            diverging=False,
        )
        h, w, _ = rgb.shape
        sy, sx = h / float(n), w / float(n)
        colors = [(255, 255, 255), (220, 40, 40), (40, 180, 220), (240, 200, 40)]
        marked = np.array(rgb, copy=True)
        for li, lp in enumerate(loops):
            col = colors[li % len(colors)]
            # draw from stored centroids only in compact form — use a small cross
            cx, cy, _cz = lp["centroid"]
            py = int(round(float(cy) * sy)) % h
            px = int(round(float(cx) * sx)) % w
            r = max(3, int(round(min(h, w) / 40.0)))
            marked[max(0, py - r):min(h, py + r + 1), px] = col
            marked[py, max(0, px - r):min(w, px + r + 1)] = col
        overlay = str(PNG / f"{prefix}_loop_centroids.png")
        snapshot.write_png(marked, overlay)
        paths["loop_centroids"] = overlay
    return paths


def _draw_loop_polylines(prefix: str, trace: dict[str, Any], n: int) -> str | None:
    """Draw traced loop polylines projected to xy. Diagnostic overlay only."""
    loops = [lp for lp in (trace.get("loops") or [])
             if int(lp.get("n_points") or 0) >= PINCH_SPLIT_CRITERION["min_loop_n_points"]]
    if not loops:
        return None
    canvas = np.zeros((n, n), dtype=float)
    for li, lp in enumerate(loops, start=1):
        pts = np.asarray(lp["points"], dtype=float)
        for x, y, _z in pts:
            ix = int(np.clip(round(x), 0, n - 1))
            iy = int(np.clip(round(y), 0, n - 1))
            canvas[ix, iy] = max(canvas[ix, iy], float(li))
            # thicken
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = ix + dx, iy + dy
                if 0 <= xx < n and 0 <= yy < n:
                    canvas[xx, yy] = max(canvas[xx, yy], float(li) * 0.7)
    path = str(PNG / f"{prefix}_loops_xy.png")
    snapshot.render_field(canvas, path, diverging=False, symmetric=False, px=360)
    return path


def _assess_pinch(series: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the a-priori isolated 1→2 criterion. Does not retune after seeing pictures."""
    one_run = 0
    two_run = 0
    max_one_run = 0
    max_two_run = 0
    first_one = None
    first_two_after_one = None
    max_loops = 0
    saw_collapse_from_one = False
    isolated_one_frames = []
    isolated_two_frames = []
    open_cap = PINCH_SPLIT_CRITERION["max_open_paths_when_isolated"]
    need_one = PINCH_SPLIT_CRITERION["isolated_one_min_frames"]
    need_two = PINCH_SPLIT_CRITERION["isolated_two_min_frames"]

    had_isolated_one = False
    for row in series:
        n = int(row["n_loops_bulk"])
        nopen = int(row["n_open_paths"])
        max_loops = max(max_loops, n)
        isolated = nopen <= open_cap
        if n == 1 and isolated:
            one_run += 1
            two_run = 0
            max_one_run = max(max_one_run, one_run)
            if first_one is None:
                first_one = row["step"]
            if one_run >= need_one:
                had_isolated_one = True
                isolated_one_frames.append(row["step"])
        elif n == 2 and isolated:
            two_run += 1
            one_run = 0
            max_two_run = max(max_two_run, two_run)
            if had_isolated_one and first_two_after_one is None:
                first_two_after_one = row["step"]
            if two_run >= need_two and had_isolated_one:
                isolated_two_frames.append(row["step"])
        else:
            if n == 0 and had_isolated_one:
                saw_collapse_from_one = True
            one_run = 0
            two_run = 0

    both_persist = bool(isolated_one_frames) and bool(isolated_two_frames)
    return {
        "criterion": PINCH_SPLIT_CRITERION,
        "max_bulk_loops_in_series": max_loops,
        "max_isolated_one_run": max_one_run,
        "max_isolated_two_run": max_two_run,
        "first_isolated_one_step": first_one,
        "first_isolated_two_after_one_step": first_two_after_one,
        "isolated_one_then_two_both_persist": both_persist,
        "collapse_1_to_0_after_isolated_one": saw_collapse_from_one,
        "looks_like_tangle": max_loops >= 4,
        "ring_pinch_split_observed": both_persist,
        "lane": "amplitude_holes_winding" if max_loops >= 1 else "no_closed_bulk_loop",
        "not_cell_division": True,
        "not_f7_network_fission": True,
    }


def _evolve_tdgl(psi0: np.ndarray, p: dict[str, Any], steps: int, sample_every: int,
                 png_prefix: str | None, png_at: list[int] | None = None) -> dict[str, Any]:
    psi = np.array(psi0, copy=True)
    dt = float(p["dt"])
    series = []
    pngs: dict[str, Any] = {}
    traces_for_draw: dict[int, dict[str, Any]] = {}
    want = set(png_at or [])
    if png_prefix:
        want.update({0, steps})
    t0 = _trace_row(psi, 0, dt)
    t0["physical_time"] = 0.0
    series.append(t0)
    if png_prefix:
        pngs["t000"] = _save_slices(f"{png_prefix}_t000", psi, t0["loops"])
        tr0 = trace_vortex_lines(psi)
        drawn = _draw_loop_polylines(f"{png_prefix}_t000", tr0, psi.shape[0])
        if drawn:
            pngs["t000_loops"] = drawn
        pngs["t000_two_dot"] = _meridional_two_dot_note(psi)
        traces_for_draw[0] = tr0

    for s in range(1, steps + 1):
        psi = gl.step(psi, (s - 1) * dt, p)
        if not np.all(np.isfinite(psi)):
            break
        take = (s % sample_every == 0) or (s == steps) or (s in want)
        if not take:
            continue
        row = _trace_row(psi, s, dt)
        series.append(row)
        if png_prefix and s in want:
            key = f"s{s:04d}"
            pngs[key] = _save_slices(f"{png_prefix}_{key}", psi, row["loops"])
            tr = trace_vortex_lines(psi)
            drawn = _draw_loop_polylines(f"{png_prefix}_{key}", tr, psi.shape[0])
            if drawn:
                pngs[f"{key}_loops"] = drawn
            pngs[f"{key}_two_dot"] = _meridional_two_dot_note(psi)
            traces_for_draw[s] = tr

    if png_prefix:
        pngs["end"] = _save_slices(f"{png_prefix}_end", psi, series[-1]["loops"])
        trn = trace_vortex_lines(psi)
        drawn = _draw_loop_polylines(f"{png_prefix}_end", trn, psi.shape[0])
        if drawn:
            pngs["end_loops"] = drawn
        pngs["end_two_dot"] = _meridional_two_dot_note(psi)

    traj = [{"mean_amp": r["mean_amp"],
             "sk_prom": measures.structure_factor_peak(
                 psi if r is series[-1] else psi)[1],
             "defects": r["xy_plaquette_defects"]} for r in series]
    # structure factor only at end (cheap); fill series sk from end for assess
    _, prom_end = measures.structure_factor_peak(psi)
    traj = [{"mean_amp": r["mean_amp"], "sk_prom": prom_end,
             "defects": r["xy_plaquette_defects"]} for r in series]
    level, detected, mb = measures.assess_level(traj) if traj else (0, {}, {})
    pinch = _assess_pinch(series)
    return {
        "grid": list(psi.shape),
        "steps": steps,
        "dt": dt,
        "sample_every": sample_every,
        "endpoint_digest": _field_digest(psi),
        "t0": {k: t0[k] for k in t0 if k != "loops"},
        "end": {k: series[-1][k] for k in series[-1] if k != "loops"},
        "series": series,
        "pinch": pinch,
        "assess_level": {"reached_level": level, "detected": detected, "measured_by": mb},
        "pngs": pngs,
        "authenticity_end": three_d_authenticity(psi),
    }


def run_grown_tdgl(seed: int, n: int = 32, steps: int = 280, sample_every: int = 20) -> dict[str, Any]:
    """育った: official g001 law + undifferentiated IC. Not an official Room."""
    genesis = {
        "model": gl.MODEL_ID,
        "seed": seed,
        "initial_state": {"noise_amplitude": 0.01, "correlation_length": 1.0},
        "protocol": {"quench": {"start": 0.0, "duration": 8.0}},
    }
    p = dict(gl.DEFAULTS)
    p["noise_amplitude"] = 0.01
    rng = np.random.default_rng(seed)
    psi0 = gl.make_initial((n, n, n), p["noise_amplitude"], rng)
    png_at = [0, steps // 3, 2 * steps // 3, steps]
    out = _evolve_tdgl(psi0, p, steps, sample_every,
                       png_prefix=f"grown_s{seed}", png_at=png_at)
    out.update({
        "lane": "grown_from_undifferentiated_ic",
        "label_ja": "育った",
        "placed_ring": False,
        "official_room": False,
        "dimension_label": f"local-3d {n}^3 (NOT official 64^3 Room)",
        "genesis": genesis,
        "law": "g001_ginzburg_landau_quench local Laplacian (np.roll), explicit Euler",
    })
    return out


def run_placed_tdgl_ring(n: int = 32, radius: float = 8.0, steps: int = 160,
                         sample_every: int = 8, seed: int = 0) -> dict[str, Any]:
    """置いた: one circular vortex ring in already-ordered TDGL. Capability check."""
    p = dict(gl.DEFAULTS)
    p["quench_duration"] = 0.0  # eps = +eps_final from t=0; ordered background
    psi0 = _ring_field(n, radius)
    # tiny undifferentiated noise on top of the ring — not a waist, not a split site
    rng = np.random.default_rng(seed)
    psi0 = psi0 + 1e-3 * (rng.standard_normal(psi0.shape) + 1j * rng.standard_normal(psi0.shape))
    png_at = [0, steps // 3, 2 * steps // 3, steps]
    out = _evolve_tdgl(psi0, p, steps, sample_every,
                       png_prefix="placed_tdgl_ring", png_at=png_at)
    out.update({
        "lane": "placed_circular_ring_capability",
        "label_ja": "置いた",
        "placed_ring": True,
        "ring_radius_imprinted": radius,
        "split_location_seeded": False,
        "target_morphology_seeded": False,
        "figure8_or_waist_seeded": False,
        "official_room": False,
        "dimension_label": f"local-3d {n}^3 TDGL (NOT official Room)",
        "law": "g001_ginzburg_landau_quench, quench_duration=0 (eps=+1), local Laplacian",
        "core_resolution_note": (
            "healing length ξ ~ 1 cell at dx=1; cells_per_core_radius is ~1, "
            "below the 3D_NATIVE_POLICY guide of ≥8. Coarse on purpose as the "
            "smallest honest 3D host check."
        ),
    })
    return out


def run_placed_gpe_ring(n: int = 32, radius: float = 7.0, n_imag: int = 40,
                        n_real: int = 160, sample: int = 16) -> dict[str, Any]:
    """置いた: e003-style GPE circular ring. FFT split-step = shortcut, fidelity lower."""
    g, mu, dt, dtau = 1.0, 1.0, 0.1, 0.05
    c = (n - 1) / 2.0
    V = 0.0
    k2 = k_squared_3d(n)
    phase0 = gpe_field.vortex_ring_phase(n, radius, charge=1)
    psi = np.sqrt(mu) * np.exp(1j * phase0)
    norm0 = gpe_measure.norm(psi)
    for _ in range(n_imag):
        psi = gpe_field.step_imag_3d(psi, V, k2, g, mu, dtau)
        psi *= np.sqrt(norm0 / np.sum(np.abs(psi) ** 2))
        psi = np.abs(psi) * np.exp(1j * phase0)

    p_dummy_dt = dt
    series = []
    pngs: dict[str, Any] = {}
    t0 = _trace_row(psi, 0, dt)
    t0["physical_time"] = 0.0
    series.append(t0)
    pngs["t000"] = _save_slices("placed_gpe_ring_t000", psi, t0["loops"])
    drawn = _draw_loop_polylines("placed_gpe_ring_t000", trace_vortex_lines(psi), n)
    if drawn:
        pngs["t000_loops"] = drawn
    pngs["t000_two_dot"] = _meridional_two_dot_note(psi)

    want = {0, n_real // 3, 2 * n_real // 3, n_real}
    for s in range(1, n_real + 1):
        psi = gpe_field.step_real_3d(psi, V, k2, g, mu, dt)
        take = (s % sample == 0) or (s == n_real) or (s in want)
        if not take:
            continue
        row = _trace_row(psi, s, p_dummy_dt)
        series.append(row)
        if s in want:
            key = f"s{s:04d}"
            pngs[key] = _save_slices(f"placed_gpe_ring_{key}", psi, row["loops"])
            tr = trace_vortex_lines(psi)
            drawn = _draw_loop_polylines(f"placed_gpe_ring_{key}", tr, n)
            if drawn:
                pngs[f"{key}_loops"] = drawn
            pngs[f"{key}_two_dot"] = _meridional_two_dot_note(psi)

    pngs["end"] = _save_slices("placed_gpe_ring_end", psi, series[-1]["loops"])
    drawn = _draw_loop_polylines("placed_gpe_ring_end", trace_vortex_lines(psi), n)
    if drawn:
        pngs["end_loops"] = drawn
    pngs["end_two_dot"] = _meridional_two_dot_note(psi)

    return {
        "lane": "placed_circular_ring_capability",
        "label_ja": "置いた",
        "placed_ring": True,
        "white": "damped-free 3D GPE (e003 family), NOT g001 TDGL",
        "solver": "spectral split-step FFT — shortcut; local×parallel fidelity is lower",
        "ring_radius_imprinted": radius,
        "n_imag": n_imag,
        "split_location_seeded": False,
        "figure8_or_waist_seeded": False,
        "official_room": False,
        "dimension_label": f"micro-3d {n}^3 GPE (NOT official Room)",
        "grid": [n, n, n],
        "steps": n_real,
        "dt": dt,
        "endpoint_digest": _field_digest(psi),
        "t0": {k: t0[k] for k in t0 if k != "loops"},
        "end": {k: series[-1][k] for k in series[-1] if k != "loops"},
        "series": series,
        "pinch": _assess_pinch(series),
        "pngs": pngs,
        "authenticity_end": three_d_authenticity(psi),
        "imprint_not_periodic_z": True,
        "e003_known": "circular GPE ring self-propagates as ONE; this run asks whether n_loops stays 1",
    }


def lookup_official_room() -> dict[str, Any]:
    """Read stored official Room facts. Display volume is NOT used as physics."""
    base = _REPO / "rooms/official/room-g001-a"
    emergence = json.loads((base / "emergence.json").read_text())
    room = json.loads((base / "room.yaml").read_text()) if False else None
    # yaml may not have a json parser; read README facts we already have
    field_meta = {}
    field_path = base / "runs/seed-0000/field.json"
    pngs: dict[str, str] = {}
    if field_path.exists():
        doc = json.loads(field_path.read_text())
        field_meta = {
            "grid": doc.get("grid"),
            "nframes": doc.get("nframes"),
            "dimension": doc.get("dimension"),
            "honesty": doc.get("honesty"),
            "times_head": (doc.get("times") or [])[:3],
            "times_tail": (doc.get("times") or [])[-3:],
            "physics": False,
            "reason": "20^3 uint8 display lens, interpolated_for_display",
        }
        # render last-frame mid slices from DISPLAY volume only, labeled as such
        den = doc["lenses"]["density"]
        arr = np.frombuffer(base64.b64decode(den["data_b64"]), np.uint8)
        g = doc["grid"]
        nf = int(doc["nframes"])
        if arr.size == nf * int(np.prod(g)):
            vol = arr.reshape((nf,) + tuple(g)).astype(float)
            vol = den["vmin"] + (den["vmax"] - den["vmin"]) * vol / 255.0
            last = vol[-1]
            mid = last.shape[2] // 2
            snapshot.render_field(last[:, :, mid], str(PNG / "official_display_end_xy_density.png"),
                                  diverging=False, px=360)
            snapshot.render_field(last[:, last.shape[1] // 2, :],
                                  str(PNG / "official_display_end_xz_density.png"),
                                  diverging=False, px=360)
            snapshot.render_field(np.sqrt(np.clip(last[:, :, mid], 0, None)),
                                  str(PNG / "official_display_end_xy_ampproxy.png"),
                                  diverging=False, px=360)
            pngs["official_display_end_xy"] = str(PNG / "official_display_end_xy_density.png")
            pngs["official_display_end_xz"] = str(PNG / "official_display_end_xz_density.png")
            first = vol[0]
            snapshot.render_field(first[:, :, mid], str(PNG / "official_display_t0_xy_density.png"),
                                  diverging=False, px=360)
            pngs["official_display_t0_xy"] = str(PNG / "official_display_t0_xy_density.png")
    seed_rows = []
    for s in (0, 1, 2):
        em = json.loads((base / f"runs/seed-{s:04d}/emergence.json").read_text())
        sm = json.loads((base / f"runs/seed-{s:04d}/summary.json").read_text())
        seed_rows.append({
            "seed": s,
            "reached_level": em.get("reached_level"),
            "candidate_level": em.get("candidate_level"),
            "defect_count": (em.get("measured_by") or {}).get("defect_count"),
            "mean_amplitude_growth": (em.get("measured_by") or {}).get("mean_amplitude_growth"),
            "final_mean_amplitude": sm.get("final_mean_amplitude"),
            "target_shape_seeded": (em.get("natural_emergence") or {}).get("target_shape_seeded"),
        })
    return {
        "meta": OFFICIAL_ROOM,
        "emergence_room": emergence,
        "seeds": seed_rows,
        "display_field": field_meta,
        "pngs": pngs,
        "loop_tracer_was_not_the_official_diagnostic": True,
        "honest_reading": (
            "241/173/117 xy-plaquette piercings is a dense vortex-line tangle, "
            "not one isolated ring. Official Room does not record a 1-ring→2-rings event."
        ),
        "room_yaml_unused": room,
    }


def _series_loop_table(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in series:
        rows.append({
            "step": r["step"],
            "t": r["physical_time"],
            "n_loops_bulk": r["n_loops_bulk"],
            "n_loops_raw": r["n_loops_raw"],
            "n_open_paths": r["n_open_paths"],
            "xy_plaquette_defects": r["xy_plaquette_defects"],
            "mean_amp": r["mean_amp"],
            "neck": r.get("neck_min_self_distance"),
            "radii": [lp["effective_radius"] for lp in r.get("loops") or []],
            "lengths": [lp["length"] for lp in r.get("loops") or []],
        })
    return rows


def main() -> None:
    print("=== ring-pinch verify (3D, not an official Room) ===", flush=True)
    print("looking up official room-g001-a (stored facts, no 64^3 rerun) ...", flush=True)
    official = lookup_official_room()
    print("  defects", [s["defect_count"] for s in official["seeds"]], flush=True)

    print("grown TDGL local-3d 32^3 seed=0 from undifferentiated IC ...", flush=True)
    grown0 = run_grown_tdgl(0)
    print(
        "  end n_loops_bulk=%s n_open=%s xy_defects=%s pinch=%s L=%s"
        % (grown0["end"]["n_loops_bulk"], grown0["end"]["n_open_paths"],
           grown0["end"]["xy_plaquette_defects"],
           grown0["pinch"]["ring_pinch_split_observed"],
           grown0["assess_level"]["reached_level"]),
        flush=True,
    )

    print("grown TDGL local-3d 32^3 seed=1 ...", flush=True)
    grown1 = run_grown_tdgl(1)
    print(
        "  end n_loops_bulk=%s n_open=%s pinch=%s"
        % (grown1["end"]["n_loops_bulk"], grown1["end"]["n_open_paths"],
           grown1["pinch"]["ring_pinch_split_observed"]),
        flush=True,
    )

    print("placed circular ring TDGL 32^3 R=8 (置いた capability) ...", flush=True)
    placed_tdgl = run_placed_tdgl_ring()
    print(
        "  t0 loops=%s end loops=%s pinch=%s collapse=%s"
        % (placed_tdgl["t0"]["n_loops_bulk"], placed_tdgl["end"]["n_loops_bulk"],
           placed_tdgl["pinch"]["ring_pinch_split_observed"],
           placed_tdgl["pinch"]["collapse_1_to_0_after_isolated_one"]),
        flush=True,
    )

    print("placed circular ring GPE 32^3 R=7 (置いた, FFT shortcut) ...", flush=True)
    placed_gpe = run_placed_gpe_ring()
    print(
        "  t0 loops=%s end loops=%s pinch=%s"
        % (placed_gpe["t0"]["n_loops_bulk"], placed_gpe["end"]["n_loops_bulk"],
           placed_gpe["pinch"]["ring_pinch_split_observed"]),
        flush=True,
    )

    verdict = {
        "official_64cubed_is_a_tangle_not_one_ring": all(
            (s.get("defect_count") or 0) > 20 for s in official["seeds"]
        ),
        "grown_32cubed_isolated_ring_pinch_split": bool(
            grown0["pinch"]["ring_pinch_split_observed"]
            or grown1["pinch"]["ring_pinch_split_observed"]
        ),
        "placed_tdgl_ring_pinch_split": bool(placed_tdgl["pinch"]["ring_pinch_split_observed"]),
        "placed_gpe_ring_pinch_split": bool(placed_gpe["pinch"]["ring_pinch_split_observed"]),
        "two_dots_on_a_slice_are_not_two_rings": True,
        "not_cell_division": True,
        "not_new_law": True,
        "not_official_3d_room": True,
        "dimension_honest": "local-3d 32^3 + stored official 64^3 summaries; no 64^3 rerun",
    }
    out = {
        "version": 1,
        "question": (
            "Can this physics show one ring-like vortex (closed loop of winding) "
            "persisting as one, cinching, then becoming two separately trackable loops?"
        ),
        "claim_tier_of_this_file": "measured",
        "role": {"primary": "N", "secondary": ["V", "F"]},
        "not_official_room": True,
        "not_life": True,
        "not_cell_division": True,
        "not_new_law": True,
        "vortex_core_lane": "amplitude_holes_with_winding (not dense high-amp blobs)",
        "jobs_kept_separate": {
            "triangle": "sitting / 3-way meeting (PR 133 / F4) — not this report",
            "two_point_cores_on_a_plane": "leftover ± pair or a meridional slice of ONE ring",
            "ring_pinch": "1 closed loop → 2 closed loops (this report; not observed here unless verdict says so)",
            "F7": "network fission, not cytokinesis",
        },
        "criterion_a_priori": PINCH_SPLIT_CRITERION,
        "official_room_g001_a": official,
        "grown_tdgl_seed0": {**{k: v for k, v in grown0.items() if k != "series"},
                             "loop_table": _series_loop_table(grown0["series"])},
        "grown_tdgl_seed1": {**{k: v for k, v in grown1.items() if k != "series"},
                             "loop_table": _series_loop_table(grown1["series"])},
        "placed_tdgl_ring": {**{k: v for k, v in placed_tdgl.items() if k != "series"},
                             "loop_table": _series_loop_table(placed_tdgl["series"])},
        "placed_gpe_ring": {**{k: v for k, v in placed_gpe.items() if k != "series"},
                            "loop_table": _series_loop_table(placed_gpe["series"])},
        "verdict": verdict,
        "honesty": {
            "visualization_separated_from_physics": True,
            "official_display_volume_is_not_physics": True,
            "placed_ring_is_not_grown": True,
            "fft_gpe_fidelity_lower_than_local_tdgl": True,
            "core_under_resolved_vs_3d_native_policy": True,
            "tracer_does_not_close_across_periodic_seam": True,
        },
    }
    # drop bulky png absolute paths' parent duplication by keeping filenames
    path = OUT / "measurements.json"
    path.write_text(json.dumps(_jsonable(out), indent=2, ensure_ascii=False))
    print("wrote", path, flush=True)
    print("VERDICT", json.dumps(verdict), flush=True)


if __name__ == "__main__":
    main()
