#!/usr/bin/env python3
"""First honest check: after amplitude grows from undifferentiated white, is there
ONE connected dense inside with a closed skin that persists?

Not a Room. Not a vesicle. Uses existing detectors:
  scipy.ndimage.label (connected components),
  genesis.diagnostics.topology3d.three_axis_percolation,
  genesis.diagnostics.topology_betti.betti3d (3D balloon vs doughnut),
  genesis.diagnostics.measures.winding_defect_count (hole card, separate).

Physics: existing g001 TDGL only. IC = uniform near-zero + tiny complex noise.
No bag, membrane, circle, or body location is placed.

A-priori criteria below are NOT retuned after seeing pictures.
Success is not triangle, not ring 1→2, not F7.
If no bag appears, that is the finding. Do not rescue it by counting holes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from genesis.diagnostics import measures  # noqa: E402
from genesis.diagnostics import topology3d  # noqa: E402
from genesis.diagnostics.topology_betti import betti3d  # noqa: E402
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tools.snapshot import colormap, render_field, write_png  # noqa: E402

HERE = Path(__file__).resolve().parent
PNG = HERE / "png"
ARTIFACT = Path("/opt/cursor/artifacts/verify-one-body-bag")

# ---- a-priori gates (frozen before looking at grown fields) ----
BAG_CRITERION = {
    "amp_max_grown": 0.3,           # local order above the noise floor (a bag need not fill the room)
    "mean_amp_grown": 0.3,          # whole-field order (room climate). Informational; not a bag gate
    "dense_rel_max": 0.5,           # high-amp bulk = yellow ground
    "min_body_frac": 0.02,          # not a speck
    "max_body_frac": 0.40,          # not the room
    "max_span_frac": 0.90,          # not wrapping/percolating
    "persist_snapshots": 5,         # consecutive bag-candidate frames
    "hole_rel_max": 0.25,           # amplitude holes (cores)
    "min_hole_voxels": 1,
}
# Do not retune. Not a success: triangle, ring-pinch, F7, hole-count.

NOT_SUCCESS = ("triangle", "ring_pinch_1_to_2", "F7", "hole_count_as_body")


def sha256_field(psi: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes())
    h.update(np.ascontiguousarray(psi.imag).tobytes())
    return h.hexdigest()


def _label6(mask: np.ndarray):
    structure = ndimage.generate_binary_structure(mask.ndim, 1)
    return ndimage.label(mask, structure=structure)


def _span_frac(coords, shape):
    if coords.size == 0:
        return [0.0] * len(shape)
    return [
        float((coords[:, ax].max() - coords[:, ax].min() + 1) / shape[ax])
        for ax in range(len(shape))
    ]


def component_table(mask: np.ndarray) -> list[dict]:
    lbl, n = _label6(mask)
    rows = []
    total = float(mask.size)
    for lab in range(1, n + 1):
        coords = np.argwhere(lbl == lab)
        frac = float(coords.shape[0] / total)
        span = _span_frac(coords, mask.shape)
        rows.append({
            "label": int(lab),
            "voxels": int(coords.shape[0]),
            "frac": frac,
            "span_frac": span,
            "percolates": bool(any(s >= BAG_CRITERION["max_span_frac"] for s in span)),
            "centroid": [float(x) for x in coords.mean(axis=0)],
        })
    rows.sort(key=lambda r: r["voxels"], reverse=True)
    return rows


def enclosed_cavities(mask: np.ndarray) -> int:
    """Background components that do not touch the padded border (2D or 3D)."""
    m = np.pad(np.asarray(mask, bool), 1)
    bg, nbg = ndimage.label(~m, structure=ndimage.generate_binary_structure(m.ndim, 1))
    faces = [bg.take(0, ax).ravel() for ax in range(m.ndim)]
    faces += [bg.take(-1, ax).ravel() for ax in range(m.ndim)]
    border = set(np.unique(np.concatenate(faces)))
    return int(sum(1 for lab in range(1, nbg + 1) if lab not in border))


def body_topology_name(mask: np.ndarray) -> dict:
    """Balloon vs doughnut for ONE bounded component. Not required to be doughnut."""
    m = np.asarray(mask, bool)
    if m.ndim == 3:
        b = betti3d(m)
        if b["b0"] != 1:
            kind = "not_one_component"
        elif b["b1"] == 0 and b["b2"] == 0:
            kind = "balloon"
        elif b["b1"] >= 1 and b["b2"] == 0:
            kind = "doughnut"
        else:
            kind = "other"
        return {"kind": kind, **{k: b[k] for k in ("b0", "b1", "b2", "chi", "genus")}}
    cavities = enclosed_cavities(m)
    lbl, n = _label6(m)
    kind = "balloon" if (n == 1 and cavities == 0) else (
        "doughnut" if (n == 1 and cavities >= 1) else "not_one_component"
    )
    return {"kind": kind, "b0": int(n), "enclosed_cavities": int(cavities)}


def classify_amp(amp: np.ndarray, *, windings: int | None = None) -> dict:
    """Classify a real amplitude field. Dense = inside candidate. Holes scored separately."""
    amp = np.asarray(amp, float)
    amax = float(amp.max()) if amp.size else 0.0
    mean = float(amp.mean())
    local_order = bool(amax >= BAG_CRITERION["amp_max_grown"])
    field_ordered = bool(mean >= BAG_CRITERION["mean_amp_grown"])
    dense_thr = BAG_CRITERION["dense_rel_max"] * max(amax, 1e-30)
    hole_thr = BAG_CRITERION["hole_rel_max"] * max(amax, 1e-30)
    dense = amp >= dense_thr
    holes = amp < hole_thr
    dense_frac = float(dense.mean())
    hole_frac = float(holes.mean())
    dense_rows = component_table(dense)
    hole_rows = component_table(holes)
    significant = [
        r for r in dense_rows
        if r["frac"] >= BAG_CRITERION["min_body_frac"]
    ]
    largest = dense_rows[0] if dense_rows else None
    room_bulk = bool(dense_frac > BAG_CRITERION["max_body_frac"])
    one_bounded = bool(
        local_order
        and (not room_bulk)
        and len(significant) == 1
        and largest is not None
        and not largest["percolates"]
        and BAG_CRITERION["min_body_frac"] <= largest["frac"] <= BAG_CRITERION["max_body_frac"]
    )
    topo = {"kind": "not_applicable_no_bounded_body"}
    if one_bounded and largest is not None:
        lbl, _ = _label6(dense)
        topo = body_topology_name(lbl == largest["label"])
    perc = topology3d.three_axis_percolation(dense) if dense.ndim == 3 else {
        "spans_all": bool(largest["percolates"]) if largest else False,
        "span_frac": largest["span_frac"] if largest else [0.0, 0.0],
        "n_components": len(dense_rows),
    }
    return {
        "mean_amp": mean,
        "amp_max": amax,
        "amp_min": float(amp.min()) if amp.size else 0.0,
        "grown": field_ordered,
        "local_order": local_order,
        "dense_frac": dense_frac,
        "hole_frac": hole_frac,
        "n_dense_components": len(dense_rows),
        "n_significant_dense": len(significant),
        "n_hole_components": len(hole_rows),
        "dense_is_room_bulk": room_bulk,
        "largest_dense": largest,
        "bag_candidate": one_bounded,
        "body_topology": topo,
        "percolation": perc,
        "winding_defect_count": windings,
        "holes_are_not_the_body": True,
    }


def classify_psi(psi: np.ndarray) -> dict:
    windings = int(measures.winding_defect_count(psi))
    out = classify_amp(np.abs(psi), windings=windings)
    if psi.ndim == 3:
        out["three_d_authenticity"] = topology3d.three_d_authenticity(psi)
    return out


def persist_verdict(frames: list[dict]) -> dict:
    """Same bag-candidate verdict on >= persist_snapshots consecutive grown frames."""
    need = int(BAG_CRITERION["persist_snapshots"])
    best = 0
    run = 0
    start = None
    best_span = None
    for i, fr in enumerate(frames):
        if fr["class"]["bag_candidate"]:
            run += 1
            if run == 1:
                start = i
            if run > best:
                best = run
                best_span = (start, i)
        else:
            run = 0
            start = None
    ok = bool(best >= need)
    return {
        "persistent_one_body": ok,
        "longest_consecutive_bag_frames": int(best),
        "required_consecutive": need,
        "span_indices": list(best_span) if best_span else None,
    }


def evolve(shape, seed, steps, snap_every, p=None):
    p = dict(gl.DEFAULTS if p is None else p)
    rng = np.random.default_rng(seed)
    psi = gl.make_initial(shape, p["noise_amplitude"], rng)
    t0 = psi.copy()
    frames = []

    def take(step_i, field):
        t = float(step_i * p["dt"])
        cls = classify_psi(field)
        frames.append({
            "step": int(step_i),
            "t": t,
            "class": cls,
            "sha256": sha256_field(field),
        })
        return field.copy()

    snaps = {0: take(0, psi)}
    for i in range(1, steps + 1):
        t = (i - 1) * p["dt"]
        psi = gl.step(psi, t, p)
        if not np.all(np.isfinite(psi)):
            snaps[i] = take(i, psi)
            return {
                "finite": False, "seed": seed, "shape": list(shape),
                "steps": i, "params": p, "t0_sha256": sha256_field(t0),
                "end_sha256": sha256_field(psi), "frames": frames, "fields": snaps,
            }
        if i % snap_every == 0 or i == steps:
            snaps[i] = take(i, psi)
    return {
        "finite": True,
        "seed": seed,
        "shape": list(shape),
        "steps": steps,
        "params": p,
        "t0_sha256": sha256_field(t0),
        "end_sha256": sha256_field(psi),
        "frames": frames,
        "fields": snaps,
        "persist": persist_verdict(frames),
    }


def _mid(field, ax0, ax1):
    sl = [slice(None)] * field.ndim
    for ax in range(field.ndim):
        if ax not in (ax0, ax1):
            sl[ax] = field.shape[ax] // 2
    return np.abs(field[tuple(sl)])


def _legend_rgb(amp, cls):
    amax = max(float(amp.max()), 1e-30)
    dense = amp >= BAG_CRITERION["dense_rel_max"] * amax
    holes = amp < BAG_CRITERION["hole_rel_max"] * amax
    skin = dense ^ ndimage.binary_erosion(dense, iterations=1)
    rgb = np.zeros(amp.shape + (3,), np.uint8)
    rgb[...] = (40, 40, 48)           # outside / low
    rgb[dense] = (253, 231, 37)       # dense inside (viridis yellow)
    rgb[holes] = (68, 1, 84)          # holes (viridis purple)
    rgb[skin] = (220, 80, 40)         # skin band
    return rgb


def save_pngs(tag: str, field: np.ndarray, dests: list[Path]):
    amp = np.abs(field)
    cls = classify_amp(amp)
    if amp.ndim == 2:
        planes = [("xy", amp)]
    else:
        planes = [
            ("xy", _mid(field, 0, 1)),
            ("xz", _mid(field, 0, 2)),
        ]
    paths = []
    for name, plane in planes:
        p_amp = f"{tag}_{name}_amp.png"
        p_leg = f"{tag}_{name}_dense_holes.png"
        render_field(plane, str(dests[0] / p_amp), px=360)
        write_png(np.kron(_legend_rgb(plane, cls), np.ones((max(1, 360 // plane.shape[0]),) * 2 + (1,), np.uint8)),
                  dests[0] / p_leg)
        for d in dests[1:]:
            d.mkdir(parents=True, exist_ok=True)
            render_field(plane, str(d / p_amp), px=360)
            write_png(np.kron(_legend_rgb(plane, cls), np.ones((max(1, 360 // plane.shape[0]),) * 2 + (1,), np.uint8)),
                      d / p_leg)
        paths.append(p_amp)
        paths.append(p_leg)
    return paths, cls


def _jsonable(run):
    out = {k: v for k, v in run.items() if k != "fields"}
    return json.loads(json.dumps(out, default=float))


def main() -> int:
    PNG.mkdir(parents=True, exist_ok=True)
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    dests = [PNG, ARTIFACT]
    p = dict(gl.DEFAULTS)
    picture_index = {}

    # 2D quick pictures (not an official Room; previous 48² triangle check is a different job)
    runs_2d = []
    for seed in (0, 1):
        run = evolve((48, 48), seed, steps=260, snap_every=26, p=p)
        t0 = run["fields"][0]
        end = run["fields"][max(run["fields"])]
        p0, _ = save_pngs(f"grown2d_s{seed}_t000", t0, dests)
        pe, _ = save_pngs(f"grown2d_s{seed}_end", end, dests)
        picture_index[f"2d_seed{seed}_t0"] = p0
        picture_index[f"2d_seed{seed}_end"] = pe
        runs_2d.append(_jsonable(run))
        print(f"2D seed={seed} bag_any={any(fr['class']['bag_candidate'] for fr in run['frames'])} "
              f"persist={run['persist']['persistent_one_body']} "
              f"end_dense_frac={run['frames'][-1]['class']['dense_frac']:.3f} "
              f"end_holes={run['frames'][-1]['class']['n_hole_components']} "
              f"windings={run['frames'][-1]['class']['winding_defect_count']}")

    # 3D local-32³ (runner local-3d size; NOT an official Room)
    runs_3d = []
    for seed in (0, 1):
        run = evolve((32, 32, 32), seed, steps=300, snap_every=30, p=p)
        t0 = run["fields"][0]
        end = run["fields"][max(run["fields"])]
        p0, _ = save_pngs(f"grown3d_s{seed}_t000", t0, dests)
        pe, _ = save_pngs(f"grown3d_s{seed}_end", end, dests)
        picture_index[f"3d_seed{seed}_t0"] = p0
        picture_index[f"3d_seed{seed}_end"] = pe
        # extra xz note: two dark dots on a slice are a line piercing a plane
        picture_index[f"3d_seed{seed}_end_xz_is_piercing_not_two_bodies"] = True
        runs_3d.append(_jsonable(run))
        endc = run["frames"][-1]["class"]
        print(f"3D seed={seed} bag_any={any(fr['class']['bag_candidate'] for fr in run['frames'])} "
              f"persist={run['persist']['persistent_one_body']} "
              f"end_dense_frac={endc['dense_frac']:.3f} "
              f"end_holes={endc['n_hole_components']} "
              f"windings={endc['winding_defect_count']} "
              f"3d={endc.get('three_d_authenticity', {}).get('genuinely_3d')}")

    any_bag = any(r["persist"]["persistent_one_body"] for r in runs_2d + runs_3d)
    any_candidate_frame = any(
        fr["class"]["bag_candidate"] for r in runs_2d + runs_3d for fr in r["frames"]
    )
    measurements = {
        "module": "verify-20260829-one-body-bag",
        "official_room": False,
        "question": "one connected dense inside with a closed skin that persists",
        "physics": "g001_ginzburg_landau_quench",
        "put_in": "TDGL law + uniform near-zero + noise. No bag/membrane/circle/location.",
        "criterion": BAG_CRITERION,
        "not_success": list(NOT_SUCCESS),
        "lanes_not_this_job": {
            "triangle": "PR 133",
            "ring_pinch": "PR 134",
        },
        "runs_2d": runs_2d,
        "runs_3d": runs_3d,
        "picture_index": picture_index,
        "finding": {
            "persistent_one_body_observed": bool(any_bag),
            "any_bag_candidate_frame": bool(any_candidate_frame),
            "rescued_by_counting_holes": False,
            "claimed_life_or_cell": False,
            "claimed_new_law": False,
            "torus_required": False,
        },
    }
    (HERE / "measurements.json").write_text(json.dumps(measurements, indent=2, ensure_ascii=False))
    (ARTIFACT / "measurements.json").write_text(json.dumps(measurements, indent=2, ensure_ascii=False))
    print("FINDING persistent_one_body_observed=", any_bag)
    print("wrote", HERE / "measurements.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
