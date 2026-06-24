"""Unit tests for core/field.py: trap, TF state, and split-step conservation."""

import numpy as np

from core import field, measure
from core.fft import k_squared


def test_harmonic_trap_min_at_center():
    L = 64
    V = field.harmonic_trap(L, 0.06)
    cx, cy = field.default_center(L)
    # Minimum is at the geometric centre and equals ~0 there.
    imin = np.unravel_index(np.argmin(V), V.shape)
    assert abs(imin[0] - cx) <= 0.5 and abs(imin[1] - cy) <= 0.5
    assert V.min() >= 0.0


def test_thomas_fermi_nonnegative():
    L = 32
    V = field.harmonic_trap(L, 0.06)
    amp = field.thomas_fermi_amplitude(V, mu=1.0)
    assert np.all(amp >= 0.0)
    # Amplitude vanishes where V exceeds mu.
    assert np.all(amp[V > 1.0] == 0.0)


def test_renormalize():
    L = 32
    V = field.harmonic_trap(L, 0.06)
    psi = field.thomas_fermi_amplitude(V, 1.0).astype(complex)
    psi = field.renormalize(psi, 100.0)
    assert abs(field.norm(psi) - 100.0) < 1e-9


def test_real_time_step_conserves_norm_and_energy():
    # The conservative split-step must preserve GPE norm and energy.
    L = 64
    g, Omega, mu = 1.0, 0.06, 1.0
    V = field.harmonic_trap(L, Omega)
    k2 = k_squared(L)
    psi, _ = field.initial_vortex_state(L, Omega, mu, R0=10.0)
    # relax briefly so we start near a real state
    norm0 = field.norm(psi)
    for _ in range(50):
        psi = field.step_imag(psi, V, k2, g, mu, 0.05)
        psi = field.renormalize(psi, norm0)
    n0, e0 = measure.norm(psi), measure.energy(psi, V, g)
    for _ in range(200):
        psi = field.step_real(psi, V, k2, g, mu, 0.1)
    assert abs(measure.norm(psi) - n0) / n0 < 1e-9
    assert abs(measure.energy(psi, V, g) - e0) / abs(e0) < 1e-5
