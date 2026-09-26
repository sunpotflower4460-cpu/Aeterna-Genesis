"""Yin and yang that become one by circling each other (P9-Q2): breathers of the sine-Gordon wave white, 1D.

    python tools/yinyang_breathers.py --out /tmp/yy

A breather is a kink (φ climbs one valley, "yang", charge +1) and an antikink (climbs down, "yin", −1) bound
together: they swap sides again and again, so the pair has no net charge, stays in one place, and beats with its
own frequency ω below the mass gap m = √λ (so it cannot radiate). Exact solution:
φ = 4 arctan[(√(m²−ω²)/ω) sin(ωt) / cosh(√(m²−ω²) x)], peak amplitude A = 4 arctan(√(m²−ω²)/ω).

Put in: the law (sine-Gordon, λ = 0.04 so a kink spans ~5 cells), t = 0 = the field slightly off the hill,
φ = π − bias + noise 0.01 (bias 0 = exactly on the hill), absorbing edges (γ = 0.05, 128 cells, the way out for
radiation). Nothing localized is put in.

Measured in two windows (t = 2000–2800 and 5000–5800), for every lump of time-averaged energy away from the
edges: net charge (from the valleys on both sides, every frame), how many kinks it contains (a ± pair appears when
φ crosses the hill), how often that pair appears and disappears, the charge dipole Σ(x − x₀)∂ₓφ/2π and how often
it flips sign, the beat frequency ω (FFT at the lump centre) vs m, and the amplitude vs the exact law after
subtracting the background swing (median |φ − valley| outside all lumps).
A lump counts as a BREATHER if: net charge 0 in every frame, ω < m, and the ± pair appeared ≥ 3 times.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from genesis.models import wave_klein_gordon as kg
from tools.snapshot import render_field

LAM, N, B = 0.04, 2048, 128


def window(phi, pi, p, mask, t_now, t0, W):
    fr, ed = [], np.zeros(N)
    k = 0
    while t_now + 1e-9 < t0 + W:
        phi, pi = kg.step(phi, pi, p, mask)
        t_now += p["dt"]
        k += 1
        if t_now >= t0 and k % 5 == 0:
            fr.append(phi.copy())
            ed += kg.energy_density(phi, pi, p)
    return phi, pi, t_now, np.array(fr), ed / max(len(fr), 1)


def lumps(fr: np.ndarray, ed: np.ndarray, m: float, dt_frame: float = 1.0) -> dict:
    inner = np.zeros(N, bool)
    inner[B + 20:N - B - 20] = True
    lab, nl = ndimage.label((ed > 0.02) & inner)
    valley = 2 * np.pi * np.round(fr / (2 * np.pi))
    outside = inner & (lab == 0)
    bg_swing = float(np.median(np.abs(fr - valley)[:, outside])) if outside.any() else 0.0
    rows = []
    for i in range(1, nl + 1):
        idx = np.nonzero(lab == i)[0]
        if len(idx) < 5:
            continue
        a, b = idx[0], idx[-1]
        left, right = fr[:, max(a - 5, 0)], fr[:, min(b + 5, N - 1)]
        net = np.unique(np.round((right - left) / (2 * np.pi)).astype(int)).tolist()
        vi = np.floor((fr[:, a:b + 1] + np.pi) / (2 * np.pi))
        nk = np.abs(np.diff(vi, axis=1)).sum(1)
        bg = 2 * np.pi * np.round(left.mean() / (2 * np.pi))
        c = a + int(np.argmax(np.abs(fr[:, a:b + 1] - bg).max(0)))
        s = fr[:, c] - bg
        f = np.fft.rfftfreq(len(s), dt_frame) * 2 * np.pi
        P = np.abs(np.fft.rfft(s - s.mean()))
        w = float(f[1 + np.argmax(P[1:])])
        A = float(np.abs(s).max()) - bg_swing
        A_exact = float(4 * np.arctan(np.sqrt(max(m * m - w * w, 0.0)) / w)) if 0 < w < m else 0.0
        rho = np.diff(fr[:, a:b + 1], axis=1) / (2 * np.pi)
        x = np.arange(rho.shape[1]) - (c - a)
        D = (rho * x).sum(1)
        big = np.abs(D) > 0.1 * np.abs(D).max() if np.abs(D).max() > 0 else np.zeros(len(D), bool)
        flips = int(np.count_nonzero(np.diff(np.sign(D[big])) != 0))
        cycles = int(np.count_nonzero(np.diff((nk > 0).astype(int)) == 1))
        rows.append({"x": int(c), "width": int(b - a + 1), "net_charge": net, "kinks_max": int(nk.max()),
                     "pair_cycles": cycles, "dipole_flips": flips, "omega_over_m": round(w / m, 3),
                     "A": round(A, 2), "A_exact": round(A_exact, 2),
                     "breather": net == [0] and w < m and cycles >= 3})
    return {"bg_swing": round(bg_swing, 3), "lumps": rows, "breathers": sum(r["breather"] for r in rows)}


def run(bias: float, seed: int, windows=((2000, 800), (5000, 800))) -> dict:
    p = dict(kg.DEFAULTS, potential="sine_gordon", lam=LAM, noise=0.01, absorb=0.05, absorb_width=B, bias=-bias)
    phi, pi = kg.make_initial((N,), np.random.default_rng(seed), p)
    mask = kg.damping_mask((N,), B)
    m, t, out, last = np.sqrt(LAM), 0.0, [], None
    for t0, W in windows:
        phi, pi, t, fr, ed = window(phi, pi, p, mask, t, t0, W)
        out.append({"t0": t0, "W": W, **lumps(fr, ed, m)})
        last = fr
    return {"bias": bias, "seed": seed, "lam": LAM, "m": m, "windows": out, "last_frames": last}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for bias in (0.0, 1.0, 1.5, 2.0):
        for seed in (1, 2, 3):
            r = run(bias, seed)
            fr = r.pop("last_frames")
            if seed == 1:
                # space (horizontal, the inner part) × time (downward): the ± pairs swapping sides
                render_field(np.sin(fr[:400, 700:1300] / 2), str(out / f"spacetime_bias{bias}.png"), diverging=True,
                             symmetric=True, px=600)
            res.append(r)
            for wdw in r["windows"]:
                br = [x for x in wdw["lumps"] if x["breather"]]
                print(f"bias={bias} seed={seed} t={wdw['t0']}: lumps {len(wdw['lumps'])}, breathers {len(br)}"
                      f" (background swing {wdw['bg_swing']})"
                      + (f" | ω/m {min(x['omega_over_m'] for x in br)}–{max(x['omega_over_m'] for x in br)}"
                         f" | pair cycles {min(x['pair_cycles'] for x in br)}–{max(x['pair_cycles'] for x in br)}"
                         f" | dipole flips {min(x['dipole_flips'] for x in br)}–{max(x['dipole_flips'] for x in br)}"
                         f" | A − A_exact {[round(x['A'] - x['A_exact'], 2) for x in br][:8]}" if br else ""),
                      flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
