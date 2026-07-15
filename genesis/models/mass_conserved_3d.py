#!/usr/bin/env python3
"""M2-E-3D white -- a MASS-CONSERVED activator-inhibitor, LOCAL 7-point (np.roll only, no FFT), that from a
structureless start settles to a stable COMPACT SINGLE 3D individual (a 'ball') GROWN, not placed.

    da/dt = Da lap(a) + f(a, b)
    db/dt = Db lap(b) - f(a, b)          f = b*(k0 + gamma a^2/(K^2 + a^2)) - delta a

The SAME f enters both fields with opposite sign, so the total (a + b) is conserved EXACTLY (no source/sink).
That conservation is the point: in 2D the three-component RD / FHN whites failed the existence gate because the
'+' state invades and FILLS the domain (M2-C/M2-D). A conserved total forbids that front-invasion, so a single
localized activator core can settle instead of a labyrinth. This white is dimension-agnostic (the local
Laplacian runs in any ndim) but its role is the 3D existence test: does a genuinely-3D stable single individual
exist to linearise a drift spectrum around?

Honours AGENTS.md: local x parallel x central-none (nearest-neighbour stencil, no global solve); grow, don't
place (IC = symmetric bump + tiny noise, motion NOT seeded, law isotropic). no_touch: measures.py untouched.
Language: a settling field 'ball' is a field structure, not life (spots != life; same maths != same thing).
"""
import numpy as np

MODEL_ID = "mass_conserved_3d"

DEFAULTS = {"Da": 0.1, "Db": 2.0, "k0": 0.067, "gamma": 1.0, "K": 1.0, "delta": 1.0, "b0": 3.0}


def local_laplacian(z):
    """LOCAL periodic Laplacian for ANY ndim: -2*ndim*z + sum over axes of roll(+-1). Nearest neighbours only
    (7-point in 3D, 5-point in 2D) -- no FFT, no global operation (central-none)."""
    out = -2.0 * z.ndim * z
    for ax in range(z.ndim):
        out = out + np.roll(z, 1, ax) + np.roll(z, -1, ax)
    return out


def reaction(a, b, p):
    """Hill-type autocatalytic conversion b -> a (rate grows with a^2) minus linear decay a -> b. The SAME f is
    ADDED to a and SUBTRACTED from b => it only MOVES mass between the two fields; (a + b) has no source."""
    return b * (p["k0"] + p["gamma"] * a * a / (p["K"] ** 2 + a * a)) - p["delta"] * a


def step(a, b, dt, p):
    """One explicit local step. Diffusion is nearest-neighbour; the reaction conserves a + b term-by-term."""
    f = reaction(a, b, p)
    a2 = a + dt * (p["Da"] * local_laplacian(a) + f)
    b2 = b + dt * (p["Db"] * local_laplacian(b) - f)
    return a2, b2


def stable_dt(p, ndim=3, dx=1.0, safety=0.25):
    """Explicit diffusion bound: dt < dx^2 / (2*ndim*Dmax). Conservative safety leaves room for the reaction."""
    dmax = max(p["Da"], p["Db"])
    return float(safety * dx * dx / (2.0 * ndim * dmax))


def make_initial(shape, b0, rng, bump_width=5.0, bump_amp=0.4, noise_amp=1e-3):
    """Symmetric activator bump + tiny noise on a uniform inhibitor b0. NO seeded motion/asymmetry (grow, not
    place). Total mass is set here and thereafter conserved by the dynamics."""
    coords = np.indices(shape).astype(float)
    centre = [(n - 1) / 2.0 for n in shape]
    r2 = sum((coords[i] - centre[i]) ** 2 for i in range(len(shape)))
    a = bump_amp * np.exp(-r2 / (2.0 * bump_width ** 2)) + noise_amp * rng.standard_normal(shape)
    b = np.full(shape, float(b0))
    return a, b


def settle(shape, params=None, steps=4000, seed=0, dt=None):
    """Evolve from t=0 (bump + noise) with no intervention; return the settled fields and mass bookkeeping.
    `shape` sets the dimension (len 3 -> 3D). dt auto-selected if None."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    dt = dt if dt is not None else stable_dt(p, ndim=len(shape))
    rng = np.random.default_rng(seed)
    a, b = make_initial(shape, p["b0"], rng)
    m0 = float((a + b).sum())
    diverged = False
    for _ in range(steps):
        a, b = step(a, b, dt, p)
        if not np.all(np.isfinite(a)):
            diverged = True
            break
    m1 = None if diverged else float((a + b).sum())
    mass_drift = None if diverged else abs(m1 - m0) / (abs(m0) + 1e-30)
    return {"a": a, "b": b, "mass0": m0, "mass1": m1, "mass_drift": mass_drift,
            "diverged": diverged, "dt": dt, "params": p}


def existence_report(a, b, p, dt, area_max=0.5):
    """Run the existence_gate on a settled state: is it a compact localized STATIONARY single individual? Returns
    (ok, info) with the connected-component count, volume fraction and gate verdict. (Imports scipy/diagnostics
    lazily so the model core stays dependency-light.)"""
    from scipy import ndimage
    from genesis.diagnostics import coupled_spectrum as cs
    from genesis.models.adapters.state_layout import StateLayout

    thr = max(0.5 * (float(a.max()) + float(a.min())), 0.3)
    mask = a > thr
    _, ncomp = ndimage.label(mask)
    vol_frac = float(mask.mean())
    shape = a.shape
    lay = StateLayout(("a", "b"), (shape, shape))
    u0 = lay.flatten((a, b))
    a1, b1 = step(a, b, dt, p)
    u1 = lay.flatten((a1, b1))
    ok, info = cs.existence_gate(u0, u1, lay, ncomp, vol_frac, area_max=area_max)
    info.update({"ncomp": int(ncomp), "vol_frac": round(vol_frac, 4), "amax": round(float(a.max()), 4)})
    return ok, info


def drift_step_map(a, b, p, dt, n_sub):
    """Build a step_map_T(state_vec)->state_vec that advances the FULL (a,b) state n_sub local steps, for
    coupled_spectrum. The base state is the settled (a,b); layout bundles both fields."""
    from genesis.models.adapters.state_layout import StateLayout

    shape = a.shape
    lay = StateLayout(("a", "b"), (shape, shape))

    def step_map_T(vec):
        aa, bb = lay.unflatten(vec)
        for _ in range(n_sub):
            aa, bb = step(aa, bb, dt, p)
        return lay.flatten((aa, bb))

    return lay, step_map_T
