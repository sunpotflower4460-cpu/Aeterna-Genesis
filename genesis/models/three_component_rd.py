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

M2-C RE-MEASUREMENT (docs/ANGULAR_MODES.md): re-measured with the FULL coupled state (u,v,w bundled), not
the u-only proxy, and guarded by `coupled_spectrum.existence_gate`. Across the k1 scan the instrument
REFUSES to report a spectrum at every point -- the state either DIES (count 0), stays a DIFFUSE DRIFTING blob
(not a stationary fixed point), or the "+" state INVADES and FILLS the domain (not localized). So the frontier
here is UPSTREAM of drift: an EXISTENCE frontier (N0 not_found_in_scan). The SAME gate ACCEPTS the SH #40
individual (positive control), so the refusal is a property of THIS white, not the instrument.
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


def coupled_audit(k1=None, N=96, settle_steps=6000, T=30, seed=1, k=8, res_gate=1e-2, area_max=0.5, p=None):
    """M2-C: re-measure this white with the FULL coupled state (u,v,w bundled), not the u-only proxy. Settle
    from the symmetric seed, then apply `coupled_spectrum.existence_gate`: only if the settled state is a
    single, compact, localized, STATIONARY individual do we linearise (bundle all three fields into a
    StateLayout, solve the coupled step-map Jacobian, identify/exclude the translation Goldstone, classify
    drift-before-split). Otherwise the audit REFUSES and returns the gate reason -- an honest existence-level
    finding (no individual to linearise; the frontier here is upstream of drift). `k1=None` uses DEFAULTS."""
    from genesis.models.adapters.state_layout import StateLayout
    from genesis.diagnostics import coupled_spectrum as cs
    p = dict(DEFAULTS if p is None else p)
    if k1 is not None:
        p["k1"] = float(k1)
    rng = np.random.default_rng(seed)
    u, v, w = make_initial((N, N), 1e-3, rng, p)
    k2 = _k2(N)
    for _ in range(settle_steps):
        u, v, w = step(u, v, w, p, k2)
        if not np.all(np.isfinite(u)):
            return {"k1": p["k1"], "gate": "REFUSED", "reason": "blow_up"}
    lay = StateLayout(("u", "v", "w"), ((N, N), (N, N), (N, N)))
    U = lay.flatten((u, v, w))
    U1 = lay.flatten(step(u, v, w, p, k2))
    s = spot_stats(u)
    area_frac = s["area"] / float(N * N)
    ok, info = cs.existence_gate(U, U1, lay, s["count"], area_frac, res_gate=res_gate, area_max=area_max)
    out = {"k1": p["k1"], **info}
    if not ok:
        out["gate"] = "REFUSED"
        return out
    out["gate"] = "PASSED"

    def step_T(vec):
        a, b, c = lay.unflatten(vec)
        for _ in range(T):
            a, b, c = step(a, b, c, p, k2)
        return lay.flatten((a, b, c))

    spec = cs.coupled_spectrum(U, step_T, lay, dx=1.0, T_dt=T * p["dt"], k=k)
    label, detected, mb = cs.classify_drift_before_split(spec)
    out.update({"n_goldstone": sum(1 for x in spec if x["is_goldstone"]), "spec_label": label,
                "detected": detected, "measured_by": mb})
    return out


def existence_scan(grid, N=64, settle=4000, seed=1):
    """M2-D: use `coupled_spectrum.existence_gate` as the OBJECTIVE to search WHERE a stable compact single
    stationary spot exists -- NOT to hunt a moving model (ANTI_DRIFT: measure where a stable individual is,
    do not place/chase one). `grid` is a list of parameter-override dicts. Returns a list of
    {**over, gate, count, area_frac, rel_res, reason}, deterministic for a fixed seed. A PASS is a regime
    where drift could then be measured; across the documented grid there are none -> the drift measurement is
    blocked by an existence frontier UPSTREAM of drift (docs/ANGULAR_MODES.md M2-D)."""
    from genesis.models.adapters.state_layout import StateLayout
    from genesis.diagnostics import coupled_spectrum as cs
    out = []
    for over in grid:
        p = dict(DEFAULTS); p.update(over)
        rng = np.random.default_rng(seed)
        u, v, w = make_initial((N, N), 1e-3, rng, p)
        k2 = _k2(N)
        blew = False
        for _ in range(settle):
            u, v, w = step(u, v, w, p, k2)
            if not np.all(np.isfinite(u)):
                blew = True
                break
        if blew:
            out.append({**over, "gate": "REFUSED", "reason": "blow_up"})
            continue
        lay = StateLayout(("u", "v", "w"), ((N, N), (N, N), (N, N)))
        U = lay.flatten((u, v, w))
        U1 = lay.flatten(step(u, v, w, p, k2))
        s = spot_stats(u)
        af = s["area"] / float(N * N)
        ok, info = cs.existence_gate(U, U1, lay, s["count"], af)
        out.append({**over, "gate": "PASSED" if ok else "REFUSED", "count": s["count"],
                    "area_frac": round(af, 3), "rel_res": info["rel_res"], "reason": info["reason"]})
    return out


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
