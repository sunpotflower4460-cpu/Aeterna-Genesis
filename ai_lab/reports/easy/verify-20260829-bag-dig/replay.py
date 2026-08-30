#!/usr/bin/env python3
"""Dig: why the usual white + TDGL does not leave a bag (one inside with a skin).

Not a Room. No vesicle, membrane, circle, or body location is placed.
Success is not triangle, not ring 1→2, not F7, not hole-count.

Frozen bag gates match the first honest check (PR 135). They are NOT retuned
after seeing pictures. Holes are a separate card.

This script:
  1. Re-reads stored official-room lenses with the bag ruler (no 64³ rerun).
  2. Runs small same-white TDGL variants (noise coarseness, cooling speed).
  3. Maps existing two-ground records (G003) without promoting them to a bag.
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
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tools.snapshot import colormap, decode_lens, write_png  # noqa: E402

HERE = Path(__file__).resolve().parent
PNG = HERE / "png"
ARTIFACT = Path("/opt/cursor/artifacts/verify-bag-dig")

# ---- a-priori gates (frozen; identical to PR 135; do not retune) ----
BAG_CRITERION = {
    "amp_max_grown": 0.3,
    "mean_amp_grown": 0.3,
    "dense_rel_max": 0.5,
    "min_body_frac": 0.02,
    "max_body_frac": 0.40,
    "max_span_frac": 0.90,
    "persist_snapshots": 5,
    "hole_rel_max": 0.25,
    "min_hole_voxels": 1,
    "outside_abs": 0.5,  # physical |ψ| scale after quench; informational
}
NOT_SUCCESS = ("triangle", "ring_pinch_1_to_2", "F7", "hole_count_as_body")


def sha256_field(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    x = np.ascontiguousarray(arr)
    if np.iscomplexobj(x):
        h.update(x.real.tobytes())
        h.update(x.imag.tobytes())
    else:
        h.update(np.asarray(x, np.float64).tobytes())
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


def classify_amp(amp: np.ndarray, *, windings: int | None = None) -> dict:
    """Dense = inside candidate. Holes scored separately and NEVER as the body."""
    amp = np.asarray(amp, float)
    amax = float(amp.max()) if amp.size else 0.0
    mean = float(amp.mean())
    amin = float(amp.min()) if amp.size else 0.0
    local_order = bool(amax >= BAG_CRITERION["amp_max_grown"])
    field_ordered = bool(mean >= BAG_CRITERION["mean_amp_grown"])
    dense_thr = BAG_CRITERION["dense_rel_max"] * max(amax, 1e-30)
    hole_thr = BAG_CRITERION["hole_rel_max"] * max(amax, 1e-30)
    dense = amp >= dense_thr
    holes = amp < hole_thr
    dense_frac = float(dense.mean())
    hole_frac = float(holes.mean())
    outside_abs = float((amp < BAG_CRITERION["outside_abs"]).mean())
    dense_rows = component_table(dense)
    hole_rows = component_table(holes)
    significant = [r for r in dense_rows if r["frac"] >= BAG_CRITERION["min_body_frac"]]
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
    # hole count is recorded and explicitly not a bag gate
    bag_from_holes = False
    perc = topology3d.three_axis_percolation(dense) if dense.ndim == 3 else {
        "spans_all": bool(largest["percolates"]) if largest else False,
        "span_frac": largest["span_frac"] if largest else [0.0] * amp.ndim,
        "n_components": len(dense_rows),
    }
    return {
        "mean_amp": mean,
        "amp_max": amax,
        "amp_min": amin,
        "grown": field_ordered,
        "local_order": local_order,
        "dense_frac": dense_frac,
        "hole_frac": hole_frac,
        "outside_abs_frac": outside_abs,
        "n_dense_components": len(dense_rows),
        "n_significant_dense": len(significant),
        "n_hole_components": len(hole_rows),
        "dense_is_room_bulk": room_bulk,
        "largest_dense": largest,
        "bag_candidate": one_bounded,
        "bag_rescued_by_holes": bag_from_holes,
        "percolation": perc,
        "winding_defect_count": windings,
        "holes_are_not_the_body": True,
        "hist_amp": _hist_summary(amp),
    }


def classify_psi(psi: np.ndarray) -> dict:
    windings = int(measures.winding_defect_count(psi))
    out = classify_amp(np.abs(psi), windings=windings)
    if psi.ndim == 3:
        out["three_d_authenticity"] = topology3d.three_d_authenticity(psi)
    return out


def classify_signed_two_ground(phi: np.ndarray) -> dict:
    """Map a signed composition field. Two grounds sitting is NOT a bag by itself."""
    phi = np.asarray(phi, float)
    a = classify_amp(np.clip(phi, 0.0, None), windings=None)
    b = classify_amp(np.clip(-phi, 0.0, None), windings=None)
    pos = phi > 0.0
    neg = phi < 0.0
    pos_rows = component_table(pos)
    neg_rows = component_table(neg)
    return {
        "mean_phi": float(phi.mean()),
        "phi_min": float(phi.min()),
        "phi_max": float(phi.max()),
        "pos_frac": float(pos.mean()),
        "neg_frac": float(neg.mean()),
        "n_pos_components": len(pos_rows),
        "n_neg_components": len(neg_rows),
        "largest_pos": pos_rows[0] if pos_rows else None,
        "largest_neg": neg_rows[0] if neg_rows else None,
        "two_grounds_present": bool(pos.mean() > 0.05 and neg.mean() > 0.05),
        "phase_a_bag_candidate": a["bag_candidate"],
        "phase_b_bag_candidate": b["bag_candidate"],
        "one_body_bag": bool(a["bag_candidate"] ^ b["bag_candidate"]),
        "hist_phi": _hist_summary(phi),
        "holes_are_not_the_body": True,
        "not_promoted_to_bag_mainline": True,
    }


def persist_verdict(frames: list[dict]) -> dict:
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
    return {
        "persistent_one_body": bool(best >= need),
        "longest_consecutive_bag_frames": int(best),
        "required_consecutive": need,
        "span_indices": list(best_span) if best_span else None,
    }


def _hist_summary(x: np.ndarray, bins: int = 24) -> dict:
    x = np.asarray(x, float).ravel()
    if x.size == 0:
        return {"n_peaks": 0, "edges": [], "counts": []}
    counts, edges = np.histogram(x, bins=bins)
    # simple peak count: local maxima above 5% of max count
    thr = 0.05 * float(counts.max() + 1e-12)
    n_peaks = 0
    for i in range(1, len(counts) - 1):
        if counts[i] >= thr and counts[i] >= counts[i - 1] and counts[i] >= counts[i + 1]:
            n_peaks += 1
    return {
        "n_peaks": int(n_peaks),
        "bin_centers": [float(0.5 * (edges[i] + edges[i + 1])) for i in range(len(counts))],
        "counts": [int(c) for c in counts],
    }


def make_initial(shape, p, rng, corr: float = 0.0):
    psi = gl.make_initial(shape, p["noise_amplitude"], rng)
    if corr and corr > 0.5:
        psi = (
            ndimage.gaussian_filter(psi.real, corr)
            + 1j * ndimage.gaussian_filter(psi.imag, corr)
        ).astype(np.complex128)
        # keep the same rms as the white start (no extra amplitude planted)
        rms = float(np.sqrt(np.mean(np.abs(psi) ** 2)) + 1e-30)
        target = float(p["noise_amplitude"] * np.sqrt(2.0))
        psi *= target / rms
    return psi


def evolve(shape, seed, steps, snap_every, p=None, corr=0.0):
    p = dict(gl.DEFAULTS if p is None else {**gl.DEFAULTS, **p})
    rng = np.random.default_rng(seed)
    psi = make_initial(shape, p, rng, corr=corr)
    frames = []
    snaps = {}

    def take(step_i, field):
        t = float(step_i * p["dt"])
        cls = classify_psi(field)
        rec = {"step": int(step_i), "t": t, "class": cls, "sha256": sha256_field(field)}
        frames.append(rec)
        return field.copy()

    snaps[0] = take(0, psi)
    for i in range(1, steps + 1):
        t = (i - 1) * p["dt"]
        psi = gl.step(psi, t, p)
        if i % snap_every == 0 or i == steps:
            snaps[i] = take(i, psi)
    return {
        "shape": list(shape),
        "seed": int(seed),
        "steps": int(steps),
        "params": {k: float(p[k]) if isinstance(p[k], (int, float)) else p[k] for k in p},
        "corr": float(corr),
        "frames": frames,
        "persist": persist_verdict(frames),
        "snaps": snaps,
        "end_sha256": frames[-1]["sha256"],
    }


def _upscale(a, px=360):
    r = max(1, px // max(a.shape[0], 1))
    return np.kron(a, np.ones((r, r), a.dtype))


def _bar(rgb, lo_rgb, hi_rgb, label_lo, label_hi):
    """Append a physical-scale legend strip (no physics change)."""
    H, W, _ = rgb.shape
    strip = np.zeros((36, W, 3), np.uint8)
    for x in range(W):
        f = x / max(W - 1, 1)
        strip[:, x] = (np.array(lo_rgb) * (1 - f) + np.array(hi_rgb) * f).astype(np.uint8)
    # end swatches
    strip[:, :18] = lo_rgb
    strip[:, -18:] = hi_rgb
    out = np.concatenate([rgb, strip], axis=0)
    return out


def render_amp_physical(amp, path, vmax=1.0, px=360):
    a = np.asarray(amp, float)
    n = np.clip(a / max(vmax, 1e-12), 0.0, 1.0)
    rgb = colormap(_upscale(n, px), diverging=False)
    purple = (68, 1, 84)
    yellow = (253, 231, 37)
    rgb = _bar(rgb, purple, yellow, "hole", "dense")
    write_png(rgb, path)
    return path


def render_dense_holes(amp, path, px=360):
    """Legend picture: yellow = dense ground, purple = holes. Physical 0–1, not min–max stretch."""
    a = np.asarray(amp, float)
    amax = max(float(a.max()), 1e-30)
    dense = a >= BAG_CRITERION["dense_rel_max"] * amax
    holes = a < BAG_CRITERION["hole_rel_max"] * amax
    r = max(1, px // max(a.shape[0], 1))
    rgb = np.zeros(a.shape + (3,), np.uint8)
    rgb[:] = (40, 40, 48)
    rgb[dense] = (253, 231, 37)
    rgb[holes] = (122, 64, 168)
    rgb = np.kron(rgb, np.ones((r, r, 1), np.uint8))
    purple = (122, 64, 168)
    yellow = (253, 231, 37)
    rgb = _bar(rgb, purple, yellow, "hole", "dense")
    write_png(rgb, path)
    return path


def render_signed(phi, path, px=360):
    a = np.asarray(phi, float)
    m = float(np.abs(a).max()) + 1e-12
    n = (a / m + 1.0) / 2.0
    rgb = colormap(_upscale(n, px), diverging=True)
    blue = (33, 102, 172)
    red = (178, 24, 43)
    rgb = _bar(rgb, blue, red, "ground-b", "ground-a")
    write_png(rgb, path)
    return path


def _copy_artifact(src: Path):
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    dest = ARTIFACT / src.name
    try:
        dest.write_bytes(src.read_bytes())
    except OSError:
        pass
    return dest


def decode_volume_lens(field_json_path, lens):
    d = json.loads(Path(field_json_path).read_text())
    grid = d["grid"]
    nf = d["nframes"]
    L = d["lenses"][lens]
    raw = np.frombuffer(
        __import__("base64").b64decode(L["data_b64"]), np.uint8
    )
    arr = raw.reshape(nf, *grid).astype(float)
    phys = L["vmin"] + (L["vmax"] - L["vmin"]) * arr / 255.0
    return phys, d


def slim_class(cls: dict) -> dict:
    out = {k: v for k, v in cls.items() if k not in ("hist_amp", "hist_phi", "three_d_authenticity")}
    for key in ("largest_dense", "largest_pos", "largest_neg"):
        if isinstance(out.get(key), dict):
            row = dict(out[key])
            row.pop("centroid", None)
            out[key] = row
    if "hist_amp" in cls:
        out["hist_n_peaks"] = cls["hist_amp"]["n_peaks"]
    if "hist_phi" in cls:
        out["hist_n_peaks"] = cls["hist_phi"]["n_peaks"]
    if "three_d_authenticity" in cls:
        out["genuinely_3d"] = cls["three_d_authenticity"].get("genuinely_3d")
    return out


def pick_growth_frame(frames):
    for fr in frames:
        if fr["class"]["mean_amp"] >= BAG_CRITERION["mean_amp_grown"]:
            return fr
    return frames[-1]


def run_tdgl_variants():
    shape = (48, 48)
    default_steps, default_snap = 220, 22
    specs = [
        {"name": "default", "seed": 0, "p": {}, "corr": 0.0},
        {"name": "default", "seed": 1, "p": {}, "corr": 0.0},
        {"name": "fast_quench", "seed": 0, "p": {"quench_duration": 1.0}, "corr": 0.0},
        {"name": "slow_quench", "seed": 0, "p": {"quench_duration": 24.0}, "corr": 0.0},
        {"name": "slow_quench_wait", "seed": 0, "p": {"quench_duration": 24.0}, "corr": 0.0,
         "steps": 500, "snap_every": 50},
        {"name": "coarse_noise", "seed": 0, "p": {}, "corr": 4.0},
        {"name": "very_coarse_noise", "seed": 0, "p": {}, "corr": 8.0},
    ]
    out = []
    for spec in specs:
        st = int(spec.get("steps", default_steps))
        sn = int(spec.get("snap_every", default_snap))
        run = evolve(shape, spec["seed"], st, sn, p=spec["p"] or None, corr=spec["corr"])
        run["name"] = spec["name"]
        out.append(run)
    return out


def save_tdgl_pictures(runs):
    PNG.mkdir(parents=True, exist_ok=True)
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    saved = []
    wanted = {("default", 0), ("fast_quench", 0), ("slow_quench", 0),
              ("slow_quench_wait", 0), ("coarse_noise", 0), ("very_coarse_noise", 0)}
    for run in runs:
        key = (run["name"], run["seed"])
        if key not in wanted:
            continue
        frames = run["frames"]
        snaps = run["snaps"]
        tag = f"tdgl_{run['name']}_s{run['seed']}"
        t0 = snaps[0]
        grow = pick_growth_frame(frames)
        end_field = snaps[max(snaps)]
        grow_field = snaps.get(int(grow["step"]), list(snaps.values())[len(snaps) // 2])

        for kind, field in (("t000", t0), ("growth", grow_field), ("end", end_field)):
            amp = np.abs(field)
            p1 = PNG / f"{tag}_{kind}_amp.png"
            p2 = PNG / f"{tag}_{kind}_dense_holes.png"
            render_amp_physical(amp, p1)
            render_dense_holes(amp, p2)
            for src in (p1, p2):
                _copy_artifact(src)
                saved.append(str(src.relative_to(_REPO)))
        # t=0 is ~0.01 on a 0–1 scale, so the physical PNG is almost flat purple.
        # One stretched picture for human eyes; not a measurement.
        amp0 = np.abs(t0)
        p_eye = PNG / f"{tag}_t000_amp_stretched_not_physics.png"
        from tools.snapshot import render_field
        render_field(amp0, p_eye, px=360)
        _copy_artifact(p_eye)
        saved.append(str(p_eye.relative_to(_REPO)))
    return saved


def score_official_rooms():
    g001_path = _REPO / "rooms/official/room-g001-a/runs/seed-0000/field.json"
    g003_path = _REPO / "rooms/official/room-g003-a/runs/seed-0000/field.json"
    g001_sum = {
        0: json.loads((_REPO / "rooms/official/room-g001-a/runs/seed-0000/summary.json").read_text()),
        1: json.loads((_REPO / "rooms/official/room-g001-a/runs/seed-0001/summary.json").read_text()),
        2: json.loads((_REPO / "rooms/official/room-g001-a/runs/seed-0002/summary.json").read_text()),
    }
    g001_em = json.loads((_REPO / "rooms/official/room-g001-a/emergence.json").read_text())

    dens, meta = decode_volume_lens(g001_path, "density")
    # density = |ψ|^2 (display lens 20³, interpolated, not the 64³ physics)
    amp = np.sqrt(np.clip(dens, 0.0, None))
    g001_frames = []
    nF = len(amp)
    pic_idx = {0: "t000", max(1, nF // 3): "mid", nF - 1: "end"}
    for i, t in enumerate(meta["times"]):
        vol = amp[i]
        cls = classify_amp(vol, windings=None)
        g001_frames.append({"t": float(t), "class": slim_class(cls), "sha256": sha256_field(vol)})
        if i in pic_idx:
            sl = vol[:, :, vol.shape[2] // 2]
            xz = vol[:, vol.shape[1] // 2, :]
            kind = pic_idx[i]
            tag = "g001_lens_s0"
            p1 = PNG / f"{tag}_{kind}_xy_amp.png"
            p2 = PNG / f"{tag}_{kind}_xy_dense_holes.png"
            p3 = PNG / f"{tag}_{kind}_xz_amp.png"
            PNG.mkdir(parents=True, exist_ok=True)
            ARTIFACT.mkdir(parents=True, exist_ok=True)
            render_amp_physical(sl, p1)
            render_dense_holes(sl, p2)
            render_amp_physical(xz, p3)
            for src in (p1, p2, p3):
                _copy_artifact(src)
            if kind == "t000":
                from tools.snapshot import render_field
                p_eye = PNG / f"{tag}_t000_xy_amp_stretched_not_physics.png"
                render_field(sl, p_eye, px=360)
                _copy_artifact(p_eye)

    g001_persist = persist_verdict([
        {"class": {"bag_candidate": fr["class"]["bag_candidate"]}} for fr in g001_frames
    ])

    phi = decode_lens(str(g003_path), "composition")
    g3 = json.loads(g003_path.read_text())
    g003_frames = []
    for i, t in enumerate(g3["times"]):
        cls = classify_signed_two_ground(phi[i])
        g003_frames.append({"t": float(t), "class": slim_class(cls), "sha256": sha256_field(phi[i])})
        if i in (0, len(phi) // 2, len(phi) - 1):
            kind = "t000" if i == 0 else ("mid" if i == len(phi) // 2 else "end")
            p = PNG / f"g003_lens_s0_{kind}_phi.png"
            PNG.mkdir(parents=True, exist_ok=True)
            ARTIFACT.mkdir(parents=True, exist_ok=True)
            render_signed(phi[i], p)
            _copy_artifact(p)

    g003_em = json.loads((_REPO / "rooms/official/room-g003-a/emergence.json").read_text())
    return {
        "g001_lens_honesty": meta["honesty"],
        "g001_lens_grid": meta["grid"],
        "g001_note": (
            "Display lens 20³ downsampled from 64³. Not a rerun. "
            "Official localization=true is Level-2 winding defects (holes), not a bag."
        ),
        "g001_official_summaries": {
            str(k): {
                "reached_level": v["reached_level"],
                "final_mean_amplitude": v["final_mean_amplitude"],
            }
            for k, v in g001_sum.items()
        },
        "g001_official_defects": g001_em["measured_by"]["defect_count"],
        "g001_official_detected": g001_em["detected"],
        "g001_lens_hole_undercount": (
            "End lens n_hole_components is 0–1; official defect_count is 241. "
            "The 20³ display lens is not a hole census. Use stored summaries for defects."
        ),
        "g001_lens_frames": g001_frames,
        "g001_lens_persist": g001_persist,
        "g003_lens_honesty": g3["honesty"],
        "g003_lens_grid": g3["grid"],
        "g003_note": (
            "Existing two-ground white (Model H / Cahn-Hilliard). "
            "Mapped, not promoted to bag mainline. 50-50 start. Display 48² from 128²."
        ),
        "g003_official_interface_fraction": g003_em["measured_by"]["interface_fraction_final"],
        "g003_official_domain_scale": g003_em["measured_by"]["domain_scale_final"],
        "g003_lens_frames": g003_frames,
        "g003_any_one_body_bag": bool(any(
            fr["class"].get("phase_a_bag_candidate") or fr["class"].get("phase_b_bag_candidate")
            for fr in g003_frames
        )),
        "g003_persist": persist_verdict([
            {"class": {"bag_candidate": bool(
                fr["class"].get("phase_a_bag_candidate") or fr["class"].get("phase_b_bag_candidate")
            )}} for fr in g003_frames
        ]),
        "g003_ruler_leak": (
            "Frozen ruler can mark one maze island as bag_candidate when other "
            "same-phase patches are each < min_body_frac. Those frames still have "
            "many components. Not one remaining inside. Not retuned this round."
        ),
    }


def map_existing_two_ground() -> dict:
    return {
        "present_without_placing_a_bag": [
            {
                "id": "room-g003-a",
                "white": "g003 Model H (Cahn-Hilliard + flow)",
                "ic": "uniform mean 0 + noise 0.05 (no droplet placed)",
                "what_grows": "two composition grounds and an interface",
                "bag_mainline": False,
                "why_not_promoted": "50-50 bicontinuous maze is two grounds sitting, not one remaining inside",
            },
            {
                "id": "e033",
                "white": "Cahn-Hilliard / Flory-Huggins",
                "ic": "uniform 0.5 + noise",
                "what_grows": "spinodal two-phase coexistence above chi_c=2",
                "bag_mainline": False,
                "why_not_promoted": "two grounds / wavelength; not scored as one body",
            },
        ],
        "exists_but_shape_was_placed": [
            {
                "id": "e020",
                "note": "round/ellipse/dumbbell/filament were PUT. Drift for the bag question. Do not use.",
            }
        ],
        "do_not_promote": [
            {
                "id": "gray_scott",
                "note": "stain splitting without inheritance. Not a bag. Not this mainline.",
            },
            {
                "id": "swift_hohenberg",
                "note": "localized bump is seeded. Not grown from undifferentiated white.",
            },
        ],
        "docs_only_not_run": [
            {
                "id": "F0_P01_active_droplet",
                "note": "preregistration only. Not implemented this round. Do not add the field.",
            }
        ],
    }


def mixing_audit() -> dict:
    return {
        "official_level2_localization": {
            "mixed_with_holes": True,
            "where": "genesis/diagnostics/measures.py::assess_level",
            "rule": "localization = defects>0 and persistent_defects",
            "room_g001_a": "detected.localization=true because defect_count=241 (holes)",
            "fix_this_round": (
                "Do not retune official L2. Point it out. Bag ruler stays separate "
                "and does not use hole count as a pass."
            ),
            "changed_measures_py": False,
        },
        "pr135_bag_criterion": {
            "mixed_with_holes": False,
            "mixed_with_triangle": False,
            "hole_fields_are_informational": True,
            "bag_candidate_ignores_n_holes": True,
            "this_report_reuses_frozen_gates": True,
        },
        "triangle_and_ring": {
            "pr133": "hole geometry. not a bag.",
            "pr134": "ring pinch. hole loop. not a bag.",
            "used_as_success_here": False,
        },
    }


def potential_note() -> dict:
    """Why yellow fills: unique bulk well of this equation. Not placed."""
    r = np.linspace(0, 1.4, 141)
    # post-quench eps=+1: V = -r^2/2 + r^4/4 ; V'(r)= -r + r^3 = r(r^2-1)
    V = -0.5 * r**2 + 0.25 * r**4
    return {
        "equation": "dψ/dt = eps ψ - |ψ|^2 ψ + Du lap ψ",
        "after_quench_eps": 1.0,
        "bulk_potential": "V(r)=-r^2/2 + r^4/4",
        "stable_bulk_amplitude": 1.0,
        "unstable_at_zero": True,
        "second_stable_amplitude": None,
        "holes_remain_only_if_topological": True,
        "V_at_0": float(V[0]),
        "V_at_1": float(-0.5 * 1 + 0.25 * 1),
    }


def main():
    PNG.mkdir(parents=True, exist_ok=True)
    ARTIFACT.mkdir(parents=True, exist_ok=True)

    mixing = mixing_audit()
    two_ground_map = map_existing_two_ground()
    rooms = score_official_rooms()
    runs = run_tdgl_variants()
    pictures = save_tdgl_pictures(runs)

    slim_runs = []
    any_bag = False
    yellow_fill = []
    for run in runs:
        persist = run["persist"]
        if persist["persistent_one_body"]:
            any_bag = True
        end = run["frames"][-1]["class"]
        grow = pick_growth_frame(run["frames"])
        yellow_fill.append({
            "name": run["name"],
            "seed": run["seed"],
            "corr": run["corr"],
            "quench_duration": run["params"]["quench_duration"],
            "t0_mean": run["frames"][0]["class"]["mean_amp"],
            "growth_t": grow["t"],
            "growth_mean": grow["class"]["mean_amp"],
            "growth_dense_frac": grow["class"]["dense_frac"],
            "end_mean": end["mean_amp"],
            "end_dense_frac": end["dense_frac"],
            "end_outside_abs_frac": end["outside_abs_frac"],
            "end_n_holes": end["n_hole_components"],
            "end_windings": end["winding_defect_count"],
            "end_hist_peaks": end["hist_amp"]["n_peaks"],
            "end_room_bulk": end["dense_is_room_bulk"],
            "bag_candidate_any": bool(any(fr["class"]["bag_candidate"] for fr in run["frames"])),
            "persistent_one_body": persist["persistent_one_body"],
            "longest_bag_run": persist["longest_consecutive_bag_frames"],
            "end_sha256": run["end_sha256"],
        })
        slim_runs.append({
            "name": run["name"],
            "seed": run["seed"],
            "corr": run["corr"],
            "params": run["params"],
            "persist": persist,
            "frames": [
                {"t": fr["t"], "sha256": fr["sha256"], "class": slim_class(fr["class"])}
                for fr in run["frames"]
            ],
            "end_sha256": run["end_sha256"],
        })

    report = {
        "module": "verify-20260829-bag-dig",
        "not_an_official_room": True,
        "question": "Why does white+TDGL fill the room with dense ground, and does a bag appear if we only change coarseness/cooling?",
        "put_in": "existing g001 TDGL; white near-zero (+ optional smoothed noise, same rms); no bag/circle/membrane",
        "not_success": list(NOT_SUCCESS),
        "bag_criterion_frozen": BAG_CRITERION,
        "goal_progress_json_untouched": True,
        "mixing_audit": mixing,
        "why_yellow_fills": potential_note(),
        "tdgl_variants": slim_runs,
        "tdgl_yellow_fill_table": yellow_fill,
        "any_persistent_one_body": any_bag,
        "outside_remains_in_this_white": bool(
            any(row["end_outside_abs_frac"] > 0.20 and not row["end_room_bulk"] for row in yellow_fill)
        ),
        "official_rooms": rooms,
        "two_ground_map": two_ground_map,
        "pictures": pictures,
        "next_honest_move_one": (
            "Score the existing two-ground white (G003 / Cahn-Hilliard) for maze vs "
            "one remaining inside by changing only mean composition of a uniform+noise start. "
            "Do not place a droplet. Do not add a membrane field to TDGL. Do not return to triangles."
        ),
    }
    (HERE / "measurements.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "any_persistent_one_body": any_bag,
        "n_runs": len(runs),
        "yellow_fill": yellow_fill,
        "g001_lens_persist": rooms["g001_lens_persist"],
        "g003_any_one_body_bag": rooms["g003_any_one_body_bag"],
        "pictures": len(pictures),
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
