"""Captured by the outside beat, or keeping its own rhythm? (P16, H7 -- 0D staircase, then 3D first, 2D after)

    python tools/golden_forcing.py --out /tmp/gf --dim 0 --gamma 0.1              # staircase of one cell
    python tools/golden_forcing.py --out /tmp/gf --dim 3 --s 0.6180 --seed 1       # medium, beat at 1/φ
    python tools/golden_forcing.py --out /tmp/gf --dim 2 --s 0.3183 --seed 1       # medium, beat at 1/π

Law: genesis/models/forced_oscillator.py (FitzHugh–Nagumo medium that oscillates by itself, period T0), plus an
outside beat γ cos(Ω t) with period Tf = s·T0, the same everywhere (put in).

Measured:
* the cumulative phase Θ of every point (unwrapped angle around the limit cycle), sampled once per beat after a
  transient (stroboscope). The rotation number ρ = own turns per beat.
* captured (locked) at p/q: over the late window, Θ(t + q Tf) − Θ(t) stays at 2π p for every sample (max deviation
  below `tol`) AND the whole window drifts by less than `tol` from p/q (no slow slip), with q ≤ `qmax`. The share of the medium that is captured, and at which p/q.
* 0D: ρ against s for many independent cells at once (D = 0, one beat frequency per cell): the staircase, the widths
  of its steps at chosen fractions, and the minimal beat strength that captures a given s (bisection over γ).
* 3D / 2D: the stroboscopic phase of captured points -- how many phase groups (peaks of its histogram) and how many
  connected domains in space; the phase singularities (spiral tips in 2D, vortex-line pieces in 3D, as in P13) of the
  last frame; the same without the beat (γ = 0).
"""
from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from genesis.models import forced_oscillator as fo
from tools.snapshot import render_field

GOLDEN = (np.sqrt(5.0) - 1.0) / 2.0        # 1/φ = 0.6180...
NAMED = {"1/3": 1 / 3, "1/2": 0.5, "1/1": 1.0, "1/pi": 1 / np.pi, "7/22": 7 / 22, "1/phi": GOLDEN, "3/5": 0.6,
         "5/8": 0.625, "1/sqrt2": 1 / np.sqrt(2.0), "1/e": 1 / np.e}


def _wrap(x):
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def lock_of(strobe: np.ndarray, qmax: int, tol: float):
    """strobe: (K, ...) cumulative phase once per beat. Returns (rho, p, q, locked) arrays (q = 0 where not locked).
    Phases turn negatively for this medium, so the magnitude is used."""
    th = -strobe if strobe[-1].mean() < strobe[0].mean() else strobe
    K = th.shape[0]
    rho = (th[-1] - th[0]) / (2.0 * np.pi * (K - 1))
    p_out = np.zeros(rho.shape, int)
    q_out = np.zeros(rho.shape, int)
    for q in range(1, qmax + 1):
        if K <= q + 2:
            break
        d = th[q:] - th[:-q]
        p = np.round(np.median(d, axis=0) / (2.0 * np.pi)).astype(int)
        dev = np.max(np.abs(d - 2.0 * np.pi * p), axis=0)
        m = ((K - 1) // q) * q                      # no slow drift over the whole window either
        drift = np.abs(th[m] - th[0] - 2.0 * np.pi * p * (m // q))
        new = (q_out == 0) & (dev < tol) & (drift < tol) & (p > 0)
        p_out[new], q_out[new] = p[new], q
    locked = q_out > 0
    if np.any(locked):                          # reduce p/q
        g = np.gcd(p_out, np.maximum(q_out, 1))
        p_out[locked] //= g[locked]
        q_out[locked] //= g[locked]
    return rho, p_out, q_out, locked


def run_cells(s, gamma: float, n_trans: float = 60.0, n_beats: int = 150, qmax: int = 12, tol: float = 0.05,
              p: dict | None = None):
    """Independent oscillators (D = 0), one per value of s. Transient n_trans·T0, then n_beats beats sampled."""
    p = dict(fo.DEFAULTS, **(p or {}), gamma=np.asarray(gamma, float), D=0.0)
    s = np.asarray(s, float)
    Om = 2.0 * np.pi / (s * fo.T0)
    Tf = s * fo.T0
    u = np.full(s.shape, -1.0)
    v = np.full(s.shape, -0.5)
    theta = fo.phase(u, v)
    Theta = theta.copy()
    t, dt = 0.0, p["dt"]
    t_start = n_trans * fo.T0
    k_next = np.zeros(s.shape, int)                 # next beat index to sample, per cell
    strobe = np.full((n_beats,) + s.shape, np.nan)
    t_end = t_start + n_beats * Tf.max() + dt
    while t < t_end:
        u, v = fo.step(u, v, t, p, Om=Om)
        t += dt
        th = fo.phase(u, v)
        Th_new = Theta + _wrap(th - theta)
        target = t_start + k_next * Tf
        hit = (k_next < n_beats) & (t >= target)
        if np.any(hit):                             # linear interpolation inside the step
            w = (t - target[hit]) / dt
            idx = np.nonzero(hit)
            strobe[(k_next[hit],) + idx] = Th_new[hit] - w * (Th_new[hit] - Theta[hit])
            k_next[hit] += 1
        Theta, theta = Th_new, th
    return lock_of(strobe, qmax, tol)


def staircase(gamma: float, s_lo=0.25, s_hi=1.1, n=851, **kw):
    s = np.linspace(s_lo, s_hi, n)
    rho, p, q, locked = run_cells(s, gamma, **kw)
    return s, rho, p, q, locked


def tongues(s, gammas, **kw):
    """Arnold-tongue diagram: for every (γ, s) the captured fraction p/q (q = 0: free). One run, all cells at once."""
    s = np.asarray(s, float)
    gammas = np.asarray(gammas, float)
    S, G = np.meshgrid(s, gammas)
    rho, p, q, locked = run_cells(S.ravel(), G.ravel(), **kw)
    sh = G.shape
    return rho.reshape(sh), p.reshape(sh), q.reshape(sh), locked.reshape(sh)


def first_capture(gammas, locked) -> np.ndarray:
    """For each s (column): the smallest γ of the scan at which it is captured (inf if never)."""
    gammas = np.asarray(gammas, float)
    any_ = locked.any(axis=0)
    first = np.argmax(locked, axis=0)
    return np.where(any_, gammas[first], np.inf)


def capture_map(s, g_hi: float = 0.3, iters: int = 9, **kw) -> np.ndarray:
    """Smallest beat strength capturing each oscillator (vectorised bisection over γ ∈ [0, g_hi]); inf if even
    g_hi does not capture it. The Arnold-tongue diagram seen from above: 0 inside a tongue at γ → 0 is never
    reached, small near wide tongues (simple fractions), large far from them."""
    s = np.asarray(s, float)
    lo, hi = np.zeros(s.shape), np.full(s.shape, g_hi)
    ok = run_cells(s, hi, **kw)[3]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        lk = run_cells(s, mid, **kw)[3]
        hi = np.where(lk, mid, hi)
        lo = np.where(lk, lo, mid)
    return np.where(ok, hi, np.inf)


def capture_gamma(s: float, g_hi: float = 0.6, iters: int = 9, **kw) -> float:
    """Smallest beat strength (bisection on [0, g_hi]) at which one oscillator at this s is captured (q ≤ qmax)."""
    lo, hi = 0.0, g_hi
    if not run_cells([s], hi, **kw)[3][0]:
        return float("inf")
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if run_cells([s], mid, **kw)[3][0]:
            hi = mid
        else:
            lo = mid
    return hi


def run_medium(dim: int, s: float, gamma: float, seed: int, n: int | None = None, n_trans: float = 40.0,
               n_beats: int = 45, qmax: int = 8, tol: float = 0.05, out: Path | None = None):
    n = n or (48 if dim == 3 else 128)
    shape = (n,) * dim
    p = dict(fo.DEFAULTS, gamma=gamma, s=s)
    u, v = fo.make_initial(shape, np.random.default_rng(seed), p)
    Om = 2.0 * np.pi / (s * fo.T0)
    Tf = s * fo.T0
    theta = fo.phase(u, v)
    Theta = theta.copy()
    t, dt = 0.0, p["dt"]
    t_start = n_trans * fo.T0
    strobe = np.empty((n_beats,) + shape)
    k = 0
    while k < n_beats:
        u, v = fo.step(u, v, t, p, Om=Om)
        t += dt
        th = fo.phase(u, v)
        Th_new = Theta + _wrap(th - theta)
        target = t_start + k * Tf
        if t >= target:
            w = (t - target) / dt
            strobe[k] = Th_new - w * (Th_new - Theta)
            k += 1
        Theta, theta = Th_new, th
    rho, pp, qq, locked = lock_of(strobe, qmax, tol)
    res = {"dim": dim, "n": n, "s": s, "gamma": gamma, "seed": seed, "T": round(t, 1),
           "captured_share": round(float(locked.mean()), 4),
           "rho_median": round(float(np.median(rho)), 5), "rho_p5_p95": [round(float(x), 5) for x in
                                                                           np.percentile(rho, [5, 95])]}
    fr = {}
    for a, b in zip(pp[locked], qq[locked]):
        fr[f"{a}/{b}"] = fr.get(f"{a}/{b}", 0) + 1
    res["captured_at"] = {k2: round(v2 / locked.size, 4) for k2, v2 in sorted(fr.items(), key=lambda x: -x[1])[:4]}
    # phase groups: the stroboscopic phase (mod 2π) of captured points, histogram peaks and spatial domains
    ph = np.mod(strobe[-1], 2.0 * np.pi)
    groups, domains = 0, 0
    if locked.mean() > 0.2:
        h, _ = np.histogram(ph[locked], bins=36, range=(0, 2 * np.pi))
        hs = np.convolve(np.r_[h[-1], h, h[0]], [1, 1, 1], "valid") / 3.0
        peaks = [i for i in range(36) if hs[i] >= hs[i - 1] and hs[i] > hs[(i + 1) % 36] and hs[i] > 0.1 * hs.max()]
        groups = len(peaks)
        if groups:
            centers = (np.array(peaks) + 0.5) * (2 * np.pi / 36)
            lab = np.argmin(np.abs(_wrap(ph[..., None] - centers)), axis=-1) + 1
            lab = np.where(locked, lab, 0)
            from genesis.models.gray_scott_two import labels as _periodic_labels
            domains = int(sum(len(np.unique(_periodic_labels((lab == g).astype(float), 0.5))) - 1
                              for g in range(1, groups + 1)))
    res.update(phase_groups=groups, phase_domains=domains)
    z = (u - fo.U_STAR) + 1j * (v - fo.V_STAR)
    if dim == 3:
        from genesis.diagnostics import vortex_rings as vr
        res["line_pieces"] = len(vr.rings(z))
    else:
        from tools.torus_birth import vortices_2d
        res["spiral_tips"] = len(vortices_2d(z))
    if out is not None:
        mid = (slice(None),) * (dim - 1) + (n // 2,) if dim == 3 else (slice(None),) * dim
        tag = f"gf{dim}d_s{s:.4f}_g{gamma}_seed{seed}"
        render_field(ph[mid], str(out / f"{tag}_phase.png"), px=480)        # stroboscopic phase (middle slice in 3D)
        render_field(u[mid], str(out / f"{tag}_u.png"), px=480)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dim", type=int, default=3, choices=(0, 2, 3))
    ap.add_argument("--s", type=float, default=GOLDEN)
    ap.add_argument("--gamma", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.dim == 0:
        s, rho, p, q, locked = staircase(a.gamma)
        rows = {}
        for name, x in NAMED.items():
            j = int(np.argmin(np.abs(s - x)))
            r1 = run_cells([x], a.gamma)
            rows[name] = {"s": round(x, 6), "rho": round(float(r1[0][0]), 5),
                          "captured": bool(r1[3][0]), "at": f"{r1[1][0]}/{r1[2][0]}" if r1[3][0] else None}
        steps = {}
        for fr in [Fraction(1, 3), Fraction(1, 2), Fraction(1, 1), Fraction(3, 5), Fraction(5, 8), Fraction(2, 3),
                   Fraction(3, 2), Fraction(2, 1), Fraction(3, 1)]:
            # rho = own turns per beat = s·(ω_own/ω_free) ~ s; the step of rho = p/q
            m = locked & (p * fr.denominator == q * fr.numerator)
            steps[f"{fr.numerator}/{fr.denominator}"] = round(float(m.sum() * (s[1] - s[0])), 4)
        res = {"gamma": a.gamma, "T0": fo.T0, "named": rows, "step_widths_in_s": steps,
               "locked_share_of_s": round(float(locked.mean()), 4), "s": s.tolist(), "rho": rho.tolist(),
               "p": p.tolist(), "q": q.tolist()}
        img = np.zeros((200, len(s)))
        for j, r in enumerate(rho):
            y = int(np.clip((r - rho.min()) / (rho.max() - rho.min() + 1e-12) * 199, 0, 199))
            img[199 - y, j] = 2.0 if locked[j] else 1.0
        render_field(img, str(out / f"gf0d_g{a.gamma}_staircase.png"), px=720)
        print(f"0D gamma={a.gamma}: locked share of s {res['locked_share_of_s']} | steps {steps}", flush=True)
        for k, v in rows.items():
            print("   ", k, v, flush=True)
        (out / f"gf0d_g{a.gamma}.json").write_text(json.dumps(res))
        return 0
    r = run_medium(a.dim, a.s, a.gamma, a.seed, a.n, out=out)
    print(f"{a.dim}D s={a.s:.4f} gamma={a.gamma} seed={a.seed}: captured {r['captured_share']} at {r['captured_at']}"
          f" | rho median {r['rho_median']} (p5–p95 {r['rho_p5_p95']}) | phase groups {r['phase_groups']} domains"
          f" {r['phase_domains']} | " + (f"line pieces {r['line_pieces']}" if a.dim == 3 else
                                          f"spiral tips {r['spiral_tips']}"), flush=True)
    (out / f"gf{a.dim}d_s{a.s:.4f}_g{a.gamma}_seed{a.seed}.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
