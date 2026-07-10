#!/usr/bin/env python3
"""Reference Genesis model: complex time-dependent Ginzburg-Landau (TDGL) quench.

Faithful field law (put in): a single complex order-parameter field psi(x,t) evolving by
    d(psi)/dt = eps*psi - |psi|^2*psi + Du * lap(psi)
After a quench (eps: negative -> positive) the disordered (psi ~ 0) state is unstable; the field
symmetry-breaks (Level 1) and phase winding DEFECTS (2D point vortices / 3D vortex lines) form and
persist (Level 2). NO defects, pattern or wavelength are put in -- only the field law + a uniform
near-zero start with tiny noise. This is the Kibble-Zurek mechanism.

Dimension-AGNOSTIC: the same code runs in 2D (N x N) and 3D (N x N x N) via np.roll over all axes.
This is the reference model the common Runner (genesis/runners/runner.py) is fixed against.
"""

import numpy as np

MODEL_ID = "g001_ginzburg_landau_quench"

DEFAULTS = {"Du": 1.0, "dt": 0.1, "eps_final": 1.0, "quench_start": 0.0, "quench_duration": 8.0,
            "noise_amplitude": 1.0e-2}


def laplacian(Z):
    """Periodic Laplacian over all axes (2D or 3D), unit spacing."""
    out = -2 * Z.ndim * Z
    for ax in range(Z.ndim):
        out = out + np.roll(Z, 1, ax) + np.roll(Z, -1, ax)
    return out


def make_initial(shape, noise_amplitude, rng):
    """Uniform near-zero disordered state + tiny complex noise (NO pattern seeded)."""
    return (noise_amplitude * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))).astype(np.complex128)


def eps_of_t(t, p):
    """Quench: eps ramps from -eps_final to +eps_final over quench_duration (physical protocol)."""
    q0, qd, ef = p["quench_start"], p["quench_duration"], p["eps_final"]
    if qd <= 0:
        return ef
    frac = min(max((t - q0) / qd, 0.0), 1.0)
    return ef * (2.0 * frac - 1.0)


def step(psi, t, p):
    """One explicit Euler step of the TDGL field law."""
    eps = eps_of_t(t, p)
    return psi + p["dt"] * (eps * psi - (np.abs(psi) ** 2) * psi + p["Du"] * laplacian(psi))


def free_energy(psi, p):
    """GL free energy F = ∫ [ -eps|psi|^2/2 (dropped, time-dep) + |psi|^4/4 + Du|grad psi|^2/2 ].
    We track the quench-independent part for a conservation/monotonicity diagnostic."""
    grad2 = 0.0
    for ax in range(psi.ndim):
        d = np.roll(psi, -1, ax) - psi
        grad2 = grad2 + np.abs(d) ** 2
    return float(np.mean(0.25 * np.abs(psi) ** 4 + 0.5 * p["Du"] * grad2))
