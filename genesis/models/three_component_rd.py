#!/usr/bin/env python3
"""Three-component reaction-diffusion (activator u + fast inhibitor v + slow long-range inhibitor w) --
the canonical "dissipative soliton" white (Purwins/Schenk/Bode). A DISTINCT white probing the frontier
beyond Swift-Hohenberg's L4-static individual: **can a SINGLE persistent individual spontaneously START
MOVING (drift bifurcation = emergent symmetry breaking), without placing motion?**

  u_t = Du lap u + lam u - u^3 - k3 v - k4 w + k1
  v_t = (Dv lap v + u - v) / tau       (fast inhibitor: shapes/confines the spot)
  w_t = (Dw lap w + u - w) / theta     (slow, long-range inhibitor: its lagging "wake" can drive drift)

Motion is NOT placed (no advection term); IC = one symmetric bump + noise (v=w=0), so any motion is
emergent. Semi-implicit spectral (all diffusions implicit -> any Dw, no CFL limit).

HONEST STATUS (docs/WHITE_CEILINGS.md): across a physically-guided scan of (k1,k3,k4,theta,Dv,tau) the
single-compact-spot existence window in 2D is a knife-edge -- off it the structure DIES, or the "+" state
INVADES and fills, or it SPLITS into multi-spot / labyrinthine turbulence (= the Gray-Scott replication
trap: the centroid of a REPLICATING population wanders, which is NOT a single self-propelled individual).
A clean single, compact, persistent spot that also self-propels was NOT reached at accessible resolution
=> **self-propelled single individual = frontier** (原則5: attacked, not avoided; motion not placed).
「同じ数学 != 同じもの」: a moving field spot is a moving localized structure, not a living thing.
"""

import numpy as np

MODEL_ID = "three_component_rd"

# A representative "near-drift" set (bistable core k3<1; slow long-range w). Frontier: no clean single
# self-propelled spot -- included so the frontier is REPRODUCIBLE, not hidden.
DEFAULTS = {"Du": 0.5, "Dv": 2.0, "Dw": 40.0, "lam": 1.0, "k1": 0.0, "k3": 0.5, "k4": 2.0,
            "tau": 1.0, "theta": 60.0, "dt": 0.1, "seed_amp": 1.5, "seed_width": 4.0}


def _k2(N, dx=1.0):
    k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
    KX, KY = np.meshgrid(k, k, indexing="ij")
    return KX ** 2 + KY ** 2


def make_initial(shape, noise_amplitude, rng, p=None):
    """One symmetric Gaussian activator bump + tiny noise; inhibitors start at zero (NO motion seeded)."""
    p = dict(DEFAULTS if p is None else p)
    N = shape[0]
    x = np.arange(N) - N / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    u = p["seed_amp"] * np.exp(-(X ** 2 + Y ** 2) / (2.0 * p["seed_width"] ** 2))
    u = u + noise_amplitude * rng.standard_normal(shape)
    return u, np.zeros(shape), np.zeros(shape)


def step(u, v, w, p, k2=None):
    """One semi-implicit spectral step (diffusions implicit, reactions explicit)."""
    if k2 is None:
        k2 = _k2(u.shape[0])
    dt = p["dt"]
    den_u = 1.0 - dt * p["lam"] + dt * p["Du"] * k2          # implicit (Du lap + lam u)
    den_v = 1.0 + dt * (p["Dv"] * k2 + 1.0) / p["tau"]
    den_w = 1.0 + dt * (p["Dw"] * k2 + 1.0) / p["theta"]
    Nu = -u ** 3 - p["k3"] * v - p["k4"] * w + p["k1"]       # explicit reaction remainder for u
    u = np.real(np.fft.ifft2((np.fft.fft2(u) + dt * np.fft.fft2(Nu)) / den_u))
    v = np.real(np.fft.ifft2((np.fft.fft2(v) + dt * np.fft.fft2(u) / p["tau"]) / den_v))
    w = np.real(np.fft.ifft2((np.fft.fft2(w) + dt * np.fft.fft2(u) / p["theta"]) / den_w))
    return u, v, w


def spot_stats(u, thr=0.4):
    """(count, area, centroid(y,x)) of localized activator spots -- count distinguishes a single body
    from a replicating population (the Gray-Scott trap)."""
    from scipy import ndimage
    m = u > thr
    lbl, n = ndimage.label(m)
    area = int(m.sum())
    if area == 0:
        return {"count": 0, "area": 0, "centroid": (np.nan, np.nan)}
    idx = np.indices(u.shape)
    cy = float((idx[0] * m).sum() / m.sum())
    cx = float((idx[1] * m).sum() / m.sum())
    return {"count": int(n), "area": area, "centroid": (cy, cx)}


def run_traj(seed, N=96, steps=8000, snap=1000, p=None):
    """Run from a symmetric seed; return per-snapshot (count, area_fraction, centroid) trajectory."""
    p = dict(DEFAULTS if p is None else p)
    rng = np.random.default_rng(seed)
    u, v, w = make_initial((N, N), 1e-3, rng, p)
    k2 = _k2(N)
    traj = []
    for i in range(steps):
        u, v, w = step(u, v, w, p, k2)
        if not np.all(np.isfinite(u)):
            return {"unstable": True, "traj": traj}
        if i % snap == 0 or i == steps - 1:
            s = spot_stats(u)
            traj.append({"i": i, "count": s["count"], "area_fraction": s["area"] / float(N * N),
                         "centroid": s["centroid"]})
    return {"unstable": False, "traj": traj, "u": u}
