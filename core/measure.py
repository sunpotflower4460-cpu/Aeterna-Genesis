"""Measurement instruments: conserved quantities and (later) geometry probes.

These are the "rulers" of LAW.md audit 5 -- agreement with reality is checked
by number, not by eye. For e001 the relevant rulers are the GPE norm and
energy (which the conservative real-time split-step should preserve).
"""

import numpy as np

from .fft import k_squared


def norm(psi, dx=1.0):
    """integral |psi|^2 dV."""
    return float(np.sum(np.abs(psi) ** 2) * dx * dx)


def energy(psi, V, g, dx=1.0):
    """GPE energy functional E = integral[ 1/2|grad psi|^2 + V|psi|^2 + 1/2 g|psi|^4 ].

    Kinetic part is evaluated spectrally via Parseval:
    sum_x |grad psi|^2 = (1/N) sum_k k^2 |psi_hat_k|^2.
    """
    L = psi.shape[0]
    k2 = k_squared(L, dx)
    psi_hat = np.fft.fft2(psi)
    N = psi.size
    kinetic = 0.5 * np.sum(k2 * np.abs(psi_hat) ** 2) / N * dx * dx
    rho = np.abs(psi) ** 2
    potential = np.sum(V * rho) * dx * dx
    interaction = 0.5 * g * np.sum(rho ** 2) * dx * dx
    return float(kinetic + potential + interaction)


def energy_3d(psi, V, g, dx=1.0):
    """GPE energy functional on an L^3 grid (V may be a scalar 0 for a box).

    Same form as energy() but with the kinetic part evaluated via the 3D FFT
    (Parseval): sum_x |grad psi|^2 = (1/N) sum_k k^2 |psi_hat_k|^2.
    """
    from .fft import k_squared_3d
    L = psi.shape[0]
    k2 = k_squared_3d(L, dx)
    psi_hat = np.fft.fftn(psi)
    N = psi.size
    dV = dx ** 3
    kinetic = 0.5 * np.sum(k2 * np.abs(psi_hat) ** 2) / N * dV
    rho = np.abs(psi) ** 2
    potential = np.sum(V * rho) * dV
    interaction = 0.5 * g * np.sum(rho ** 2) * dV
    return float(kinetic + potential + interaction)


def relative_drift(series):
    """Max fractional deviation of a series from its initial value.

    Useful for reporting conservation: relative_drift(norms) ~ 0 means norm is
    conserved. Returns 0.0 for an empty/degenerate series.
    """
    arr = np.asarray(series, dtype=float)
    if arr.size == 0 or arr[0] == 0.0:
        return 0.0
    return float(np.max(np.abs(arr - arr[0]) / np.abs(arr[0])))


def unwrap_cumulative(angles):
    """Cumulative rotation (radians) from a sequence of polar angles.

    Wraps each step difference into (-pi, pi] and accumulates, so a vortex that
    circulates many times produces a monotonically growing total rather than a
    sawtooth. Returns an array the same length as `angles`, starting at 0.
    """
    angles = np.asarray(angles, dtype=float)
    if angles.size == 0:
        return np.array([])
    diffs = np.diff(angles)
    diffs = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    cum = np.concatenate([[0.0], np.cumsum(diffs)])
    return cum


def gradient_energy(psi, dx=1.0):
    """Spectral kinetic energy 1/2 integral |grad psi|^2 -- a complexity proxy.

    Rises as a smooth field develops structure (the arrow of complexity in
    e008) and falls again during coarsening. Works for 2D or 3D arrays.
    """
    L = psi.shape[0]
    k = np.where(np.arange(L) <= L // 2, np.arange(L), np.arange(L) - L) \
        * (2.0 * np.pi / (L * dx))
    ks = np.meshgrid(*([k] * psi.ndim), indexing="ij")
    k2 = sum(kk ** 2 for kk in ks)
    psi_hat = np.fft.fftn(psi)
    N = psi.size
    return float(0.5 * np.sum(k2 * np.abs(psi_hat) ** 2) / N * dx ** psi.ndim)


def correlation_length(field, dx=1.0):
    """Spectral correlation length 2*pi / <|k|> of (field - mean), 2D or 3D.

    <|k|> is the power-weighted first moment of the wavenumber. A growing
    correlation length signals coarsening (domains merging); for vortex
    coarsening it tracks the inter-defect spacing. Returns 0.0 for a flat field.
    """
    L = field.shape[0]
    k = np.where(np.arange(L) <= L // 2, np.arange(L), np.arange(L) - L) \
        * (2.0 * np.pi / (L * dx))
    ks = np.meshgrid(*([k] * field.ndim), indexing="ij")
    kmag = np.sqrt(sum(kk ** 2 for kk in ks))
    f = np.asarray(field) - np.mean(field)
    power = np.abs(np.fft.fftn(f)) ** 2
    total = power.sum()
    if total <= 0:
        return 0.0
    kbar = float((kmag * power).sum() / total)
    return float(2.0 * np.pi / kbar) if kbar > 0 else 0.0


def coherence_length(psi, dx=1.0):
    """First-order coherence length: the 1/e point of g1(r), 2D or 3D.

    g1(r) is the spatial autocorrelation of the fluctuation field psi - <psi>,
    computed via the Wiener-Khinchin theorem (g1 = ifft(|fft|^2)), normalised to
    g1(0)=1 and radially averaged. The coherence length xi is the radius where
    g1 first falls below 1/e, found by linear interpolation between bins.

    This is the Kibble-Zurek "frozen" length scale (e010): the size of the
    independently-chosen order-parameter domains left by a quench. The mean is
    subtracted so that the long-range order of the condensate does not swamp the
    domain/defect-scale decorrelation we want to track (the inter-defect spacing
    is found empirically to be a CONSTANT multiple of this xi -- the KZ
    signature). Returns 0.0 for a flat field.
    """
    L = psi.shape[0]
    f = np.asarray(psi) - np.mean(psi)
    ac = np.fft.fftshift(np.fft.ifftn(np.abs(np.fft.fftn(f)) ** 2).real)
    peak = ac.max()
    if peak <= 0:
        return 0.0
    ac = ac / peak
    c = L // 2
    idx = np.indices(ac.shape)
    r = np.rint(np.sqrt(sum((ix - c) ** 2 for ix in idx))).astype(int)
    radial = np.bincount(r.ravel(), ac.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    thr = 1.0 / np.e
    below = np.where(radial < thr)[0]
    if len(below) == 0:
        return float(len(radial) * dx)
    i = int(below[0])
    if i == 0:
        return 0.0
    r0, r1 = radial[i - 1], radial[i]
    frac = (r0 - thr) / (r0 - r1) if r0 != r1 else 0.0
    return float(((i - 1) + frac) * dx)
