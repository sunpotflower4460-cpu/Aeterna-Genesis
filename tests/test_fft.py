"""Unit tests for core/fft.py: round-trip identity and dispersion relation."""

import numpy as np

from core import fft


def test_fft_roundtrip_is_identity():
    rng = np.random.default_rng(0)
    psi = rng.standard_normal((32, 32)) + 1j * rng.standard_normal((32, 32))
    back = fft.ifft2(fft.fft2(psi))
    assert np.allclose(back, psi, atol=1e-12)


def test_wavenumber_convention():
    # idx <= L//2 stays positive; above folds to idx - L.
    k = fft.wavenumbers(8, dx=1.0)
    expected = 2 * np.pi * np.array([0, 1, 2, 3, 4, -3, -2, -1]) / 8.0
    assert np.allclose(k, expected)


def test_free_particle_dispersion():
    # A plane wave exp(i k.x) is an eigenstate of -1/2 lap with eigenvalue
    # 1/2 |k|^2. The spectral kinetic operator must reproduce this.
    L = 32
    kx, ky = fft.wavenumber_grid(L)
    x, y = np.meshgrid(np.arange(L), np.arange(L), indexing="ij")
    # mode (n_x, n_y) = (3, 2)
    kx0 = 2 * np.pi * 3 / L
    ky0 = 2 * np.pi * 2 / L
    psi = np.exp(1j * (kx0 * x + ky0 * y))
    psi_hat = fft.fft2(psi)
    lap_hat = -(kx ** 2 + ky ** 2) * psi_hat
    lap = fft.ifft2(lap_hat)
    # -1/2 lap psi = 1/2 (kx0^2 + ky0^2) psi
    eig = 0.5 * (kx0 ** 2 + ky0 ** 2)
    assert np.allclose(-0.5 * lap, eig * psi, atol=1e-10)
