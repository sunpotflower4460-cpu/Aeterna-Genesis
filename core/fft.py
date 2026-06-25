"""2D FFT helpers and wavenumber grids for split-step Fourier propagation.

The wavenumber convention matches the spec exactly:

    k = 2*pi * (idx if idx <= L/2 else idx - L) / (L * dx)

so that the kinetic operator -1/2 * laplacian becomes multiplication by
1/2 * k^2 in Fourier space. With dx = 1 the grid spacing is one unit, which
is the convention used throughout e001.
"""

import numpy as np


def wavenumbers(L, dx=1.0):
    """1D wavenumber array following the spec convention.

    idx <= L//2 keeps a positive index; idx > L//2 folds to idx - L. This is
    the standard FFT frequency layout (differs from numpy.fft.fftfreq only in
    the sign of the Nyquist bin, which is irrelevant to the dynamics).
    """
    idx = np.arange(L)
    folded = np.where(idx <= L // 2, idx, idx - L)
    return folded * (2.0 * np.pi / (L * dx))


def wavenumber_grid(L, dx=1.0):
    """Return (kx, ky) meshes with indexing='ij' (axis 0 -> x, axis 1 -> y)."""
    k = wavenumbers(L, dx)
    kx, ky = np.meshgrid(k, k, indexing="ij")
    return kx, ky


def k_squared(L, dx=1.0):
    """Return kx^2 + ky^2, the multiplier for the kinetic propagator."""
    kx, ky = wavenumber_grid(L, dx)
    return kx ** 2 + ky ** 2


def fft2(psi):
    return np.fft.fft2(psi)


def ifft2(psi_hat):
    return np.fft.ifft2(psi_hat)


def k_squared_3d(L, dx=1.0):
    """Return kx^2 + ky^2 + kz^2 on an L^3 grid (the 3D kinetic multiplier).

    Same wavenumber convention as the 2D case; used by the 3D split-step
    propagators (e003 vortex ring). FFTs are np.fft.fftn over all three axes.
    """
    k = wavenumbers(L, dx)
    kx, ky, kz = np.meshgrid(k, k, k, indexing="ij")
    return kx ** 2 + ky ** 2 + kz ** 2
