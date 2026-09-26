"""Do two like vortices attract or repel? (light-and-phase white, 2D) -- a check that the white carries the known
physics: type I (β < 1) attract, β = 1 (the critical, BPS point) no force, type II (β > 1) repel.

    python tools/higgs_pair_force.py --out /tmp/pair

On the periodic box the total winding must be 0, so a (+,+) pair sits at the centre and a (−,−) pair half a box
away (their mutual influence is exponentially small at that distance). Put in: the phase winding (tanh(r/ξ) per
core, phase summed over periodic images) and the gauge field that screens it away from the cores (link angle =
phase difference, faded out inside ~1/(√2 e)), E = π = 0 (Gauss's law holds). Without the screening the vortices
first act as global vortices and push each other far apart -- that would measure the start, not the force.
Strong uniform friction γ = 0.5 (put in) makes the motion overdamped (with weak friction like pairs collide and
scatter at right angles, a known effect, seen here too). Measured: the distance between the two windings of the
central pair over time (0 when they sit on one plaquette).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import abelian_higgs as ah


def pair_state(n: int, d0: float, lam: float, e: float, sign_far: int = -1):
    yy, xx = np.mgrid[:n, :n].astype(float)
    cores = [(n / 2 - 0.5, n / 2 - d0 / 2 - 0.5, +1), (n / 2 - 0.5, n / 2 + d0 / 2 - 0.5, +1),
             (n / 2 - 0.5 - n / 2, n / 2 - d0 / 2 - 0.5, sign_far), (n / 2 - 0.5 - n / 2, n / 2 + d0 / 2 - 0.5, sign_far)]
    xi = 1.0 / np.sqrt(lam)
    phase = np.zeros((n, n))
    amp = np.ones((n, n))
    for cy, cx, s in cores:
        phase += s * sum(np.arctan2(yy - cy + k * n, xx - cx + m * n) for m in range(-2, 3) for k in range(-2, 3))
        dy = np.minimum(abs(yy - cy), n - abs(yy - cy))
        dx = np.minimum(abs(xx - cx), n - abs(xx - cx))
        amp *= np.tanh(np.hypot(dy, dx) / xi)
    phi = amp * np.exp(1j * phase)
    # the gauge field that screens each vortex: away from the cores the link angle follows the phase difference,
    # so the covariant derivative vanishes there (no long-range, "global-vortex" push); near a core it fades out,
    # which leaves the core's flux inside the core. E = π = 0, so Gauss's law holds.
    lam_L = 1.0 / (np.sqrt(2.0) * e)
    g = np.ones((n, n))
    for cy, cx, _ in cores:
        dy = np.minimum(abs(yy - cy), n - abs(yy - cy))
        dx = np.minimum(abs(xx - cx), n - abs(xx - cx))
        g *= 1.0 - np.exp(-(dy ** 2 + dx ** 2) / (2 * lam_L ** 2))
    th = np.stack([ah.wrap(np.roll(phase, -1, i) - phase) * g for i in (0, 1)])
    return phi, np.zeros((n, n), complex), th, np.zeros((2, n, n))


def plus_distance(phi, th, n: int) -> float | None:
    """Distance between the two windings of the central pair (identified by place, not by the sign convention):
    0 if they sit together / merged into one plaquette, None if none is left."""
    w = ah.winding(phi, th)
    ys, xs = np.nonzero(w)
    near = [(y, x) for y, x in zip(ys, xs) if abs(y - n / 2) < n / 4]      # the central pair
    if not near:
        return None
    if len(near) < 2:
        return 0.0
    (y1, x1), (y2, x2) = near[:2]
    return float(np.hypot(min(abs(y1 - y2), n - abs(y1 - y2)), min(abs(x1 - x2), n - abs(x1 - x2))))


def run(beta: float, d0: float, n: int = 64, e: float = 0.3, gamma: float = 0.5, T: float = 600.0) -> dict:
    lam = 2 * e * e * beta
    p = dict(ah.DEFAULTS, lam=lam, e=e, gamma=gamma)
    s = pair_state(n, d0, lam, e)
    rows = []
    for k in range(int(round(T / p["dt"])) + 1):
        if k % int(round(20 / p["dt"])) == 0:
            rows.append({"t": round(k * p["dt"], 1), "d": plus_distance(s[0], s[2], n)})
        s = ah.step(*s, p)
    ds = [r["d"] for r in rows if r["d"] is not None]
    return {"beta": beta, "lam": lam, "e": e, "d0": d0, "gamma": gamma, "rows": rows,
            "d_start": ds[1] if len(ds) > 1 else None, "d_end": ds[-1] if ds else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--d0", type=float, default=6.0)
    ap.add_argument("--T", type=float, default=600.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for beta in (0.25, 0.5, 1.0, 2.0, 4.0):
        r = run(beta, a.d0, T=a.T)
        res.append(r)
        a0, a1 = r["d_start"], r["d_end"]
        trend = "?" if a0 is None or a1 is None else "近づく" if a1 < a0 - 0.5 else "離れる" if a1 > a0 + 0.5 else "ほぼ同じ"
        print(f"β={beta:<5} d: {[x['d'] for x in r['rows']][::2]}  → {trend}", flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
