#!/usr/bin/env python3
"""M2-E-3D-NR white -- the mass-conserved 3D ball (mass_conserved_3d) plus a SLOW NON-RECIPROCAL inhibitor
field w. Question it was built to answer: can non-reciprocity push the stable-but-static ball into genuine
self-propulsion (drift) WITHOUT destroying it?

    da/dt = Da lap(a) + f(a,b) - kappa*w
    db/dt = Db lap(b) - f(a,b) + kappa*w      (the +-kappa*w cancels => total a+b still conserved EXACTLY)
    dw/dt = Dw lap(w) + (a - w)/tau           (w chases a with delay tau; the a<-w and w<-a couplings differ
                                               in form/sign => NON-reciprocal, non-variational)
    f = mass_conserved_3d.reaction

The a<->w loop is the Krischer-Mikhailov drift mechanism: a slow, long-range inhibitor that cannot follow a
moving core creates a fore-aft asymmetry that, past a threshold, could drive translation. Honest measurement is
DYNAMICAL -- track the spot centroid velocity (the physical quantity, measured BEFORE naming), with a
SPONTANEITY cross-check (across seeds the drift direction must be random = grown by noise, not placed).

FINDING (see ai_lab/campaigns/m2_results/m2e3d_nr_null.yaml): across the scanned (kappa,tau,Dw) box the M2
'scissors' PERSISTS -- the coupling strong enough to move the ball FRAGMENTS it (existence lost, ncomp>1), and
wherever the ball stays a single individual it is STATIC (terminal centroid speed at the noise floor, ~0.01
voxel of net motion). No single self-propelled individual in this box. tier=frontier (a limited scan, NOT an
all-parameters no-go). Honours AGENTS.md: local x parallel x central-none; grow, don't place. no_touch.
"""
import numpy as np

from genesis.models import mass_conserved_3d as mc

MODEL_ID = "mass_conserved_nr_3d"

DEFAULTS = dict(mc.DEFAULTS)
DEFAULTS.update({"kappa": 0.0, "Dw": 6.0, "tau": 8.0})   # kappa=0 -> reduces exactly to mass_conserved_3d


def step(a, b, w, dt, p):
    """One explicit local step of the (a,b,w) non-reciprocal white. a+b is conserved term-by-term; w relaxes
    toward a on timescale tau. All Laplacians are local 7-point (no FFT)."""
    f = mc.reaction(a, b, p)
    a2 = a + dt * (p["Da"] * mc.local_laplacian(a) + f - p["kappa"] * w)
    b2 = b + dt * (p["Db"] * mc.local_laplacian(b) - f + p["kappa"] * w)
    w2 = w + dt * (p["Dw"] * mc.local_laplacian(w) + (a - w) / p["tau"])
    return a2, b2, w2


def stable_dt(p, ndim=3, dx=1.0, safety=0.2):
    dmax = max(p["Da"], p["Db"], p["Dw"])
    return float(safety * dx * dx / (2.0 * ndim * dmax))


def periodic_centroid(field, thr):
    """Wrap-aware (circular-mean) centroid of the mass above `thr`, per axis, in [0, N). Correct on a periodic
    torus where a naive mean would jump when the spot straddles the boundary."""
    m = np.maximum(field - thr, 0.0)
    tot = m.sum() + 1e-30
    c = []
    for ax in range(field.ndim):
        n = field.shape[ax]
        ang = 2.0 * np.pi * (np.arange(n) / n)
        sh = [1] * field.ndim; sh[ax] = n
        s = (m * np.sin(ang).reshape(sh)).sum() / tot
        co = (m * np.cos(ang).reshape(sh)).sum() / tot
        c.append((np.arctan2(s, co) % (2.0 * np.pi)) * n / (2.0 * np.pi))
    return np.array(c)


def _wrap_disp(c1, c0, n):
    return (c1 - c0 + n / 2.0) % n - n / 2.0


def run_drift(shape, params=None, steps=15000, seed=0, dt=None, track_from=0.2):
    """Evolve (a,b,w) from bump+noise and MEASURE self-propulsion dynamically. Returns the settled component
    count, mass drift, and the centroid speed in early/mid/late thirds of the tracked window plus the late-time
    drift DIRECTION (unit vector). A genuine self-mover has ~constant late speed well above the noise floor; a
    static individual has speed decaying toward ~0. Direction should be seed-random (spontaneous)."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    N = shape[0]
    dt = dt if dt is not None else stable_dt(p, ndim=len(shape))
    rng = np.random.default_rng(seed)
    coords = np.indices(shape).astype(float)
    centre = [(n - 1) / 2.0 for n in shape]
    r2 = sum((coords[i] - centre[i]) ** 2 for i in range(len(shape)))
    a = 0.4 * np.exp(-r2 / (2.0 * 5.0 ** 2)) + 1e-3 * rng.standard_normal(shape)
    b = np.full(shape, float(p["b0"])); w = np.zeros(shape)
    m0 = float((a + b).sum())
    cs, ts = [], []
    t0 = int(steps * track_from)
    diverged = False
    for t in range(steps):
        a, b, w = step(a, b, w, dt, p)
        if not np.all(np.isfinite(a)):
            diverged = True
            break
        if t >= t0 and t % 25 == 0:
            thr = max(0.5 * (float(a.max()) + float(a.min())), 0.3)
            cs.append(periodic_centroid(a, thr)); ts.append(t * dt)
    if diverged:
        return {"diverged": True, "params": p}
    from scipy import ndimage
    thr = max(0.5 * (float(a.max()) + float(a.min())), 0.3)
    mask = a > thr
    _, ncomp = ndimage.label(mask, structure=np.ones((3,) * len(shape)))
    cs = np.array(cs); ts = np.array(ts)
    disp = np.array([_wrap_disp(cs[i + 1], cs[i], N) for i in range(len(cs) - 1)])
    vv = disp / np.diff(ts)[:, None]
    n = len(vv); i1, i2 = n // 3, 2 * n // 3
    sp = lambda seg: float(np.linalg.norm(seg.mean(axis=0))) if len(seg) else 0.0
    v_late = vv[i2:].mean(axis=0) if n >= 3 else np.zeros(len(shape))
    speed_late = float(np.linalg.norm(v_late))
    return {"diverged": False, "ncomp": int(ncomp), "vol_frac": round(float(mask.mean()), 3),
            "mass_drift": abs(float((a + b).sum()) - m0) / (abs(m0) + 1e-30),
            "speed_early": sp(vv[:i1]), "speed_mid": sp(vv[i1:i2]), "speed_late": speed_late,
            "direction_late": (v_late / (speed_late + 1e-30)),
            "self_propelled": bool(ncomp == 1 and speed_late > 1e-3 and speed_late > 0.7 * sp(vv[:i1])),
            "dt": dt, "params": p}
