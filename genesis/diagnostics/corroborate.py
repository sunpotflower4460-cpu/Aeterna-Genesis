#!/usr/bin/env python3
"""Corroboration: is an emergent result solver-independent, or an artefact of one numerical method?

Layer 1 (in-repo, hermetic): run the SAME white with two DIFFERENT spatial discretisations -- the LOCAL
nearest-neighbour stencil (the main line) and a SPECTRAL (FFT) Laplacian -- and check they agree on
scale-robust PHYSICAL observables. Agreement => the physics is real, not a finite-difference quirk.

Layer 2 (cross-repo, in tools/corroborate.py): additionally run the Genesis-Room- REFERENCE model and check
it agrees too (independent codebase). Genesis-Room- is reference only (never modified).

no_touch: measures.py untouched. Physical quantity FIRST.
"""
import numpy as np


def observables(field):
    """Scale-robust physical observables of a complex field: mean/std amplitude and the low-amplitude
    'core' fraction (vortex cores / holes). Robust to grid details -> good for cross-method comparison."""
    amp = np.abs(field)
    return {"mean_amp": float(amp.mean()), "std_amp": float(amp.std()),
            "core_frac": float((amp < 0.5).mean())}


def agree(obs_a, obs_b, tol=0.15, keys=("mean_amp", "core_frac")):
    """Do two observable dicts agree within relative tolerance `tol` on the given keys? Returns
    (bool, per-key relative differences)."""
    rel = {k: abs(obs_a[k] - obs_b[k]) / (abs(obs_a[k]) + abs(obs_b[k]) + 1e-9) for k in keys}
    return bool(all(v <= tol for v in rel.values())), {k: round(v, 4) for k, v in rel.items()}


def corroborate_local_vs_spectral(shape, t_final, seed=1, params=None, noise_amplitude=0.01, tol=0.15):
    """Layer 1: run cgl_local with the LOCAL stencil and with a SPECTRAL Laplacian from the SAME IC, compare
    observables. Returns a verdict dict. Same physics under two discretisations => solver-independent."""
    from genesis.models import cgl_local as cg
    p = dict(cg.DEFAULTS)
    if params:
        p.update(params)
    dt = cg.stable_dt(len(shape), p["b"])
    steps = int(round(t_final / dt))
    rng = np.random.default_rng(seed)
    A0 = cg.make_initial(shape, noise_amplitude, rng)
    a_local, a_spec = A0.copy(), A0.copy()
    k2 = cg.spectral_k2(shape)
    for _ in range(steps):
        a_local = cg.step(a_local, dt, p)
        a_spec = cg.step_spectral(a_spec, dt, p, k2)
    o_local, o_spec = observables(a_local), observables(a_spec)
    ok, rel = agree(o_local, o_spec, tol=tol)
    return {"corroborated": ok, "tol": tol, "rel_diff": rel, "local": o_local, "spectral": o_spec,
            "method_a": "local_stencil", "method_b": "spectral_fft", "shape": tuple(shape)}
