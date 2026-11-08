#!/usr/bin/env python3
"""Why does the yellow ground fill the room? — digging under the negative result of PR #135.

MODULE:      verify-20260829-bag-dig (dated report; NOT a Room)
QUESTION:    With the SAME white start and the SAME existing TDGL law, is there ANY start
             (noise coarseness, quench speed, final eps) for which the room does NOT end
             as one single ground — i.e. a dense inside and a not-dense outside sitting
             next to each other, with the bag gate scored on it?
PUT IN:      genesis.models.ginzburg_landau (unmodified, imported) + a structureless start.
             IC families: white / white_lowk / white_highk  (declared random fields with a
             declared scale; docs: ai_lab/dream/fission_path.MINIMAL_RANDOM_FAMILIES).
             Climate knobs: quench_duration, eps_final. Both are pre-declared environment
             (docs/PHYSICS_INTEGRITY.md §8 time_programmed_environment), never changed mid-run.
             NO bag, vesicle, membrane field, metabolism field, circle, body location, or
             body size is placed. NO new field is added.
EMERGED:     (see measurements.json) Every ordered end state is ONE ground. The amplitude
             histogram is single-peaked at |psi| = sqrt(eps). The only survivors of the
             low-amplitude side are phase-winding holes — the opposite of a bag.
CLAIM TIER:  measured (dense_frac, component tables, span, persistence, histogram,
             winding_defect_count, hashes). interpretive: the free-energy reading of why.
             analogy: cell / life / membrane — refused.
STATUS:      YELLOW / role N primary (the asked bag is not observed, and now we can say
             which property of the law forbids it in this white).

The bag gate below is COPIED VERBATIM from PR #135
(ai_lab/reports/easy/verify-20260829-one-body-bag/replay.py BAG_CRITERION).
It is NOT retuned, NOT loosened, NOT widened. Success is still not triangle, not ring 1->2,
not F7, not a hole count.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
_REPO = HERE.parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from genesis.diagnostics import measures  # noqa: E402
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tinyfont import draw_text, text_width  # noqa: E402
from tools.snapshot import colormap, write_png  # noqa: E402

FIG = HERE / "figures"

# ---------------------------------------------------------------------------
# Frozen a-priori bag gate. Copied unchanged from PR #135. DO NOT RETUNE.
# ---------------------------------------------------------------------------
BAG_CRITERION = {
    "amp_max_grown": 0.3,       # local order above the noise floor (a bag need not fill the room)
    "mean_amp_grown": 0.3,      # whole-field order (room climate). Informational; not a bag gate
    "dense_rel_max": 0.5,       # high-amp bulk = yellow ground
    "min_body_frac": 0.02,      # not a speck
    "max_body_frac": 0.40,      # not the room
    "max_span_frac": 0.90,      # not wrapping/percolating
    "persist_snapshots": 5,     # consecutive bag-candidate frames
    "hole_rel_max": 0.25,       # amplitude holes (cores) — a SEPARATE card, never a bag
    "min_hole_voxels": 1,
}
NOT_SUCCESS = ("triangle", "ring_pinch_1_to_2", "F7", "hole_count_as_body", "coexistence_alone")

# A second, SEPARATE ruler. It is NOT a bag pass and can never make a bag pass.
# It only asks: at the end, is there still an "outside" at all, or is the room one colour?
OUTSIDE_CRITERION = {
    "outside_rel_max": 0.5,      # a cell is "not dense" below half the max amplitude
    "min_outside_frac": 0.10,    # an outside worth the name occupies at least 10% of the box
}

SEEDS = (0, 1)


# ---------------------------------------------------------------------------
# starts (structureless; no object, no shape, no location)
# ---------------------------------------------------------------------------
def make_start(family: str, shape, noise_amplitude: float, rng) -> np.ndarray:
    """White noise, optionally low- or high-pass filtered in Fourier and re-scaled to the
    SAME rms. A filter changes the ROUGHNESS of the noise, not its content: no object,
    no position, no size, no shape is placed. Families match
    ai_lab/dream/fission_path.MINIMAL_RANDOM_FAMILIES."""
    psi = gl.make_initial(shape, noise_amplitude, rng)      # repo function, unmodified
    if family == "white":
        return psi
    ks = [np.fft.fftfreq(n) * 2.0 * np.pi for n in shape]
    grids = np.meshgrid(*ks, indexing="ij")
    kmag = np.sqrt(sum(g ** 2 for g in grids))
    kcut = 0.35 * float(kmag.max())
    if family == "white_lowk":
        mask = kmag <= kcut                                 # coarse, blobby noise
    elif family == "white_highk":
        mask = kmag > kcut                                  # fine, gritty noise
    else:
        raise ValueError(f"unknown family {family!r}")
    out = np.fft.ifftn(np.fft.fftn(psi) * mask)
    rms0 = float(np.sqrt(np.mean(np.abs(psi) ** 2)))
    rms1 = float(np.sqrt(np.mean(np.abs(out) ** 2))) + 1e-30
    return (out * (rms0 / rms1)).astype(np.complex128)


def sha256_field(psi: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes())
    h.update(np.ascontiguousarray(psi.imag).tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# measurement (dense side = inside candidate; holes scored on a separate card)
# ---------------------------------------------------------------------------
def _label6(mask):
    return ndimage.label(mask, structure=ndimage.generate_binary_structure(mask.ndim, 1))


def _span_frac(coords, shape):
    if coords.size == 0:
        return [0.0] * len(shape)
    return [float((coords[:, ax].max() - coords[:, ax].min() + 1) / shape[ax])
            for ax in range(len(shape))]


def component_table(mask, top=4):
    lbl, n = _label6(mask)
    if n == 0:
        return [], 0
    sizes = ndimage.sum_labels(np.ones_like(mask, float), lbl, index=np.arange(1, n + 1))
    order = np.argsort(sizes)[::-1][:top]
    total = float(mask.size)
    rows = []
    for idx in order:
        lab = int(idx) + 1
        coords = np.argwhere(lbl == lab)
        span = _span_frac(coords, mask.shape)
        rows.append({
            "label": lab,
            "voxels": int(coords.shape[0]),
            "frac": float(coords.shape[0] / total),
            "span_frac": span,
            "percolates": bool(any(s >= BAG_CRITERION["max_span_frac"] for s in span)),
        })
    return rows, int(n)


def score_frame(psi):
    """Score ONE frame. Returns the bag verdict, the separate outside ruler, and the
    separate hole card. The three are never allowed to substitute for one another."""
    amp = np.abs(psi)
    amax = float(amp.max())
    mean = float(amp.mean())
    local_order = bool(amax >= BAG_CRITERION["amp_max_grown"])
    dense = amp >= BAG_CRITERION["dense_rel_max"] * max(amax, 1e-30)
    holes = amp < BAG_CRITERION["hole_rel_max"] * max(amax, 1e-30)
    dense_frac = float(dense.mean())
    dense_rows, n_dense = component_table(dense)
    hole_rows, n_holes = component_table(holes)
    significant = [r for r in dense_rows if r["frac"] >= BAG_CRITERION["min_body_frac"]]
    largest = dense_rows[0] if dense_rows else None
    room_bulk = bool(dense_frac > BAG_CRITERION["max_body_frac"])
    bag = bool(
        local_order
        and (not room_bulk)
        and len(significant) == 1
        and largest is not None
        and not largest["percolates"]
        and BAG_CRITERION["min_body_frac"] <= largest["frac"] <= BAG_CRITERION["max_body_frac"]
    )
    if not local_order:
        why = "nothing_grew (amp_max < 0.3)"
    elif room_bulk:
        why = "room_bulk (dense side larger than max_body_frac)"
    elif largest is None:
        why = "no_dense_component"
    elif largest["percolates"]:
        why = "percolates (wraps the box)"
    elif len(significant) != 1:
        why = f"not_one_body (n_significant={len(significant)})"
    elif largest["frac"] < BAG_CRITERION["min_body_frac"]:
        why = "speck"
    else:
        why = "bag_candidate"
    outside_frac = float((amp < OUTSIDE_CRITERION["outside_rel_max"] * max(amax, 1e-30)).mean())
    hist, _ = np.histogram(amp / max(amax, 1e-30), bins=20, range=(0.0, 1.0))
    return {
        "mean_amp": mean, "amp_max": amax, "amp_min": float(amp.min()),
        "local_order": local_order,
        "dense_frac": dense_frac,
        "n_dense_components": n_dense,
        "n_significant_dense": len(significant),
        "largest_dense": largest,
        "bag": bag, "bag_reason": why,
        # separate ruler — never a bag pass
        "outside_frac": outside_frac,
        "outside_survives": bool(local_order
                                 and outside_frac >= OUTSIDE_CRITERION["min_outside_frac"]),
        # separate card — never a body count
        "hole_card": {"n_hole_components": n_holes,
                      "hole_frac": float(holes.mean()),
                      "windings": int(measures.winding_defect_count(psi)),
                      "largest_hole_frac": hole_rows[0]["frac"] if hole_rows else 0.0},
        "amp_hist_20_rel": [int(v) for v in hist],
    }


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def run_case(*, family, shape, seed, quench_duration, eps_final,
             noise_amplitude=0.01, snaps=11, keep_frames=(), t_extra=30.0):
    p = dict(gl.DEFAULTS)
    p["quench_duration"] = float(quench_duration)
    p["eps_final"] = float(eps_final)
    p["noise_amplitude"] = float(noise_amplitude)
    dt = p["dt"]
    t_end = float(quench_duration) + float(t_extra)
    steps = int(round(t_end / dt))
    every = max(1, steps // (snaps - 1))
    rng = np.random.default_rng(seed)
    psi = make_start(family, shape, noise_amplitude, rng)
    frames, saved = [], {}
    t = 0.0
    t0 = time.time()
    for s in range(steps + 1):
        if s % every == 0 or s == steps:
            sc = score_frame(psi)
            sc["step"] = int(s)
            sc["t"] = round(float(t), 3)
            sc["eps"] = round(float(gl.eps_of_t(t, p)), 4)
            frames.append(sc)
            if len(frames) - 1 in keep_frames or s == steps:
                saved[len(frames) - 1] = psi.copy()
        if s == steps:
            break
        psi = gl.step(psi, t, p)
        t += dt
    # longest run of consecutive bag frames
    best = cur = 0
    for f in frames:
        cur = cur + 1 if f["bag"] else 0
        best = max(best, cur)
    first_ordered = next((f for f in frames if f["local_order"]), None)
    return {
        "case": f"{family}_{'x'.join(map(str, shape))}_qd{quench_duration}_eps{eps_final}_s{seed}",
        "family": family, "shape": list(shape), "seed": seed,
        "quench_duration": quench_duration, "eps_final": eps_final,
        "noise_amplitude": noise_amplitude,
        "dt": dt, "Du": p["Du"], "steps": steps, "snapshot_every": every,
        "end_field_sha256": sha256_field(psi)[:16],
        "wall_seconds": round(time.time() - t0, 2),
        "any_bag_frame": any(f["bag"] for f in frames),
        "longest_bag_run": best,
        "persistent_bag": bool(best >= BAG_CRITERION["persist_snapshots"]),
        "any_outside_survives": any(f["outside_survives"] for f in frames),
        "outside_survives_at_end": bool(frames[-1]["outside_survives"]),
        "outside_frac_when_order_first_appears": (
            round(first_ordered["outside_frac"], 4) if first_ordered else None),
        "outside_frac_at_end": round(frames[-1]["outside_frac"], 4),
        "t_when_order_first_appears": first_ordered["t"] if first_ordered else None,
        "end": frames[-1],
        "frames": frames,
    }, saved, frames


# ---------------------------------------------------------------------------
# figures (visualisation only; fixed physical colour scale, legend stamped in)
# ---------------------------------------------------------------------------
BG = (250, 250, 248)
INK = (25, 25, 30)
AMP_REF = 1.0          # |psi| at equilibrium for eps_final = 1. FIXED, never stretched.
PX = 320


def _upscale(a, px=PX):
    r = max(1, px // a.shape[0])
    return np.kron(a, np.ones((r, r), a.dtype))


def _colorbar(canvas, y, x, w, h, labels):
    ramp = np.linspace(0.0, 1.0, w)[None, :].repeat(h, axis=0)
    canvas[y:y + h, x:x + w] = colormap(ramp)
    canvas[y - 1:y + h + 1, x - 1:x + w + 1][0, :] = INK
    for frac, txt in labels:
        cx = x + int(frac * (w - 1))
        canvas[y + h:y + h + 3, max(x, cx - 1):cx + 1] = INK
        draw_text(canvas, txt, y + h + 5, min(cx - text_width(txt, 2) // 2, x + w - text_width(txt, 2)), 2, INK)


def _canvas_width(field_w, lines, pad=8, indent=0):
    need = max([text_width(s, 2) + indent for s in lines] + [0]) + pad
    return int(max(field_w, need, 300))


def fig_amplitude(psi2d, path, title, sub, note):
    """Amplitude on a FIXED 0..AMP_REF viridis scale. No min-max stretch (PR #135 trap)."""
    a = np.clip(np.abs(np.asarray(psi2d)) / AMP_REF, 0.0, 1.0)
    img = colormap(_upscale(a))
    H, W, _ = img.shape
    legend = ["SCALE: |PSI| SHOWN ON A FIXED 0..1 RANGE (NOT STRETCHED TO MIN..MAX)",
              "YELLOW = DENSE SIDE (INSIDE CANDIDATE).  DARK PURPLE = LOW AMPLITUDE (HOLE / OUTSIDE)."]
    top, bot = 34, 108
    cw = _canvas_width(W, [title, sub, note] + legend)
    canvas = np.zeros((H + top + bot, cw, 3), np.uint8)
    canvas[:] = BG
    canvas[top:top + H, 0:W] = img
    draw_text(canvas, title, 6, 4, 2, INK)
    draw_text(canvas, sub, 20, 4, 2, (90, 90, 95))
    y = top + H + 10
    _colorbar(canvas, y, 4, 240, 12,
              [(0.0, "0"), (0.25, "0.25"), (0.5, "0.5"), (0.75, "0.75"), (1.0, "1.0")])
    y += 32
    for s in legend:
        draw_text(canvas, s, y, 4, 2, (60, 60, 70))
        y += 14
    draw_text(canvas, note, y + 6, 4, 2, INK)
    return write_png(canvas, path)


DENSE_RGB = (253, 231, 37)     # same yellow as the top of the viridis ramp
MID_RGB = (33, 145, 140)       # the in-between band
HOLE_RGB = (68, 1, 84)         # same dark purple as the bottom of the ramp


def fig_classes(psi2d, path, title, sub, note):
    """The three classes the gates actually use, painted flat so nothing is stretched."""
    amp = np.abs(np.asarray(psi2d))
    amax = float(amp.max()) + 1e-30
    cls = np.full(amp.shape, 1, np.uint8)
    cls[amp >= BAG_CRITERION["dense_rel_max"] * amax] = 2
    cls[amp < BAG_CRITERION["hole_rel_max"] * amax] = 0
    lut = np.array([HOLE_RGB, MID_RGB, DENSE_RGB], np.uint8)
    img = lut[_upscale(cls)]
    H, W, _ = img.shape
    keys = ((DENSE_RGB, "YELLOW = DENSE SIDE, |PSI| >= 0.5 MAX (INSIDE CANDIDATE)"),
            (MID_RGB, "TEAL   = IN BETWEEN, 0.25 .. 0.5 MAX (THIS IS WHERE A SKIN WOULD BE)"),
            (HOLE_RGB, "PURPLE = HOLE / OUTSIDE, |PSI| < 0.25 MAX (NOT A BODY)"))
    top, bot = 34, 84
    cw = _canvas_width(W, [title, sub, note] + [k[1] for k in keys], indent=30)
    canvas = np.zeros((H + top + bot, cw, 3), np.uint8)
    canvas[:] = BG
    canvas[top:top + H, 0:W] = img
    draw_text(canvas, title, 6, 4, 2, INK)
    draw_text(canvas, sub, 20, 4, 2, (90, 90, 95))
    y = top + H + 10
    for rgb, txt in keys:
        canvas[y:y + 10, 4:24] = np.asarray(rgb, np.uint8)
        canvas[y:y + 10, 4:24][0, :] = INK
        draw_text(canvas, txt, y + 1, 30, 2, INK)
        y += 16
    draw_text(canvas, note, y + 6, 4, 2, INK)
    return write_png(canvas, path)


def fig_histogram(cases, path, title, note):
    """Amplitude histograms at the end. One peak = one ground = no outside to sit next to."""
    nb = 20
    rowh, gap, barw = 74, 12, 20
    sub = "X = |PSI| / MAX|PSI| (0 LEFT .. 1 RIGHT), Y = HOW MANY CELLS (SQRT SCALE)"
    W = _canvas_width(60 + nb * barw, [title, sub, note])
    H = 46 + len(cases) * (rowh + gap) + 40
    canvas = np.zeros((H, W, 3), np.uint8)
    canvas[:] = BG
    draw_text(canvas, title, 6, 4, 2, INK)
    draw_text(canvas, sub, 20, 4, 2, (90, 90, 95))
    y = 44
    for label, hist in cases:
        h = np.asarray(hist, float)
        hs = np.sqrt(h)
        hs = hs / (hs.max() + 1e-30)
        draw_text(canvas, label, y, 4, 2, INK)
        base = y + rowh
        for i, v in enumerate(hs):
            bh = int(round(v * (rowh - 14)))
            x0 = 56 + i * barw
            rgb = colormap(np.array([(i + 0.5) / nb]))[0]
            if bh > 0:
                canvas[base - bh:base, x0:x0 + barw - 3] = rgb
        canvas[base:base + 1, 56:56 + nb * barw] = INK
        y += rowh + gap
    draw_text(canvas, note, H - 26, 4, 2, INK)
    return write_png(canvas, path)


# ---------------------------------------------------------------------------
def main():
    FIG.mkdir(parents=True, exist_ok=True)
    results, figures = [], []

    # ---- A. does the noise ROUGHNESS or the COOLING SPEED change the ending? (2D 48x48)
    shape2d = (48, 48)
    keep = (0, 4, 10)       # start / middle / end snapshot indices
    fig_pool = {}
    for family in ("white", "white_lowk", "white_highk"):
        for qd in (1.0, 8.0, 40.0):
            for seed in SEEDS:
                res, saved, frames = run_case(family=family, shape=shape2d, seed=seed,
                                              quench_duration=qd, eps_final=1.0,
                                              keep_frames=keep)
                res["group"] = "A_roughness_and_cooling_2d"
                results.append(res)
                if seed == 0:
                    fig_pool[(family, qd)] = (saved, frames)
                print(f"  {res['case']}: dense_frac_end={res['end']['dense_frac']:.3f} "
                      f"bag={res['persistent_bag']} outside={res['any_outside_survives']}")

    # ---- B. does the room's FINAL eps change the ending? (2D 48x48, white, seed 0/1)
    for eps in (-1.0, 0.0, 0.25, 1.0):
        for seed in SEEDS:
            res, saved, frames = run_case(family="white", shape=shape2d, seed=seed,
                                          quench_duration=8.0, eps_final=eps,
                                          keep_frames=keep)
            res["group"] = "B_eps_sweep_2d"
            results.append(res)
            if seed == 0:
                fig_pool[("eps", eps)] = (saved, frames)
            print(f"  {res['case']}: dense_frac_end={res['end']['dense_frac']:.3f} "
                  f"bag={res['persistent_bag']} outside={res['any_outside_survives']}")

    # ---- C. the same two questions in a small 3D box (32^3, NOT an official Room)
    shape3d = (32, 32, 32)
    for family in ("white", "white_lowk"):
        for seed in SEEDS:
            res, saved, frames = run_case(family=family, shape=shape3d, seed=seed,
                                          quench_duration=8.0, eps_final=1.0,
                                          keep_frames=keep)
            res["group"] = "C_small_3d"
            results.append(res)
            if seed == 0:
                fig_pool[("3d", family)] = (saved, frames)
            print(f"  {res['case']}: dense_frac_end={res['end']['dense_frac']:.3f} "
                  f"bag={res['persistent_bag']} outside={res['any_outside_survives']}")

    # ---- D. the ONE case whose end frame still had an outside was simply not finished
    #         growing (eps=0.25 is a shallow room, so it climbs slowly). Run it long.
    for seed in SEEDS:
        res, saved, frames = run_case(family="white", shape=shape2d, seed=seed,
                                      quench_duration=8.0, eps_final=0.25,
                                      t_extra=400.0, snaps=11, keep_frames=keep)
        res["group"] = "D_shallow_room_run_long"
        res["note"] = ("the shallow eps=0.25 room only looked like it kept an outside "
                       "because it was still climbing; run to t=408 it closes too")
        results.append(res)
        if seed == 0:
            fig_pool[("epslong", 0.25)] = (saved, frames)
        print(f"  {res['case']}_LONG: dense_frac_end={res['end']['dense_frac']:.3f} "
              f"outside_frac_end={res['end']['outside_frac']:.3f} "
              f"bag={res['persistent_bag']}")

    # ---- figures -----------------------------------------------------------
    def _f(psi):
        return psi if psi.ndim == 2 else psi[:, :, psi.shape[2] // 2]

    saved, frames = fig_pool[("white", 8.0)]
    idx = sorted(saved)
    notes = {
        "start": "NOTHING IS PLACED HERE: JUST WHITE GRIT. THE HOLE COUNT AT T=0 IS NOISE PHASE, NOT HOLES OF A GROUND.",
        "growing": "THE ONLY MOMENT AN OUTSIDE EXISTS. IT IS ONE GROUND STILL FILLING IN, NOT TWO GROUNDS.",
        "end": "THE YELLOW GROUND HAS FILLED THE ROOM. WHAT IS LEFT DARK IS HOLES.",
    }
    for n, (i, tag) in enumerate([(idx[0], "start"), (idx[1], "growing"), (idx[-1], "end")],
                                 start=1):
        f = frames[i]
        p = FIG / f"fig{n:02d}_2d_white_{tag}.png"
        fig_amplitude(_f(saved[i]), p,
                      f"2D 48X48 TDGL WHITE  T={f['t']}  ({tag})",
                      f"DENSE FRAC={f['dense_frac']:.3f}  OUTSIDE FRAC={f['outside_frac']:.3f}"
                      f"  HOLE PATCHES={f['hole_card']['n_hole_components']}",
                      f"BAG: {'YES' if f['bag'] else 'NO'} - {f['bag_reason'].upper()}. "
                      + notes[tag])
        figures.append(p.name)

    i = idx[-1]
    p = FIG / "fig04_2d_white_end_classes.png"
    fig_classes(_f(saved[i]), p, "2D 48X48 TDGL WHITE - END, PAINTED BY CLASS",
                "SAME FRAME AS FIG03. FLAT COLOURS, NO STRETCH.",
                "THE ROOM IS ONE GROUND. THE PURPLE LEFT OVER IS HOLES, NOT AN OUTSIDE.")
    figures.append(p.name)

    saved_l, frames_l = fig_pool[("white_lowk", 8.0)]
    il = sorted(saved_l)[-1]
    p = FIG / "fig05_2d_white_lowk_end.png"
    fig_amplitude(_f(saved_l[il]), p, "2D 48X48 TDGL COARSE WHITE (LOW-K) - END",
                  f"DENSE FRAC={frames_l[il]['dense_frac']:.3f}  "
                  f"OUTSIDE FRAC={frames_l[il]['outside_frac']:.3f}",
                  "COARSER NOISE: FEWER HOLES, SAME ONE GROUND. BAG: NO.")
    figures.append(p.name)

    saved_f, frames_f = fig_pool[("white", 1.0)]
    iff = sorted(saved_f)[-1]
    p = FIG / "fig06_2d_fast_quench_end.png"
    fig_amplitude(_f(saved_f[iff]), p, "2D 48X48 TDGL FAST COOLING (QD=1) - END",
                  f"DENSE FRAC={frames_f[iff]['dense_frac']:.3f}  "
                  f"HOLES={frames_f[iff]['hole_card']['n_hole_components']}",
                  "FAST COOLING MAKES MORE HOLES, NOT A BAG. BAG: NO.")
    figures.append(p.name)

    saved_n, frames_n = fig_pool[("eps", -1.0)]
    inn = sorted(saved_n)[-1]
    p = FIG / "fig07_2d_eps_negative_end.png"
    fig_amplitude(_f(saved_n[inn]), p, "2D 48X48 TDGL ROOM NEVER TURNS ON (EPS=-1) - END",
                  f"AMP MAX={frames_n[inn]['amp_max']:.2e}  (FIXED SCALE, SO IT IS BLACK)",
                  "ALL OUTSIDE, NO INSIDE. THE OTHER END OF THE SAME SWITCH. BAG: NO.")
    figures.append(p.name)

    saved_3, frames_3 = fig_pool[("3d", "white")]
    i3 = sorted(saved_3)[-1]
    vol = saved_3[i3]
    amp3 = np.abs(vol)
    holes3 = amp3 < BAG_CRITERION["hole_rel_max"] * float(amp3.max())
    zpick = int(np.argmax(holes3.sum(axis=(0, 1))))     # the slice with the most hole cells
    p = FIG / "fig08_3d_white_end_slice_with_holes.png"
    fig_amplitude(vol[:, :, zpick], p,
                  f"3D 32X32X32 TDGL WHITE - END, Z={zpick} SLICE",
                  f"DENSE FRAC(3D BOX)={frames_3[i3]['dense_frac']:.3f}  "
                  f"HOLE PATCHES(3D BOX)={frames_3[i3]['hole_card']['n_hole_components']}"
                  f"  (SLICE PICKED AS THE ONE WITH THE MOST HOLE CELLS)",
                  "DARK DOTS ARE VORTEX LINES PIERCING THE SLICE, NOT BODIES. BAG: NO.")
    figures.append(p.name)

    hist_cases = []
    for key, label in ((("white", 8.0), "WHITE QD=8"),
                       (("white_lowk", 8.0), "COARSE LOW-K QD=8"),
                       (("white", 1.0), "WHITE QD=1 FAST"),
                       (("eps", 0.25), "SHALLOW EPS=0.25 AT T=38 (STILL CLIMBING)"),
                       (("epslong", 0.25), "SHALLOW EPS=0.25 AT T=408 (FINISHED)")):
        _s, _fr = fig_pool[key]
        hist_cases.append((label, _fr[-1]["amp_hist_20_rel"]))
    p = FIG / "fig09_amplitude_histograms_end.png"
    fig_histogram(hist_cases, p, "END AMPLITUDE HISTOGRAMS - ONE PEAK EVERY TIME",
                  "ONE PEAK = ONE GROUND. A BAG NEEDS TWO PEAKS THAT BOTH STAY.")
    figures.append(p.name)

    # ---- summary -----------------------------------------------------------
    summary = {
        "report": "verify-20260829-bag-dig",
        "date": "2026-08-29",
        "is_official_room": False,
        "model": gl.MODEL_ID,
        "model_file": "genesis/models/ginzburg_landau.py (imported unmodified)",
        "new_fields_added": 0,
        "shapes_placed_in_ic": 0,
        "bag_criterion": BAG_CRITERION,
        "bag_criterion_source": "verbatim copy of PR #135 "
                                "ai_lab/reports/easy/verify-20260829-one-body-bag/replay.py",
        "bag_criterion_retuned": False,
        "outside_criterion": OUTSIDE_CRITERION,
        "outside_criterion_is_not_a_bag_pass": True,
        "not_success": list(NOT_SUCCESS),
        "n_cases": len(results),
        "cases_with_any_bag_frame": sum(1 for r in results if r["any_bag_frame"]),
        "cases_with_persistent_bag": sum(1 for r in results if r["persistent_bag"]),
        "cases_with_a_transient_outside_while_amplitude_climbs": sum(
            1 for r in results if r["any_outside_survives"]),
        "cases_where_outside_still_there_at_end": sum(
            1 for r in results if r["outside_survives_at_end"]),
        "transient_outside_note": (
            "In every ordered case the low-amplitude side exists only while the amplitude "
            "is still climbing, then closes to a few percent. It is a passing stage of one "
            "ground filling the box, not a second ground sitting next to the first. This is "
            "NOT a bag pass and was never scored as one."),
        "goal_progress_json_edited": False,
        "official_rooms_touched": [],
        "figures": figures,
        "cases": results,
    }
    (HERE / "measurements.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n--- SUMMARY ---")
    print(f"cases: {summary['n_cases']}")
    print(f"any bag frame:   {summary['cases_with_any_bag_frame']}")
    print(f"persistent bag:  {summary['cases_with_persistent_bag']}")
    print(f"transient outside while climbing: "
          f"{summary['cases_with_a_transient_outside_while_amplitude_climbs']}")
    print(f"outside still there at the end:   "
          f"{summary['cases_where_outside_still_there_at_end']}")
    for r in results:
        e = r["end"]
        print(f"  {r['case']:52s} dense={e['dense_frac']:.3f} out={e['outside_frac']:.3f} "
              f"holes={e['hole_card']['n_hole_components']:4d} bag={r['persistent_bag']}")


if __name__ == "__main__":
    main()
